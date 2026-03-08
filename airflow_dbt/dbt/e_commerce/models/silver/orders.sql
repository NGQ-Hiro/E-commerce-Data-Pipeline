{{
  config(
    materialized = 'incremental',
    unique_key = 'order_id',
    on_schema_change='append_new_columns',
    partition_by={
        "field": "cdc_dt",
        "data_type": "date"
    }
  )
}}


with cdc as (
    select * from {{ source('bronze', 'orders_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'orders_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        -- Get new changes from CDC
        select 
            after.order_id,
            after.customer_id,
            after.order_status,
            TIMESTAMP_SECONDS(CAST(after.order_purchase_timestamp / 1000000 AS INT64)) as order_purchase_timestamp,
            TIMESTAMP_SECONDS(CAST(after.order_approved_at / 1000000 AS INT64)) as order_approved_at,
            TIMESTAMP_SECONDS(CAST(after.order_delivered_carrier_date / 1000000 AS INT64)) as order_delivered_carrier_date,
            TIMESTAMP_SECONDS(CAST(after.order_delivered_customer_date / 1000000 AS INT64)) as order_delivered_customer_date,
            TIMESTAMP_SECONDS(CAST(after.order_estimated_delivery_date / 1000000 AS INT64)) as order_estimated_delivery_date,
            cast(dt as date) as cdc_dt
        from cdc
        where dt >= (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        -- Initial load from Snapshot
        select 
            order_id,
            customer_id,
            order_status,
            order_purchase_timestamp,
            order_approved_at,
            order_delivered_carrier_date,
            order_delivered_customer_date,
            order_estimated_delivery_date,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

deduped_data as (
    -- Ensure only 1 row per order_id reaches the merge step
    select *
    from raw_source
    qualify row_number() over (partition by order_id order by cdc_dt desc nulls last) = 1
)

select * from deduped_data