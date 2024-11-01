from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..core.constants import LogLevel

@dataclass
class QueueMessage:
    level: LogLevel
    message: str
    timestamp: datetime
    payload: Optional[dict] = None
    retry_count: int = 0
    batch_id: Optional[str] = None
