from __future__ import annotations

import csv
import hashlib
import io
import secrets
import time
import unicodedata
from collections import defaultdict, deque
from pathlib import Path
from functools import lru_cache
from datetime import timedelta
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .core import (
    accepted_user, accepted_in_session, agent_token_hash, audit, aware, bearer, can, create_access_token, current_terms,
    current_user, hash_password, issue_agent_token, session, terms_accepted, utcnow, verify_password,
)
from .models import Alert, AuditLog, Computer, IndicatorSnapshot, Laboratory, Metric, SystemSetting, TermAcceptance, TermDocument, User
from .schemas import (
    AcceptTerms, AlertOut, ComputerIn, ComputerOut, HyperVImport, LabIn, LabOut,
    Login, MetricIn, MetricOut, SettingsIn, TermsPublish, UserCreate, UserOut,
)
from .services import computer_status, indicator, latest_metric, save_indicator_snapshot, system_settings, update_alerts

router = APIRouter(prefix="/api")
admins = can("ADMIN")
editors = can("ADMIN", "TECNICO")
readers = can("ADMIN", "TECNICO", "GESTOR")

_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempt_lock = Lock()


def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().casefold()


def clean(text: str) -> str:
    return " ".join(text.strip().split())


def unique_error(db: Session, label: str):
    db.rollback()
    raise HTTPException(409, f"{label} já cadastrado")


def lab_or_404(db: Session, lab_id: int) -> Laboratory:
    item = db.get(Laboratory, lab_id)
    if not item:
        raise HTTPException(404, "Laboratório não encontrado")
    return item


def pc_or_404(db: Session, computer_id: int) -> Computer:
    item = db.get(Computer, computer_id)
    if not item:
        raise HTTPException(404, "Computador não encontrado")
    return item


