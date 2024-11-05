from datetime import datetime
import json
from typing import Any, Dict, Optional

from ..core.constants import LogLevel
from ..queue.message import QueueMessage

class MessageSerializer:
    """Handles message serialization for WebSocket communication."""

    @staticmethod
    def serialize(message: QueueMessage) -> str:
        """Serialize a QueueMessage to JSON string."""
        data = {
            "level": message.level.value,
            "message": message.message,
            "timestamp": message.timestamp.isoformat(),
            "payload": message.payload or {},
            "metadata": {
                "retry_count": message.retry_count,
                "batch_id": message.batch_id
            }
        }
        return json.dumps(data)

    @staticmethod
    def deserialize(data: str) -> Dict[str, Any]:
        """Deserialize a JSON string to dictionary."""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")