select 
    geolocation_zip_code_prefix,
    avg(geolocation_lat) as latitude,
    avg(geolocation_lng) as longtitude,
    max(geolocation_city) as city,
    max(geolocation_state) as state
from {{ source('bronze', 'geolocation_snapshot_external') }}
group by geolocation_zip_code_prefix