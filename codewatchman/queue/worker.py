from __future__ import annotations
import asyncio
import logging
import threading
from typing import Optional, Callable, List
from datetime import datetime, timedelta

from ..handlers.websocket import WebSocketHandler
from ..core.config import CodeWatchmanConfig
from .message_queue import MessageQueue, QueueMessage

class QueueWorker:
    """Asynchronous queue worker that processes messages in the background."""

    def __init__(self, queue: MessageQueue, config: CodeWatchmanConfig, message_handler: Callable[[QueueMessage], bool]):
        self.queue = queue
        self.config = config
        self._running = False
        self.message_handler = message_handler
        self._thread: Optional[threading.Thread] = None
        self._last_batch_time = datetime.now()
        self._shutdown_complete = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        """Start the worker thread."""
        if self._running:
            return

        self._running = True
        self._shutdown_complete.clear()
        self._thread = threading.Thread(target=self._run_worker, daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        """Stop the worker thread."""
        if not self._running:
            return

        self._running = False

        # Wait for shutdown to complete - 30 seconds timeout
        shutdown_complete = await asyncio.wait_for(
            asyncio.to_thread(self._shutdown_complete.wait),
            timeout=30.0
        )

        if not shutdown_complete:
            logging.error("Queue worker shutdown timed out")

        if self._thread and self._thread.is_alive():
            await asyncio.to_thread(self._thread.join, timeout=self.config.batch_interval)

    def _run_worker(self) -> None:
        """Main worker loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._process_queue())
        except Exception as e:
            logging.error(f"Worker error: {str(e)}")
        finally:
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()

                # Wait for tasks to complete with timeout
                if pending:
                    self._loop.run_until_complete(
                        asyncio.wait(pending, timeout=5.0)
                    )
            finally:
                self._loop.close()
                self._shutdown_complete.set()

    async def _process_queue(self) -> None:
        """Process messages from the queue with optimized batch handling."""
        batch_start_time = datetime.now()
        consecutive_empty = 0

        while self._running or not self.queue.empty():
            try:
                if self._should_process_batch():
                    messages = await self.queue.get_batch()
                    if messages:
                        consecutive_empty = 0
                        await self._process_batch(messages)
                        self._last_batch_time = datetime.now()
                    else:
                        consecutive_empty += 1
                        # Exponential backoff for empty queues
                        if consecutive_empty > 3:
                            await asyncio.sleep(min(0.1 * (2 ** (consecutive_empty - 3)), 1.0))
                        else:
                            await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.01)

            except Exception as e:
                logging.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(self.config.retry_delay)

    def _should_process_batch(self) -> bool:
        """Check if it's time to process the next batch."""
        time_since_last = datetime.now() - self._last_batch_time
        return time_since_last >= timedelta(seconds=self.config.batch_interval)

    async def _process_batch(self, messages: List[QueueMessage]) -> None:
        """Process a batch of messages with improved error handling and metrics."""
        processed = failed = 0
        batch_size = len(messages)

        # Process messages in smaller chunks for better responsiveness
        chunk_size = min(10, batch_size)
        for i in range(0, batch_size, chunk_size):
            chunk = messages[i:i + chunk_size]
            chunk_results = await asyncio.gather(
                *(self._process_single_message(msg) for msg in chunk),
                return_exceptions=True
            )

            for result in chunk_results:
                if isinstance(result, Exception):
                    failed += 1
                    logging.error(f"Message processing error: {str(result)}")
                elif result:
                    processed += 1
                else:
                    failed += 1

        # Update queue statistics
        self.queue.mark_processed(processed)
        if failed > 0:
            self.queue.mark_failed(failed)

    async def _process_single_message(self, message: QueueMessage) -> bool:
        """Process a single message with retry logic."""
        try:
            if await self.message_handler(message):
                return True

            if message.retry_count < self.config.max_retries:
                message.retry_count += 1
                await self.queue.put(
                    level=message.level,
                    message=message.message,
                    timestamp=message.timestamp,
                    payload=message.payload
                )
            return False
        except Exception as e:
            logging.error(f"Message processing error: {str(e)}")
            return False