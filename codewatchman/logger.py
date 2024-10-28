import logging
import threading
from typing import Optional, Dict, Any
from queue import Queue
from .config import CodeWatchmanConfig

class CodeWatchman(logging.Logger):
    # Custom log levels
    SUCCESS = 25
    FAILURE = 45

    def __init__(self, config: CodeWatchmanConfig, name: str = "CodeWatchman"):
        super().__init__(name, config.log_level)

        # Register custom log levels
        logging.addLevelName(self.SUCCESS, "SUCCESS")
        logging.addLevelName(self.FAILURE, "FAILURE")

        self.config = config
        self._message_queue = Queue(maxsize=config.queue_size)
        self._transport_thread = None
        self._should_stop = threading.Event()

        # Setup console handler if enabled
        if config.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(config.log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

        # Initialize transport thread
        self._init_transport()

    def _init_transport(self):
        """Initialize the transport thread for sending logs to server"""
        self._transport_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._transport_thread.start()

    def _process_queue(self):
        """Process messages from queue and send to server"""
        # TODO: Implement WebSocket connection and message sending
        pass

    def _log_with_extra(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal method to handle logging with extra parameters"""
        if extra is None:
            extra = {}

        # Log to console through parent Logger
        super().log(level, msg, extra=extra, **kwargs)

        # Prepare message for server
        log_entry = {
            "level": logging.getLevelName(level),
            "message": msg,
            "extra": extra,
            "project_id": self.config.project_id
            # Additional context will be added here
        }

        # Add to queue for processing
        try:
            self._message_queue.put(log_entry, block=False)
        except Queue.Full:
            self.warning("Message queue is full, log message dropped")

    def sep(self):
        """Add a separator line to the logs"""
        separator = "-" * 50
        self.info(separator)

    def success(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log a success message"""
        self._log_with_extra(self.SUCCESS, msg, extra, **kwargs)

    def failure(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log a failure message"""
        self._log_with_extra(self.FAILURE, msg, extra, **kwargs)

    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, extra, **kwargs)

    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log_with_extra(logging.INFO, msg, extra, **kwargs)

    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log_with_extra(logging.WARNING, msg, extra, **kwargs)

    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log_with_extra(logging.ERROR, msg, extra, **kwargs)

    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._log_with_extra(logging.CRITICAL, msg, extra, **kwargs)

    def close(self):
        """
        Gracefully shut down the logger, ensuring all messages are processed
        """
        self._should_stop.set()

        # Wait for queue to be empty
        while not self._message_queue.empty():
            pass

        if self._transport_thread and self._transport_thread.is_alive():
            self._transport_thread.join(timeout=5.0)