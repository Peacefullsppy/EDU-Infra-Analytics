from typing import Literal

from pydantic import BaseModel, EmailStr, Field


StatusLaboratorio = Literal["ativo", "inativo"]
StatusComputador = Literal["online", "atencao", "critico", "offline"]
PerfilUsuario = Literal["admin", "tecnico", "gestor"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: PerfilUsuario


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


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
