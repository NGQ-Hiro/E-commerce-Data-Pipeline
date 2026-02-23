
{{
  config(
    materialized = 'incremental',
    unique_key = 'scd_id', 
    incremental_strategy = 'merge',
    on_schema_change = 'append_new_columns',
    cluster_by = ['customer_id']
  )
}}

with cdc as (
    select * from {{ source('bronze', 'customers_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'customers_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        select 
            after.customer_id as customer_id,
            after.customer_unique_id,
            after.customer_zip_code_prefix,
            after.customer_city,
            after.customer_state,
            op as operation,
            timestamp_millis(source_ts_ms) as event_timestamp,
            cast(dt as date) as cdc_dt
        from cdc
        where cast(dt as date) >= (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        select 
            customer_id,
            customer_unique_id,
            customer_zip_code_prefix,
            customer_city,
            customer_state,
            'r' as operation,
            timestamp('2026-01-01') as event_timestamp,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

{% if is_incremental() %}

-- OPTIMIZED: Only fetch old records that have NEW CDC events (avoid full table scan)
old_records_affected as (
    select 
        scd_id,
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        operation,
        cdc_dt,
        valid_from as event_timestamp
    from {{ this }}
    where customer_id in (select distinct customer_id from raw_source)
),

all_events as (
    -- Old records that are affected
    select * from old_records_affected
    
    union all
    
    -- New CDC events
    select 
        null as scd_id,
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        operation,
        cdc_dt,
        event_timestamp
    from raw_source
),

processing_scd as (
    select 
        coalesce(scd_id, generate_uuid()) as scd_id,
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        operation,
        cdc_dt,
        event_timestamp,
        
        -- WINDOW FUNCTION on COMBINED data (only affected old + new)
        lead(event_timestamp) over (
            partition by customer_id 
            order by event_timestamp asc
        ) as next_event_time
    from all_events
)

select
    scd_id,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    operation,
    cdc_dt,
    event_timestamp as valid_from,
    
    case 
        when operation = 'd' then event_timestamp
        else coalesce(next_event_time, timestamp('9999-12-31')) 
    end as valid_to,
    
    case 
        when next_event_time is null and operation != 'd' then true 
        else false 
    end as is_current

{% else %}

-- INITIAL LOAD: Just from snapshot
processing_scd as (
    select 
        *,
        generate_uuid() as scd_id,
        lead(event_timestamp) over (partition by customer_id order by event_timestamp asc) as next_event_time
    from raw_source
)

select
    scd_id,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    operation,
    cdc_dt,
    event_timestamp as valid_from,
    
    case 
        when operation = 'd' then event_timestamp
        else coalesce(next_event_time, timestamp('9999-12-31')) 
    end as valid_to,
    
    case 
        when next_event_time is null and operation != 'd' then true 
        else false 
    end as is_current
from processing_scd

{% endif %}
