import time
import logging
from threading import Timer

logger = logging.getLogger(__name__)


class Debounce:
    """
    Debounce pattern - відкладає виконання функції до закінчення періоду без нових викликів
    """
    def __init__(self, func, wait_time):
        self.func = func
        self.wait_time = wait_time
        self.timer = None
        self.last_result = None
        self.call_count = 0

    def call(self, *args, **kwargs):
        """Викликає функцію після wait_time секунд без нових викликів"""
        self.call_count += 1

        if self.timer:
            self.timer.cancel()
            logger.info(f"Cancelled previous timer. Total calls: {self.call_count}")

        def delayed_call():
            logger.info(f"Executing debounced function after {self.wait_time}s")
            self.last_result = self.func(*args, **kwargs)
            self.call_count = 0

        self.timer = Timer(self.wait_time, delayed_call)
        self.timer.start()

    def flush(self):
        """Примусово завершує таймер і повертає останній результат"""
        if self.timer:
            self.timer.cancel()
            self.timer.join()
        return self.last_result

    def cancel(self):
        """Скасовує очікуваний виклик"""
        if self.timer:
            self.timer.cancel()
            logger.info("Debounce cancelled")