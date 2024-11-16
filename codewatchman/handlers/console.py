import logging

from ..utils import ConsoleFormatter
from ..core.config import CodeWatchmanConfig

class ConsoleHandler(logging.StreamHandler):
    def __init__(self, config: CodeWatchmanConfig):
        super().__init__()
        self.setFormatter(ConsoleFormatter(config))

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with exception handling.

        Args:
            record: LogRecord instance to emit
        """
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)
