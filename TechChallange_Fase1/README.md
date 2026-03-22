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
| `customer_region` | Região geogr
áfica do cliente |
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
4. **Modelagem Preditiva** - Construção e avaliação de modelos de classificação (opcional)
5. **Conclusões e Recomendações** - Insights e próximos passos

## Principais Insights

### Fatores Críticos Identificados:
- **Atraso na entrega** é o principal driver de insatisfação
- **Múltiplos contatos com atendimento** indicam problemas sérios na experiência
- **Reclamações** têm impacto devastador no NPS

### Análise de Detratores vs Promotores:
- Detratores têm em média **mais dias de atraso** nas entregas
- Promotores recompram até **5x mais** que detratores
- Existe um threshold claro de atraso que degrada drasticamente o NPS

### Variação Regional:
- Diferentes regiões apresentam variações significativas no NPS
- Sugere necessidade de ajustes logísticos específicos por região

## Recomendações para o Negócio

### Para Logística:
- Investir em rastreamento preciso e comunicação proativa
- Criar SLAs diferenciados por região
- Reduzir tentativas de entrega através de melhor planejamento

### Para Atendimento:
- Implementar sistema de alerta de clientes em risco
- Treinamento focado em resolução no primeiro contato
- Priorizar casos com múltiplas reclamações

### Para Produto/Marketing:
- Segmentar comunicações por perfil de NPS previsto
- Criar programas de fidelidade para promotores
- Ações de recuperação direcionadas para detratores

### Modelo Preditivo:
- Implementar pipeline de predição para ação proativa
- Sistema de alertas para clientes com alto risco de insatisfação
- Priorização inteligente de atendimento baseada em predição

## Limitações e Próximos Passos

### Limitações:
- NPS é uma métrica retrospectiva - coletada após a jornada completa
- Possível viés de resposta (clientes extremos tendem a responder mais)
- Correlação não implica causalidade - necessário validar insights com testes

### Próximos Passos:
1. Validar modelo preditivo com dados mais recentes
2. Implementar pipeline de predição em produção
3. Realizar testes A/B para validar intervenções propostas
4. Expandir análise com dados de comentários (NLP)
5. Monitorar ROI das ações preventivas implementadas

## Autores

- Fernanda Benin
- Luccas Marques
- Diego Santin
- Henrique Toriello
- Nicolas Stumpf

**Equipe Tech Challenge - FIAP Pós-Graduação AI Scientist**
