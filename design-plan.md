# CodeWatchman Library Design Plan

## Project Structure
```
codewatchman/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── logger.py          # Main CodeWatchman class
│   ├── config.py          # Configuration class
│   └── constants.py       # Constants and enums
├── handlers/
│   ├── __init__.py
│   ├── base_handler.py    # Abstract base handler
│   ├── console.py         # Console output handler
│   └── websocket.py       # WebSocket handler for server communication
├── queue/
│   ├── __init__.py
│   ├── message_queue.py   # Async queue implementation
│   └── worker.py          # Queue worker/processor
└── utils/
    ├── __init__.py
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

2. **Optional Dependencies**
   - `psutil`: For detailed system information
   - `pytest`: For testing
   - `black`: For code formatting
   - `mypy`: For type checking

## Component Details

### 1. Core Components

#### CodeWatchmanConfig
```python
@dataclass
class CodeWatchmanConfig:
    project_id: str
    project_secret: str
    server_url: str = "wss://api.codewatchman.com/v1/logs"
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

#### BaseHandler
- Abstract base class
- Defines interface for all handlers
- Implements common functionality

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

## Implementation Strategy

### Phase 1: Core Functionality
1. Basic logger implementation
2. Console handler
3. Configuration system

### Phase 2: Queue System
1. Message queue implementation
2. Worker thread
3. Basic retry logic

### Phase 3: WebSocket Integration
1. WebSocket handler
2. Authentication
3. Connection management

### Phase 4: Enhanced Features
1. System information collection
2. Error handling
3. Performance optimizations

## Usage Examples

### Basic Usage
```python
from codewatchman import CodeWatchman, CodeWatchmanConfig

config = CodeWatchmanConfig(
    project_id="project123",
    project_secret="secret456"
)

logger = CodeWatchman(config=config)
with logger:
    logger.info("Application started")
    try:
        # Your code here
        logger.success("Operation completed")
    except Exception as e:
        logger.error("Operation failed", exc_info=True)
```

### Advanced Usage
```python
logger = CodeWatchman(
    config=config,
    level=logging.DEBUG,
    queue_size=2000,
    retry_attempts=5
)

logger.warning(
    "Resource usage high",
    extra={
        "payload": {
            "cpu_usage": 85.5,
            "memory_usage": 75.2,
            "disk_space": 90.1
        },
        "tags": ["performance", "resource-warning"]
    }
)
```

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