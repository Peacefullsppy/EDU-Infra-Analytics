from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import register_audit
from app.config import FRONTEND_URL
from app.database import get_db, init_db
from app.external import consultar_cep
from app.models import AuditLog, Computer, Laboratory, User
from app.schemas import (
    ComputadorCreate,
    LaboratorioCreate,
    LoginRequest,
    LoginResponse,
    StatusComputador,
)
from app.security import (
    create_access_token,
    get_current_user,
    require_roles,
    verify_password,
)

app = FastAPI(
    title="EDU-Infra Analytics API",
    version="0.2.0",
    description=(
        "API do EDU-Infra Analytics com PostgreSQL/SQLAlchemy, autenticação JWT, "
        "auditoria, LGPD e integração externa ViaCEP."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


def user_payload(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def contar_status(db: Session):
    computadores = db.scalars(select(Computer)).all()
    total = len(computadores)
    offline = sum(1 for pc in computadores if pc.status == "offline")
    atencao = sum(1 for pc in computadores if pc.status in {"atencao", "critico"})
    online = total - offline
    return {"total": total, "online": online, "offline": offline, "atencao": atencao}


@app.get("/")
def root():
    return {"message": "EDU-Infra Analytics API funcionando"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "conectado"}


@app.post("/auth/login", response_model=LoginResponse)
def login(dados: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == dados.email))
    if user is None or not verify_password(dados.password, user.password_hash):
        register_audit(
            db,
            "LOGIN_FALHA",
            "auth",
            request=request,
            details={"email": dados.email},
        )
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    token = create_access_token(user)
    register_audit(db, "LOGIN_SUCESSO", "auth", user=user, request=request)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_payload(user),
    }


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return user_payload(current_user)


@app.get("/dashboard")
def obter_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    status = contar_status(db)
    iies = [value for value in db.scalars(select(Laboratory.iie)).all() if value is not None]
    iie_geral = round(sum(iies) / len(iies)) if iies else 0
    register_audit(db, "VISUALIZAR_DASHBOARD", "dashboard", current_user, request)
    return {"iie_geral": iie_geral, "computadores": status, "alertas": status["atencao"]}


@app.get("/laboratorios")
def listar_laboratorios(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    laboratorios = db.scalars(select(Laboratory).order_by(Laboratory.id)).all()
    resultado = []

    for lab in laboratorios:
        pcs = db.scalars(select(Computer).where(Computer.laboratorio_id == lab.id)).all()
        total = len(pcs)
        problemas = sum(1 for pc in pcs if pc.status in {"offline", "atencao", "critico"})
        online = total - problemas
        resultado.append(
            {
                "id": lab.id,
                "nome": lab.nome,
                "localizacao": lab.localizacao,
                "status": lab.status,
                "iie": lab.iie,
                "equipamentos": total,
                "online": online,
                "problemas": problemas,
            }
        )

    register_audit(db, "LISTAR_LABORATORIOS", "laboratorio", current_user, request)
    return resultado


@app.post("/laboratorios", status_code=201)
def criar_laboratorio(
    dados: LaboratorioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "tecnico")),
):
    novo = Laboratory(
        nome=dados.nome.strip(),
        localizacao=dados.localizacao.strip(),
        status=dados.status,
        iie=None,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    register_audit(
        db,
        "CRIAR_LABORATORIO",
        "laboratorio",
        current_user,
        request,
        {"laboratorio_id": novo.id, "nome": novo.nome},
    )

    return {
        "id": novo.id,
        "nome": novo.nome,
        "localizacao": novo.localizacao,
        "status": novo.status,
        "iie": novo.iie,
        "equipamentos": 0,
        "online": 0,
        "problemas": 0,
    }


@app.get("/computadores")
def listar_computadores(
    request: Request,
    laboratorio_id: int | None = Query(default=None, gt=0),
    status: StatusComputador | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Computer).order_by(Computer.id)
    if laboratorio_id is not None:
        stmt = stmt.where(Computer.laboratorio_id == laboratorio_id)
    if status is not None:
        stmt = stmt.where(Computer.status == status)

    pcs = db.scalars(stmt).all()
    register_audit(db, "LISTAR_COMPUTADORES", "computador", current_user, request)
    return [
        {
            "id": pc.id,
            "hostname": pc.hostname,
            "ip": pc.ip,
            "laboratorio_id": pc.laboratorio_id,
            "status": pc.status,
            "cpu": pc.cpu,
            "ram": pc.ram,
            "disco": pc.disco,
            "ultima_coleta": pc.ultima_coleta,
        }
        for pc in pcs
    ]


@app.post("/computadores", status_code=201)
def criar_computador(
    dados: ComputadorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "tecnico")),
):
    """RN01: todo computador deve pertencer a um laboratório existente."""
    laboratorio = db.get(Laboratory, dados.laboratorio_id)

    if laboratorio is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "RN01: não é possível cadastrar o computador. "
                "O laboratório informado não existe."
            ),
        )

    hostname_existente = db.scalar(select(Computer).where(Computer.hostname == dados.hostname.strip()))
    if hostname_existente:
        raise HTTPException(status_code=409, detail="Já existe um computador com este hostname.")

    novo = Computer(
        hostname=dados.hostname.strip(),
        ip=dados.ip.strip(),
        laboratorio_id=dados.laboratorio_id,
        status=dados.status,
        cpu=dados.cpu,
        ram=dados.ram,
        disco=dados.disco,
        ultima_coleta="agora",
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    register_audit(
        db,
        "CRIAR_COMPUTADOR",
        "computador",
        current_user,
        request,
        {"computador_id": novo.id, "hostname": novo.hostname, "laboratorio_id": novo.laboratorio_id},
    )

    return {
        "id": novo.id,
        "hostname": novo.hostname,
        "ip": novo.ip,
        "laboratorio_id": novo.laboratorio_id,
        "status": novo.status,
        "cpu": novo.cpu,
        "ram": novo.ram,
        "disco": novo.disco,
        "ultima_coleta": novo.ultima_coleta,
        "laboratorio": laboratorio.nome,
    }


@app.get("/alertas")
def listar_alertas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    computadores = db.scalars(select(Computer).order_by(Computer.id)).all()
    alertas = []

    for pc in computadores:
        if pc.status == "offline":
            alertas.append(
                {
                    "computador": pc.hostname,
                    "tipo": "offline",
                    "mensagem": "Equipamento offline",
                    "hora": pc.ultima_coleta,
                }
            )
        elif pc.status in {"atencao", "critico"}:
            if pc.disco is not None and pc.disco >= 90:
                mensagem = f"Disco em {pc.disco}%"
            elif pc.ram is not None and pc.ram >= 90:
                mensagem = f"Uso de RAM em {pc.ram}%"
            elif pc.cpu is not None and pc.cpu >= 90:
                mensagem = f"CPU acima de {pc.cpu}%"
            else:
                mensagem = "Equipamento requer atenção"

            alertas.append(
                {
                    "computador": pc.hostname,
                    "tipo": pc.status,
                    "mensagem": mensagem,
                    "hora": pc.ultima_coleta,
                }
            )

    register_audit(db, "LISTAR_ALERTAS", "alerta", current_user, request)
    return alertas[:6]


@app.get("/indicadores")
def indicadores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    labs = db.scalars(select(Laboratory).order_by(Laboratory.id)).all()
    status = contar_status(db)
    valores_iie = [lab.iie for lab in labs if lab.iie is not None]
    return {
        "iie_medio": round(sum(valores_iie) / len(valores_iie), 1) if valores_iie else 0,
        "disponibilidade_percentual": round((status["online"] / status["total"]) * 100, 1) if status["total"] else 0,
        "laboratorios": [
            {"id": lab.id, "nome": lab.nome, "iie": lab.iie, "status": lab.status}
            for lab in labs
        ],
    }


@app.get("/relatorios/resumo")
def relatorio_resumo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    status = contar_status(db)
    labs = db.scalar(select(func.count(Laboratory.id))) or 0
    return {
        "laboratorios": labs,
        "computadores": status,
        "observacao": "Resumo acadêmico do estado atual da infraestrutura.",
    }


@app.get("/externo/cep/{cep}")
async def cep(
    cep: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resultado = await consultar_cep(cep)
    register_audit(
        db,
        "CONSULTAR_API_EXTERNA",
        "viacep",
        current_user,
        request,
        {"cep": resultado["cep"]},
    )
    return resultado


@app.get("/auditoria")
def auditoria(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    logs = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    resultado = []
    for log in logs:
        user = db.get(User, log.user_id) if log.user_id else None
        resultado.append(
            {
                "id": log.id,
                "usuario": user.email if user else "não autenticado",
                "acao": log.action,
                "entidade": log.entity,
                "detalhes": log.details,
                "ip": log.ip_address,
                "data_hora": log.created_at.isoformat(),
            }
        )
    return resultado


@app.get("/privacidade")
def privacidade():
    return {
        "projeto": "EDU-Infra Analytics",
        "finalidade": "Diagnóstico e acompanhamento da infraestrutura tecnológica escolar.",
        "dados_pessoais_previstos": ["nome", "e-mail", "perfil de acesso"],
        "dados_sensiveis_previstos": False,
        "observacao": (
            "Versão acadêmica. Em implantação real, a instituição deve definir "
            "controlador, base legal, prazos de retenção e canal para titulares."
        ),
    }
