"""Confere esquema, termos iniciais e configurações do banco escolhido no .env."""
from sqlalchemy import inspect, text
from app.core import engine, SessionLocal
from app.models import Base, SystemSetting, TermDocument
from app.core import current_terms


def main():
    expected = set(Base.metadata.tables)
    actual = set(inspect(engine).get_table_names())
    missing = sorted(expected - actual)
    with SessionLocal() as db:
        doc = current_terms(db) if not missing else None
        settings = db.get(SystemSetting, 1) if not missing else None
    print("Tipo de banco:", engine.dialect.name)
    print("Tabelas esperadas:", len(expected))
    print("Tabelas existentes:", len(actual))
    print("Tabelas ausentes:", ", ".join(missing) or "nenhuma")
    print("Termos vigentes:", doc.version if doc else "AUSENTES")
    print("Configurações:", "OK" if settings else "AUSENTES")
    if missing or not doc or not settings:
        raise SystemExit(1)
    print("Verificação concluída com sucesso")


if __name__ == '__main__':
    main()
