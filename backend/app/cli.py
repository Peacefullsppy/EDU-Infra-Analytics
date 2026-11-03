"""Criação explícita do primeiro usuário; nunca insere laboratório ou computador fictício."""
import argparse
from getpass import getpass

from sqlalchemy import func, select
from pydantic import ValidationError

from .schemas import UserCreate
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
        if password != confirmation:
            raise SystemExit("As senhas informadas são diferentes.")
        try:
            validated = UserCreate(name=name, email=email, password=password, role="admin")
        except ValidationError as exc:
            raise SystemExit("Nome, e-mail ou senha inválidos. Confira os requisitos de cadastro.") from exc
        db.add(User(name=validated.name.strip(), email=str(validated.email).lower(), password_hash=hash_password(password), role="admin"))
        db.commit()
        print("Primeiro administrador criado. Nenhum dado de demonstração foi inserido.")


if __name__ == "__main__":
    main()
