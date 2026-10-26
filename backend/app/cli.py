"""Criação explícita do primeiro usuário; nunca insere laboratório ou computador fictício."""
import argparse
from getpass import getpass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_engine
from .models import User
from .security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Bootstrap seguro de administrador")
    parser.add_argument("create-admin", choices=["create-admin"])
    args = parser.parse_args()
    with Session(get_engine()) as db:
        existing = db.scalar(select(func.count(User.id))) or 0
        if existing > 0:
            raise SystemExit("Já existe usuário. Crie outros pelo painel administrativo.")
        name = input("Nome completo: ").strip()
        email = input("E-mail: ").strip().lower()
        password = getpass("Senha (mínimo 12 caracteres): ")
        confirmation = getpass("Confirmar senha: ")
        if len(name) < 2 or "@" not in email or len(password) < 12 or password != confirmation:
            raise SystemExit("Dados inválidos ou senhas diferentes.")
        db.add(User(name=name, email=email, password_hash=hash_password(password), role="admin"))
        db.commit()
        print("Primeiro administrador criado. Nenhum dado de demonstração foi inserido.")


if __name__ == "__main__":
    main()
