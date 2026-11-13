# Dados

## Dataset

Este projeto utiliza o **Brazilian E-Commerce Public Dataset by Olist**, disponível no Kaggle.
O dataset contém aproximadamente 115 mil avaliações de clientes sobre pedidos de e-commerce
realizados entre 2016 e 2018.

## Download

1. Acesse [Kaggle — Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Baixe o arquivo ZIP e extraia em `data/raw/`

```bash
mkdir -p data/raw/
# Coloque os arquivos CSV aqui
```

## Arquivo obrigatório

| Arquivo | Uso |
|---------|-----|
| `olist_order_reviews_dataset.csv` | Textos e notas das avaliações — base do índice vetorial |

## Arquivos opcionais (enriquecimento de metadados)

Quando presentes em `data/raw/`, o `load_reviews()` os utiliza automaticamente
para enriquecer cada avaliação com categoria de produto e prazo de entrega.
Esses metadados são armazenados no ChromaDB e aparecerão nas respostas da API.

| Arquivo | Metadados adicionados |
|---------|----------------------|
| `olist_orders_dataset.csv` | `purchase_year`, `purchase_month`, `delivery_delta_days` |
| `olist_order_items_dataset.csv` | Ponte entre pedidos e produtos |
| `olist_products_dataset.csv` | Categoria do produto em português |
| `product_category_name_translation.csv` | Categoria do produto em inglês |

`delivery_delta_days` é calculado como `order_delivered_customer_date - order_estimated_delivery_date`:
valores negativos indicam entrega antes do prazo, positivos indicam atraso.

## Estrutura local

```
data/
├── raw/                     # CSVs do Kaggle (gitignored)
│   ├── olist_order_reviews_dataset.csv        (obrigatório)
│   ├── olist_orders_dataset.csv               (opcional)
│   ├── olist_order_items_dataset.csv          (opcional)
│   ├── olist_products_dataset.csv             (opcional)
│   └── product_category_name_translation.csv  (opcional)
└── chroma_db/               # Índice vetorial gerado (gitignored)
```
