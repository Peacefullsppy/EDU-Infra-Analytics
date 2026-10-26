from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .logic import audit, dashboard_summary, serialize_computer, state
from .models import AuditLog, Computer, Laboratory, User
from .schemas import (ComputerInput, ComputerRead, LaboratoryInput, LaboratoryRead,
                      LoginInput, LoginOutput, UserCreate, UserRead, UserState)
from .security import current_user, hash_password, issue_token, password_matches, roles
from .settings import get_settings

app = FastAPI(title="EDU-Infra Analytics — API nova", version="0.1.0", description="Base autoral de reconstrução; banco sem dados de demonstração")
app.add_middleware(CORSMiddleware, allow_origins=get_settings()["cors_origins"], allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])


def lab_data(lab: Laboratory, db: Session) -> dict:
    return {"id": lab.id, "name": lab.name, "location": lab.location, "is_active": lab.is_active,
            "computer_count": db.scalar(select(func.count(Computer.id)).where(Computer.laboratory_id == lab.id)) or 0}


def lab_or_404(db: Session, lab_id: int) -> Laboratory:
    lab = db.get(Laboratory, lab_id)
    if lab is None:
        raise HTTPException(404, "Laboratório não encontrado")
    return lab


def pc_or_404(db: Session, pc_id: int) -> Computer:
    pc = db.get(Computer, pc_id)
    if pc is None:
        raise HTTPException(404, "Computador não encontrado")
    return pc


def unique_conflict(exc: IntegrityError):
    raise HTTPException(409, "Registro duplicado ou referência inválida") from exc


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "connected"}


@app.post("/api/v1/auth/login", response_model=LoginOutput)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not password_matches(payload.password, user.password_hash):
        audit(db, None, "LOGIN_FAILED", "auth")
        db.commit()
        raise HTTPException(401, "Credenciais inválidas")
    if not user.is_active:
        audit(db, user.id, "LOGIN_INACTIVE", "auth")
        db.commit()
        raise HTTPException(403, "Usuário inativo")
    audit(db, user.id, "LOGIN_SUCCESS", "auth")
    db.commit()
    return {"access_token": issue_token(user), "user": user}


@app.get("/api/v1/auth/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/users", response_model=list[UserRead])
def users(db: Session = Depends(get_db), user: User = Depends(roles("admin"))):
    return db.scalars(select(User).order_by(User.id)).all()


