from __future__ import annotations

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Callable

from .config import CodeWatchmanConfig
from .constants import ConnectionState, LogLevel
from ..queue import MessageQueue, QueueWorker, QueueMessage
from ..handlers.websocket import WebSocketHandler
from ..utils.metrics import ConnectionMetrics, QueueMetrics, MetricsAggregator

class WatchmanOrchestrator:
    def __init__(self, config: CodeWatchmanConfig):
        self.config = config
        self.logger = logging.getLogger("WatchmanOrchestrator")

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
        self.metrics_aggregator = MetricsAggregator(config=config)
        self._metrics_task: Optional[asyncio.Task] = None

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
            if not hasattr(self, 'websocket') or not hasattr(self, 'message_queue') or not hasattr(self, 'queue_worker'):
                raise RuntimeError("Components not properly initialized")

            # Start WebSocket connection
            await self.websocket.connect()

            # Start queue worker
            self.queue_worker.start()

            # Start metrics collection
            self._metrics_task = asyncio.create_task(self._collect_metrics())

            self.logger.info("WatchmanOrchestrator started successfully")
        except Exception as e:
            self._running = False
            self.logger.error(f"Failed to start WatchmanOrchestrator: {e}")
            raise

    async def stop(self) -> None:
        """Stop the manager and its components gracefully."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        try:
            # Cancel metrics collection
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass

            # Stop accepting new messages
            self.message_queue.pause()

            # Wait for queue to process remaining messages
            await self.queue_worker.stop()

            # Close WebSocket connection
            await self.websocket.disconnect()

            self.logger.info("WatchmanOrchestrator stopped successfully")
        except Exception as e:
            self.logger.error(f"Error during WatchmanOrchestrator shutdown: {e}")
            raise
        finally:
            self.message_queue.clear()

    async def enqueue(self, level: LogLevel, message: str, payload: dict | None = None) -> bool:
        """Enqueue a message for processing.

        Args:
            level (LogLevel): The severity level of the log message.
            message (str): The log message.
            payload (dict, optional): Additional payload data.

        Returns:
            bool: True if the message was enqueued successfully, False otherwise.
        """
        if not self._running:
            self.logger.warning("Attempted to enqueue message while orchestrator is not running")
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

    def _handle_connection_state(self, new_state: ConnectionState) -> None:
        """Handle WebSocket connection state changes.

        Args:
            new_state (ConnectionState): The new state of the WebSocket connection.
        """
        old_state = self.connection_metrics.current_state
        self.connection_metrics.record_state_change(old_state, new_state)

        if new_state == ConnectionState.CONNECTED:
            self.connection_metrics.record_connection_attempt(True)
            self.message_queue.resume()
        elif new_state == ConnectionState.DISCONNECTED:
            self.connection_metrics.record_connection_attempt(False)
            self.message_queue.pause()

    async def _handle_message(self, message: QueueMessage) -> bool:
        """Handle a message from the queue.

        Args:
            message (QueueMessage): The message to handle.

        Returns:
            bool: True if handled successfully, False otherwise.
        """
        try:
            self.logger.debug(f"Sending message: {message}")
            if not self.websocket.is_connected():
                self.logger.warning("WebSocket is not connected. Cannot send message.")
                return False
            await self.websocket.send_message(message=str(message))
            self.queue_metrics.record_batch_processing(1, 1, 0)
            return True
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            self.queue_metrics.record_batch_processing(1, 0, 1)
            return False

    async def _collect_metrics(self) -> None:
        """Periodically collect and send system metrics."""
        while self._running:
            try:
                self.metrics_aggregator.add_system_metrics(self.config)
                latest_metrics = self.metrics_aggregator.get_latest_metrics()

                # Convert metrics to JSON string
                metrics_json = json.dumps(latest_metrics)

                # Send metrics to WebSocket server
                if self.websocket.is_connected():
                    await self.websocket.send_message(message=metrics_json)
                    self.logger.debug("Sent metrics to WebSocket server")
                else:
                    self.logger.warning("WebSocket is not connected. Metrics not sent.")

                # Wait for the next collection cycle
                await asyncio.sleep(5.0)  # Adjust interval as needed
            except asyncio.CancelledError:
                self.logger.info("Metrics collection task cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error collecting or sending metrics: {e}")
                await asyncio.sleep(1.0)