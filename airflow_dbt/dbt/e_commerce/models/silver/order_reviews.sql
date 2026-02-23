{{
  config(
    materialized = 'incremental',
    unique_key = 'review_id',
    on_schema_change='append_new_columns'
  )
}}

with cdc as (
    select * from {{ source('bronze', 'order_reviews_cdc_external') }}
),

snapshot as (
    select * from {{ source('bronze', 'order_reviews_snapshot_external') }}
),

raw_source as (
    {% if is_incremental() %}
        -- Get new changes from CDC
        select 
            after.review_id,
            after.order_id,
            after.review_score,
            after.review_comment_title,
            after.review_comment_message,
            TIMESTAMP_SECONDS(CAST(after.review_creation_date / 1000000 AS INT64)) as review_creation_date,
            TIMESTAMP_SECONDS(CAST(after.review_answer_timestamp / 1000000 AS INT64)) as review_answer_timestamp,
            cast(dt as date) as cdc_dt
        from cdc
        where cast(dt as date) > (select coalesce(max(cdc_dt), '1900-01-01') from {{ this }})
    {% else %}
        -- Initial load from Snapshot
        select 
            review_id,
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            review_answer_timestamp,
            cast(null as date) as cdc_dt
        from snapshot
    {% endif %}
),

deduped_data as (
    -- Ensure only 1 row per review_id reaches the merge step
    select *
    from raw_source
    qualify row_number() over (partition by review_id order by cdc_dt desc nulls last) = 1
)

select * from deduped_data
