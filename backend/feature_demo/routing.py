"""In portfolio mode every native mutation becomes a durable job before execution."""

import re
from contextlib import aclosing

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.core.config import get_settings
from app.db.session import get_session
from feature_demo.execution import execution


class DemoRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request: Request):
            if request.method != "POST" or not get_settings().demo_enabled or execution.get():
                return await original(request)
            from feature_demo.dispatch import dispatch_job
            from feature_demo.jobs import CreateJob, accept_job, job_state
            from feature_demo.operations import OPERATIONS, NativeInput, check_owner
            from feature_demo.session import current_demo_session

            operation = next((o for o in OPERATIONS if o.path == self.path), None)
            if operation is None:
                raise HTTPException(status_code=404, detail="unregistered evaluation operation")
            # Honor the application's DB override in tests; production uses the normal factory.
            dependency = request.app.dependency_overrides.get(get_session, get_session)
            async with aclosing(dependency()) as sessions:
                async for db in sessions:
                    visitor = await current_demo_session(request, db)
                    key = request.headers.get("idempotency-key", "")
                    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", key):
                        raise HTTPException(status_code=428, detail="Idempotency-Key required")
                    await check_owner(
                        db,
                        visitor.id,
                        operation,
                        NativeInput(params=request.path_params),
                        check_state=False,
                    )
                    try:
                        body = await request.json() if await request.body() else {}
                        job_input = CreateJob(
                            feature=operation.feature,
                            action=operation.action,
                            input={"params": request.path_params, "body": body},
                        )
                    except (ValidationError, ValueError) as exc:
                        raise HTTPException(
                            status_code=422, detail="invalid evaluation input"
                        ) from exc
                    job = await accept_job(db, visitor.id, key, job_input)
                    await dispatch_job(db, job)
                    return JSONResponse(
                        status_code=202,
                        content=jsonable_encoder(job_state(job)),
                        headers={"Cache-Control": "no-store"},
                    )

        return handle
