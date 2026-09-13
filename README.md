


EDU-Infra Analytics
Plataforma para diagnóstico, monitoramento e acompanhamento da infraestrutura tecnológica de ambientes educacionais.

Sobre o projeto
O EDU-Infra Analytics é um projeto acadêmico desenvolvido no curso de Engenharia de Software com o objetivo de auxiliar equipes de TI e gestores escolares no acompanhamento da infraestrutura tecnológica de laboratórios de informática.

A proposta é centralizar informações sobre laboratórios e computadores, permitindo visualizar a situação dos equipamentos, acompanhar métricas de desempenho, identificar problemas e futuramente gerar indicadores e relatórios que apoiem a tomada de decisão.

O projeto está sendo desenvolvido de forma incremental, começando pelas funcionalidades essenciais do MVP.

Objetivo
Desenvolver uma plataforma capaz de organizar, monitorar e analisar a infraestrutura tecnológica de ambientes educacionais, facilitando a identificação de problemas em laboratórios e computadores.

Objetivos específicos
Cadastrar e gerenciar laboratórios.

Cadastrar e gerenciar computadores.

Relacionar computadores aos laboratórios cadastrados.

Coletar informações de CPU, memória RAM, armazenamento e disponibilidade.

Exibir informações em dashboards.

Criar alertas para equipamentos com problemas.

Criar indicadores de infraestrutura.

Desenvolver o Índice de Infraestrutura Educacional (IIE).

Gerar relatórios para acompanhamento da infraestrutura.

Validar o sistema em um ambiente educacional simulado.

Regra de negócio implementada
RN01 — Vínculo entre computador e laboratório
Todo computador cadastrado deve estar vinculado a um laboratório previamente cadastrado no sistema.

O cadastro deve ser recusado quando o laboratorio_id informado não corresponder a um laboratório existente.

Fluxo simplificado:

Cadastro de computador
        |
        v
Recebe laboratorio_id
        |
        v
Laboratório existe?
     /       \
   Sim       Não
    |         |
    v         v
Cadastrar   Recusar cadastro
Tecnologias
Frontend
React

JavaScript

HTML

CSS

Vite

ESLint

Backend
Python

FastAPI

Pydantic

Banco de dados
Planejado para as próximas etapas:

PostgreSQL

SQLAlchemy

Alembic

Monitoramento
Planejado:

Python

psutil

Testes
Swagger / OpenAPI do FastAPI

Postman

Pytest

Infraestrutura
Hyper-V

Windows Server

Versionamento
Git

GitHub

GitHub Projects

Prototipação e documentação
Figma

Excalidraw

Estrutura do projeto
EDU-Infra-Analytics/
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |   `-- database.py
|   |
|   |-- tests/
|   `-- requirements.txt
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- assets/
|   |   |-- components/
|   |   |-- pages/
|   |   |-- services/
|   |   |-- App.jsx
|   |   `-- main.jsx
|   |
|   |-- package.json
|   `-- vite.config.js
|
|-- docs/
|-- infrastructure/
|-- .gitignore
`-- README.md
Funcionalidades atuais
Visualização da área de Laboratórios.

Cards com resumo dos laboratórios e equipamentos.

Listagem dos laboratórios.

Cadastro básico de laboratórios.

Listagem de computadores.

Cadastro básico de computadores.

Validação da RN01.

Comunicação entre frontend React e backend FastAPI.

Nesta fase inicial, parte dos dados ainda pode estar armazenada temporariamente em memória. A persistência com PostgreSQL será adicionada posteriormente.

Como executar o projeto
1. Backend
Entre na pasta:

cd backend
Crie o ambiente virtual, caso ainda não exista:

python -m venv .venv
Ative o ambiente virtual no PowerShell:

.\.venv\Scripts\Activate.ps1
Instale as dependências:

pip install -r requirements.txt
Execute a API:

uvicorn app.main:app --reload
A API ficará disponível em:

http://127.0.0.1:8000
Documentação automática:

http://127.0.0.1:8000/docs
2. Frontend
Em outro terminal:

cd frontend
Instale as dependências:

npm install
Execute o projeto:

npm run dev
O endereço normalmente será:

http://localhost:5173
Checklist
Planejamento e documentação
Definir tema do projeto

Definir problema

Definir objetivo geral

Definir objetivos específicos

Definir escopo inicial

Definir tecnologias

Criar arquitetura inicial

Criar protótipos no Figma

Finalizar requisitos funcionais

Finalizar requisitos não funcionais

Criar histórias de usuário

Criar critérios de aceitação

Criar DER

Criar diagramas UML necessários

Estrutura e versionamento
Criar repositório Git

Configurar GitHub

Criar estrutura do backend

Criar estrutura do frontend

Configurar .gitignore

Utilizar branches para desenvolvimento

Configurar GitHub Projects

Organizar documentação na pasta docs

Backend
Configurar FastAPI

Criar endpoint inicial da API

Criar cadastro básico de laboratórios

Criar listagem de laboratórios

Criar cadastro básico de computadores

Criar listagem de computadores

Implementar RN01

Configurar PostgreSQL

Configurar SQLAlchemy

Configurar Alembic

Criar persistência de laboratórios

Criar persistência de computadores

Criar validações adicionais

Criar sistema de alertas

Criar endpoints de indicadores

Criar endpoints de relatórios

Frontend
Configurar React com Vite

Criar estrutura inicial do frontend

Criar tela de Laboratórios

Criar tela de Computadores completa

Criar Dashboard completo

Criar tela de Indicadores

Criar tela de Relatórios

Integrar todas as telas com a API

Melhorar responsividade

Criar tratamento visual de erros e carregamento

Monitoramento
Criar agente Python

Coletar CPU

Coletar memória RAM

Coletar armazenamento

Coletar hostname

Coletar endereço IP

Coletar disponibilidade

Enviar métricas para a API

Salvar histórico de métricas

Indicadores
Definir regras do IIE

Implementar cálculo do IIE

Exibir IIE por laboratório

Criar indicadores gerais

Criar alertas de manutenção

Testes
Testar endpoints básicos pelo Swagger

Testar RN01 com laboratório existente

Testar RN01 com laboratório inexistente

Criar testes automatizados com Pytest

Criar coleção no Postman

Testar integração frontend/backend

Testar integração com PostgreSQL

Executar testes funcionais do MVP

Infraestrutura e validação
Configurar Hyper-V

Configurar máquinas virtuais

Preparar Windows Server

Criar ambiente educacional simulado

Instalar agente de monitoramento

Validar coleta de métricas

Entrega final
Revisar código

Revisar documentação

Atualizar README

Registrar evidências

Finalizar MVP

Preparar apresentação

Finalizar documentação acadêmica

Arquitetura prevista
Computadores dos laboratórios
            |
            v
     Agente de monitoramento
        Python + psutil
            |
            v
          JSON
            |
            v
         FastAPI
            |
            v
       PostgreSQL
            |
            v
     React / Dashboard
            |
            v
    Equipe de TI / Gestores
Status
Em desenvolvimento.

Atualmente o projeto está na etapa inicial do MVP, com foco no cadastro e gerenciamento de laboratórios e computadores e na implementação das primeiras regras de negócio.

Projeto acadêmico
Projeto: EDU-Infra Analytics
Curso: Bacharelado em Engenharia de Software
Instituição: Universidade de Mogi das Cruzes — UMC

Este README será atualizado conforme novas funcionalidades forem implementadas.
