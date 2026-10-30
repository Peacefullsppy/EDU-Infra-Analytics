"""Integração do recurso Laboratórios: HTTP -> JWT/RBAC -> ORM -> SQLite."""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Laboratory

BASE = "/api/v1/laboratorios"


def dados_laboratorio(**mudancas):
    dados = {"name": f"Laboratório {uuid4().hex[:12]}", "location": "Bloco de Engenharia", "is_active": True}
    return {**dados, **mudancas}


def criar_laboratorio(client, headers, **mudancas):
    response = client.post(BASE, headers=headers, json=dados_laboratorio(**mudancas))
    assert response.status_code == 201, response.text
    return response.json()


def test_listar_laboratorios_sem_cadastros_retorna_200_e_lista_vazia(client, headers):
    # Arrange: banco criado exclusivamente para este teste, sem laboratórios.
    # Act
    response = client.get(BASE, headers=headers())
    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_criar_laboratorio_com_dados_validos_retorna_201_e_persiste(client, headers, test_engine):
    # Arrange
    dados = dados_laboratorio()
    # Act
    response = client.post(BASE, json=dados, headers=headers())
    # Assert
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int) and body["id"] > 0
    assert {k: body[k] for k in dados} == dados
    assert body["computer_count"] == 0
    with Session(test_engine) as db:
        gravado = db.get(Laboratory, body["id"])
        assert gravado is not None
        assert gravado.name == dados["name"]
        assert gravado.location == dados["location"]
        assert gravado.is_active is True
        assert db.scalar(select(AuditLog).where(
            AuditLog.entity == "laboratory", AuditLog.entity_id == body["id"], AuditLog.action == "CREATE"
        )) is not None


def test_obter_laboratorio_existente_retorna_200_e_campos(client, headers):
    # Arrange
    credencial = headers()
    lab = criar_laboratorio(client, credencial)
    # Act
    response = client.get(f"{BASE}/{lab['id']}", headers=credencial)
    # Assert
    assert response.status_code == 200
    assert response.json() == lab


def test_atualizar_laboratorio_existente_retorna_200_e_grava_alteracoes(client, headers, test_engine):
    # Arrange
    credencial = headers()
    lab = criar_laboratorio(client, credencial)
    dados_novos = dados_laboratorio(is_active=False)
    # Act
    response = client.put(f"{BASE}/{lab['id']}", json=dados_novos, headers=credencial)
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": lab["id"], "computer_count": 0, **dados_novos}
    with Session(test_engine) as db:
        gravado = db.get(Laboratory, lab["id"])
        assert gravado is not None and gravado.name == dados_novos["name"]
        assert gravado.location == dados_novos["location"]
        assert gravado.is_active is False


def test_excluir_laboratorio_vazio_retorna_204_e_remove_do_banco(client, headers, test_engine):
    # Arrange
    credencial = headers()
    lab = criar_laboratorio(client, credencial)
    # Act
    response = client.delete(f"{BASE}/{lab['id']}", headers=credencial)
    # Assert
    assert response.status_code == 204
    assert response.content == b""
    with Session(test_engine) as db:
        assert db.get(Laboratory, lab["id"]) is None
    busca = client.get(f"{BASE}/{lab['id']}", headers=credencial)
    assert busca.status_code == 404
    assert busca.json()["detail"] == "Laboratório não encontrado"


def test_listar_laboratorios_cadastrados_retorna_200_e_registro(client, headers):
    # Arrange
    credencial = headers()
    criado = criar_laboratorio(client, credencial)
    # Act
    response = client.get(BASE, headers=credencial)
    # Assert
    assert response.status_code == 200
    assert response.json() == [criado]


def test_obter_laboratorio_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange: banco novo e ID não cadastrado.
    # Act
    response = client.get(f"{BASE}/999999", headers=headers())
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Laboratório não encontrado"}


def test_criar_laboratorio_com_nome_invalido_retorna_422_com_detalhes(client, headers):
    # Arrange
    dados = dados_laboratorio(name="x")
    # Act
    response = client.post(BASE, json=dados, headers=headers())
    # Assert
    assert response.status_code == 422
    assert any("name" in str(erro["loc"]) for erro in response.json()["detail"])


def test_excluir_laboratorio_com_computador_vinculado_retorna_409_com_mensagem(client, headers):
    # Arrange
    credencial = headers()
    lab = criar_laboratorio(client, credencial)
    pc = client.post("/api/v1/computadores", json={
        "hostname": f"PC-{uuid4().hex[:12]}", "laboratory_id": lab["id"]
    }, headers=credencial)
    assert pc.status_code == 201
    # Act
    response = client.delete(f"{BASE}/{lab['id']}", headers=credencial)
    # Assert
    assert response.status_code == 409
    assert "computadores" in response.json()["detail"]
    assert client.get(f"{BASE}/{lab['id']}", headers=credencial).json()["computer_count"] == 1


def test_criar_laboratorio_sem_token_retorna_401_com_header_e_mensagem(client):
    # Arrange
    dados = dados_laboratorio()
    # Act
    response = client.post(BASE, json=dados)
    # Assert: header WWW-Authenticate é relevante para autenticação (seção 3.1 do PDF).
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Autenticação necessária"}


def test_criar_laboratorio_com_perfil_gestor_retorna_403_com_mensagem(client, headers):
    # Arrange
    credencial = headers("gestor")
    # Act
    response = client.post(BASE, json=dados_laboratorio(), headers=credencial)
    # Assert
    assert response.status_code == 403
    assert response.json() == {"detail": "Perfil sem permissão para esta operação"}


def test_criar_laboratorio_com_perfil_tecnico_retorna_201_com_corpo(client, headers):
    # Arrange
    dados = dados_laboratorio()
    credencial = headers("tecnico")
    # Act
    response = client.post(BASE, json=dados, headers=credencial)
    # Assert
    assert response.status_code == 201
    assert response.json()["id"] > 0
    assert response.json()["name"] == dados["name"]
    assert response.json()["location"] == dados["location"]


def test_atualizar_laboratorio_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange
    dados = dados_laboratorio()
    # Act
    response = client.put(f"{BASE}/999999", json=dados, headers=headers())
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Laboratório não encontrado"}


def test_excluir_laboratorio_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange: ID não cadastrado.
    # Act
    response = client.delete(f"{BASE}/999999", headers=headers())
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Laboratório não encontrado"}
