import asyncio
import logging
import threading

from .log import CWMLog
from ..core.config import CodeWatchmanConfig

class MessageQueue:
    """
    Log Queue Manager for CodeWatchman. The class is responsible for managing the queue of logs and processing them.

    """
    def __init__(self, config: CodeWatchmanConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

        self.queue = asyncio.Queue(maxsize=config.max_size)

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def put(self, message: CWMLog):
        await self.queue.put(message)

    def enqueue(self, message: CWMLog):
        try:
            future = asyncio.run_coroutine_threadsafe(self.put(message), self.loop)
            future.result(timeout=1)
            self.logger.debug(f"Enqueued message: {message}")

        except Exception as e:
            self.logger.error(f"Error enqueuing message: {e}")

    @property
    def size(self):
        return self.queue.qsize()

    @property
    def is_empty(self):
        return self.queue.empty()

    @property
    def is_full(self):
        return self.queue.full()

    def clear(self):
        while not self.queue.empty():
            self.queue.get_nowait()

