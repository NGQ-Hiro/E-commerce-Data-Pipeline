-- ORDER BIGTABLE: Order-level fact table
-- Grain: 1 row per order
-- Contains: order details, customer, aggregated payments, aggregated reviews, date dimension, customer geo
{{
  config(
  materialized = 'incremental',
  incremental_strategy = 'merge',
  unique_key = 'order_id',
  on_schema_change = 'append_new_columns',
    cluster_by = ['order_id', 'customer_id'],
    partition_by = {
        "field": "order_date",
        "data_type": "date",
        "granularity": "month"
    }
  )
}}

with filtered_orders as (
  select o.*
  from {{ ref('orders') }} o
  {% if is_incremental() %}
  where cast(o.order_purchase_timestamp as date) >= (
    select date_sub(coalesce(max(order_date), date('1900-01-01')), interval 3 day)
    from {{ this }}
  )
  {% endif %}
),

-- Aggregate payments by order_id
payments_agg as (
  select
    order_id,
    sum(payment_value) as total_payment_value,
    count(*) as payment_count,
    STRING_AGG(DISTINCT payment_type, ', ' ORDER BY payment_type) AS payment_types
  from {{ ref('payments') }}
  group by order_id
),

-- Aggregate reviews by order_id
reviews_agg as (
  select
    order_id,
    count(*) as review_count,
    avg(review_score) as avg_review_score,
    max(review_creation_date) as latest_review_date,
    min(review_creation_date) as first_review_date,
  from {{ ref('order_reviews') }}
  group by order_id
)

select
  -- Primary key
  o.order_id,
  
  -- Foreign keys
  o.customer_id,
  c.scd_id as customer_key,
  d.date_key as order_date_key,
  
  -- Order information
  o.order_status,
  cast(o.order_purchase_timestamp as date) as order_date,
  o.order_purchase_timestamp,
  o.order_delivered_customer_date,
  o.order_estimated_delivery_date,
  
  -- Payment aggregates
  pa.total_payment_value,
  pa.payment_count,
  pa.payment_types,
  
  -- Review aggregates
  ra.review_count,
  ra.avg_review_score,
  ra.latest_review_date,
  ra.first_review_date,
  
  -- Customer geolocation
  c.customer_city,
  c.customer_state,
  geo_cust.latitude as customer_lat,
  geo_cust.longtitude as customer_lng,

  -- dim_date
  d.year,
  d.quarter,
  d.month,
  d.day,
  d.day_of_week,
  d.is_weekend,
  d.is_holiday,
  
  -- Calculated metrics
  case 
    when o.order_delivered_customer_date is not null and o.order_purchase_timestamp is not null
    then date_diff(cast(o.order_delivered_customer_date as date), cast(o.order_purchase_timestamp as date), day)
  end as delivery_days,
  
  case 
    when o.order_delivered_customer_date is not null and o.order_estimated_delivery_date is not null
    then date_diff(cast(o.order_delivered_customer_date as date), cast(o.order_estimated_delivery_date as date), day)
  end as delivery_delay_days

from filtered_orders o
left join payments_agg pa on o.order_id = pa.order_id
left join reviews_agg ra on o.order_id = ra.order_id
left join {{ ref('customers') }} c
  on o.customer_id = c.customer_id
  and o.order_purchase_timestamp >= c.valid_from
  and o.order_purchase_timestamp < c.valid_to
left join {{ ref('dim_date') }} d 
  on cast(o.order_purchase_timestamp as date) = d.full_date
left join {{ ref('geolocations') }} geo_cust
  on safe_cast(c.customer_zip_code_prefix as int64) = safe_cast(geo_cust.geolocation_zip_code_prefix as int64)
