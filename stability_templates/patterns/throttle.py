import time
import logging

logger = logging.getLogger(__name__)


class ThrottledException(Exception):
    """Виключення при перевищенні ліміту викликів"""
    pass


class Throttle:
    """
    Throttle pattern - обмежує кількість викликів функції за період часу
    """
    def __init__(self, func, calls_per_period, period=1.0):
        self.func = func
        self.calls_per_period = calls_per_period
        self.period = period
        self.call_times = []

    def call(self, *args, **kwargs):
        """Виконує функцію з обмеженням по частоті викликів"""
        current_time = time.time()

        # Видаляємо старі відмітки часу
        self.call_times = [
            t for t in self.call_times
            if current_time - t < self.period
        ]

        if len(self.call_times) >= self.calls_per_period:
            wait_time = self.period - (current_time - self.call_times[0])
            logger.warning(
                f"Throttled: {len(self.call_times)}/{self.calls_per_period} "
                f"calls in {self.period}s. Wait {wait_time:.2f}s"
            )
            raise ThrottledException(
                f"Rate limit exceeded: {self.calls_per_period} calls per {self.period}s. "
                f"Retry after {wait_time:.2f}s"
            )

        self.call_times.append(current_time)
        logger.info(
            f"Call allowed: {len(self.call_times)}/{self.calls_per_period} "
            f"in current period"
        )
        return self.func(*args, **kwargs)

    def reset(self):
        """Скидає історію викликів"""
        self.call_times = []
        logger.info("Throttle reset")

    def get_remaining_calls(self):
        """Повертає кількість доступних викликів"""
        current_time = time.time()
        self.call_times = [
            t for t in self.call_times
            if current_time - t < self.period
        ]
        return self.calls_per_period - len(self.call_times)