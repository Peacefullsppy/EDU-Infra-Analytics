# Cronograma PFC — 19/10 a 29/11/2026 (6 semanas)

## Semana 1 — 19 a 25/10 | Requisitos, banco vazio e CRUD completo

Entregar: auditoria da V2, backlog RF/RNF/RN, arquitetura greenfield, migração inicial, bootstrap admin, APIs de laboratório e computador (GET/POST/PUT/DELETE), auth/RBAC/auditoria e frontend sem mock. Confirmar que deletar lab ocupado retorna HTTP 409. Evidências: commits, 7+ testes pytest, screenshots de banco vazio e cadastros reais.

## Semana 2 — 26/10 a 01/11 | Qualidade de integração e banco demonstrável

Configurar Supabase/PostgreSQL, migrations Alembic e CORS do ambiente de demonstração; ampliar teste de autorização (401/403), 409, edição e exclusões; alinhar telas responsivas, erros e confirmação; integrar GitHub Actions e coleção Postman. Revisar UML/DER, descrições e monografia (capítulos 1–5).

## Semana 3 — 02 a 08/11 | Agente e métricas reais

Implementar agente Python/psutil numa VM/dispositivo controlado; cadastrar credencial individual de equipamento; endpoint autenticado de ingestão; tabela `MetricSample`; atualização de `last_seen_at`; alerta por limiares e janela de ausência de coleta. Testar com 1–2 equipamentos reais e explicar método de medição.

## Semana 4 — 09 a 15/11 | Diferencial educacional

Criar entidades `EducationalActivity`, `TechnologyRequirement` e ligação laboratório/atividade; permitir cadastrar requisito mínimo (ex. armazenamento e RAM disponível); implementar avaliação de adequação verificável com dados reais/inventário; registrar critérios de validação IIE com orientador. Não fabricar pontuação para cumprir cronograma.

## Semana 5 — 16 a 22/11 | Relatórios, testes e infraestrutura

Adicionar histórico temporal, gráficos com medições reais, CSV/relatório de evidências, testes de integração completos e resposta a falha do agente. Preparar Hyper-V/Windows Server conforme recursos disponíveis. Executar checklist de segurança e consolidar screenshots/vídeo da demonstração.

## Semana 6 — 23 a 29/11 | Monografia, apresentação e ensaio

Finalizar diagramas e seções de implementação/resultados, matriz RF↔teste, referências, ABNT e relatório de limitações. Congelar versão, marcar release/commit, gerar backup seguro do banco, ensaiar defesa de 10–15 minutos e plano de contingência sem acesso ao Supabase. Prever pelo menos dois dias de margem para imprevistos e feedback do orientador.

## Caminho crítico

**Banco → CRUD → autenticação/perfis → agente/telemetria → contexto educacional → evidências de validação → monografia.** Evitar gastar as primeiras semanas aperfeiçoando apenas CSS ou reconstruindo Figma visualmente.

## Plano de contingência caso o cronograma atrase

Prioridade absoluta: CRUD+RBAC+logs+PostgreSQL+testes+agente real em um computador+relação atividade/requisito. Se faltar tempo, cortar integrações ornamentais, animações, ViaCEP e relatórios PDF avançados. Na monografia, registrar de forma explícita o que ficou planejado em vez de simular a entrega.
