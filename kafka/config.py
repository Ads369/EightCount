import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

KAFKA_CLIENT_ID = "eightcount-producer"

KAFKA_CONSUMER_GROUP = "eightcount-group"

KAFKA_AUTO_OFFSET_RESET = "earliest"

TOPIC_STUDENT_EVENTS = "student.events"
TOPIC_SUBSCRIPTION_EVENTS = "subscription.events"
TOPIC_CHECKIN_EVENTS = "checkin.events"

ALL_TOPICS = [
    TOPIC_STUDENT_EVENTS,
    TOPIC_SUBSCRIPTION_EVENTS,
    TOPIC_CHECKIN_EVENTS,
]
