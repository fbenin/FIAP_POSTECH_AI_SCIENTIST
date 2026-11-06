# Dados

## Dataset

Este projeto utiliza o **Brazilian E-Commerce Public Dataset by Olist**, disponível no Kaggle. O dataset contém aproximadamente 115 mil avaliações de clientes sobre pedidos de e-commerce.

## Download

1. Acesse [Kaggle - Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Faça o download do arquivo `olist_order_reviews_dataset.csv`
3. Crie a pasta `data/raw/` se ela não existir
4. Coloque o arquivo CSV em `data/raw/olist_order_reviews_dataset.csv`

```bash
mkdir -p data/raw/
# Coloque o arquivo CSV aqui
```

## Colunas Esperadas

O arquivo `olist_order_reviews_dataset.csv` deve conter as seguintes colunas:

- `review_id`: Identificador único da avaliação
- `order_id`: ID do pedido relacionado
- `review_score`: Pontuação de 1 a 5
- `review_comment_title`: Título do comentário (opcional, pode estar vazio)
- `review_comment_message`: Texto completo da avaliação
- `review_creation_date`: Data e hora de criação da avaliação

## Estrutura Local

- `data/raw/` — Contém o CSV do Kaggle (gitignored)
- `data/chroma_db/` — Índice de vetores gerado pelo builder (gitignored)
