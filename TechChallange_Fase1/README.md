# Tech Challenge Fase 1 - Case NPS Preditivo

Este projeto faz parte da Pós-Graduação em AI Scientist da FIAP e tem como objetivo analisar e prever a satisfação de clientes de um e-commerce através do Net Promoter Score (NPS).

## Objetivo do Projeto

Desenvolver uma análise exploratória e preditiva para compreender os fatores que influenciam a satisfação do cliente em um e-commerce, permitindo à empresa atuar de forma proativa na melhoria da experiência do cliente antes mesmo da aplicação da pesquisa de NPS.

## Contexto do Negócio

Com o crescimento acelerado do e-commerce nacional, a empresa passou a lidar com um volume cada vez maior de pedidos, entregas e interações com clientes. Esse crescimento trouxe ganhos importantes de escala, mas também revelou desafios relevantes na experiência do cliente, especialmente refletidos na alta variabilidade do Net Promoter Score (NPS) entre diferentes perfis de consumidores.

**Problema de Negócio:** Quais fatores operacionais realmente influenciam a satisfação do cliente e como a empresa pode agir de forma proativa para melhorar a experiência antes mesmo da aplicação da pesquisa de NPS?

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
├── models/                  # Modelos treinados e serializados
├── reports/                 # Relatórios e visualizações
└── README.md               # Este arquivo
```

## Como Reproduzir os Resultados

### Pré-requisitos

- Python 3.8+
- Jupyter Notebook ou JupyterLab
- Bibliotecas necessárias (veja requirements.txt)

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/fbenin/FIAP_POSTECH_AI_SCIENTIST.git
cd FIAP_POSTECH_AI_SCIENTIST/TechChallange_Fase1
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute os notebooks na seguinte ordem:
   - `01_entendimento_negocio.ipynb` - Análise conceitual do problema
   - `02_analise_exploratoria.ipynb` - EDA e insights
   - `03_modelagem_preditiva.ipynb` - Construção do modelo (opcional)

## Principais Insights

[A ser preenchido após a análise exploratória]

## Recomendações para o Negócio

[A ser preenchido após a análise]

## Limitações e Próximos Passos

[A ser preenchido durante o desenvolvimento]

## Autores

Equipe Tech Challenge - FIAP Pós-Graduação AI Scientist

## Licença

Este projeto é desenvolvido para fins acadêmicos como parte do programa de Pós-Graduação da FIAP.