-- =============================================
-- 1. Table: product_category_name_translation
-- =============================================
CREATE TABLE product_category_name_translation (
    product_category_name VARCHAR(64) PRIMARY KEY,
    product_category_name_english VARCHAR(64)
);

-- =============================================
-- 2. Table: geolocation
-- =============================================
-- Lưu ý: Bảng này trong dataset Olist gốc có nhiều dòng trùng zip_code_prefix
CREATE TABLE geolocation (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city VARCHAR(64),
    geolocation_state VARCHAR(64)
);

-- =============================================
-- 3. Table: sellers
-- =============================================
CREATE TABLE sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(64),
    seller_state VARCHAR(64)
);

-- =============================================
-- 4. Table: customers
-- =============================================
CREATE TABLE customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(32),
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(64),
    customer_state VARCHAR(64)
);

-- =============================================
-- 5. Table: products
-- =============================================
CREATE TABLE products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(64),
    product_name_length INTEGER,
    product_description_length INTEGER, -- Độ dài thường là số nguyên
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm DOUBLE PRECISION,
    product_height_cm DOUBLE PRECISION,
    product_width_cm DOUBLE PRECISION,
    -- FK
    FOREIGN KEY (product_category_name) REFERENCES product_category_name_translation(product_category_name)
);

-- =============================================
-- 6. Table: orders
-- =============================================
CREATE TABLE orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64),
    order_status VARCHAR(32),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    -- FK
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- =============================================
-- 7. Table: order_items
-- =============================================
CREATE TABLE order_items (
    order_id VARCHAR(64), -- có thể trùng lặp vì 1 order có nhiều item
    order_item_id INTEGER, -- cái này là số thứ tự item trong đơn hàng
    product_id VARCHAR(64),
    seller_id VARCHAR(64),
    shipping_limit_date TIMESTAMP,
    price DOUBLE PRECISION, -- giá tiền
    freight_value DOUBLE PRECISION, -- giá vận chuyển từng item trong 1 order
    -- FKs
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- =============================================
-- 8. Table: payments
-- =============================================
-- Not have PK
CREATE TABLE payments (
    order_id VARCHAR(64),
    payment_sequential INTEGER, -- trả bằng nhiều loại (khác nhau creadit hoặc boleto ....)
    payment_type VARCHAR(32),
    payment_installments INTEGER, -- số lần trả góp (nhưng vẫn lưu một lần)
    payment_value DOUBLE PRECISION, -- Có thể dùng NUMERIC(10,2) nếu muốn chính xác tiền tệ
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- =============================================
-- 9. Table: order_reviews
-- =============================================
CREATE TABLE order_reviews (
    review_id VARCHAR(64), -- not unique
    order_id VARCHAR(64),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);


-- =============================================
CREATE INDEX idx_order_items_product_id_hash
ON order_items
USING HASH (product_id);