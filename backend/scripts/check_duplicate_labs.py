"""Verifica repetições antes da migração 0002; não modifica o banco de dados."""
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_engine


def main() -> int:
    try:
        with get_engine().connect() as connection:
            records = connection.execute(text("SELECT id, name, location FROM laboratories ORDER BY id")).all()
    except SQLAlchemyError as exc:
        print("Não foi possível consultar laboratories. Confira o DATABASE_URL e aplique primeiro a migração 0001.")
        return 2
    grouped = defaultdict(list)
    for row in records:
        grouped[(row.name.strip().casefold(), row.location.strip().casefold())].append(row)
    duplicated = [group for group in grouped.values() if len(group) > 1]
    if not duplicated:
        print(f"Nenhum laboratório repetido entre os {len(records)} registros consultados.")
        return 0
    print("Laboratórios repetidos: revise antes de aplicar a migração 0002.")
    for group in duplicated:
        for row in group:
            print(f"  ID {row.id}: {row.name} | {row.location}")
        print()
    print("O programa não excluiu nenhum registro.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
