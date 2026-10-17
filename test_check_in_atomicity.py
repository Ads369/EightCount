import concurrent.futures

from app import Application
from exceptions import NoLessionsLeftError


def test_check_in_spends_exactly_once_under_concurrency(tmp_path, monkeypatch):
    """При балансе 1 из N одновременных списаний проходит ровно одно.

    CHECK_IN_DELAY специально расширяет окно гонки, чтобы потоки
    действительно накладывались друг на друга. Атомарность списания
    должна удержать баланс в корректном состоянии: одно успешное
    списание, остальные — NoLessionsLeftError, баланс 0.
    """
    monkeypatch.setenv("CHECK_IN_DELAY", "0.05")
    service = Application(str(tmp_path / "test.db")).service

    service.add_student("Алексей")
    service.add_subscription("Алексей", 1)

    successes: list = []
    no_lessons: list = []
    unexpected: list = []

    def attempt():
        try:
            service.check_in("Алексей")
            successes.append(1)
        except NoLessionsLeftError:
            no_lessons.append(1)
        except Exception as exc:  # noqa: BLE001 - фиксируем всё неожиданное
            unexpected.append(repr(exc))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: attempt(), range(8)))

    assert len(successes) == 1, f"успешных списаний должно быть 1, а не {len(successes)}"
    assert len(no_lessons) == 7, f"отказов должно быть 7, а не {len(no_lessons)}"
    assert unexpected == [], f"неожиданные ошибки: {unexpected}"

    subs = service.get_all_subscription()
    assert subs[0]["total_visits"] == 0
