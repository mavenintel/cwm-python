import pytest
from codewatchman import CodeWatchmanConfig
from codewatchman.core.constants import LogLevel

def test_valid_config():
    config = CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456"
    )
    assert config.project_id == "test123"
    assert config.project_secret == "secret456"
    assert config.server_url == "ws://localhost:8787/log"
    assert config.level == LogLevel.INFO

def test_invalid_project_id():
    with pytest.raises(ValueError, match="project_id must be a non-empty string"):
        CodeWatchmanConfig(project_id="", project_secret="secret")

def test_invalid_project_secret():
    with pytest.raises(ValueError, match="project_secret must be a non-empty string"):
        CodeWatchmanConfig(project_id="test", project_secret="")

def test_invalid_server_url():
    with pytest.raises(ValueError, match="server_url must use ws:// or wss:// protocol"):
        CodeWatchmanConfig(
            project_id="test",
            project_secret="secret",
            server_url="http://example.com"
        )

def test_invalid_log_level():
    with pytest.raises(ValueError, match="Invalid logging level"):
        CodeWatchmanConfig(
            project_id="test",
            project_secret="secret",
            level=999
        )

def test_custom_config():
    config = CodeWatchmanConfig(
        project_id="test",
        project_secret="secret",
        server_url="wss://logs.example.com",
        level=LogLevel.DEBUG,
        console_logging=False,
        separator_length=50
    )
    assert config.server_url == "wss://logs.example.com"
    assert config.level == LogLevel.DEBUG
    assert config.console_logging is False
    assert config.separator_length == 50