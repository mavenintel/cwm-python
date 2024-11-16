import asyncio
import logging
import threading
from typing import List

from .log import CWMLog
from ..handlers import WebSocketHandler
from ..core.config import CodeWatchmanConfig

class MessageQueue:
    """
    Log Queue Manager for CodeWatchman. The class is responsible for managing the queue of logs and processing them.

    """
    def __init__(self, config: CodeWatchmanConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

        self.queue = asyncio.Queue(maxsize=config.max_size)
        self.websocket = WebSocketHandler(config, logger)

        self.loop = asyncio.new_event_loop()
        self.shutdown_event = asyncio.Event()
        self.consume_task = None
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.consume_task = self.loop.create_task(self.consume())
        self.loop.run_forever()

    async def process_batch(self, batch: List[CWMLog]):
        """
        Processes a batch of messages.
        """
        try:
            # Assuming you have a method in WebSocketHandler to send a batch
            await self.websocket.send(batch)
            self.logger.debug(f"Processed batch of {len(batch)} messages.")
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")

    async def consume(self):
        """
        Consumes data from the queue either when the batch size is reached
        or at regular time intervals.
        """
        batch = []
        start_time = asyncio.get_event_loop().time()

        try:
            while not self.shutdown_event.is_set():
                try:
                    # Calculate the remaining time until the next interval
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    time_remaining = max(0, self.config.process_interval - elapsed_time)

                    # Wait for a message from the queue with a timeout
                    message = await asyncio.wait_for(self.queue.get(), timeout=time_remaining)
                    batch.append(message)

                    # If batch size is reached, process the batch
                    if len(batch) >= self.config.batch_size:
                        await self.process_batch(batch)
                        batch = []
                        start_time = asyncio.get_event_loop().time()

                except asyncio.TimeoutError:
                    # Timeout occurred, process the batch if it's not empty
                    if batch:
                        await self.process_batch(batch)
                        batch = []
                    start_time = asyncio.get_event_loop().time()

            # Process any remaining messages in the queue
            while not self.queue.empty():
                try:
                    message = self.queue.get_nowait()
                    batch.append(message)
                    if len(batch) >= self.config.batch_size:
                        await self.process_batch(batch)
                        batch = []
                except asyncio.QueueEmpty:
                    break

            # Process final batch if any
            if batch:
                await self.process_batch(batch)

        except Exception as e:
            self.logger.error(f"Error in consume task: {e}")
            raise
        finally:
            self.logger.debug("Consume task completed.")

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

    async def _shutdown(self):
        self.shutdown_event.set()
        if self.consume_task:
            print("Waiting for consume task to finish")
            await self.consume_task  # Wait for the consume coroutine to finish
        self.logger.debug("Shutdown complete.")
        return True

    def shutdown(self):
        """
        Signals the consume coroutine to exit and waits for it to finish.
        """
        if self.consume_task:
            future = asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)
            try:
                future.result(timeout=self.config.shutdown_timeout)
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")

            # Stop the event loop safely from outside the loop
            self.loop.call_soon_threadsafe(self.loop.stop)
            # Wait for the thread running the loop to finish
            self.thread.join(timeout=self.config.shutdown_timeout)

            if self.thread.is_alive():
                self.logger.warning("Shutdown thread is still alive after timeout.")

            # Close the loop now that it is no longer running
            self.loop.close()
