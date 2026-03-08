-- ORDER ITEM BIGTABLE: Order item-level fact table
-- Grain: 1 row per order item (order_id + order_item_id)
-- Contains: order_item details, seller, product, seller geo
{{
  config(
  materialized = 'incremental',
  incremental_strategy = 'merge',
  unique_key = 'order_item_key',
  on_schema_change = 'append_new_columns',
    cluster_by = ['seller_id', 'product_id'],
    partition_by = {
        "field": "order_date",
        "data_type": "date",
        "granularity": "month"
    }
  )
}}

with filtered_order_items as (
  select oi.*
  from {{ ref('order_items') }} oi
  inner join {{ ref('orders') }} o on oi.order_id = o.order_id
  {% if is_incremental() %}
  where cast(o.order_purchase_timestamp as date) >= (
    select date_sub(coalesce(max(order_date), date('1900-01-01')), interval 3 day)
    from {{ this }}
  )
  {% endif %}
)

select
  -- Composite primary key
  to_hex(md5(concat(
    coalesce(cast(oi.order_id as string), ''), '-',
    coalesce(cast(oi.order_item_id as string), '')
  ))) as order_item_key,
  
  -- Foreign keys
  oi.order_id,
  oi.order_item_id,
  oi.seller_id,
  s.scd_id as seller_key,
  oi.product_id,
  d.date_key as order_date_key,
  
  -- For partitioning only
  cast(o.order_purchase_timestamp as date) as order_date,
  
  -- Order item details
  oi.price as item_price,
  oi.freight_value as item_freight,
  
  -- Product information
  pr.product_category_name,
  
  -- Seller geolocation
  geo_sell.city as seller_city,
  geo_sell.state as seller_state,
  geo_sell.latitude as seller_lat,
  geo_sell.longtitude as seller_lng,

  -- dim_date
  d.year,
  d.quarter,
  d.month,
  d.day,
  d.day_of_week,
  d.is_weekend,
  d.is_holiday

from filtered_order_items oi
left join {{ ref('orders') }} o on oi.order_id = o.order_id
left join {{ ref('products') }} pr on oi.product_id = pr.product_id
left join {{ ref('sellers') }} s
  on oi.seller_id = s.seller_id
  and o.order_purchase_timestamp >= s.valid_from
  and o.order_purchase_timestamp < s.valid_to
left join {{ ref('dim_date') }} d 
  on cast(o.order_purchase_timestamp as date) = d.full_date
left join {{ ref('geolocations') }} geo_sell
  on safe_cast(s.seller_zip_code_prefix as int64) = safe_cast(geo_sell.geolocation_zip_code_prefix as int64)
