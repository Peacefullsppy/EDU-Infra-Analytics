# Backlog de requisitos e matriz de rastreabilidade — monografia UMC

**Origem e método:** a seção 5.1 da monografia apresenta funcionalidades por prioridade, mas **não as enumera** como RF/RNF/RN. Os IDs abaixo são estabelecidos **nesta engenharia de requisitos**, sem atribuí-los literalmente à monografia. A enumeração V2 do relatório antigo é histórica e pode ser diferente. Os itens são classificados como **S1** (alvo da Semana 1) ou **posterior** (previstos na monografia, mas não concluídos nesta entrega).

## Requisitos funcionais (RF)

| ID | Requisito | Referência na monografia | Sprint | Estado e critério de aceite |
|---|---|---|---|---|
| RF01 | Autenticar usuários por e-mail/senha e sessão JWT | 2.4; 3.7.1 | S1 | **Testado:** login correto 200; inválido 401; `/auth/me` protegido |
| RF02 | Administrador inicial criado explicitamente | 3.7 (desdobramento técnico) | S1 | **Testado por evidência:** sem usuário inicial; CLI cria apenas primeiro admin; senha hash |
| RF03 | Restringir ações segundo perfil admin/técnico/gestor | 3.7.3 | S1 | **Testado:** gestor não altera; técnico não exclui laboratório; admin consulta auditoria |
| RF04 | Listar, consultar, criar, editar e excluir laboratórios | 1.2.2; 5.1 item 1 | S1 | **Testado:** GET/POST/PUT/DELETE e 409 quando ocupado |
| RF05 | Listar, consultar, criar, editar e excluir computadores | 1.2.2; 5.1 item 1 | S1 | **Testado:** GET/POST/PUT/DELETE, vínculo existente, hostname único |
| RF06 | Exibir dashboard com dados efetivamente cadastrados | 2.6; 5.1 item 5 | S1/base | **Parcial:** totais SQL corretos; estados de operação ainda sem agente |
| RF07 | Registrar auditoria de login e alteração | 2.4; 3.7 e gestão técnica | S1 | **Testado:** CREATE/UPDATE/DELETE e autenticação, admin-only para consulta |
| RF08 | Coletar CPU, RAM, disco, SO e uptime por agente Python/psutil | 2.2–2.3; 5.1 item 2 | posterior | **Não implementado**; exigir origem e timestamp verificáveis |
| RF09 | Distinguir disponibilidade/online/offline/sem coleta e anomalias | 1.4; 5.1 item 3 | posterior | **Parcial:** cálculo do estado definido, mas ainda sem ingestão |
| RF10 | Gerar alertas de degradação baseados em medições | 2.4; 5.1 item 3 | posterior | **Parcial:** leitura derivada, sem métricas reais/alertas persistidos |
| RF11 | Calcular IIE de laboratório com método fundamentado | 1.4; 5.1 item 4 | posterior | **Não implementado**; na ausência de fórmula validada, valor `null` |
| RF12 | Apresentar dados de infraestrutura, alertas e IIE no dashboard | 2.6; 5.1 item 5 | posterior | **Parcial:** totais e telas, sem IIE ou telemetria |
| RF13 | Consultar histórico de medições e indicadores | 2.5; 5.1 item 6 | posterior | **Não implementado**; faltam séries históricas |
| RF14 | Emitir relatório-resumo de infraestrutura | 2.6; 5.1 item 6 | S1/base | **Parcial:** relatório resumo atual, sem histórico exportável |
| RF15 | Administrador gerenciar usuários e estados | 3.7 (desdobramento técnico) | S1 | **Testado:** criar/desativar usuários, com RBAC |

## Requisitos não funcionais (RNF)

| ID | Categoria | Critério verificável de aceite | Estado atual |
|---|---|---|---|
| RNF01 | Segurança | Endpoints de dados retornam 401 sem token e 403 para papel inadequado | **Testado** |
| RNF02 | Senhas | Nunca armazenar senha em claro; hash Argon2 em usuários | **Implementado; política de recuperação pendente** |
| RNF03 | Persistência | SQLAlchemy e Alembic criam schema sem dados predefinidos | **Testado em SQLite; PostgreSQL pendente** |
| RNF04 | Integridade | FK impede órfão; nenhuma exclusão em cascata de computadores | **Testado** |
| RNF05 | Validação | Pydantic rejeita entradas inválidas com HTTP 422 | **Testado** |
| RNF06 | Usabilidade | Formulários exibem erro e confirmação; tela vazia é explícita | **Inspecionado no código; QA visual pendente** |
| RNF07 | Responsividade | Interface deve atender telas desktop e móveis | **CSS disponível; inspeção em navegador pendente** |
| RNF08 | Disponibilidade | API `/health` consulta conexão; evitar afirmar uptime não monitorado | **Implementado; SLO não definido na monografia** |
| RNF09 | Rastreabilidade | Gravar usuário/ação/entidade/timestamp em operações críticas | **Testado** |
| RNF10 | Privacidade/LGPD | Minimizar dados pessoais; definir retenção, acesso e consentimentos/base legal apropriada com instituição | **Parcial** |
| RNF11 | Qualidade | Executar ≥ 7 testes pytest verdes, com caso explícito HTTP 409 | **27 aprovados nesta revisão (02/11/2026)** |
| RNF12 | Comunicação segura | Configurar HTTPS e segredos fora do Git para implantação | **Parcial; TLS de produção pendente** |

