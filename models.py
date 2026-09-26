from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="gestor", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    auditorias: Mapped[list[AuditLog]] = relationship(back_populates="usuario")


class Laboratory(Base):
    __tablename__ = "laboratories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    localizacao: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ativo", nullable=False)
    iie: Mapped[float | None] = mapped_column(Float, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    computadores: Mapped[list[Computer]] = relationship(
        back_populates="laboratorio",
        cascade="all, delete-orphan",
    )


class Computer(Base):
    __tablename__ = "computers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    laboratorio_id: Mapped[int] = mapped_column(
        ForeignKey("laboratories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="online", nullable=False)
    cpu: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ram: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disco: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ultima_coleta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    laboratorio: Mapped[Laboratory] = relationship(back_populates="computadores")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acao: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    recurso: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recurso_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    metodo: Mapped[str | None] = mapped_column(String(12), nullable=True)
    caminho: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detalhes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    usuario: Mapped[User | None] = relationship(back_populates="auditorias")
