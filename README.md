# EDU-Infra Analytics

Sistema para diagnóstico e monitoramento da infraestrutura tecnológica de ambientes educacionais.

Esta versão foi **reconstruída a partir da entrega 14/09**. O Dashboard, as telas de Laboratórios e Computadores, os dados demonstrativos e a regra de negócio RN01 foram preservados como base. Sobre essa base foram adicionadas as etapas posteriores: persistência em banco, autenticação, controle de acesso, auditoria, LGPD, API externa, indicadores e relatório-resumo.

## Objetivo

Desenvolver uma plataforma capaz de monitorar, organizar e analisar a infraestrutura tecnológica de ambientes educacionais, apoiando equipes de TI e gestores na identificação de problemas e na tomada de decisão.

## O que está implementado

- Dashboard baseado no protótipo da entrega 14/09.
- Cadastro e listagem de laboratórios.
- Cadastro e listagem de computadores.
- **RN01:** todo computador precisa estar vinculado a um laboratório existente.
- PostgreSQL por SQLAlchemy, com suporte a Supabase.
- SQLite local automático quando `DATABASE_URL` não é informada, apenas para facilitar desenvolvimento.
- Alembic com migração inicial.
- Tela de login.
- Autenticação JWT.
- Senhas com hash Argon2.
- Perfis `admin`, `tecnico` e `gestor`.
- Auditoria de ações importantes.
- Tela de Privacidade/LGPD.
- Integração externa com ViaCEP.
- Tela de Configurações com teste da API externa e auditoria.
- Indicadores básicos e IIE por laboratório.
- Relatório-resumo da infraestrutura.
- Dados demonstrativos: 3 laboratórios e 60 computadores.

## RN01 — vínculo entre computador e laboratório

> Todo computador cadastrado deve estar vinculado a um laboratório previamente cadastrado no sistema.

A validação é realizada no backend. Se `laboratorio_id` não existir, a API retorna erro `400`.

Exemplo inválido:

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

Resposta:

```json
{
  "detail": "RN01: não é possível cadastrar o computador. O laboratório informado não existe."
}
```

## Estrutura

```text
EDU-Infra-Analytics-refeito/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── audit.py
│   │   ├── external.py
│   │   └── seed.py
│   ├── alembic/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── .env.example
├── docs/
└── README.md
```

## 1. Rodar o backend localmente

No PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Abra `backend/.env` e defina pelo menos:

```env
JWT_SECRET_KEY=uma-chave-aleatoria-grande
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@escola.edu
ADMIN_PASSWORD=Admin123456
```

Se `DATABASE_URL` ficar vazia, o projeto utiliza SQLite local para desenvolvimento.

Crie as tabelas e os dados iniciais:

```powershell
python -m app.seed
```

Resultado esperado na primeira execução:

```text
Iniciando seed do EDU-Infra Analytics...
Administrador criado: admin@escola.edu
Dados de demonstração criados: 3 laboratórios e 60 computadores.
Seed finalizado com sucesso.
```

Inicie a API:

```powershell
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## 2. Usar PostgreSQL no Supabase

No Supabase, abra **Connect > Session pooler** e copie a connection string. Coloque em `backend/.env`:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:SUA_SENHA@HOST_POOLER:5432/postgres
```

Use a string fornecida pelo próprio Supabase. Não copie os colchetes de `[YOUR-PASSWORD]`.

Depois execute novamente:

```powershell
python -m app.seed
```

O `.env` não deve ser enviado ao GitHub.

## 3. Rodar o frontend

Abra outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

Entre com o e-mail e a senha definidos em `ADMIN_EMAIL` e `ADMIN_PASSWORD` antes de executar o seed.

## Perfis de acesso

| Perfil | Consulta | Cadastro de laboratórios/computadores | Auditoria |
|---|---|---|---|
| `admin` | Sim | Sim | Sim |
| `tecnico` | Sim | Sim | Não |
| `gestor` | Sim | Não | Não |

Nesta etapa, o seed cria apenas o administrador. Os demais perfis estão preparados no backend para evolução posterior do gerenciamento de usuários.

## Auditoria

São registrados, entre outros:

- `LOGIN_SUCESSO`
- `LOGIN_FALHA`
- `VISUALIZAR_DASHBOARD`
- `LISTAR_LABORATORIOS`
- `CRIAR_LABORATORIO`
- `LISTAR_COMPUTADORES`
- `CRIAR_COMPUTADOR`
- `LISTAR_ALERTAS`
- `CONSULTAR_API_EXTERNA`

Somente o perfil `admin` pode consultar `/auditoria` e visualizar a tabela na tela de Configurações.

## API externa

O ViaCEP foi incluído como integração **complementar**, não como dependência central do funcionamento do sistema. O endpoint é:

```text
GET /externo/cep/{cep}
```

## LGPD

A aplicação evita dados pessoais desnecessários. Nesta versão, os dados pessoais previstos são nome, e-mail e perfil de acesso. Não são previstos dados sensíveis de alunos ou professores.

A tela de Privacidade documenta o tratamento previsto. Em uma implantação real, ainda será necessário definir formalmente controlador, base legal, política de retenção e canal para exercício dos direitos dos titulares.

## Tecnologias

### Frontend
- React
- JavaScript
- HTML/CSS
- Vite
- ESLint

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PyJWT
- Argon2
- HTTPX

### Banco de dados
- PostgreSQL
- Supabase como hospedagem prevista
- SQLite apenas como alternativa local de desenvolvimento

## Arquitetura resumida

```text
Usuário
  ↓
React / Vite
  ↓  JWT + JSON
FastAPI
  ├── autenticação e RBAC
  ├── regras de negócio (RN01)
  ├── auditoria
  └── ViaCEP
  ↓
SQLAlchemy
  ↓
PostgreSQL / Supabase
```

A etapa futura do agente de monitoramento continua prevista:

```text
Computadores dos laboratórios
        ↓
Agente Python + psutil
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Dashboard
```

## Próximas etapas

- agente de monitoramento com `psutil`;
- histórico real de métricas;
- alertas persistidos como entidade própria;
- cadastro/gestão de usuários;
- redefinição de senha;
- relatórios exportáveis;
- testes automatizados mais completos;
- validação em Hyper-V/Windows Server.

## Projeto acadêmico

Projeto desenvolvido como parte do Projeto Final de Curso em Engenharia de Software da Universidade de Mogi das Cruzes (UMC).
