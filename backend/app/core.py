from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Generator

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, User, TermDocument, TermAcceptance


class Settings(BaseSettings):
    database_url: str = "sqlite:///./edu_infra_dev.db"
    jwt_secret_key: str = "LOCAL-ONLY-CHANGE-ME-DO-NOT-USE-IN-PRODUCTION"
    jwt_expire_minutes: int = 120
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    require_https: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def sqlite_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=2)
bearer = HTTPBearer(auto_error=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def session() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("A senha deve ter pelo menos 12 caracteres")
    return hasher.hash(password)


def verify_password(secret: str, encoded: str) -> bool:
    try:
        return hasher.verify(encoded, secret)
    except (VerifyMismatchError, VerificationError, ValueError):
        return False


def agent_token_hash(token: str) -> str:
    return hmac.new(settings.jwt_secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


def issue_agent_token() -> tuple[str, str]:
    token = "eia_" + secrets.token_urlsafe(40)
    return token, agent_token_hash(token)


def create_access_token(user: User, terms_version: str | None = None) -> str:
    # A cada login o token nasce sem confirmação de termos; aceite emite novo token.
    now = utcnow()
    return jwt.encode({"sub": str(user.id), "type": "access", "terms_version": terms_version, "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}, settings.jwt_secret_key, algorithm="HS256")


def user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options={"require": ["exp", "sub", "iat"]})
        if payload.get("type") != "access":
            raise ValueError("Tipo de token inválido")
        uid = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado") from exc
    user = db.get(User, uid)
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo ou inexistente")
    return user


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(session)) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação necessária")
    return user_from_token(credentials.credentials, db)


def current_terms(db: Session) -> TermDocument | None:
    return db.scalar(select(TermDocument).where(TermDocument.active.is_(True)).order_by(TermDocument.published_at.desc(), TermDocument.id.desc()))


def terms_accepted(db: Session, user: User) -> bool:
    doc = current_terms(db)
    if doc is None:
        return False
    return db.scalar(select(TermAcceptance.id).where(TermAcceptance.user_id == user.id, TermAcceptance.terms_id == doc.id)) is not None


def accepted_in_session(db: Session, user: User, token: str) -> bool:
    doc = current_terms(db)
    if not doc or not terms_accepted(db, user):
        return False
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload.get("terms_version") == doc.version
    except jwt.PyJWTError:
        return False


def accepted_user(user: User = Depends(current_user), credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(session)) -> User:
    if not credentials or not accepted_in_session(db, user, credentials.credentials):
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED, "Confirme os Termos e Condições vigentes nesta sessão para continuar")
    return user


def can(*roles: str):
    def dependency(user: User = Depends(accepted_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão insuficiente")
        return user
    return dependency


def audit(db: Session, actor_id: int | None, action: str, entity: str, entity_id: int | None = None, details: str = ""):
    from .models import AuditLog
    db.add(AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, details=details[:1000]))


def validate_startup():
    # Evita credencial padrão em ambientes configurados para HTTPS.
    if settings.require_https and (settings.jwt_secret_key.startswith("LOCAL-ONLY") or len(settings.jwt_secret_key) < 32):
        raise RuntimeError("Defina JWT_SECRET_KEY forte antes de ativar REQUIRE_HTTPS")
