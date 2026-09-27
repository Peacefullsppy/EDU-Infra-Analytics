from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


url = DATABASE_URL
engine_options = {"pool_pre_ping": True}

if url.startswith("postgresql://"):
    # Usa o driver psycopg 3 instalado pelo requirements.txt.
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)

if url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Importa os modelos antes do create_all para registrá-los no metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
