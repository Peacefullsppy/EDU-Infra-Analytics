from __future__ import annotations

from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from .core import aware, utcnow
from .models import Alert, Computer, IndicatorSnapshot, Laboratory, Metric, SystemSetting


def system_settings(db: Session) -> SystemSetting:
    config = db.get(SystemSetting, 1)
    if config is None:
        config = SystemSetting(id=1, cpu_alert_threshold=90, memory_alert_threshold=90, disk_alert_threshold=90, stale_after_seconds=600)
        db.add(config)
        db.flush()
    return config


def latest_metric(db: Session, computer_id: int) -> Metric | None:
    return db.scalar(select(Metric).where(Metric.computer_id == computer_id).order_by(Metric.collected_at.desc(), Metric.id.desc()).limit(1))


def computer_status(computer: Computer, stale_seconds: int, now=None) -> str:
    if not computer.active:
        return "inactive"
    if computer.last_seen_at is None:
        return "sem_coleta"
    if (now or utcnow()) - aware(computer.last_seen_at) > timedelta(seconds=stale_seconds):
        return "offline"
    return "online"


def indicator(db: Session, lab: Laboratory, config: SystemSetting | None = None, now=None) -> dict:
    config = config or system_settings(db)
    now = now or utcnow()
    computers = db.scalars(select(Computer).where(Computer.laboratory_id == lab.id, Computer.active.is_(True)).order_by(Computer.id)).all()
    total = len(computers)
    if not total:
        return {"laboratory_id": lab.id, "laboratory": lab.name, "score": None, "coverage": 0, "online": 0, "offline": 0, "sem_coleta": 0, "total": 0, "classification": "sem_dados"}
    valid = []
    online = 0
    offline = 0
    no_data = 0
    for c in computers:
        state = computer_status(c, config.stale_after_seconds, now)
        if state == "online":
            measure = latest_metric(db, c.id)
            if measure:
                valid.append(measure)
                online += 1
            else:
                no_data += 1
        elif state == "offline":
            offline += 1
        else:
            no_data += 1
    coverage = round(100 * len(valid) / total, 2)
    if not valid:
        score = None
        classification = "sem_dados"
    else:
        # Índice heurístico: 40% disponibilidade + 60% eficiência média.
        # Máquinas não observadas não recebem pontuação artificialmente positiva.
        efficiencies = [0.35 * (100 - m.cpu_percent) + 0.35 * (100 - m.memory_percent) + 0.30 * (100 - m.disk_percent) for m in valid]
        score = round(40 * online / total + 0.60 * sum(efficiencies) / total, 2)
        classification = "adequado" if score >= 75 else "atencao" if score >= 50 else "critico"
    return {"laboratory_id": lab.id, "laboratory": lab.name, "score": score, "coverage": coverage, "online": online, "offline": offline, "sem_coleta": no_data, "total": total, "classification": classification}


def save_indicator_snapshot(db: Session, lab: Laboratory):
    item = indicator(db, lab)
    db.add(IndicatorSnapshot(laboratory_id=lab.id, score=item["score"], coverage=item["coverage"], online=item["online"], total=item["total"]))


def update_alerts(db: Session, computer_id: int, metric: Metric):
    cfg = system_settings(db)
    checks = (
        ("cpu", metric.cpu_percent, cfg.cpu_alert_threshold),
        ("memory", metric.memory_percent, cfg.memory_alert_threshold),
        ("disk", metric.disk_percent, cfg.disk_alert_threshold),
    )
    for kind, value, limit in checks:
        active = db.scalar(select(Alert).where(Alert.computer_id == computer_id, Alert.type == kind, Alert.status.in_(["open", "acknowledged"])).order_by(Alert.created_at.desc()).limit(1))
        if value >= limit:
            if not active:
                db.add(Alert(computer_id=computer_id, type=kind, severity="critical" if value >= 97 else "warning", message=f"{kind.upper()} atingiu {value:.1f}% (limite {limit}%)", status="open"))
        elif value < max(0, limit - 5) and active:
            active.status = "resolved"
            active.resolved_at = utcnow()
