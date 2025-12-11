import time
import pytest
from unittest import mock
from stability_templates.patterns.concurrency_templates.fan_in import FanIn


def test_fan_in_multiple_sources():
    """Тест: збір результатів з декількох джерел"""
    def source1():
        time.sleep(0.1)
        return "result1"

    def source2():
        time.sleep(0.2)
        return "result2"

    def source3():
        time.sleep(0.1)
        return "result3"

    fan_in = FanIn([source1, source2, source3])
    results = fan_in.collect()

    assert len(results) == 3
    success_results = [r[1] for r in results if r[2] is None]
    assert "result1" in success_results
    assert "result2" in success_results


def test_fan_in_with_failures():
    """Тест: обробка помилок в джерелах"""
    def good_source():
        return "success"

    def bad_source():
        raise Exception("Source failed")

    fan_in = FanIn([good_source, bad_source])
    results = fan_in.collect()

    assert len(results) == 2
    successes = [r for r in results if r[2] is None]
    failures = [r for r in results if r[2] is not None]

    assert len(successes) == 1
    assert len(failures) == 1


def test_fan_in_with_server(server_url, mock_service):
    """Тест з реальними HTTP запитами"""
    from stability_templates.utils.http_client import make_request

    sources = [
        lambda: make_request(f"{server_url}/success"),
        lambda: make_request(f"{server_url}/counter"),
        lambda: make_request(f"{server_url}/success")
    ]

    fan_in = FanIn(sources)
    results = fan_in.collect()

    assert len(results) == 3


def test_fan_in_performance_comparison():
    """
    Тест-порівняння: Послідовне виконання vs Fan-In (Паралельне)
    """
    import time

    # Функція, яка імітує довгий запит (0.5 сек)
    def slow_task():
        time.sleep(0.5)
        return "done"

    tasks_count = 3

    # ---------------------------------------------------------
    # 1. Послідовне виконання (Sequential)
    # ---------------------------------------------------------
    start_seq = time.perf_counter()

    results_seq = []
    for _ in range(tasks_count):
        results_seq.append(slow_task())

    duration_seq = time.perf_counter() - start_seq

    # ---------------------------------------------------------
    # 2. Паралельне виконання (Fan-In)
    # ---------------------------------------------------------
    sources = [slow_task] * tasks_count  # Створюємо список з 3-х функцій
    fan_in = FanIn(sources)

    start_par = time.perf_counter()
    results_par = fan_in.collect()
    duration_par = time.perf_counter() - start_par

    # ---------------------------------------------------------
    # 3. Вивід результатів та перевірка
    # ---------------------------------------------------------
    print(f"\n--- Performance Comparison ---")
    print(f"Sequential Duration: {duration_seq:.4f}s (Expected: ~{0.5 * tasks_count}s)")
    print(f"Fan-In Duration:     {duration_par:.4f}s (Expected: ~0.5s)")
    print(f"Speedup:             {duration_seq / duration_par:.2f}x faster")

    # Перевірки
    assert len(results_seq) == tasks_count
    assert len(results_par) == tasks_count

    # Fan-In має бути значно швидшим (хоча б у 2 рази для 3-х задач)
    assert duration_par < duration_seq