# Resultados de testes — EDU-Infra Analytics 1.6

**Data da execução:** 08/11/2026 (ambiente de avaliação Linux/Python 3.13.5).

## Execução local confirmada

| Resultado | Contagem |
|---|---:|
| Casos coletados pelo Pytest | 377 |
| Aprovados | **361** |
| Falharam | **0** |
| Ignorados por ambiente/opt-in | **16** |
| Cobertura agregada de instruções do backend (`app/`) | **95%** |

Distribuição dos **361 aprovados**: 189 cenários novos de unidade, 109 de integração isolada, 9 jornadas completas pela API e 54 testes da suíte original. Foram ignorados 9 testes de navegador e 7 testes que exigem PostgreSQL real descartável. Os cenários ignorados **não foram aprovados nem executados**.

Execução utilizada:

```powershell
cd backend
python -m pytest -q --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --junitxml=pytest-results.xml
```

## Cobertura por módulo

| Módulo | Cobertura |
|---|---:|
| `app/cli.py` | 79% |
| `app/core.py` | 92% |
| `app/main.py` | 75% |
| `app/models.py` | 100% |
| `app/routes.py` | 95% |
| `app/schemas.py` | 99% |
| `app/services.py` | 99% |
| **Total** | **95%** |

Os arquivos `reports/pytest-results.xml`, `reports/coverage.xml` e `reports/pytest-execucao.log` permitem conferir os resultados. O Pytest também apresentou três avisos não impeditivos; consulte o log e revise se os componentes forem atualizados.

## Etapas dependentes de serviços externos

- **PostgreSQL real:** 7 cenários opt-in possuem testes de chave estrangeira, unicidade e fluxo com migrações; foram ignorados na execução local porque não havia instância PostgreSQL descartável configurada.
- **Navegador React:** 9 cenários Playwright foram incluídos, mas foram ignorados sem frontend/backend ativos em ambiente E2E isolado.
- **Frontend Vitest:** testes de contrato HTTP, eventos de sessão, formatação e gráficos foram adicionados a `frontend/tests/`; sua execução e o build Vite ainda dependem da instalação das bibliotecas npm, indisponível neste ambiente de avaliação.

A CI em `.github/workflows/ci.yml` configura esses ambientes para validar os cenários restantes e arquivar relatórios. **A configuração da CI não equivale a uma execução bem-sucedida no GitHub Actions; consulte as execuções reais após publicar o repositório.**

## Melhorias de qualidade implementadas

A validação de campos obrigatórios foi reforçada para impedir nomes, hostnames, títulos e identificadores contendo apenas espaços em branco. Esses casos foram incluídos na suíte de regressão tanto no nível de schema quanto no HTTP da API.

**Limites:** os testes de integração isolada usam SQLite em memória, enquanto o ambiente institucional destina-se ao PostgreSQL. Testes automatizados e cobertura alta não substituem auditoria de segurança, carga, testes no Hyper-V/Windows e revisão LGPD antes de produção.
