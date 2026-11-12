# EightCount

Система учёта посещений для секций, кружков и учебных заведений. Заменяет ручной журнал: администратор отмечает приход ученика, система автоматически списывает занятие с абонемента.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.0+-E92063.svg)](https://docs.pydantic.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg)](https://www.postgresql.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Kafka UI](https://img.shields.io/badge/Kafka%20UI-provectuslabs-6A5ACD)](https://github.com/provectus/kafka-ui)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Содержание

- [О проекте](#о-проекте)
- [Стек](#стек)
- [Архитектура](#архитектура)
- [Формат событий](#формат-событий)
- [Установка](#установка)
- [Запуск](#запуск)
- [HTTP-коды](#http-коды)
- [Логирование](#логирование)
- [Соавторы](#соавторы)
- [Лицензия](#лицензия)

## О проекте

EightCount — REST API для автоматизации учёта посещений. Администратор секции отмечает приход ученика одной кнопкой, система проверяет баланс абонемента и списывает занятие. Больше не нужен бумажный журнал и ручной подсчёт.

### Проблема

- **Нет контроля баланса** — непонятно, кто и сколько должен заплатить.
- **Ошибки списания** — можно дважды списать или недобрать сумму.
- **Сложный отчёт в конце месяца** — всё сводится к ручному труду.

### Решение

- **Автоматическое списание** — не даст уйти в минус.
- **Единый баланс** — одна подписка на ученика.
- **История операций** — видно, кто и когда приходил.
- **Валидация данных** — мусор не попадёт в БД.
- **Асинхронная обработка** — запись в БД через Kafka, клиент не ждёт.

## Стек

| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.12 | Язык |
| FastAPI | 0.100+ | Веб-фреймворк |
| Pydantic | 2.0+ | Валидация данных |
| PostgreSQL | 16 | База данных |
| psycopg2 | latest | Драйвер PostgreSQL |
| aiokafka | latest | Асинхронный producer |
| kafka-python | latest | Синхронный consumer |
| Apache Kafka | latest | Брокер сообщений |
| Kafka UI | latest | Веб-интерфейс для Kafka |
| uvicorn | latest | ASGI-сервер |
| uv | latest | Управление зависимостями |
| logging | stdlib | Логирование |

## Архитектура

Проект построен по принципу слоистой архитектуры. Каждый слой знает только про своё.

### Синхронный путь (чтение)

`GET`-эндпоинты читают данные напрямую из БД, минуя Kafka.

```
Клиент (HTTP)
     |
     | JSON
     v
routes.py (FastAPI)
     |
     | вызовы service
     v
service.py
     |
     | вызовы repo
     v
postgres_repository.py
     |
     | SQL
     v
PostgreSQL 16
```

### Асинхронный путь (запись)

`POST`/`DELETE`-эндпоинты отправляют событие в Kafka и сразу отвечают `{"status": "queued"}`. Запись в БД выполняет consumer.

```
Клиент (HTTP)
     |
     | JSON
     v
routes.py (FastAPI)
     |
     | producer.send_event(topic, key, value, headers)
     v
producer.py (aiokafka)
     |
     | событие (key=event_id, headers=topic, value={action, data})
     v
Apache Kafka
     |
     | consumer.poll()
     v
consumer.py
     |
     | process_event(value, key, topic_from_headers)
     v
service.py
     |
     | вызовы repo
     v
postgres_repository.py
     |
     | SQL
     v
PostgreSQL 16
```

### Бэкенд БД

Проект работает на PostgreSQL. Подключение задаётся через переменные окружения:

| Переменная | Значение | Что используется |
|---|---|---|
| `DATABASE_URL` | DSN | Строка подключения для PostgreSQL |

Продакшен работает на PostgreSQL: там есть `ON DELETE CASCADE`, `FOR UPDATE` для блокировок и `ON CONFLICT ... DO UPDATE` для upsert-подписок. Это гарантирует защиту от гонок при параллельных запросах.

## Формат событий

События в Kafka имеют строгую структуру: **`event_id` → Key**, **`topic` → Headers**, **полезная нагрузка → Value**.

### Key

Уникальный идентификатор события (UUID). Используется для идемпотентности: consumer проверяет `processed_events` по `event_id` и пропускает дубли.

```
17b7eef9-b2be-49ae-905a-1d61e697f340
```

### Headers

Содержат имя топика, из которого пришло событие. Consumer читает `topic` из headers и по нему выбирает handler.

```
topic: checkin.events
```

### Value

Только полезная нагрузка: `action` и `data`. Без `event_id`, `topic`, `timestamp`.

```json
{
  "action": "checkin.processed",
  "data": {
    "owner": "Лёха5"
  }
}
```

### Примеры по топикам

**`student.events`** — создание/удаление ученика:

```json
{
  "action": "student.created",
  "data": {"name": "Лёха"}
}
```

```json
{
  "action": "student.deleted",
  "data": {"name": "Лёха"}
}
```

**`subscription.events`** — создание/удаление подписки:

```json
{
  "action": "subscription.created",
  "data": {"owner": "Лёха", "total_visits": 10}
}
```

```json
{
  "action": "subscription.deleted",
  "data": {"owner": "Лёха"}
}
```

**`checkin.events`** — списание занятия:

```json
{
  "action": "checkin.processed",
  "data": {"owner": "Лёха"}
}
```

## Установка

### Требования

- Python 3.10+
- pip или uv
- PostgreSQL 16

### Шаги

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Ads369/EightCount.git
cd EightCount

# 2. Создать виртуальное окружение
python -m venv venv

# 3. Активировать
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Установить зависимости
pip install fastapi uvicorn pydantic psycopg2-binary aiokafka kafka-python
```

Альтернатива — через `uv`:

```bash
uv sync
```

## Запуск

### Продакшен (Docker)

```bash
cp .env.example .env   # заполнить POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB
docker compose up -d --build
```

Сервис `web` соберётся из `Dockerfile`, дождётся healthcheck'а Postgres и поднимется на порту `8000`.

### Продакшен (без Docker)

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname \
KAFKA_BOOTSTRAP_SERVERS=localhost:9093 \
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Consumer (отдельный процесс)

Consumer запускается **отдельно** от FastAPI — на хосте или в отдельном контейнере. Он читает из Kafka и пишет в БД.

```bash
uv run python -m kafka_integration.consumer
```

### Интерактивная документация

- Swagger UI: http://127.0.0.1:8000/docs

### Kafka UI

- Kafka UI: http://127.0.0.1:8080

Позволяет просматривать топики, сообщения (Key, Headers, Value), consumer groups и lag.

## HTTP-коды

| Код | Когда |
|---|---|
| 200 | Успешный запрос |
| 400 | Неверное имя при удалении ученика |
| 404 | Ученик / подписка не найдены, занятия закончились |
| 409 | Ученик с таким именем уже существует |
| 500 | Ошибка БД |
| 502 | Не удалось отправить событие в Kafka |
| 503 | БД временно недоступна |

## Логирование

Проект использует стандартный модуль `logging`.

### Уровни

| Уровень | Когда |
|---|---|
| DEBUG | Поиск в БД, отладочная информация |
| INFO | Запросы, успешные операции, отправка событий |
| WARNING | Бизнес-ошибки (ученик не найден, занятия закончились) |
| ERROR | Ошибки БД, ошибки отправки в Kafka |

## Соавторы

- Alexandrov Dmitriy — [@Ads369](https://github.com/Ads369)
- Gerasimov Vladislav — [GerasimovDev-py](https://github.com/GerasimovDev-py)

## Лицензия

MIT License. См. [LICENSE](LICENSE).