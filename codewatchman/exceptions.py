class CodeWatchmanError(Exception):
    pass


class CodeWatchmanConfigurationError(CodeWatchmanError):
    pass


class CodeWatchmanConnectionError(CodeWatchmanError):
    pass


class CodeWatchmanAPIError(CodeWatchmanError):
    pass
