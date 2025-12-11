import time
import pytest
from stability_templates.patterns.concurrency_templates.future import FutureResult


def test_future_success():
    """Тест: успішне виконання Future"""
    def slow_task():
        time.sleep(0.2)
        return "completed"

    future = FutureResult(slow_task).start()
    assert not future.is_ready()

    result = future.get(timeout=1)
    assert result == "completed"
    assert future.is_ready()


def test_future_timeout():
    """Тест: timeout при очікуванні"""
    def very_slow():
        time.sleep(5)
        return "too late"

    future = FutureResult(very_slow).start()

    with pytest.raises(TimeoutError):
        future.get(timeout=0.5)


def test_future_exception():
    """Тест: обробка виключень"""
    def failing_task():
        raise ValueError("Task failed")

    future = FutureResult(failing_task).start()

    with pytest.raises(ValueError):
        future.get()


def test_future_concurrency_proof():
    """
    Тест: Доказ того, що головний потік не заблокований
    і може виконувати обчислення, поки Future працює у фоні.
    """
    import time

    # 1. Задача для Future (Фон)
    def heavy_background_task():
        time.sleep(1.0)  # Імітація важкого запиту до БД
        return 100

    # 2. Запускаємо Future
    start_time = time.perf_counter()
    future = FutureResult(heavy_background_task).start()

    # 3. Поки Future спить, робимо роботу в головному потоці (Main Thread)
    # Якби start() був блокуючим, ми б не дійшли сюди, поки task не завершиться
    main_thread_work_result = 0
    for i in range(5):
        time.sleep(0.1)  # Імітація роботи (рендеринг UI, інші розрахунки)
        main_thread_work_result += 10
        print(f"Main thread doing work... step {i + 1}")

    # 4. Забираємо результат Future
    future_result = future.get()
    total_time = time.perf_counter() - start_time

    # ПЕРЕВІРКА:

    # Ми встигли зробити роботу в головному потоці (5 * 0.1s = 0.5s)
    assert main_thread_work_result == 50

    # Ми отримали результат з фону
    assert future_result == 100

    # ЗАГАЛЬНИЙ ЧАС:
    # Послідовно це зайняло б: 1.0s (background) + 0.5s (main) = 1.5s
    # Паралельно це зайняло: max(1.0, 0.5) ≈ 1.0s (+ overhead)
    print(f"\nTotal time: {total_time:.4f}s (Expected ~1.0s)")

    # Перевіряємо, що ми дійсно зекономили час (менше ніж послідовна сума)
    assert total_time < 1.4