import time
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


def test_future_exception():
    """Тест: обробка виключень"""
    def failing_task():
        raise ValueError("Task failed")

    future = FutureResult(failing_task).start()

    with pytest.raises(ValueError):
        future.get()