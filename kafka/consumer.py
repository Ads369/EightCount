import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaConsumer

from kafka.config import (
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

# --- Сервис ---
application = Application()
service = application.service
repo = service.repo


def handle_student_event(data: dict) -> None:
    """Обрабатывает события учеников."""
    action = data.get("action")
    name = data.get("data", {}).get("name")

    if action == "student.created":
        try:
            service.add_student(name)
            print(f"[consumer] Создан ученик: {name}")
        except Exception as e:
            print(f"[consumer] Ошибка создания ученика {name}: {e}")

    elif action == "student.deleted":
        try:
            service.remove_student(name)
            print(f"[consumer] Удалён ученик: {name}")
        except Exception as e:
            print(f"[consumer] Ошибка удаления ученика {name}: {e}")

    else:
        print(f"[consumer] Неизвестное действие для студента: {action}")


def handle_subscription_event(data: dict) -> None:
    """Обрабатывает события подписок."""
    action = data.get("action")
    owner = data.get("data", {}).get("owner")
    total_visits = data.get("data", {}).get("total_visits")

    if action == "subscription.created":
        try:
            service.add_subscription(owner, total_visits)
            print(f"[consumer] Создана подписка для {owner}: {total_visits} визитов")
        except Exception as e:
            print(f"[consumer] Ошибка создания подписки для {owner}: {e}")

    elif action == "subscription.deleted":
        try:
            service.remove_subscription(owner)
            print(f"[consumer] Удалена подписка для {owner}")
        except Exception as e:
            print(f"[consumer] Ошибка удаления подписки для {owner}: {e}")

    else:
        print(f"[consumer] Неизвестное действие для подписки: {action}")


def handle_checkin_event(data: dict) -> None:
    """Обрабатывает события списания занятий."""
    owner = data.get("data", {}).get("owner")

    try:
        remaining = service.check_in(owner)
        print(f"[consumer] Списание для {owner}, осталось: {remaining}")
    except Exception as e:
        print(f"[consumer] Ошибка списания для {owner}: {e}")


def process_event(raw_message: str) -> None:
    """Разбирает сырое сообщение из Kafka и вызывает соответствующий обработчик."""
    try:
        event = json.loads(raw_message)
    except json.JSONDecodeError as e:
        print(f"[consumer] Ошибка парсинга JSON: {e}")
        return

    event_id = event.get("event_id")
    if not event_id:
        print("[consumer] Сообщение без event_id, пропускаем")
        return

    # Идемпотентность через БД
    if repo.is_event_processed(event_id):
        print(f"[consumer] Событие {event_id} уже обрабатывалось, пропускаем")
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
        print(f"[consumer] Неизвестный топик: {topic}")

    repo.mark_event_processed(event_id)


def start_consumer() -> None:
    """Запускает консюмер в бесконечном цикле."""
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_CONSUMER_GROUP,
        auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
        value_deserializer=lambda v: v.decode("utf-8") if v else None,
        key_deserializer=lambda v: v.decode("utf-8") if v else None,
    )
    consumer.subscribe(ALL_TOPICS)

    print(f"[consumer] Подписка на топики: {ALL_TOPICS}")
    print("[consumer] Ожидание сообщений... (Ctrl+C для остановки)")

    try:
        while True:
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                continue

            for topic_partition, records in messages.items():
                for message in records:
                    try:
                        raw_value = message.value
                        print(f"[consumer] Получено из {message.topic}: {raw_value}")
                        process_event(raw_value)
                    except Exception as e:
                        print(f"[consumer] Ошибка обработки сообщения: {e}")

    except KeyboardInterrupt:
        print("\n[consumer] Остановка по запросу пользователя")
    finally:
        consumer.close()
        print("[consumer] Соединение закрыто")


if __name__ == "__main__":
    start_consumer()
