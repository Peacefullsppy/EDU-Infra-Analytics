"""Semeia exclusivamente o banco SQLite efêmero de E2E. Nunca usar em produção."""
from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import select
from app.core import SessionLocal, engine, hash_password, settings
from app.models import User


def main():
    if os.environ.get('EDU_E2E_DISPOSABLE') != 'SIM':
        raise SystemExit('Defina EDU_E2E_DISPOSABLE=SIM para o banco temporário de E2E.')
    url=settings.database_url
    if not url.startswith('sqlite:///') or 'edu-e2e-' not in url:
        raise SystemExit('Recusado: E2E exige SQLite isolado com nome edu-e2e-*.sqlite.')
    password=os.environ.get('E2E_TEST_PASSWORD','')
    if len(password)<12:
        raise SystemExit('E2E_TEST_PASSWORD deve possuir pelo menos 12 caracteres.')
    for role,name in [('ADMIN','Admin'),('GESTOR','Gestor'),('TECNICO','Tecnico')]:
        email=f'e2e-{name.lower()}@example.org'
        with SessionLocal() as db:
            if db.scalar(select(User.id).where(User.email==email)) is None:
                db.add(User(name=f'E2E {name}',email=email,password_hash=hash_password(password),role=role))
                db.commit()
    print('Contas E2E criadas somente no banco SQLite descartável.')


if __name__=='__main__':
    main()