def csv_safe(value) -> str:
    text = str(value if value is not None else "")
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def csv_response(headers: list[str], rows: list[list], filename: str):
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([csv_safe(v) for v in row])
    return StreamingResponse(iter(["\ufeff" + stream.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/auth/login")
def login(payload: Login, db: Session = Depends(session)):
    key = payload.email.lower().strip()
    now = time.monotonic()
    with _attempt_lock:
        q = _attempts[key]
        while q and now - q[0] > 300:
            q.popleft()
        if len(q) >= 8:
            raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos")
    user = db.scalar(select(User).where(User.email == key))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        with _attempt_lock:
            _attempts[key].append(time.monotonic())
        raise HTTPException(401, "Credenciais inválidas")
    with _attempt_lock:
        _attempts.pop(key, None)
    audit(db, user.id, "login", "user", user.id)
    db.commit()
    return {"access_token": create_access_token(user), "token_type": "bearer", "terms_accepted": False, "previously_accepted": terms_accepted(db, user)}


@router.get("/auth/me")
def me(user: User = Depends(current_user), credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(session)):
    return {"user": UserOut.model_validate(user), "terms_accepted": bool(credentials and accepted_in_session(db, user, credentials.credentials)), "required_terms_version": (doc.version if (doc := current_terms(db)) else None)}


@router.get("/public/terms/current")
def public_terms(db: Session = Depends(session)):
    doc = current_terms(db)
    if not doc:
        raise HTTPException(503, "Termos não publicados")
    return {"version": doc.version, "title": doc.title, "content": doc.content, "published_at": doc.published_at}


@lru_cache(maxsize=1)
def _privacy_notice_text() -> str:
    return (Path(__file__).resolve().parent / "legal" / "aviso_de_privacidade_v1.txt").read_text(encoding="utf-8")


@router.get("/public/privacy-notice")
def public_privacy_notice():
    """Aviso de privacidade visível inclusive sem conta ou aceite de Termos."""
    return {
        "version": "1.0",
        "title": "Aviso de Privacidade — EDU-Infra Analytics",
        "updated_at": "2026-11-08",
        "content": _privacy_notice_text(),
    }


@router.get("/terms/current")
def terms(user: User = Depends(current_user), db: Session = Depends(session)):
    doc = current_terms(db)
    if not doc:
        raise HTTPException(503, "Termos não publicados")
    return {"version": doc.version, "title": doc.title, "content": doc.content, "published_at": doc.published_at, "accepted": terms_accepted(db, user)}


@router.post("/terms/accept")
def accept_terms(payload: AcceptTerms, user: User = Depends(current_user), db: Session = Depends(session)):
    doc = current_terms(db)
    if not doc:
        raise HTTPException(503, "Termos não publicados")
    if payload.version != doc.version:
        raise HTTPException(409, "A versão dos termos mudou. Leia a versão atual")
    if not terms_accepted(db, user):
        db.add(TermAcceptance(user_id=user.id, terms_id=doc.id))
        audit(db, user.id, "terms.accept", "term_document", doc.id, f"Versão {doc.version}")
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if not terms_accepted(db, user):
                raise HTTPException(409, "Falha no registro do aceite")
    return {"accepted": True, "version": doc.version, "access_token": create_access_token(user, doc.version), "token_type": "bearer"}


@router.post("/terms/publish", status_code=201)
def publish_terms(payload: TermsPublish, user: User = Depends(admins), db: Session = Depends(session)):
    if db.scalar(select(TermDocument.id).where(TermDocument.version == payload.version)):
        raise HTTPException(409, "Versão já publicada")
    db.query(TermDocument).filter(TermDocument.active.is_(True)).update({"active": False}, synchronize_session=False)
    doc = TermDocument(version=payload.version, title=payload.title, content=payload.content, active=True)
    db.add(doc)
    db.flush()
    audit(db, user.id, "terms.publish", "term_document", doc.id, payload.version)
    db.commit()
    return {"id": doc.id, "version": doc.version, "active": True}


@router.get("/terms/acceptances")
def terms_acceptances(user: User = Depends(admins), db: Session = Depends(session)):
    rows = db.execute(select(TermAcceptance, User.email, TermDocument.version).join(User, User.id == TermAcceptance.user_id).join(TermDocument, TermDocument.id == TermAcceptance.terms_id).order_by(TermAcceptance.accepted_at.desc()).limit(300)).all()
    return [{"user_id": a.user_id, "email": email, "version": version, "accepted_at": a.accepted_at} for a, email, version in rows]


@router.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(admins), db: Session = Depends(session)):
    return db.scalars(select(User).order_by(User.name)).all()


@router.post("/users", response_model=UserOut, status_code=201)
def add_user(payload: UserCreate, user: User = Depends(admins), db: Session = Depends(session)):
    entity = User(name=clean(payload.name), email=str(payload.email).strip().lower(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(entity)
    try:
        db.flush()
    except IntegrityError:
        unique_error(db, "E-mail")
    audit(db, user.id, "user.create", "user", entity.id)
    db.commit()
    return entity


@router.patch("/users/{user_id}/status")
def toggle_user_status(user_id: int, active: bool, user: User = Depends(admins), db: Session = Depends(session)):
    entity = db.get(User, user_id)
    if not entity:
        raise HTTPException(404, "Usuário não encontrado")
    if entity.id == user.id and not active:
        raise HTTPException(409, "Não é possível desativar a própria conta")
    entity.active = active
    audit(db, user.id, "user.status", "user", entity.id, f"active={active}")
    db.commit()
    return {"id": entity.id, "active": entity.active}


@router.get("/laboratories", response_model=list[LabOut])
def laboratories(q: str = "", active: bool | None = None, user: User = Depends(readers), db: Session = Depends(session)):
    statement = select(Laboratory)
    if q:
        text = f"%{q.strip()}%"
        statement = statement.where(or_(Laboratory.name.ilike(text), Laboratory.location.ilike(text)))
    if active is not None:
        statement = statement.where(Laboratory.active == active)
    return db.scalars(statement.order_by(Laboratory.name)).all()


@router.post("/laboratories", response_model=LabOut, status_code=201)
def create_lab(payload: LabIn, user: User = Depends(editors), db: Session = Depends(session)):
    name, location = clean(payload.name), clean(payload.location)
    lab = Laboratory(name=name, location=location, name_key=normalized(name), location_key=normalized(location), active=payload.active)
    db.add(lab)
    try:
        db.flush()
    except IntegrityError:
        unique_error(db, "Laboratório com nome e localização iguais")
    audit(db, user.id, "laboratory.create", "laboratory", lab.id)
    db.commit()
    return lab


@router.put("/laboratories/{lab_id}", response_model=LabOut)
def update_lab(lab_id: int, payload: LabIn, user: User = Depends(editors), db: Session = Depends(session)):
    lab = lab_or_404(db, lab_id)
    lab.name, lab.location, lab.active = clean(payload.name), clean(payload.location), payload.active
    lab.name_key, lab.location_key = normalized(lab.name), normalized(lab.location)
    try:
        db.flush()
    except IntegrityError:
        unique_error(db, "Laboratório com nome e localização iguais")
    audit(db, user.id, "laboratory.update", "laboratory", lab_id)
    db.commit()
    return lab


@router.delete("/laboratories/{lab_id}", status_code=204)
def delete_lab(lab_id: int, user: User = Depends(editors), db: Session = Depends(session)):
    lab = lab_or_404(db, lab_id)
    if db.scalar(select(func.count(Computer.id)).where(Computer.laboratory_id == lab_id)):
        raise HTTPException(409, "Remova ou transfira os computadores antes de excluir o laboratório")
    db.delete(lab)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Laboratório possui computadores associados")
    audit(db, user.id, "laboratory.delete", "laboratory", lab_id)
    db.commit()


@router.get("/computers")
def computers(q: str = "", laboratory_id: int | None = None, user: User = Depends(readers), db: Session = Depends(session)):
    cfg = system_settings(db)
    statement = select(Computer)
    if q:
        statement = statement.where(or_(Computer.name.ilike(f"%{q}%"), Computer.hostname.ilike(f"%{q}%")))
    if laboratory_id:
        statement = statement.where(Computer.laboratory_id == laboratory_id)
    items = db.scalars(statement.order_by(Computer.name)).all()
    return [{**ComputerOut.model_validate(pc).model_dump(mode="json"), "status": computer_status(pc, cfg.stale_after_seconds), "latest_metric": MetricOut.model_validate(m).model_dump(mode="json") if (m := latest_metric(db, pc.id)) else None} for pc in items]


@router.post("/computers", response_model=ComputerOut, status_code=201)
def create_pc(payload: ComputerIn, user: User = Depends(editors), db: Session = Depends(session)):
    lab_or_404(db, payload.laboratory_id)
    pc = Computer(laboratory_id=payload.laboratory_id, name=clean(payload.name), hostname=clean(payload.hostname), ip_address=payload.ip_address, active=payload.active)
    db.add(pc)
    try:
        db.flush()
    except IntegrityError:
        unique_error(db, "Hostname no laboratório")
    audit(db, user.id, "computer.create", "computer", pc.id)
    db.commit()
    return pc


@router.put("/computers/{computer_id}", response_model=ComputerOut)
def update_pc(computer_id: int, payload: ComputerIn, user: User = Depends(editors), db: Session = Depends(session)):
    pc = pc_or_404(db, computer_id)
    lab_or_404(db, payload.laboratory_id)
    for field, value in {"laboratory_id": payload.laboratory_id, "name": clean(payload.name), "hostname": clean(payload.hostname), "ip_address": payload.ip_address, "active": payload.active}.items():
        setattr(pc, field, value)
    try:
        db.flush()
    except IntegrityError:
        unique_error(db, "Hostname no laboratório")
    audit(db, user.id, "computer.update", "computer", pc.id)
    db.commit()
    return pc


@router.delete("/computers/{computer_id}", status_code=204)
def delete_pc(computer_id: int, user: User = Depends(editors), db: Session = Depends(session)):
    pc = pc_or_404(db, computer_id)
    # A exclusão de computador remove seu histórico de medições e alertas.
    db.delete(pc)
    audit(db, user.id, "computer.delete", "computer", computer_id)
    db.commit()


@router.post("/computers/{computer_id}/token")
def rotate_token(computer_id: int, user: User = Depends(editors), db: Session = Depends(session)):
    pc = pc_or_404(db, computer_id)
    raw, hashed = issue_agent_token()
    pc.agent_token_hash = hashed
    pc.agent_token_issued_at = utcnow()
    audit(db, user.id, "computer.token.rotate", "computer", computer_id)
    db.commit()
    return {"computer_id": pc.id, "agent_token": raw, "shown_once": True}


@router.delete("/computers/{computer_id}/token")
def revoke_token(computer_id: int, user: User = Depends(editors), db: Session = Depends(session)):
    pc = pc_or_404(db, computer_id)
    pc.agent_token_hash = None
    pc.agent_token_issued_at = None
    audit(db, user.id, "computer.token.revoke", "computer", computer_id)
    db.commit()
    return {"revoked": True}


@router.post("/agent/metrics", status_code=201)
def ingest_metric(payload: MetricIn, x_computer_id: Annotated[int | None, Header()] = None, x_agent_token: Annotated[str | None, Header()] = None, db: Session = Depends(session)):
    if not x_computer_id or not x_agent_token:
        raise HTTPException(401, "Credenciais do agente obrigatórias")
    pc = db.get(Computer, x_computer_id)
    if not pc or not pc.active or not pc.agent_token_hash or not secrets.compare_digest(pc.agent_token_hash, agent_token_hash(x_agent_token)):
        raise HTTPException(401, "Token do agente inválido")
    now = utcnow()
    captured = payload.collected_at.astimezone(now.tzinfo)
    if captured > now + timedelta(minutes=5) or captured < now - timedelta(days=2):
        raise HTTPException(422, "Horário de coleta fora da janela permitida")
    measurement = Metric(computer_id=pc.id, **payload.model_dump())
    measurement.collected_at = captured
    db.add(measurement)
    if not pc.last_seen_at or captured >= aware(pc.last_seen_at):
        pc.last_seen_at = now
    db.flush()
    update_alerts(db, pc.id, measurement)
    save_indicator_snapshot(db, pc.laboratory)
    db.commit()
    return {"id": measurement.id, "computer_id": pc.id, "received": True}


@router.get("/computers/{computer_id}/metrics", response_model=list[MetricOut])
def history(computer_id: int, limit: int = Query(60, ge=1, le=500), user: User = Depends(readers), db: Session = Depends(session)):
    pc_or_404(db, computer_id)
    return db.scalars(select(Metric).where(Metric.computer_id == computer_id).order_by(Metric.collected_at.desc()).limit(limit)).all()


@router.get("/alerts", response_model=list[AlertOut])
def alerts(state: str | None = None, user: User = Depends(readers), db: Session = Depends(session)):
    stmt = select(Alert)
    if state:
        stmt = stmt.where(Alert.status == state)
    return db.scalars(stmt.order_by(Alert.created_at.desc()).limit(500)).all()


@router.patch("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, user: User = Depends(editors), db: Session = Depends(session)):
    item = db.get(Alert, alert_id)
    if not item:
        raise HTTPException(404, "Alerta não encontrado")
    if item.status == "open":
        item.status = "acknowledged"
        item.acknowledged_at = utcnow()
        audit(db, user.id, "alert.acknowledge", "alert", item.id)
        db.commit()
    return item


@router.get("/indicators")
def indicators(user: User = Depends(readers), db: Session = Depends(session)):
    cfg = system_settings(db)
    return [indicator(db, lab, cfg) for lab in db.scalars(select(Laboratory).order_by(Laboratory.name)).all()]


@router.get("/indicators/{lab_id}/history")
def indicator_history(lab_id: int, limit: int = Query(100, ge=1, le=500), user: User = Depends(readers), db: Session = Depends(session)):
    lab_or_404(db, lab_id)
    items = db.scalars(select(IndicatorSnapshot).where(IndicatorSnapshot.laboratory_id == lab_id).order_by(IndicatorSnapshot.calculated_at.desc()).limit(limit)).all()
    return [{"score": i.score, "coverage": i.coverage, "online": i.online, "total": i.total, "calculated_at": i.calculated_at} for i in items]


@router.get("/dashboard/summary")
def summary(user: User = Depends(readers), db: Session = Depends(session)):
    cfg = system_settings(db)
    pcs = db.scalars(select(Computer)).all()
    states = [computer_status(pc, cfg.stale_after_seconds) for pc in pcs]
    labs = db.scalars(select(Laboratory)).all()
    computed = [indicator(db, lab, cfg) for lab in labs]
    scores = [i["score"] for i in computed if i["score"] is not None]
    return {"laboratories": len(labs), "computers": len(pcs), "online": states.count("online"), "offline": states.count("offline"), "sem_coleta": states.count("sem_coleta"), "inactive": states.count("inactive"), "open_alerts": db.scalar(select(func.count(Alert.id)).where(Alert.status.in_(["open", "acknowledged"]))) or 0, "iie_average": round(sum(scores) / len(scores), 2) if scores else None, "indicators": computed}


@router.get("/settings")
def get_configuration(user: User = Depends(readers), db: Session = Depends(session)):
    obj = system_settings(db)
    return SettingsIn.model_validate(obj, from_attributes=True)


@router.put("/settings")
def set_configuration(payload: SettingsIn, user: User = Depends(admins), db: Session = Depends(session)):
    obj = system_settings(db)
    for key, value in payload.model_dump().items():
        setattr(obj, key, value)
    audit(db, user.id, "settings.update", "system_settings", 1)
    db.commit()
    return payload


@router.get("/reports/metrics.csv")
def report_metrics(computer_id: int | None = None, limit: int = Query(10000, ge=1, le=50000), user: User = Depends(readers), db: Session = Depends(session)):
    stmt = select(Metric, Computer.hostname).join(Computer, Computer.id == Metric.computer_id)
    if computer_id:
        pc_or_404(db, computer_id)
        stmt = stmt.where(Metric.computer_id == computer_id)
    records = db.execute(stmt.order_by(Metric.collected_at.desc()).limit(limit)).all()
    rows = [[m.id, m.computer_id, hostname, m.collected_at.isoformat(), m.cpu_percent, m.memory_percent, m.disk_percent, m.uptime_seconds, m.os_name] for m, hostname in records]
    return csv_response(["Medição", "Computador ID", "Hostname", "Data da coleta", "CPU (%)", "Memória (%)", "Disco (%)", "Uptime (segundos)", "Sistema operacional"], rows, "metricas_eduinfra.csv")


@router.get("/reports/indicators.csv")
def report_indicators(user: User = Depends(readers), db: Session = Depends(session)):
    rows = [[i["laboratory_id"], i["laboratory"], i["score"], i["coverage"], i["online"], i["offline"], i["total"], i["classification"]] for i in [indicator(db, lab) for lab in db.scalars(select(Laboratory)).all()]]
    return csv_response(["ID", "Laboratório", "IIE", "Cobertura (%)", "Online", "Offline", "Total", "Classificação"], rows, "indicadores_eduinfra.csv")


@router.get("/audit")
def audit_logs(limit: int = Query(100, ge=1, le=500), user: User = Depends(admins), db: Session = Depends(session)):
    items = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)).all()
    return [{"id": i.id, "actor_id": i.actor_id, "action": i.action, "entity": i.entity, "entity_id": i.entity_id, "details": i.details, "created_at": i.created_at} for i in items]


@router.post("/hyperv/import")
def import_hyperv(payload: HyperVImport, user: User = Depends(editors), db: Session = Depends(session)):
    lab_or_404(db, payload.laboratory_id)
    created, updated = 0, 0
    for vm in payload.vms:
        item = db.scalar(select(Computer).where(Computer.hyperv_vm_id == vm.vm_id))
        if item:
            # A origem Hyper-V não modifica ID, credenciais ou métricas do agente.
            item.hyperv_state = vm.state
            item.name = vm.name
            updated += 1
        else:
            item = Computer(laboratory_id=payload.laboratory_id, name=vm.name, hostname="hyperv-" + hashlib.sha256(vm.vm_id.encode()).hexdigest()[:20], source="hyperv", hyperv_vm_id=vm.vm_id, hyperv_state=vm.state)
            db.add(item)
            created += 1
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Inventário contém VM duplicada ou hostname em conflito")
    audit(db, user.id, "hyperv.import", "laboratory", payload.laboratory_id, f"created={created}, updated={updated}")
    db.commit()
    return {"created": created, "updated": updated, "total": len(payload.vms)}
