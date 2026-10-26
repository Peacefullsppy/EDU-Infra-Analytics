from app.schemas import ComputerInput
from pydantic import ValidationError
import pytest


def test_without_token_is_blocked(client):
    assert client.get("/api/v1/laboratorios").status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "admin@example.org", "password": "incorreta"}).status_code == 401


def test_database_begins_without_labs_and_without_metrics(client, headers):
    result = client.get("/api/v1/dashboard", headers=headers())
    assert result.status_code == 200
    assert result.json() == {
        "laboratories": 0,
        "computers": {"total": 0, "sem_coleta": 0, "online": 0, "offline": 0, "atencao": 0, "critico": 0},
        "availability_percent": None,
        "iie": None,
        "iie_status": "nao_definido",
    }


def test_crud_and_protection_of_laboratory_with_computers(client, headers):
    admin = headers()
    lab = client.post("/api/v1/laboratorios", json={"name": "Laboratório A", "location": "Bloco 2", "is_active": True}, headers=admin)
    assert lab.status_code == 201
    lab_id = lab.json()["id"]
    updated = client.put(f"/api/v1/laboratorios/{lab_id}", json={"name": "Laboratório B", "location": "Bloco 3", "is_active": True}, headers=admin)
    assert updated.status_code == 200 and updated.json()["name"] == "Laboratório B"
    not_found = client.post("/api/v1/computadores", json={"hostname": "PC-01", "laboratory_id": 999}, headers=admin)
    assert not_found.status_code == 404
    pc = client.post("/api/v1/computadores", json={"hostname": "pc-01", "laboratory_id": lab_id}, headers=admin)
    assert pc.status_code == 201 and pc.json()["status"] == "sem_coleta"
    pc_id = pc.json()["id"]
    assert client.delete(f"/api/v1/laboratorios/{lab_id}", headers=admin).status_code == 409
    changed = client.put(f"/api/v1/computadores/{pc_id}", json={"hostname": "PC-02", "laboratory_id": lab_id, "ip_address": "10.0.0.2"}, headers=admin)
    assert changed.status_code == 200 and changed.json()["hostname"] == "PC-02"
    assert client.delete(f"/api/v1/computadores/{pc_id}", headers=admin).status_code == 204
    assert client.delete(f"/api/v1/laboratorios/{lab_id}", headers=admin).status_code == 204
    assert client.get("/api/v1/laboratorios", headers=admin).json() == []
    entries = client.get("/api/v1/auditoria", headers=admin).json()
    assert any(x["action"] == "DELETE" and x["entity"] == "laboratory" for x in entries)


def test_roles_are_enforced_on_server(client, headers):
    gestor = headers("gestor")
    tecnico = headers("tecnico")
    assert client.post("/api/v1/laboratorios", headers=gestor, json={"name": "Lab 1", "location": "Bloco 1"}).status_code == 403
    assert client.post("/api/v1/laboratorios", headers=tecnico, json={"name": "Lab 1", "location": "Bloco 1"}).status_code == 201
    assert client.get("/api/v1/auditoria", headers=tecnico).status_code == 403
    assert client.delete("/api/v1/laboratorios/1", headers=tecnico).status_code == 403
    assert client.get("/api/v1/dashboard", headers=gestor).status_code == 200


def test_duplicate_hostname_and_input_validation(client, headers):
    a = headers()
    lab = client.post("/api/v1/laboratorios", headers=a, json={"name": "Lab 1", "location": "Prédio 1"}).json()["id"]
    payload = {"hostname": "PC-03", "laboratory_id": lab}
    assert client.post("/api/v1/computadores", headers=a, json=payload).status_code == 201
    assert client.post("/api/v1/computadores", headers=a, json=payload).status_code == 409
    assert client.post("/api/v1/computadores", headers=a, json={**payload, "hostname": "PC-04", "ip_address": "999.999.999.999"}).status_code == 422
    assert client.get("/api/v1/dashboard", headers=a).json()["computers"]["sem_coleta"] == 1


def test_user_management_and_inactive_login(client, headers):
    a = headers()
    new_user = client.post("/api/v1/users", headers=a, json={"name": "Gestor Real", "email": "novo@example.org", "password": "UmaSenhaValida123", "role": "gestor"})
    assert new_user.status_code == 201
    user_id = new_user.json()["id"]
    assert client.patch(f"/api/v1/users/{user_id}", headers=a, json={"is_active": False}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "novo@example.org", "password": "UmaSenhaValida123"}).status_code == 403
    assert client.patch("/api/v1/users/1", headers=a, json={"is_active": False}).status_code == 409


def test_hostname_validation():
    with pytest.raises(ValidationError):
        ComputerInput(hostname="PC COM ESPAÇO", laboratory_id=1)
