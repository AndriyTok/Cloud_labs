import time
import pytest
from unittest import mock
from stability_templates.patterns.concurrency_templates.fan_in import FanIn


def test_fan_in_multiple_sources():
    """Тест: збір результатів з декількох джерел"""
    print("\n=== Fan-In Multiple Sources Test ===")

    def source1():
        print("  Source 1 started...")
        time.sleep(0.1)
        print("  Source 1 completed!")
        return "result1"

    def source2():
        print("  Source 2 started...")
        time.sleep(0.2)
        print("  Source 2 completed!")
        return "result2"

    def source3():
        print("  Source 3 started...")
        time.sleep(0.1)
        print("  Source 3 completed!")
        return "result3"

    print("\nStarting Fan-In collection from 3 sources...")
    fan_in = FanIn([source1, source2, source3])
    results = fan_in.collect()

    success_results = [r[1] for r in results if r[2] is None]
    print(f'\n✓ Raw results (source_id, result, error): {results}')
    print(f'✓ Success results: {success_results}')
    print(f'✓ Total sources collected: {len(results)}/3')

    assert len(results) == 3
    assert "result1" in success_results
    assert "result2" in success_results


def test_fan_in_with_server(server_url, mock_service):
    """Тест з реальними HTTP запитами"""
    print("\n=== Fan-In HTTP Requests Test ===")
    from stability_templates.utils.http_client import make_request

    print(f"\nServer URL: {server_url}")

    sources = [
        lambda: make_request(f"{server_url}/success"),
        lambda: make_request(f"{server_url}/counter"),
        lambda: make_request(f"{server_url}/success")
    ]

    print(f"Sources to call: {len(sources)}")
    print("  - /success")
    print("  - /counter")
    print("  - /success")

    fan_in = FanIn(sources)
    print("\nCollecting results from all sources...")
    results = fan_in.collect()

    print(f'\n✓ Fan-In HTTP Results: {results}')
    print(f'✓ Total responses: {len(results)}/3')

    assert len(results) == 3


def test_fan_in_performance_comparison():
    """
    Тест-порівняння: Послідовне виконання vs Fan-In (Паралельне)
    """
    import time

    print("\n=== Fan-In Performance Comparison ===")

    def slow_task():
        time.sleep(0.5)
        return "done"

    tasks_count = 3
    print(f"\nTask count: {tasks_count}")
    print(f"Each task duration: 0.5s")

    # Послідовне виконання
    print("\n--- Sequential Execution ---")
    start_seq = time.perf_counter()

    results_seq = []
    for i in range(tasks_count):
        print(f"  Executing task {i+1}/{tasks_count}...")
        results_seq.append(slow_task())

    duration_seq = time.perf_counter() - start_seq
    print(f"✓ Sequential completed in {duration_seq:.4f}s")

    # Fan-In (паралельне)
    print("\n--- Fan-In Parallel Execution ---")
    sources = [slow_task] * tasks_count
    fan_in = FanIn(sources)

    start_par = time.perf_counter()
    print("  All tasks started in parallel...")
    results_par = fan_in.collect()
    duration_par = time.perf_counter() - start_par
    print(f"✓ Fan-In completed in {duration_par:.4f}s")

    print(f"\n--- Performance Summary ---")
    print(f"Sequential Duration: {duration_seq:.4f}s (Expected: ~{0.5 * tasks_count}s)")
    print(f"Fan-In Duration:     {duration_par:.4f}s (Expected: ~0.5s)")
    print(f"Speedup:             {duration_seq / duration_par:.2f}x faster")
    print(f"✓ Efficiency gain: {((duration_seq - duration_par) / duration_seq * 100):.1f}%")

    assert len(results_seq) == tasks_count
    assert len(results_par) == tasks_count
    assert duration_par < duration_seq