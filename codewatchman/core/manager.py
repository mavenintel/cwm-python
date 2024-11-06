from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable

from .config import CodeWatchmanConfig
from .constants import ConnectionState, LogLevel
from ..queue import MessageQueue, QueueWorker, QueueMessage
from ..handlers.websocket import WebSocketHandler
from ..utils.metrics import ConnectionMetrics, QueueMetrics

class WatchmanManager:
    def __init__(self, config: CodeWatchmanConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.message_queue = MessageQueue(config)
        self.websocket = WebSocketHandler(config)

        # Initialize worker with the message handler
        self.queue_worker = QueueWorker(
            queue=self.message_queue,
            config=config,
            message_handler=self._handle_message
        )

        # Metrics
        self.connection_metrics = ConnectionMetrics()
        self.queue_metrics = QueueMetrics()

        # State
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Register WebSocket state callback
        self.websocket.register_state_callback(self._handle_connection_state)

    @property
    def is_running(self) -> bool:
        """Check if the manager is running."""
        return self._running

    @property
    def connection_state(self) -> ConnectionState:
        """Get the current WebSocket connection state."""
        return self.websocket.state

    async def start(self) -> None:
        """Start the Watchman manager and all its components."""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()

        try:
            # Start WebSocket connection
            await self.websocket.connect()

            # Start queue worker
            self.queue_worker.start()

            self.logger.info("WatchmanManager started successfully")
        except Exception as e:
            self._running = False
            self.logger.error(f"Failed to start WatchmanManager: {e}")
            raise

    async def stop(self) -> None:
        """Stop the manager and its components gracefully."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        try:
            # Stop accepting new messages
            self.message_queue.pause()

            # Wait for queue to process remaining messages
            await self.queue_worker.stop()

            # Close WebSocket connection
            await self.websocket.disconnect()

            self.logger.info("WatchmanManager stopped successfully")
        except Exception as e:
            self.logger.error(f"Error during WatchmanManager shutdown: {e}")
            raise
        finally:
            self.message_queue.clear()

    async def enqueue(self, level: LogLevel, message: str, payload: dict | None = None) -> bool:
        """Enqueue a message for processing."""
        if not self._running:
            return False

        try:
            success = await self.message_queue.put(
                level=level,
                message=message,
                timestamp=datetime.now(),
                payload=payload
            )
            if not success:
                self.logger.warning("Failed to enqueue message: Queue is full")
            return success
        except Exception as e:
            self.logger.error(f"Error enqueueing message: {e}")
            return False


    def _handle_connection_state(self, state: ConnectionState) -> None:
        """Handle WebSocket connection state changes."""
        self.connection_metrics.record_state_change(self.websocket.state, state)

        if state == ConnectionState.CONNECTED:
            self.connection_metrics.record_connection_attempt(True)
            self.message_queue.resume()
        elif state == ConnectionState.DISCONNECTED:
            self.connection_metrics.record_connection_attempt(False)
            self.message_queue.pause()

    async def _handle_message(self, message: QueueMessage) -> bool:
        """Handle a message from the queue."""
        try:
            if not self.websocket.is_connected():
                return False
            await self.websocket.send_message(message=str(message))
            self.queue_metrics.record_batch_processing(1, 1, 0)
            return True
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            self.queue_metrics.record_batch_processing(1, 0, 1)
            return False

