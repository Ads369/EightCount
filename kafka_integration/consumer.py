import json
from datetime import datetime, timezone

from kafka import KafkaConsumer

from kafka_integration.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_AUTO_OFFSET_RESET,
    TOPIC_STUDENT_EVENTS,
    TOPIC_SUBSCRIPTION_EVENTS,
    TOPIC_CHECKIN_EVENTS,
    ALL_TOPICS,
)
from service import SubscriptionService
from app import Application

application = Application()
service = application.service
repo = service.repo
print(f"[DEBUG] repo = {type(repo).__name__}", flush=True)

def handle_student_event(data: dict) -> None:
    action = data.get("action")
    name = data.get("data", {}).get("name")
    if action == "student.created":
        try:
            service.add_student(name)
            print(f"[consumer] Создан ученик: {name}", flush=True)
        except Exception as e:
            print(f"[consumer] Ошибка создания ученика {name}: {e}", flush=True)
    elif action == "student.deleted":
        try:
            service.remove_student(name)
            print(f"[consumer] Удалён ученик: {name}", flush=True)
        except Exception as e:
            print(f"[consumer] Ошибка удаления ученика {name}: {e}", flush=True)
    else:
        print(f"[consumer] Неизвестное действие для студента: {action}", flush=True)


def handle_subscription_event(data: dict) -> None:
    action = data.get("action")
    owner = data.get("data", {}).get("owner")
    total_visits = data.get("data", {}).get("total_visits")
    if action == "subscription.created":
        try:
            service.add_subscription(owner, total_visits)
            print(f"[consumer] Создана подписка для {owner}: {total_visits} визитов", flush=True)
        except Exception as e:
            print(f"[consumer] Ошибка создания подписки для {owner}: {e}", flush=True)
    elif action == "subscription.deleted":
        try:
            service.remove_subscription(owner)
            print(f"[consumer] Удалена подписка для {owner}", flush=True)
        except Exception as e:
            print(f"[consumer] Ошибка удаления подписки для {owner}: {e}", flush=True)
    else:
        print(f"[consumer] Неизвестное действие для подписки: {action}", flush=True)


def handle_checkin_event(data: dict) -> None:
    owner = data.get("data", {}).get("owner")
    try:
        remaining = service.check_in(owner)
        print(f"[consumer] Списание для {owner}, осталось: {remaining}", flush=True)
    except Exception as e:
        print(f"[consumer] Ошибка списания для {owner}: {e}", flush=True)


def process_event(raw_message: str) -> None:
    try:
        event = json.loads(raw_message)
    except json.JSONDecodeError as e:
        print(f"[consumer] Ошибка парсинга JSON: {e}", flush=True)
        return

    event_id = event.get("event_id")
    if not event_id:
        print("[consumer] Сообщение без event_id, пропускаем", flush=True)
        return

    if repo.is_event_processed(event_id):
        print(f"[consumer] Событие {event_id} уже обрабатывалось, пропускаем", flush=True)
        return

    topic = event.get("topic", "")
    data = event.get("data", {})

    if "student" in topic:
        handle_student_event(data)
    elif "subscription" in topic:
        handle_subscription_event(data)
    elif "checkin" in topic:
        handle_checkin_event(data)
    else:
        print(f"[consumer] Неизвестный топик: {topic}", flush=True)

    repo.mark_event_processed(event_id)


def start_consumer() -> None:
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_CONSUMER_GROUP,
        auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
        request_timeout_ms=5000,
        consumer_timeout_ms=1000,
    )
    consumer.subscribe(ALL_TOPICS)

    print(f"[consumer] Подписка на топики: {ALL_TOPICS}", flush=True)
    print("[consumer] Ожидание сообщений (Ctrl+C для остановки)", flush=True)

    try:
        while True:
            records = consumer.poll(timeout_ms=1000)
            if not records:
                continue
            for topic_partition, messages in records.items():
                for message in messages:
                    try:
                        raw_value = message.value.decode("utf-8") if message.value else ""
                        print(f"[consumer] Получено из {message.topic}: {raw_value}", flush=True)
                        process_event(raw_value)
                    except Exception as e:
                        print(f"[consumer] Ошибка обработки сообщения: {e}", flush=True)
    except KeyboardInterrupt:
        print("\n[consumer] Остановка по запросу пользователя", flush=True)
    finally:
        consumer.close()
        print("[consumer] Соединение закрыто", flush=True)


if __name__ == "__main__":
    start_consumer()
