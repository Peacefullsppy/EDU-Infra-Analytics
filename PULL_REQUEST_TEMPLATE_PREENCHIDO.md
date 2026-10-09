## 1. Identificação
- **Aluno(s):** Matheus D’Eleutério de Castro Lopes - RA 11231103149
- **Projeto (PFC):** EDU-Infra Analytics
- **Branch:** feat/testes-automatizados

## 2. Resumo da entrega
Foram implementados testes automatizados para validações de entrada, regra de vínculo entre computador e laboratório (RN01), autenticação e persistência do EDU-Infra Analytics. A entrega adiciona 13 cenários unitários e 4 cenários de integração, utilizando pytest, mocks, TestClient do FastAPI e banco SQLite em memória isolado para os testes.

## 3. Cenários de testes unitários implementados
| # | Classe testada | Método / regra | Cenário | Tipo | Arquivo de teste | Método de teste |
|---|----------------|----------------|---------|------|------------------|-----------------|
| 1 | ComputadorCreate | validação do cadastro | Dados válidos de computador | Feliz | test_schemas.py | test_deve_aceitar_computador_valido |
| 2 | ComputadorCreate | laboratorio_id > 0 | Laboratório com ID igual a zero | Violação | test_schemas.py | test_deve_rejeitar_laboratorio_id_zero |
| 3 | ComputadorCreate | métricas entre 0 e 100 | CPU, RAM e disco iguais a 0 | Limite | test_schemas.py | test_deve_aceitar_metricas_nos_limites_permitidos[0] |
| 4 | ComputadorCreate | métricas entre 0 e 100 | CPU, RAM e disco iguais a 100 | Limite | test_schemas.py | test_deve_aceitar_metricas_nos_limites_permitidos[100] |
| 5 | ComputadorCreate | CPU <= 100 | CPU igual a 101 | Violação | test_schemas.py | test_deve_rejeitar_cpu_acima_de_cem |
| 6 | LaboratorioCreate | validação do cadastro | Laboratório com dados válidos | Feliz | test_schemas.py | test_deve_aceitar_laboratorio_valido |
| 7 | LaboratorioCreate | nome com mínimo de 2 caracteres | Nome com apenas 1 caractere | Violação | test_schemas.py | test_deve_rejeitar_nome_com_um_caractere |
| 8 | LaboratorioCreate | limites máximos de texto | Nome com 80 e localização com 120 caracteres | Limite | test_schemas.py | test_deve_aceitar_tamanhos_maximos_definidos |
| 9 | LoginRequest | validação de credenciais | E-mail e senha em formato válido | Feliz | test_schemas.py | test_deve_aceitar_email_e_senha_validos |
| 10 | LoginRequest | validação de e-mail | E-mail em formato inválido | Violação | test_schemas.py | test_deve_rejeitar_email_em_formato_invalido |
| 11 | LoginRequest | senha com mínimo de 1 caractere | Senha com exatamente 1 caractere | Limite | test_schemas.py | test_deve_aceitar_senha_com_um_caractere_no_limite_minimo |
| 12 | Regra RN01 / criar_computador | persistência quando laboratório existe | Laboratório existente permite cadastro do computador | Feliz | test_computer_business_rules.py | test_deve_persistir_computador_quando_laboratorio_existe |
| 13 | Regra RN01 / criar_computador | bloquear laboratório inexistente | Laboratório inexistente retorna erro e não persiste | Violação | test_computer_business_rules.py | test_nao_deve_persistir_computador_quando_laboratorio_nao_existe |

Tipo: Feliz | Violação | Limite
**Total de cenários unitários:** 13

## 4. Cenários de testes de integração implementados
| # | Camadas envolvidas | Cenário | Arquivo de teste | Método de teste | Recurso usado |
|---|--------------------|---------|------------------|-----------------|---------------|
| 1 | API + Autenticação + BD | POST /auth/login retorna 200, token e dados do usuário | test_api_integration.py | test_login_valido_retorna_200_token_e_usuario | FastAPI TestClient + SQLite em memória |
| 2 | API + Regra RN01 + BD | POST /computadores retorna 400 quando laboratório não existe | test_api_integration.py | test_post_computadores_retorna_400_quando_laboratorio_nao_existe | FastAPI TestClient + SQLite em memória |
| 3 | SQLAlchemy + BD | Salvar e recuperar laboratório no banco de teste | test_api_integration.py | test_persistencia_salva_e_recupera_laboratorio_no_sqlite | SQLAlchemy + SQLite em memória |
| 4 | API + Autenticação + Regras + BD | Criar laboratório, criar computador vinculado e consultar o recurso | test_api_integration.py | test_fluxo_completo_cria_laboratorio_computador_e_consulta_recurso | FastAPI TestClient + SQLAlchemy + SQLite em memória |

**Total de cenários de integração:** 4

## 5. Arquivos de teste criados ou alterados
| Arquivo (caminho completo) | Criado / Alterado | Qtd. de testes |
|----------------------------|-------------------|----------------|
| backend/tests/unit/test_schemas.py | Criado | 11 |
| backend/tests/unit/test_computer_business_rules.py | Criado | 2 |
| backend/tests/integration/test_api_integration.py | Criado | 4 |

**Total de arquivos de teste:** 3  |  **Total de testes:** 17

## 6. Como executar os testes
```
cd backend
python -m pytest -q
```

## 7. Evidências
- **Resultado da execução:** 17 passed in 1.86s
- **Link do CI (se houver):** não se aplica

## 8. Decisões e dificuldades
- **O que foi mockado e por quê:** Nos testes unitários da RN01 foram mockadas a Session do SQLAlchemy e a função de auditoria. O objetivo foi testar apenas a regra de cadastro do computador e verificar as interações de persistência, sem acessar banco de dados, rede ou outros recursos externos. O cenário de laboratório inexistente também verifica que `add()` e `commit()` não são chamados.
- **Bugs encontrados pelos testes (se houver):** nenhum bug de regra de negócio foi identificado durante a execução dos cenários implementados; não foi necessária alteração do comportamento de produção para fazer os testes passarem.
- **Dificuldades:** A principal adaptação foi aplicar ao projeto Python/FastAPI os conceitos do exercício apresentados originalmente em Java. Para manter os testes de integração independentes do banco de desenvolvimento e do Supabase, foi utilizado SQLite em memória com sobrescrita da dependência `get_db`. Também foi definida uma chave JWT exclusiva no ambiente de teste para que a autenticação pudesse ser exercitada sem depender do arquivo `.env` do desenvolvedor.

## 9. Checklist de entrega
- [x] Todos os testes passam localmente com o comando da seção 6
- [x] Cada cenário listado nas seções 3 e 4 existe no código
- [x] Cada arquivo de teste alterado ou criado está listado na seção 5
- [x] Mínimos do exercício atendidos (10 unitários em 3 classes; 4 de integração)
- [x] Nenhum teste com @Disabled, sem asserção ou com Thread.sleep
- [ ] Professor adicionado como reviewer
