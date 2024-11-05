import asyncio
import logging
import websockets
from typing import Optional, Callable
from datetime import datetime, timedelta

from .base import BaseHandler
from ..core.constants import ConnectionState
from ..core.config import CodeWatchmanConfig

class WebSocketHandler(BaseHandler):
    def __init__(self, config: CodeWatchmanConfig):
        super().__init__()
        self.config = config
        self.connection = None
        self.state = ConnectionState.DISCONNECTED
        self.last_attempt = None
        self.attempt_count = 0
        self._state_callbacks = []

        # Add heartbeat related attributes
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_heartbeat: Optional[datetime] = None
        self._heartbeat_received = asyncio.Event()

    async def _start_heartbeat(self) -> None:
        """Start the heartbeat mechanism."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _stop_heartbeat(self) -> None:
        """Stop the heartbeat mechanism."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop that sends pings and monitors responses."""
        while self.state == ConnectionState.CONNECTED:
            try:
                # Send heartbeat
                await self.connection.ping()
                self._heartbeat_received.clear()

                # Wait for pong response
                try:
                    await asyncio.wait_for(
                        self._heartbeat_received.wait(),
                        timeout=self.config.heartbeat_timeout
                    )
                    self._last_heartbeat = datetime.now()
                except asyncio.TimeoutError:
                    logging.error("Heartbeat timeout - no response received")
                    await self._handle_heartbeat_timeout()
                    break

                # Wait for next interval
                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                logging.error(f"Heartbeat error: {str(e)}")
                await self._handle_heartbeat_timeout()
                break

    async def _handle_heartbeat_timeout(self) -> None:
        """Handle heartbeat timeout by initiating reconnection."""
        logging.warning("Heartbeat timeout - initiating reconnection")
        await self.disconnect()
        await self.connect()

    def add_state_callback(self, callback: Callable[[ConnectionState], None]) -> None:
        """Add a callback for state changes."""
        self._state_callbacks.append(callback)

    def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify callbacks."""
        self.state = new_state
        for callback in self._state_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                logging.error(f"State callback error: {e}")

    async def connect(self):
        """Establish WebSocket connection with retry logic."""
        if self.state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            return True

        self._set_state(ConnectionState.CONNECTING)

        while self.state != ConnectionState.CONNECTED:
            try:
                if self._should_retry():
                    self.connection = await websockets.connect(
                        self.config.server_url,
                        extra_headers={
                            "x-project-id": self.config.project_id,
                            "x-project-secret": self.config.project_secret,
                        }
                    )
                    self.connection.set_pong_handler(self._handle_pong)
                    self._set_state(ConnectionState.CONNECTED)
                    self.attempt_count = 0
                    logging.info("WebSocket connection established")
                    await self._start_heartbeat()
                    self._listen_task = asyncio.create_task(self._listen_messages())
                    return True

            except Exception as e:
                self.attempt_count += 1
                await self._handle_connection_error(e)

                if self.config.max_retry_attempts != -1 and self.attempt_count >= self.config.max_retry_attempts:
                    self._set_state(ConnectionState.FAILED)
                    print("Maximum retry attempts reached")
                    return False

        return self.state == ConnectionState.CONNECTED

    def _should_retry(self) -> bool:
        """Check if we should attempt reconnection."""
        if self.state == ConnectionState.FAILED:
            return False

        if not self.last_attempt:
            return True

        # Calculate backoff with exponential increase
        backoff = min(
            self.config.initial_retry_delay * (self.config.retry_multiplier ** self.attempt_count),
            self.config.max_retry_delay
        )

        next_attempt = self.last_attempt + timedelta(seconds=backoff)
        return datetime.now() >= next_attempt

    async def _handle_connection_error(self, error: Exception) -> None:
        """Handle connection errors with exponential backoff."""
        self._set_state(ConnectionState.RECONNECTING)
        self.last_attempt = datetime.now()

        backoff = min(
            self.config.initial_retry_delay * (self.config.retry_multiplier ** self.attempt_count),
            self.config.max_retry_delay
        )

        print(f"Connection failed: {str(error)}. Retrying in {backoff}s")
        await asyncio.sleep(backoff)

    async def disconnect(self):
        """Close the WebSocket connection."""
        if self.state == ConnectionState.CONNECTED:
            try:
                await self._stop_heartbeat()
                self._listen_task.cancel()
                await self._listen_task
                await self.connection.close()
                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Failed to close WebSocket connection: {e}")
            finally:
                self._set_state(ConnectionState.DISCONNECTED)

    async def send_message(self, message: str):
        """Send a message over the WebSocket."""
        if self.connection:
            try:
                await self.connection.send(message)
                logging.info(f"Message sent: {message}")
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
                await self._handle_heartbeat_timeout()

    async def _listen_messages(self) -> None:
        """Continuously listen for incoming messages."""
        while self.state == ConnectionState.CONNECTED:
            try:
                message = await self.connection.recv()
                logging.info(f"Message received: {message}")
                # Here you can add logic to handle different types of messages
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Failed to receive message: {e}")
                await self._handle_heartbeat_timeout()
                break

    async def receive_message(self) -> Optional[str]:
        """
        Receive a message from the WebSocket.

        Returns:
            Optional[str]: The received message, or None if failed.
        """
        if self.connection:
            try:
                message = await self.connection.recv()
                logging.info(f"Message received: {message}")
                return message
            except Exception as e:
                logging.error(f"Failed to receive message: {e}")
                await self._handle_heartbeat_timeout()
                return None

    def _handle_pong(self, frame: bytes = None) -> None:
        """Handle pong response from server."""
        self._heartbeat_received.set()
        logging.debug("Pong received")