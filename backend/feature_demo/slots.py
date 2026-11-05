"""Cross-process slots have no TTL: only confirmed completion can release them."""

import asyncio
import os
import socket
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update

from app.core.config import get_settings
from feature_demo.execution import execution
from feature_demo.limits import enabled, gate, insert
from feature_demo.models import DemoJob, DemoSlot


async def acquire(maker, kind, job_id, lease, resource=None):
    maximum = (
        get_settings().demo_max_evaluations
        if kind == "evaluation"
        else get_settings().demo_max_sandboxes
    )
    while True:
        async with maker() as db:
            await gate(db)
            for index in range(maximum):
                await db.execute(
                    insert(db, DemoSlot).values(kind=kind, number=index).on_conflict_do_nothing()
                )
            occupied = await db.scalar(
                select(DemoSlot).where(
                    DemoSlot.kind == kind, DemoSlot.job_id.is_not(None), DemoSlot.number >= maximum
                )
            )
            if occupied is None:
                slot = await db.scalar(
                    select(DemoSlot)
                    .where(
                        DemoSlot.kind == kind, DemoSlot.number < maximum, DemoSlot.job_id.is_(None)
                    )
                    .order_by(DemoSlot.number)
                    .limit(1)
                )
                if slot:
                    slot.job_id, slot.lease = job_id, lease
                    slot.pid, slot.host, slot.resource = os.getpid(), socket.gethostname(), resource
                    number = slot.number
                    await db.commit()
                    return number
            await db.rollback()
        await asyncio.sleep(0.1)


async def release(maker, kind, number, lease):
    async with maker() as db:
        await db.execute(
            update(DemoSlot)
            .where(
                DemoSlot.kind == kind,
                DemoSlot.number == number,
                DemoSlot.lease == lease,
            )
            .values(job_id=None, lease=None, pid=None, host=None, resource=None)
        )
        await db.commit()


@contextmanager
def sandbox_slot(name):
    if not enabled():
        yield
        return
    from feature_demo.meter import sync

    active = execution.get()
    if active is None:
        raise HTTPException(status_code=403, detail="demo code execution requires a job")
    lease = uuid4().hex
    number = sync(acquire(active.sessions, "sandbox", active.job_id, lease, name))
    try:
        yield
    except Exception:
        # The runner may be unable to confirm container cleanup. Keep the slot for recovery.
        raise
    else:
        sync(release(active.sessions, "sandbox", number, lease))


def dead_local_process(slot) -> bool:
    if slot.host != socket.gethostname() or not slot.pid:
        return False
    try:
        os.kill(slot.pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        pass
    return False


async def recover_slots(db):
    await gate(db)
    released = unresolved = 0
    for slot in await db.scalars(select(DemoSlot).where(DemoSlot.job_id.is_not(None))):
        if not dead_local_process(slot):
            unresolved += 1
            continue
        if slot.kind == "sandbox":
            if not slot.resource or not slot.resource.startswith("gaudi-sandbox-"):
                unresolved += 1
                continue
            # Confirm daemon access before inferring container absence.
            try:
                inventory = await asyncio.to_thread(
                    subprocess.run,
                    ["docker", "ps", "-a", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if inventory.returncode:
                    unresolved += 1
                    continue
                if slot.resource in inventory.stdout.splitlines():
                    cleaned = await asyncio.to_thread(
                        subprocess.run,
                        ["docker", "rm", "--force", slot.resource],
                        capture_output=True,
                        timeout=10,
                    )
                    if cleaned.returncode:
                        unresolved += 1
                        continue
            except (OSError, subprocess.TimeoutExpired):
                unresolved += 1
                continue
        if slot.kind == "evaluation":
            from feature_demo.meter import close_inflight

            job = await db.get(DemoJob, slot.job_id, populate_existing=True)
            if job and job.status == "running" and job.lease == slot.lease:
                job.status, job.phase, job.error_code = "failed", "failed", "worker_interrupted"
                job.finished_at = job.updated_at = datetime.now(timezone.utc)
            await close_inflight(db, slot.job_id)
        slot.job_id = slot.lease = slot.pid = slot.host = slot.resource = None
        released += 1
    await db.commit()
    return {"slots_released": released, "slots_unresolved": unresolved}
