import time
import pytest
from unittest import mock
from stability_templates.patterns.timeout import (
    Timeout,
    TimeoutException,
    timeout_decorator
)


def test_timeout_fast_function():
    """Тест: швидка функція встигає"""
    mock_fn = mock.Mock(return_value="result")
    timeout = Timeout(mock_fn, timeout_seconds=2)

    result = timeout.call()
    assert result == "result"


def test_timeout_slow_function():
    """Тест: повільна функція перевищує ліміт"""

    def slow_fn():
        time.sleep(3)
        return "too late"

    timeout = Timeout(slow_fn, timeout_seconds=1)

    with pytest.raises(TimeoutException):
        timeout.call()


def test_timeout_decorator():
    """Тест: декоратор timeout"""

    @timeout_decorator(seconds=1)
    def fast_function():
        return "quick"

    @timeout_decorator(seconds=1)
    def slow_function():
        time.sleep(2)
        return "slow"

    assert fast_function() == "quick"

    with pytest.raises(TimeoutException):
        slow_function()


def test_timeout_with_server(server_url, mock_service):
    """Тест з повільним сервером"""
    from stability_templates.utils.http_client import make_request

    timeout_fast = Timeout(
        lambda: make_request(f"{server_url}/success", timeout=5.0),
        timeout_seconds=3
    )
    result = timeout_fast.call()
    assert result is not None

    timeout_slow = Timeout(
        lambda: make_request(f"{server_url}/slow?delay=5", timeout=10.0),
        timeout_seconds=2
    )

    with pytest.raises(TimeoutException):
        timeout_slow.call()
