from __future__ import annotations
import asyncio
import logging
import threading
from typing import Optional
from datetime import datetime, timedelta

from ..core.config import CodeWatchmanConfig
from .message_queue import MessageQueue

class QueueWorker:
    """Asynchronous queue worker that processes messages in the background."""

    def __init__(self, queue: MessageQueue, config: CodeWatchmanConfig):
        self.queue = queue
        self.config = config
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_batch_time = datetime.now()
        self._shutdown_complete = threading.Event()

    def start(self) -> None:
        """Start the worker thread."""
        if self._running:
            return

        self._running = True
        self._shutdown_complete.clear()
        self._thread = threading.Thread(target=self._run_worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the worker thread."""
        self._running = False

        # Wait for shutdown to complete - 30 seconds timeout
        if not self._shutdown_complete.wait(timeout=30.0):
            logging.error("Queue worker shutdown timed out")

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.config.batch_interval)

    def _run_worker(self) -> None:
        """Main worker loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._process_queue())
        except Exception as e:
            logging.error(f"Worker error: {str(e)}")
        finally:
            loop.close()
            self._shutdown_complete.set()  # Signal completion

    async def _process_queue(self) -> None:
        """Process messages from the queue."""
        while self._running or not self.queue.empty():
            try:
                if self._should_process_batch():
                    messages = await self.queue.get_batch()
                    if messages:
                        try:
                            await self._process_batch(messages)
                            self._last_batch_time = datetime.now()
                        except Exception as e:
                            for msg in messages:
                                await self.queue.put(msg.level, msg.message, msg.payload)

                            logging.error(f"Batch processing error: {str(e)}")
                            await asyncio.sleep(self.config.retry_delay)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Batch processing error: {str(e)}")
                await asyncio.sleep(self.config.retry_delay)

    def _should_process_batch(self) -> bool:
        """Check if it's time to process the next batch."""
        time_since_last = datetime.now() - self._last_batch_time
        return time_since_last >= timedelta(seconds=self.config.batch_interval)

    async def _process_batch(self, messages: list) -> None:
        """Process a batch of messages."""
        # This will be implemented when we add WebSocket handler
        # For now, just mark them as processed
        self.queue.mark_processed(len(messages))