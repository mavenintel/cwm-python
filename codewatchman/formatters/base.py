from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import datetime

class BaseFormatter(ABC):
    """
    Abstract base class for all CodeWatchman formatters.
    Defines the interface that all formatters must implement.
    """

    @abstractmethod
    def format(self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Format a log message according to the formatter's rules.

        Args:
            level: The log level (DEBUG, INFO, etc.)
            msg: The log message
            extra: Additional data to include in the log
            **kwargs: Additional keyword arguments

        Returns:
            Dict containing the formatted log message
        """
        pass

    def get_level_name(self, level: int) -> str:
        """Get the string name of a logging level."""
        return logging.getLevelName(level)

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.datetime.utcnow().isoformat() + 'Z'

    def get_context(self, **kwargs) -> Dict[str, Any]:
        """
        Extract context information from the logging call.
        Override this method to add custom context information.
        """
        return {
            'timestamp': self.get_timestamp(),
            **kwargs
        }