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


def test_sharding_performance_comparison():
    """
    Тест-порівняння: Обробка в одному потоці vs Шардінг (4 потоки)
    """
    import time

    # 1. Підготовка даних
    # 20 елементів. Кожен обробляється 0.1 сек.
    items = [(f"user_{i}", f"data_{i}") for i in range(20)]

    def slow_process(key, value):
        time.sleep(0.1)
        return f"processed {key}"

    # ---------------------------------------------------------
    # Сценарій А: Без шардінгу (Послідовно)
    # ---------------------------------------------------------
    start_seq = time.perf_counter()

    results_seq = []
    for key, value in items:
        results_seq.append(slow_process(key, value))

    duration_seq = time.perf_counter() - start_seq

    # ---------------------------------------------------------
    # Сценарій Б: Шардінг (4 шарди / потоки)
    # ---------------------------------------------------------
    # Створюємо 4 однакових обробники (імітуємо 4 сервери)
    handlers = [slow_process, slow_process, slow_process, slow_process]
    sharding = Sharding(handlers)

    start_shard = time.perf_counter()
    results_shard = sharding.process(items)
    duration_shard = time.perf_counter() - start_shard

    # ---------------------------------------------------------
    # Результати
    # ---------------------------------------------------------
    print(f"\n--- Sharding Performance ---")
    print(f"Items count: {len(items)}")
    print(f"Single Thread Time: {duration_seq:.4f}s (Expected: ~2.0s)")
    print(f"Sharded (4x) Time:  {duration_shard:.4f}s (Expected: ~0.5s)")

    # Speedup = У скільки разів швидше
    speedup = duration_seq / duration_shard
    print(f"Speedup:            {speedup:.2f}x faster")

    # Перевірки
    assert len(results_seq) == 20
    assert len(results_shard) == 20

    assert speedup > 2.0