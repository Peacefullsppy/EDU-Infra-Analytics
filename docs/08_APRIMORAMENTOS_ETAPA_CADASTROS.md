# Revisão da etapa de cadastros — 02/11/2026

## Base documental

Este incremento utiliza o código da entrega da Semana 1 e a monografia UMC `EDU_Infra_Analytics_Projeto_Completo_UMC(1).docx`, principalmente os itens 1.2.2, 2.4, 3.3, 4.5, 5.1 e 5.3. Não modifica o objetivo geral nem incorpora novos módulos à primeira versão.

## O que foi encontrado e por que foi alterado

| Problema observado | Melhoria entregue | Razão prática | Verificação |
|---|---|---|---|
| Um laboratório podia aparecer duas vezes com mesmo nome e localização | Consulta prévia e índice de unicidade no banco; HTTP 409 para repetição em cadastro ou edição | Não aumentar indevidamente os totais do dashboard | `test_laboratorio_nao_duplica...`, `test_duplicidade_com_letras_acentuadas...`, `test_edicao_para_laboratorio_duplicado...` |
| Erros de exclusão de laboratório poderiam escapar se o vínculo fosse criado entre a verificação e a gravação | `IntegrityError` com `rollback` e resposta HTTP 409 | Proteger dados mesmo quando duas ações ocorrem quase ao mesmo tempo | Restrição FK RESTRICT, testes HTTP 409; concorrência simultânea **não simulada** |
| Listagem do laboratório era difícil de consultar por nome ou local | `GET /laboratorios?busca=...&ativo=...` + busca/filtro na tela | Encontrar rapidamente um laboratório ativo ou inativo | `test_busca_laboratorios_por_nome_local_e_ativo` |
| Consulta de computadores não permitia busca direta no backend | `GET /computadores?busca=...&laboratory_id=...` | Localizar um equipamento em laboratório específico | `test_busca_computadores_por_hostname_e_laboratorio`, `test_busca_trata_percentual_como_texto_e_nao_coringa` |
| Após falha na atualização de uma consulta, a interface podia manter a resposta anterior | Limpeza de dados antigos antes de carregar nova resposta | Evitar que o usuário confunda resultados antigos com a situação atual | Análise estática da tela; **teste no navegador pendente** |
| O cadastro duplicado poderia registrar ação bem-sucedida indevidamente | Tratamento do conflito antes do registro de sucesso; rollback para conflito do banco | Histórico de auditoria coerente com ações concluídas | Testes de rejeição e auditoria |

## Regras que permanecem

- Só o administrador exclui laboratórios; laboratório com computador vinculado retorna **409**, preservando ambos.
- O técnico pode cadastrar/editar computadores e laboratórios; gestor apenas consulta dados.
- O primeiro administrador é criado manualmente; sem laboratórios, computadores, senhas ou métricas de demonstração.
- O IIE continua `null` até a metodologia estar aprovada. O agente psutil e as medições permanecem para as próximas etapas.

## Migração 0002: cuidado ao atualizar um banco já usado

A migração `0002_unique_labs` cria o índice `uq_laboratories_name_location_ci` sobre nome e localização. Em um banco **já populado**, cadastros repetidos impedem a criação desse índice. Antes de atualizar, faça backup e confira duplicidades com `python -m scripts.check_duplicate_labs`. O script só consulta: não apaga nem altera registros. Se encontrar duplicatas, decida manualmente qual cadastro deve permanecer e transfira os computadores antes de excluir o registro repetido. Depois execute:

```powershell
cd backend
python -m alembic upgrade head
python -m pytest -q
```

A validação automática da unicidade ocorre no backend e utiliza comparação sem diferenciar maiúsculas e minúsculas. Há ainda um índice no banco para reduzir o risco de duplicidades em gravações simultâneas; o comportamento exato com caracteres acentuados em operações concorrentes depende do banco utilizado.

## Evidências desta revisão

- **28 testes pytest aprovados**, incluindo nove novos cenários de consulta, integridade e auditoria.
- Migrações `0001_empty` e `0002_unique_labs` aplicadas em **SQLite temporário**, criando a estrutura sem registros de laboratórios ou computadores.
- Sintaxe JSX analisada sem erro; `npm run build` **não executado** porque `npm install --offline` não encontrou `@vitejs/plugin-react` no cache.
- PostgreSQL/Supabase, testes em navegador e máquinas virtuais **ainda não validados**.

## Relação com a monografia

Este incremento reforça o cadastro previsto na primeira prioridade da seção 5.1, os cuidados com a persistência descritos na seção 3.3 e os testes indicados na seção 4.5. A justificativa e as limitações aparecem também na nova seção 5.5 da monografia atualizada. Não se pode concluir, apenas com esses resultados, que a infraestrutura foi monitorada ou que o IIE já foi validado.

### Conferência adicional de migração com registro anterior

Também foi executada uma passagem de `0001_empty` para `0002_unique_labs` em SQLite com **um laboratório criado apenas para o teste**. Depois da atualização, o mesmo laboratório continuou presente, com ID, nome e localização preservados (`evidencias/migracao_preserva_registro_existente.txt`). Isso confirma esse cenário de migração, mas não substitui a execução no PostgreSQL da instituição.
