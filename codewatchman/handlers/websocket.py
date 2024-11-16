import logging
import asyncio
import websockets
import json
from typing import List, Optional

from ..core.config import CodeWatchmanConfig
from ..core.constants import ConnectionState

class WebSocketHandler:
    """Handler for sending messages to a WebSocket server."""
    def __init__(self, config: CodeWatchmanConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

        self.state = ConnectionState.DISCONNECTED
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.retry_count = 0
        self.lock = asyncio.Lock()

    @property
    def can_connect(self) -> bool:
        return (
            self.state in [ConnectionState.DISCONNECTED,ConnectionState.FAILED]
            and self.retry_count < self.config.max_retry_attempts
        )

    @property
    def connected(self) -> bool:
        return self.state == ConnectionState.CONNECTED

    async def connect(self) -> bool:
        """Connect to the WebSocket server."""
        async with self.lock:
            if self.connected:
                return True

            if not self.can_connect:
                self.logger.error("Cannot connect: maximum retry attempts reached.")
                return False

            self.state = ConnectionState.CONNECTING
            retry_delay = self.config.initial_retry_delay

            while self.retry_count < self.config.max_retry_attempts:
                try:
                    self.connection = await websockets.connect(
                        self.config.server_url,
                        extra_headers={
                            "x-project-id": self.config.project_id,
                            "x-project-secret": self.config.project_secret,
                        },
                        ping_interval=self.config.ping_interval,
                        ping_timeout=self.config.ping_timeout,
                    )
                    self.state = ConnectionState.CONNECTED
                    self.logger.debug("WebSocket connection established.")
                    self.retry_count = 0  # Reset retry count on successful connection
                    return True

                except Exception as e:
                    self.state = ConnectionState.FAILED
                    self.retry_count += 1
                    self.logger.error(f"WebSocket connection failed: {e}. Retrying in {retry_delay} seconds.")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * self.config.retry_multiplier, self.config.max_retry_delay)

            self.logger.error("Maximum retry attempts reached. Failed to connect to WebSocket server.")
            return False

    async def send(self, messages: List[str]) -> bool:
        """Send messages to the WebSocket server."""
        if not self.connected:
            connected = await self.connect()
            if not connected:
                self.logger.error("Cannot send messages: not connected to WebSocket server.")
                return False

        try:
            # Prepare the messages as JSON
            self.logger.debug(f"Sending batch of {len(messages)} messages.")
            payload = json.dumps([json.loads(str(message)) for message in messages])

            await self.connection.send(payload)
            self.logger.debug(f"Sent batch of {len(messages)} messages.")
            return True

        except Exception as e:
            self.logger.error(f"Error sending messages: {e}")
            self.state = ConnectionState.FAILED
            await self.disconnect()
            return False

    async def disconnect(self) -> bool:
        """Close the WebSocket connection."""
        async with self.lock:
            try:
                if not self.connected or self.connection is None:
                    return True

                await self.connection.close()
                self.state = ConnectionState.DISCONNECTED
                self.logger.debug("WebSocket connection closed.")
                return True
            except Exception as e:
                self.logger.error(f"Error closing WebSocket connection: {str(e)}")
                return False