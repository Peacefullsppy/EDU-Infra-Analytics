"""Contratos de validação Pydantic: valores de fronteira e entradas hostis."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas import (LabIn, ComputerIn, MetricIn, SettingsIn, TermsPublish,
                         AcceptTerms, UserCreate, HyperVImport)


@pytest.mark.unit
@pytest.mark.parametrize('name,location', [
    ('A', 'Sala 1'), ('', 'Sala 1'), ('  ', 'Sala 1'),
    ('L'*121, 'Sala 1'), ('Laboratório', 'X'), ('Laboratório', ''),
    ('Laboratório', 'A'*181),
])
def test_laboratory_rejects_invalid_inputs(name, location):
    with pytest.raises(ValidationError):
        LabIn(name=name, location=location)


@pytest.mark.unit
@pytest.mark.parametrize('name,host,lab_id', [
    ('X', 'PC01', 1), ('A'*121, 'PC01', 1),
    ('Computer', '', 1), ('Computer', 'X'*121, 1),
    ('Computer', 'PC01', 0), ('Computer', 'PC01', -1),
])
def test_computer_required_fields(name, host, lab_id):
    with pytest.raises(ValidationError):
        ComputerIn(name=name, hostname=host, laboratory_id=lab_id)


@pytest.mark.unit
@pytest.mark.parametrize('address', ['127.0.0.1','192.168.0.254','::1','2001:db8::1'])
def test_computer_accepts_valid_ip(address):
    assert ComputerIn(name='Servidor', hostname='srv', laboratory_id=1, ip_address=address).ip_address == address


@pytest.mark.unit
@pytest.mark.parametrize('address', ['300.1.2.3','invalid','127.0.0.1:8000','2001:db8:::1','10.1.2'])
def test_computer_rejects_invalid_ip(address):
    with pytest.raises(ValidationError):
        ComputerIn(name='Servidor', hostname='srv', laboratory_id=1, ip_address=address)


@pytest.mark.unit
@pytest.mark.parametrize('field,bad', [
    ('cpu_percent', -0.01), ('cpu_percent', 100.01),
    ('memory_percent', -1), ('memory_percent', 101),
    ('disk_percent', -1), ('disk_percent', 100.1),
    ('uptime_seconds', -1), ('os_name', 'X'), ('os_name', 'A'*181),
    ('collected_at', '2026-01-01T12:00:00'),
])
def test_metric_rejects_invalid_fields(field, bad):
    payload = {'cpu_percent': 30, 'memory_percent': 40, 'disk_percent': 50,
               'uptime_seconds': 12, 'os_name': 'Windows 11',
               'collected_at': datetime.now(timezone.utc)}
    payload[field] = bad
    with pytest.raises(ValidationError):
        MetricIn(**payload)


@pytest.mark.unit
@pytest.mark.parametrize('usage', [0, 50, 100])
def test_metric_accepts_valid_usage_boundaries(usage):
    payload = MetricIn(cpu_percent=usage, memory_percent=usage, disk_percent=usage,
                       uptime_seconds=0, os_name='Linux', collected_at=datetime.now(timezone.utc))
    assert payload.cpu_percent == payload.memory_percent == payload.disk_percent == usage


@pytest.mark.unit
@pytest.mark.parametrize('field,bad', [
    ('cpu_alert_threshold',49),('cpu_alert_threshold',101),
    ('memory_alert_threshold',0),('memory_alert_threshold',101),
    ('disk_alert_threshold',49),('disk_alert_threshold',200),
    ('stale_after_seconds',59),('stale_after_seconds',86401),
])
def test_settings_limits(field,bad):
    values = {'cpu_alert_threshold': 90, 'memory_alert_threshold': 90,
              'disk_alert_threshold': 90, 'stale_after_seconds': 600}
    values[field] = bad
    with pytest.raises(ValidationError):
        SettingsIn(**values)


@pytest.mark.unit
@pytest.mark.parametrize('value', ['../etc/passwd', 'termos com espaço', '', 'x'*33, 'térmos'])
def test_terms_publish_rejects_invalid_versions(value):
    with pytest.raises(ValidationError):
        TermsPublish(version=value, title='Termos para avaliação', content='A'*160)


@pytest.mark.unit
@pytest.mark.parametrize('field,value', [('title','X'),('content','A'*149),('content','A'*50001)])
def test_terms_publish_rejects_invalid_content(field,value):
    payload = {'version':'1.6', 'title':'Termos e Condições', 'content':'A'*180}
    payload[field] = value
    with pytest.raises(ValidationError):
        TermsPublish(**payload)


@pytest.mark.unit
@pytest.mark.parametrize('flag', [False, 0, 'false', None])
def test_terms_accept_requires_true(flag):
    with pytest.raises(ValidationError):
        AcceptTerms(version='1.6', accepted=flag)


@pytest.mark.unit
@pytest.mark.parametrize('role', ['SUPERADMIN', 'STUDENT', 'admin', ''])
def test_user_create_restricts_role(role):
    with pytest.raises(ValidationError):
        UserCreate(name='Usuario', email='user@example.org',password='SecurePassword123!',role=role)


@pytest.mark.unit
@pytest.mark.parametrize('field,bad', [
    ('name','A'),('name','A'*121),('email','invalid'),('password','short'),('password','A'*129)
])
def test_user_create_rejects_invalid_credentials(field,bad):
    data = {'name':'Usuario', 'email':'user@example.org', 'password':'SecurePassword123!', 'role':'GESTOR'}
    data[field] = bad
    with pytest.raises(ValidationError):
        UserCreate(**data)


@pytest.mark.unit
@pytest.mark.parametrize('vms', [[],[{'vm_id':'x','name':'VM','state':'On'}],
    [{'vm_id':'valid-vm-id','name':'','state':'On'}],
    [{'vm_id':'valid-vm-id','name':'VM','state':''}],
    [{'vm_id':'valid-vm-id','name':'VM','state':'On'}]*101])
def test_hyperv_inventory_rejects_invalid_payload(vms):
    with pytest.raises(ValidationError):
        HyperVImport(laboratory_id=1,vms=vms)


@pytest.mark.unit
def test_hyperv_inventory_accepts_valid_payload():
    result = HyperVImport(laboratory_id=12,vms=[{'vm_id':'abc-123','name':'VM Aula','state':'Running'}])
    assert result.vms[0].name == 'VM Aula'


@pytest.mark.unit
@pytest.mark.parametrize('schema,payload', [
    (LabIn, {'name':'  ', 'location':'Sala B'}),
    (LabIn, {'name':'Laboratório', 'location':'   '}),
    (ComputerIn, {'name':'  ', 'hostname':'pc1', 'laboratory_id':1}),
    (ComputerIn, {'name':'Computador', 'hostname':'   ', 'laboratory_id':1}),
    (UserCreate, {'name':'  ', 'email':'user@example.org', 'password':'SecurePassword123!'}),
    (TermsPublish, {'version':'1.6', 'title':'Título de Termos', 'content':' '*160}),
    (HyperVImport, {'laboratory_id':1, 'vms':[{'vm_id':'valid-vm-id','name':' ','state':'Running'}]}),
])
def test_whitespace_only_values_are_rejected(schema,payload):
    with pytest.raises(ValidationError):
        schema(**payload)
