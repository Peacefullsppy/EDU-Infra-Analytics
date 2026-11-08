"""Gerenciamento via CLI. Nunca semeia administradores com senhas estáticas."""
import argparse
from getpass import getpass
from sqlalchemy import select
from .core import SessionLocal, hash_password
from .models import User


def create_admin():
    name = input("Nome do administrador: ").strip()
    email = input("E-mail do administrador: ").strip().lower()
    password = getpass("Senha (mín. 12 caracteres): ")
    if len(name) < 2 or "@" not in email:
        raise SystemExit("Nome ou e-mail inválido")
    try:
        hashed = hash_password(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)):
            raise SystemExit("E-mail já cadastrado")
        db.add(User(name=name, email=email, password_hash=hashed, role="ADMIN"))
        db.commit()
        print("Administrador criado com sucesso")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create-admin"])
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin()


if __name__ == "__main__":
    main()
