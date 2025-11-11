import time
import logging

logger = logging.getLogger(__name__)


class Retry:
    """
    Retry pattern - автоматично повторює виклик функції при помилках
    """
    def __init__(self, func, max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
        self.func = func
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
        self.attempt_count = 0

    def call(self, *args, **kwargs):
        """Виконує функцію з автоматичним повтором при помилках"""
        self.attempt_count = 0
        current_delay = self.delay

        while self.attempt_count < self.max_attempts:
            self.attempt_count += 1

            try:
                result = self.func(*args, **kwargs)
                logger.info(f"Success on attempt {self.attempt_count}/{self.max_attempts}")
                return result

            except self.exceptions as e:
                if self.attempt_count >= self.max_attempts:
                    logger.error(f"Failed after {self.attempt_count} attempts")
                    raise RetryExhausted(
                        f"Max retry attempts ({self.max_attempts}) exceeded"
                    ) from e

                logger.warning(
                    f"Attempt {self.attempt_count}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {current_delay}s..."
                )
                time.sleep(current_delay)
                current_delay *= self.backoff

    def reset(self):
        """Скидає лічильник спроб"""
        self.attempt_count = 0


class RetryExhausted(Exception):
    """Виключення, коли вичерпані всі спроби повтору"""
    pass