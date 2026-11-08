"""Jornadas E2E da API com todas as camadas reais, em banco temporário independente."""
from datetime import datetime, timezone
import csv
import io
import pytest
from tests.conftest import auth,lab,pc,measurement,setup_agent


@pytest.mark.e2e
def test_first_access_accept_terms_create_lab_vm_measure_review_export_delete(client):
    login=client.post('/api/auth/login',json={'email':'admin@example.org','password':'TestPassword1234!'})
    assert login.status_code==200 and login.json()['terms_accepted'] is False
    pre={'Authorization':'Bearer '+login.json()['access_token']}
    assert client.get('/api/dashboard/summary',headers=pre).status_code==428
    document=client.get('/api/public/terms/current').json()
    accepted=client.post('/api/terms/accept',headers=pre,json={'version':document['version'],'accepted':True})
    assert accepted.status_code==200
    head={'Authorization':'Bearer '+accepted.json()['access_token']}
    l=lab(client,head,'Laboratório E2E','Bloco Z');c=pc(client,head,l['id'],'VM Lab E2E','E2E-HOST')
    issued=client.post(f"/api/computers/{c['id']}/token",headers=head).json()['agent_token']
    a={'X-Computer-ID':str(c['id']),'X-Agent-Token':issued}
    assert client.post('/api/agent/metrics',headers=a,json=measurement(cpu=99,ram=35,disk=20)).status_code==201
    assert client.get('/api/dashboard/summary',headers=head).json()['online']==1
    assert client.get('/api/indicators',headers=head).json()[0]['coverage']==100
    alerts=client.get('/api/alerts?state=open',headers=head).json()
    assert len(alerts)==1 and alerts[0]['type']=='cpu'
    assert client.patch(f"/api/alerts/{alerts[0]['id']}/acknowledge",headers=head).status_code==200
    downloaded=client.get('/api/reports/metrics.csv',headers=head)
    assert downloaded.status_code==200 and 'E2E-HOST' in downloaded.text
    assert client.delete(f"/api/laboratories/{l['id']}",headers=head).status_code==409
    assert client.delete(f"/api/computers/{c['id']}",headers=head).status_code==204
    assert client.delete(f"/api/laboratories/{l['id']}",headers=head).status_code==204


@pytest.mark.e2e
def test_each_login_requires_terms_again_even_if_version_previously_accepted(client):
    h=auth(client)
    assert client.get('/api/dashboard/summary',headers=h).status_code==200
    fresh=auth(client,accept=False)
    assert client.get('/api/dashboard/summary',headers=fresh).status_code==428
    assert client.get('/api/auth/me',headers=fresh).json()['terms_accepted'] is False
    assert client.get('/api/terms/current',headers=fresh).json()['accepted'] is True
    assert client.get('/api/dashboard/summary',headers=h).status_code==200


@pytest.mark.e2e
def test_new_terms_revokes_privilege_of_existing_sessions(client):
    old=auth(client)
    publish={'version':'e2e.1','title':'Termos atualizados da plataforma','content':'Novo documento. '*20}
    assert client.post('/api/terms/publish',json=publish,headers=old).status_code==201
    assert client.get('/api/laboratories',headers=old).status_code==428
    assert client.post('/api/terms/accept',headers=old,json={'version':'1.0','accepted':True}).status_code==409
    r=client.post('/api/terms/accept',headers=old,json={'version':'e2e.1','accepted':True})
    assert r.status_code==200
    renewed={'Authorization':'Bearer '+r.json()['access_token']}
    assert client.get('/api/laboratories',headers=renewed).status_code==200


@pytest.mark.e2e
def test_agent_token_is_independent_from_user_session_and_rotates(client):
    h=auth(client);_,c,a=setup_agent(client,h)
    assert client.post('/api/agent/metrics',json=measurement(),headers=a).status_code==201
    old=a.copy()
    new=client.post(f"/api/computers/{c['id']}/token",headers=h).json()['agent_token']
    assert client.post('/api/agent/metrics',json=measurement(),headers=old).status_code==401
    a['X-Agent-Token']=new
    assert client.post('/api/agent/metrics',json=measurement(),headers=a).status_code==201
    assert len(client.get(f"/api/computers/{c['id']}/metrics",headers=h).json())==2


@pytest.mark.e2e
def test_technician_can_operate_but_cannot_manage_accounts(client):
    h=auth(client,'TECNICO');l=lab(client,h);pc(client,h,l['id'])
    assert client.get('/api/dashboard/summary',headers=h).json()['computers']==1
    assert client.get('/api/users',headers=h).status_code==403
    assert client.get('/api/audit',headers=h).status_code==403


@pytest.mark.e2e
def test_manager_cannot_write_but_can_read_dashboard_and_reports(client):
    admin=auth(client);l=lab(client,admin)
    mgr=auth(client,'GESTOR')
    assert client.get('/api/dashboard/summary',headers=mgr).json()['laboratories']==1
    assert client.post('/api/laboratories',headers=mgr,json={'name':'Invalido','location':'Sala'}).status_code==403
    assert client.get('/api/reports/indicators.csv',headers=mgr).status_code==200


@pytest.mark.e2e
def test_hyperv_inventory_to_agent_and_history(client):
    h=auth(client);l=lab(client,h)
    vm={'vm_id':'4f6ad010-abcd-4311-aaaa-010101010101','name':'VM Hyper-V E2E','state':'Running'}
    created=client.post('/api/hyperv/import',json={'laboratory_id':l['id'],'vms':[vm]},headers=h)
    assert created.status_code==200 and created.json()['created']==1
    device=client.get('/api/computers',headers=h).json()[0]
    assert device['source']=='hyperv'
    assert device['status']=='sem_coleta'
    key=client.post(f"/api/computers/{device['id']}/token",headers=h).json()['agent_token']
    headers={'X-Computer-ID':str(device['id']),'X-Agent-Token':key}
    assert client.post('/api/agent/metrics',headers=headers,json=measurement()).status_code==201
    assert client.get('/api/computers',headers=h).json()[0]['status']=='online'
    assert len(client.get(f"/api/computers/{device['id']}/metrics",headers=h).json())==1


@pytest.mark.e2e
def test_alert_is_open_acknowledged_and_then_resolved(client):
    h=auth(client);_,pc_info,agent=setup_agent(client,h)
    client.post('/api/agent/metrics',headers=agent,json=measurement(disk=99))
    item=client.get('/api/alerts?state=open',headers=h).json()[0]
    assert client.patch(f"/api/alerts/{item['id']}/acknowledge",headers=h).json()['status']=='acknowledged'
    client.post('/api/agent/metrics',headers=agent,json=measurement(disk=20))
    assert client.get('/api/alerts?state=resolved',headers=h).json()[0]['status']=='resolved'


@pytest.mark.e2e
def test_public_privacy_access_does_not_require_accepting_terms(client):
    r=client.get('/api/public/privacy-notice')
    assert r.status_code==200 and 'LGPD' in r.json()['content']
    assert client.get('/api/public/terms/current').status_code==200
    assert client.get('/api/dashboard/summary').status_code==401
