# Evolução aplicada sobre a entrega 14/09

## Base preservada

A reconstrução parte diretamente da versão `entrega1409` enviada pelo aluno. Foram mantidos como referência principal:

- layout do Dashboard;
- tela de Laboratórios;
- tela de Computadores;
- dados demonstrativos de três laboratórios e sessenta computadores;
- RN01 de vínculo obrigatório entre computador e laboratório;
- React/Vite no frontend;
- FastAPI no backend.

## Etapa 1 — persistência

Os dados que antes estavam em listas Python foram migrados para modelos SQLAlchemy:

- `users`;
- `laboratories`;
- `computers`;
- `audit_logs`.

O projeto funciona com PostgreSQL/Supabase através de `DATABASE_URL`. Se a variável estiver vazia, usa SQLite local apenas para facilitar desenvolvimento e testes.

## Etapa 2 — autenticação e autorização

Foi incluído:

- login por e-mail e senha;
- JWT;
- Argon2 para hash de senha;
- perfis `admin`, `tecnico` e `gestor`;
- proteção dos endpoints principais;
- autorização para cadastros e auditoria.

## Etapa 3 — auditoria

A tabela `audit_logs` registra ações relevantes, o usuário associado, IP, entidade e horário. A consulta de auditoria fica restrita ao administrador.

## Etapa 4 — API externa

O ViaCEP é usado como integração complementar em Configurações. Ele não é necessário para cadastrar laboratórios ou computadores e, portanto, não se torna um ponto único de falha do núcleo do projeto.

## Etapa 5 — LGPD

Foi criada uma tela de Privacidade e um endpoint público `/privacidade`. A aplicação trabalha com minimização de dados e prevê nome, e-mail e perfil de acesso como dados pessoais necessários à autenticação.

## Etapa 6 — telas complementares

Indicadores e Relatórios deixaram de ser apenas placeholders. Nesta versão apresentam um resumo funcional dos dados já disponíveis, sem prometer recursos de histórico que ainda não foram implementados.
