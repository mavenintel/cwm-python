from __future__ import annotations
import pytest
import logging
from codewatchman import CodeWatchman, CodeWatchmanConfig
from codewatchman.core.constants import LogLevel

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456"
    )

@pytest.fixture
def logger(config):
    return CodeWatchman(config=config, level=logging.DEBUG)

def test_logger_initialization(logger):
    assert isinstance(logger, CodeWatchman)
    assert logger.level == logging.DEBUG

def test_custom_log_levels(logger):
    assert hasattr(logger, 'success')
    assert hasattr(logger, 'failure')
    assert LogLevel.SUCCESS > logging.INFO
    assert LogLevel.FAILURE > logging.ERROR

def test_separator(logger, capsys):
    logger.sep()
    captured = capsys.readouterr()
    assert "-" * 50 in captured.out

def test_config_validation():
    with pytest.raises(ValueError):
        CodeWatchmanConfig(project_id="", project_secret="secret")
    with pytest.raises(ValueError):
        CodeWatchmanConfig(project_id="test", project_secret="")