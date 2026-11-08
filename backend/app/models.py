from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="GESTOR")
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Laboratory(Base):
    __tablename__ = "laboratories"
    __table_args__ = (UniqueConstraint("name_key", "location_key", name="uq_laboratory_normalized"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(180), nullable=False)
    name_key: Mapped[str] = mapped_column(String(120), nullable=False)
    location_key: Mapped[str] = mapped_column(String(180), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    computers: Mapped[list[Computer]] = relationship(back_populates="laboratory", passive_deletes=True)


class Computer(Base):
    __tablename__ = "computers"
    __table_args__ = (
        UniqueConstraint("laboratory_id", "hostname", name="uq_computer_lab_hostname"),
        UniqueConstraint("hyperv_vm_id", name="uq_computer_hyperv_vm_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    laboratory_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    hostname: Mapped[str] = mapped_column(String(120), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(48))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    hyperv_vm_id: Mapped[str | None] = mapped_column(String(80))
    hyperv_state: Mapped[str | None] = mapped_column(String(32))
    agent_token_hash: Mapped[str | None] = mapped_column(String(64))
    agent_token_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    laboratory: Mapped[Laboratory] = relationship(back_populates="computers")
    metrics: Mapped[list[Metric]] = relationship(back_populates="computer", cascade="all, delete", passive_deletes=True)


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (Index("ix_metric_computer_collected", "computer_id", "collected_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    computer_id: Mapped[int] = mapped_column(ForeignKey("computers.id", ondelete="CASCADE"), nullable=False)
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    memory_percent: Mapped[float] = mapped_column(Float, nullable=False)
    disk_percent: Mapped[float] = mapped_column(Float, nullable=False)
    uptime_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    os_name: Mapped[str] = mapped_column(String(180), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    computer: Mapped[Computer] = relationship(back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alert_computer_status", "computer_id", "status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    computer_id: Mapped[int] = mapped_column(ForeignKey("computers.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(25), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), default="warning", nullable=False)
    message: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TermDocument(Base):
    __tablename__ = "term_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TermAcceptance(Base):
    __tablename__ = "term_acceptances"
    __table_args__ = (UniqueConstraint("user_id", "terms_id", name="uq_user_terms"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    terms_id: Mapped[int] = mapped_column(ForeignKey("term_documents.id", ondelete="RESTRICT"), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"
    __table_args__ = (Index("ix_indicator_lab_calculated", "laboratory_id", "calculated_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    laboratory_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    coverage: Mapped[float] = mapped_column(Float, nullable=False)
    online: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    cpu_alert_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    memory_alert_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    disk_alert_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    stale_after_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