## Regras de negócio (RN)

| ID | Regra formal | Evidência e expectativa |
|---|---|---|
| RN01 | Todo computador deve pertencer a um laboratório existente | FK `RESTRICT`; 404 para laboratório ausente |
| RN02 | `hostname` identifica unicamente cada computador e é normalizado | Índice UNIQUE; conflito 409 |
| RN03 | Gestor somente consulta dados; técnico cadastra/edita; admin também gerencia acessos | Ver RBAC em `security.py` e testes |
| RN04 | Excluir laboratório é operação exclusiva de administrador | Técnico/gestor recebem 403 |
| RN05 | Excluir laboratório com computador vinculado é proibido | **HTTP 409**, preservar laboratório e computador |
| RN06 | Excluir computador não deve excluir automaticamente o laboratório | DELETE PC 204 e FK preservada |
| RN07 | Usuário desativado não obtém login nem acesso por JWT emitido anteriormente | Login 403, recurso 401 |
| RN08 | Auditoria dos eventos não pode ser consultada por técnico ou gestor | HTTP 403 |
| RN09 | Migração inicial deve criar tabelas vazias, sem dados demonstrativos | `0001_empty`; SQL counts == 0 |
| RN10 | Computador recém-cadastrado sem telemetria é `sem_coleta`, nunca automaticamente `online` | Teste de cadastro retorna `sem_coleta` |
| RN11 | Percentual de disponibilidade observado exclui estado sem coleta do denominador e conta `online`, `atencao`, `critico` como conectados | `logic.py`; teste de estados |
| RN12 | IIE não pode ser inferido de simples cadastro ou pesos improvisados | API `iie: null`; cálculo aguarda definição fundamentada |
| RN13 | Contas de gestão são criadas explicitamente; não existem senhas iniciais padronizadas | CLI create-admin; senhas hash |
| RN14 | Não coletar dados individuais de aluno/professor no monitoramento | Recorte LGPD da monografia (3.7.5) |

## Matriz sintética de rastreabilidade

| Fluxo | Requisito(s) | Implementação | Teste/evidência |
|---|---|---|---|
| Login e perfis | RF01, RF03, RNF01, RNF02, RN03, RN07 | `security.py`, `main.py` | `test_without_token_is_blocked`, `test_login_perfil_e_consulta_do_proprio_usuario`, `test_token_invalido_retorna_401`, `test_user_management_and_inactive_login` |
| Bootstrap inicial | RF02, RN09, RN13 | `cli.py`, migração | `scripts/gerar_evidencias_semana1.py` |
| CRUD laboratórios | RF04, RN01, RN04, RN05 | `main.py`, `models.py` | `test_crud_and_protection_of_laboratory_with_computers`, `test_computador_ocupando_laboratorio_impede_delete_409_e_nao_remove_dados` |
| CRUD computadores | RF05, RN01, RN02, RN06 | `main.py`, `schemas.py` | `test_duplicate_hostname_and_input_validation`, `test_hostname_duplicado_na_edicao_retorna_409` |
| Auditoria | RF07, RN08, RN09 | `AuditLog`, `audit()` e API admin | `test_auditoria_registra_criacao_edicao_e_exclusao` |
| Dashboard vazio | RF06, RN10, RN12 | `logic.py`, `Dashboard` em `App.jsx` | `test_database_begins_without_labs_and_without_metrics`; prints SQL em `evidencias/` |
| Agente e IIE | RF08–RF13 | *Ainda não implementado* | Sem comprovação: próximos incrementos |

## Refinamento de requisitos em 02/11/2026 (sem mudança de escopo)

| ID | Complemento vinculado ao requisito existente | Aceite e evidência |
|---|---|---|
| RF04 | Buscar laboratórios por nome/localização e filtrar ativos/inativos | `test_busca_laboratorios_por_nome_local_e_ativo`; tela `Laboratories` |
| RF05 | Buscar computadores por hostname e por laboratório | `test_busca_computadores_por_hostname_e_laboratorio` |
| RNF04 | Evitar dois registros do mesmo ambiente | Migração `0002_unique_labs` + HTTP 409; backup/checagem em bancos já utilizados |
| RNF06 | Não exibir dados anteriores como atuais após falha de carregamento | `useLoad` reinicia a consulta; teste em navegador pendente |
| RN15 | Não permitir duplicar laboratório com nome e localização iguais (ignorando caixa) | HTTP 409 em POST/PUT; testes de duplicidade simples, edição e acentuação |
| RN05 | Preservar o HTTP 409 também em conflito de vínculo detectado durante a gravação | `IntegrityError` protegido por rollback; concorrência simultânea pendente de simulação |

Os identificadores acima são desdobramentos de engenharia dos requisitos da monografia, e não numeração original do texto acadêmico.
