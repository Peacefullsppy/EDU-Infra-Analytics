from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(
    title="EDU-Infra Analytics API",
    version="0.1.0",
    description="MVP da primeira regra de negócio do EDU-Infra Analytics."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

StatusLaboratorio = Literal["ativo", "inativo"]
StatusComputador = Literal["online", "atencao", "critico", "offline"]


class LaboratorioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    localizacao: str = Field(min_length=2, max_length=120)
    status: StatusLaboratorio = "ativo"


class ComputadorCreate(BaseModel):
    hostname: str = Field(min_length=2, max_length=80)
    ip: str = Field(min_length=7, max_length=45)
    laboratorio_id: int = Field(gt=0)
    status: StatusComputador = "online"
    cpu: int | None = Field(default=None, ge=0, le=100)
    ram: int | None = Field(default=None, ge=0, le=100)
    disco: int | None = Field(default=None, ge=0, le=100)


# Dados temporários em memória.
# Nesta primeira etapa ainda não usamos PostgreSQL.
laboratorios = [
    {"id": 1, "nome": "LAB 01", "localizacao": "Informática 1", "status": "ativo", "iie": 91},
    {"id": 2, "nome": "LAB 02", "localizacao": "Informática 2", "status": "ativo", "iie": 78},
    {"id": 3, "nome": "LAB 03", "localizacao": "Informática 3", "status": "ativo", "iie": 64},
]


def _gerar_computadores_demo():
    dados = []
    configuracao = {
        1: {"total": 20, "offline": set(), "atencao": {2}, "critico": set()},
        2: {"total": 25, "offline": {11}, "atencao": {8, 12}, "critico": set()},
        3: {"total": 15, "offline": {7}, "atencao": {9, 10}, "critico": {4}},
    }

    id_atual = 1

    for laboratorio_id, config in configuracao.items():
        for numero in range(1, config["total"] + 1):
            if numero in config["offline"]:
                status = "offline"
                cpu = ram = disco = None
            elif numero in config["critico"]:
                status = "critico"
                cpu, ram, disco = 84, 76, 96
            elif numero in config["atencao"]:
                status = "atencao"
                if laboratorio_id == 1 and numero == 2:
                    cpu, ram, disco = 92, 87, 70
                elif laboratorio_id == 2 and numero == 8:
                    cpu, ram, disco = 45, 93, 67
                else:
                    cpu, ram, disco = 88, 81, 74
            else:
                status = "online"
                cpu = 24 + ((numero * 7 + laboratorio_id * 5) % 42)
                ram = 38 + ((numero * 5 + laboratorio_id * 7) % 30)
                disco = 45 + ((numero * 3 + laboratorio_id * 11) % 28)

            dados.append({
                "id": id_atual,
                "hostname": f"LAB{laboratorio_id:02d}-PC{numero:02d}",
                "ip": f"192.168.{laboratorio_id}.{100 + numero}",
                "laboratorio_id": laboratorio_id,
                "status": status,
                "cpu": cpu,
                "ram": ram,
                "disco": disco,
                "ultima_coleta": "09:20" if status != "offline" else "07:55",
            })
            id_atual += 1

    return dados


computadores = _gerar_computadores_demo()


def buscar_laboratorio_por_id(laboratorio_id: int):
    return next((lab for lab in laboratorios if lab["id"] == laboratorio_id), None)


def contar_status():
    total = len(computadores)
    offline = sum(1 for pc in computadores if pc["status"] == "offline")
    atencao = sum(1 for pc in computadores if pc["status"] in {"atencao", "critico"})
    online = total - offline
    return {"total": total, "online": online, "offline": offline, "atencao": atencao}


@app.get("/")
def root():
    return {"message": "EDU-Infra Analytics API funcionando"}


@app.get("/dashboard")
def obter_dashboard():
    status = contar_status()
    return {"iie_geral": 82, "computadores": status, "alertas": status["atencao"]}


@app.get("/laboratorios")
def listar_laboratorios():
    resultado = []
    for laboratorio in laboratorios:
        pcs = [pc for pc in computadores if pc["laboratorio_id"] == laboratorio["id"]]
        total = len(pcs)
        problemas = sum(1 for pc in pcs if pc["status"] in {"offline", "atencao", "critico"})
        online = total - problemas
        resultado.append({**laboratorio, "equipamentos": total, "online": online, "problemas": problemas})
    return resultado


@app.post("/laboratorios", status_code=201)
def criar_laboratorio(dados: LaboratorioCreate):
    novo_id = max((lab["id"] for lab in laboratorios), default=0) + 1
    novo_laboratorio = {
        "id": novo_id,
        "nome": dados.nome.strip(),
        "localizacao": dados.localizacao.strip(),
        "status": dados.status,
        "iie": None,
    }
    laboratorios.append(novo_laboratorio)
    return novo_laboratorio


@app.get("/computadores")
def listar_computadores(
    laboratorio_id: int | None = Query(default=None, gt=0),
    status: StatusComputador | None = None,
):
    resultado = computadores
    if laboratorio_id is not None:
        resultado = [pc for pc in resultado if pc["laboratorio_id"] == laboratorio_id]
    if status is not None:
        resultado = [pc for pc in resultado if pc["status"] == status]
    return resultado


@app.post("/computadores", status_code=201)
def criar_computador(dados: ComputadorCreate):
    """RN01: todo computador deve pertencer a um laboratório existente."""
    laboratorio = buscar_laboratorio_por_id(dados.laboratorio_id)

    # PRIMEIRA REGRA DE NEGÓCIO
    if laboratorio is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "RN01: não é possível cadastrar o computador. "
                "O laboratório informado não existe."
            ),
        )

    novo_id = max((pc["id"] for pc in computadores), default=0) + 1
    novo_computador = {
        "id": novo_id,
        "hostname": dados.hostname.strip(),
        "ip": dados.ip.strip(),
        "laboratorio_id": dados.laboratorio_id,
        "status": dados.status,
        "cpu": dados.cpu,
        "ram": dados.ram,
        "disco": dados.disco,
        "ultima_coleta": "agora",
    }
    computadores.append(novo_computador)
    return {**novo_computador, "laboratorio": laboratorio["nome"]}


@app.get("/alertas")
def listar_alertas():
    alertas = []
    for pc in computadores:
        if pc["status"] == "offline":
            alertas.append({
                "computador": pc["hostname"],
                "tipo": "offline",
                "mensagem": "Equipamento offline",
                "hora": pc["ultima_coleta"],
            })
        elif pc["status"] in {"atencao", "critico"}:
            if pc["disco"] is not None and pc["disco"] >= 90:
                mensagem = f"Disco em {pc['disco']}%"
            elif pc["ram"] is not None and pc["ram"] >= 90:
                mensagem = f"Uso de RAM em {pc['ram']}%"
            elif pc["cpu"] is not None and pc["cpu"] >= 90:
                mensagem = f"CPU acima de {pc['cpu']}%"
            else:
                mensagem = "Equipamento requer atenção"
            alertas.append({
                "computador": pc["hostname"],
                "tipo": pc["status"],
                "mensagem": mensagem,
                "hora": pc["ultima_coleta"],
            })
    return alertas[:6]
