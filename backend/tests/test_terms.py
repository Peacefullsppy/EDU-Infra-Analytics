from datetime import datetime, timedelta, timezone
import jwt
import pytest
from app.core import settings
from app.models import TermAcceptance, TermDocument, User
from .conftest import auth, lab


def test_public_terms_access_without_login(client):
    result = client.get('/api/public/terms/current')
    assert result.status_code == 200
    assert result.json()['version'] == '1.0'


def test_login_requires_terms_before_business_access(client):
    h=auth(client,accept=False)
    assert client.get('/api/auth/me',headers=h).json()['terms_accepted'] is False
    assert client.get('/api/laboratories',headers=h).status_code == 428
    assert client.get('/api/computers',headers=h).status_code == 428
    assert client.get('/api/dashboard/summary',headers=h).status_code == 428
    assert client.get('/api/terms/current',headers=h).json()['accepted'] is False


def test_accept_unlocks_application(client):
    h=auth(client,accept=False)
    response=client.post('/api/terms/accept',json={'version':'1.0','accepted':True},headers=h)
    assert response.status_code==200
    assert client.get('/api/laboratories',headers=h).status_code==428
    h={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get('/api/laboratories',headers=h).status_code==200
    assert client.get('/api/auth/me',headers=h).json()['terms_accepted'] is True


def test_accept_requires_explicit_true(client):
    h=auth(client,accept=False)
    assert client.post('/api/terms/accept',json={'version':'1.0','accepted':False},headers=h).status_code==422


def test_accept_rejects_outdated_version(client):
    h=auth(client,accept=False)
    assert client.post('/api/terms/accept',json={'version':'0.9','accepted':True},headers=h).status_code==409


def test_accept_idempotent_without_duplicate_entries(client):
    h=auth(client)
    assert client.post('/api/terms/accept',json={'version':'1.0','accepted':True},headers=h).status_code==200
    with client.Session() as db:
        assert db.query(TermAcceptance).count()==1


def test_terms_update_forces_every_user_to_accept_again(client):
    h=auth(client)
    payload={'version':'2.0','title':'Termos e Condições Atualizados','content':'Novas obrigações e condições de uso. '*12}
    assert client.post('/api/terms/publish',json=payload,headers=h).status_code==201
    assert client.get('/api/laboratories',headers=h).status_code==428
    assert client.get('/api/terms/current',headers=h).json()['version']=='2.0'
    assert client.post('/api/terms/accept',json={'version':'1.0','accepted':True},headers=h).status_code==409
    response=client.post('/api/terms/accept',json={'version':'2.0','accepted':True},headers=h)
    assert response.status_code==200
    h={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get('/api/laboratories',headers=h).status_code==200
    assert client.get('/api/terms/acceptances',headers=h).status_code==200
    with client.Session() as db:
        assert db.query(TermDocument).filter_by(active=True).count()==1


def test_duplicate_terms_version_is_rejected(client):
    h=auth(client)
    assert client.post('/api/terms/publish',headers=h,json={'version':'1.0','title':'Termos repetidos','content':'x'*180}).status_code==409


def test_only_admin_can_publish_terms(client):
    h=auth(client,'GESTOR')
    assert client.post('/api/terms/publish',headers=h,json={'version':'2.0','title':'Novos termos de uso','content':'x'*180}).status_code==403


def test_protected_endpoints_reject_missing_token(client):
    for path in ['/api/laboratories','/api/computers','/api/alerts','/api/users','/api/audit']:
        assert client.get(path).status_code==401


def test_forged_and_expired_tokens_rejected(client):
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer xxx.yyy.zzz'}).status_code==401
    token=jwt.encode({'sub':'1','iat':datetime.now(timezone.utc)-timedelta(days=4),'exp':datetime.now(timezone.utc)-timedelta(days=3),'type':'access'},settings.jwt_secret_key,algorithm='HS256')
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401


def test_invalid_password_rejected(client):
    assert client.post('/api/auth/login',json={'email':'admin@example.org','password':'wrong'}).status_code==401


def test_every_new_login_requires_session_terms_confirmation(client):
    first = auth(client)
    assert client.get('/api/laboratories',headers=first).status_code == 200
    second = auth(client,accept=False)
    assert client.get('/api/auth/me',headers=second).json()['terms_accepted'] is False
    assert client.get('/api/laboratories',headers=second).status_code == 428
    result = client.post('/api/terms/accept',json={'version':'1.0','accepted':True},headers=second)
    assert result.status_code == 200
    second_new = {'Authorization': 'Bearer ' + result.json()['access_token']}
    assert client.get('/api/laboratories',headers=second_new).status_code == 200
