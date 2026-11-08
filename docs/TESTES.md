# Estratégia de testes — EDU-Infra Analytics 1.6

## Pirâmide de validação

- **Unitários** (`backend/tests/unit/`): contratos Pydantic, limites do IIE, status, alertas, JWT, Argon2, escape CSV, CLI e agente isolado com mocks.
- **Integração** (`backend/tests/integration/`): matriz RBAC, bloqueio por Termos, CRUD, consultas, persistência, integridade referencial, tokens, alertas, filtros, CSV, Hyper-V e auditoria. Usam SQLite em memória, com chaves estrangeiras habilitadas e fixture isolada por cenário.
- **Jornadas E2E de API** (`backend/tests/e2e/test_complete_journeys_api.py`): fluxos completos por HTTP TestClient cobrindo login→Termos→cadastros→coleta→alertas→relatórios e políticas de permissão.
- **E2E de navegador** (`backend/tests/e2e/test_browser_user_flows.py`): Chromium/Playwright com frontend Vite, backend Uvicorn e SQLite descartável; fluxos reais de interação e responsividade.
- **PostgreSQL real** (`backend/tests/test_postgresql.py`): integração opt-in no banco descartável fornecido pela CI; o teste pode inserir e excluir dados.

- **Frontend unitário** (`frontend/tests/`): testes Vitest de cliente REST, bloqueio de sessão, formatação e gráficos SVG, sem necessidade do backend.

## Comandos

No terminal dentro de `backend`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pytest -q -m unit
python -m pytest -q -m integration
python -m pytest -q -m e2e
python -m pytest -q --cov=app --cov-report=term-missing --cov-report=html
```

**Atenção:** `-m e2e` inclui as jornadas via API. Os cenários de navegador são **ignorados** quando não há frontend de teste conectado. Isso não deve ser apresentado como E2E de navegador executado. Os testes locais de API/integração em SQLite não substituem a integração real em PostgreSQL.

No terminal `frontend`, execute `npm install`, `npm run build` e `npm run test:unit`.

## E2E de navegador, ambiente exclusivo de testes

Requisitos: Python 3.13, Node 22, npm, Chromium do Playwright e portas `8000` e `5173` livres. **Não aponte para banco de produção nem reutilize usuários reais.** Configure `EDU_E2E_DISPOSABLE=SIM` e uma URL SQLite contendo `edu-e2e-` para autorizar explicitamente os dados descartáveis.

Em PowerShell, terminal 1 (`backend`):

```powershell
python -m pip install -r requirements-e2e.txt
python -m playwright install chromium
$env:EDU_E2E_DISPOSABLE='SIM'
$env:DATABASE_URL='sqlite:///./edu-e2e-local.sqlite'
$env:JWT_SECRET_KEY='secret-for-disposable-e2e-only-change-in-real-env'
$env:E2E_TEST_PASSWORD='Strong-E2E-Password-123!'
python -m alembic upgrade head
python -m scripts.seed_e2e
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 (`frontend`):

```powershell
npm install
$env:VITE_API_URL='http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1 --port 5173
```

Terminal 3 (`backend`):

```powershell
$env:E2E_BASE_URL='http://127.0.0.1:5173'
$env:EDU_E2E_DISPOSABLE='SIM'
$env:E2E_TEST_PASSWORD='Strong-E2E-Password-123!'
python -m pytest -q tests/e2e/test_browser_user_flows.py
```

Os arquivos e senhas usados são exclusivamente de teste. Para repetições, utilize uma nova base SQLite descartável ou reinicialize-a deliberadamente somente após conferir o nome do arquivo. O script `seed_e2e.py` recusa conexão com banco que não seja SQLite de teste.

## CI automatizada

O workflow `.github/workflows/ci.yml` contém verificações separadas para PostgreSQL de teste, build do frontend e navegador Chromium em ambiente SQLite descartável. A CI é a fonte mais adequada para apresentar resultados reproduzíveis com logs e artefatos de cobertura. Não confunda testes existentes, coletados, executados e aprovados: somente resultados observados devem ser informados na apresentação.

## Limites de credibilidade

A cobertura de instruções não demonstra, por si só, qualidade de software. Os testes são uma amostragem de comportamento e precisam ser complementados por revisão de segurança, testes com Hyper-V/Windows reais, carga, falhas de rede e auditoria antes de produção. A integração PostgreSQL e os E2E de navegador dependem de serviços que podem não estar presentes no ambiente local.
