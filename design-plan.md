I want to build a Python library called CodeWatchman, which is a custom logging module. The module should be a wrapper around Python's default logging library—the library logs to the console as well as to a server. The server calls should happen without blocking the script execution. This is how the library usage will be.

```python
import CodeWatchman, CodeWatchmanConfig

cwm_config = CodeWatchmanConfig(
    project_id="project123",
    project_secret="secret456"
)
logger = CodeWatchman(config=cwm_config, level=logging.DEBUG)

logger.debug("This is a debug message")
logger.sep()
logger.info("This is an info message")
logger.sep()
logger.warning("This is a warning message",  extra={ "payload": { "key": "value" } }
)
logger.error("This is an error message")
logger.critical("This is a critical message")
logger.success(
	"This is a success message",
	extra={ "payload": { "key": "value" } }
)
logger.sep()
logger.failure("This is a fail message")
logger.success("All messages sent.")
logger.close()
 ```

1. Upon Creating the class, if there are credentials provided in the config object, connect to the client-server and send over machine and environment data. This step should be blocking as it is a necessary step.
2. Each log after that should be sent to the console and web socket handlers.
3. Add logs to a queue to process and send data asynchronously without stopping the program. The queue is consumed continuously waiting for data.
4. When the program is complete, finish processing everything in the queue, close the connection and then exit the program. The `logger.close()` method will ensure that the program will not exit without processing all logs and closing the web socket connection.
Now, create a high-level plan for this library such as file and class structure as well as which libraries to use.

## Project Structure
```
codewatchman/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── logger.py          # Main CodeWatchman class
│   ├── config.py          # Configuration class
│   ├── manager.py         # Manager class
│   └── constants.py       # Constants and enums
├── handlers/
│   ├── __init__.py
│   ├── base_handler.py    # Abstract base handler
│   ├── console.py         # Console output handler
│   └── websocket.py       # WebSocket handler for server
├── queue/
│   ├── __init__.py
│   ├── message_queue.py   # Async queue implementation
│   └── worker.py          # Queue worker/processor
└── utils/
    ├── __init__.py
    ├── base_formatter.py  # Base class for utils
    ├── formatters.py      # Log formatting utilities
    └── system_info.py     # System/environment info collector

tests/
├── __init__.py
├── test_logger.py
├── test_handlers.py
└── test_queue.py
```

## Dependencies
1. **Core Dependencies**
   - `websockets`: For WebSocket client implementation
   - `asyncio`: For async operations and queue management
   - `dataclasses`: For configuration objects
   - `typing`: For type hints
   - `logging`: Python's built-in logging module
   - `colorama`: For colored console output
   - `tqdm`: For progress tracking

2. **Optional Dependencies**
   - `psutil`: For detailed system information
   - `pytest`: For testing
   - `black`: For code formatting
   - `mypy`: For type checking

## Component Details

### 1. Core Components

#### CodeWatchman Config
```python
@dataclass
class CodeWatchmanConfig:
    project_id: str
    project_secret: str
    server_url: str = "ws://localhost:8787/log"
    queue_size: int = 1000
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 5.0
```

#### CodeWatchman (Main Logger)
- Inherits from `logging.Logger`
- Manages handlers and queue
- Provides additional logging methods (success, failure, sep)
- Handles graceful shutdown
- Implements context manager protocol

#### WatchmanManager
- Manages the lifecycle of the logger
- Initializes the logger with the provided configuration
- Stops the logger gracefully when the program exits

### 2. Queue System

#### MessageQueue
- Built on `asyncio.Queue`
- Thread-safe implementation
- Supports batch processing
- Implements retry mechanism
- Handles backpressure

#### QueueWorker
- Runs in separate thread
- Processes messages asynchronously
- Handles reconnection logic
- Implements backoff strategy

### 3. Handlers

#### ConsoleHandler
- Extends `logging.StreamHandler`
- Custom formatting
- ANSI color support
- Progress indicators

#### WebSocketHandler
- Async WebSocket client
- Handles connection management
- Implements heartbeat
- Handles authentication
- Supports message batching

## Key Features

### 1. Asynchronous Operation
- Non-blocking WebSocket operations
- Background queue processing
- Graceful shutdown handling
- Connection recovery

### 2. Log Enrichment
- System information
- Environment details
- Stack traces
- Custom metadata
- Timestamps in ISO 8601 format
- Color-coded logs using `colorama`
- Standard log levels:
  - DEBUG
  - INFO
  - WARNING
  - ERROR
  - CRITICAL
- Custom levels:
  - SUCCESS
  - FAILURE

### 3. Error Handling
- Connection failures
- Queue overflow
- Message delivery failure
- Process interruption

### 4. Performance Considerations
- Memory-efficient queue
- Batch processing
- Connection pooling
- Message compression

### 5. Extra Features
- System information collection
- Custom log formatting
- Message batching
- Error handling and retry logic
- Connection state monitoring
- Queue statistics
- tqdm support for monitoring progress

## Implementation Strategy

### 1. Initialization Flow
1. Create CodeWatchman instance
2. Initialize configuration
3. Set up logging handlers
4. Start queue manager
5. Establish WebSocket connection
6. Send initial system information

### 2. Logging Flow
1. Log message created
2. Format message with extras
3. Send to console handler
4. Add to message queue
5. Background worker processes queue
6. Send via WebSocket
7. Handle success/failure
8. Implement tqdm progress logging support

### 3. Shutdown Flow
1. Stop accepting new messages
2. Process remaining queue items
3. Send final statistics
4. Close WebSocket connection
5. Stop worker threads
6. Clean up resources

## Testing Strategy

1. **Unit Tests**
   - Individual component testing
   - Mock WebSocket server
   - Queue behavior
   - Handler logic

2. **Integration Tests**
   - End-to-end logging flow
   - Queue processing
   - WebSocket communication

3. **Performance Tests**
   - High-volume logging
   - Connection handling
   - Memory usage
   - Queue throughput

## Future Enhancements

1. Multiple server endpoints support
2. Custom handler plugins
3. Log aggregation and filtering
4. Real-time log streaming
5. Metrics collection
6. Log rotation and archival
7. Encryption support
8. Custom formatting templates