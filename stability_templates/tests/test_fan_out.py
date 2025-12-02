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