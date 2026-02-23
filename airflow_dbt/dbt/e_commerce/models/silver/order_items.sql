{{
  config(
    materialized = 'incremental',
    unique_key = ['order_id', 'order_item_id'],
    on_schema_change='append_new_columns'
  )
}}

with cdc as (
    select * from {{ source('bronze', 'order_items_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'order_items_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        -- Get new changes from CDC
        select 
            after.order_id,
            after.order_item_id,
            after.product_id,
            after.seller_id,
            TIMESTAMP_SECONDS(CAST(after.shipping_limit_date / 1000000 AS INT64)) as shipping_limit_date,
            after.price,
            after.freight_value,
            cast(dt as date) as cdc_dt
        from cdc
        where cast(dt as date) > (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        -- Initial load from Snapshot
        select 
            order_id,
            order_item_id,
            product_id,
            seller_id,
            cast(shipping_limit_date as timestamp) as shipping_limit_date,
            price,
            freight_value,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

deduped_data as (
    -- Ensure only 1 row per order_item reaches the merge step
    select *
    from raw_source
    qualify row_number() over (partition by order_id, order_item_id order by cdc_dt desc nulls last) = 1
)

select * from deduped_data
