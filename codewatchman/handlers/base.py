from abc import ABC, abstractmethod

class BaseHandler(ABC):
    """Abstract base class for all handlers."""

    @abstractmethod
    async def connect(self):
        """Establish a connection."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close the connection."""
        pass

    @abstractmethod
    async def send_message(self, message: str):
        """Send a message."""
        pass

    @abstractmethod
    async def receive_message(self):
        """Receive a message."""
        pass