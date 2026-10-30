"""HTTP via socket TCP real em porta aleatória (equivalente a RANDOM_PORT)."""
import socket
from threading import Event, Thread
from uuid import uuid4

import httpx
import pytest
import uvicorn
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db import Base, get_engine
from app.main import app
from app.models import Laboratory, User
from app.security import hash_password
from app.settings import get_settings

SENHA = "SenhaFortissima123"


@pytest.fixture()
def http_real(tmp_path, monkeypatch):
    """Isola totalmente a aplicação e exercita ASGI sobre TCP; sem mocks de camadas."""
    banco = tmp_path / "http_real.db"
    banco_url = f"sqlite:///{banco}"
    monkeypatch.setenv("DATABASE_URL", banco_url)
    monkeypatch.setenv("JWT_SECRET_KEY", "http-test-secret-key-with-more-than-32-characters")
    get_engine.cache_clear()
    get_settings.cache_clear()

    engine = create_engine(banco_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def habilitar_chaves_estrangeiras(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    email_admin = f"admin-{uuid4().hex}@example.org"
    with Session(engine) as db:
        db.add(User(name="Administrador de integração", email=email_admin,
                    password_hash=hash_password(SENHA), role="admin"))
        db.commit()

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    porta = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=porta, log_level="error", lifespan="off"
    ))
    thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    stop_event = Event()
    try:
        # Aguarda a inicialização com Event.wait, sem sleeps arbitrários.
        while not server.started and thread.is_alive():
            stop_event.wait(0.01)
        assert server.started, "Servidor HTTP da suíte não iniciou"
        with httpx.Client(base_url=f"http://127.0.0.1:{porta}", timeout=5, trust_env=False) as client:
            response = client.post("/api/v1/auth/login", json={
                "email": email_admin, "password": SENHA
            })
            assert response.status_code == 200, response.text
            assert response.json()["user"]["email"] == email_admin
            token = response.json()["access_token"]
            yield client, {"Authorization": f"Bearer {token}"}, engine
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        assert not thread.is_alive(), "Servidor HTTP não finalizou"
        listener.close()
        engine.dispose()
        get_engine.cache_clear()
        get_settings.cache_clear()


def test_http_real_criar_e_buscar_laboratorio_retorna_201_200_e_persiste(http_real):
    # Arrange
    client, auth, engine = http_real
    dados = {"name": f"Lab TCP {uuid4().hex[:10]}", "location": "Sala 101", "is_active": True}
    # Act
    criado = client.post("/api/v1/laboratorios", json=dados, headers=auth)
    # Assert (corpo + estado persistido verificado independentemente do HTTP)
    assert criado.status_code == 201
    body = criado.json()
    assert body["id"] > 0
    assert body["name"] == dados["name"]
    assert body["location"] == dados["location"]
    assert body["computer_count"] == 0
    busca = client.get(f"/api/v1/laboratorios/{body['id']}", headers=auth)
    assert busca.status_code == 200
    assert busca.json() == body
    with Session(engine) as db:
        registro = db.get(Laboratory, body["id"])
        assert registro is not None and registro.name == dados["name"]


def test_http_real_criar_computador_sem_laboratorio_retorna_404_com_mensagem(http_real):
    # Arrange
    client, auth, _engine = http_real
    dados = {"hostname": f"PC-{uuid4().hex[:10]}", "laboratory_id": 999999}
    # Act
    response = client.post("/api/v1/computadores", json=dados, headers=auth)
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Laboratório não encontrado"}
