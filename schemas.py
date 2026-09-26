from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

StatusLaboratorio = Literal["ativo", "inativo"]
StatusComputador = Literal["online", "atencao", "critico", "offline"]
RoleUsuario = Literal["admin", "tecnico", "gestor"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RoleUsuario = "gestor"


class UserOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: str
    ativo: bool

    model_config = {"from_attributes": True}


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


class AuditLogOut(BaseModel):
    id: int
    usuario: str | None
    role: str | None
    acao: str
    recurso: str
    recurso_id: str | None
    metodo: str | None
    caminho: str | None
    detalhes: dict | None
    criado_em: datetime


class CepOut(BaseModel):
    cep: str
    logradouro: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str
    uf: str
    ibge: str | None = None
