"""Matriz real de permissões e aceite, utilizando cliente HTTP + banco isolado."""
import pytest
from tests.conftest import auth,lab,pc

READ_URLS=[
    '/api/laboratories','/api/computers','/api/alerts','/api/indicators',
    '/api/dashboard/summary','/api/settings','/api/reports/metrics.csv',
    '/api/reports/indicators.csv'
]


@pytest.mark.integration
@pytest.mark.parametrize('endpoint',READ_URLS)
def test_read_endpoints_reject_missing_authorization(client,endpoint):
    assert client.get(endpoint).status_code==401


@pytest.mark.integration
@pytest.mark.parametrize('endpoint',READ_URLS)
def test_read_endpoints_reject_login_without_terms(client,endpoint):
    header=auth(client,accept=False)
    assert client.get(endpoint,headers=header).status_code==428


@pytest.mark.integration
@pytest.mark.parametrize('role', ['ADMIN','TECNICO','GESTOR'])
@pytest.mark.parametrize('endpoint',READ_URLS)
def test_all_roles_can_read_operational_resources(client,role,endpoint):
    header=auth(client,role)
    assert client.get(endpoint,headers=header).status_code==200


@pytest.mark.integration
@pytest.mark.parametrize('endpoint', ['/api/users','/api/audit','/api/terms/acceptances'])
@pytest.mark.parametrize('role', ['TECNICO','GESTOR'])
def test_admin_only_views_reject_nonadmins(client,endpoint,role):
    assert client.get(endpoint,headers=auth(client,role)).status_code==403


@pytest.mark.integration
@pytest.mark.parametrize('endpoint', ['/api/users','/api/audit','/api/terms/acceptances'])
def test_admin_only_views_accept_admin(client,endpoint):
    assert client.get(endpoint,headers=auth(client)).status_code==200


@pytest.mark.integration
@pytest.mark.parametrize('role', ['TECNICO','GESTOR'])
def test_nonadmins_cannot_change_monitoring_thresholds(client,role):
    payload={'cpu_alert_threshold':70,'memory_alert_threshold':70,'disk_alert_threshold':70,'stale_after_seconds':120}
    assert client.put('/api/settings',headers=auth(client,role),json=payload).status_code==403


@pytest.mark.integration
@pytest.mark.parametrize('role', ['ADMIN','TECNICO'])
def test_editors_can_create_labs_and_computers(client,role):
    header=auth(client,role)
    laboratory=lab(client,header)
    computer=pc(client,header,laboratory['id'])
    assert computer['laboratory_id']==laboratory['id']


@pytest.mark.integration
@pytest.mark.parametrize('method,path,body', [
    ('POST','/api/laboratories',{'name':'Novo laboratório','location':'Bloco A'}),
    ('POST','/api/computers',{'laboratory_id':1,'name':'PC 01','hostname':'pc-01'}),
    ('POST','/api/hyperv/import',{'laboratory_id':1,'vms':[{'vm_id':'vm-guid','name':'vm','state':'Running'}]}),
    ('POST','/api/users',{'name':'User','email':'foo@example.org','password':'SecurePassword123!'}),
])
def test_manager_cannot_mutate_resources(client,method,path,body):
    assert client.request(method,path,json=body,headers=auth(client,'GESTOR')).status_code==403


@pytest.mark.integration
@pytest.mark.parametrize('path', ['/api/computers/999/metrics','/api/indicators/999/history'])
def test_unknown_resource_histories_return_404(client,path):
    assert client.get(path,headers=auth(client)).status_code==404


@pytest.mark.integration
@pytest.mark.parametrize('path', ['/api/computers/999/token','/api/alerts/999/acknowledge'])
def test_unknown_resource_actions_return_404(client,path):
    response=(client.post(path,headers=auth(client)) if 'token' in path else client.patch(path,headers=auth(client)))
    assert response.status_code==404
