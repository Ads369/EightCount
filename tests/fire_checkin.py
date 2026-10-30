"""Демо: N параллельных check-in запросов к одному ученику.

Показывает, что происходит, когда несколько процессов (или потоков)
одновременно списывают занятия с одного абонемента.

Как запустить:

    1. Подготовить ученика с балансом 1:
       curl -X POST http://127.0.0.1:8000/students \
            -H 'Content-Type: application/json' -d '{"name":"Алексей"}'
       curl -X POST http://127.0.0.1:8000/subscriptions \
            -H 'Content-Type: application/json' -d '{"owner":"Алексей","total_visits":1}'

    2. Запустить сервер с несколькими процессами и расширенным окном гонки:
       CHECK_IN_DELAY=0.5 uvicorn main:app --workers 4

    3. Пустить параллельные запросы:
       python fire_checkin.py

Ожидание ДО фикса: все запросы вернут 200, но баланс станет 0
(одно занятие списалось, остальные прошли "бесплатно").
Ожидание ПОСЛЕ фикса: ровно один 200, остальные — ошибка.
"""
import argparse
import concurrent.futures
import json
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8000/check-in"


def one_check_in(base_url: str, owner: str):
    data = json.dumps({"owner": owner}).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="Алексей")
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.count) as pool:
        results = list(
            pool.map(lambda _: one_check_in(args.url, args.owner), range(args.count))
        )

    ok = sum(1 for status, _ in results if status == 200)
    print(f"Запросов: {args.count}, успешных списаний: {ok}")
    for i, (status, body) in enumerate(results, start=1):
        print(f"  #{i}: HTTP {status} {body}")


if __name__ == "__main__":
    main()
