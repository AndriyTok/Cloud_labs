import logging
from threading import Thread, Event
from typing import Optional, Any

logger = logging.getLogger(__name__)


class FutureResult:
    """
    Future pattern - представляє результат асинхронної операції
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._result = None
        self._exception = None
        self._ready = Event()
        self._thread = None

    def start(self):
        """Запускає асинхронне виконання"""
        def worker():
            try:
                self._result = self.func(*self.args, **self.kwargs)
                logger.info("Future completed successfully")
            except Exception as e:
                self._exception = e
                logger.error(f"Future failed: {e}")
            finally:
                self._ready.set()

        self._thread = Thread(target=worker)
        self._thread.start()
        return self

    def get(self, timeout: Optional[float] = None) -> Any:
        """Очікує завершення і повертає результат"""
        if not self._ready.wait(timeout=timeout):
            raise TimeoutError(f"Future did not complete within {timeout}s")

        if self._exception:
            raise self._exception

        return self._result

    def is_ready(self) -> bool:
        """Перевіряє чи готовий результат"""
        return self._ready.is_set()

    def cancel(self):
        """Скасовує виконання (якщо ще не почалося)"""
        if not self.is_ready():
            logger.warning("Future cannot be cancelled after starting")