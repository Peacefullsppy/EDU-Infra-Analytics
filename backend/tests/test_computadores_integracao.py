"""Integração do recurso Computadores, incluindo FK, unicidade e fluxo entre recursos."""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Computer

LABS = "/api/v1/laboratorios"
PCS = "/api/v1/computadores"


def criar_laboratorio(client, auth):
    response = client.post(LABS, headers=auth, json={
        "name": f"Laboratório {uuid4().hex[:12]}", "location": "Prédio Central", "is_active": True
    })
    assert response.status_code == 201, response.text
    return response.json()


def dados_computador(lab_id, **mudancas):
    base = {"hostname": f"PC-{uuid4().hex[:12].upper()}", "laboratory_id": lab_id, "ip_address": "10.20.0.42"}
    return {**base, **mudancas}


def criar_computador(client, auth, lab_id, **mudancas):
    response = client.post(PCS, headers=auth, json=dados_computador(lab_id, **mudancas))
    assert response.status_code == 201, response.text
    return response.json()


def test_listar_computadores_sem_cadastros_retorna_200_e_lista_vazia(client, headers):
    # Arrange: SQLite recém-criado e sem computadores.
    # Act
    response = client.get(PCS, headers=headers())
    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_criar_computador_valido_retorna_201_e_persiste(client, headers, test_engine):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    dados = dados_computador(lab["id"])
    # Act
    response = client.post(PCS, headers=auth, json=dados)
    # Assert
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int) and body["id"] > 0
    assert body["hostname"] == dados["hostname"]
    assert body["laboratory_id"] == lab["id"]
    assert body["ip_address"] == dados["ip_address"]
    assert body["status"] == "sem_coleta"
    assert body["last_seen_at"] is None
    with Session(test_engine) as db:
        gravado = db.get(Computer, body["id"])
        assert gravado is not None
        assert gravado.hostname == dados["hostname"]
        assert gravado.laboratory_id == lab["id"]
        assert db.scalar(select(AuditLog).where(
            AuditLog.entity == "computer", AuditLog.entity_id == body["id"], AuditLog.action == "CREATE"
        )) is not None


def test_obter_computador_existente_retorna_200_e_campos(client, headers):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    pc = criar_computador(client, auth, lab["id"])
    # Act
    response = client.get(f"{PCS}/{pc['id']}", headers=auth)
    # Assert
    assert response.status_code == 200
    assert response.json() == pc


def test_atualizar_computador_existente_retorna_200_e_persiste(client, headers, test_engine):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    pc = criar_computador(client, auth, lab["id"])
    novos = dados_computador(lab["id"], ip_address="10.20.0.99")
    # Act
    response = client.put(f"{PCS}/{pc['id']}", headers=auth, json=novos)
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == pc["id"]
    assert response.json()["hostname"] == novos["hostname"]
    assert response.json()["ip_address"] == novos["ip_address"]
    assert response.json()["status"] == "sem_coleta"
    with Session(test_engine) as db:
        gravado = db.get(Computer, pc["id"])
        assert gravado is not None and gravado.hostname == novos["hostname"]
        assert gravado.ip_address == "10.20.0.99"


def test_excluir_computador_existente_retorna_204_e_remove_do_banco(client, headers, test_engine):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    pc = criar_computador(client, auth, lab["id"])
    # Act
    response = client.delete(f"{PCS}/{pc['id']}", headers=auth)
    # Assert
    assert response.status_code == 204
    assert response.content == b""
    with Session(test_engine) as db:
        assert db.get(Computer, pc["id"]) is None
    response_get = client.get(f"{PCS}/{pc['id']}", headers=auth)
    assert response_get.status_code == 404
    assert response_get.json()["detail"] == "Computador não encontrado"


def test_listar_computadores_por_laboratorio_retorna_200_e_somente_os_vinculados(client, headers):
    # Arrange
    auth = headers()
    primeiro = criar_laboratorio(client, auth)
    segundo = criar_laboratorio(client, auth)
    pc_primeiro = criar_computador(client, auth, primeiro["id"])
    pc_segundo = criar_computador(client, auth, segundo["id"])
    # Act
    response = client.get(PCS, params={"laboratory_id": primeiro["id"]}, headers=auth)
    # Assert
    assert response.status_code == 200
    assert response.json() == [pc_primeiro]
    assert pc_segundo["id"] not in [item["id"] for item in response.json()]


def test_criar_computador_com_laboratorio_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange
    dados = dados_computador(999999)
    # Act
    response = client.post(PCS, headers=headers(), json=dados)
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Laboratório não encontrado"}


def test_criar_computador_com_hostname_duplicado_retorna_409_com_mensagem(client, headers):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    primeiro = criar_computador(client, auth, lab["id"])
    # Act
    response = client.post(PCS, headers=auth, json=dados_computador(
        lab["id"], hostname=primeiro["hostname"]
    ))
    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Registro duplicado ou referência inválida"}
    assert client.get(PCS, headers=auth).json() == [primeiro]


def test_obter_computador_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange: ID não existente.
    # Act
    response = client.get(f"{PCS}/999999", headers=headers())
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Computador não encontrado"}


def test_atualizar_computador_com_ip_invalido_retorna_422_com_erro(client, headers):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    pc = criar_computador(client, auth, lab["id"])
    # Act
    response = client.put(f"{PCS}/{pc['id']}", headers=auth, json=dados_computador(
        lab["id"], ip_address="999.999.999.999"
    ))
    # Assert
    assert response.status_code == 422
    assert any("ip_address" in str(error["loc"]) for error in response.json()["detail"])
    assert client.get(f"{PCS}/{pc['id']}", headers=auth).json()["ip_address"] == pc["ip_address"]


def test_atualizar_computador_com_hostname_duplicado_retorna_409_com_mensagem(client, headers):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    primeiro = criar_computador(client, auth, lab["id"])
    segundo = criar_computador(client, auth, lab["id"])
    # Act
    response = client.put(f"{PCS}/{segundo['id']}", headers=auth, json=dados_computador(
        lab["id"], hostname=primeiro["hostname"]
    ))
    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Registro duplicado ou referência inválida"}
    assert client.get(f"{PCS}/{segundo['id']}", headers=auth).json()["hostname"] == segundo["hostname"]


def test_atualizar_computador_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange
    auth = headers()
    lab = criar_laboratorio(client, auth)
    # Act
    response = client.put(f"{PCS}/999999", headers=auth, json=dados_computador(lab["id"]))
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Computador não encontrado"}


def test_excluir_computador_inexistente_retorna_404_com_mensagem(client, headers):
    # Arrange: ID não cadastrado.
    # Act
    response = client.delete(f"{PCS}/999999", headers=headers())
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Computador não encontrado"}


def test_criar_laboratorio_e_computador_e_consultar_vinculo_retorna_200(client, headers):
    # Arrange: dois recursos relacionados criados pelas próprias rotas HTTP.
    auth = headers()
    lab = criar_laboratorio(client, auth)
    pc = criar_computador(client, auth, lab["id"])
    # Act
    listado = client.get(PCS, params={"laboratory_id": lab["id"]}, headers=auth)
    consultado = client.get(f"{LABS}/{lab['id']}", headers=auth)
    # Assert
    assert listado.status_code == 200
    assert listado.json() == [pc]
    assert consultado.status_code == 200
    assert consultado.json()["computer_count"] == 1
    assert consultado.json()["name"] == lab["name"]
