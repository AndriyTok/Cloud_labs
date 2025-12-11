import pytest
from unittest import mock
from stability_templates.patterns.concurrency_templates.fan_out import FanOut


def test_fan_out_distribution():
    """Тест: розподіл даних між обробниками"""
    results = []

    def handler1(data):
        results.append(f"h1: {data}")
        return f"processed by handler1: {data}"

    def handler2(data):
        results.append(f"h2: {data}")
        return f"processed by handler2: {data}"

    fan_out = FanOut([handler1, handler2])
    outputs = fan_out.distribute("test_data")

    assert len(outputs) == 2
    assert len(results) == 2


def test_fan_out_with_failures():
    """Тест: обробка помилок в обробниках"""
    def good_handler(data):
        return f"processed: {data}"

    def bad_handler(data):
        raise Exception("Handler error")

    fan_out = FanOut([good_handler, bad_handler])
    results = fan_out.distribute("test")

    successes = [r for r in results if r[2] is None]
    failures = [r for r in results if r[2] is not None]

    assert len(successes) == 1
    assert len(failures) == 1


def test_fan_out_performance_comparison():
    """
    Тест-порівняння: Послідовне виконання vs Fan-Out (Паралельне)
    """
    import time

    # Функція, яка імітує довгу обробку (0.5 сек)
    def slow_handler(data):
        time.sleep(0.5)
        return f"processed {data}"

    # Створюємо 3 однакові "важкі" обробники
    handlers = [slow_handler, slow_handler, slow_handler]
    test_data = "event_data"

    # ---------------------------------------------------------
    # 1. Послідовне виконання (Sequential)
    # ---------------------------------------------------------
    start_seq = time.perf_counter()

    results_seq = []
    # У послідовному режимі ми викликаємо хендлери по черзі
    for handler in handlers:
        results_seq.append(handler(test_data))

    duration_seq = time.perf_counter() - start_seq

    # ---------------------------------------------------------
    # 2. Паралельне виконання (Fan-Out)
    # ---------------------------------------------------------
    fan_out = FanOut(handlers)

    start_par = time.perf_counter()
    # Fan-Out запускає їх одночасно в окремих потоках
    results_par = fan_out.distribute(test_data)
    duration_par = time.perf_counter() - start_par

    # ---------------------------------------------------------
    # 3. Вивід результатів та перевірка
    # ---------------------------------------------------------
    print(f"\n--- Fan-Out Performance Comparison ---")
    print(f"Sequential Duration: {duration_seq:.4f}s (Expected: ~1.5s)")
    print(f"Fan-Out Duration:    {duration_par:.4f}s (Expected: ~0.5s)")
    print(f"Speedup:             {duration_seq / duration_par:.2f}x faster")

    # Перевіряємо, що результати однакові (кількісно)
    assert len(results_seq) == 3
    assert len(results_par) == 3

    # Головна перевірка: Паралельне має бути швидшим за послідовне
    assert duration_par < duration_seq