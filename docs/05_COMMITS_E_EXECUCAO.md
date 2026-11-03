# Evidências de versionamento e execução

## Proveniência e limites

Esta entrega é derivada do arquivo ZIP V0.1 enviado nesta conversa e da monografia UMC anexada. O histórico Git incluído no artefato será **gerado localmente nesta rodada de entrega** para documentar importação e alterações executadas. Ele **não substitui o histórico real anterior** de repositórios pessoais nem constitui publicação automática no GitHub. Não foram utilizados logins, tokens GitHub nem credenciais de Supabase do usuário.

## Evidências geradas

- `backend/tests/test_mvp.py`: sete casos preexistentes no ZIP de entrada.
- `backend/tests/test_entrega_semana1.py`: 12 casos adicionais nesta entrega.
- `evidencias/resultado_evidencias.json`: JSON gerado a partir de Alembic + API + SQL reais, em SQLite temporário.
- `evidencias/01_banco_vazio.png`: saída visual da consulta SQL com quatro tabelas zeradas.
- `evidencias/02_cadastros_reais.png`: POST 201 laboratório e computador, contagens SQL e dashboard.
- `evidencias/03_conflito_http_409.png`: HTTP 409 e GETs provando preservação do vínculo.
- `evidencias/*.html`: mesma evidência em HTML, legível no navegador.

## Histórico local de commits

Preencher a partir da saída efetiva de `git log --oneline` que acompanha esta entrega no arquivo `evidencias/git_log_local.txt`. Para reproduzir esse histórico, importe o arquivo `EDU_Infra_Analytics_Git_Historico.bundle` em repositório Git local. **Não atribuir os commits locais ao GitHub antes do push.**

```powershell
git clone EDU_Infra_Analytics_Git_Historico.bundle edu-infra-historico
cd edu-infra-historico
git log --oneline --all
```

Depois de revisar e configurar o seu próprio repositório GitHub:

```powershell
git remote add origin URL_DO_SEU_REPOSITORIO
git branch -M main
git push -u origin main
```

**Não execute `git push --force`** para substituir histórico remoto preexistente. Se já existir uma `main` com trabalho próprio, prefira criar uma branch de entrega e abrir PR em vez de sobrescrever o repositório.

## Registros de testes

O log de testes encontra-se em `evidencias/pytest_19_testes.txt`. A ordem e contagem podem variar se você adicionar casos ao evoluir o projeto. O fluxo efetivo para esta entrega foi: importar ZIP → corrigir lógica/CLI → ampliar testes → migrar SQLite temporário → cadastrar dados por API → registrar SQL → gerar capturas → confirmar 409 → produzir documentação → criar commits locais.
