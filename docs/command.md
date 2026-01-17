# Postgres

- cannot connect or switch different db in the init
- Only can do it in cli

docker compose up -d (not show log)
docker compuse down -v (rm entire container)
docker compose logs -f postgres
docker exec -it postgres psql -U admin -d db
-it container_name -U user -d database_name

\l -- liệt kê database
\c db -- kết nối sang database db
\dt -- liệt kê bảng
\dt+ -- liệt kê bảng kèm size
\d table_name -- mô tả cấu trúc bảng
\du -- liệt kê user (role)
\dn -- liệt kê schema
\q -- thoát psql
\x -- đổi cách trình bày tables

# Debezium

- First time debezium init and read the database, it scan all table then read the log from that current (only 1 time when init debezium)
  r: snapshot database
- u: update, d: delete, c: insert
- Add connector
  curl -X POST http://localhost:8083/connectors \
   -H "Content-Type: application/json" \
   -d @debezium.json
- Delete connector
  curl -X DELETE http://localhost:8083/connectors/olist-connector

- Get list connector
  curl http://localhost:8083/connectors

- Test debezium
  create table orders(
  id text primary key,
  salary int
  );

insert into orders (id, salary)
values
('marry', 20),
('peter', 10);

    "before": null,
    "after": {
    	"id": "marry",
    	"salary": 20
    }

UPDATE orders
SET salary = 30
WHERE id = 'marry';

DELETE FROM orders
WHERE id = 'peter';

# Kafka

# GCP

- gcloud init: sign in -> create or choose project
- gsutil ls: ls the bucket in gcs
- cat /var/log/cloud-init-output.log: see log when init
# SSH

ssh -i ~/.ssh/gcloud hieu@<ip>
