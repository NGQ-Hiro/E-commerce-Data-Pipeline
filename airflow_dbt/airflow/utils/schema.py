from google.cloud import bigquery
common_metadata = [
            bigquery.SchemaField("_last_cdc_ts", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("_ingestion_time", "TIMESTAMP", mode="NULLABLE"),
        ]

schema = {
    "product_category_name_translation": [
        bigquery.SchemaField("product_category_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_category_name_english", "STRING", mode="NULLABLE"),
    ] + common_metadata,

    "geolocation": [
        bigquery.SchemaField("geolocation_zip_code_prefix", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("geolocation_lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("geolocation_lng", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("geolocation_city", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("geolocation_state", "STRING", mode="NULLABLE"),
    ] + common_metadata,

    "sellers": [
        bigquery.SchemaField("seller_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("seller_zip_code_prefix", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("seller_city", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("seller_state", "STRING", mode="NULLABLE"),
    ] + common_metadata,

    "customers": [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_unique_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("customer_zip_code_prefix", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("customer_city", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("customer_state", "STRING", mode="NULLABLE"),
    ] + common_metadata,

    "products": [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_category_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("product_name_length", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("product_description_length", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("product_photos_qty", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("product_weight_g", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("product_length_cm", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("product_height_cm", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("product_width_cm", "FLOAT", mode="NULLABLE"),
    ] + common_metadata,

    "orders": [
        bigquery.SchemaField("order_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("order_status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("order_purchase_timestamp", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("order_approved_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("order_delivered_carrier_date", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("order_delivered_customer_date", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("order_estimated_delivery_date", "TIMESTAMP", mode="NULLABLE"),
    ] + common_metadata,

    "order_items": [
        bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("order_item_id", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("product_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("seller_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("shipping_limit_date", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("price", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("freight_value", "FLOAT", mode="NULLABLE"),
    ] + common_metadata,

    "payments": [
        bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("payment_sequential", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("payment_type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("payment_installments", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("payment_value", "FLOAT", mode="NULLABLE"),
    ] + common_metadata,

    "order_reviews": [
        bigquery.SchemaField("review_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("order_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("review_score", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("review_comment_title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("review_comment_message", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("review_creation_date", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("review_answer_timestamp", "TIMESTAMP", mode="NULLABLE"),
    ] + common_metadata,
}