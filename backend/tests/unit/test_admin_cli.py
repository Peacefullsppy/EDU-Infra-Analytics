"""CLI de administração: entradas inválidas, duplicatas e proteção de senhas."""
import pytest
from sqlalchemy import select
from app import cli
from app.models import User
from tests.conftest import auth


def patch_input(monkeypatch, name, email, password):
    seq=iter([name,email])
    monkeypatch.setattr('builtins.input',lambda _:next(seq))
    monkeypatch.setattr(cli,'getpass',lambda _:password)


@pytest.mark.integration
@pytest.mark.parametrize('name,email,password,message',[
    ('X','new@example.org','SecurePassword123!','Nome ou e-mail inválido'),
    ('Valid Name','invalid-email','SecurePassword123!','Nome ou e-mail inválido'),
    ('Valid Name','new@example.org','short','pelo menos 12 caracteres'),
])
def test_admin_cli_rejects_bad_input(client,monkeypatch,name,email,password,message):
    monkeypatch.setattr(cli,'SessionLocal',client.Session)
    patch_input(monkeypatch,name,email,password)
    with pytest.raises(SystemExit,match=message):cli.create_admin()
    with client.Session() as db:
        assert db.scalar(select(User.id).where(User.email=='new@example.org')) is None


@pytest.mark.integration
def test_admin_cli_rejects_existing_email(client,monkeypatch):
    monkeypatch.setattr(cli,'SessionLocal',client.Session)
    patch_input(monkeypatch,'Demo User','ADMIN@example.org','SecurePassword123!')
    with pytest.raises(SystemExit,match='E-mail já cadastrado'):cli.create_admin()


@pytest.mark.integration
def test_admin_cli_creates_hashed_administrator(client,monkeypatch,capsys):
    monkeypatch.setattr(cli,'SessionLocal',client.Session)
    patch_input(monkeypatch,'Demo Administrator','DEMO@example.org','SecurePassword123!')
    cli.create_admin()
    with client.Session() as db:
        account=db.scalar(select(User).where(User.email=='demo@example.org'))
        assert account.role=='ADMIN'
        assert account.password_hash.startswith('$argon2')
        assert 'SecurePassword123!' not in account.password_hash
    assert 'Administrador criado' in capsys.readouterr().out
