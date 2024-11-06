from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from threading import Lock

from ..core.constants import LogLevel
from ..core.config import CodeWatchmanConfig
from .message import QueueMessage

class MessageQueue:
    """Thread-safe asynchronous message queue implementation."""
    def __init__(self, config: CodeWatchmanConfig):
        self.config = config
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_size)
        self._lock = Lock()
        self._paused = False

        # Statistics
        self._total_messages = 0
        self._processed_messages = 0
        self._failed_messages = 0
        self._retried_messages = 0

        # Batch processing
        self._current_batch: List[QueueMessage] = []
        self._batch_lock = Lock()

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

    async def put(self, level: int, message: str, payload: Optional[dict] = None) -> bool:
        """Add message to queue.

        Args:
            level: Log level
            message: Log message
            payload: Optional extra data

        Returns:
            bool: True if message was queued successfully

        Raises:
            ValueError: If level is invalid or message is not a string
            TypeError: If message is not a string
        """
        if not isinstance(level, (int, LogLevel)) or level not in [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
            LogLevel.SUCCESS,
            LogLevel.FAILURE
        ]:
            raise ValueError("Invalid logging level")

        if not isinstance(message, str):
            raise TypeError("Message must be a string")

        if self.is_full:
            logging.warning("Queue is full - message dropped")
            return False

        queue_message = QueueMessage(
            level=level,
            message=message,
            timestamp=datetime.utcnow(),
            payload=payload
        )

        with self._lock:
            self._total_messages += 1

        try:
            await self._queue.put(queue_message)
            return True
        except Exception as e:
            logging.error(f"Failed to queue message: {str(e)}")
            return False

    async def get(self) -> Optional[QueueMessage]:
        """Get next message from queue.

        Returns:
            QueueMessage or None if queue is empty
        """
        try:
            return await self._queue.get()
        except asyncio.QueueEmpty:
            return None

    async def get_batch(self) -> List[QueueMessage]:
        """Get batch of messages up to batch_size.

        Returns:
            List of QueueMessage objects
        """
        messages = []

        with self._batch_lock:
            while len(messages) < self.config.batch_size and not self._queue.empty():
                if msg := await self.get():
                    messages.append(msg)

        return messages

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