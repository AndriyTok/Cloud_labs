import pytest
from stability_templates.patterns.concurrency_templates.sharding import Sharding


def test_sharding_distribution():
    """Тест: розподіл даних між shards"""
    print("\n=== Sharding Distribution Test ===")
    processed = {0: [], 1: [], 2: []}

    def handler0(key, value):
        print(f"  Shard 0 processing: {key} -> {value}")
        processed[0].append((key, value))
        return f"shard0: {value}"

    def handler1(key, value):
        print(f"  Shard 1 processing: {key} -> {value}")
        processed[1].append((key, value))
        return f"shard1: {value}"

    def handler2(key, value):
        print(f"  Shard 2 processing: {key} -> {value}")
        processed[2].append((key, value))
        return f"shard2: {value}"

    print("\nInitializing Sharding with 3 shards...")
    sharding = Sharding([handler0, handler1, handler2])

    items = [
        ("user_1", "data1"),
        ("user_2", "data2"),
        ("user_3", "data3"),
        ("user_4", "data4"),
    ]

    print(f"\nProcessing {len(items)} items...")
    for key, value in items:
        shard_id = sharding.get_shard(key)
        print(f"  {key} -> Shard {shard_id}")

    results = sharding.process(items)

    print(f"\n✓ Results: {results}")
    print(f"\n--- Distribution Summary ---")
    for shard_id, items_list in processed.items():
        print(f"Shard {shard_id}: {len(items_list)} items - {items_list}")
    print(f"✓ Total processed: {len(results)}/4 items")

    assert len(results) == 4


def test_sharding_consistent_hashing():
    """Тест: консистентне хешування"""
    print("\n=== Sharding Consistent Hashing Test ===")
    handlers = [lambda k, v: v for _ in range(3)]
    sharding = Sharding(handlers)

    test_key = "test_key"
    print(f"\nTesting key: '{test_key}'")

    shard1 = sharding.get_shard(test_key)
    print(f"  First call -> Shard {shard1}")

    shard2 = sharding.get_shard(test_key)
    print(f"  Second call -> Shard {shard2}")

    print(f"\n✓ Consistent: {shard1 == shard2}")
    print(f"✓ Same key always maps to Shard {shard1}")

    assert shard1 == shard2




def test_sharding_performance_comparison():
    """
    Тест-порівняння: Обробка в одному потоці vs Шардінг (4 потоки)
    """
    import time

    print("\n=== Sharding Performance Comparison ===")

    items = [(f"user_{i}", f"data_{i}") for i in range(20)]
    print(f"\nItems count: {len(items)}")
    print(f"Processing time per item: 0.1s")

    def slow_process(key, value):
        time.sleep(0.1)
        return f"processed {key}"

    # Послідовна обробка
    print("\n--- Single Thread Execution ---")
    start_seq = time.perf_counter()

    results_seq = []
    for i, (key, value) in enumerate(items, 1):
        if i % 5 == 0:
            print(f"  Processed {i}/{len(items)} items...")
        results_seq.append(slow_process(key, value))

    duration_seq = time.perf_counter() - start_seq
    print(f"✓ Single thread completed in {duration_seq:.4f}s")

    # Шардінг (4 потоки)
    print("\n--- Sharded (4 threads) Execution ---")
    handlers = [slow_process, slow_process, slow_process, slow_process]
    sharding = Sharding(handlers)

    start_shard = time.perf_counter()
    print("  All shards started in parallel...")
    results_shard = sharding.process(items)
    duration_shard = time.perf_counter() - start_shard
    print(f"✓ Sharded execution completed in {duration_shard:.4f}s")

    speedup = duration_seq / duration_shard

    print(f"\n--- Performance Summary ---")
    print(f"Single Thread Time: {duration_seq:.4f}s (Expected: ~2.0s)")
    print(f"Sharded (4x) Time:  {duration_shard:.4f}s (Expected: ~0.5s)")
    print(f"Speedup:            {speedup:.2f}x faster")
    print(f"✓ Efficiency gain: {((duration_seq - duration_shard) / duration_seq * 100):.1f}%")

    assert len(results_seq) == 20
    assert len(results_shard) == 20
    assert speedup > 2.0
