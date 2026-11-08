from datetime import datetime, timedelta, timezone
import pytest
from app.models import AuditLog, Computer, Metric, User
from .conftest import auth, lab, pc, measurement, setup_agent


def test_create_and_list_labs(client):
    h=auth(client)
    created=lab(client,h)
    data=client.get('/api/laboratories',headers=h).json()
    assert data[0]['id']==created['id']


def test_labs_prevent_normalized_duplicates(client):
    h=auth(client)
    lab(client,h)
    response=client.post('/api/laboratories',json={'name':' laboratório a ','location':'bloco 1','active':True},headers=h)
    assert response.status_code==409


def test_same_lab_name_different_location_allowed(client):
    h=auth(client)
    lab(client,h)
    assert client.post('/api/laboratories',json={'name':'Laboratório A','location':'Bloco 2','active':True},headers=h).status_code==201


def test_update_and_filter_lab(client):
    h=auth(client)
    l=lab(client,h)
    assert client.put(f"/api/laboratories/{l['id']}",json={'name':'Lab Teste','location':'Bloco Novo','active':False},headers=h).status_code==200
    items=client.get('/api/laboratories?q=Teste&active=false',headers=h).json()
    assert len(items)==1 and not items[0]['active']


def test_lab_delete_with_computers_returns_conflict(client):
    h=auth(client)
    l=lab(client,h)
    c=pc(client,h,l['id'])
    assert client.delete(f"/api/laboratories/{l['id']}",headers=h).status_code==409
    assert client.get('/api/laboratories',headers=h).status_code==200
    client.delete(f"/api/computers/{c['id']}",headers=h)
    assert client.delete(f"/api/laboratories/{l['id']}",headers=h).status_code==204


def test_lab_missing_returns_404(client):
    h=auth(client)
    assert client.delete('/api/laboratories/100',headers=h).status_code==404


def test_pc_missing_lab_returns_404(client):
    h=auth(client)
    r=client.post('/api/computers',headers=h,json={'laboratory_id':999,'name':'Teste PC','hostname':'HOST-99','active':True})
    assert r.status_code==404


def test_pc_invalid_ip_returns_422(client):
    h=auth(client)
    l=lab(client,h)
    assert client.post('/api/computers',headers=h,json={'laboratory_id':l['id'],'name':'PC','hostname':'HOST-99','ip_address':'INVALIDO','active':True}).status_code==422


def test_pc_duplicate_host_per_lab(client):
    h=auth(client)
    l=lab(client,h)
    pc(client,h,l['id'])
    r=client.post('/api/computers',headers=h,json={'laboratory_id':l['id'],'name':'Segundo PC','hostname':'VM-01','active':True})
    assert r.status_code==409


def test_pc_update_and_delete(client):
    h=auth(client)
    l=lab(client,h)
    c=pc(client,h,l['id'])
    r=client.put(f"/api/computers/{c['id']}",headers=h,json={'laboratory_id':l['id'],'name':'VM Updated','hostname':'VM-NEW','ip_address':'10.10.0.2','active':True})
    assert r.status_code==200 and r.json()['name']=='VM Updated'
    assert client.delete(f"/api/computers/{c['id']}",headers=h).status_code==204
    assert client.get('/api/computers',headers=h).json()==[]


def test_role_permissions_for_technician_and_manager(client):
    manager=auth(client,'GESTOR')
    technician=auth(client,'TECNICO')
    assert client.get('/api/laboratories',headers=manager).status_code==200
    assert client.post('/api/laboratories',json={'name':'Novo laboratório','location':'Novo bloco','active':True},headers=manager).status_code==403
    assert client.post('/api/laboratories',json={'name':'Novo laboratório','location':'Novo bloco','active':True},headers=technician).status_code==201
    assert client.get('/api/users',headers=technician).status_code==403
    assert client.get('/api/settings',headers=manager).status_code==200
    assert client.put('/api/settings',headers=technician,json={'cpu_alert_threshold':70,'memory_alert_threshold':80,'disk_alert_threshold':90,'stale_after_seconds':600}).status_code==403


