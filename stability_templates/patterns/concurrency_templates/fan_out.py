import logging
from threading import Thread
from queue import Queue

logger = logging.getLogger(__name__)


class FanOut:
    """
    Fan-Out pattern - розподіляє одну задачу на декілька обробників
    Демультиплексор: один вхід → багато виходів
    """
    def __init__(self, handlers):
        self.handlers = handlers
        self.result_queue = Queue()

    def distribute(self, data):
        """Розподіляє дані між обробниками"""
        threads = []

        def worker(handler, handler_id, data):
            try:
                result = handler(data)
                self.result_queue.put((handler_id, result, None))
                logger.info(f"Handler {handler_id} processed data successfully")
            except Exception as e:
                self.result_queue.put((handler_id, None, e))
                logger.error(f"Handler {handler_id} failed: {e}")

        for idx, handler in enumerate(self.handlers):
            thread = Thread(target=worker, args=(handler, idx, data))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())

        logger.info(f"Fan-Out distributed to {len(self.handlers)} handlers")
        return results