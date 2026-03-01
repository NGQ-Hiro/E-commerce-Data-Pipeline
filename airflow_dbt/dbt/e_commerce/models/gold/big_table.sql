{{
  config(
  materialized = 'incremental',
  incremental_strategy = 'merge',
  unique_key = 'bigtable_key',
  on_schema_change = 'append_new_columns',
    cluster_by = ['order_id'],
    partition_by = {
        "field": "order_date",
        "data_type": "date",
        "granularity": "month"
    }
  )
}}

with filtered_orders as (
  select *
  from {{ ref('orders') }}
  {% if is_incremental() %}
  where cast(order_purchase_timestamp as date) >= (
    select date_sub(coalesce(max(order_date), date('1900-01-01')), interval 3 day)
    from {{ this }}
  )
  {% endif %}
)

select
  to_hex(md5(concat(
    coalesce(cast(o.order_id as string), ''), '|',
    coalesce(cast(oi.order_item_id as string), ''), '|',
    coalesce(cast(p.payment_sequential as string), ''), '|',
    coalesce(cast(r.review_id as string), '')
  ))) as bigtable_key,
  o.order_id,
  o.customer_id,
  oi.seller_id,
  oi.product_id,
  c.scd_id as customer_key,
  s.scd_id as seller_key,
  d.date_key as order_date_key,

  -- Order details
  o.order_status,
  o.order_purchase_timestamp,
  o.order_approved_at,
  o.order_delivered_carrier_date,
  o.order_delivered_customer_date,
  o.order_estimated_delivery_date,
  cast(o.order_purchase_timestamp as date) as order_date,

  -- Order item details
  oi.order_item_id,
  oi.price as item_price,
  oi.freight_value as item_freight,

  -- Payment details
  p.payment_sequential,
  p.payment_type,
  p.payment_installments,
  p.payment_value,

  -- Review details
  r.review_id,
  coalesce(r.review_score, 0) as review_score,
  r.review_creation_date,

  -- Geolocation details (customer location)
  geo_cust.city as customer_city,
  geo_cust.state as customer_state,
  geo_cust.latitude as customer_lat,
  geo_cust.longtitude as customer_lng,

  -- Geolocation details (seller location)
  geo_sell.city as seller_city,
  geo_sell.state as seller_state,
  geo_sell.latitude as seller_lat,
  geo_sell.longtitude as seller_lng

from filtered_orders o
left join {{ ref('order_items') }} oi on o.order_id = oi.order_id
left join {{ ref('payments') }} p on o.order_id = p.order_id
left join {{ ref('order_reviews') }} r on o.order_id = r.order_id
left join {{ ref('customers') }} c on o.customer_id = c.customer_id and o.order_purchase_timestamp between c.valid_from and c.valid_to
left join {{ ref('sellers') }} s on oi.seller_id = s.seller_id and o.order_purchase_timestamp between s.valid_from and s.valid_to
left join {{ ref('dim_date') }} d on cast(o.order_purchase_timestamp as date) = d.full_date
left join {{ ref('geolocations') }} geo_cust on c.customer_zip_code_prefix = geo_cust.geolocation_zip_code_prefix
left join {{ ref('geolocations') }} geo_sell on s.seller_zip_code_prefix = geo_sell.geolocation_zip_code_prefix