def test_admin_manage_users_and_self_guard(client):
    h=auth(client)
    r=client.post('/api/users',headers=h,json={'name':'Usuario Externo','email':'external@example.org','password':'MyStrongPwd1234','role':'GESTOR'})
    assert r.status_code==201
    assert len(client.get('/api/users',headers=h).json())==4
    assert client.patch(f"/api/users/{r.json()['id']}/status?active=false",headers=h).status_code==200
    assert client.patch('/api/users/1/status?active=false',headers=h).status_code==409
    assert client.post('/api/users',headers=h,json={'name':'Usuario Externo','email':'external@example.org','password':'MyStrongPwd1234','role':'GESTOR'}).status_code==409


def test_agent_requires_token(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    assert client.post('/api/agent/metrics',json=measurement()).status_code==401
    bad={**agent,'X-Agent-Token':'invalid'}
    assert client.post('/api/agent/metrics',json=measurement(),headers=bad).status_code==401


def test_agent_success_and_dashboard_counts(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    response=client.post('/api/agent/metrics',json=measurement(),headers=agent)
    assert response.status_code==201,response.text
    pcs=client.get('/api/computers',headers=h).json()
    assert pcs[0]['status']=='online'
    assert pcs[0]['latest_metric']['cpu_percent']==40
    assert len(client.get(f"/api/computers/{c['id']}/metrics",headers=h).json())==1
    dashboard=client.get('/api/dashboard/summary',headers=h).json()
    assert dashboard['online']==1
    assert dashboard['computers']==1


def test_agent_rejects_metrics_out_of_range(client):
    h=auth(client)
    _,_,agent=setup_agent(client,h)
    assert client.post('/api/agent/metrics',json=measurement(cpu=120),headers=agent).status_code==422
    assert client.post('/api/agent/metrics',json=measurement(ram=-1),headers=agent).status_code==422


def test_agent_rejects_future_and_old_timestamps(client):
    h=auth(client)
    _,_,agent=setup_agent(client,h)
    assert client.post('/api/agent/metrics',json=measurement(stamp=datetime.now(timezone.utc)+timedelta(days=1)),headers=agent).status_code==422
    assert client.post('/api/agent/metrics',json=measurement(stamp=datetime.now(timezone.utc)-timedelta(days=3)),headers=agent).status_code==422


def test_token_rotation_and_revocation(client):
    h=auth(client)
    _,c,agent=setup_agent(client,h)
    t2=client.post(f"/api/computers/{c['id']}/token",headers=h).json()['agent_token']
    assert agent['X-Agent-Token']!=t2
    assert client.post('/api/agent/metrics',json=measurement(),headers=agent).status_code==401
    agent['X-Agent-Token']=t2
    assert client.post('/api/agent/metrics',json=measurement(),headers=agent).status_code==201
    assert client.delete(f"/api/computers/{c['id']}/token",headers=h).status_code==200
    assert client.post('/api/agent/metrics',json=measurement(),headers=agent).status_code==401


def test_alerts_creation_and_acknowledgement(client):
    h=auth(client)
    _,c,agent=setup_agent(client,h)
    assert client.post('/api/agent/metrics',json=measurement(cpu=98),headers=agent).status_code==201
    alerts=client.get('/api/alerts?state=open',headers=h).json()
    assert len(alerts)==1 and alerts[0]['type']=='cpu'
    assert client.patch(f"/api/alerts/{alerts[0]['id']}/acknowledge",headers=h).status_code==200
    assert client.get('/api/alerts?state=acknowledged',headers=h).json()[0]['status']=='acknowledged'


def test_alert_auto_resolves_on_recovery(client):
    h=auth(client)
    _,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(cpu=98),headers=agent)
    client.post('/api/agent/metrics',json=measurement(cpu=40),headers=agent)
    assert len(client.get('/api/alerts?state=resolved',headers=h).json())==1
    assert len(client.get('/api/alerts?state=open',headers=h).json())==0


def test_alert_does_not_duplicate_when_still_high(client):
    h=auth(client)
    _,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(cpu=99),headers=agent)
    client.post('/api/agent/metrics',json=measurement(cpu=98),headers=agent)
    assert len(client.get('/api/alerts?state=open',headers=h).json())==1


