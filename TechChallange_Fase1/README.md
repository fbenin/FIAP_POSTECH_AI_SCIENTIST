# Tech Challenge Fase 1 - Case NPS Preditivo

Este projeto faz parte da Pós-Graduação em AI Scientist da FIAP e tem como objetivo analisar e prever a satisfação de clientes de um e-commerce através do Net Promoter Score (NPS).

## Objetivo do Projeto

Desenvolver uma análise exploratória e preditiva para compreender os fatores que influenciam a satisfação do cliente em um e-commerce, permitindo à empresa atuar de forma proativa na melhoria da experiência do cliente antes mesmo da aplicação da pesquisa de NPS.

## Contexto do Negócio

Com o crescimento acelerado do e-commerce nacional, a empresa passou a lidar com um volume cada vez maior de pedidos, entregas e interações com clientes. Esse crescimento trouxe ganhos importantes de escala, mas também revelou desafios relevantes na experiência do cliente, especialmente refletidos na alta variabilidade do Net Promoter Score (NPS) entre diferentes perfis de consumidores.

**Problema de Negócio:** Quais fatores operacionais realmente influenciam a satisfação do cliente e como a empresa pode agir de forma proativa para melhorar a experiência antes mesmo da aplicação da pesquisa de NPS?

**Por que o NPS é importante para um e-commerce?** Através do NPS é possível identificar a satisfação do cliente e ter análise preditiva relacionada as metas de negócio.
Por exemplo reduzir o índice de churn e aumentar o número de promotores da marca.

**Quais áreas poderiam se beneficiar desses insights? Exemplos: logística, atendimento, pricing, produto etc.** 
Todas as áreas da empresa podem se beneficiar dos Insights do NPS e aumentar a satisfação do cliente. 
A questão é traduzir os dados para as metas de negócio, trazendo insights valiosos para cada área poder tomar decisões.

** Como o NPS impacta:

- Recompra: criando promotores da marca que aumentam a recompra.

- Boca a boca: é um marketing orgânico, promotores satisfeitos com a marca divulgando-a.

- Market share em e-commerce: ajuda a monitorar a experiância da compra, para manter a retenção de clientes.



## Descrição da Base de Dados

A base de dados contém informações históricas de pedidos, entregas e interações com o atendimento ao cliente.

### Dicionário de Dados

| Variável | Descrição |
|----------|-----------|
| `customer_id` | Identificador único do cliente |
| `order_id` | Identificador único do pedido |
| `customer_age` | Idade do cliente |
| `customer_region` | Região geográfica do cliente |
| `customer_tenure_months` | Tempo de relacionamento do cliente com a empresa (em meses) |
| `order_value` | Valor total do pedido |
| `items_quantity` | Quantidade de itens no pedido |
| `discount_value` | Valor de desconto aplicado ao pedido |
| `payment_installments` | Número de parcelas do pagamento |
| `delivery_time_days` | Tempo total de entrega (em dias) |
| `delivery_delay_days` | Quantidade de dias de atraso na entrega |
| `freight_value` | Valor do frete |
| `delivery_attempts` | Número de tentativas de entrega |
| `customer_service_contacts` | Número de contatos do cliente com o atendimento |
| `resolution_time_days` | Tempo para resolução de problemas (em dias) |
| `complaints_count` | Número de reclamações registradas pelo cliente |
| `repeat_purchase_30d` | Indica se houve recompra em até 30 dias após o pedido (0 = não, 1 = sim) |
| `csat_internal_score` | Score interno de satisfação do cliente |
| `nps_score` | Nota de satisfação do cliente (NPS), variando de 0 a 10, coletada após a experiência de compra |

## Metodologia Utilizada

O projeto está estruturado nas seguintes etapas:

1. **Entendimento do Negócio**
   - Análise do problema de negócio
   - Importância do NPS para e-commerce
   - Identificação de áreas beneficiadas pelos insights
   - Reflexão sobre impactos em recompra, boca a boca e market share

2. **Definição da Target**
   - Identificação da variável alvo (NPS)
   - Justificativa da escolha
   - Momento de coleta na jornada do cliente
   - Riscos associados ao uso da variável

3. **Análise Exploratória dos Dados (EDA)**
   - Identificação de fatores críticos para a satisfação
   - Análise de geradores de detratores
   - Identificação de pontos de ruptura na experiência
   - Perfis de clientes com NPS alto/baixo

4. **Modelagem Preditiva (Opcional)**
   - Definição da variável alvo
   - Seleção e preparação de features
   - Estratégia de separação dos dados
   - Escolha e treinamento do modelo
   - Avaliação de resultados
   - Aplicação prática na empresa

## Estrutura do Projeto

```
TechChallange_Fase1/
├── data/                    # Dados brutos e processados
│   └── desafio_nps_fase_1.csv
├── notebooks/               # Jupyter notebooks para análise e experimentação
├── models/                  # Pasta reservada para modelos futuros
├── reports/                 # Relatórios e visualizações
└── README.md               # Este arquivo
```

## Como Reproduzir os Resultados

### Instalação das Dependências

1. Instale as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### Execução

2. Execute o notebook principal:
   - `tech_challenge_fase1_analysis.ipynb` - Análise completa do projeto

O notebook está organizado nas seguintes seções:
1. **Entendimento do Negócio** - Contextualização do problema e importância do NPS
2. **Definição da Target** - Justificativa da escolha do NPS e riscos associados
3. **Análise Exploratória (EDA)** - Análise detalhada dos dados com visualizações
4. **Modelagem Preditiva** - Regressão Linear Múltipla para previsão do NPS Score (opcional)
5. **Conclusões e Recomendações** - Insights e próximos passos

## Autores

- Fernanda Benin
- Luccas Marques
- Diego Santin
- Henrique Toriello
- Nicolas Stumpf

**Equipe Tech Challenge - FIAP Pós-Graduação AI Scientist**
