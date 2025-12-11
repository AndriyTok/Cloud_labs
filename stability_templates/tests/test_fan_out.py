import pytest
from unittest import mock
from stability_templates.patterns.concurrency_templates.fan_out import FanOut


def test_fan_out_distribution():
    """Тест: розподіл даних між обробниками"""
    print("\n=== Fan-Out Distribution Test ===")
    results = []

    def handler1(data):
        print(f"  Handler 1 received: {data}")
        results.append(f"h1: {data}")
        return f"processed by handler1: {data}"

    def handler2(data):
        print(f"  Handler 2 received: {data}")
        results.append(f"h2: {data}")
        return f"processed by handler2: {data}"

    print("\nStarting Fan-Out distribution...")
    fan_out = FanOut([handler1, handler2])
    outputs = fan_out.distribute("test_data")

    print(f'\nAll handlers received: {results}')
    print(f'All outputs: {outputs}')
    print(f'\n✓ Total handlers executed: {len(outputs)}')
    print(f'✓ All data distributed: {len(results)} handlers processed the data')

    assert len(outputs) == 2
    assert len(results) == 2


from unittest.mock import Mock, patch

def test_fan_out_with_mock_http():
    """Тест Fan-Out з мок-HTTP запитами"""
    print("\n=== Fan-Out Mock HTTP Test ===")

    # Створюємо мок-функцію для HTTP-запитів
    mock_request = Mock()
    mock_request.side_effect = [
        {"status": "ok", "data": "response1"},
        {"status": "ok", "data": "response2"},
        {"status": "ok", "data": "response3"}
    ]

    def handler1(data):
        print(f"  Handler 1: calling API with {data}")
        return mock_request()

    def handler2(data):
        print(f"  Handler 2: calling API with {data}")
        return mock_request()

    def handler3(data):
        print(f"  Handler 3: calling API with {data}")
        return mock_request()

    print("\nStarting Fan-Out with mock HTTP...")
    fan_out = FanOut([handler1, handler2, handler3])
    results = fan_out.distribute("user_data")

    print(f"\n✓ Mock was called {mock_request.call_count} times")
    print(f"✓ Results: {[r[1] for r in results if r[2] is None]}")

    assert mock_request.call_count == 3
    assert len(results) == 3

def test_fan_out_performance_comparison():
    """
    Тест-порівняння: Послідовне виконання vs Fan-Out (Паралельне)
    """
    import time

    def slow_handler(data):
        time.sleep(0.5)
        return f"processed {data}"

    handlers = [slow_handler, slow_handler, slow_handler]
    test_data = "event_data"

    start_seq = time.perf_counter()

    results_seq = []
    for handler in handlers:
        results_seq.append(handler(test_data))

    duration_seq = time.perf_counter() - start_seq
    fan_out = FanOut(handlers)

    start_par = time.perf_counter()

    results_par = fan_out.distribute(test_data)
    duration_par = time.perf_counter() - start_par

    print(f"\n--- Fan-Out Performance Comparison ---")
    print(f"Sequential Duration: {duration_seq:.4f}s (Expected: ~1.5s)")
    print(f"Fan-Out Duration:    {duration_par:.4f}s (Expected: ~0.5s)")
    print(f"Speedup:             {duration_seq / duration_par:.2f}x faster")

    assert len(results_seq) == 3
    assert len(results_par) == 3

    assert duration_par < duration_seq