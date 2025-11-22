import logging
import signal
from threading import Thread
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


class Timeout:
    """
    Timeout pattern - обмежує максимальний час виконання функції
    """

    def __init__(self, func, timeout_seconds):
        self.func = func
        self.timeout_seconds = timeout_seconds

    def call(self, *args, **kwargs):
        """Виконує функцію з обмеженням часу"""
        result_queue = Queue()
        exception_queue = Queue()

        def worker():
            try:
                result = self.func(*args, **kwargs)
                result_queue.put(result)
            except Exception as e:
                exception_queue.put(e)

        thread = Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_seconds)

        # Перевіряємо чи потік завершився
        if thread.is_alive():
            logger.warning(f"Timeout after {self.timeout_seconds}s")
            raise TimeoutException(f"Operation timed out after {self.timeout_seconds}s")

        # Перевіряємо виключення
        if not exception_queue.empty():
            e = exception_queue.get()
            logger.error(f"Function raised exception: {e}")
            raise e

        # Повертаємо результат
        if not result_queue.empty():
            result = result_queue.get()
            logger.info(f"Completed within {self.timeout_seconds}s timeout")
            return result

        raise TimeoutException("No result returned")
