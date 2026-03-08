{{
  config(
    materialized = 'incremental',
    unique_key = ['order_id', 'payment_sequential'],
    on_schema_change='append_new_columns'
  )
}}

with cdc as (
    select * from {{ source('bronze', 'payments_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'payments_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        -- Get new changes from CDC
        select 
            after.order_id,
            after.payment_sequential,
            after.payment_type,
            after.payment_installments,
            after.payment_value,
            cast(dt as date) as cdc_dt
        from cdc
        where cast(dt as date) >= (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        -- Initial load from Snapshot
        select 
            order_id,
            payment_sequential,
            payment_type,
            payment_installments,
            payment_value,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

deduped_data as (
    -- Ensure only 1 row per order_id+payment_sequential reaches the merge step
    select *
    from raw_source
    qualify row_number() over (partition by order_id, payment_sequential order by cdc_dt desc nulls last) = 1
)

select * from deduped_data