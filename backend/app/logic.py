from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import AuditLog, Computer, Laboratory


# Regras exploratórias de severidade técnica; IIE não é inferido destas regras.
THRESHOLD_WARNING = 80
THRESHOLD_CRITICAL = 95
OFFLINE_AFTER_MINUTES = 10


def state(computer: Computer) -> str:
    if computer.last_seen_at is None:
        return "sem_coleta"
    last = computer.last_seen_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - last > timedelta(minutes=OFFLINE_AFTER_MINUTES):
        return "offline"
    metrics = [m for m in (computer.cpu_percent, computer.ram_percent, computer.disk_percent) if m is not None]
    if any(m >= THRESHOLD_CRITICAL for m in metrics):
        return "critico"
    if any(m >= THRESHOLD_WARNING for m in metrics):
        return "atencao"
    return "online"


def dashboard_summary(db: Session) -> dict:
    pcs = db.scalars(select(Computer)).all()
    statuses = [state(pc) for pc in pcs]
    summary = {key: statuses.count(key) for key in ("sem_coleta", "online", "offline", "atencao", "critico")}
    measured = len(pcs) - summary["sem_coleta"]
    summary["total"] = len(pcs)
    return {
        "laboratories": db.scalar(select(func.count(Laboratory.id))) or 0,
        "computers": summary,
        "availability_percent": round(summary["online"] / measured * 100, 1) if measured else None,
        "iie": None,
        "iie_status": "nao_definido",
    }


def audit(db: Session, user_id: int | None, action: str, entity: str, entity_id: int | None = None, detail: str | None = None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, detail=detail))


def serialize_computer(pc: Computer) -> dict:
    return {
        "id": pc.id, "hostname": pc.hostname, "ip_address": pc.ip_address,
        "laboratory_id": pc.laboratory_id, "status": state(pc),
        "cpu_percent": pc.cpu_percent, "ram_percent": pc.ram_percent,
        "disk_percent": pc.disk_percent, "last_seen_at": pc.last_seen_at,
    }
