import hashlib
import ipaddress
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import get_settings
from feature_demo.limits import insert
from feature_demo.models import DemoIssuance


def client_address(request):
    peer = request.client.host if request.client else "unknown"
    networks = [
        ipaddress.ip_network(value.strip())
        for value in get_settings().demo_trusted_proxies.split(",")
        if value.strip()
    ]
    try:
        current = ipaddress.ip_address(peer)
        if not any(current in network for network in networks):
            return str(current)
        chain = request.headers.get("x-forwarded-for", "").split(",")
        if len(chain) > 10:
            raise ValueError("proxy chain too long")
        for value in reversed(chain):
            if not any(current in network for network in networks):
                break
            current = ipaddress.ip_address(value.strip())
        return str(current)
    except ValueError:
        return peer


async def check_issuance(db, request):
    hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    address_hash = hashlib.sha256(client_address(request).encode()).hexdigest()
    statement = insert(db, DemoIssuance).values(key=f"{hour}:{address_hash}", count=1)
    statement = statement.on_conflict_do_update(
        index_elements=[DemoIssuance.key],
        set_={"count": DemoIssuance.count + 1},
        where=DemoIssuance.count < get_settings().demo_session_issues_per_hour,
    ).returning(DemoIssuance.count)
    if await db.scalar(statement) is None:
        raise HTTPException(status_code=429, detail="demo session issuance limit reached")
