# EDU-Infra Analytics — pacote de entrega da Semana 1 (02/11/2026)

**Fonte acadêmica:** monografia UMC anexada, “EDU-INFRA ANALYTICS: SISTEMA PARA DIAGNÓSTICO DA INFRAESTRUTURA TECNOLÓGICA ESCOLAR” (2026). **Base de código:** ZIP V0.1(3) fornecido. Não foi criada uma nova monografia nem alterado seu escopo.

## Entregas verificadas nesta rodada

1. Auditoria da monografia UMC e das **anotações de revisão da V2** (`docs/01_...`), com delimitação de escopo e pendências.
2. Matriz de requisitos RF/RNF/RN e vínculo entre código, teste e monografia (`docs/02_...`).
3. Arquitetura greenfield com diagramas Mermaid de componentes e entidades (`docs/03_...`).
4. Migração inicial Alembic sem seed; executada em SQLite temporário; PostgreSQL alvo da monografia **ainda não validado**.
5. Bootstrap do primeiro administrador com senha Argon2 e validação Pydantic; não cria laboratórios/computadores.
6. REST com GET/POST/PUT/DELETE de laboratórios e computadores; JWT, RBAC e auditoria.
7. React com `fetch` real e estados vazios (código inspecionado); build depende de `npm install` conectado.
8. **19 pytest aprovados** e HTTP **409** comprovado ao excluir laboratório ocupado.
9. Capturas dos resultados SQL e de API em `evidencias/`; logs e histórico Git local exportado em bundle (externo ao ZIP).

## Início rápido no Windows

Leia primeiro [`docs/04_PROCEDIMENTO_VALIDACAO.md`](docs/04_PROCEDIMENTO_VALIDACAO.md), depois o [`README.md`](README.md) do projeto original, e use o `.env.example`. Para desenvolver com PostgreSQL/Supabase, configure **suas próprias** credenciais. Nunca comite `.env` nem gere dados falsos de laboratório na base institucional.

## O que não afirmar à banca ainda

Não está demonstrado deploy PostgreSQL/Supabase, screenshots do próprio React em execução, telemetria real psutil, IIE calculado, histórico de métricas, implantação Hyper-V/Windows Server ou efeitos sobre qualidade educacional. Os HTML/PNG entregues são relatórios visuais **derivados de SQL/API locais**, não prints da interface React. A próxima implementação deve seguir as semanas 2 a 6 do cronograma e o escopo efetivamente descrito na monografia.
