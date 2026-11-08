from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core import hash_password, session
from app.models import Base, SystemSetting, TermDocument, User


@pytest.fixture
def client():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as db:
        db.add(TermDocument(version="1.0", title="Termos e Condições de Uso", content="Documento de aceite 1.0" * 15, active=True, published_at=datetime.now(timezone.utc)))
        db.add(SystemSetting(id=1, cpu_alert_threshold=90, memory_alert_threshold=90, disk_alert_threshold=90, stale_after_seconds=600))
        for role, name in [("ADMIN", "Admin"), ("TECNICO", "Tecnico"), ("GESTOR", "Gestor")]:
            db.add(User(name=name, email=f"{name.lower()}@example.org", password_hash=hash_password("TestPassword1234!"), role=role))
        db.commit()
    def override():
        with Session() as db:
            yield db
    app.dependency_overrides[session] = override
    with TestClient(app) as client:
        client.Session = Session
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def auth(client, role="ADMIN", accept=True):
    email = {"ADMIN": "admin", "TECNICO": "tecnico", "GESTOR": "gestor"}[role] + "@example.org"
    login = client.post("/api/auth/login", json={"email": email, "password": "TestPassword1234!"})
    assert login.status_code == 200, login.text
    header = {"Authorization": "Bearer " + login.json()["access_token"]}
    if accept:
        response = client.post("/api/terms/accept", json={"version": "1.0", "accepted": True}, headers=header)
        assert response.status_code == 200, response.text
        header = {"Authorization": "Bearer " + response.json()["access_token"]}
    return header


def lab(client, header, name="Laboratório A", location="Bloco 1"):
    result = client.post("/api/laboratories", json={"name":name,"location":location,"active":True}, headers=header)
    assert result.status_code == 201, result.text
    return result.json()


def pc(client, header, lab_id, name="VM 01", hostname="VM-01"):
    result = client.post("/api/computers", json={"laboratory_id":lab_id,"name":name,"hostname":hostname,"active":True}, headers=header)
    assert result.status_code == 201, result.text
    return result.json()


def measurement(cpu=40, ram=50, disk=60, stamp=None, os_name="Windows Server"):
    return {"cpu_percent":cpu,"memory_percent":ram,"disk_percent":disk,"uptime_seconds":3600,"os_name":os_name,"collected_at":(stamp or datetime.now(timezone.utc)).isoformat()}


def setup_agent(client, header):
    l = lab(client, header)
    c = pc(client, header, l["id"])
    raw = client.post(f"/api/computers/{c['id']}/token", headers=header).json()["agent_token"]
    return l, c, {"X-Computer-ID":str(c["id"]),"X-Agent-Token":raw}
