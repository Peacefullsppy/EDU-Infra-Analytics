# Parecer de revisão completa — monografia V2 (26 páginas)

**Natureza:** diagnóstico e proposta de reescrita. A V2 não deve ser entregue como descrição do novo software sem passar por atualização e verificação de evidências. As decisões aqui propostas aguardam validação do autor e do orientador.

| Seção/páginas da V2 | Conteúdo encontrado | Correção necessária para a nova edição |
|---|---|---|
| Capa, folha de rosto (1–2) | Título, instituição e orientação | Preservar dados institucionais e confirmar exigências ABNT da UMC; atualizar ano/versão apenas se necessário. |
| Resumo e Abstract (3–4) | Declaram várias funcionalidades **já desenvolvidas** | Reescrever após conclusão de testes do novo sistema; no estágio atual, afirmar apenas entregas comprovadas. |
| Figuras, tabelas e sumário (5–6) | Inventários de arquitetura, classes, BPMN | Recriar imagens e atualizar numeração/citações após a mudança dos diagramas; automatizar sumário no Word. |
| Introdução (7–10) | Problema, objetivos, justificativa, escopo; distinção versão/evolução | Manter recorte acadêmico; acrescentar CRUD de edição/exclusão, coleta autêntica e dados reais; atualizar status real de cada etapa. |
| Literatura (10) | Alves/Xavier/Paula; Soares Neto; UNESCO; OECD; Sommerville; Wieringa | Conservar enquadramento e checar metadados bibliográficos/citações. Literatura não determina fórmula IIE. |
| Arquitetura (10–12) | React→FastAPI→SQLAlchemy→PostgreSQL; SQLite opcional; agente planeado | Desenhar arquitetura **nova**, mostrar rota de coleta como planejada, e distinguir conexão local PostgreSQL/Supabase. |
| Tecnologias (12–13) | React/Vite; Python/FastAPI/Pydantic; SQLAlchemy/Alembic; JWT/Argon2; ViaCEP; GitHub/Pytest/Postman/Hyper-V | Atualizar para bibliotecas efetivamente usadas, versões instaladas e evidências de execução; não chamar ViaCEP ou agente de concluído antes dos testes. |
| Metodologia (13–14) | Desenvolvimento incremental, Scrum adaptado, Projects, UML/BPMN, testes | Documentar **reescrita greenfield** e critérios de aceite por Sprint; inserir rastreabilidade requisito→teste→evidência. |
| Estado atual 5.1 (14) | Diz que sistemas anteriores estavam prontos | Reclassificar segundo entregas da nova base, não preservar rótulos antigos. |
| RF01–RF18 (15–16) | Matriz implementação/parcial/planejado | Manter numeração, atualizar situação; acrescentar RF19–RF26 propostos (editar, excluir, usuários, dados reais, agente autenticado). |
| RNF01–RNF11 (16–17) | Segurança, persistência, validação, usabilidade e evolução | Tornar mensuráveis: status HTTP de autorização, cobertura de testes, tempo de resposta sob carga definida, logs, acessibilidade básica e recuperação de dados. |
| RN01–RN08 (17–18) | Vínculo obrigatório, hostname único, RBAC, viaCEP, IIE | Decidir política de exclusão sem cascata, estados sem coleta, origem das métricas e tratamento de ausência de dados. |
| Diagrama de classes 5.5 (18–19) | 4 entidades persistidas + serviços + domínio acadêmico planejado | Recriar conforme `models.py`; exibir extensão `MetricSample`, `MonitoringCredential`, `Activity/Requirement` apenas quando explicitamente projetadas/implementadas. |
| BPMN 5.6 (20–21) | Mostra agente, persistência de métricas/alerta/indicadores | Separar BPMN do fluxo **implementado agora** do fluxo **futuro**; evitar confundir atividade planejada com execução comprovada. |
| Domínio educacional 5.7 (22) | Contextos de disciplina/turma/atividade e adequação | Implementar extensão mínima verificável; ex.: “atividade exige 8 GB RAM” só deve gerar compatibilidade com inventário real, não CPU% de uso. |
| IIE 5.8 (22–23) | Índice exploratório; fórmula e pesos ainda não validados | Manter `não calculado` e explicar método de futura construção; não usar sementes ou pontuação arbitrária. |
| Segurança/LGPD 5.9 (23–24) | JWT, Argon2, RBAC, auditoria, redução dados pessoais | Acrescentar ameaças e testes de autorização, chaves em `.env`, retenção e diferença entre aplicação acadêmica e produção. |
| Persistência 5.10 (24) | PostgreSQL/Supabase e Alembic, SQLite local | Atualizar tabelas e migrações da reconstrução, logs de validação do banco e política RESTRICT. |
| Considerações 6 (24–25) | Tratam a versão anterior como concluída e agente como próximo passo | Reescrever por evidências finais, resultados de testes, riscos, limitações e trabalhos futuros. |
| Bibliografia (25–26) | Referências conceituais e técnicas | Validar conformidade ABNT, URLs, datas de acesso e citações cruzadas; não afirmar consulta a referências que não foram verificadas. |

## Ajustes editoriais e metodológicos fundamentais

1. Evitar frases “atualmente implementado” sem prova (commit, tela executada, teste ou consulta SQL).
2. Separar dados cadastrais de telemetria: cadastro de computador não fornece *status online* verificável.
3. Distinguir **disponibilidade observada** do IIE. Sem coleta, porcentagem de disponibilidade é *indisponível*, não 0%.
4. Discutir riscos de exclusão de laboratório com computadores: `RESTRICT` + 409 + mensagem amigável.
5. Enfatizar o diferencial educacional: requisito de capacidade de **atividade** versus capacidade de equipamentos, sem usar dados de alunos.
6. Substituir screenshots de templates/números artificiais por telas com dados provenientes de testes e registros criados ao vivo.
7. No capítulo de testes, apresentar cenário, método, dado de entrada, resultado esperado, resultado obtido, ambiente e data.

## Recomposição sugerida da monografia final

1. Introdução: problema, objetivo, escopo e recorte educacional.
2. Referencial teórico: infraestrutura tecnológica educacional, monitoramento, manutenção e requisitos.
3. Metodologia: desenvolvimento incremental greenfield, critérios de aceite e ferramentas.
4. Requisitos: RF/RNF/RN, rastreabilidade e prioridades.
5. Projeto técnico: arquitetura, BPMN implementado, UML/DER, API, segurança/LGPD e dados.
6. Implementação: backend, banco, frontend, agente, módulos educacionais — apenas o que existir.
7. Testes e resultados: endpoints, autorização, persistência, coleta, indicadores, usabilidade e limitações.
8. Conclusões: relação com objetivos, limites e evolução futura.
9. Referências e apêndices: Swagger/OpenAPI, cenários de testes, screenshots, configurações sem segredo.

**Observação:** a nova estrutura é proposta, não norma institucional verificada. Validar com orientador e manual da instituição antes da diagramação final.
