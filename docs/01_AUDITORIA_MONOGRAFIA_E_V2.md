# Auditoria de conformidade — EDU-Infra Analytics, marco da Semana 1

**Data da revisão:** 02/11/2026. **Fontes:** (A) `EDU_Infra_Analytics_Projeto_Completo_UMC(1).docx`, 24 páginas; (B) o relatório `docs/REVISAO_MONOGRAFIA_V2.md` e a matriz `docs/ESCOPO_E_REQUISITOS.md` presentes no ZIP V0.1(3); (C) código do próprio ZIP V0.1(3) e alterações desta entrega. **Importante:** o arquivo original da monografia V2 de 26 páginas **não foi anexado nesta rodada**. Portanto, a V2 é auditada **indiretamente** a partir das notas (B); a monografia UMC anexada (A) é a referência prioritária. Não confundir as duas versões.

## 1. Escopo acadêmico autorizado pela monografia entregue

A monografia define como objetivo geral monitorar e analisar infraestrutura tecnológica de ambientes educacionais, permitindo identificar problemas e apoiar decisões (1.2, p. 7). A versão inicial contempla: cadastro de laboratórios e computadores; agente Python/psutil; CPU, RAM, armazenamento e disponibilidade; diagnóstico por alertas; Índice de Infraestrutura Educacional (IIE); dashboard; relatórios e histórico (1.4, p. 8; 2.2–2.7, pp. 10–11; 5.1, p. 21). Stack: React/JS/HTML/CSS, Python/FastAPI/Pydantic, PostgreSQL/SQLAlchemy/Alembic, JWT/RBAC/hashing, GitHub Projects, pytest/Postman, Hyper-V/Windows Server (capítulos 2–4).

A mesma monografia **exclui** explicitamente do MVP IA, manutenção preditiva, integração com sistemas acadêmicos, aplicativo móvel, automações avançadas e monitoramento completo de redes/servidores (1.4). Logo, as propostas da revisão V2 relativas a ViaCEP, cadastro de atividades acadêmicas, comparação de requisitos pedagógicos, inferência de resultados escolares ou integração acadêmica **não se tornam requisitos do projeto atual automaticamente**. Precisam de decisão formal e revisão da monografia, antes de qualquer implementação.

## 2. Matriz de auditoria, capítulos 1–6

| Local da monografia | Requisito/alegação | Código e evidência observada | Avaliação |
|---|---|---|---|
| 1.2, p. 7 | Gestão dos laboratórios/equipamentos | CRUD GET/POST/PUT/DELETE e teste de vínculo/409 | **Implementado e testado em SQLite** |
| 1.4, p. 8 | Monitoramento básico CPU/RAM/disco/disponibilidade | Colunas nullable e estado `sem_coleta` existem; não há agente/endpoint de coleta | **Planejado; não comprova coleta** |
| 1.4 e 5.1, pp. 8/21 | IIE | API devolve `null`; nenhum peso/fórmula validado | **Pendente; não inventar pontuação** |
| 2.1–2.7, pp. 9–11 | Cinco componentes conectados | API, banco e interface em código; agente ausente | **Parcial** |
| 2.5 e 3.3, pp. 11/13–14 | PostgreSQL e Alembic | Migração `0001_empty`; execução demonstrada **em SQLite** | **Migração testada, PostgreSQL não verificado** |
| 2.6 e 3.1, pp. 11–13 | React, dashboard e telas | Código busca dados via `fetch` real, sem array de registros fixos; build não executado (npm indisponível) | **Implementado no código, execução visual pendente** |
| 3.7, pp. 17–18 | Autenticação e permissões | JWT, Argon2, RBAC admin/técnico/gestor e testes HTTP 401/403 | **Implementado e testado** |
| 3.7.5, p. 18 | LGPD | Minimização de nome/e-mail/perfil e aviso; retenção institucional não definida | **Parcial** |
| 3.8, p. 18 | Hyper-V/Windows Server | Nenhuma VM/servidor acessível nesta execução | **Pendente** |
| 4.2–4.5, pp. 19–20 | Scrum adaptado, requisitos, rastreabilidade, validação | Arquivos de cronograma, requisitos, testes e evidências nesta entrega | **Documentado; validação contínua** |
| 5.1, p. 21 | Alertas/indicadores/relatórios/histórico | Rotas resumidas e alertas derivados do estado atual; sem amostras temporais reais | **Parcial** |
| 6, p. 21 | Projeto ainda em desenvolvimento | Não apresentar métricas finais de impacto nem implantação como validadas | **Coerente com estado real** |

## 3. Auditoria técnica do ZIP V0.1 de origem

**Conformidades confirmadas:** código separa modelos, schemas, segurança e lógica; usuário administrador inicial apenas via CLI, sem contas default; migração sem `INSERT`; relação `Computer.laboratory_id` obrigatória com `ondelete=RESTRICT`; endpoints de CRUD com autenticação e papéis; front busca dados de HTTP; testes de negócio e conflito 409; histórico de alterações em `AuditLog`.

**Correções desta entrega:** cálculo de disponibilidade considera os estados online, atenção e crítico como computadores **conectados** dentro das medições observadas; CLI do administrador inicial passa a validar e-mail, nome e senha no mesmo schema Pydantic da aplicação; cobertura pytest ampliada de 7 para 19 casos com autorização, conflito, rollback e integridade.

**Restrições honestas:** os testes usam SQLite temporário com FKs habilitadas, não PostgreSQL; não houve execução bem-sucedida de `npm install`/`vite build` por falha DNS com o registry npm; não há screenshot do React em execução; não houve implantação Hyper-V; não há coleta de agentes, amostras de métricas ou cálculo IIE; auditoria em produção e LGPD exigem políticas institucionais, gestão de segredos, TLS e supervisão.

## 4. Parecer conclusivo da Semana 1

A entrega **atinge tecnicamente** a maior parte do marco de construção da Semana 1 no ambiente local, incluindo 7+ testes e confirmação explícita de HTTP 409. A produção de evidências é reproduzível e **não usa o banco institucional**. Entretanto, não deve ser rotulada como deploy PostgreSQL, frontend visualmente validado, conclusão da monografia ou sistema de monitoramento funcional. A validação em PostgreSQL, a execução visual do React e o desenvolvimento do agente são tarefas distintas do cronograma posterior.

**Cadeia de evidências:** `backend/tests/`, `evidencias/resultado_evidencias.json`, `evidencias/*.png`, `docs/02_REQUISITOS_RF_RNF_RN.md`, `docs/03_ARQUITETURA_GREENFIELD.md`, `docs/04_PROCEDIMENTO_VALIDACAO.md`, `docs/05_COMMITS_E_EXECUCAO.md`.
