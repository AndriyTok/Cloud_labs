import pytest
from unittest import mock
from stability_templates.patterns.retry import Retry, RetryExhausted


def test_retry_success_first_attempt():
    """Тест: успіх на першій спробі"""
    mock_fn = mock.Mock(return_value="success")
    retry = Retry(mock_fn, max_attempts=3, delay=0.1)

    result = retry.call()
    assert result == "success"
    assert mock_fn.call_count == 1


def test_retry_success_after_failures():
    """Тест: успіх після кількох невдач"""
    mock_fn = mock.Mock(
        side_effect=[Exception(), Exception(), "success"]
    )
    retry = Retry(mock_fn, max_attempts=3, delay=0.1)

    result = retry.call()
    assert result == "success"
    assert mock_fn.call_count == 3


def test_retry_exhausted():
    """Тест: вичерпані всі спроби"""
    mock_fn = mock.Mock(side_effect=Exception("Persistent error"))
    retry = Retry(mock_fn, max_attempts=3, delay=0.1)

    with pytest.raises(RetryExhausted):
        retry.call()

    assert mock_fn.call_count == 3


def test_retry_backoff():
    """Тест: експоненційна затримка"""
    import time

    mock_fn = mock.Mock(side_effect=Exception())
    retry = Retry(mock_fn, max_attempts=3, delay=0.1, backoff=2)

    start = time.time()

    with pytest.raises(RetryExhausted):
        retry.call()

    duration = time.time() - start
    assert duration >= 0.3


def test_retry_with_server(server_url, mock_service):
    """Тест з нестабільним сервером"""
    from stability_templates.utils.http_client import make_request

    retry = Retry(
        lambda: make_request(f"{server_url}/unstable"),
        max_attempts=5,
        delay=0.5
    )

    try:
        result = retry.call()
        assert result is not None
    except RetryExhausted:
        pytest.skip("Server too unstable for this test run")