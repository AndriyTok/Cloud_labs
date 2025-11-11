import time
import pytest
from unittest import mock
from stability_templates.patterns.throttle import Throttle, ThrottledException


def test_throttle_allows_limited_calls():
    """Тест: дозволяє обмежену кількість викликів"""
    mock_fn = mock.Mock(return_value="success")
    throttle = Throttle(mock_fn, calls_per_period=3, period=1.0)

    for i in range(3):
        throttle.call()

    with pytest.raises(ThrottledException):
        throttle.call()


def test_throttle_resets_after_period():
    """Тест: скидається після періоду"""
    mock_fn = mock.Mock(return_value="success")
    throttle = Throttle(mock_fn, calls_per_period=2, period=0.5)

    throttle.call()
    throttle.call()

    with pytest.raises(ThrottledException):
        throttle.call()

    time.sleep(0.6)

    throttle.call()
    assert mock_fn.call_count == 3


def test_throttle_remaining_calls():
    """Тест: підрахунок доступних викликів"""
    mock_fn = mock.Mock()
    throttle = Throttle(mock_fn, calls_per_period=5, period=1.0)

    assert throttle.get_remaining_calls() == 5

    throttle.call()
    assert throttle.get_remaining_calls() == 4


def test_throttle_with_server(server_url, mock_service):
    """Тест з реальним сервером"""
    from stability_templates.utils.http_client import make_request

    throttle = Throttle(
        lambda: make_request(f"{server_url}/counter"),
        calls_per_period=3,
        period=1.0
    )

    success_count = 0
    for i in range(5):
        try:
            throttle.call()
            success_count += 1
        except ThrottledException:
            pass

    assert success_count == 3
