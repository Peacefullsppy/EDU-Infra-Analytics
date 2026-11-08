"""Verifica artefatos reprodutíveis, sem depender de banco/VM externos."""
import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime
import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent


def test_initial_sqlite_migration_creates_tables_and_terms(tmp_path):
    db_path = tmp_path / "migration.db"
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + db_path.as_posix(), "JWT_SECRET_KEY": "test-secret-strong-enough-for-dev-env-12345"}
    run = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    with sqlite3.connect(db_path) as db:
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"users", "term_documents", "term_acceptances", "laboratories", "computers", "metrics", "alerts", "indicator_snapshots", "system_settings", "audit_logs", "alembic_version"} <= names
        assert db.execute("SELECT version FROM term_documents WHERE active=1").fetchone()[0] == "2.1-lgpd"
        assert db.execute("SELECT COUNT(*) FROM term_documents").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM laboratories").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM computers").fetchone()[0] == 0


@pytest.fixture
def agent_module():
    import importlib.util
    location = ROOT / "agent" / "agent.py"
    spec = importlib.util.spec_from_file_location("edu_infra_test_agent", location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_agent_requires_HTTPS_outside_localhost(agent_module, monkeypatch):
    monkeypatch.setenv("EDU_COMPUTER_ID", "1")
    monkeypatch.setenv("EDU_AGENT_TOKEN", "eia_secret" )
    monkeypatch.setenv("EDU_API_URL", "http://192.168.0.10:8000")
    with pytest.raises(ValueError, match="HTTPS"):
        agent_module.configuration()


def test_agent_supports_loopback_dev(agent_module, monkeypatch):
    monkeypatch.setenv("EDU_COMPUTER_ID", "5")
    monkeypatch.setenv("EDU_AGENT_TOKEN", "eia_fake-secret")
    monkeypatch.setenv("EDU_API_URL", "http://127.0.0.1:8000")
    url, ident, token, interval, disk = agent_module.configuration()
    assert url == "http://127.0.0.1:8000"
    assert ident == 5


def test_agent_rejects_missing_token(agent_module, monkeypatch):
    monkeypatch.setenv("EDU_COMPUTER_ID", "1")
    monkeypatch.setenv("EDU_AGENT_TOKEN", "")
    monkeypatch.setenv("EDU_API_URL", "https://host.ts.net")
    with pytest.raises(ValueError, match="EDU_AGENT_TOKEN"):
        agent_module.configuration()


def test_agent_collects_valid_metrics(agent_module):
    disk = "C:\\" if os.name == "nt" else "/"
    data = agent_module.collect(disk)
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 <= data["memory_percent"] <= 100
    assert 0 <= data["disk_percent"] <= 100
    assert data["uptime_seconds"] >= 0
    assert datetime.fromisoformat(data["collected_at"]).tzinfo is not None


def test_migration_preserves_existing_terms_and_acceptances(tmp_path):
    """Um banco V2 já utilizado mantém aceites ao receber a versão LGPD."""
    from sqlalchemy import create_engine, text
    db_path = tmp_path / 'existing.db'
    env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + db_path.as_posix(),
           'JWT_SECRET_KEY': 'test-secret-strong-enough-for-dev-env-12345'}
    previous = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '3764cfd9f21b'],
                              cwd=BACKEND, env=env, capture_output=True, text=True)
    assert previous.returncode == 0, previous.stdout + previous.stderr
    import sqlite3
    with sqlite3.connect(db_path) as con:
        con.execute("INSERT INTO users (id,name,email,password_hash,role,active,created_at) VALUES (1,'Exemplo','exemplo@example.org','hash','ADMIN',1,'2026-01-01')")
        con.execute("INSERT INTO term_acceptances (user_id,terms_id,accepted_at) VALUES (1,1,'2026-01-01')")
        con.commit()
    upgraded = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                              cwd=BACKEND, env=env, capture_output=True, text=True)
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    with sqlite3.connect(db_path) as con:
        assert con.execute("SELECT version FROM term_documents WHERE active=1").fetchone()[0] == '2.1-lgpd'
        assert con.execute("SELECT COUNT(*) FROM term_acceptances").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM term_documents").fetchone()[0] == 2
