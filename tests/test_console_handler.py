import pytest
import logging
from codewatchman import CodeWatchmanConfig
from codewatchman.handlers.console import ConsoleHandler
from codewatchman.utils.console_formatter import ConsoleFormatter

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456"
    )

@pytest.fixture
def handler(config):
    return ConsoleHandler(config)

def test_handler_initialization(handler):
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, ConsoleFormatter)

def test_handler_emit(handler, caplog):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

    handler.emit(record)
    assert "Test message" in caplog.text

def test_handler_error_handling(handler, caplog):
    # Create a bad record that will cause an error
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg=None,  # This will cause an error
        args=(),
        exc_info=None
    )

    # Should not raise an exception
    handler.emit(record)