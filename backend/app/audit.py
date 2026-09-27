import json

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def register_audit(
    db: Session,
    action: str,
    entity: str,
    user: User | None = None,
    request: Request | None = None,
    details: dict | str | None = None,
):
    if isinstance(details, dict):
        details_text = json.dumps(details, ensure_ascii=False)
    else:
        details_text = details

    ip_address = None
    if request is not None and request.client is not None:
        ip_address = request.client.host

    log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        details=details_text,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
