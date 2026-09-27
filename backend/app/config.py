import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    """Retorna a URL do banco.

    Para facilitar o desenvolvimento, se DATABASE_URL estiver vazia o projeto
    usa SQLite local. Em produção/entrega, basta informar a URL do PostgreSQL
    do Supabase no arquivo .env.
    """
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        return "sqlite:///./edu_infra.db"
    return value


DATABASE_URL = get_database_url()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "troque-esta-chave-em-producao")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@escola.edu")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
