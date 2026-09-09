# EDU-Infra Analytics

Sistema para diagnóstico e monitoramento da infraestrutura tecnológica de ambientes educacionais.

##  Descrição do projeto

O **EDU-Infra Analytics** é uma plataforma desenvolvida como Projeto Final de Curso em Engenharia de Software, com foco no acompanhamento da infraestrutura tecnológica de instituições de ensino.

A proposta do sistema é centralizar informações sobre laboratórios e computadores, coletar métricas de desempenho e disponibilidade dos equipamentos e apresentar esses dados em dashboards, indicadores, alertas e relatórios.

A plataforma busca auxiliar equipes de TI e gestores na identificação de problemas relacionados à infraestrutura tecnológica, contribuindo para uma manutenção mais organizada e para uma melhor tomada de decisão.

## Objetivo

Desenvolver uma plataforma capaz de **monitorar, organizar e analisar a infraestrutura tecnológica de ambientes educacionais**, permitindo o acompanhamento de laboratórios e computadores e fornecendo indicadores que apoiem equipes de TI e gestores.

### Objetivos específicos

- Cadastrar e gerenciar laboratórios.
- Cadastrar e gerenciar computadores.
- Coletar informações de CPU, memória RAM, armazenamento e disponibilidade.
- Registrar o histórico das métricas coletadas.
- Exibir os dados em um dashboard.
- Criar alertas relacionados ao estado dos equipamentos.
- Desenvolver indicadores para avaliação da infraestrutura.
- Implementar o Índice de Infraestrutura Educacional (IIE).
- Gerar relatórios para acompanhamento da infraestrutura.
- Validar a solução em um ambiente educacional simulado.

## 🛠️ Tecnologias previstas

### Frontend

- React
- JavaScript
- HTML
- CSS
- Vite
- ESLint

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Banco de dados

- PostgreSQL

### Monitoramento

- Python
- psutil

### Testes

- Pytest
- Postman

### Infraestrutura

- Hyper-V
- Windows Server

### Versionamento e gerenciamento

- Git
- GitHub
- GitHub Projects

### Prototipação e documentação

- Figma
- Excalidraw

## ✅ Checklist do projeto

### 1. Planejamento e documentação

- [x] Definir o tema do projeto
- [x] Definir o problema
- [x] Definir o objetivo geral
- [x] Definir os objetivos específicos
- [x] Definir o escopo inicial
- [x] Definir as tecnologias do projeto
- [x] Criar a arquitetura inicial do sistema
- [x] Criar protótipos iniciais no Figma
- [ ] Finalizar requisitos funcionais
- [ ] Finalizar requisitos não funcionais
- [ ] Criar histórias de usuário
- [ ] Definir critérios de aceitação
- [ ] Criar diagrama de casos de uso
- [ ] Criar diagrama de classes
- [ ] Criar o DER do banco de dados

### 2. Estrutura do projeto

- [x] Criar repositório no GitHub
- [x] Criar estrutura inicial do frontend
- [x] Criar estrutura inicial do backend
- [x] Configurar `.gitignore`
- [ ] Criar estrutura do agente de monitoramento
- [ ] Criar estrutura de testes
- [ ] Criar estrutura de documentação
- [ ] Configurar GitHub Projects

### 3. Backend

- [ ] Configurar FastAPI
- [ ] Configurar conexão com PostgreSQL
- [ ] Configurar SQLAlchemy
- [ ] Configurar Alembic
- [ ] Criar modelo de usuários
- [ ] Criar modelo de laboratórios
- [ ] Criar modelo de computadores
- [ ] Criar modelo de métricas
- [ ] Criar modelo de alertas
- [ ] Criar autenticação com JWT
- [ ] Implementar controle de acesso por perfil
- [ ] Criar API de laboratórios
- [ ] Criar API de computadores
- [ ] Criar API de métricas
- [ ] Criar API de alertas
- [ ] Criar API de indicadores
- [ ] Criar API de relatórios

### 4. Frontend

- [ ] Criar layout principal
- [ ] Criar tela de login
- [ ] Criar dashboard
- [ ] Criar tela de laboratórios
- [ ] Criar tela de computadores
- [ ] Criar tela de detalhes do computador
- [ ] Criar tela de indicadores
- [ ] Criar tela de relatórios
- [ ] Integrar frontend com a API
- [ ] Implementar tratamento de erros
- [ ] Implementar estados de carregamento

### 5. Agente de monitoramento

- [ ] Criar agente em Python
- [ ] Coletar uso de CPU
- [ ] Coletar uso de memória RAM
- [ ] Coletar uso de armazenamento
- [ ] Coletar disponibilidade do equipamento
- [ ] Coletar hostname
- [ ] Coletar endereço IP
- [ ] Enviar métricas para a API
- [ ] Criar tratamento de falhas de comunicação
- [ ] Testar agente em ambiente virtualizado

### 6. Indicadores e relatórios

- [ ] Definir regras do Índice de Infraestrutura Educacional (IIE)
- [ ] Implementar cálculo do IIE
- [ ] Exibir o IIE no dashboard
- [ ] Criar histórico de indicadores
- [ ] Criar relatórios de infraestrutura
- [ ] Criar alertas visuais no dashboard

### 7. Testes

- [ ] Criar testes unitários com Pytest
- [ ] Testar endpoints com Postman
- [ ] Testar autenticação
- [ ] Testar integração com PostgreSQL
- [ ] Testar integração entre frontend e backend
- [ ] Testar coleta do agente
- [ ] Testar geração de indicadores
- [ ] Realizar testes funcionais

### 8. Ambiente de validação

- [ ] Configurar Hyper-V
- [ ] Criar máquinas virtuais
- [ ] Configurar Windows Server
- [ ] Preparar ambiente educacional simulado
- [ ] Instalar agente nos computadores simulados
- [ ] Validar coleta e envio das métricas

### 9. Finalização

- [ ] Revisar código
- [ ] Revisar segurança
- [ ] Revisar documentação
- [ ] Registrar evidências com screenshots
- [ ] Atualizar diagramas
- [ ] Atualizar README
- [ ] Finalizar documentação acadêmica
- [ ] Preparar apresentação do projeto
- [ ] Finalizar versão MVP

##  Arquitetura resumida

```text
Computadores dos laboratórios
            ↓
     Agente Python
         (psutil)
            ↓
           JSON
            ↓
       FastAPI / API
            ↓
       PostgreSQL
            ↓
     React / Dashboard
            ↓
 Equipe de TI / Gestores
```

##  Funcionalidades previstas

- Gerenciamento de laboratórios
- Gerenciamento de computadores
- Monitoramento de recursos
- Histórico de métricas
- Dashboard
- Alertas
- Indicadores
- Índice de Infraestrutura Educacional
- Relatórios
- Autenticação e controle de acesso

##  Status do projeto

> Em desenvolvimento.

O projeto encontra-se na etapa de estruturação e implementação inicial do frontend, backend e ambiente de desenvolvimento.

## Projeto acadêmico

Projeto desenvolvido como parte do **Projeto Final de Curso em Engenharia de Software**.

**Projeto:** EDU-Infra Analytics  
**Curso:** Bacharelado em Engenharia de Software  
**Instituição:** Universidade de Mogi das Cruzes (UMC)

---

> Este README será atualizado conforme o desenvolvimento do projeto avançar.
