import logging
from typing import Callable, List, Any
from threading import Thread
from queue import Queue

logger = logging.getLogger(__name__)


class Sharding:
    """
    Sharding pattern - розподіляє дані між декількома обробниками
    за ключем (hash-based distribution)
    """
    def __init__(self, handlers: List[Callable], hash_func: Callable = hash):
        self.handlers = handlers
        self.hash_func = hash_func
        self.num_shards = len(handlers)
        self.result_queue = Queue()

    def get_shard(self, key: Any) -> int:
        """Визначає shard за ключем"""
        return self.hash_func(key) % self.num_shards

    def process(self, items: List[tuple]):
        """
        Розподіляє items між shards і обробляє паралельно
        items: [(key, value), ...]
        """
        # Групуємо items за shards
        shards = {i: [] for i in range(self.num_shards)}
        for key, value in items:
            shard_id = self.get_shard(key)
            shards[shard_id].append((key, value))

        logger.info(f"Distributed {len(items)} items across {self.num_shards} shards")

        threads = []

        def worker(shard_id, handler, data):
            try:
                results = []
                for key, value in data:
                    result = handler(key, value)
                    results.append((key, result, None))

                self.result_queue.put((shard_id, results, None))
                logger.info(f"Shard {shard_id} processed {len(data)} items")
            except Exception as e:
                self.result_queue.put((shard_id, [], e))
                logger.error(f"Shard {shard_id} failed: {e}")

        for shard_id, data in shards.items():
            if data:
                thread = Thread(
                    target=worker,
                    args=(shard_id, self.handlers[shard_id], data)
                )
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

        all_results = []
        while not self.result_queue.empty():
            shard_id, results, error = self.result_queue.get()
            if error:
                logger.error(f"Shard {shard_id} error: {error}")
            all_results.extend(results)

        return all_results