import asyncio
import logging
import websockets
from ..core.config import CodeWatchmanConfig
from .base import BaseHandler  # Assuming this is the base class

class WebSocketHandler(BaseHandler):
    def __init__(self, config: CodeWatchmanConfig):
        super().__init__()
        self.config = config
        self.connection = None

    async def connect(self):
        """Establish a WebSocket connection."""
        try:
            self.connection = await websockets.connect(
                self.config.server_url,
                extra_headers={
                    "x-project-id": self.config.project_id,
                    "x-project-secret": self.config.project_secret,
                }
            )
            logging.info("WebSocket connection established.")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket: {e}")

    async def disconnect(self):
        """Close the WebSocket connection."""
        if self.connection:
            try:
                await self.connection.close()
                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Failed to close WebSocket connection: {e}")
            finally:
                self.connection = None  # Ensure the connection attribute is set to None

    async def send_message(self, message: str):
        """Send a message over the WebSocket."""
        if self.connection:
            try:
                await self.connection.send(message)
                logging.info(f"Message sent: {message}")
            except Exception as e:
                logging.error(f"Failed to send message: {e}")

    async def receive_message(self):
        """Receive a message from the WebSocket."""
        if self.connection:
            try:
                message = await self.connection.recv()
                logging.info(f"Message received: {message}")
                return message
            except Exception as e:
                logging.error(f"Failed to receive message: {e}")
                return None