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

        if not None in [config.server_url, config.project_id, config.project_secret]:
            self.websocket.connect()

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
            messages = [str(message) for message in batch]
            await self.websocket.send(messages)
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
            self.logger.debug("Waiting for consume task to finish")
            await self.consume_task  # Wait for the consume coroutine to finish

        if self.websocket:
            self.logger.debug("Disconnecting from WebSocket server")
            await self.websocket.disconnect()

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

            # Wait for all pending tasks to complete
            async def wait_for_pending_tasks():
                current_task = asyncio.current_task(loop=self.loop)
                pending = [task for task in asyncio.all_tasks(loop=self.loop)
                        if task is not current_task and not task.done()]
                if pending:
                    self.logger.debug("Waiting for pending tasks to complete.")
                    await asyncio.gather(*pending, return_exceptions=True)

            future = asyncio.run_coroutine_threadsafe(wait_for_pending_tasks(), self.loop)
            try:
                future.result(timeout=self.config.shutdown_timeout)
            except Exception as e:
                self.logger.error(f"Error waiting for pending tasks: {e}")

            # Stop the event loop safely from outside the loop
            self.loop.call_soon_threadsafe(self.loop.stop)
            # Wait for the thread running the loop to finish
            self.thread.join(timeout=self.config.shutdown_timeout)

            if self.thread.is_alive():
                self.logger.warning("Shutdown thread is still alive after timeout.")

            # Close the loop now that it is no longer running
            self.loop.close()
