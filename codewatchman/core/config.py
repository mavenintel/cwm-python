from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeWatchmanConfig:
    """Configuration class for CodeWatchman logger."""
    project_id: str
    project_secret: str
    server_url: str = "ws://localhost:8787/log"
    queue_size: int = 1000
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 5.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not self.project_id or not isinstance(self.project_id, str):
            raise ValueError("project_id must be a non-empty string")
        if not self.project_secret or not isinstance(self.project_secret, str):
            raise ValueError("project_secret must be a non-empty string")