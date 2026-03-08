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
        -- deterministic event id
        to_hex(md5(concat(
            cast(after.customer_id as string),
            cast(source.ts_ms as string),
            cast(source.lsn as string)
        ))) as scd_id,
        after.customer_id as customer_id,
        after.customer_unique_id as customer_unique_id,
        after.customer_zip_code_prefix as customer_zip_code_prefix,
        after.customer_city as customer_city,
        after.customer_state as customer_state,
        op as operation,
        cast(dt as date) as cdc_dt,
        timestamp_trunc(timestamp_millis(source.ts_ms), second) as event_timestamp
    from cdc

    -- lookback 3 ngày để handle late data
    where cast(dt as date) >= (
        select date_sub(
            coalesce(max(cdc_dt), '1900-01-01'),
            interval 3 day
        )
        from {{ this }}
    )

    -- deduplication trong trường hợp có nhiều event cho cùng 1 customer_id, lsn
    qualify row_number() over (
            partition by after.customer_id, source.lsn
            order by source.lsn desc
        ) = 1

{% else %}

    select
        to_hex(md5(concat(
            cast(customer_id as string),
            'snapshot'
        ))) as scd_id,
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        'r' as operation,
        cast('2026-01-01' as date) as cdc_dt,
        timestamp('2023-01-01') as event_timestamp
    from snapshot

{% endif %}
),

{% if is_incremental() %}

-- Loại duplicate event đã tồn tại
new_events as (
    select *
    from raw_source r
    where not exists (
        select 1
        from {{ this }} t
        where t.customer_id = r.customer_id and t.scd_id = r.scd_id
    )
),

-- chỉ lấy record cũ của customer bị ảnh hưởng
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
    where customer_id in (
        select distinct customer_id from new_events
    )
),

all_events as (
    select * from new_events
    union all
    select * from old_records_affected
),

processing_scd as (
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
    valid_from,

    case
        when operation = 'd' then valid_from
        else coalesce(next_event_time, timestamp('9999-12-31'))
    end as valid_to,

    case
        when next_event_time is null and operation != 'd'
        then true else false
    end as is_current

from processing_scd

{% else %}

processing_scd as (
    select
        *,
        lead(event_timestamp) over (
            partition by customer_id
            order by event_timestamp asc
        ) as next_event_time
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
        when next_event_time is null and operation != 'd'
        then true else false
    end as is_current

from processing_scd
{% endif %}