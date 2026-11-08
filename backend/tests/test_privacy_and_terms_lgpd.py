"""Garantias de disponibilização jurídica: não alteram o aceite legado dos testes."""
from pathlib import Path
from app.routes import _privacy_notice_text


def test_privacy_notice_public_without_login(client):
    res = client.get('/api/public/privacy-notice')
    assert res.status_code == 200
    data = res.json()
    assert data['version'] == '1.0'
    assert 'DIREITOS DOS TITULARES' in data['content']
    assert 'consentimento genérico' in data['content']


def test_terms_v2_explicitly_separates_acceptance_from_consent():
    root = Path(__file__).resolve().parents[2]
    text = (root / 'legal' / 'TERMOS_E_CONDICOES_V2_1_LGPD.txt').read_text(encoding='utf-8')
    assert 'NÃO se presume' in text
    assert '26. LEGISLAÇÃO APLICÁVEL' in text
    assert 'Resolução CD/ANPD nº 15/2024' in text
    assert 'PREENCHER:' in text


def test_privacy_notice_is_standalone_file():
    assert 'LGPD' in _privacy_notice_text()
