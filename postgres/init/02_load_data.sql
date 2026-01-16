-- =============================================
-- PHẦN LOAD DATA
-- =============================================

-- 1. Load các bảng danh mục/độc lập trước
COPY product_category_name_translation
FROM '/data/product_category_name_translation.csv' 
DELIMITER ',' CSV HEADER;

COPY geolocation
FROM '/data/olist_geolocation_dataset.csv' 
DELIMITER ',' CSV HEADER;

COPY sellers
FROM '/data/olist_sellers_dataset.csv' 
DELIMITER ',' CSV HEADER;

COPY customers
FROM '/data/olist_customers_dataset.csv' 
DELIMITER ',' CSV HEADER;

COPY products
FROM '/data/olist_products_dataset.csv' 
DELIMITER ',' CSV HEADER;

-- 2. Load bảng Orders (Phụ thuộc customers)
COPY orders
FROM '/data/olist_orders_dataset.csv' 
DELIMITER ',' CSV HEADER;

-- 3. Load các bảng chi tiết (Phụ thuộc Orders, Products, Sellers)
COPY order_items
FROM '/data/olist_order_items_dataset.csv' 
DELIMITER ',' CSV HEADER;

-- Chú ý: Tên bảng là 'payments', file csv là 'olist_order_payments_dataset.csv'
COPY payments 
FROM '/data/olist_order_payments_dataset.csv' 
DELIMITER ',' CSV HEADER;

COPY order_reviews
FROM '/data/olist_order_reviews_dataset.csv' 
DELIMITER ',' CSV HEADER;