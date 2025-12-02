import logging
from threading import Thread
from queue import Queue

logger = logging.getLogger(__name__)


class FanIn:
    """
    Fan-In pattern - об'єднує результати з декількох джерел в одне
    Мультиплексор: багато входів → один вихід
    """
    def __init__(self, sources):
        self.sources = sources
        self.result_queue = Queue()

    def collect(self, *args, **kwargs):
        """Збирає результати з усіх джерел"""
        threads = []

        def worker(source, source_id):
            try:
                result = source(*args, **kwargs)
                self.result_queue.put((source_id, result, None))
                logger.info(f"Source {source_id} completed successfully")
            except Exception as e:
                self.result_queue.put((source_id, None, e))
                logger.error(f"Source {source_id} failed: {e}")

        for idx, source in enumerate(self.sources):
            thread = Thread(target=worker, args=(source, idx))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())

        logger.info(f"Fan-In collected {len(results)} results from {len(self.sources)} sources")
        return results