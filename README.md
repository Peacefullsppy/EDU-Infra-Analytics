# EDU-Infra Analytics 1.6

Sistema web para cadastro e diagnóstico técnico de laboratórios e computadores de instituições de ensino. Reúne monitoramento de CPU, RAM e disco, alertas, histórico de medições, indicador experimental IIE, relatórios CSV, inventário Hyper-V, autenticação por perfis e Termos e Condições versionados.

## Tecnologias

- Backend: Python 3.13, FastAPI, SQLAlchemy, Alembic e PostgreSQL.
- Frontend: React, Vite e JavaScript.
- Monitoramento: agente Python com `psutil` e `httpx`.
- Virtualização: Hyper-V e scripts PowerShell.
- Testes: Pytest, TestClient, PostgreSQL descartável e Playwright (E2E de navegador).

## Organização

```text
backend/app/       API, modelos, validações e serviços
backend/alembic/    Migrações de banco
backend/tests/      Testes unitários, integração e jornadas E2E
frontend/src/      Interface e comunicação HTTP
agent/             Agente de métricas para host ou VM
hyperv/            Scripts de inventário e agendamento do agente
infra/             PostgreSQL com Docker Compose
legal/             Termos, aviso de privacidade e orientações
.github/workflows/ Integração contínua
```

## Inicialização (Windows / PowerShell)

Requisitos: Python 3.13, Node.js 22, Docker Desktop em execução e PowerShell. Mantenha senhas e tokens apenas em arquivos `.env` locais.

**1. Banco de dados**

```powershell
cd infra
Copy-Item .env.example .env
notepad .env
docker compose --env-file .env -f compose.postgres.yml up -d
cd ..
```

**2. API**

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
notepad .env
python -m alembic upgrade head
python -m scripts.check_db
python -m app.cli create-admin
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Configure `backend/.env` com a senha real do PostgreSQL e uma `JWT_SECRET_KEY` forte. O Compose publica por padrão a porta local `5433`; ajuste `backend/.env` se alterou a porta para evitar conflitos.

Documentação Swagger: `http://127.0.0.1:8000/docs`. Saúde: `http://127.0.0.1:8000/health`.

**3. Interface (novo terminal)**

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Acesse `http://127.0.0.1:5173`. O usuário precisa aceitar os Termos vigentes após cada login para acessar as funcionalidades.

**4. Agente (no host ou em cada VM, terminal próprio)**

```powershell
cd agent
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python agent.py --once
python agent.py
```

Configure `EDU_COMPUTER_ID`, `EDU_AGENT_TOKEN` e `EDU_API_URL` com os valores do equipamento cadastrado. Dentro de uma VM, use o HTTPS do host acessível pela rede, não `127.0.0.1` da VM.

## Testes

Na pasta `backend` com `requirements-dev.txt` instalado:

```powershell
python -m pytest -q
python -m pytest -q -m unit
python -m pytest -q -m integration
python -m pytest -q -m e2e
python -m pytest --cov=app --cov-report=term-missing
```


