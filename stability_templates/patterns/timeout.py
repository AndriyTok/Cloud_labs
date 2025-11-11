import signal
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Виключення при перевищенні часу виконання"""
    pass


class Timeout:
    """
    Timeout pattern - обмежує максимальний час виконання функції
    """
    def __init__(self, func, timeout_seconds):
        self.func = func
        self.timeout_seconds = timeout_seconds

    def call(self, *args, **kwargs):
        """Виконує функцію з обмеженням часу виконання"""
        def timeout_handler(signum, frame):
            logger.error(f"Timeout: function exceeded {self.timeout_seconds}s")
            raise TimeoutException(
                f"Function execution exceeded {self.timeout_seconds}s timeout"
            )

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)

        try:
            result = self.func(*args, **kwargs)
            signal.alarm(0)  # Скасовуємо alarm
            logger.info(f"Function completed within {self.timeout_seconds}s timeout")
            return result
        except TimeoutException:
            raise
        finally:
            signal.signal(signal.SIGALRM, old_handler)


def timeout_decorator(seconds):
    """Декоратор для додавання timeout до функції"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timeout = Timeout(func, seconds)
            return timeout.call(*args, **kwargs)
        return wrapper
    return decorator