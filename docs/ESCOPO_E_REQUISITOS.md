# Reconstrução do EDU-Infra Analytics — análise de escopo e rastreabilidade

**Fontes utilizadas apenas para análise:** monografia V2 (26 páginas) e ZIP `EDU-Infra-Analytics-testes-unitarios(1).zip`. **Não** houve reutilização de código, CSS, imagens ou telas do ZIP. O novo repositório não contém arquivo `seed.py` nem dados demonstrativos. **Atualizado em:** 20/10/2026.

## 1. Problema e objetivo

O problema da monografia (seções 1.1–1.4) permanece pertinente: equipes de TI educacionais precisam centralizar estado de computadores e laboratórios para apoiar planejamento de manutenção e identificação de indisponibilidade. O diferencial **educacional** não é apenas usar computadores em escolas; é permitir avaliar, futuramente, se um laboratório atende às exigências técnicas de uma atividade acadêmica (seção 5.7). O projeto não mede aprendizagem, notas ou qualidade pedagógica.

## 2. Requisitos V2 versus reconstrução

Legenda: **N** = implementado *na nova base V0.1*, **P** = planejado para a reconstrução, **PA** = parcialmente coberto. Os rótulos “Implementado” da V2 descrevem a versão anterior e devem ser reclassificados durante a reescrita da monografia.

| Requisito V2 | Entrega no sistema novo | Estado novo | Critério de aceite |
|---|---|---|---|
| RF01 autenticação | JWT + senha Argon2 | N | Login válido retorna token; inválido retorna 401 |
| RF02 consulta usuário | `/auth/me` | N | Dados do próprio usuário, rota protegida |
| RF03 RBAC admin/técnico/gestor | Permissões backend | N | Gestor não realiza escrita; só admin acessa auditoria |
| RF04 laboratórios | Listar, consultar, criar, editar, excluir | N, ampliado | Banco vazio; CRUD completo com 409 ao excluir laboratório ocupado |
| RF05 computadores | Listar, consultar, criar, editar, excluir | N, ampliado | Registros inseridos manualmente com laboratório válido |
| RF06 vínculo obrigatório | Validação no backend + FK `RESTRICT` | N | Laboratório inválido retorna 404 e não insere PC |
| RF07 dashboard | Contagens reais e ausência explícita de cálculo IIE | PA | Sem dados retorna zero e IIE `null`, sem gráfico fictício |
| RF08 alertas de visualização | Endpoint derivado do estado comprovado | PA | Sem telemetria não gera alertas artificiais |
| RF09 indicadores por laboratório | Contagem por laboratório; IIE ausente | PA | Contagem real por laboratório; metodologia IIE futura |
| RF10 relatório-resumo | Endpoint e tela de consulta | N/PA | Gera resumo real; exportação avançada pendente |
| RF11 auditoria | Login e mutações gravados | PA | Eventos persistem; ampliar para eventos de coleta e falhas |
| RF12 auditoria exclusiva admin | `/auditoria` | N | Demais perfis recebem 403 |
| RF13 privacidade | Endpoint e tela | N/PA | Informações básicas; política de retenção institucional pendente |
| RF14 ViaCEP | Não incluído no núcleo reconstruído | P | Integração opcional, sem bloquear CRUD |
| RF15 agente Python + psutil | Não implementado | P | Agente envia métricas com credencial própria e registro de erro |
| RF16 histórico de métricas | Não implementado | P | Tabela temporal consultável com timestamps |
| RF17 contexto acadêmico | Não implementado | P | Cadastrar atividade e vínculo com laboratório sem dados de alunos |
| RF18 adequação educacional | Não implementado | P | Comparar requisitos técnicos contra parque de máquinas |

## 3. Novos requisitos propostos (sujeitos à aprovação)

