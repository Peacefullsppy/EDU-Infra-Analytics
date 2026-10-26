# EDU-Infra Analytics — reconstrução autoral desde zero

Nova base independente, criada após **auditoria** da monografia V2 e do ZIP fornecido. Não foram reaproveitados componentes React, layouts do Figma, scripts de seed, imagens ou módulos Python anteriores. Nenhum computador ou laboratório é cadastrado automaticamente.

## O que já funciona (v0.1)

- REST FastAPI autenticada via JWT; Argon2; perfil `admin`, `tecnico`, `gestor`.
- Criação do **primeiro administrador pelo terminal**, com senha digitada e sem credenciais de demonstração.
- CRUD de laboratórios e computadores (API e telas React), RBAC e logs de auditoria.
- Exclusão de laboratório somente por admin, **proibida** se existirem computadores vinculados. Nenhuma exclusão em cascata de computador.
- Dados reais consultados diretamente do banco. Sem métricas inventadas, seed, data fixa, gráfico fictício ou IIE fabricado.
- Dashboard, indicadores, alertas derivados de medições existentes, resumo, privacidade, gestão de usuários e auditoria.
- Migração inicial Alembic que cria esquema **vazio**; PostgreSQL/Supabase como destino da demonstração e SQLite local explícito.
- Sete testes backend automatizados (em 20/10/2026).

**Ainda não implementado:** agente de telemetria/psutil, ingestão de métricas, histórico temporal, cálculo validado do IIE, módulo educacional, relatórios exportáveis, ViaCEP e implantação Hyper-V. Ver cronograma em `docs/`.

## Instalação e execução — Windows PowerShell

Pré-requisitos: Python 3.12+, Node.js com npm, PowerShell e acesso ao registry npm. Ter PostgreSQL/Supabase é necessário para a versão final, mas não para executar a primeira versão em SQLite local.

### Terminal 1 — backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Obrigatório:** abra `backend/.env` e substitua `JWT_SECRET_KEY` por uma string aleatória com ao menos 32 caracteres. Para gerar uma no PowerShell, rode:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Cole a saída em `JWT_SECRET_KEY=` dentro de `.env`, **sem registrar essa chave no GitHub**. O arquivo `.env.example` usa SQLite local explicitamente para facilitar o primeiro uso. Para PostgreSQL/Supabase, substitua `DATABASE_URL` por uma string de conexão PostgreSQL com `psycopg`. Confirme os parâmetros pelo painel Connect do seu Supabase, sem expor a senha.

```powershell
python -m alembic upgrade head
python -m app.cli create-admin
python -m uvicorn app.main:app --reload
```

Digite nome, e-mail e senha forte no assistente `create-admin`; esse fluxo não cria laboratórios nem computadores. Rotas: `http://127.0.0.1:8000/docs` (OpenAPI) e `http://127.0.0.1:8000/health`.

**Importante:** execute `create-admin` somente quando não houver usuários. Outras contas são cadastradas na tela de Usuários após autenticar como admin. Para banco local totalmente novo, use outro banco/arquivo e repita as migrações (não apagar dados de trabalho).

### Terminal 2 — frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Abra `http://127.0.0.1:5173`, entre com a conta criada no terminal e faça seu **primeiro cadastro real** de laboratório. Em seguida crie um computador associado. O painel mostrará números dos registros cadastrados e o estado `Sem coleta`, pois o agente ainda não está implementado. O IIE aparece `Não calculado`.

### Testes

```powershell
cd backend
python -m pytest -q
```

Os testes criam dados **apenas em bancos temporários isolados**. Não modificam a sua instância principal ou o Supabase.

## Regras e papéis

| Operação | admin | tecnico | gestor |
|---|---:|---:|---:|
| Consultar laboratórios/computadores/painel | Sim | Sim | Sim |
| Criar/editar laboratórios | Sim | Sim | Não |
| Excluir laboratórios vazios | Sim | Não | Não |
| Criar/editar/excluir computadores | Sim | Sim | Não |
| Administrar usuários e consultar auditoria | Sim | Não | Não |

## Estrutura

- `backend/app/`: schemas, persistência, autenticação, endpoints e regras.
- `backend/alembic/`: migrações de esquema sem seed.
- `backend/tests/`: cenários pytest com SQLite separado.
- `frontend/src/`: interface independente React/CSS.
- `docs/ESCOPO_E_REQUISITOS.md`: matriz completa RF01–RF18 e propostas RF19–RF26.
- `docs/REVISAO_MONOGRAFIA_V2.md`: relatório de atualização da monografia, seção por seção.
- `docs/CRONOGRAMA_SEIS_SEMANAS.md`: plano até a defesa.
- `docs/FERRAMENTAS_TECH_STACK.md`: como integrar ferramentas e fluxo de trabalho.

## Próxima versão

Primeiro adicionar ingestão autenticada por dispositivo, séries históricas reais, estado derivado de `last_seen_at`, alertas e coleta automática com psutil. Depois a especialização educacional (atividades/requisitos), testes de aderência e proposta fundamentada do IIE. Não afirmar que módulos planejados já foram entregues.
