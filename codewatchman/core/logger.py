from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .constants import LogLevel, SEPARATOR
from ..handlers import ConsoleHandler
from .config import CodeWatchmanConfig
from .orchestrator import WatchmanOrchestrator

class CodeWatchman(logging.Logger):
    def __init__(self, config: CodeWatchmanConfig, name: str = "CodeWatchman"):
        super().__init__(name, config.level)

        # Disable noisy log messages
        # logging.getLogger("asyncio").setLevel(logging.WARNING)
        # logging.getLogger("websockets").setLevel(logging.WARNING)

        # Register custom log levels
        logging.addLevelName(LogLevel.SUCCESS, "SUCCESS")
        logging.addLevelName(LogLevel.FAILURE, "FAILURE")

        self.config = config

        # Enable propagation to root logger
        self.propagate = True

        # Create console handler with colored formatting
        if config.console_logging:
            self.addHandler(ConsoleHandler(config))

        self.orchestrator = WatchmanOrchestrator(config)

        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # Start the manager
        self.loop.run_until_complete(self.orchestrator.start())

    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a success message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(LogLevel.SUCCESS, msg, *args, **kwargs)

    def failure(self, msg: str, *args, **kwargs) -> None:
        """Log a failure message.

        Args:
            msg: Message to log
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
        """
        self.log(LogLevel.FAILURE, msg, *args, **kwargs)

    def _log(self, level: LogLevel, msg: str, *args, **kwargs) -> None:
        """Log a message with the given level."""
        super()._log(level, msg, *args, **kwargs)

        asyncio.run_coroutine_threadsafe(
            self.orchestrator.enqueue(level, msg, kwargs.get("extra", {})),
            self.loop
        )

    def sep(self, name: Optional[str] = None) -> None:
        """Add a separator line to the logs"""
        self.info((SEPARATOR, name) if name else SEPARATOR)

    def __enter__(self) -> CodeWatchman:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit with cleanup."""
        self.close()

    def close(self) -> None:
        """Close the logger and clean up resources."""
        try:
            # Run shutdown sequence
            self.loop.run_until_complete(self.orchestrator.stop())

            # Cancel all pending tasks
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()

            # Wait for tasks to complete with timeout
            if pending:
                self.loop.run_until_complete(
                    asyncio.wait(pending, timeout=5.0)
                )
        except Exception as e:
            logging.error(f"Error during logger shutdown: {e}")
        finally:
            self.handlers.clear()
            try:
                self.loop.close()
            except Exception as e:
                logging.error(f"Error closing event loop: {e}")
