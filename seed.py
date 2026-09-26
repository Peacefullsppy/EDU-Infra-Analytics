import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import func, select

from app.database import SessionLocal, init_db
from app.models import Computer, Laboratory, User
from app.security import hash_password

load_dotenv()


def criar_admin(db):
    email = os.getenv("ADMIN_EMAIL", "admin@escola.edu").lower().strip()
    password = os.getenv("ADMIN_PASSWORD")
    nome = os.getenv("ADMIN_NAME", "Administrador")

    if not password:
        raise RuntimeError(
            "Defina ADMIN_PASSWORD no arquivo .env antes de executar o seed."
        )

    existente = db.scalar(select(User).where(User.email == email))
    if existente:
        print(f"Usuário administrador já existe: {email}")
        return

    db.add(
        User(
            nome=nome,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            ativo=True,
        )
    )
    db.commit()
    print(f"Administrador criado: {email}")


def criar_dados_demo(db):
    total_labs = db.scalar(select(func.count(Laboratory.id))) or 0
    if total_labs:
        print("Laboratórios já existem. Seed de demonstração ignorado.")
        return

    labs = [
        Laboratory(nome="LAB 01", localizacao="Informática 1", status="ativo", iie=91),
        Laboratory(nome="LAB 02", localizacao="Informática 2", status="ativo", iie=78),
        Laboratory(nome="LAB 03", localizacao="Informática 3", status="ativo", iie=64),
    ]
    db.add_all(labs)
    db.flush()

    configuracao = {
        labs[0].id: {"total": 20, "offline": set(), "atencao": {2}, "critico": set()},
        labs[1].id: {"total": 25, "offline": {11}, "atencao": {8, 12}, "critico": set()},
        labs[2].id: {"total": 15, "offline": {7}, "atencao": {9, 10}, "critico": {4}},
    }

    for lab_id, config in configuracao.items():
        for numero in range(1, config["total"] + 1):
            if numero in config["offline"]:
                status = "offline"
                cpu = ram = disco = None
            elif numero in config["critico"]:
                status = "critico"
                cpu, ram, disco = 84, 76, 96
            elif numero in config["atencao"]:
                status = "atencao"
                if lab_id == labs[0].id and numero == 2:
                    cpu, ram, disco = 92, 87, 70
                elif lab_id == labs[1].id and numero == 8:
                    cpu, ram, disco = 45, 93, 67
                else:
                    cpu, ram, disco = 88, 81, 74
            else:
                status = "online"
                cpu = 24 + ((numero * 7 + lab_id * 5) % 42)
                ram = 38 + ((numero * 5 + lab_id * 7) % 30)
                disco = 45 + ((numero * 3 + lab_id * 11) % 28)

            db.add(
                Computer(
                    hostname=f"LAB{lab_id:02d}-PC{numero:02d}",
                    ip=f"192.168.{lab_id}.{100 + numero}",
                    laboratorio_id=lab_id,
                    status=status,
                    cpu=cpu,
                    ram=ram,
                    disco=disco,
                    ultima_coleta=datetime.now(timezone.utc),
                )
            )

    db.commit()
    print("Dados de demonstração criados.")


def main():
    init_db()
    db = SessionLocal()
    try:
        criar_admin(db)
        criar_dados_demo(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
