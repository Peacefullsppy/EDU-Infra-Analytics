"""Fluxos que confirmam integridade SQL, filtros, métricas, auditoria e CSV."""
import csv
import io
from datetime import datetime,timedelta,timezone
import pytest
from sqlalchemy import func,select
from app.models import Alert, AuditLog, Computer, IndicatorSnapshot, Laboratory, Metric
from tests.conftest import auth,lab,pc,measurement,setup_agent


@pytest.mark.integration
@pytest.mark.parametrize('alias', [' laboratório a ','LABORATÓRIO A','Laboratório  A'])
def test_lab_normalization_rejects_duplicate_alias(client,alias):
    head=auth(client)
    lab(client,head,name='Laboratório A',location='Sala Azul')
    res=client.post('/api/laboratories',headers=head,json={'name':alias,'location':'Sala Azul'})
    assert res.status_code==409


@pytest.mark.integration
@pytest.mark.parametrize('query,expect', [
    ('biblioteca',1),('LAB A',1),('sala',2),('xxxxx',0),('',2)
])
def test_lab_search_filter_case_insensitive(client,query,expect):
    head=auth(client)
    lab(client,head,name='LAB A',location='Sala 101')
    lab(client,head,name='Biblioteca',location='Sala 102')
    assert len(client.get('/api/laboratories',headers=head,params={'q':query}).json())==expect


@pytest.mark.integration
def test_lab_active_filter_and_update(client):
    head=auth(client)
    l=lab(client,head)
    change=client.put(f"/api/laboratories/{l['id']}",headers=head,json={'name':'Alterado','location':'Sala 20','active':False})
    assert change.status_code==200
    assert len(client.get('/api/laboratories?active=false',headers=head).json())==1
    assert len(client.get('/api/laboratories?active=true',headers=head).json())==0


@pytest.mark.integration
def test_deleting_lab_with_pc_fails_without_losing_records(client):
    head=auth(client)
    l=lab(client,head);c=pc(client,head,l['id'])
    assert client.delete(f"/api/laboratories/{l['id']}",headers=head).status_code==409
    assert len(client.get('/api/laboratories',headers=head).json())==1
    assert len(client.get('/api/computers',headers=head).json())==1


@pytest.mark.integration
def test_deleting_pc_then_lab_succeeds(client):
    head=auth(client)
    l=lab(client,head);c=pc(client,head,l['id'])
    assert client.delete(f"/api/computers/{c['id']}",headers=head).status_code==204
    assert client.delete(f"/api/laboratories/{l['id']}",headers=head).status_code==204
    assert client.get('/api/laboratories',headers=head).json()==[]


@pytest.mark.integration
@pytest.mark.parametrize('address', ['192.168.1.1','::1'])
def test_pc_persists_normalized_ip_address(client,address):
    head=auth(client);l=lab(client,head)
    c=client.post('/api/computers',headers=head,json={'laboratory_id':l['id'],'name':'Servidor','hostname':'SRV-01','ip_address':address})
    assert c.status_code==201 and c.json()['ip_address']==address


@pytest.mark.integration
@pytest.mark.parametrize('query,expected', [('vm',2),('pc-02',1),('inexistente',0)])
def test_pc_search_matches_host_and_name(client,query,expected):
    head=auth(client);l=lab(client,head)
    pc(client,head,l['id'],name='VM A',hostname='pc-01')
    pc(client,head,l['id'],name='VM B',hostname='pc-02')
    assert len(client.get('/api/computers',params={'q':query},headers=head).json())==expected


@pytest.mark.integration
def test_pc_filter_isolated_by_laboratory(client):
    head=auth(client);la=lab(client,head,name='Lab A',location='sala');lb=lab(client,head,name='Lab B',location='sala')
    pc(client,head,la['id'],name='VM A',hostname='vm1')
    pc(client,head,lb['id'],name='VM B',hostname='vm1')
    assert len(client.get('/api/computers',params={'laboratory_id':la['id']},headers=head).json())==1
    assert len(client.get('/api/computers',params={'laboratory_id':lb['id']},headers=head).json())==1


@pytest.mark.integration
def test_token_rotation_stores_digest_not_token(client):
    head=auth(client);_,c,agent=setup_agent(client,head)
    with client.Session() as db:
        item=db.get(Computer,c['id'])
        assert item.agent_token_hash != agent['X-Agent-Token']
        assert len(item.agent_token_hash)==64


