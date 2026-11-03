"""Cenários independentes, alinhados aos requisitos da Semana 1 e à monografia."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.logic import dashboard_summary, state
from app.models import Computer


def test_login_perfil_e_consulta_do_proprio_usuario(client, headers):
    for role in ("admin", "tecnico", "gestor"):
        response = client.get('/api/v1/auth/me', headers=headers(role))
        assert response.status_code == 200
        assert response.json()['role'] == role
        assert 'password_hash' not in response.json()


def test_token_invalido_retorna_401(client):
    assert client.get('/api/v1/computadores', headers={'Authorization': 'Bearer token.invalido'}).status_code == 401


def test_get_sem_token_retorna_401(client):
    for endpoint in ('/api/v1/dashboard', '/api/v1/computadores', '/api/v1/auditoria'):
        assert client.get(endpoint).status_code == 401


def test_gestor_nao_pode_editar_laboratorio(client, headers):
    admin = headers()
    lab = client.post('/api/v1/laboratorios', headers=admin, json={'name':'Lab 1', 'location':'Bloco 1'}).json()
    gestor = headers('gestor')
    assert client.put(f"/api/v1/laboratorios/{lab['id']}", headers=gestor, json={'name':'Fraude', 'location':'Bloco 2'}).status_code == 403
    assert client.get(f"/api/v1/laboratorios/{lab['id']}", headers=gestor).json()['name'] == 'Lab 1'


def test_tecnico_nao_pode_excluir_laboratorio_sem_computador(client, headers):
    admin = headers()
    lab = client.post('/api/v1/laboratorios', headers=admin, json={'name':'Lab 1','location':'Bloco 1'}).json()
    assert client.delete(f"/api/v1/laboratorios/{lab['id']}", headers=headers('tecnico')).status_code == 403
    assert client.get(f"/api/v1/laboratorios/{lab['id']}", headers=admin).status_code == 200


def test_computador_ocupando_laboratorio_impede_delete_409_e_nao_remove_dados(client, headers):
    admin = headers()
    lab = client.post('/api/v1/laboratorios', headers=admin, json={'name':'Laboratório ocupado','location':'Prédio A'}).json()
    pc = client.post('/api/v1/computadores', headers=admin, json={'hostname':'LAB-A-01','laboratory_id':lab['id']}).json()
    response = client.delete(f"/api/v1/laboratorios/{lab['id']}", headers=admin)
    assert response.status_code == 409
    assert 'computadores' in response.json()['detail'].lower()
    assert client.get(f"/api/v1/laboratorios/{lab['id']}", headers=admin).json()['computer_count'] == 1
    assert client.get(f"/api/v1/computadores/{pc['id']}", headers=admin).status_code == 200
    assert not [a for a in client.get('/api/v1/auditoria', headers=admin).json() if a['entity']=='laboratory' and a['action']=='DELETE']


def test_computador_nao_pode_mudar_para_laboratorio_inexistente(client, headers):
    admin = headers()
    lab = client.post('/api/v1/laboratorios', headers=admin, json={'name':'Lab 1', 'location':'Bloco 1'}).json()
    pc = client.post('/api/v1/computadores', headers=admin, json={'hostname':'PC-001','laboratory_id':lab['id']}).json()
    assert client.put(f"/api/v1/computadores/{pc['id']}", headers=admin, json={'hostname':'PC-001','laboratory_id':99999}).status_code == 404
    assert client.get(f"/api/v1/computadores/{pc['id']}", headers=admin).json()['laboratory_id'] == lab['id']


def test_hostname_duplicado_na_edicao_retorna_409(client, headers):
    admin = headers()
    lab = client.post('/api/v1/laboratorios', headers=admin, json={'name':'Lab 1', 'location':'Bloco 1'}).json()
    first = client.post('/api/v1/computadores', headers=admin, json={'hostname':'LAB-1','laboratory_id':lab['id']}).json()
    second = client.post('/api/v1/computadores', headers=admin, json={'hostname':'LAB-2','laboratory_id':lab['id']}).json()
    assert client.put(f"/api/v1/computadores/{second['id']}", headers=admin, json={'hostname':first['hostname'],'laboratory_id':lab['id']}).status_code == 409
    assert client.get(f"/api/v1/computadores/{second['id']}", headers=admin).json()['hostname'] == 'LAB-2'


def test_filtro_de_computadores_por_laboratorio(client, headers):
    admin = headers()
    ids=[]
    for i in range(2):
        ids.append(client.post('/api/v1/laboratorios', headers=admin, json={'name':f'Lab {i}','location':'Bloco'}).json()['id'])
    for i, lab_id in enumerate(ids):
        client.post('/api/v1/computadores', headers=admin, json={'hostname':f'PC-{i}','laboratory_id':lab_id})
    response = client.get(f'/api/v1/computadores?laboratory_id={ids[0]}', headers=admin)
    assert response.status_code == 200 and len(response.json()) == 1
    assert response.json()[0]['laboratory_id'] == ids[0]


def test_apenas_admin_pode_criar_usuarios(client, headers):
    payload={'name':'Pessoa Teste','email':'pessoa@example.org','password':'SenhaSegura123!','role':'gestor'}
    assert client.post('/api/v1/users', headers=headers('tecnico'), json=payload).status_code == 403
    assert client.post('/api/v1/users', headers=headers('gestor'), json=payload).status_code == 403
    assert client.post('/api/v1/users', headers=headers(), json=payload).status_code == 201


def test_auditoria_registra_criacao_edicao_e_exclusao(client, headers):
    admin=headers()
    lab=client.post('/api/v1/laboratorios', headers=admin, json={'name':'Lab 1', 'location':'Bloco 1'}).json()
    client.put(f"/api/v1/laboratorios/{lab['id']}", headers=admin, json={'name':'Lab 2','location':'Bloco 2'})
    client.delete(f"/api/v1/laboratorios/{lab['id']}", headers=admin)
    logs=client.get('/api/v1/auditoria', headers=admin).json()
    actions=[x['action'] for x in logs if x['entity']=='laboratory' and x['entity_id']==lab['id']]
    assert actions == ['DELETE','UPDATE','CREATE']
    assert all(x['user_id'] is not None for x in logs if x['entity']=='laboratory')


def test_disponibilidade_conta_online_atencao_e_critico_sem_inventar_medicao():
    now=datetime.now(timezone.utc)
    base=dict(laboratory_id=1, hostname='TEST')
    no_data=Computer(**base)
    assert state(no_data) == 'sem_coleta'
    assert state(Computer(**base, last_seen_at=now, cpu_percent=85)) == 'atencao'
    assert state(Computer(**base, last_seen_at=now, ram_percent=96)) == 'critico'
    assert state(Computer(**base, last_seen_at=now - timedelta(minutes=30))) == 'offline'
