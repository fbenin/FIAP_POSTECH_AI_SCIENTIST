# Tech Challenge – Fase 2
## Pipeline Híbrido para Análise da Alfabetização no Brasil

**FIAP PosTech – Inteligência Artificial para Cientistas**

---

## Contexto do Problema

A alfabetização na infância é um dos pilares fundamentais para o desenvolvimento educacional, social e econômico do Brasil. O **Compromisso Nacional Criança Alfabetizada** mobiliza União, estados e municípios com o objetivo de garantir que todas as crianças brasileiras estejam alfabetizadas até o final do 2º ano do ensino fundamental.

O Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP) realizou em 2023 a **Pesquisa Alfabetiza Brasil**, que definiu o ponto de corte de **743 pontos na escala de proficiência do Saeb** como critério de alfabetização. A partir disso, foi criado o **Indicador Criança Alfabetizada**, que expressa o percentual de estudantes que atingem esse patamar.

A meta nacional é que, até **2030**, todas as crianças brasileiras estejam alfabetizadas ao final do 2º ano do ensino fundamental.

---

## O Desafio

Construir uma **pipeline híbrida de dados (Batch + Streaming)** capaz de integrar diferentes fontes relacionadas ao indicador de alfabetização, garantindo qualidade, escalabilidade e eficiência de custos em ambiente de nuvem.

**Fonte de dados principal:** [Indicador Criança Alfabetizada – Base dos Dados](https://basedosdados.org)

---

## Arquitetura da Solução

A pipeline segue a **Arquitetura Medalhão** com três camadas:

| Camada | Descrição |
|--------|-----------|
| **Bronze** | Dados brutos ingeridos das fontes, sem transformações |
| **Silver** | Dados tratados: limpeza, padronização, integração entre bases |
| **Gold** | Camada analítica pronta para dashboards, análises e ML |

> Diagrama da arquitetura: `docs/architecture/`

---

## Estrutura do Repositório

```
├── pipeline/
│   ├── batch/          # Ingestão periódica de dados históricos
│   │   ├── extract/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   ├── streaming/      # Simulação de eventos em tempo quase real
│   │   ├── producer/
│   │   └── consumer/
│   └── orchestration/  # Orquestração dos pipelines
├── quality/            # Regras e checks de qualidade de dados
├── infra/terraform/    # Infraestrutura como código (IaC)
├── monitoring/         # Alertas e dashboards de observabilidade
├── notebooks/          # Análises exploratórias
└── docs/               # Documentação técnica, arquitetura e FinOps
```

---

## Tecnologias Utilizadas

> _A ser preenchido conforme decisões do time_

---

## Decisões Arquiteturais

> _A ser preenchido: trade-offs de Batch vs Streaming, Data Lake vs Data Warehouse, Custo vs Performance_

---

## Monitoramento e FinOps

> _A ser preenchido: estratégia de observabilidade e controle de custos_

---

## Aplicação em IA

> _A ser preenchido: como a camada Gold será usada para modelos preditivos e análise de desigualdade educacional_

---

## Equipe

> _A ser preenchido_
