import time
import pytest
from unittest import mock
from stability_templates.patterns.debounce import Debounce


def test_debounce_delays_execution():
    """Тест: debounce відкладає виконання"""
    mock_fn = mock.Mock(return_value="result")
    debounce = Debounce(mock_fn, wait_time=0.5)

    debounce.call("arg1")
    assert mock_fn.call_count == 0  # Ще не викликано

    time.sleep(0.6)
    assert mock_fn.call_count == 1


def test_debounce_cancels_previous():
    """Тест: швидкі виклики скасовують попередні"""
    mock_fn = mock.Mock(return_value="result")
    debounce = Debounce(mock_fn, wait_time=0.3)

    for i in range(5):
        debounce.call(i)
        time.sleep(0.1)

    time.sleep(0.4)
    assert mock_fn.call_count == 1
    mock_fn.assert_called_with(4)


def test_debounce_flush():
    """Тест: flush примусово завершує виконання"""
    mock_fn = mock.Mock(return_value="result")
    debounce = Debounce(mock_fn, wait_time=2.0)

    debounce.call("test")
    result = debounce.flush()

    assert result is None


def test_debounce_with_server(server_url, mock_service):
    """Тест з реальним сервером"""
    from stability_templates.utils.http_client import make_request

    debounce = Debounce(
        lambda: make_request(f"{server_url}/counter"),
        wait_time=0.5
    )

    for _ in range(5):
        debounce.call()
        time.sleep(0.1)

    time.sleep(0.6)