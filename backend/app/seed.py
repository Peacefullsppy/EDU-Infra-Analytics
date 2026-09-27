from sqlalchemy import select

from app.config import ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD
from app.database import SessionLocal, init_db
from app.models import Computer, Laboratory, User
from app.security import hash_password


def criar_admin(db):
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "Defina ADMIN_PASSWORD no arquivo .env antes de executar o seed."
        )

    admin = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
    if admin:
        print(f"Administrador já existe: {ADMIN_EMAIL}")
        return

    admin = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print(f"Administrador criado: {ADMIN_EMAIL}")


def criar_dados_demo(db):
    quantidade = db.query(Laboratory).count()
    if quantidade > 0:
        print("Laboratórios já existem. Seed de demonstração ignorado.")
        return

    labs = [
        Laboratory(id=1, nome="LAB 01", localizacao="Informática 1", status="ativo", iie=91),
        Laboratory(id=2, nome="LAB 02", localizacao="Informática 2", status="ativo", iie=78),
        Laboratory(id=3, nome="LAB 03", localizacao="Informática 3", status="ativo", iie=64),
    ]
    db.add_all(labs)
    db.flush()

    configuracao = {
        1: {"total": 20, "offline": set(), "atencao": {2}, "critico": set()},
        2: {"total": 25, "offline": {11}, "atencao": {8, 12}, "critico": set()},
        3: {"total": 15, "offline": {7}, "atencao": {9, 10}, "critico": {4}},
    }

    computadores = []
    for laboratorio_id, config in configuracao.items():
        for numero in range(1, config["total"] + 1):
            if numero in config["offline"]:
                status = "offline"
                cpu = ram = disco = None
            elif numero in config["critico"]:
                status = "critico"
                cpu, ram, disco = 84, 76, 96
            elif numero in config["atencao"]:
                status = "atencao"
                if laboratorio_id == 1 and numero == 2:
                    cpu, ram, disco = 92, 87, 70
                elif laboratorio_id == 2 and numero == 8:
                    cpu, ram, disco = 45, 93, 67
                else:
                    cpu, ram, disco = 88, 81, 74
            else:
                status = "online"
                cpu = 24 + ((numero * 7 + laboratorio_id * 5) % 42)
                ram = 38 + ((numero * 5 + laboratorio_id * 7) % 30)
                disco = 45 + ((numero * 3 + laboratorio_id * 11) % 28)

            computadores.append(
                Computer(
                    hostname=f"LAB{laboratorio_id:02d}-PC{numero:02d}",
                    ip=f"192.168.{laboratorio_id}.{100 + numero}",
                    laboratorio_id=laboratorio_id,
                    status=status,
                    cpu=cpu,
                    ram=ram,
                    disco=disco,
                    ultima_coleta="09:20" if status != "offline" else "07:55",
                )
            )

    db.add_all(computadores)
    db.commit()
    print("Dados de demonstração criados: 3 laboratórios e 60 computadores.")


def main():
    print("Iniciando seed do EDU-Infra Analytics...")
    init_db()
    db = SessionLocal()
    try:
        criar_admin(db)
        criar_dados_demo(db)
        print("Seed finalizado com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
