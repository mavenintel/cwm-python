import pytest
import asyncio
from datetime import datetime
from codewatchman import CodeWatchmanConfig
from codewatchman.queue import MessageQueue, QueueWorker, QueueMessage
from codewatchman.core.constants import LogLevel

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456",
        max_size=100,
        batch_size=10,
        batch_interval=0.1
    )

@pytest.fixture
def message_queue(config):
    return MessageQueue(config)

@pytest.fixture
def queue_worker(message_queue, config):
    return QueueWorker(message_queue, config)

@pytest.mark.asyncio
async def test_queue_message_creation():
    msg = QueueMessage(
        level=LogLevel.INFO,
        message="Test message",
        timestamp=datetime.utcnow(),
        payload={"key": "value"}
    )

    assert msg.level == LogLevel.INFO
    assert msg.message == "Test message"
    assert isinstance(msg.timestamp, datetime)
    assert msg.payload == {"key": "value"}
    assert msg.retry_count == 0
    assert msg.batch_id is None

@pytest.mark.asyncio
async def test_queue_put_and_get(message_queue):
    # Test putting a message
    success = await message_queue.put(
        level=LogLevel.INFO,
        message="Test message",
        payload={"test": "data"}
    )
    assert success is True

    # Test getting the message
    msg = await message_queue.get()
    assert msg is not None
    assert msg.level == LogLevel.INFO
    assert msg.message == "Test message"
    assert msg.payload == {"test": "data"}

@pytest.mark.asyncio
async def test_queue_batch_operations(message_queue):
    # Put multiple messages
    for i in range(5):
        await message_queue.put(
            level=LogLevel.INFO,
            message=f"Message {i}"
        )

    # Get batch of messages
    batch = await message_queue.get_batch()
    assert len(batch) == 5

    # Test batch processing
    message_queue.mark_processed(len(batch))
    stats = message_queue.stats
    assert stats["processed_messages"] == 5

@pytest.mark.asyncio
async def test_queue_statistics(message_queue):
    # Put some messages
    await message_queue.put(LogLevel.INFO, "Success message")
    await message_queue.put(LogLevel.ERROR, "Error message")

    # Mark various states
    message_queue.mark_processed(1)
    message_queue.mark_failed(1)
    message_queue.mark_retried(1)

    stats = message_queue.stats
    assert stats["total_messages"] == 2
    assert stats["processed_messages"] == 1
    assert stats["failed_messages"] == 1
    assert stats["retried_messages"] == 1

@pytest.mark.asyncio
async def test_queue_full_behavior(message_queue):
    # Fill queue to capacity
    for _ in range(message_queue.config.max_size):
        await message_queue.put(LogLevel.INFO, "Test message")

    # Try to put one more message
    success = await message_queue.put(LogLevel.INFO, "Overflow message")
    assert success is False
    assert message_queue.is_full is True

def test_worker_lifecycle(queue_worker):
    # Test worker start
    queue_worker.start()
    assert queue_worker._running is True
    assert queue_worker._thread is not None
    assert queue_worker._thread.is_alive()

    # Test worker stop
    queue_worker.stop()
    assert queue_worker._running is False
    assert not queue_worker._thread.is_alive()

@pytest.mark.asyncio
async def test_worker_batch_processing(message_queue, queue_worker):
    # Put some messages
    for i in range(5):
        await message_queue.put(LogLevel.INFO, f"Message {i}")

    # Start worker
    queue_worker.start()

    # Wait for processing
    await asyncio.sleep(0.5)

    # Check if messages were processed
    stats = message_queue.stats
    assert stats["processed_messages"] > 0


@pytest.mark.asyncio
async def test_queue_shutdown(message_queue):
    # Put some messages
    for i in range(5):
        await message_queue.put(LogLevel.INFO, f"Message {i}")

    initial_size = message_queue.size
    assert initial_size == 5

    # Start processing in background
    worker = QueueWorker(message_queue, message_queue.config)
    worker.start()

    # Shutdown queue
    await message_queue.shutdown()
    worker.stop()

    # Verify queue is empty or timeout occurred
    assert message_queue.size == 0, "Queue should be empty after shutdown"