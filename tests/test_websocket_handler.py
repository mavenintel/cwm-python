import pytest
import asyncio
from codewatchman.handlers.websocket import WebSocketHandler
from codewatchman.core.config import CodeWatchmanConfig

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456",
        server_url="ws://localhost:8787/log"
    )

@pytest.mark.asyncio
async def test_websocket_connection(config):
    handler = WebSocketHandler(config)
    await handler.connect()
    assert handler.connection is not None
    await handler.disconnect()
    assert handler.connection is None