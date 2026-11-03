# Roteiro verificável da Semana 1

## Pré-requisitos e ambiente

- Python 3.12+ e PostgreSQL 14+ **para validação do banco alvo**; SQLite local é uma alternativa de teste, **não comprovação PostgreSQL**.
- Node.js e npm com acesso ao registro de pacotes para validar frontend React/Vite.
- Em Windows/PowerShell, execute os blocos na pasta indicada. Não versionar `.env`, `*.db` ou credenciais.

## A. Criar banco sem cadastros

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env`: `JWT_SECRET_KEY` aleatória com no mínimo 32 caracteres e `DATABASE_URL`. Para **PostgreSQL local**, uma URL típica é `postgresql+psycopg://usuario:senha@localhost:5432/edu_infra`. No Supabase, obtenha a string do painel da sua instância, preferencialmente pela opção compatível com IPv4/pooler e SSL/TLS conforme orientação do provedor; não publicar credenciais. Para testar de forma isolada, use o SQLite `sqlite:///./edu_infra_dev.db` do `.env.example` (sem dados de escola).

```powershell
python -m alembic upgrade head
python -m alembic current
```

**Conferência inicial:** após a migração, `users`, `laboratories`, `computers`, `audit_logs` devem possuir **zero linhas**. Pode-se conferir diretamente com SQL: `SELECT COUNT(*) FROM users;`, `SELECT COUNT(*) FROM laboratories;`, `SELECT COUNT(*) FROM computers;` e `SELECT COUNT(*) FROM audit_logs;`. Uma base previamente utilizada não estará vazia; para evidenciar a condição inicial use banco novo, nunca apague produção.

## B. Bootstrap e API real

```powershell
python -m app.cli create-admin
python -m uvicorn app.main:app --reload
```

Entre com nome, e-mail válido e senha forte escolhida no terminal; nenhuma senha padronizada é fornecida pelo projeto. Acesse `/docs` para executar `POST /api/v1/auth/login`, copiar o token e autorizar chamadas subsequentes. Cadastre um laboratório real de teste e um computador vinculado; utilize `GET` para comprovar persistência e tente excluir o laboratório antes do computador.

### Exemplo de sequência HTTP

```http
POST /api/v1/auth/login               → 200 / 401
GET  /api/v1/laboratorios            → 200 [] (antes de cadastrar)
POST /api/v1/laboratorios            → 201 {"id": 1, ...}
POST /api/v1/computadores            → 201 {"laboratory_id": 1, ...}
DELETE /api/v1/laboratorios/1        → 409 (ocupado)
GET /api/v1/laboratorios/1          → 200 (preservado)
DELETE /api/v1/computadores/1        → 204
DELETE /api/v1/laboratorios/1        → 204
```

**IDs são exemplos ilustrativos**, não valores fixos do sistema: substitua pelos IDs retornados pelas requisições atuais.

## C. Frontend sem mocks

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run build
npm run dev
```

Acesse `http://127.0.0.1:5173`. Faça login com o admin configurado e realize cadastro/edição/exclusão. Na aba Network do navegador verifique chamadas reais a `/api/v1/laboratorios` e `/api/v1/computadores`. Com banco sem cadastros, as tabelas aparecem vazias; após POST, os dados devem aparecer depois de atualizar a consulta. Não há `seed` nem mock de inventário no frontend. Documente console sem erros, responsividade e mensagens. **Nesta sessão o npm falhou ao acessar registry.npmjs.org (DNS EAI_AGAIN), logo estas verificações visuais permanecem pendentes.**

## D. Testes automatizados

```powershell
cd backend
python -m pytest -q
```

Resultado desta execução (02/11/2026): **19 passed** (Linux, Python da sessão, SQLite temporário). Inclui 401, 403, 404, 409, 422, CRUD completo, login, auditoria, duplicidade e integridade. Testes não manipulam a instância principal.

## E. Reproduzir relatórios e capturas do banco de validação

Na raiz do projeto:

```powershell
python scripts/gerar_evidencias_semana1.py
```

O script executa de verdade o `alembic upgrade head` em um SQLite temporário, consulta o banco vazio, cria o primeiro administrador via CLI, envia POSTs pela API FastAPI (TestClient real, sem mock de serviços e sem banco principal), consulta SQL, confirma HTTP 409 e grava `evidencias/resultado_evidencias.json`. HTMLs e capturas PNG são relatórios de **consultas SQL e respostas HTTP reais**, não screenshots do frontend React e não provas de PostgreSQL/Supabase. PNG automático só é gerado quando Playwright e Chromium estiverem disponíveis; caso contrário, abra HTML no navegador e capture manualmente.

## F. Critérios de aceite e riscos finais

| Critério | Resultado nesta execução |
|---|---|
| Banco novo criado por migração e sem seed | Aprovado no SQLite temporário |
| Bootstrap admin não cria laboratórios ou computadores | Aprovado no SQLite temporário |
| CRUD de laboratório/PC com dados persistidos | Aprovado via FastAPI TestClient + SQL |
| DELETE de lab ocupado retorna HTTP 409, sem excluir dados | **Aprovado** |
| RBAC 401/403 e auditoria CREATE/UPDATE/DELETE | Aprovado pelos pytest |
| ≥7 testes pytest | **19/19 aprovados** |
| React sem mock (análise de código) | Confirmado no código; build/navegador não verificados |
| Migração inicial no PostgreSQL/Supabase | **Pendente**: sem conexão/credenciais para PostgreSQL |
| Commit remoto e screenshots de ambiente institucional | **Pendente**: sem publicação/acesso remoto |

**Cuidados:** execução em teste local não demonstra prontidão para produção. Os valores de disponibilidade não equivalem à qualidade do ensino; IIE permanece `null` até método academicamente validado.
