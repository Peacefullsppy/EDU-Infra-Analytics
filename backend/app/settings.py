import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings():
    database_url = os.getenv("DATABASE_URL", "").strip()
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not database_url:
        raise RuntimeError("Defina DATABASE_URL no arquivo .env")
    if len(secret) < 32 or "SUBSTITUA" in secret.upper():
        raise RuntimeError("JWT_SECRET_KEY deve ter pelo menos 32 caracteres")
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]
    cors = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
    return {"database_url": database_url, "secret": secret, "cors_origins": cors}
