import os
os.environ["DATABASE_URL"] = "sqlite:///./tests_configuration_only.db"
os.environ["JWT_SECRET_KEY"] = "tests-secret-key-32-characters-long-123"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_con, record):
        dbapi_con.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for name, role in [("Admin", "admin"), ("Tecnico", "tecnico"), ("Gestor", "gestor")]:
            db.add(User(name=name, email=f"{role}@example.org", password_hash=hash_password("SenhaFortissima123"), role=role))
        db.commit()

    def override_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def headers(client):
    def login(role="admin"):
        result = client.post("/api/v1/auth/login", json={"email": f"{role}@example.org", "password": "SenhaFortissima123"})
        assert result.status_code == 200
        return {"Authorization": f"Bearer {result.json()['access_token']}"}
    return login
