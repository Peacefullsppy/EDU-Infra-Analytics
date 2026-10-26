from datetime import datetime
from ipaddress import ip_address
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["admin", "tecnico", "gestor"]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: Role
    is_active: bool


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class LoginOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LaboratoryInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=160)
    is_active: bool = True

    @field_validator("name", "location")
    @classmethod
    def strip_nonempty(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Informe ao menos dois caracteres")
        return value


class LaboratoryRead(LaboratoryInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    computer_count: int = 0


class ComputerInput(BaseModel):
    hostname: str = Field(min_length=2, max_length=100)
    ip_address: str | None = None
    laboratory_id: int = Field(gt=0)

    @field_validator("hostname")
    @classmethod
    def normalize_hostname(cls, value):
        value = value.strip().upper()
        if len(value) < 2 or any(c.isspace() for c in value):
            raise ValueError("Hostname deve ter ao menos dois caracteres e não conter espaços")
        return value

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, value):
        if not value:
            return None
        return str(ip_address(value))


class ComputerRead(ComputerInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: Literal["sem_coleta", "online", "offline", "atencao", "critico"]
    cpu_percent: int | None = None
    ram_percent: int | None = None
    disk_percent: int | None = None
    last_seen_at: datetime | None = None


class UserState(BaseModel):
    is_active: bool
