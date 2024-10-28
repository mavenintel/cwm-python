from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging

@dataclass
class CodeWatchmanConfig:
    project_id: str
    project_secret: str
    server_url: str = "ws://localhost:8787/log"
    queue_size: int = 1000
    retry_attempts: int = 3
    log_level: int = logging.INFO
    console_output: bool = True