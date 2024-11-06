from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, median

from ..core.constants import ConnectionState, LogLevel

@dataclass
class ConnectionMetrics:
    """
    Tracks connection-related metrics and statistics.
    """
    # State tracking
    state_changes: List[Tuple[datetime, ConnectionState]] = field(default_factory=list)
    current_state: ConnectionState = ConnectionState.DISCONNECTED
    last_state_change: Optional[datetime] = None

    # Connection attempts
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0

    # Timing metrics
    connection_times: List[float] = field(default_factory=list)
    disconnection_times: List[float] = field(default_factory=list)
    uptime_periods: List[float] = field(default_factory=list)

    # Error tracking
    errors: Dict[str, int] = field(default_factory=dict)
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def record_state_change(self, old_state: ConnectionState, new_state: ConnectionState) -> None:
        """Record a connection state change."""
        now = datetime.now()
        self.state_changes.append((now, new_state))
        self.current_state = new_state

        if self.last_state_change:
            duration = (now - self.last_state_change).total_seconds()

            if old_state == ConnectionState.CONNECTED:
                self.uptime_periods.append(duration)
            elif old_state == ConnectionState.CONNECTING and new_state == ConnectionState.CONNECTED:
                self.connection_times.append(duration)
            elif old_state == ConnectionState.DISCONNECTED and new_state == ConnectionState.DISCONNECTED:
                self.disconnection_times.append(duration)

        self.last_state_change = now

    def record_connection_attempt(self, successful: bool) -> None:
        """Record the result of a connection attempt."""
        self.connection_attempts += 1
        if successful:
            self.successful_connections += 1
        else:
            self.failed_connections += 1

    def record_error(self, error: str) -> None:
        """Record a connection-related error."""
        self.errors[error] = self.errors.get(error, 0) + 1
        self.last_error = error
        self.last_error_time = datetime.now()

    def get_summary(self) -> dict:
        """Get a summary of connection metrics."""
        return {
            "current_state": self.current_state.value,
            "total_attempts": self.connection_attempts,
            "success_rate": (self.successful_connections / self.connection_attempts * 100
                           if self.connection_attempts > 0 else 0),
            "avg_connection_time": mean(self.connection_times) if self.connection_times else 0,
            "median_connection_time": median(self.connection_times) if self.connection_times else 0,
            "total_errors": sum(self.errors.values()),
            "uptime_percentage": (sum(self.uptime_periods) /
                                (datetime.now() - self.state_changes[0][0]).total_seconds() * 100
                                if self.state_changes else 0),
            "error_frequency": self.errors
        }

@dataclass
class QueueMetrics:
    """
    Tracks queue-related metrics and statistics.
    """
    # Message tracking
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: Dict[LogLevel, int] = field(default_factory=dict)
    messages_by_level: Dict[LogLevel, int] = field(default_factory=dict)

    # Batch tracking
    batch_sizes: List[int] = field(default_factory=list)
    batch_processing_times: List[float] = field(default_factory=list)

    # Queue size tracking
    queue_size_history: List[Tuple[datetime, int]] = field(default_factory=list)
    peak_queue_size: int = 0

    # Performance metrics
    processing_start_times: Dict[str, datetime] = field(default_factory=dict)
    retry_counts: Dict[str, int] = field(default_factory=dict)

    def record_message_queued(self, level: LogLevel) -> None:
        """Record a message being queued."""
        self.total_messages += 1
        self.messages_by_level[level] = self.messages_by_level.get(level, 0) + 1

        current_size = len(self.queue_size_history)
        self.queue_size_history.append((datetime.now(), current_size))
        self.peak_queue_size = max(self.peak_queue_size, current_size)

    def record_batch_processing(
        self,
        batch_size: int,
        successful: int,
        failed: int,
        processing_time: float
    ) -> None:
        """Record batch processing results."""
        self.batch_sizes.append(batch_size)
        self.batch_processing_times.append(processing_time)
        self.processed_messages += successful

    def record_message_failure(self, level: LogLevel, message_id: str) -> None:
        """Record a message processing failure."""
        self.failed_messages[level] = self.failed_messages.get(level, 0) + 1
        self.retry_counts[message_id] = self.retry_counts.get(message_id, 0) + 1

    def start_processing(self, message_id: str) -> None:
        """Record the start of message processing."""
        self.processing_start_times[message_id] = datetime.now()

    def end_processing(self, message_id: str) -> Optional[float]:
        """Record the end of message processing and return processing time."""
        if message_id in self.processing_start_times:
            start_time = self.processing_start_times.pop(message_id)
            return (datetime.now() - start_time).total_seconds()
        return None

    def get_summary(self) -> dict:
        """Get a summary of queue metrics."""
        return {
            "total_messages": self.total_messages,
            "processed_messages": self.processed_messages,
            "failed_messages": sum(self.failed_messages.values()),
            "success_rate": (self.processed_messages / self.total_messages * 100
                           if self.total_messages > 0 else 0),
            "average_batch_size": mean(self.batch_sizes) if self.batch_sizes else 0,
            "average_processing_time": mean(self.batch_processing_times)
                                     if self.batch_processing_times else 0,
            "peak_queue_size": self.peak_queue_size,
            "messages_by_level": {level.name: count
                                for level, count in self.messages_by_level.items()},
            "retry_distribution": {
                "no_retry": len([c for c in self.retry_counts.values() if c == 0]),
                "single_retry": len([c for c in self.retry_counts.values() if c == 1]),
                "multiple_retries": len([c for c in self.retry_counts.values() if c > 1])
            }
        }