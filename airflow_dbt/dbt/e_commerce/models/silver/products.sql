-- =============================================
-- Table: products
-- =============================================
-- CREATE TABLE products (
--     product_id VARCHAR(64) PRIMARY KEY,
--     product_category_name VARCHAR(64),
--     product_name_length INTEGER,
--     product_description_length INTEGER, -- Độ dài thường là số nguyên
--     product_photos_qty INTEGER,
--     product_weight_g INTEGER,
--     product_length_cm DOUBLE PRECISION,
--     product_height_cm DOUBLE PRECISION,
--     product_width_cm DOUBLE PRECISION,
--     -- FK
--     FOREIGN KEY (product_category_name) REFERENCES product_category_name_translation(product_category_name)
-- );



select 
    product_id,
    b.product_category_name_english as product_category_name,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from {{source('bronze', 'products_snapshot_external')}} a 
left join {{source('bronze', 'product_category_name_translation_snapshot_external')}} b
on a.product_category_name = b.product_category_name