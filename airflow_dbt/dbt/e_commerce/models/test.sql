{{ config(
    materialized='table'
) }}

select *
from `e_commerce_dataset_bronze.customers_cdc_external`
limit