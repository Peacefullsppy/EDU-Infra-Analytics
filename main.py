import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.audit import registrar_auditoria
from app.database import get_db, init_db
from app.external import consultar_cep
from app.models import AuditLog, Computer, Laboratory, User
from app.schemas import (
    AuditLogOut,
    CepOut,
    ComputadorCreate,
    LaboratorioCreate,
    StatusComputador,
    Token,
    UserCreate,
    UserOut,
)
from app.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EDU-Infra Analytics API",
    version="0.2.0",
    description=(
        "Etapa com PostgreSQL/Supabase, autenticação JWT, auditoria, "
        "LGPD e integração externa ViaCEP."
    ),
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def laboratorio_para_dict(lab: Laboratory):
    pcs = lab.computadores
    total = len(pcs)
    problemas = sum(1 for pc in pcs if pc.status in {"offline", "atencao", "critico"})
    online = total - problemas
    return {
        "id": lab.id,
        "nome": lab.nome,
        "localizacao": lab.localizacao,
        "status": lab.status,
        "iie": lab.iie,
        "equipamentos": total,
        "online": online,
        "problemas": problemas,
    }


def computador_para_dict(pc: Computer):
    return {
        "id": pc.id,
        "hostname": pc.hostname,
        "ip": pc.ip,
        "laboratorio_id": pc.laboratorio_id,
        "status": pc.status,
        "cpu": pc.cpu,
        "ram": pc.ram,
        "disco": pc.disco,
        "ultima_coleta": (
            pc.ultima_coleta.astimezone(timezone.utc).strftime("%H:%M")
            if pc.ultima_coleta
            else "--"
        ),
    }


@app.get("/")
def root():
    return {"message": "EDU-Infra Analytics API funcionando", "version": "0.2.0"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "conectado"}


@app.post("/auth/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username.lower().strip()
    user = authenticate_user(db, email, form_data.password)

    if user is None:
        registrar_auditoria(
            db,
            user=None,
            acao="LOGIN_FALHOU",
            recurso="autenticacao",
            request=request,
            detalhes={"motivo": "credenciais_invalidas"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user)
    registrar_auditoria(
        db,
        user=user,
        acao="LOGIN_SUCESSO",
        recurso="autenticacao",
        request=request,
    )
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/auth/users", response_model=UserOut, status_code=201)
def criar_usuario(
    dados: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    email = dados.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Já existe um usuário com este e-mail.")

    user = User(
        nome=dados.nome.strip(),
        email=email,
        password_hash=hash_password(dados.password),
        role=dados.role,
        ativo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    registrar_auditoria(
        db,
        user=current_user,
        acao="CRIAR_USUARIO",
        recurso="usuarios",
        recurso_id=user.id,
        request=request,
        detalhes={"role": user.role},
    )
    return user


@app.get("/dashboard")
def obter_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pcs = db.scalars(select(Computer)).all()
    labs = db.scalars(select(Laboratory)).all()

    total = len(pcs)
    offline = sum(1 for pc in pcs if pc.status == "offline")
    atencao = sum(1 for pc in pcs if pc.status in {"atencao", "critico"})
    online = total - offline
    iies = [lab.iie for lab in labs if lab.iie is not None]
    iie_geral = round(sum(iies) / len(iies)) if iies else 0

    registrar_auditoria(
        db,
        user=current_user,
        acao="VISUALIZAR_DASHBOARD",
        recurso="dashboard",
        request=request,
    )

    return {
        "iie_geral": iie_geral,
        "computadores": {"total": total, "online": online, "offline": offline, "atencao": atencao},
        "alertas": atencao,
    }


@app.get("/laboratorios")
def listar_laboratorios(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    labs = db.scalars(
        select(Laboratory).options(selectinload(Laboratory.computadores)).order_by(Laboratory.id)
    ).all()

    registrar_auditoria(
        db,
        user=current_user,
        acao="LISTAR_LABORATORIOS",
        recurso="laboratorios",
        request=request,
    )
    return [laboratorio_para_dict(lab) for lab in labs]


@app.post("/laboratorios", status_code=201)
def criar_laboratorio(
    dados: LaboratorioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "tecnico")),
):
    lab = Laboratory(
        nome=dados.nome.strip(),
        localizacao=dados.localizacao.strip(),
        status=dados.status,
        iie=None,
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)

    registrar_auditoria(
        db,
        user=current_user,
        acao="CRIAR_LABORATORIO",
        recurso="laboratorios",
        recurso_id=lab.id,
        request=request,
        detalhes={"nome": lab.nome},
    )

    return {
        "id": lab.id,
        "nome": lab.nome,
        "localizacao": lab.localizacao,
        "status": lab.status,
        "iie": lab.iie,
    }


@app.get("/computadores")
def listar_computadores(
    request: Request,
    laboratorio_id: int | None = Query(default=None, gt=0),
    status_filtro: StatusComputador | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Computer).order_by(Computer.id)
    if laboratorio_id is not None:
        stmt = stmt.where(Computer.laboratorio_id == laboratorio_id)
    if status_filtro is not None:
        stmt = stmt.where(Computer.status == status_filtro)

    pcs = db.scalars(stmt).all()
    registrar_auditoria(
        db,
        user=current_user,
        acao="LISTAR_COMPUTADORES",
        recurso="computadores",
        request=request,
    )
    return [computador_para_dict(pc) for pc in pcs]


@app.post("/computadores", status_code=201)
def criar_computador(
    dados: ComputadorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "tecnico")),
):
    # RN01: todo computador deve pertencer a um laboratório existente.
    laboratorio = db.get(Laboratory, dados.laboratorio_id)
    if laboratorio is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "RN01: não é possível cadastrar o computador. "
                "O laboratório informado não existe."
            ),
        )

    if db.scalar(select(Computer).where(Computer.hostname == dados.hostname.strip())):
        raise HTTPException(status_code=409, detail="Já existe um computador com este hostname.")

    computador = Computer(
        hostname=dados.hostname.strip(),
        ip=dados.ip.strip(),
        laboratorio_id=dados.laboratorio_id,
        status=dados.status,
        cpu=dados.cpu,
        ram=dados.ram,
        disco=dados.disco,
        ultima_coleta=datetime.now(timezone.utc),
    )
    db.add(computador)
    db.commit()
    db.refresh(computador)

    registrar_auditoria(
        db,
        user=current_user,
        acao="CRIAR_COMPUTADOR",
        recurso="computadores",
        recurso_id=computador.id,
        request=request,
        detalhes={"laboratorio_id": computador.laboratorio_id},
    )

    return {**computador_para_dict(computador), "laboratorio": laboratorio.nome}


