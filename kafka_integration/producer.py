import threading
from kafka import KafkaProducer

from kafka_integration.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CLIENT_ID

_producer = None
_producer_lock = threading.Lock()


def _get_producer():
    global _producer
    if _producer is None:
        with _producer_lock:
            if _producer is None:
                _producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    client_id=KAFKA_CLIENT_ID,
                    request_timeout_ms=3000,
                    max_block_ms=3000,
                )
    return _producer


def _send_async(topic: str, key: str, value: str) -> None:
    """Отправляет событие в отдельном потоке, не блокируя основной."""
    def _do_send():
        try:
            producer = _get_producer()
            producer.send(
                topic,
                key=key.encode("utf-8"),
                value=value.encode("utf-8"),
            )
            producer.flush(timeout=2.0)
        except Exception as e:
            print(f"Ошибка отправки события в Kafka: {e}")

    thread = threading.Thread(target=_do_send, daemon=True)
    thread.start()


def send_event(topic: str, key: str, value: str) -> None:
    """Отправляет событие в указанный топик Kafka (fire-and-forget, не блокирует)."""
    _send_async(topic, key, value)


def flush(timeout: float = 2.0) -> None:
    """Ждёт завершения отправки всех сообщений с таймаутом."""
    global _producer
    if _producer is not None:
        try:
            _producer.flush(timeout=timeout)
        except Exception as e:
            print(f"Kafka flush timeout или ошибка: {e}")
