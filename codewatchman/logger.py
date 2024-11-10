import logging
from typing import Optional
from .console_handler import ConsoleHandler
from .config import CodeWatchmanConfig, default_config

class CodeWatchman(logging.Logger):
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self, config: Optional[CodeWatchmanConfig] = default_config):
        super().__init__(config.name, config.level)

        self.setLevel(config.level)
        self.config = config

        console_handler = ConsoleHandler(config)
        console_handler.setLevel(config.level)
        formatter = logging.Formatter(config.local_log_format, config.local_log_date_format)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

    def sep(self):
        self.info("-" * self.config.sep_length, extra={ "ignore@ws": True })

    def success(self, message, extra=None):
        if self.config.enable_colors:
            message = f"\u2713 {message}"

        self.info(message, extra=extra)

    def failure(self, message, extra=None):
        self.error(f"\u2717 {message}", extra=extra)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        if self.isEnabledFor(level):
            super()._log(level, msg, args, exc_info, extra, stack_info)

    def close(self):
        return True