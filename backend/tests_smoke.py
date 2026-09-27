"""Teste simples de importação para verificar se a aplicação inicia."""
from app.main import app


def test_app_title():
    assert app.title == "EDU-Infra Analytics API"
