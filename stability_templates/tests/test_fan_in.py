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