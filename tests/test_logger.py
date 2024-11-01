import pytest
import logging
from io import StringIO
from codewatchman import CodeWatchman, CodeWatchmanConfig, LogLevel

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456",
        level=LogLevel.DEBUG  # Ensure the logger captures DEBUG level
    )

@pytest.fixture
def logger(config):
    return CodeWatchman(config)

@pytest.fixture
def caplog_backend():
    return StringIO()

def test_with_dummy_handler(logger, caplog, caplog_backend):
    dummy_handler = logging.StreamHandler(caplog_backend)
    dummy_handler.setLevel(logging.DEBUG)
    logger.addHandler(dummy_handler)

    logger.info("Test log message")

    logger.removeHandler(dummy_handler)
    dummy_handler.flush()
    assert "Test log message" in caplog_backend.getvalue()

def test_logger_initialization(logger):
    assert isinstance(logger, logging.Logger)
    assert logger.level == LogLevel.DEBUG
    assert len(logger.handlers) == 1  # Console handler

def test_custom_log_levels(logger, caplog):
    # Specify the logger name to capture logs from
    caplog.set_level(logging.DEBUG, logger=logger.name)

    logger.success("Success message")
    logger.failure("Failure message")

    messages = [record.message for record in caplog.records]
    level_names = [record.levelname for record in caplog.records]

    assert "Success message" in messages
    assert "Failure message" in messages
    assert "SUCCESS" in level_names
    assert "FAILURE" in level_names

def test_separator(logger, caplog):
    # Set caplog to capture INFO and above
    caplog.set_level(logging.INFO)

    logger.sep()
    separator_line = "-" * logger.config.separator_length
    logger.sep("Test Section")

    # Check messages using caplog.records
    messages = [record.message for record in caplog.records]

    assert separator_line in messages
    assert "Test Section" in messages

def test_context_manager(config, caplog):
    caplog.set_level(logging.INFO, logger="CodeWatchman")

    with CodeWatchman(config) as logger:
        assert len(logger.handlers) == 1
        logger.info("Test message")

    assert len(logger.handlers) == 0

    # Check the captured log
    assert "Test message" in caplog.text

def test_disable_console_logging(config):
    config.console_logging = False
    logger = CodeWatchman(config)
    assert len(logger.handlers) == 0

def test_log_levels(logger, caplog):
    messages = {
        "debug": "Debug message",
        "info": "Info message",
        "warning": "Warning message",
        "error": "Error message",
        "critical": "Critical message"
    }

    for level, msg in messages.items():
        getattr(logger, level)(msg)
        assert msg in caplog.text

def test_close(logger):
    assert len(logger.handlers) > 0
    logger.close()
    assert len(logger.handlers) == 0