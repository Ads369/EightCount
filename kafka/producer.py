from kafka import KafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CLIENT_ID

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    client_id=KAFKA_CLIENT_ID,
)


def delivery_report(error, message):
    if error is not None:
        print(f"Ошибка доставки Kafka: {error}")
    else:
        print(
            f"Сообщение доставлено в {message.topic} "
            f"[раздел {message.partition}, смещение {message.offset}]"
        )


def send_event(topic: str, key: str, value: str) -> None:
    """Отправляет событие в указанный топик Kafka.

    Args:
        topic: Название топика (например, 'student.events').
        key: Ключ сообщения (используется для маршрутизации в раздел).
        value: Тело сообщения в виде строки (обычно JSON).
    """
    future = producer.send(
        topic,
        key=key.encode("utf-8"),
        value=value.encode("utf-8"),
    )
    # delivery_report вызывается асинхронно через callback
    future.add_callback(lambda m: delivery_report(None, m))
    future.add_errback(lambda e: delivery_report(e, None))


def flush(timeout: float = 2.0) -> None:
    """Ждёт завершения отправки всех сообщений с таймаутом.

    Args:
        timeout: Максимальное время ожидания в секундах.
                 Если Kafka недоступна, не блокирует вечно.
    """
    try:
        producer.flush(timeout=timeout)
    except Exception as e:
        print(f"Kafka flush timeout или ошибка: {e}")
