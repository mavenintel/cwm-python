import logging

class CodeWatchman(logging.Logger):
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self, name: str, level: int = logging.DEBUG):
        super().__init__(name, level)
        self.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

    def color_message(self, message, level):
        colors = {
            logging.DEBUG: '\033[94m',    # Blue
            logging.INFO: '\033[96m',     # gray
            logging.WARNING: '\033[93m',  # Yellow
            logging.ERROR: '\033[91m',    # Red
            logging.CRITICAL: '\033[95m', # Magenta
        }
        reset = '\033[0m' # Reset color

        self.debug

        return f"{colors.get(level, reset)}{message}{reset}"

    def success(self, message):
        success_message = f"\u2713 {message}"
        self.info(success_message)

    def failure(self, message):
        failure_message = f"\u2717 {message}"
        self.error(failure_message)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        if self.isEnabledFor(level):
            colored_msg = self.color_message(msg, level)
            super()._log(level, colored_msg, args, exc_info, extra, stack_info)