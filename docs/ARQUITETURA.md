# Arquitetura — EDU-Infra Analytics 1.6

## Componentes e localização

| Responsabilidade | Localização | Finalidade |
|---|---|---|
| API e segurança HTTP | `backend/app/main.py` | FastAPI, CORS, cabeçalhos, `/health` |
| Configuração e autenticação | `backend/app/core.py` | Banco, Argon2, JWT, controle de acesso, token do agente |
| Persistência | `backend/app/models.py` | Entidades SQLAlchemy e relacionamentos |
| Contratos de entrada/saída | `backend/app/schemas.py` | Validação Pydantic |
| Endpoints | `backend/app/routes.py` | CRUD, autenticação, aceite, coleta, relatórios, Hyper-V |
| Regras técnicas | `backend/app/services.py` | Estados, alertas, IIE e snapshots |
| Migrações | `backend/alembic/` | Alterações de esquema e publicações versionadas de Termos |
| Telas React | `frontend/src/App.jsx` | Login, Termos, dashboard e módulos de gestão |
| Cliente HTTP | `frontend/src/api.js` | JWT de sessão, requisições e exports CSV |
| Componentes visuais | `frontend/src/components/` | Identidade e gráficos SVG |
| CSS | `frontend/src/styles.css` | Responsividade, cores, tabelas e modais |
| Agente | `agent/agent.py` | Leitura de CPU/RAM/disco/uptime e envio de medições |
| Inventário VM | `hyperv/Export-HyperVInventory.ps1` | Consulta as VMs via `Get-VM` |
| Publicação inventário | `hyperv/Sync-HyperVInventory.ps1` | Envia inventário à API autenticada |
| CI | `.github/workflows/ci.yml` | Migração, testes, cobertura, build e E2E |

## Caminhos de dados

1. **Login:** React → `POST /api/auth/login` → Argon2/JWT → `GET /api/terms/current` → `POST /api/terms/accept` → acesso ao painel. O aceite é obrigatório por sessão.
2. **Laboratórios:** React → `POST/GET/PUT/DELETE /api/laboratories` → schemas e RBAC → SQLAlchemy → PostgreSQL.
3. **Monitoramento:** psutil na máquina monitorada → `POST /api/agent/metrics` com token próprio → validação e persistência → alertas e snapshots → consultas do dashboard.
4. **Hyper-V:** PowerShell no host exporta dados de inventário → `POST /api/hyperv/import`. O inventário não coleta diretamente a utilização do SO convidado; cada VM exige agente próprio.
5. **Relatórios:** backend monta CSV a partir de registros persistidos e neutraliza campos que poderiam ser interpretados como fórmulas em planilhas.

## Segurança e limitações

Usuários com perfis `ADMIN`, `TECNICO` e `GESTOR` têm permissões distintas verificadas na API. Senhas usam hash Argon2, e o agente armazena somente hash HMAC do token emitido. HTTPS deve ser obrigatório para agentes remotos. Auditoria registra operações administrativas. O IIE estima condições técnicas e não estabelece relação causal com indicadores pedagógicos.

Os Termos de Uso possuem seu próprio versionamento jurídico `2.1-lgpd`, distinto da versão **1.6** do sistema. IDs das migrações são preservados para manter compatibilidade com bancos existentes.
