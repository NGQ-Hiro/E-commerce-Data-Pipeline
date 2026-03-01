{{
  config(
    materialized = 'table'
  )
}}

with date_spine as (
    -- Generate dates from 2016-01-01 to 2026-12-31
    select
        cast(day as date) as full_date
    from unnest(generate_date_array('2016-01-01', '2026-12-31')) as day
),

date_with_keys as (
    select
        format_date('%Y%m%d', full_date) as date_key,
        full_date,
        extract(year from full_date) as year,
        extract(quarter from full_date) as quarter,
        extract(month from full_date) as month,
        extract(day from full_date) as day,
        extract(dayofweek from full_date) - 1 as day_of_week,  -- 0 = Sunday, 6 = Saturday
        case 
            when extract(dayofweek from full_date) in (1, 7) then true 
            else false 
        end as is_weekend,
        -- Brazil public holidays (simplified)
        case 
            when format_date('%m-%d', full_date) in (
                '01-01',  -- New Year
                '04-21',  -- Tiradentes' Day
                '05-01',  -- Labour Day
                '09-07',  -- Independence Day
                '10-12',  -- Nossa Senhora Aparecida
                '11-02',  -- All Souls' Day
                '11-15',  -- Proclamation of the Republic
                '11-20',  -- Black Consciousness Day
                '12-25'   -- Christmas
            ) then true
            else false
        end as is_holiday
    from date_spine
)

select * from date_with_keys
order by full_date