# EightCount

Система учёта посещений для секций, кружков и учебных заведений.
Заменяет ручной журнал: администратор отмечает приход ученика,
система автоматически списывает занятие с абонемента.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.0+-E92063.svg)](https://docs.pydantic.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Установка](#установка)
- [Запуск](#запуск)
- [API Reference](#api-reference)
- [Примеры запросов](#примеры-запросов)
- [HTTP-коды](#http-коды)
- [Логирование](#логирование)
- [Обработка ошибок](#обработка-ошибок)
- [Roadmap](#roadmap)
- [Соавторы](#соавторы)
- [Лицензия](#лицензия)

---

## О проекте

**EightCount** — REST API для автоматизации учёта посещений. Администратор
секции отмечает приход ученика одной кнопкой, система проверяет баланс
абонемента и списывает занятие. Больше не нужен бумажный журнал и ручной
подсчёт.

### Проблема

- Нет контроля баланса — непонятно, кто и сколько должен заплатить.
- Ошибки списания — можно дважды списать или недобрать сумму.
- Сложный отчёт в конце месяца — всё сводится к ручному труду.

### Решение

- Автоматическое списание — не даст уйти в минус.
- Единый баланс — одна подписка на ученика.
- История операций — видно, кто и когда приходил.
- Валидация данных — мусор не попадёт в БД.

---

## Возможности

| Функция | Описание | Статус |
|---|---|---|
| Учёт учеников | Создание, просмотр, удаление | Готово |
| Подписки | Создание и пополнение баланса | Готово |
| Списание занятий | Одна операция — минус одно занятие | Готово |
| Баланс ученика | Видно, сколько занятий осталось | Готово |
| Валидация | Pydantic-схемы для всех запросов | Готово |
| Логирование | Все операции пишутся в лог | Готово |
| Слоистая архитектура | domain / service / repo / routes | Готово |
| Обработка ошибок | Свои исключения + HTTP-коды | Готово |
| Отчёты | Список всех учеников с балансом | Готово |
| Тесты | Автоматические тесты | В планах |
| Аутентификация | JWT-токены для админов | В планах |
| Docker | Контейнеризация | В планах |

---

## Технологии

| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.12 | Язык |
| FastAPI | 0.100+ | Веб-фреймворк |
| Pydantic | 2.0+ | Валидация данных |
| SQLite | 3 | База данных |
| uvicorn | latest | ASGI-сервер |
| uv | latest | Управление зависимостями |
| logging | stdlib | Логирование |

---

## Архитектура

Проект построен по принципу слоистой архитектуры. Каждый слой знает
только про своё.

```
+-------------------------------------------------------------+
|                      Клиент (HTTP)                          |
+-----------------------------+-------------------------------+
                              | JSON
                              v
+-------------------------------------------------------------+
|                    routes.py (FastAPI)                      |
|  - HTTP-эндпоинты                                           |
|  - Валидация через Pydantic                                 |
|  - Преобразование исключений в HTTP-коды                    |
+-----------------------------+-------------------------------+
                              | вызовы service
                              v
+-------------------------------------------------------------+
|                       service.py                            |
|  - Бизнес-логика                                            |
|  - Проверки (ученик есть, подписка есть, баланс > 0)        |
|  - Логирование                                              |
|  - Бросает DomainError                                      |
+-----------------------------+-------------------------------+
                              | вызовы repo (StorageRepository)
                              v
+-------------------------------------------------------------+
|                  sql_repository.py                          |
|  - SQL-запросы                                              |
|  - Ловит sqlite3.Error, превращает в DBError                |
|  - Никакой бизнес-логики                                    |
+-----------------------------+-------------------------------+
                              | SQL
                              v
+-------------------------------------------------------------+
|                    SQLite (EightCount.db)                   |
|  - students (id, name)                                      |
|  - subscriptions (id, student_id, total_visits)             |
+-------------------------------------------------------------+
```

### Правила слоёв

| Слой | Знает про | НЕ знает про |
|---|---|---|
| routes | HTTP, JSON, Pydantic | SQL, бизнес-правила |
| service | Бизнес-правила, domain | HTTP, SQL |
| sql_repository | SQL, SQLite | HTTP, бизнес-правила |
| domain | Сущности | HTTP, SQL, БД |
| requests_dto / responses_dto | Pydantic, валидацию | SQL, БД |

---

## Структура проекта

```
EightCount/
├── domain.py                  # Сущности Student, Subscription + StorageRepository (Protocol)
├── exceptions.py              # DomainError, DBError и наследники
├── sql_repository.py          # Работа с SQLite: SQL, логирование, преобразование ошибок
├── service.py                 # Бизнес-логика: проверки, решения
├── requests_dto.py            # Request-схемы (Pydantic) для API
├── responses_dto.py           # Response-схемы (Pydantic) для API
├── app.py                     # Сборка зависимостей (Application)
├── routes.py                  # HTTP-эндпоинты
├── main.py                    # Точка входа (FastAPI + uvicorn)
├── demo.py                    # Локальная проверка сценариев
├── validators.py              # Создание Pydantic-моделей вручную (для demo)
├── test_subscription.py       # Тесты
├── pyproject.toml             # Метаданные проекта и зависимости
├── uv.lock                    # Зафиксированные версии зависимостей
├── .gitignore                 # Игнорируемые файлы
└── README.md
```

### Роли файлов

| Файл | Роль |
|---|---|
| domain.py | Что такое ученик и подписка. Плюс интерфейс StorageRepository |
| exceptions.py | Свои исключения. DomainError — родитель бизнес-ошибок |
| sql_repository.py | Единственное место с SQL. Ловит sqlite3.Error, превращает в DBError |
| service.py | Бизнес-логика. Не знает про HTTP и SQL |
| requests_dto.py | Pydantic-схемы запросов. Валидация входа |
| responses_dto.py | Pydantic-схемы ответов. Описание выхода |
| app.py | Сборка repo и service в Application |
| routes.py | HTTP-эндпоинты. Ловит DomainError, DBError, отдаёт HTTP-коды |
| main.py | Запуск приложения |
| demo.py | Локальная проверка без FastAPI |
| validators.py | Создание Pydantic-моделей вручную для demo |
| test_subscription.py | Тесты |
| pyproject.toml | Метаданные проекта и зависимости |
| uv.lock | Зафиксированные версии зависимостей |

### Request DTO и Response DTO

В проекте два файла с Pydantic-схемами, разделённые по направлению данных:

| | requests_dto.py | responses_dto.py |
|---|---|---|
| Зачем | Валидация входа API | Описание выхода API |
| Где используется | routes.py | routes.py |
| Направление | Клиент → Сервер | Сервер → Клиент |
| Технология | Pydantic BaseModel | Pydantic BaseModel |
| Валидация | Есть (Field) | Есть (типы) |

- requests_dto.py — что клиент присылает. Например, AddStudentRequest с полем name.
- responses_dto.py — что сервер отдаёт. Например, StudentResponse с полями id и name.

---

## Установка

### Требования

- Python 3.10+
- pip или uv

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
pip install fastapi uvicorn pydantic
```

### Альтернатива — через uv

```bash
uv sync
```

---

## Запуск

### Development

```bash
uvicorn main:app --reload
```

Сервер запустится на http://127.0.0.1:8000.

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Интерактивная документация

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## API Reference

### Base URL

```
http://127.0.0.1:8000
```

### Ученики

#### POST /students

Создать нового ученика.

**Request Body:**

```json
{
  "name": "Алексей"
}
```

**Ограничения:**

- name — строка, от 1 до 100 символов.

**Responses:**

| Код | Описание |
|---|---|
| 200 | Ученик создан |
| 409 | Ученик уже существует |
| 422 | Ошибка валидации |
| 500 | Ошибка БД |

**Пример ответа 200:**

```json
{
  "status": "Пользователь Алексей добавлен, id=1"
}
```

---

#### GET /students

Получить список учеников с балансом занятий.

**Responses:**

| Код | Описание |
|---|---|
| 200 | Список учеников |
| 500 | Ошибка БД |

**Пример ответа 200:**

```json
[
  {"id": 1, "name": "Алексей", "total_visits": 4},
  {"id": 2, "name": "Роман", "total_visits": 0}
]
```

---

#### DELETE /students/{name}

Удалить ученика и все его подписки.

**Path Parameters:**

| Параметр | Тип | Описание |
|---|---|---|
| name | string | Имя ученика |

**Responses:**

| Код | Описание |
|---|---|
| 200 | Ученик удалён |
| 404 | Ученик не найден |
| 500 | Ошибка БД |

---

### Подписки

#### POST /subscriptions

Создать подписку или пополнить существующую (upsert).

**Request Body:**

```json
{
  "owner": "Алексей",
  "total_visits": 5
}
```

**Ограничения:**

- owner — строка, от 1 до 100 символов.
- total_visits — целое, больше 0, не больше 1000.

**Поведение:**

- Если у ученика нет подписки — создаётся новая.
- Если есть — баланс прибавляется.

**Responses:**

| Код | Описание |
|---|---|
| 200 | Подписка создана/обновлена |
| 404 | Ученик не найден |
| 422 | Ошибка валидации |
| 500 | Ошибка БД |

**Пример ответа 200:**

```json
{
  "status": "Подписка для Алексей обновлена, id=1, +5 занятий"
}
```

---

#### GET /subscriptions

Получить список всех подписок.

**Responses:**

| Код | Описание |
|---|---|
| 200 | Список подписок |
| 500 | Ошибка БД |

**Пример ответа 200:**

```json
[
  {"id": 1, "owner": "Алексей", "total_visits": 4}
]
```

---

#### DELETE /subscriptions/{owner}

Удалить подписку ученика (ученик остаётся).

**Path Parameters:**

| Параметр | Тип | Описание |
|---|---|---|
| owner | string | Имя ученика |

**Responses:**

| Код | Описание |
|---|---|
| 200 | Подписка удалена |
| 404 | Ученик или подписка не найдена |
| 500 | Ошибка БД |

---

### Посещения

#### POST /check-in

Списать одно занятие у ученика.

**Request Body:**

```json
{
  "owner": "Алексей"
}
```

**Responses:**

| Код | Описание |
|---|---|
| 200 | Занятие списано |
| 402 | Занятия закончились |
| 404 | Ученик или подписка не найдена |
| 422 | Ошибка валидации |
| 500 | Ошибка БД |

**Пример ответа 200:**

```json
{
  "status": "ok",
  "message": "Алексей занятие списалось"
}
```

---

## Примеры запросов

### Создать ученика

```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Алексей"}'
```

### Пополнить подписку

```bash
curl -X POST http://127.0.0.1:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"owner": "Алексей", "total_visits": 5}'
```

### Списать занятие

```bash
curl -X POST http://127.0.0.1:8000/check-in \
  -H "Content-Type: application/json" \
  -d '{"owner": "Алексей"}'
```

### Получить список учеников

```bash
curl http://127.0.0.1:8000/students
```

### Удалить подписку

```bash
curl -X DELETE http://127.0.0.1:8000/subscriptions/Алексей
```

### Удалить ученика

```bash
curl -X DELETE http://127.0.0.1:8000/students/Алексей
```

---

## HTTP-коды

| Код | Название | Когда |
|---|---|---|
| 200 | OK | Успешная операция |
| 402 | Payment Required | Занятия закончились |
| 404 | Not Found | Ученик или подписка не найдена |
| 409 | Conflict | Ученик уже существует |
| 422 | Unprocessable Entity | Ошибка валидации (Pydantic) |
| 500 | Internal Server Error | Ошибка БД или неизвестная ошибка |

---

## Логирование

Проект использует стандартный модуль logging.

**Уровни:**

| Уровень | Когда |
|---|---|
| DEBUG | Поиск в БД, отладочная информация |
| INFO | Запросы, успешные операции |
| WARNING | Бизнес-ошибки (ученик не найден, занятия закончились) |
| ERROR | Ошибки БД |

**Формат:**

```
%(asctime)s [%(levelname)-8s] %(name)s: %(message)s
```

**Пример вывода:**

```
17:09:39 [INFO    ] service: Запрос на добавление: Алексей
17:09:39 [INFO    ] sql_repository: Поиск студента в БД: Алексей
17:09:39 [WARNING ] sql_repository: Ученик не найден в БД: Алексей
17:09:39 [INFO    ] service: Добавлен: Алексей id = 2
```

---

## Обработка ошибок

### Свои исключения

```
DomainError (базовое)
├── StudentNotFoundError      — ученик не найден
├── StudentAlreadyExistsError — ученик уже существует
├── SubscriptionNotFoundError — подписка не найдена
└── NoLessonsLeftError        — занятия закончились

DBError (отдельно)            — ошибка базы данных
```

### Где бросаются

| Исключение | Где бросается |
|---|---|
| StudentNotFoundError | service.add_subscription, service.check_in, service.remove_* |
| StudentAlreadyExistsError | service.add_student |
| SubscriptionNotFoundError | service.check_in, service.remove_subscription |
| NoLessonsLeftError | service.check_in |
| DBError | Все методы sql_repository |

### Где ловятся

- sql_repository — ловит sqlite3.Error, превращает в DBError.
- routes — ловит DomainError и DBError, превращает в HTTP-коды.

---

## Roadmap

- [x] Слоистая архитектура
- [x] Pydantic-валидация
- [x] Логирование
- [x] Свои исключения
- [x] CRUD для учеников
- [x] CRUD для подписок
- [x] Upsert для подписок
- [ ] Фикс database is locked
- [ ] Фикс FOREIGN KEY constraint failed при удалении
- [ ] Тесты (pytest)
- [ ] Миграции (Alembic)
- [ ] Docker + docker-compose
- [ ] Аутентификация (JWT)
- [ ] Роли (админ / ученик)
- [ ] Отчёты (за месяц, за период)

---

## Соавторы

- Alexandrov Dmitriy — [@Ads369](https://github.com/Ads369)
- Gerasimov Vladislav — [GerasimovDev-py](https://github.com/GerasimovDev-py)

---

## Лицензия

MIT License. См. [LICENSE](LICENSE).