@pytest.mark.integration
@pytest.mark.parametrize('field,bad', [('cpu_percent',101),('memory_percent',-1),('disk_percent',-1),('uptime_seconds',-10),('os_name','x')])
def test_invalid_metric_is_not_committed(client,field,bad):
    head=auth(client);_,c,agent=setup_agent(client,head)
    data=measurement();data[field]=bad
    assert client.post('/api/agent/metrics',headers=agent,json=data).status_code==422
    with client.Session() as db:
        assert db.scalar(select(func.count(Metric.id)))==0
        assert db.scalar(select(func.count(IndicatorSnapshot.id)))==0


@pytest.mark.integration
def test_unregistered_agent_cannot_write_database(client):
    head=auth(client);_,c,agent=setup_agent(client,head)
    agent['X-Agent-Token']='eia_wrong'
    assert client.post('/api/agent/metrics',headers=agent,json=measurement()).status_code==401
    with client.Session() as db: assert db.scalar(select(func.count(Metric.id)))==0


@pytest.mark.integration
@pytest.mark.parametrize('cpu,ram,disk,expected_types', [
    (95,20,20,{'cpu'}),(20,95,20,{'memory'}),(20,20,95,{'disk'}),
    (95,96,97,{'cpu','memory','disk'}),(20,20,20,set()),
])
def test_agent_alert_types_follow_configured_thresholds(client,cpu,ram,disk,expected_types):
    head=auth(client);_,c,agent=setup_agent(client,head)
    response=client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=cpu,ram=ram,disk=disk))
    assert response.status_code==201
    alerts=client.get('/api/alerts?state=open',headers=head).json()
    assert {a['type'] for a in alerts}==expected_types


@pytest.mark.integration
def test_agent_recovery_resolves_all_open_alerts(client):
    head=auth(client);_,c,agent=setup_agent(client,head)
    assert client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=99,ram=99,disk=99)).status_code==201
    assert len(client.get('/api/alerts?state=open',headers=head).json())==3
    assert client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=40,ram=40,disk=40)).status_code==201
    assert len(client.get('/api/alerts?state=open',headers=head).json())==0
    assert len(client.get('/api/alerts?state=resolved',headers=head).json())==3


@pytest.mark.integration
def test_deleted_pc_cascades_alerts_metrics_and_indicators(client):
    head=auth(client);l,c,agent=setup_agent(client,head)
    assert client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=99)).status_code==201
    assert client.delete(f"/api/computers/{c['id']}",headers=head).status_code==204
    with client.Session() as db:
        assert db.scalar(select(func.count(Metric.id)))==0
        assert db.scalar(select(func.count(Alert.id)))==0
        # Snapshots intentionally remain linked to laboratory, not computer.
        assert db.scalar(select(func.count(IndicatorSnapshot.id)))==1


@pytest.mark.integration
def test_indicators_not_faked_with_no_computers(client):
    head=auth(client)
    lab(client,head)
    result=client.get('/api/indicators',headers=head).json()
    assert len(result)==1 and result[0]['score'] is None
    assert result[0]['classification']=='sem_dados'


@pytest.mark.integration
def test_metrics_history_descending_and_limited(client):
    head=auth(client);_,c,agent=setup_agent(client,head)
    for cpu in [22,44,66]:
        client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=cpu))
    items=client.get(f"/api/computers/{c['id']}/metrics?limit=2",headers=head).json()
    assert len(items)==2
    assert all('cpu_percent' in m for m in items)


@pytest.mark.integration
@pytest.mark.parametrize('limit', [0,501,-1])
def test_metric_history_limit_is_restricted(client,limit):
    head=auth(client);l=lab(client,head);c=pc(client,head,l['id'])
    assert client.get(f"/api/computers/{c['id']}/metrics",params={'limit':limit},headers=head).status_code==422


@pytest.mark.integration
@pytest.mark.parametrize('limit', [0,501,-1])
def test_audit_limit_is_restricted(client,limit):
    head=auth(client)
    assert client.get('/api/audit',params={'limit':limit},headers=head).status_code==422


