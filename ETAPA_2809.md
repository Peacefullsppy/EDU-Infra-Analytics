# Etapa documentada — 28/09

## Objetivo

Documentar e validar a etapa que exige login, auditoria, informações relacionadas à LGPD e integração com API externa, incluindo persistência em PostgreSQL hospedável no Supabase.

## Requisitos atendidos

### 1. Login

Implementado no frontend e no FastAPI.

- endpoint: `POST /auth/login`;
- usuário identificado pelo e-mail;
- senha armazenada somente como hash Argon2;
- token JWT com expiração configurável;
- endpoint `GET /auth/me` para validar a sessão;
- rotas de negócio exigem autenticação.

### 2. Controle de acesso

Perfis:

- `admin`;
- `tecnico`;
- `gestor`.

A criação de usuários e a visualização do log de auditoria são restritas ao administrador. Cadastros de laboratórios e computadores são permitidos para administrador e técnico.

### 3. Auditoria

Tabela: `audit_logs`.

Cada registro pode conter:

- usuário responsável;
- ação;
- recurso;
- identificador do recurso;
- método HTTP;
- caminho da API;
- detalhes técnicos mínimos;
- data e hora.

Não são armazenadas senhas, JWTs ou o conteúdo das credenciais.

### 4. LGPD

Foi adicionada uma página pública de Política de Privacidade e Termo de Uso, acessível a partir da tela de login.

O projeto mantém a abordagem de minimização: nome, e-mail e perfil são os dados pessoais previstos para os usuários do sistema. O MVP não prevê dados sensíveis de alunos ou professores.

A página deixa claro que uma implantação real deverá definir formalmente:

- controlador;
- base legal aplicável;
- prazos de retenção;
- canal para exercício de direitos;
- processo institucional de resposta a incidentes.

### 5. API externa

Serviço: ViaCEP.

Endpoint interno:

```text
GET /integracoes/cep/{cep}
```

O backend valida o CEP, consulta o serviço externo e devolve uma resposta reduzida com os campos relevantes. A integração é opcional e não é necessária para que laboratórios, computadores e monitoramento funcionem.

### 6. PostgreSQL e Supabase

O backend utiliza SQLAlchemy. A URL de conexão é recebida exclusivamente por variável de ambiente:

```text
DATABASE_URL
```

Para ambiente local conectado ao Supabase, recomenda-se copiar do painel do projeto a connection string exibida em **Connect**. Em rede IPv4 pode ser utilizado o Session pooler na porta 5432.

O backend não usa chave pública do Supabase para acessar o banco. A conexão PostgreSQL ocorre somente pelo servidor FastAPI e a credencial permanece em `.env`.

## Entidades persistidas

### users

Dados de autenticação e perfil.

### laboratories

Laboratórios cadastrados.

### computers

Computadores vinculados aos laboratórios.

### audit_logs

Acessos e ações relevantes.

## Evidências sugeridas para apresentar ao orientador

1. Supabase mostrando as quatro tabelas criadas.
2. `GET /health` retornando banco conectado.
3. Login funcional na interface.
4. Tentativa de acessar uma rota sem JWT retornando `401`.
5. Cadastro de laboratório e computador.
6. Tentativa da RN01 com `laboratorio_id` inexistente retornando `400`.
7. Página Configurações exibindo registros de auditoria.
8. Consulta de CEP pela integração externa.
9. Página de Política de Privacidade/LGPD.
10. Repositório Git com `.env` ausente e `.env.example` presente.

## Fluxo lógico

```text
[Login React]
     |
     | e-mail + senha
     v
[FastAPI /auth/login]
     |
     | verifica hash
     v
[PostgreSQL / users]
     |
     | JWT
     v
[Frontend autenticado]
     |
     +----> laboratórios / computadores / dashboard
     |                 |
     |                 v
     |             PostgreSQL
     |
     +----> configurações ----> ViaCEP
     |
     +----> auditoria --------> audit_logs
```

## Limitações desta etapa

- O projeto ainda não possui recuperação de senha por e-mail.
- O fluxo de consentimento não foi implementado porque não há cadastro público de usuários; as contas são administrativas.
- Alembic ainda não está configurado; as tabelas desta etapa são criadas pelo SQLAlchemy.
- A política apresentada é uma implementação acadêmica e deverá ser revisada institucionalmente antes de uma implantação real.
