import time
from unittest.mock import Mock

import pytest
from stability_templates.patterns.concurrency_templates.future import FutureResult


def test_future_success():
    """Тест: успішне виконання Future"""
    def slow_task():
        time.sleep(0.2)
        return "completed"

    future = FutureResult(slow_task).start()
    assert not future.is_ready()

    result = future.get(timeout=1)
    assert result == "completed"
    assert future.is_ready()


def test_future_timeout():
    """Тест: timeout при очікуванні"""
    def very_slow():
        time.sleep(5)
        return "too late"

    future = FutureResult(very_slow).start()

    with pytest.raises(TimeoutError):
        future.get(timeout=0.5)


def test_future_with_mock_async_operation():
    """Тест Future з мок-асинхронною операцією"""
    print("\n=== Future Mock Async Operation Test ===")

    # Імітуємо виклик зовнішнього API
    mock_api = Mock()
    mock_api.fetch_data = Mock(return_value={"user": "John", "age": 30})

    def async_api_call():
        print("  Calling mock API in background...")
        time.sleep(0.2)  # Імітація мережевої затримки
        result = mock_api.fetch_data()
        print(f"  Mock API returned: {result}")
        return result

    print("\nStarting Future with mock API...")
    future = FutureResult(async_api_call).start()

    print("Main thread is free to do other work...")
    time.sleep(0.1)

    result = future.get(timeout=1)

    print(f"\n✓ Mock API called: {mock_api.fetch_data.called}")
    print(f"✓ Call count: {mock_api.fetch_data.call_count}")
    print(f"✓ Result: {result}")

    assert mock_api.fetch_data.called
    assert result == {"user": "John", "age": 30}


def test_future_exception():
    """Тест: обробка виключень"""
    def failing_task():
        raise ValueError("Task failed")

    future = FutureResult(failing_task).start()

    with pytest.raises(ValueError):
        future.get()


def test_future_concurrency_proof():
    """
    Тест: Доказ того, що головний потік не заблокований
    і може виконувати обчислення, поки Future працює у фоні.
    """
    import time

    def heavy_background_task():
        time.sleep(1.0)  # Імітація важкого запиту до БД
        return 100

    start_time = time.perf_counter()
    future = FutureResult(heavy_background_task).start()


    main_thread_work_result = 0
    for i in range(5):
        time.sleep(0.1)  # Імітація роботи (рендеринг UI, інші розрахунки)
        main_thread_work_result += 10
        print(f"Main thread doing work... step {i + 1}")


    future_result = future.get()
    total_time = time.perf_counter() - start_time

    assert main_thread_work_result == 50

    assert future_result == 100


    print(f"\nTotal time: {total_time:.4f}s (Expected ~1.0s)")

    assert total_time < 1.4