@pytest.mark.integration
def test_reports_empty_database_contain_only_headers(client):
    head=auth(client)
    text=client.get('/api/reports/metrics.csv',headers=head).text
    assert 'Medição' in text and 'CPU' in text
    rows=list(csv.reader(io.StringIO(text.lstrip('\ufeff')), delimiter=';'))
    assert len(rows)==1


@pytest.mark.integration
def test_filtered_csv_exports_exact_computer(client):
    head=auth(client);l=lab(client,head)
    c1=pc(client,head,l['id'],name='VM A',hostname='vm-a')
    c2=pc(client,head,l['id'],name='VM B',hostname='vm-b')
    for c in [c1,c2]:
        token=client.post(f"/api/computers/{c['id']}/token",headers=head).json()['agent_token']
        agent={'X-Computer-ID':str(c['id']),'X-Agent-Token':token}
        assert client.post('/api/agent/metrics',headers=agent,json=measurement()).status_code==201
    csv_data=client.get('/api/reports/metrics.csv',params={'computer_id':c1['id']},headers=head).text
    assert 'vm-a' in csv_data and 'vm-b' not in csv_data


@pytest.mark.integration
def test_audit_does_not_log_agent_token_plaintext(client):
    head=auth(client);_,c,agent=setup_agent(client,head)
    content=str(client.get('/api/audit',headers=head).json())
    assert agent['X-Agent-Token'] not in content
    assert 'computer.token.rotate' in content


@pytest.mark.integration
def test_manager_can_read_reports_but_cannot_acknowledge_alert(client):
    admin=auth(client);manager=auth(client,'GESTOR')
    _,c,agent=setup_agent(client,admin)
    client.post('/api/agent/metrics',headers=agent,json=measurement(cpu=99))
    a=client.get('/api/alerts',headers=manager).json()[0]
    assert client.get('/api/reports/metrics.csv',headers=manager).status_code==200
    assert client.patch(f"/api/alerts/{a['id']}/acknowledge",headers=manager).status_code==403


@pytest.mark.integration
def test_deactivated_user_token_is_revoked_immediately(client):
    admin=auth(client)
    created=client.post('/api/users',headers=admin,json={'name':'Demo Gestor','email':'demo@example.org','password':'SecurePassword123!','role':'GESTOR'}).json()
    token=client.post('/api/auth/login',json={'email':'demo@example.org','password':'SecurePassword123!'}).json()['access_token']
    assert client.patch(f"/api/users/{created['id']}/status?active=false",headers=admin).status_code==200
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401


@pytest.mark.integration
def test_hyperv_sync_preserves_existing_agent_credentials(client):
    head=auth(client);l=lab(client,head)
    vm={'vm_id':'94d7caff-0b0c-40ce-a6c5-887b3d884b3b','name':'VM Original','state':'Running'}
    result=client.post('/api/hyperv/import',headers=head,json={'laboratory_id':l['id'],'vms':[vm]})
    assert result.status_code==200
    device=client.get('/api/computers',headers=head).json()[0]
    token=client.post(f"/api/computers/{device['id']}/token",headers=head).json()['agent_token']
    vm.update(name='VM Renomeada',state='Paused')
    assert client.post('/api/hyperv/import',headers=head,json={'laboratory_id':l['id'],'vms':[vm]}).status_code==200
    with client.Session() as db:
        entity=db.get(Computer,device['id'])
        assert entity.name=='VM Renomeada' and entity.hyperv_state=='Paused'
        from app.core import agent_token_hash
        assert entity.agent_token_hash == agent_token_hash(token)


@pytest.mark.integration
@pytest.mark.parametrize('entity,payload', [
    ('/api/laboratories',{'name':'  ','location':'Sala A'}),
    ('/api/laboratories',{'name':'Lab','location':'   '}),
    ('/api/computers',{'laboratory_id':1,'name':'PC','hostname':'   '}),
])
def test_api_rejects_blank_identifiers_before_database_write(client,entity,payload):
    head=auth(client)
    if entity.endswith('/computers'):
        lab(client,head)
    assert client.post(entity,headers=head,json=payload).status_code==422
    with client.Session() as db:
        if entity.endswith('/laboratories'):
            assert db.scalar(select(func.count(Laboratory.id)))==0
        else:
            assert db.scalar(select(func.count(Computer.id)))==0
