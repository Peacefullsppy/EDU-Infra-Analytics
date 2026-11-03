"""Gera evidências reproduzíveis a partir de uma migração e chamadas à API reais.

Atenção: usa banco SQLite TEMPORÁRIO de validação, sem tocar no banco do usuário.
Screenshots HTML são relatórios gerados de consultas SQL e respostas reais à API,
NÃO são capturas do frontend React nem provas de Supabase/PostgreSQL.
"""
import html
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
OUT = ROOT / 'evidencias'
OUT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='edu_infra_evidencia_') as td:
    dbpath = Path(td) / 'validacao.sqlite3'
    env = dict(os.environ, DATABASE_URL='sqlite:///' + str(dbpath), JWT_SECRET_KEY=secrets.token_urlsafe(48))
    env['PYTHONPATH'] = str(BACKEND)
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=BACKEND, env=env, check=True, capture_output=True, text=True)
    os.environ.update({key: env[key] for key in ('DATABASE_URL','JWT_SECRET_KEY','PYTHONPATH')})
    sys.path.insert(0, str(BACKEND))
    from app.cli import main as bootstrap
    from app.main import app
    from fastapi.testclient import TestClient

    def sql_snapshot():
        with sqlite3.connect(dbpath) as conn:
            return {table: conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                    for table in ('users', 'laboratories', 'computers', 'audit_logs')}

    empty = sql_snapshot()
    assert empty == dict.fromkeys(empty, 0), 'Migração não produziu banco vazio'
    password = secrets.token_urlsafe(24)
    with patch.object(sys, 'argv', ['app.cli', 'create-admin']), \
         patch('builtins.input', side_effect=['Administrador de Validação', 'validacao@example.org']), \
         patch('app.cli.getpass', side_effect=[password, password]):
        bootstrap()
    bootstrap_snapshot = sql_snapshot()
    assert bootstrap_snapshot == {'users': 1, 'laboratories': 0, 'computers': 0, 'audit_logs': 0}

    with TestClient(app) as client:
        response = client.post('/api/v1/auth/login', json={'email':'validacao@example.org', 'password': password})
        assert response.status_code == 200, response.text
        auth = {'Authorization':'Bearer ' + response.json()['access_token']}
        before = client.get('/api/v1/dashboard', headers=auth)
        assert before.status_code == 200 and before.json()['laboratories'] == 0
        lab = client.post('/api/v1/laboratorios', headers=auth,
                          json={'name':'Laboratório de Validação', 'location':'Ambiente local de testes','is_active':True})
        assert lab.status_code == 201, lab.text
        pc = client.post('/api/v1/computadores', headers=auth,
                         json={'hostname':'VALIDACAO-PC-01','ip_address':'192.0.2.10','laboratory_id':lab.json()['id']})
        assert pc.status_code == 201, pc.text
        conflict = client.delete('/api/v1/laboratorios/' + str(lab.json()['id']), headers=auth)
        assert conflict.status_code == 409, conflict.text
        after = client.get('/api/v1/dashboard', headers=auth)
        labs = client.get('/api/v1/laboratorios', headers=auth)
        pcs = client.get('/api/v1/computadores', headers=auth)
        assert after.status_code == labs.status_code == pcs.status_code == 200
        assert len(labs.json()) == 1 and len(pcs.json()) == 1 and pcs.json()[0]['status'] == 'sem_coleta'
        assert after.json()['iie'] is None
    final = sql_snapshot()
    assert final['laboratories'] == 1 and final['computers'] == 1
    result = {
        'metodo': 'Alembic upgrade head + bootstrap CLI + chamadas HTTP via FastAPI TestClient + consultas SQL SQLite',
        'ambiente': 'Banco temporário SQLite de validação. Não representa o banco real do usuário nem PostgreSQL/Supabase.',
        'migracao_banco_vazio': empty,
        'apos_bootstrap_admin': bootstrap_snapshot,
        'antes_cadastros_dashboard': before.json(),
        'api_post_laboratorio': {'http':lab.status_code, 'body':lab.json()},
        'api_post_computador': {'http':pc.status_code, 'body':pc.json()},
        'api_delete_laboratorio_ocupado': {'http': conflict.status_code, 'body': conflict.json()},
        'api_get_laboratorios': {'http':labs.status_code,'body':labs.json()},
        'api_get_computadores': {'http':pcs.status_code,'body':pcs.json()},
        'depois_cadastros_dashboard': after.json(),
        'consultas_sql_apos_cadastros': final,
        'senha_token': 'Não armazenados nas evidências',
    }
    (OUT / 'resultado_evidencias.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

    def panel(title, caption, data):
        return (f'<article><header><h2>{html.escape(title)}</h2><p>{html.escape(caption)}</p></header>'
                f'<pre>{html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))}</pre></article>')

    styles = '''<style>body{font:15px/1.5 system-ui,-apple-system,Arial;background:#f3f6fa;color:#16273f;margin:0;padding:42px}main{max-width:1150px;margin:auto}.eyebrow{color:#186a91;letter-spacing:2px;font-size:12px;font-weight:700;text-transform:uppercase}h1{font-size:32px;margin:8px 0 5px}.muted{color:#5a6a7e}section{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:28px}article{background:white;border:1px solid #dce4ef;border-radius:14px;overflow:hidden;box-shadow:0 5px 16px #1328490e}header{padding:18px 22px 8px}h2{font-size:18px;margin:0}header p{margin:5px 0;color:#52647a;font-size:13px}pre{font-size:14px;padding:15px 22px 24px;white-space:pre-wrap;word-break:break-word;line-height:1.65;background:#f9fbfe;border-top:1px solid #e3eaf3;margin:0}.footer{padding-top:22px;font-size:13px;color:#5a6a7e}</style>'''
    pages = {
        '01_banco_vazio': [
            panel('Consulta SQL após Alembic', 'Quatro tabelas sem registros, antes do bootstrap', empty),
            panel('Dashboard sem cadastros', 'Consulta real autenticada após criação explícita de um administrador', before.json()),
        ],
        '02_cadastros_reais': [
            panel('Laboratório criado por POST', 'HTTP 201 • Persistido em banco SQLite temporário', lab.json()),
            panel('Computador criado por POST', 'HTTP 201 • Registrado no laboratório • Sem telemetria simulada', pc.json()),
            panel('Contagem SQL após cadastros', 'Consultas SELECT COUNT(*) no banco temporário', final),
            panel('Dashboard após cadastros', 'GET /api/v1/dashboard • dados vindos de SQL', after.json()),
        ],
        '03_conflito_http_409': [
            panel('DELETE bloqueado', 'Exclusão de laboratório com computador associado', {'http':conflict.status_code, **conflict.json()}),
            panel('Registros preservados', 'Consultas GET reais após tentativa de exclusão', {'laboratorios':labs.json(), 'computadores':pcs.json()}),
        ],
    }
    for basename, panels in pages.items():
        document = f'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>{html.escape(basename)}</title>{styles}<main><div class="eyebrow">EDU-INFRA ANALYTICS • EVIDÊNCIA DE TESTE</div><h1>{basename.replace("_", " ").title()}</h1><p class="muted">Origem: migração e requisições executadas em banco temporário local, sem mocks e sem acesso a sistemas de produção.</p><section>{"".join(panels)}</section><p class="footer">Relatório de consulta e respostas, não captura do frontend React. O agente e o IIE ainda não foram implementados.</p></main></html>'
        (OUT / f'{basename}.html').write_text(document, encoding='utf-8')
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
                page = browser.new_page(viewport={'width': 1480, 'height': 1000}, device_scale_factor=1)
                page.set_content(document, wait_until='load')
                page.screenshot(path=str(OUT / f'{basename}.png'), full_page=True)
                browser.close()
        except Exception as exc:
            print('Screenshot indisponível; relatório HTML foi criado:', exc)
    print(json.dumps({'ok':True, 'contagens_iniciais':empty, 'contagens_finais':final,
                      'http409':conflict.status_code, 'pasta':str(OUT)}, ensure_ascii=False))
