"""Teste destrutivo APENAS para PostgreSQL efêmero de CI. Nunca executar em produção."""
import os
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.core import SessionLocal, engine, hash_password
from app.main import app
from app.models import User


@pytest.mark.skipif(os.environ.get("EDU_TEST_POSTGRES_DISPOSABLE") != "SIM" or engine.dialect.name != "postgresql", reason="Requer PostgreSQL de teste descartável e opt-in")
def test_full_flow_on_real_postgres():
    suffix = uuid.uuid4().hex[:12]
    email = f"ci-{suffix}@example.org"
    with SessionLocal() as db:
        db.add(User(name="CI Integration", email=email, password_hash=hash_password("IntegrationPassword123!"), role="ADMIN"))
        db.commit()
    with TestClient(app) as client:
        token = client.post("/api/auth/login", json={"email":email,"password":"IntegrationPassword123!"}).json()["access_token"]
        headers={"Authorization":f"Bearer {token}"}
        assert client.get('/api/laboratories',headers=headers).status_code==428
        current=client.get('/api/terms/current',headers=headers).json()['version']
        r=client.post('/api/terms/accept',json={'version':current,'accepted':True},headers=headers)
        assert r.status_code==200,r.text
        headers={"Authorization":"Bearer "+r.json()["access_token"]}
        l=client.post('/api/laboratories',json={'name':f"CI Lab {suffix}",'location':'Postgres CI','active':True},headers=headers)
        assert l.status_code==201,l.text
        lab_id=l.json()['id']
        c=client.post('/api/computers',json={'name':'Host CI','hostname':f"ci-{suffix}",'laboratory_id':lab_id,'active':True},headers=headers)
        assert c.status_code==201,c.text
        pc_id=c.json()['id']
        key=client.post(f'/api/computers/{pc_id}/token',headers=headers).json()['agent_token']
        result=client.post('/api/agent/metrics',json={'cpu_percent':20,'memory_percent':30,'disk_percent':40,'uptime_seconds':60,'os_name':'Linux CI','collected_at':datetime.now(timezone.utc).isoformat()},headers={'X-Agent-Token':key,'X-Computer-ID':str(pc_id)})
        assert result.status_code==201,result.text
        assert client.get('/api/indicators',headers=headers).json()[0]['score'] is not None
        assert client.get('/api/reports/metrics.csv',headers=headers).status_code==200
        assert client.delete(f'/api/computers/{pc_id}',headers=headers).status_code==204
        assert client.delete(f'/api/laboratories/{lab_id}',headers=headers).status_code==204
