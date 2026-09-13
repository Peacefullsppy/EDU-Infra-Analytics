# EDU-Infra Analytics

Sistema para diagnóstico e monitoramento da infraestrutura tecnológica de ambientes educacionais.

## Etapa atual

Esta versão implementa a **primeira regra de negócio (RN01)** e uma interface inicial baseada nos protótipos de Dashboard, Laboratórios e Computadores.

### RN01 — vínculo entre computador e laboratório

> Todo computador cadastrado deve estar vinculado a um laboratório previamente cadastrado no sistema.

A validação acontece no backend. Se o `laboratorio_id` informado não existir, a API recusa o cadastro com erro `400`.

Exemplo inválido no Swagger (`http://127.0.0.1:8000/docs`):

```json
{
  "hostname": "PC-TESTE",
  "ip": "192.168.1.200",
  "laboratorio_id": 999,
  "status": "online",
  "cpu": 20,
  "ram": 40,
  "disco": 50
}
```

Resposta esperada:

```json
{
  "detail": "RN01: não é possível cadastrar o computador. O laboratório informado não existe."
}
```

## O que está funcionando

- Dashboard inicial.
- Listagem e cadastro de laboratórios.
- Listagem e cadastro de computadores.
- Filtros de computadores.
- RN01 validada no backend.
- Dados demonstrativos em memória.
- CORS entre React e FastAPI.
- Sem tela de login nesta etapa.

## Executar backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

## Executar frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Próxima etapa

Trocar os dados em memória por persistência com PostgreSQL + SQLAlchemy + Alembic, mantendo a mesma RN01.
