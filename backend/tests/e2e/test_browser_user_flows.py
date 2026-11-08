"""E2E de navegador real com Playwright: frontend React + API FastAPI + SQLite temporário.

Executar somente em ambiente dedicado, com E2E_BASE_URL e EDU_E2E_DISPOSABLE=SIM.
"""
import os
from uuid import uuid4
import pytest

playwright = pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect

BASE=os.environ.get('E2E_BASE_URL','').rstrip('/')
PASSWORD=os.environ.get('E2E_TEST_PASSWORD','')


@pytest.fixture(scope='module')
def browser():
    if not BASE or os.environ.get('EDU_E2E_DISPOSABLE')!='SIM':
        pytest.skip('E2E navegador só é executado contra banco descartável configurado')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    page=browser.new_page(viewport={'width':1366,'height':860},locale='pt-BR')
    page.goto(BASE)
    yield page
    page.close()


def login(page,role='admin',accept=True):
    page.get_by_label('E-mail institucional').fill(f'e2e-{role}@example.org')
    page.get_by_label('Senha').fill(PASSWORD)
    page.get_by_role('button',name='Entrar no sistema').click()
    expect(page.get_by_role('heading',name='Antes de continuar')).to_be_visible(timeout=12000)
    if accept:
        page.locator('.terms-check input[type="checkbox"]').check()
        page.get_by_role('button',name='Aceitar e acessar painel').click()
        expect(page.get_by_role('heading',name='Dashboard',exact=True)).to_be_visible(timeout=12000)


@pytest.mark.e2e
@pytest.mark.browser
def test_login_displays_terms_before_dashboard(page):
    login(page,accept=False)
    expect(page.get_by_role('button',name='Aceitar e acessar painel')).to_be_disabled()
    expect(page.get_by_role('heading',name='Dashboard',exact=True)).to_have_count(0)


@pytest.mark.e2e
@pytest.mark.browser
def test_terms_checkbox_unlocks_dashboard(page):
    login(page)
    expect(page.get_by_role('heading',name='Dashboard',exact=True)).to_be_visible()
    expect(page.get_by_role('navigation',name='Navegação principal')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.browser
def test_privacy_notice_is_available_without_login(page):
    page.get_by_role('button',name='Aviso de Privacidade').click()
    expect(page.get_by_role('dialog',name='Aviso de Privacidade e LGPD')).to_be_visible()
    expect(page.get_by_role('dialog').get_by_text('LGPD').first).to_be_visible(timeout=10000)


@pytest.mark.e2e
@pytest.mark.browser
def test_login_and_logout_require_terms_again(page):
    login(page)
    page.get_by_role('button',name='Sair',exact=True).click()
    expect(page.get_by_role('button',name='Entrar no sistema')).to_be_visible()
    login(page,accept=False)
    expect(page.get_by_role('heading',name='Antes de continuar')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.browser
def test_admin_creates_laboratory_and_sees_it_in_table(page):
    login(page)
    label=f'Laboratório E2E {uuid4().hex[:6]}'
    page.get_by_role('navigation',name='Navegação principal').get_by_role('button',name='Laboratórios').click()
    page.get_by_role('button',name='Novo laboratório').click()
    dialog=page.get_by_role('dialog',name='Novo laboratório')
    dialog.get_by_label('Nome do laboratório').fill(label)
    dialog.get_by_label('Localização').fill('Bloco E2E')
    dialog.get_by_role('button',name='Salvar laboratório').click()
    expect(page.get_by_text(label,exact=True)).to_be_visible(timeout=12000)


@pytest.mark.e2e
@pytest.mark.browser
def test_admin_registers_computer_without_generated_metrics(page):
    login(page)
    labname=f'E2E Lab {uuid4().hex[:6]}'
    page.get_by_role('navigation',name='Navegação principal').get_by_role('button',name='Laboratórios').click()
    page.get_by_role('button',name='Novo laboratório').click()
    d=page.get_by_role('dialog',name='Novo laboratório')
    d.get_by_label('Nome do laboratório').fill(labname)
    d.get_by_label('Localização').fill('E2E')
    d.get_by_role('button',name='Salvar laboratório').click()
    expect(page.get_by_text(labname,exact=True)).to_be_visible(timeout=12000)
    page.get_by_role('navigation',name='Navegação principal').get_by_role('button',name='Computadores').click()
    page.get_by_role('button',name='Novo computador').click()
    dialog=page.get_by_role('dialog',name='Novo computador')
    dialog.get_by_label('Laboratório',exact=True).select_option(label=labname)
    dialog.get_by_label('Nome de exibição').fill('VM E2E Browser')
    dialog.get_by_label('Hostname').fill(f'e2e-vm-{uuid4().hex[:8]}')
    dialog.get_by_role('button',name='Salvar computador').click()
    expect(page.get_by_text('VM E2E Browser',exact=True)).to_be_visible(timeout=12000)


@pytest.mark.e2e
@pytest.mark.browser
def test_manager_cannot_create_laboratories_or_see_users(page):
    login(page,role='gestor')
    nav=page.get_by_role('navigation',name='Navegação principal')
    expect(nav.get_by_role('button',name='Usuários')).to_have_count(0)
    nav.get_by_role('button',name='Laboratórios').click()
    expect(page.get_by_role('button',name='Novo laboratório')).to_have_count(0)


@pytest.mark.e2e
@pytest.mark.browser
def test_admin_settings_shows_current_terms_and_audit(page):
    login(page)
    page.get_by_role('navigation',name='Navegação principal').get_by_role('button',name='Configurações').click()
    expect(page.get_by_role('heading',name='Termos e Condições',exact=True)).to_be_visible()
    expect(page.get_by_role('heading',name='Auditoria recente')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.browser
def test_mobile_navigation_reaches_laboratories(browser):
    if not BASE: pytest.skip('Sem frontend configurado')
    p=browser.new_page(viewport={'width':390,'height':844},locale='pt-BR')
    try:
        p.goto(BASE)
        login(p)
        p.get_by_role('button',name='Abrir menu').click()
        p.get_by_role('navigation',name='Navegação principal').get_by_role('button',name='Laboratórios').click()
        expect(p.get_by_role('heading',name='Laboratórios',exact=True)).to_be_visible()
    finally:
        p.close()