def test_indicator_has_no_fake_score_before_collection(client):
    h=auth(client)
    l=lab(client,h)
    pc(client,h,l['id'])
    indicator=client.get('/api/indicators',headers=h).json()[0]
    assert indicator['score'] is None
    assert indicator['coverage']==0


def test_indicator_score_and_snapshot_after_collection(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(cpu=10,ram=20,disk=30),headers=agent)
    i=client.get('/api/indicators',headers=h).json()[0]
    assert i['score'] is not None and 0 <= i['score'] <= 100
    assert i['coverage']==100
    assert len(client.get(f"/api/indicators/{l['id']}/history",headers=h).json())==1


def test_stale_metrics_signal_offline(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(),headers=agent)
    with client.Session() as db:
        item=db.get(Computer,c['id']);item.last_seen_at=datetime.now(timezone.utc)-timedelta(hours=1);db.commit()
    assert client.get('/api/computers',headers=h).json()[0]['status']=='offline'
    assert client.get('/api/indicators',headers=h).json()[0]['score'] is None


def test_admin_changes_thresholds(client):
    h=auth(client)
    body={'cpu_alert_threshold':75,'memory_alert_threshold':76,'disk_alert_threshold':77,'stale_after_seconds':120}
    assert client.put('/api/settings',json=body,headers=h).status_code==200
    assert client.get('/api/settings',headers=h).json()['cpu_alert_threshold']==75


def test_reports_csv_download(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(),headers=agent)
    r=client.get('/api/reports/metrics.csv',headers=h)
    assert r.status_code==200 and 'text/csv' in r.headers['content-type']
    assert 'Windows Server' in r.text
    assert client.get('/api/reports/indicators.csv',headers=h).status_code==200


def test_reports_protected_by_terms(client):
    h=auth(client,accept=False)
    assert client.get('/api/reports/metrics.csv',headers=h).status_code==428


def test_csv_formula_injection_is_escaped(client):
    h=auth(client)
    l=lab(client,h,name='=HYPERLINK("bad")')
    res=client.get('/api/reports/indicators.csv',headers=h)
    assert "'=HYPERLINK" in res.text


def test_hyperv_import_registers_vms(client):
    h=auth(client)
    l=lab(client,h)
    vms=[{'vm_id':'881d99c5-aaaa-4bbb-9ccc-000000000001','name':'VM One','state':'Running'},{'vm_id':'881d99c5-aaaa-4bbb-9ccc-000000000002','name':'VM Two','state':'Off'}]
    r=client.post('/api/hyperv/import',headers=h,json={'laboratory_id':l['id'],'vms':vms})
    assert r.status_code==200,r.text
    assert r.json()['created']==2
    data=client.get('/api/computers',headers=h).json()
    assert len(data)==2 and all(x['source']=='hyperv' for x in data)
    assert all(x['status']=='sem_coleta' for x in data)
    vms[0]['state']='Paused'
    r2=client.post('/api/hyperv/import',headers=h,json={'laboratory_id':l['id'],'vms':vms})
    assert r2.json()['created']==0 and r2.json()['updated']==2


def test_hyperv_import_rejects_missing_lab(client):
    h=auth(client)
    r=client.post('/api/hyperv/import',headers=h,json={'laboratory_id':999,'vms':[{'vm_id':'some-vm-id','name':'VM','state':'Running'}]})
    assert r.status_code==404


def test_hyperv_import_rejects_manager(client):
    h=auth(client,'GESTOR')
    r=client.post('/api/hyperv/import',headers=h,json={'laboratory_id':1,'vms':[{'vm_id':'some-vm-id','name':'VM','state':'Running'}]})
    assert r.status_code==403


def test_audit_log_tracks_actions(client):
    h=auth(client)
    lab(client,h)
    a=client.get('/api/audit',headers=h).json()
    assert any(x['action']=='laboratory.create' for x in a)
    assert any(x['action']=='terms.accept' for x in a)


def test_computer_delete_cascades_metrics(client):
    h=auth(client)
    l,c,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',json=measurement(),headers=agent)
    assert client.delete(f"/api/computers/{c['id']}",headers=h).status_code==204
    with client.Session() as db:
        assert db.query(Metric).count()==0
