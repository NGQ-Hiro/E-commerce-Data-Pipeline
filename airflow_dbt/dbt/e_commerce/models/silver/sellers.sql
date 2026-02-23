
{{
  config(
    materialized = 'incremental',
    unique_key = 'seller_id',
    on_schema_change='append_new_columns'
  )
}}

with cdc as (
    select * from {{ source('bronze', 'sellers_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'sellers_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        -- Get new changes from CDC
        select 
            after.seller_id,
            after.seller_zip_code_prefix,
            after.seller_city,
            after.seller_state,
            cast(dt as date) as cdc_dt
        from cdc
        -- Use dbt's built-in lookback logic instead of a manual run_query if possible
        where dt > (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        -- Initial load from Snapshot
        select 
            seller_id,
            seller_zip_code_prefix,
            seller_city,
            seller_state,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

deduped_data as (
    -- Ensure only 1 row per seller_id reaches the merge step
    select *
    from raw_source
    qualify row_number() over (partition by seller_id order by cdc_dt desc nulls last) = 1
)

-- dbt will take this SELECT and turn it into a MERGE for you
select * from deduped_data


