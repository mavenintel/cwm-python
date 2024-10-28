import logging
import threading
from typing import Optional, Dict, Any
from queue import Queue
from .config import CodeWatchmanConfig
from .formatters import DefaultFormatter, ServerFormatter

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

        # Initialize formatters
        self._console_formatter = DefaultFormatter()
        self._server_formatter = ServerFormatter()

        # Setup console handler if enabled
        if config.console_output:
            self._setup_console_handler()

        # Initialize transport thread
        self._init_transport()

    def _setup_console_handler(self):
        """Setup console handler with our custom formatter"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.config.log_level)

        # Create a custom Formatter that uses our DefaultFormatter
        class CustomFormatter(logging.Formatter):
            def __init__(self, cwm_formatter):
                super().__init__()
                self.cwm_formatter = cwm_formatter

            def format(self, record):
                # Use our custom formatter to format the message
                return self.cwm_formatter.format(
                    level=record.levelno,
                    msg=record.getMessage(),
                    extra=getattr(record, 'extra', None),
                    thread=record.thread
                )

        console_handler.setFormatter(CustomFormatter(self._console_formatter))
        self.addHandler(console_handler)



    def _init_transport(self):
        """Initialize the transport thread for sending logs to server"""
        self._transport_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._transport_thread.start()

    def _process_queue(self):
        """Process messages from queue and send to server"""
        while not self._should_stop.is_set():
            try:
                # Get message from queue with timeout to allow checking _should_stop
                message = self._message_queue.get(timeout=0.1)

                # TODO: Send message to server via WebSocket
                # This is where we'll implement the actual server communication

                self._message_queue.task_done()

            except Queue.Empty:
                continue
            except Exception as e:
                # Log error but don't raise to keep thread running
                super().error(f"Error processing log message: {str(e)}")

    def _log_with_extra(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal method to handle logging with extra parameters"""
        if extra is None:
            extra = {}

        # Log to console through parent Logger
        super().log(level, msg, extra=extra, **kwargs)

        # Format message for server using ServerFormatter
        log_entry = self._server_formatter.format(
            level=level,
            msg=msg,
            extra=extra,
            thread=threading.get_ident(),
            **kwargs
        )

        # Add project identification
        log_entry['project_id'] = self.config.project_id

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