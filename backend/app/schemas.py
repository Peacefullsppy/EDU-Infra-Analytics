from __future__ import annotations

from datetime import datetime
from ipaddress import ip_address
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Literal


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Login(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Literal["ADMIN", "TECNICO", "GESTOR"] = "GESTOR"

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Informe um nome válido")
        return value


class UserOut(Out):
    id: int
    name: str
    email: EmailStr
    role: str
    active: bool
    created_at: datetime


class LabIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=180)
    active: bool = True

    @field_validator("name", "location")
    @classmethod
    def nonempty_lab_fields(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Nome e localização devem conter texto válido")
        return value


class LabOut(Out):
    id: int
    name: str
    location: str
    active: bool
    created_at: datetime


class ComputerIn(BaseModel):
    laboratory_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    hostname: str = Field(min_length=1, max_length=120)
    ip_address: str | None = None
    active: bool = True

    @field_validator("name", "hostname")
    @classmethod
    def nonempty_computer_fields(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Informe um nome ou hostname válido")
        return value

    @field_validator("ip_address")
    @classmethod
    def valid_ip(cls, value):
        if not value:
            return None
        return str(ip_address(value))


class ComputerOut(Out):
    id: int
    laboratory_id: int
    name: str
    hostname: str
    ip_address: str | None
    active: bool
    source: str
    hyperv_vm_id: str | None
    hyperv_state: str | None
    last_seen_at: datetime | None
    created_at: datetime


class MetricIn(BaseModel):
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    uptime_seconds: float = Field(ge=0)
    os_name: str = Field(min_length=2, max_length=180)
    collected_at: datetime

    @field_validator("collected_at")
    @classmethod
    def date_with_timezone(cls, value):
        if not value.tzinfo:
            raise ValueError("collected_at deve ter fuso horário")
        return value


class MetricOut(Out):
    id: int
    computer_id: int
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: float
    os_name: str
    collected_at: datetime


class AlertOut(Out):
    id: int
    computer_id: int
    type: str
    severity: str
    message: str
    status: str
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None


class SettingsIn(BaseModel):
    cpu_alert_threshold: int = Field(ge=50, le=100)
    memory_alert_threshold: int = Field(ge=50, le=100)
    disk_alert_threshold: int = Field(ge=50, le=100)
    stale_after_seconds: int = Field(ge=60, le=86400)


class TermsPublish(BaseModel):
    version: str = Field(min_length=1, max_length=32, pattern=r"^[0-9A-Za-z._-]+$")
    title: str = Field(min_length=5, max_length=180)
    content: str = Field(min_length=150, max_length=50000)

    @field_validator("title", "content")
    @classmethod
    def legal_text_cannot_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("O documento deve conter texto")
        return value


class AcceptTerms(BaseModel):
    version: str
    accepted: Literal[True]


class HyperVEntry(BaseModel):
    vm_id: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=32)

    @field_validator("vm_id", "name", "state")
    @classmethod
    def nonempty_vm_fields(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Identificação da VM não pode estar em branco")
        return value


class HyperVImport(BaseModel):
    laboratory_id: int = Field(gt=0)
    vms: list[HyperVEntry] = Field(min_length=1, max_length=100)
