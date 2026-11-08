# EDU-Infra Analytics 1.6 — Preparação jurídica e de privacidade

**Base de revisão:** 08/11/2026. **Escopo:** Edu Infra Analytics 1.6; publicação do documento de Termos por migração `20261108lgpd`. A versão contratual `2.1-lgpd` é independente da versão do software.

> Os textos em `TERMOS_E_CONDICOES_V2_1_LGPD.txt` e `AVISO_DE_PRIVACIDADE_V1.txt` são minutas técnicas/acadêmicas, **não uma certificação de conformidade com a LGPD**. A instituição que colocar o sistema em operação deverá validar o conteúdo com seus responsáveis jurídicos, de segurança e de proteção de dados.

## O que foi integrado

- Termos de Uso ampliados: versão `2.1-lgpd`, 26 cláusulas, inseridos em `term_documents` por migração **sem apagar documentos e aceites anteriores**. Uma publicação de nova versão invalida a autorização dos tokens de sessões que aceitaram uma versão anterior.
- Aviso de Privacidade público: `GET /api/public/privacy-notice`. Tela de login, etapa de aceite e interface autenticada permitem consultar o documento.
- O aceite **não é confundido com consentimento LGPD**: a confirmação apenas documenta a concordância com as condições de uso. Uma base legal deve ser definida independentemente para cada operação de tratamento, e consentimento específico, quando exigível, requer mecanismo próprio.
- A confirmação de Termos é solicitada em **cada novo login**. O banco mantém o **primeiro aceite de cada usuário por versão** (`term_acceptances`), não um novo registro de aceite a cada sessão. Login e outras operações possuem auditoria separada.
- Texto de cada seção é exibido com formatação legível, sem interpretar o conteúdo vindo da API como HTML.

## Pontos que exigem preenchimento antes de uso real

| Pendência | O que a instituição precisa decidir / documentar |
|---|---|
| Identificação do controlador | Razão social/nome, CNPJ quando aplicável, endereço e representante ou setor responsável |
| Encarregado/canal | Identidade, contato, hipóteses de designação ou eventual dispensa regulatória, sem inventar nome ou e-mail |
| Bases legais | Fundamentação concreta para cada finalidade e categoria de dado; documentar diferenças entre instituição pública e privada |
| Registro das operações | Categorias, finalidade, origem, acesso, transferências, retenção, medidas de segurança e operadores |
| Retenção | Critérios e temporalidade para contas, métricas, alertas, logs, aceites, relatórios e backups; implementar expurgo quando necessário |
| Prestadores | Identificar banco local/Supabase, nuvem, suporte, Tailscale e outros utilizados de fato; assinar ajustes contratuais |
| Transferência internacional | Identificar países e garantias aplicáveis, se ocorrer, conforme LGPD e ANPD |
| Atendimento ao titular | Instituir canal válido, verificação proporcional de identidade, fluxos e evidências de atendimento |
| Incidentes | Plano de resposta, registro e comunicação ao controlador, ANPD e titulares nos casos exigidos pela regulamentação |
| Crianças e adolescentes | Evitar dados de estudantes sem necessidade; avaliar melhor interesse e requisitos aplicáveis se o escopo mudar |
| Segurança | HTTPS remoto, segredo JWT, RBAC, políticas de contas, backup, atualizações, administração de agentes e avaliação de riscos |
| Qualidade dos dados | Evitar dados pessoais em campos livres, exportações desnecessárias e uso do IIE para avaliações de pessoas |

## O que o código atual faz — e o que não faz automaticamente

**Implementado:** autenticação e autorização, senha com hash, token por computador, auditoria, confirmação versionada de Termos, registros técnicos de equipamentos e relatórios, aviso público, exigência de HTTPS remoto no agente, configurações básicas de limiares de monitoramento.

**Não implementado como fluxo integral e automatizado:** gestão completa de solicitações de titulares, exclusão/anonimização universal programada, cadastro de controlador e encarregado, publicação dinâmica do Aviso de Privacidade pelo admin, registro de consentimentos específicos, inventário formal de operadores, programa de prevenção e comunicação automática de incidentes, transferência internacional contratualmente regularizada. Esses assuntos exigem medidas organizacionais e, conforme o uso, desenvolvimento adicional.

## Como publicar no banco existente

1. Faça backup do PostgreSQL e, caso necessário, do diretório de documentação e configurações locais.
2. Extraia esta versão sem sobrescrever o projeto anterior. Mantenha suas senhas fora do ZIP e copie seus arquivos `.env` locais para os locais apropriados.
3. No terminal da pasta `backend`, com o ambiente virtual ativo e `DATABASE_URL` apontando ao banco correto, execute:

   ```powershell
   python -m alembic upgrade head
   python -m alembic current
   ```

   A revisão esperada é `20261108lgpd (head)`.
4. Reinicie o FastAPI e abra o frontend.
5. Consulte `GET /api/public/terms/current` para conferir versão `2.1-lgpd` e `GET /api/public/privacy-notice` para abrir o aviso.
6. Ao fazer login, confirme que a nova versão exige aceite antes do acesso às funcionalidades.
7. **Antes de operação institucional verdadeira**, revise os textos, substitua os campos `[PREENCHER: ...]`, publique documento adaptado pelo endpoint administrativo `/api/terms/publish` com nova versão e distribua o Aviso de Privacidade institucional atualizado. Não deixe os placeholders em produção.

## Referências legais e orientativas consultadas

- [LGPD — Lei nº 13.709/2018, texto atualizado (Câmara dos Deputados)](https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html)
- [LGPD — edição atualizada até julho de 2026 (Senado Federal)](https://www2.senado.leg.br/jspui/handle/id/962304)
- [ANPD — Perguntas frequentes, bases legais](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes)
- [ANPD — Direitos dos titulares](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados/direito-dos-titulares)
- [ANPD — Definições de controlador, operador e encarregado](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-para-definicoes-dos-agentes-de-tratamento-de-dados-pessoais-e-do-encarregado)
- [ANPD — Comunicação de incidentes e Resolução CD/ANPD nº 15/2024](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis)

O propósito destes documentos é orientar a governança e transparência; a aderência legal depende de práticas efetivas, não apenas de textos na interface.
