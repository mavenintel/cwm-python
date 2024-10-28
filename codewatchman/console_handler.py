import logging

class ConsoleHandler(logging.StreamHandler):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def color_message(self, message, level):
        if not self.config.enable_colors:
            return message

        colors = {
            logging.DEBUG: '\033[97m',    # Blue
            logging.INFO: '\033[90m',     # gray
            logging.WARNING: '\033[93m',  # Yellow
            logging.ERROR: '\033[91m',    # Red
            logging.CRITICAL: '\033[95m', # Magenta
            'SUCCESS': '\033[92m',        # Green
        }

        reset = '\033[0m' # Reset color

        return f"{colors.get(level, reset)}{message}{reset}"

    def emit(self, record):
        try:
            msg = self.format(record)
            colored_msg = self.color_message(msg, record.levelno)
            stream = self.stream
            stream.write(colored_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)