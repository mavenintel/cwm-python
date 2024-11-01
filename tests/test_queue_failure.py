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
        max_size=5,  # Small size to test overflow
        batch_size=2,
        batch_interval=0.1,
        retry_delay=0.1
    )

@pytest.fixture
def message_queue(config):
    return MessageQueue(config)

@pytest.mark.asyncio
async def test_queue_overflow_handling(message_queue):
    # Fill queue to max capacity
    for i in range(message_queue.config.max_size):
        success = await message_queue.put(LogLevel.INFO, f"Message {i}")
        assert success is True

    # Try to add one more message
    success = await message_queue.put(LogLevel.INFO, "Overflow message")
    assert success is False

    # Verify queue size hasn't exceeded max
    assert message_queue.size == message_queue.config.max_size

@pytest.mark.asyncio
async def test_worker_error_handling(message_queue, config):
    # Create a worker that will raise an exception during processing
    class ErrorWorker(QueueWorker):
        async def _process_batch(self, messages: list) -> None:
            raise Exception("Simulated processing error")

    worker = ErrorWorker(message_queue, config)

    # Add some messages
    await message_queue.put(LogLevel.INFO, "Test message 1")
    await message_queue.put(LogLevel.INFO, "Test message 2")

    # Start worker
    worker.start()
    await asyncio.sleep(0.5)  # Give time for processing attempt

    # Check that messages are still in queue after error
    assert message_queue.size == 2

    # Stop worker
    worker.stop()

@pytest.mark.asyncio
async def test_invalid_message_handling(message_queue):
    # Try to create message with invalid level
    with pytest.raises(ValueError):
        await message_queue.put(999, "Invalid level message")

    # Try to create message with invalid message type
    with pytest.raises(TypeError):
        await message_queue.put(LogLevel.INFO, {"invalid": "message"})

@pytest.mark.asyncio
async def test_batch_processing_timeout(message_queue, config):
    # Create a worker with slow processing
    class SlowWorker(QueueWorker):
        async def _process_batch(self, messages: list) -> None:
            await asyncio.sleep(2)  # Simulate slow processing
            self.queue.mark_processed(len(messages))

    worker = SlowWorker(message_queue, config)

    # Add messages
    for i in range(3):
        await message_queue.put(LogLevel.INFO, f"Message {i}")

    # Start worker
    worker.start()

    # Wait for less time than processing needs
    await asyncio.sleep(0.5)

    # Stop worker (should timeout)
    worker.stop()

    # Check that not all messages were processed
    stats = message_queue.stats
    assert stats["processed_messages"] < 3

@pytest.mark.asyncio
async def test_worker_shutdown_with_pending_messages(message_queue, config):
    worker = QueueWorker(message_queue, config)

    # Add more messages than can be processed in one batch
    for i in range(10):
        await message_queue.put(LogLevel.INFO, f"Message {i}")

    # Start and immediately stop worker
    worker.start()
    worker.stop()

    # Verify some messages remain unprocessed
    assert message_queue.size > 0

@pytest.mark.asyncio
async def test_queue_statistics_during_failures(message_queue):
    # Add messages and simulate different failure scenarios
    await message_queue.put(LogLevel.INFO, "Success message")
    await message_queue.put(LogLevel.ERROR, "Error message")

    # Simulate processing states
    message_queue.mark_failed(1)
    message_queue.mark_retried(1)

    # Check statistics
    stats = message_queue.stats
    assert stats["failed_messages"] == 1
    assert stats["retried_messages"] == 1
    assert stats["processed_messages"] == 0