- **RF19**: editar os dados de laboratório e registrar quem alterou.
- **RF20**: excluir laboratório somente se não houver computadores vinculados, e somente por `admin`.
- **RF21**: editar hostname, IP e laboratório do computador com validação de unicidade.
- **RF22**: excluir computador com autorização `admin`/`tecnico` e auditoria.
- **RF23**: administrador cria/ativa/desativa usuários, sem credenciais de demonstração.
- **RF24**: apresentar dados vazios e indicadores indisponíveis de forma honesta, sem valores simulados.
- **RF25**: autenticar a coleta automática e manter rastreabilidade temporal da origem da medição.
- **RF26**: definir política de estados: `sem_coleta` não é `offline` e cadastro não é confirmação de conectividade.

## 4. Regras de negócio revistas

| Regra | Conteúdo e decisão |
|---|---|
| RN01 (V2) | Todo computador pertence a laboratório existente: mantida, verificada na API e no banco. |
| RN02 (V2) | Hostname único: mantida, normalização para maiúsculas. |
| RN03 (V2) | `admin` e `tecnico` podem cadastrar: mantida e ampliada para edição; exclusão de laboratório apenas `admin`. |
| RN04 (V2) | Apenas `admin` lê auditoria: mantida. |
| RN05 (V2) | Usuário inativo não autentica e tokens existentes deixam de ter acesso: implementado. |
| RN06 (V2) | ViaCEP não interfere no núcleo: será mantida quando integrada. |
| RN07 (V2) | IIE é indicador interno, **não qualidade educacional**: mantida; sem valor até definir metodologia. |
| RN08 (V2) | Não coletar dados sensíveis de alunos para associação acadêmica: mantida como objetivo. |
| Nova proposta | Não apagar computadores automaticamente com laboratórios; retornar 409 quando houver vínculos. |
| Nova proposta | `sem_coleta` é estado distinto: nunca afirmar equipamento online por simples cadastro. |

## 5. Critérios de qualidade e limitações

- O banco é criado **vazio** por migração; somente criação explícita e protegida do administrador insere o primeiro usuário.
- Status de coleta e métricas ainda não são escritos por API nesta etapa. Antes de implantar o agente, o painel mostra `sem_coleta` e IIE não calculado.
- Não há métricas históricas, gráfico de série temporal, notificações externas, alertas persistidos nem diagnóstico de adequação acadêmica nesta entrega; estes elementos serão adicionados por incrementos testáveis.
- SQLite é alternativa **explícita** para desenvolvimento local. PostgreSQL (Supabase) será demonstrado após credenciais e migração próprias, sem importar seed antigo.
- `sessionStorage` no frontend contém o token JWT até o fechamento da aba. Antes de produção, revisar estratégias de sessão, CSP, limites de requisição, senha, recuperação de acesso e proteção a ataques web.
- A nova base foi validada com testes pytest; compilação frontend precisa ser efetuada onde `npm install` tenha conexão ao registro NPM.

## 6. Modelo conceitual por incremento

**Incremento 1 (implementado):** `User 1—N AuditLog`; `Laboratory 1—N Computer` com `ondelete=RESTRICT`; números de dashboard calculados por consulta ao banco. Os perfis são atributos de `User`, sem subclasses.

**Incremento 2 (planejado):** `Computer 1—N MetricSample(timestamp,cpu,ram,disk,source)`; `Alert` com severidade, origem e estado de resolução; `MonitoringCredential` associada ao equipamento; job de detecção de ausência de coleta.

**Incremento 3 (planejado):** `EducationalActivity 1—N TechnologyRequirement`; relação atividade ↔ laboratório (agendamento contextual simplificado). Evitar cadastro completo de matrículas, notas ou estudantes.

**IIE:** não definir pesos arbitrários na implementação. Primeiro especificar unidades, janela de observação, completude de dados, hipóteses e método de validação; comparar cenários e negociar metodologia com orientador. Publicar versão e metodologia do cálculo no relatório quando aprovado.