@app.get("/alertas")
def listar_alertas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pcs = db.scalars(select(Computer).order_by(Computer.id)).all()
    alertas = []

    for pc in pcs:
        if pc.status == "offline":
            mensagem = "Equipamento offline"
        elif pc.status in {"atencao", "critico"}:
            if pc.disco is not None and pc.disco >= 90:
                mensagem = f"Disco em {pc.disco}%"
            elif pc.ram is not None and pc.ram >= 90:
                mensagem = f"Uso de RAM em {pc.ram}%"
            elif pc.cpu is not None and pc.cpu >= 90:
                mensagem = f"CPU acima de {pc.cpu}%"
            else:
                mensagem = "Equipamento requer atenção"
        else:
            continue

        alertas.append(
            {
                "computador": pc.hostname,
                "tipo": pc.status,
                "mensagem": mensagem,
                "hora": pc.ultima_coleta.strftime("%H:%M") if pc.ultima_coleta else "--",
            }
        )

    registrar_auditoria(
        db,
        user=current_user,
        acao="LISTAR_ALERTAS",
        recurso="alertas",
        request=request,
    )
    return alertas[:6]


@app.get("/integracoes/cep/{cep}", response_model=CepOut)
async def buscar_cep(
    cep: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resultado = await consultar_cep(cep)
    registrar_auditoria(
        db,
        user=current_user,
        acao="CONSULTAR_API_EXTERNA",
        recurso="viacep",
        request=request,
        detalhes={"cep": resultado["cep"]},
    )
    return resultado


@app.get("/auditoria", response_model=list[AuditLogOut])
def listar_auditoria(
    limite: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    logs = db.scalars(
        select(AuditLog)
        .options(selectinload(AuditLog.usuario))
        .order_by(AuditLog.criado_em.desc())
        .limit(limite)
    ).all()

    return [
        AuditLogOut(
            id=log.id,
            usuario=log.usuario.nome if log.usuario else None,
            role=log.usuario.role if log.usuario else None,
            acao=log.acao,
            recurso=log.recurso,
            recurso_id=log.recurso_id,
            metodo=log.metodo,
            caminho=log.caminho,
            detalhes=log.detalhes,
            criado_em=log.criado_em,
        )
        for log in logs
    ]


@app.get("/legal/lgpd")
def informacoes_lgpd():
    return {
        "versao": "1.0",
        "titulo": "Política de Privacidade e Termo de Uso",
        "dados_pessoais": ["nome", "e-mail", "perfil de acesso"],
        "finalidades": [
            "autenticação e controle de acesso",
            "registro de auditoria das ações realizadas",
            "operação e segurança do sistema",
        ],
        "dados_sensiveis": "O MVP não prevê a coleta de dados pessoais sensíveis de alunos ou professores.",
        "principios": ["finalidade", "necessidade", "transparência", "segurança", "prevenção"],
        "observacao": (
            "Em uma implantação institucional real, a instituição controladora deverá "
            "definir os canais de atendimento, bases legais aplicáveis e prazos formais de retenção."
        ),
    }
