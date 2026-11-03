"""Correcoes de cadastro e consulta previstas no escopo inicial do PFC."""
from sqlalchemy import select

from app.models import AuditLog


def lab(client, auth, name="Laboratório Azul", location="Bloco B"):
    return client.post("/api/v1/laboratorios", headers=auth, json={"name": name, "location": location})


def test_laboratorio_nao_duplica_mesmo_com_diferenca_de_maiusculas(client, headers):
    auth = headers()
    first = lab(client, auth)
    repeated = lab(client, auth, "laboratório azul", "BLOCO B")
    assert first.status_code == 201
    assert repeated.status_code == 409
    assert "já existe" in repeated.json()["detail"].lower()
    listed = client.get("/api/v1/laboratorios", headers=auth).json()
    assert len(listed) == 1
    assert listed[0]["computer_count"] == 0
    records = client.get("/api/v1/auditoria", headers=auth).json()
    assert len([row for row in records if row["entity"] == "laboratory" and row["action"] == "CREATE"]) == 1


def test_mesmo_nome_em_outro_local_nao_e_duplicado(client, headers):
    auth = headers()
    assert lab(client, auth, "Laboratório A", "Bloco A").status_code == 201
    assert lab(client, auth, "Laboratório A", "Bloco B").status_code == 201


def test_edicao_para_laboratorio_duplicado_retorna_409_e_preserva_dados(client, headers):
    auth = headers()
    first = lab(client, auth, "Sala 10", "Primeiro andar").json()
    second = lab(client, auth, "Sala 11", "Segundo andar").json()
    result = client.put(f"/api/v1/laboratorios/{second['id']}", headers=auth,
                        json={"name": "SALA 10", "location": "PRIMEIRO ANDAR"})
    assert result.status_code == 409
    original = client.get(f"/api/v1/laboratorios/{second['id']}", headers=auth).json()
    assert original["name"] == "Sala 11"
    assert original["location"] == "Segundo andar"
    logs = client.get("/api/v1/auditoria", headers=auth).json()
    assert not any(r["entity"] == "laboratory" and r["entity_id"] == second["id"] and r["action"] == "UPDATE" for r in logs)


def test_busca_laboratorios_por_nome_local_e_ativo(client, headers):
    auth = headers()
    lab(client, auth, "Sala do térreo", "Prédio Norte")
    client.post("/api/v1/laboratorios", headers=auth,
                json={"name": "Sala informática", "location": "Prédio Sul", "is_active": False})
    result = client.get("/api/v1/laboratorios", headers=auth, params={"busca": "NORTE", "ativo": "true"})
    assert result.status_code == 200
    assert [v["name"] for v in result.json()] == ["Sala do térreo"]
    assert len(client.get("/api/v1/laboratorios", headers=auth, params={"ativo": "false"}).json()) == 1
    assert client.get("/api/v1/laboratorios", headers=auth, params={"busca": "nenhum"}).json() == []


def test_busca_computadores_por_hostname_e_laboratorio(client, headers):
    auth = headers()
    one = lab(client, auth, "Sala A", "Bloco 1").json()
    two = lab(client, auth, "Sala B", "Bloco 2").json()
    for host, lab_id in (("INF-A-01", one["id"]), ("INF-A-02", one["id"]), ("INF-B-01", two["id"])):
        assert client.post("/api/v1/computadores", headers=auth,
                           json={"hostname": host, "laboratory_id": lab_id}).status_code == 201
    result = client.get("/api/v1/computadores", headers=auth,
                        params={"busca": "a-0", "laboratory_id": one["id"]})
    assert result.status_code == 200
    assert [r["hostname"] for r in result.json()] == ["INF-A-01", "INF-A-02"]
    assert client.get("/api/v1/computadores", headers=auth, params={"laboratory_id": -1}).status_code == 422


def test_busca_exige_login_e_respeita_perfis(client, headers):
    assert client.get("/api/v1/laboratorios", params={"busca": "Sala"}).status_code == 401
    assert client.get("/api/v1/laboratorios", params={"ativo": "true"}, headers=headers("gestor")).status_code == 200
    assert client.get("/api/v1/computadores", params={"busca": "PC"}, headers=headers("gestor")).status_code == 200


def test_exclusao_de_laboratorio_ocupado_continua_409(client, headers):
    auth = headers()
    lab_id = lab(client, auth).json()["id"]
    computer = client.post("/api/v1/computadores", headers=auth,
                           json={"hostname": "PC-LAB", "laboratory_id": lab_id}).json()
    assert client.delete(f"/api/v1/laboratorios/{lab_id}", headers=auth).status_code == 409
    assert client.get(f"/api/v1/laboratorios/{lab_id}", headers=auth).json()["computer_count"] == 1
    assert client.get(f"/api/v1/computadores/{computer['id']}", headers=auth).status_code == 200
    assert client.delete(f"/api/v1/computadores/{computer['id']}", headers=auth).status_code == 204
    assert client.delete(f"/api/v1/laboratorios/{lab_id}", headers=auth).status_code == 204


def test_duplicidade_com_letras_acentuadas_em_caixa_alta(client, headers):
    auth = headers()
    assert lab(client, auth, "Laboratório Órion", "Área A").status_code == 201
    assert lab(client, auth, "LABORATÓRIO ÓRION", "ÁREA A").status_code == 409
    assert len(client.get("/api/v1/laboratorios", headers=auth).json()) == 1


def test_busca_trata_percentual_como_texto_e_nao_coringa(client, headers):
    auth = headers()
    assert lab(client, auth, "Sala 20", "Prédio Principal").status_code == 201
    assert client.get("/api/v1/laboratorios", params={"busca": "%"}, headers=auth).json() == []
    assert client.get("/api/v1/computadores", params={"busca": "_"}, headers=auth).json() == []
