import logging
from typing import Optional
from .handlers import ConsoleHandler
from .core.config import CodeWatchmanConfig

class CodeWatchman(logging.Logger):
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self, config: Optional[CodeWatchmanConfig] = None):
        super().__init__(config.name, config.level)

        self.setLevel(config.level)

        if config is None:
            config = CodeWatchmanConfig()

        self.config = config

        console_handler = ConsoleHandler(config)
        console_handler.setLevel(config.level)
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
