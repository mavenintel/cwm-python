from __future__ import annotations
import asyncio
import logging
from threading import Lock
from typing import List, Optional
from datetime import datetime
from collections import deque
from weakref import WeakSet

from ..core.config import CodeWatchmanConfig
from ..core.constants import LogLevel
from .message import QueueMessage

class MessageQueue:
    """Thread-safe asynchronous message queue implementation."""
    def __init__(self, config: CodeWatchmanConfig):
        self.config = config
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_size)
        self._lock = Lock()
        self._paused = False

        # Use deque for batch processing (more efficient than list)
        self._current_batch: deque = deque(maxlen=config.batch_size)
        self._batch_lock = Lock()

        # Use WeakSet for callbacks to prevent memory leaks
        self._callbacks = WeakSet()

        # Statistics with atomic counters
        self._total_messages = 0
        self._processed_messages = 0
        self._failed_messages = 0
        self._retried_messages = 0

        # Performance optimizations
        self._batch_ready = asyncio.Event()
        self._flush_threshold = min(config.batch_size // 2, 50)  # Dynamic flush threshold

    @property
    def size(self) -> int:
        """Current queue size."""
        return self._queue.qsize()

    @property
    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return self.size >= self.config.max_size

    @property
    def stats(self) -> dict:
        """Get queue statistics."""
        with self._lock:
            return {
                "total_messages": self._total_messages,
                "processed_messages": self._processed_messages,
                "failed_messages": self._failed_messages,
                "retried_messages": self._retried_messages,
                "current_queue_size": self.size
            }

    async def put(self, level: LogLevel, message: str, timestamp: Optional[datetime] = None, payload: Optional[dict] = None) -> bool:
        """Put a message in the queue with optimized batching."""
        if self._paused or self.is_full:
            return False

        try:
            msg = QueueMessage(
                level=level,
                message=message,
                timestamp=timestamp or datetime.now(),
                payload=payload
            )

            # Fast path for non-full queue
            if self.size < self.config.max_size - self._flush_threshold:
                await self._queue.put(msg)
                self._increment_total()
                return True

            # Slow path with lock for near-full queue
            async with asyncio.Lock():
                if self.is_full:
                    return False
                await self._queue.put(msg)
                self._increment_total()
                return True

        except Exception as e:
            logging.error(f"Error putting message in queue: {e}")
            return False

    def _increment_total(self) -> None:
        """Thread-safe counter increment."""
        with self._lock:
            self._total_messages += 1
            if self.size >= self._flush_threshold:
                self._batch_ready.set()

    async def get_batch(self) -> List[QueueMessage]:
        """Get a batch of messages with optimized retrieval."""
        if self._paused:
            return []

        batch = []
        try:
            # Wait for batch threshold or timeout
            await asyncio.wait_for(self._batch_ready.wait(), timeout=self.config.batch_interval)
        except asyncio.TimeoutError:
            pass

        # Collect messages up to batch size
        while len(batch) < self.config.batch_size and not self._queue.empty():
            try:
                msg = self._queue.get_nowait()
                batch.append(msg)
            except asyncio.QueueEmpty:
                break

        if not batch:
            self._batch_ready.clear()

        return batch

    def mark_processed(self, count: int = 1) -> None:
        """Mark messages as successfully processed.

        Args:
            count: Number of messages processed
        """
        with self._lock:
            self._processed_messages += count

    def mark_failed(self, count: int = 1) -> None:
        """Mark messages as failed.

        Args:
            count: Number of failed messages
        """
        with self._lock:
            self._failed_messages += count

    def mark_retried(self, count: int = 1) -> None:
        """Mark messages as retried.

        Args:
            count: Number of retried messages
        """
        with self._lock:
            self._retried_messages += count

    async def shutdown(self) -> None:
        """Gracefully shutdown the queue."""
        # Process remaining items
        while not self._queue.empty():
            await asyncio.sleep(0.1)

    def pause(self) -> None:
        """Pause queue processing."""
        with self._lock:
            self._paused = True
            logging.debug("Queue processing paused")

    def resume(self) -> None:
        """Resume queue processing."""
        with self._lock:
            self._paused = False
            logging.debug("Queue processing resumed")

    def is_paused(self) -> bool:
        """Check if queue processing is paused."""
        return self._paused

    def clear(self) -> None:
        """Clear all messages from the queue."""
        try:
            while not self._queue.empty():
                self._queue.get_nowait()
            logging.debug("Queue cleared")
        except Exception as e:
            logging.error(f"Error clearing queue: {e}")

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()