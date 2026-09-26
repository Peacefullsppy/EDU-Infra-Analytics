# EDU-Infra Analytics

Sistema para diagnóstico e monitoramento da infraestrutura tecnológica de ambientes educacionais.

## Etapa 28/09 — segurança, persistência e integrações

Esta versão evolui o MVP para atender à etapa de validação com:

- login funcional;
- autenticação por JWT;
- senhas armazenadas com hash Argon2;
- controle de acesso por perfil (`admin`, `tecnico` e `gestor`);
- PostgreSQL como banco de dados;
- configuração pronta para PostgreSQL hospedado no Supabase;
- logs de auditoria de acessos e ações;
- página com Política de Privacidade e informações relacionadas à LGPD;
- integração externa com o ViaCEP;
- manutenção da RN01: todo computador deve estar associado a um laboratório existente.

## Arquitetura desta etapa

```text
React
  |
  | HTTPS / JSON + JWT
  v
FastAPI
  | \
  |  \----> ViaCEP (API externa opcional)
  |
  v
SQLAlchemy
  |
  v
PostgreSQL / Supabase
  |
  +-- users
  +-- laboratories
  +-- computers
  +-- audit_logs
```

## 1. Criar o banco no Supabase

1. Crie um projeto no Supabase.
2. Abra **Connect** no painel do projeto.
3. Para desenvolvimento local em redes IPv4, copie a conexão **Session pooler**, porta `5432`.
4. Copie `backend/.env.example` para `backend/.env`.
5. Cole a connection string em `DATABASE_URL`.

Exemplo de formato:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:SENHA@HOST_POOLER:5432/postgres?sslmode=require
```

Não copie literalmente o exemplo acima: use os dados mostrados pelo Supabase.

## 2. Configurar o backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env` e preencha:

```env
DATABASE_URL=...
JWT_SECRET_KEY=...
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@escola.edu
ADMIN_PASSWORD=uma-senha-forte
```

Para gerar uma chave JWT pelo Python:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Coloque o resultado em `JWT_SECRET_KEY`.

## 3. Criar tabelas e usuário administrador

Com o `.venv` ativado:

```powershell
python -m app.seed
```

O comando:

- cria as tabelas no PostgreSQL/Supabase;
- cria o usuário administrador definido no `.env`;
- cria os três laboratórios e os computadores de demonstração caso o banco esteja vazio.

Depois execute:

```powershell
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Teste da conexão com o banco:

```text
GET /health
```

Resposta esperada:

```json
{
  "status": "ok",
  "database": "conectado"
}
```

## 4. Executar o frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Acesse:

```text
http://localhost:5173
```

Faça login com `ADMIN_EMAIL` e `ADMIN_PASSWORD` definidos no backend.

## Login e autorização

A rota de login é:

```text
POST /auth/login
```

Após autenticar, o backend devolve um token JWT. O frontend mantém o token apenas na sessão do navegador e o envia no header:

```text
Authorization: Bearer TOKEN
```

Perfis implementados:

| Perfil | Acesso principal |
|---|---|
| `admin` | leitura, cadastros, criação de usuários e auditoria |
| `tecnico` | leitura e cadastro de laboratórios/computadores |
| `gestor` | consulta das informações |

## Auditoria

Os registros são armazenados na tabela:

```text
audit_logs
```

São registrados, entre outros:

- login realizado;
- tentativa de login inválida;
- visualização do dashboard;
- listagem de laboratórios;
- cadastro de laboratório;
- listagem de computadores;
- cadastro de computador;
- consulta de alertas;
- consulta à API externa ViaCEP.

O administrador pode consultar os registros em **Configurações** ou pela API:

```text
GET /auditoria
```

Senhas e tokens não são gravados nos logs.

## Integração com API externa

A integração escolhida para esta etapa é o **ViaCEP**.

Fluxo:

```text
Usuário
  |
  v
Tela Configurações
  |
  v
FastAPI /integracoes/cep/{cep}
  |
  v
ViaCEP
  |
  v
FastAPI normaliza a resposta
  |
  v
Frontend
```

A integração é auxiliar. Se o ViaCEP estiver indisponível, o monitoramento principal continua funcionando.

## LGPD

A tela de login possui acesso à página **Política de Privacidade e Termo de Uso**.

Nesta versão são previstos apenas:

- nome;
- e-mail;
- perfil de acesso.

O MVP não prevê dados pessoais sensíveis de alunos ou professores.

Os registros de auditoria são utilizados para rastreabilidade e segurança. A política deixa explícito que, em uma implantação institucional real, a instituição deverá definir controlador, bases legais, canal dos titulares e prazos de retenção.

## RN01 — vínculo entre computador e laboratório

> Todo computador cadastrado deve estar vinculado a um laboratório previamente cadastrado.

A validação continua no backend antes de salvar o computador no PostgreSQL.

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

Resultado esperado:

```text
400 Bad Request
```

## Estrutura principal

```text
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    security.py
    audit.py
    external.py
    seed.py
  .env.example
  requirements.txt

frontend/
  src/
    pages/
      Login/
      Dashboard/
      Laboratories/
      Computers/
      Settings/
      Privacy/
    services/api.js
  .env.example

docs/
  ETAPA_2809.md
```

## Segurança de configuração

Nunca envie para o GitHub:

```text
.env
```

O `.gitignore` já está preparado para ignorá-lo. Envie apenas:

```text
.env.example
```

## Status

**Em desenvolvimento.**

Esta etapa entrega a base funcional de persistência, login, autorização, auditoria, privacidade/LGPD e integração externa. Indicadores, relatórios avançados, agente de monitoramento e migrações com Alembic continuam como próximas etapas do MVP.
