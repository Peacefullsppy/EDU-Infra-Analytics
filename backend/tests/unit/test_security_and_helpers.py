"""Hash de credenciais, tokens, normalização, cabeçalhos e CSV."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import jwt
import pytest
from fastapi import HTTPException
from app import core
from app import routes
from app.models import User


@pytest.mark.unit
@pytest.mark.parametrize('password', ['', 'abc', '12345678901', '🔒'*11])
def test_password_minimum_length(password):
    with pytest.raises(ValueError):
        core.hash_password(password)


@pytest.mark.unit
def test_password_hash_is_salted_and_one_way():
    first = core.hash_password('UniquePassword123!')
    second = core.hash_password('UniquePassword123!')
    assert first != second
    assert 'UniquePassword123!' not in first
    assert core.verify_password('UniquePassword123!', first)
    assert not core.verify_password('DifferentPassword1!', first)


@pytest.mark.unit
@pytest.mark.parametrize('encoded', ['', 'invalid', '$argon2id$v=19$bad', '!!!', 'plain'])
def test_password_verify_handles_malformed_encoded_data(encoded):
    assert not core.verify_password('SecurePassword123!', encoded)


@pytest.mark.unit
def test_agent_token_is_random_and_not_stored_plaintext():
    token1, digest1=core.issue_agent_token()
    token2, digest2=core.issue_agent_token()
    assert token1.startswith('eia_') and token2.startswith('eia_')
    assert token1 != token2
    assert len(digest1) == 64 and digest1 != digest2
    assert token1 not in digest1
    assert core.agent_token_hash(token1) == digest1
    assert core.agent_token_hash(token2) != digest1


@pytest.mark.unit
@pytest.mark.parametrize('text,expected', [
    ('  LAB A  ','lab a'),('LAB A','lab a'),('LÁB','láb'),
    ('ＡＢＣ','abc'),('\tSala 01\n','sala 01'),('TÉCNICO','técnico'),
])
def test_normalized_unicode(text,expected):
    assert routes.normalized(text) == expected


@pytest.mark.unit
@pytest.mark.parametrize('text,expected', [
    ('  Bloco  A  ', 'Bloco A'),('A\nB\t C','A B C'),(' X ','X'),('ABC','ABC'),
])
def test_clean_whitespace(text,expected):
    assert routes.clean(text) == expected


@pytest.mark.unit
@pytest.mark.parametrize('text,expected', [
    ('=SUM(1,2)', "'=SUM(1,2)"), ('+CMD',"'+CMD"), ('-1',"'-1"),
    ('@HYPERLINK',"'@HYPERLINK"), ('\tcmd',"'\tcmd"), ('\rdata',"'\rdata"),
    ('Safe','Safe'), ('', ''), (None,''), (42,'42')
])
def test_csv_safe_blocks_spreadsheet_formula_injection(text, expected):
    assert routes.csv_safe(text) == expected


@pytest.mark.unit
def test_create_access_token_declares_session_renewal():
    user = SimpleNamespace(id=42)
    before = core.create_access_token(user)
    after = core.create_access_token(user, '2.1-lgpd')
    p1=jwt.decode(before,core.settings.jwt_secret_key,algorithms=['HS256'])
    p2=jwt.decode(after,core.settings.jwt_secret_key,algorithms=['HS256'])
    assert p1['sub']=='42' and p1['terms_version'] is None
    assert p2['terms_version']=='2.1-lgpd'
    assert p2['type']=='access'
    assert p2['exp'] > p2['iat']


@pytest.mark.unit
@pytest.mark.parametrize('tamper', [
    {'type':'refresh'}, {'sub':'not-a-number'}, {'sub':'999'},
])
def test_invalid_jwt_payload_is_rejected_by_user_lookup(tamper):
    from unittest.mock import Mock
    p={'type':'access','sub':'1','iat':core.utcnow(),'exp':core.utcnow()+timedelta(minutes=3)}
    p.update(tamper)
    token=jwt.encode(p,core.settings.jwt_secret_key,algorithm='HS256')
    with pytest.raises(HTTPException) as exc:
        core.user_from_token(token,Mock(get=lambda _model, _id: None))
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_expired_jwt_is_rejected():
    from unittest.mock import Mock
    now = core.utcnow()
    token=jwt.encode({'type':'access','sub':'1','iat':now-timedelta(minutes=5),'exp':now-timedelta(minutes=1)},core.settings.jwt_secret_key,algorithm='HS256')
    with pytest.raises(HTTPException) as exc:
        core.user_from_token(token,Mock())
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_aware_converts_naive_datetime_to_utc():
    naive=datetime(2026,1,1,12,0)
    assert core.aware(naive).utcoffset()==timedelta(0)
    assert core.aware(None) is None
    aware=datetime.now(timezone.utc)
    assert core.aware(aware) is aware


@pytest.mark.unit
def test_user_token_lookup_requires_active_account():
    from unittest.mock import Mock
    token=core.create_access_token(SimpleNamespace(id=15))
    db=Mock()
    db.get.return_value=User(id=15,name='Inactive',email='inactive@example.org',password_hash='x',role='GESTOR',active=False)
    with pytest.raises(HTTPException) as exc:
        core.user_from_token(token,db)
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_csv_stream_response_has_safe_headers_and_bom():
    result=routes.csv_response(['A','B'], [['=cmd','ok']], 'safe.csv')
    assert result.headers['content-disposition'].endswith('"safe.csv"')
    assert result.media_type.startswith('text/csv')
    import asyncio
    async def gather():
        return b''.join([chunk.encode() if isinstance(chunk,str) else chunk async for chunk in result.body_iterator])
    body=asyncio.run(gather())
    assert body.startswith('\ufeff'.encode('utf-8'))
    assert b"'=cmd" in body
