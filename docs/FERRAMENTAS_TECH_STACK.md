# Como usar o stack na reconstrução, ferramenta por ferramenta

| Ferramenta | Responsabilidade | Uso neste ciclo |
|---|---|---|
| **VS Code** | Edição e depuração | Abrir pasta raiz; terminais separados para API e frontend; configurações .env locais. |
| **Python 3.12+ / FastAPI** | Endpoints, autorização e validação | Servir `app.main:app` por Uvicorn; Swagger automático em `/docs`. |
| **Pydantic** | Contratos REST e validação | Esquemas de laboratório, computador, login e usuário, com limites de comprimento e IP válido. |
| **SQLAlchemy 2** | ORM/transações | Classes User, Laboratory, Computer, AuditLog. Chaves estrangeiras e `RESTRICT`. |
| **Alembic** | Migração versionada | Executar `python -m alembic upgrade head` no banco novo; não usar scripts de seed. |
| **PostgreSQL + Supabase** | Persistência final da demo | Criar projeto isolado, copiar URI de conexão no `.env` do backend, nunca commitá-la; testar `/health`. |
| **SQLite (dev local)** | Rápida execução local | Selecionado explicitamente no `.env.example`; não confundir validação local com banco final. |
| **React + Vite** | Interface web | Tela e estilos autorais, fetch em `/api/v1`, atualização após operações; estados vazios reais. |
| **Git/GitHub** | Versionamento e rastreabilidade | Repositório novo, branch de feature por incremento, PR, tags de release; workflow pytest no push/PR. |
| **GitHub Projects** | Backlog | Colunas A Fazer, Em Andamento, Em Validação, Concluído; um cartão por requisito/critério de aceite. |
| **Pytest + HTTPX** | Validação automática | Testes CRUD, login, RBAC, integridade e banco vazio; executar a cada commit. |
| **Postman** | Cenários manuais de API | Importar coleção do diretório docs; colocar base URL e token dinamicamente, registrar evidências. |
| **psutil** | Métricas de CPU/RAM/disco | **Semana 3**: agente separado, execução em computador autorizado, token por dispositivo e registro temporal. |
| **Hyper-V + Windows Server** | Demonstração da infraestrutura | **Semana 5**: laboratório controlado para executar agente e demonstrar coleta/segurança. |
| **Figma** | Design da experiência, não base de dados | Opcional: esboçar fluxos vazios e estados de erro. Não importar telas do projeto antigo ou números desenhados. |
| **ViaCEP** | Integração externa complementar | Adiar para depois do núcleo; não faz parte do cadastro nem do monitoramento. |

## Fluxo de trabalho sugerido

1. Criar a issue no GitHub Projects (ex.: `RF20 – bloquear exclusão de laboratório ocupado`).
2. Descrever cenário esperado e teste de autorização (admin vs gestor/técnico).
3. Implementar migração/modelo → schema/service → endpoint → teste → tela → mensagem de erro.
4. Rodar testes backend e build frontend, abrir pull request e revisar resultado no Postman.
5. Capturar evidência real, registrar status do requisito e corrigir o capítulo correspondente da monografia.

## Segurança operacional

Não enviar `.env`, URL com senha do Supabase, chaves JWT ou usuários reais em screenshots. Não executar agente em máquinas não autorizadas. Usar identificadores de teste rotulados como *teste* apenas na documentação ou banco de teste, nunca no banco vazio inicial da aplicação.
