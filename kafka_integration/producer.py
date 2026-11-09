import json
import logging
from aiokafka import AIOKafkaProducer

from kafka_integration.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CLIENT_ID
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    """Запускает producer при старте приложения (один раз на процесс)."""
    global _producer
    if _producer is not None:
        return

    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id=KAFKA_CLIENT_ID,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        request_timeout_ms=15000,
    )
    await _producer.start()
    logger.info(
        "Kafka producer запущен: bootstrap=%s, client_id=%s",
        KAFKA_BOOTSTRAP_SERVERS,
        KAFKA_CLIENT_ID,
    )


async def stop_producer() -> None:
    """Останавливает producer при выключении приложения."""
    global _producer
    if _producer is None:
        return
    try:
        await _producer.stop()
        logger.info("Kafka producer остановлен")
    finally:
        _producer = None


async def send_event(topic: str, value: dict) -> None:
    """
    Отправляет событие в Kafka и ждёт подтверждения от брокера.
    Бросает RuntimeError, если producer не запущен.
    Бросает исключение Kafka при ошибке отправки (таймаут, недоступность).
    """
    if _producer is None:
        raise RuntimeError("Producer не запущен")
    try:
        metadata = await asyncio.wait_for(
            _producer.send_and_wait(topic, value=value),
            timeout=5.0,
        )
        logger.info(...)
    except asyncio.TimeoutError:
        logger.error("Таймаут отправки в Kafka (topic=%s)", topic)
        raise
    except Exception as e:
        logger.error("Ошибка отправки в Kafka (topic=%s): %s", topic, e)
        raise
