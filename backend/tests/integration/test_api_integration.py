import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Computer, Laboratory, User
import app.security as security
from app.security import hash_password

security.JWT_SECRET_KEY = "chave-jwt-exclusiva-para-testes-automatizados-2026"


@pytest.fixture()
def db_session():
    # Banco real SQLite em memória, isolado e descartável para cada teste.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    session.add(
        User(
            id=1,
            name="Administrador de Teste",
            email="admin.teste@escola.edu",
            password_hash=hash_password("SenhaTeste123"),
            role="admin",
            is_active=True,
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    cliente = TestClient(app)
    try:
        yield cliente
    finally:
        app.dependency_overrides.clear()
        cliente.close()


def autenticar(client):
    resposta = client.post(
        "/auth/login",
        json={"email": "admin.teste@escola.edu", "password": "SenhaTeste123"},
    )
    assert resposta.status_code == 200
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_login_valido_retorna_200_token_e_usuario(client):
    # Arrange
    payload = {"email": "admin.teste@escola.edu", "password": "SenhaTeste123"}

    # Act
    resposta = client.post("/auth/login", json=payload)

    # Assert
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"]
    assert corpo["user"]["email"] == "admin.teste@escola.edu"
    assert corpo["user"]["role"] == "admin"


@pytest.mark.integration
def test_post_computadores_retorna_400_quando_laboratorio_nao_existe(client):
    # Arrange
    headers = autenticar(client)
    payload = {
        "hostname": "PC-SEM-LAB",
        "ip": "192.168.20.20",
        "laboratorio_id": 999,
        "status": "online",
    }

    # Act
    resposta = client.post("/computadores", json=payload, headers=headers)

    # Assert
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "RN01" in corpo["detail"]
    assert "laboratório informado não existe" in corpo["detail"]


@pytest.mark.integration
def test_persistencia_salva_e_recupera_laboratorio_no_sqlite(db_session):
    # Arrange
    laboratorio = Laboratory(
        nome="Laboratório de Integração",
        localizacao="Bloco T",
        status="ativo",
        iie=80,
    )

    # Act
    db_session.add(laboratorio)
    db_session.commit()
    db_session.refresh(laboratorio)
    recuperado = db_session.scalar(
        select(Laboratory).where(Laboratory.nome == "Laboratório de Integração")
    )

    # Assert
    assert recuperado is not None
    assert recuperado.id == laboratorio.id
    assert recuperado.localizacao == "Bloco T"
    assert recuperado.iie == 80


@pytest.mark.integration
def test_fluxo_completo_cria_laboratorio_computador_e_consulta_recurso(client, db_session):
    # Arrange
    headers = autenticar(client)

    # Act - API cria laboratório
    resposta_lab = client.post(
        "/laboratorios",
        json={
            "nome": "LAB Integração",
            "localizacao": "Bloco B - Sala 20",
            "status": "ativo",
        },
        headers=headers,
    )
    assert resposta_lab.status_code == 201
    laboratorio_id = resposta_lab.json()["id"]

    # Act - API cria computador vinculado ao laboratório
    resposta_pc = client.post(
        "/computadores",
        json={
            "hostname": "LABINT-PC01",
            "ip": "10.0.0.10",
            "laboratorio_id": laboratorio_id,
            "status": "online",
            "cpu": 25,
            "ram": 40,
            "disco": 55,
        },
        headers=headers,
    )
    assert resposta_pc.status_code == 201

    # Act - consulta pelo endpoint e também confirma persistência
    resposta_lista = client.get(
        f"/computadores?laboratorio_id={laboratorio_id}",
        headers=headers,
    )
    computador_banco = db_session.scalar(
        select(Computer).where(Computer.hostname == "LABINT-PC01")
    )

    # Assert
    assert resposta_lista.status_code == 200
    lista = resposta_lista.json()
    assert len(lista) == 1
    assert lista[0]["hostname"] == "LABINT-PC01"
    assert lista[0]["laboratorio_id"] == laboratorio_id
    assert computador_banco is not None
    assert computador_banco.ip == "10.0.0.10"
