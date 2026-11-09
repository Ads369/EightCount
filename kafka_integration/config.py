import os
from pathlib import Path

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")

KAFKA_CLIENT_ID = "eightcount-producer"

KAFKA_CONSUMER_GROUP = os.environ.get("KAFKA_CONSUMER_GROUP", "eightcount-group-v3")

KAFKA_AUTO_OFFSET_RESET = "earliest"

TOPIC_STUDENT_EVENTS = "student.events"
TOPIC_SUBSCRIPTION_EVENTS = "subscription.events"
TOPIC_CHECKIN_EVENTS = "checkin.events"

ALL_TOPICS = [
    TOPIC_STUDENT_EVENTS,
    TOPIC_SUBSCRIPTION_EVENTS,
    TOPIC_CHECKIN_EVENTS,
]
