from airflow import DAG
from airflow.providers.google.cloud.operators.pubsub import (
    PubSubPublishMessageOperator,
    PubSubCreateTopicOperator # <--- Import thêm cái này
)
from datetime import datetime

PROJECT_ID = "e-commerce-484010"
TOPIC_ID = "orders"

with DAG("test_gcp_provider", start_date=datetime(2025, 1, 1), schedule=None) as dag:
    
    # 1. Task tạo Topic (nếu chưa có)
    create_topic = PubSubCreateTopicOperator(
        task_id="create_topic",
        project_id=PROJECT_ID,
        topic=TOPIC_ID,
        fail_if_exists=False, # Quan trọng: Nếu có rồi thì không báo lỗi
    )

    # 2. Task bắn tin nhắn
    publish_msg = PubSubPublishMessageOperator(
        task_id="publish_msg",
        project_id=PROJECT_ID,
        topic=TOPIC_ID,
        messages=[{"data": b"Hello from Airflow 3"}],
    )

    # Thiết lập thứ tự
    create_topic >> publish_msg