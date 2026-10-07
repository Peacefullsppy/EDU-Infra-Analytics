from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.main import criar_computador
from app.models import Computer, Laboratory, User
from app.schemas import ComputadorCreate


def _usuario_tecnico():
    return User(
        id=10,
        name="Técnico de TI",
        email="tecnico@escola.edu",
        password_hash="hash-de-teste",
        role="tecnico",
        is_active=True,
    )


def _request_mock():
    request = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.mark.unit
def test_deve_persistir_computador_quando_laboratorio_existe():
    # Arrange
    db = MagicMock()
    laboratorio = Laboratory(id=1, nome="LAB 01", localizacao="Bloco A", status="ativo")
    db.get.return_value = laboratorio
    db.scalar.return_value = None

    def atribuir_id(objeto):
        if isinstance(objeto, Computer):
            objeto.id = 99

    db.refresh.side_effect = atribuir_id
    dados = ComputadorCreate(
        hostname="LAB01-PC99",
        ip="192.168.1.199",
        laboratorio_id=1,
        status="online",
        cpu=30,
        ram=40,
        disco=50,
    )

    # Act
    with patch("app.main.register_audit") as audit_mock:
        resultado = criar_computador(dados, _request_mock(), db, _usuario_tecnico())

    # Assert
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    audit_mock.assert_called_once()
    assert resultado["hostname"] == "LAB01-PC99"
    assert resultado["laboratorio"] == "LAB 01"


@pytest.mark.unit
def test_nao_deve_persistir_computador_quando_laboratorio_nao_existe():
    # Arrange
    db = MagicMock()
    db.get.return_value = None
    dados = ComputadorCreate(
        hostname="PC-SEM-LAB",
        ip="192.168.50.10",
        laboratorio_id=999,
    )

    # Act
    with patch("app.main.register_audit") as audit_mock:
        with pytest.raises(HTTPException) as exc:
            criar_computador(dados, _request_mock(), db, _usuario_tecnico())

    # Assert
    assert exc.value.status_code == 400
    assert "RN01" in exc.value.detail
    assert "laboratório informado não existe" in exc.value.detail
    db.add.assert_not_called()
    db.commit.assert_not_called()
    audit_mock.assert_not_called()
