from typing import Any, Dict, Optional
import logging
import os
import sys
import traceback
from colorama import init, Fore, Style
from .base import BaseFormatter

# Initialize colorama for cross-platform colored output
init()

class DefaultFormatter(BaseFormatter):
    """
    Default console formatter with colored output.
    """

    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
        25: Fore.GREEN,  # SUCCESS
        45: Fore.RED,    # FAILURE
    }

    def format(self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Format a log message for console output with colors.

        Returns:
            str: Formatted log message ready for console output
        """
        color = self.COLORS.get(level, Fore.WHITE)
        level_name = f"{color}{self.get_level_name(level):8}{Style.RESET_ALL}"
        timestamp = self.get_timestamp()

        # Format the basic message
        formatted = f"{timestamp} | {level_name} | {msg}"

        # Add extra information if present
        if extra and extra.get('payload'):
            formatted += f"\n{' ' * 32}Extra: {extra['payload']}"

        return formatted


class ServerFormatter(BaseFormatter):
    """
    Formatter for preparing logs to be sent to the server.
    """

    def format(self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Format a log message for server transmission.

        Returns:
            Dict containing the formatted log data
        """
        # Get call context
        frame = self._get_caller_frame()

        context = {
            'file': frame.get('file', 'unknown'),
            'line': frame.get('line', 0),
            'function': frame.get('function', 'unknown'),
            'module': frame.get('module', 'unknown'),
        }

        # Prepare the log entry
        log_entry = {
            'timestamp': self.get_timestamp(),
            'level': self.get_level_name(level),
            'message': msg,
            'context': context,
            'extra': extra or {},
            'process_id': os.getpid(),
            'thread_id': kwargs.get('thread', ''),
            'python_version': sys.version.split()[0],
        }

        # Add stack trace for error levels
        if level >= logging.ERROR:
            log_entry['stacktrace'] = traceback.format_stack()

        return log_entry

    def _get_caller_frame(self) -> Dict[str, Any]:
        """
        Get information about the caller's frame.
        Skips the logging framework frames to find the actual caller.
        """
        frame = sys._getframe()
        while frame:
            if (frame.f_code.co_filename.find('logging') == -1 and
                frame.f_code.co_filename.find('codewatchman') == -1):
                return {
                    'file': os.path.basename(frame.f_code.co_filename),
                    'line': frame.f_lineno,
                    'function': frame.f_code.co_name,
                    'module': frame.f_globals.get('__name__', 'unknown'),
                }
            frame = frame.f_back

        return {}