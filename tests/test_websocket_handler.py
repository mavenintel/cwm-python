import pytest
import asyncio
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime

from codewatchman.handlers.websocket import WebSocketHandler
from codewatchman.core.config import CodeWatchmanConfig
from codewatchman.utils.serializer import MessageSerializer
from codewatchman.queue.message_queue import QueueMessage
from codewatchman.core.constants import LogLevel, ConnectionState


@pytest.fixture(scope="module")
def test_config():
    """
    Fixture for test configuration with optimized parameters to speed up tests.
    """
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456",
        max_retry_attempts=1,           # Minimize retry attempts
        initial_retry_delay=0.01,       # Reduce initial retry delay
        retry_multiplier=1.0,           # No multiplier to keep delays consistent
        max_retry_delay=0.02,           # Cap the maximum retry delay
        heartbeat_interval=0.05,        # Further reduced interval for faster tests
        heartbeat_timeout=0.03          # Further reduced timeout for faster tests
    )


@pytest.fixture(autouse=True)
def mock_sleep():
    """
    Automatically mock asyncio.sleep to eliminate actual delays during tests.
    """
    with patch("asyncio.sleep", new=AsyncMock()):
        yield


@pytest.mark.asyncio
async def test_connection_retry_logic(test_config):
    """
    Test the connection retry logic with minimized delays and attempts.
    """
    handler = WebSocketHandler(test_config)

    with patch("websockets.connect", side_effect=ConnectionError):
        start_time = datetime.now()
        await handler.connect()

        # Verify that only one retry attempt was made
        assert handler.attempt_count == 1
        assert handler.last_attempt >= start_time


@pytest.mark.asyncio
async def test_message_serialization():
    """
    Test the serialization and deserialization of QueueMessage.
    """
    message = QueueMessage(
        level=LogLevel.INFO,
        message="Test message",
        timestamp=datetime.now()
    )

    serialized = MessageSerializer.serialize(message)
    deserialized = MessageSerializer.deserialize(serialized)

    assert deserialized["message"] == "Test message"
    assert deserialized["level"] == LogLevel.INFO.value


@pytest.mark.asyncio
async def test_connection_state_transitions(test_config):
    """
    Test the state transitions of the WebSocketHandler during connection attempts.
    """
    handler = WebSocketHandler(test_config)
    states = []

    # Add state callback
    handler.add_state_callback(lambda state: states.append(state))

    with patch("websockets.connect", side_effect=ConnectionError):
        success = await handler.connect()
        assert not success
        assert handler.state == ConnectionState.FAILED
        # Expected states: CONNECTING -> FAILED
        assert states == [
            ConnectionState.CONNECTING,
            ConnectionState.RECONNECTING,
            ConnectionState.FAILED
        ]


@pytest.mark.asyncio
async def test_exponential_backoff(test_config):
    """
    Test the exponential backoff mechanism with mocked sleep to capture delays.
    """
    handler = WebSocketHandler(test_config)
    delays = []

    async def mock_sleep_fn(delay):
        delays.append(delay)

    with patch("asyncio.sleep", side_effect=mock_sleep_fn):
        with patch("websockets.connect", side_effect=ConnectionError):
            await handler.connect()

    # Since max_retry_attempts=1 and retry_multiplier=1.0, expected delays:
    # Only one retry with initial_retry_delay=0.01
    assert delays == [0.01]


@pytest.mark.asyncio
async def test_heartbeat_pings(test_config):
    """
    Test that heartbeat pings are sent and handled correctly.
    """
    handler = WebSocketHandler(test_config)

    # Create a more complete mock WebSocket
    mock_ws = AsyncMock()
    mock_ws.ping = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.set_pong_handler = Mock()

    # Mock the context manager methods
    mock_ws.__aenter__.return_value = mock_ws
    mock_ws.__aexit__.return_value = None


    with patch("websockets.connect", return_value=mock_ws):
        # Connect and wait briefly for heartbeat to start
        await handler.connect()
        await asyncio.sleep(0.1)  # Small delay to allow heartbeat to begin

        # Verify ping was called
        assert mock_ws.ping.called, "Ping was not called"

        # Simulate a successful heartbeat cycle
        handler._heartbeat_received.set()
        assert handler._last_heartbeat is not None
        assert handler.state == ConnectionState.CONNECTED

        # Test heartbeat timeout
        handler._heartbeat_received.clear()
        # Wait for timeout to trigger
        await asyncio.sleep(test_config.heartbeat_timeout + 0.01)

        # Verify connection state changed after timeout
        assert handler.state != ConnectionState.CONNECTED

        await handler.disconnect()


@pytest.mark.asyncio
async def test_pong_received(test_config):
    """
    Test that receiving a pong sets the heartbeat_received event.
    """
    handler = WebSocketHandler(test_config)

    mock_ws = AsyncMock()

    with patch("websockets.connect", return_value=mock_ws):
        await handler.connect()

        # Initially, the heartbeat_received event should not be set
        assert not handler._heartbeat_received.is_set()

        # Simulate receiving a pong
        handler._handle_pong()

        # Now, the heartbeat_received event should be set
        assert handler._heartbeat_received.is_set()

        await handler.disconnect()