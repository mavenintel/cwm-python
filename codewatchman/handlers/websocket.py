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
        self._listen_task = None
        self._closing = False

    def register_state_callback(self, callback: Callable[[ConnectionState], None]) -> None:
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
                        },
                        ping_interval=self.config.ping_interval,
                        ping_timeout=self.config.ping_timeout,
                    )
                    self._set_state(ConnectionState.CONNECTED)
                    self.attempt_count = 0
                    logging.info("WebSocket connection established")
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
        if self.state == ConnectionState.CONNECTED and not self._closing:
            self._closing = True
            try:
                if self._listen_task:
                    self._listen_task.cancel()
                    try:
                        await self._listen_task
                    except asyncio.CancelledError:
                        pass

                if self.connection:
                    await self.connection.close()
                    self.connection = None

                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Failed to close WebSocket connection: {e}")
            finally:
                self._closing = False
                self._set_state(ConnectionState.DISCONNECTED)

    async def send_message(self, message: str):
        """Send a message over the WebSocket."""
        if self.connection:
            try:
                print(f"Sending message: {message}")
                await self.connection.send(message)
                logging.info(f"Message sent: {message}")
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
                await self._handle_heartbeat_timeout()

    async def _listen_messages(self) -> None:
        """Continuously listen for incoming messages."""
        try:
            while self.state == ConnectionState.CONNECTED and not self._closing:
                try:
                    message = await self.connection.recv()
                    logging.info(f"Message received: {message}")
                except websockets.ConnectionClosed:
                    if not self._closing:
                        logging.warning("WebSocket connection closed - initiating reconnection")
                        self._set_state(ConnectionState.RECONNECTING)
                        await self.connect()
                    break
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if not self._closing:
                        logging.error(f"Error receiving message: {str(e)}")
                        self._set_state(ConnectionState.RECONNECTING)
                        await self.connect()
                    break
        except asyncio.CancelledError:
            pass

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