@app.post("/api/v1/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), actor: User = Depends(roles("admin"))):
    user = User(name=payload.name.strip(), email=str(payload.email).lower(), role=payload.role, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.flush()
        audit(db, actor.id, "CREATE", "user", user.id)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        unique_conflict(e)
    db.refresh(user)
    return user


@app.patch("/api/v1/users/{user_id}", response_model=UserRead)
def set_user_state(user_id: int, payload: UserState, db: Session = Depends(get_db), actor: User = Depends(roles("admin"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    if user_id == actor.id and not payload.is_active:
        raise HTTPException(409, "Você não pode desativar sua própria conta")
    user.is_active = payload.is_active
    audit(db, actor.id, "UPDATE_STATE", "user", user.id)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/v1/laboratorios", response_model=list[LaboratoryRead])
def list_labs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [lab_data(l, db) for l in db.scalars(select(Laboratory).order_by(Laboratory.id)).all()]


@app.post("/api/v1/laboratorios", response_model=LaboratoryRead, status_code=201)
def add_lab(payload: LaboratoryInput, db: Session = Depends(get_db), user: User = Depends(roles("admin", "tecnico"))):
    lab = Laboratory(**payload.model_dump())
    db.add(lab)
    db.flush()
    audit(db, user.id, "CREATE", "laboratory", lab.id)
    db.commit()
    db.refresh(lab)
    return lab_data(lab, db)


@app.get("/api/v1/laboratorios/{lab_id}", response_model=LaboratoryRead)
def get_lab(lab_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return lab_data(lab_or_404(db, lab_id), db)


@app.put("/api/v1/laboratorios/{lab_id}", response_model=LaboratoryRead)
def update_lab(lab_id: int, payload: LaboratoryInput, db: Session = Depends(get_db), user: User = Depends(roles("admin", "tecnico"))):
    lab = lab_or_404(db, lab_id)
    for key, value in payload.model_dump().items():
        setattr(lab, key, value)
    audit(db, user.id, "UPDATE", "laboratory", lab.id)
    db.commit()
    db.refresh(lab)
    return lab_data(lab, db)


@app.delete("/api/v1/laboratorios/{lab_id}", status_code=204)
def delete_lab(lab_id: int, db: Session = Depends(get_db), user: User = Depends(roles("admin"))):
    lab = lab_or_404(db, lab_id)
    if db.scalar(select(func.count(Computer.id)).where(Computer.laboratory_id == lab_id)):
        raise HTTPException(409, "Transfira ou exclua os computadores antes de excluir o laboratório")
    db.delete(lab)
    audit(db, user.id, "DELETE", "laboratory", lab_id)
    db.commit()


@app.get("/api/v1/computadores", response_model=list[ComputerRead])
def list_pcs(laboratory_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = select(Computer).order_by(Computer.id)
    if laboratory_id is not None:
        q = q.where(Computer.laboratory_id == laboratory_id)
    return [serialize_computer(pc) for pc in db.scalars(q).all()]


@app.post("/api/v1/computadores", response_model=ComputerRead, status_code=201)
def add_pc(payload: ComputerInput, db: Session = Depends(get_db), user: User = Depends(roles("admin", "tecnico"))):
    lab_or_404(db, payload.laboratory_id)
    pc = Computer(**payload.model_dump())
    db.add(pc)
    try:
        db.flush()
        audit(db, user.id, "CREATE", "computer", pc.id)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        unique_conflict(e)
    db.refresh(pc)
    return serialize_computer(pc)


@app.get("/api/v1/computadores/{pc_id}", response_model=ComputerRead)
def get_pc(pc_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return serialize_computer(pc_or_404(db, pc_id))


@app.put("/api/v1/computadores/{pc_id}", response_model=ComputerRead)
def update_pc(pc_id: int, payload: ComputerInput, db: Session = Depends(get_db), user: User = Depends(roles("admin", "tecnico"))):
    pc = pc_or_404(db, pc_id)
    lab_or_404(db, payload.laboratory_id)
    for key, value in payload.model_dump().items():
        setattr(pc, key, value)
    try:
        audit(db, user.id, "UPDATE", "computer", pc.id)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        unique_conflict(e)
    db.refresh(pc)
    return serialize_computer(pc)


@app.delete("/api/v1/computadores/{pc_id}", status_code=204)
def delete_pc(pc_id: int, db: Session = Depends(get_db), user: User = Depends(roles("admin", "tecnico"))):
    pc = pc_or_404(db, pc_id)
    db.delete(pc)
    audit(db, user.id, "DELETE", "computer", pc_id)
    db.commit()


@app.get("/api/v1/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return dashboard_summary(db)


@app.get("/api/v1/indicadores")
def indicators(db: Session = Depends(get_db), user: User = Depends(current_user)):
    result = dashboard_summary(db)
    result["laboratory_details"] = [lab_data(l, db) for l in db.scalars(select(Laboratory).order_by(Laboratory.id)).all()]
    return result


@app.get("/api/v1/alertas")
def alerts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [{"computer_id": p.id, "hostname": p.hostname, "status": state(p), "laboratory_id": p.laboratory_id}
            for p in db.scalars(select(Computer).order_by(Computer.id)).all() if state(p) in ("offline", "atencao", "critico")]


@app.get("/api/v1/relatorios/resumo")
def report_summary(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return dashboard_summary(db)


@app.get("/api/v1/auditoria")
def audit_log(db: Session = Depends(get_db), user: User = Depends(roles("admin"))):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(100)).all()
    return [{"id": x.id, "user_id": x.user_id, "action": x.action, "entity": x.entity, "entity_id": x.entity_id,
             "detail": x.detail, "created_at": x.created_at} for x in rows]


@app.get("/api/v1/privacidade")
def privacy():
    return {"finalidade": "Diagnóstico da infraestrutura tecnológica educacional", "dados_pessoais": ["nome", "e-mail", "perfil de acesso"],
            "aviso": "A instituição responsável deve estabelecer base legal, retenção e canal de contato antes de uso real."}
