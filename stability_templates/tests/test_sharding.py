import pytest
from stability_templates.patterns.concurrency_templates.sharding import Sharding


def test_sharding_distribution():
    """Тест: розподіл даних між shards"""
    processed = {0: [], 1: [], 2: []}

    def handler0(key, value):
        processed[0].append((key, value))
        return f"shard0: {value}"

    def handler1(key, value):
        processed[1].append((key, value))
        return f"shard1: {value}"

    def handler2(key, value):
        processed[2].append((key, value))
        return f"shard2: {value}"

    sharding = Sharding([handler0, handler1, handler2])

    items = [
        ("user_1", "data1"),
        ("user_2", "data2"),
        ("user_3", "data3"),
        ("user_4", "data4"),
    ]

    results = sharding.process(items)
    assert len(results) == 4


def test_sharding_consistent_hashing():
    """Тест: консистентне хешування"""
    handlers = [lambda k, v: v for _ in range(3)]
    sharding = Sharding(handlers)

    shard1 = sharding.get_shard("test_key")
    shard2 = sharding.get_shard("test_key")

    assert shard1 == shard2