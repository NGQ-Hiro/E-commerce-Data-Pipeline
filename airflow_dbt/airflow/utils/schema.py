from google.cloud import bigquery

# Product Category Name Translation Schema
PRODUCT_CATEGORY_NAME_TRANSLATION_SCHEMA = [
    bigquery.SchemaField("product_category_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("product_category_name_english", "STRING", mode="NULLABLE"),
]

# Geolocation Schema
GEOLOCATION_SCHEMA = [
    bigquery.SchemaField("geolocation_zip_code_prefix", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("geolocation_lat", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("geolocation_lng", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("geolocation_city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("geolocation_state", "STRING", mode="NULLABLE"),
]

# Sellers Schema
SELLERS_SCHEMA = [
    bigquery.SchemaField("seller_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("seller_zip_code_prefix", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("seller_city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("seller_state", "STRING", mode="NULLABLE"),
]

# Customers Schema
CUSTOMERS_SCHEMA = [
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("customer_unique_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("customer_zip_code_prefix", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("customer_city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("customer_state", "STRING", mode="NULLABLE"),
]

# Products Schema
PRODUCTS_SCHEMA = [
    bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("product_category_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("product_name_length", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("product_description_length", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("product_photos_qty", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("product_weight_g", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("product_length_cm", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("product_height_cm", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("product_width_cm", "FLOAT64", mode="NULLABLE"),
]

# Orders Schema
ORDERS_SCHEMA = [
    bigquery.SchemaField("order_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("order_status", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("order_purchase_timestamp", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("order_approved_at", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("order_delivered_carrier_date", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("order_delivered_customer_date", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("order_estimated_delivery_date", "TIMESTAMP", mode="NULLABLE"),
]

# Order Items Schema
ORDER_ITEMS_SCHEMA = [
    bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("order_item_id", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("product_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("seller_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("shipping_limit_date", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("price", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("freight_value", "FLOAT64", mode="NULLABLE"),
]

# Payments Schema
PAYMENTS_SCHEMA = [
    bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("payment_sequential", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("payment_type", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("payment_installments", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("payment_value", "FLOAT64", mode="NULLABLE"),
]

# Order Reviews Schema
ORDER_REVIEWS_SCHEMA = [
    bigquery.SchemaField("review_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("review_score", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("review_comment_title", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("review_comment_message", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("review_creation_date", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("review_answer_timestamp", "TIMESTAMP", mode="NULLABLE"),
]

# Schema Mapping Dictionary
SCHEMAS = {
    "product_category_name_translation": PRODUCT_CATEGORY_NAME_TRANSLATION_SCHEMA,
    "geolocation": GEOLOCATION_SCHEMA,
    "sellers": SELLERS_SCHEMA,
    "customers": CUSTOMERS_SCHEMA,
    "products": PRODUCTS_SCHEMA,
    "orders": ORDERS_SCHEMA,
    "order_items": ORDER_ITEMS_SCHEMA,
    "payments": PAYMENTS_SCHEMA,
    "order_reviews": ORDER_REVIEWS_SCHEMA,
}

def get_schema(table_name: str):
    """Get schema for a specific table"""
    return SCHEMAS.get(table_name, None)
