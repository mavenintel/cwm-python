from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from statistics import mean, median
import psutil
import os
import platform
import subprocess
import json
import logging

from ..core.config import CodeWatchmanConfig
from ..core.constants import ConnectionState, LogLevel

@dataclass
class GPUMetrics:
    """GPU-specific metrics for both NVIDIA and Apple Silicon."""
    vendor: str = "unknown"  # nvidia, apple, or unknown
    name: str = "unknown"
    memory_total: int = 0      # in MB
    memory_used: int = 0       # in MB
    memory_free: int = 0       # in MB
    utilization: float = 0.0   # in percentage
    temperature: float = 0.0   # in Celsius
    power_usage: float = 0.0   # in Watts

    @classmethod
    def collect(cls, enable_gpu: bool) -> List[GPUMetrics]:
        """Collect GPU metrics based on available hardware."""
        try:
            if enable_gpu:
                if platform.system() == "Darwin" and platform.processor() == "arm":
                    return cls._collect_apple_gpu()
                else:
                    nvidia_gpus = cls._collect_nvidia_gpu()
                    if nvidia_gpus:
                        return nvidia_gpus
            return []
        except Exception as e:
            logging.warning(f"Failed to collect GPU metrics: {str(e)}")
            return []

    @classmethod
    def _collect_nvidia_gpu(cls) -> List[GPUMetrics]:
        """Collect NVIDIA GPU metrics using nvidia-smi."""
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            gpus = []

            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) < 7:
                        continue  # Skip incomplete lines
                    name, mem_total, mem_used, mem_free, util, temp, power = parts[:7]
                    gpus.append(cls(
                        vendor="nvidia",
                        name=name.strip(),
                        memory_total=int(float(mem_total)),
                        memory_used=int(float(mem_used)),
                        memory_free=int(float(mem_free)),
                        utilization=float(util),
                        temperature=float(temp),
                        power_usage=float(power) if power.strip().lower() != "n/a" else 0.0
                    ))
            return gpus
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logging.warning(f"Failed to collect NVIDIA GPU metrics: {str(e)}")
            return []

    @classmethod
    def _collect_apple_gpu(cls) -> List[GPUMetrics]:
        """Collect Apple Silicon GPU metrics using powermetrics."""
        try:
            # Need sudo access for powermetrics
            cmd = ["sudo", "powermetrics", "-s", "gpu", "-n", "1", "--format", "json"]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Extract GPU metrics from powermetrics output
            gpu_stats = data.get("gpu_stats", {})

            return [cls(
                vendor="apple",
                name="Apple Silicon GPU",
                memory_total=gpu_stats.get("gpu_memory_total", 0),
                memory_used=gpu_stats.get("gpu_memory_used", 0),
                memory_free=gpu_stats.get("gpu_memory_total", 0) - gpu_stats.get("gpu_memory_used", 0),
                utilization=gpu_stats.get("gpu_utilization", 0.0),
                temperature=gpu_stats.get("gpu_temperature", 0.0),
                power_usage=gpu_stats.get("gpu_power", 0.0)
            )]
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError) as e:
            logging.warning(f"Failed to collect Apple GPU metrics: {str(e)}")
            return []

@dataclass
class SystemMetrics:
    """System-level metrics collection."""
    enable_gpu: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    cpu_freq: Optional[float] = None

    # Memory metrics
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0

    # Disk metrics
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0

    # Process metrics
    process_id: int = 0
    process_memory: float = 0.0
    process_threads: int = 0

    # System info
    platform_system: str = ""
    platform_release: str = ""
    platform_version: str = ""
    python_version: str = ""

    # GPU metrics
    gpus: List[GPUMetrics] = field(default_factory=list)

    @classmethod
    def collect(cls, enable_gpu: bool = False) -> SystemMetrics:
        """Collect current system metrics."""
        metrics = cls(enable_gpu=enable_gpu)

        # CPU information
        metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        metrics.cpu_freq = cpu_freq.current if cpu_freq else None

        # Memory information
        mem = psutil.virtual_memory()
        metrics.memory_total = mem.total
        metrics.memory_available = mem.available
        metrics.memory_used = mem.used
        metrics.memory_percent = mem.percent

        # Disk information
        disk = psutil.disk_usage('/')
        metrics.disk_total = disk.total
        metrics.disk_used = disk.used
        metrics.disk_free = disk.free
        metrics.disk_percent = disk.percent

        # Process information
        process = psutil.Process(os.getpid())
        metrics.process_id = process.pid
        metrics.process_memory = process.memory_percent()
        metrics.process_threads = process.num_threads()

        # System information
        metrics.platform_system = platform.system()
        metrics.platform_release = platform.release()
        metrics.platform_version = platform.version()
        metrics.python_version = platform.python_version()

        # GPU metrics (only if enabled)
        if enable_gpu:
            metrics.gpus = GPUMetrics.collect(enable_gpu=True)

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        result = self.__dict__.copy()
        if not self.enable_gpu:
            result.pop('gpus', None)
        else:
            result['gpus'] = [gpu.__dict__ for gpu in self.gpus]
        return result

@dataclass
class ConnectionMetrics:
    """Metrics related to WebSocket connections."""
    current_state: ConnectionState = ConnectionState.DISCONNECTED
    connection_attempts: int = 0
    successful_connections: int = 0
    connection_times: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=dict)
    uptime_periods: List[float] = field(default_factory=list)
    state_changes: List[Tuple[datetime, ConnectionState]] = field(default_factory=list)

    def record_state_change(self, old_state: ConnectionState, new_state: ConnectionState) -> None:
        """Record a change in connection state."""
        self.state_changes.append((datetime.now(), new_state))
        if new_state == ConnectionState.CONNECTED:
            self.successful_connections += 1
        elif new_state == ConnectionState.DISCONNECTED:
            if self.state_changes:
                last_change_time, _ = self.state_changes[-2] if len(self.state_changes) > 1 else (datetime.now(), old_state)
                uptime = (datetime.now() - last_change_time).total_seconds()
                self.uptime_periods.append(uptime)
        self.current_state = new_state

    def record_connection_attempt(self, success: bool) -> None:
        """Record a connection attempt."""
        self.connection_attempts += 1
        if success:
            self.successful_connections += 1
        else:
            self.errors["connection_failed"] = self.errors.get("connection_failed", 0) + 1

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
    """Metrics related to the message queue."""
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: Dict[str, int] = field(default_factory=dict)
    batch_sizes: List[int] = field(default_factory=list)
    batch_processing_times: List[float] = field(default_factory=list)
    peak_queue_size: int = 0
    messages_by_level: Dict[LogLevel, int] = field(default_factory=dict)
    retry_counts: Dict[int, int] = field(default_factory=dict)

    def record_message(self, level: LogLevel) -> None:
        """Record a new message."""
        self.total_messages += 1
        self.messages_by_level[level] = self.messages_by_level.get(level, 0) + 1
        if self.total_messages > self.peak_queue_size:
            self.peak_queue_size = self.total_messages

    def record_processed_message(self, success: bool) -> None:
        """Record a processed message."""
        self.processed_messages += 1 if success else 0
        if not success:
            self.failed_messages["processing_failed"] = self.failed_messages.get("processing_failed", 0) + 1

    def record_batch_processing(self, batch_size: int, success_count: int, failure_count: int) -> None:
        """Record batch processing statistics."""
        self.batch_sizes.append(batch_size)
        # Assuming processing time is handled elsewhere or can be added
        self.processed_messages += success_count
        for _ in range(failure_count):
            self.failed_messages["batch_failure"] = self.failed_messages.get("batch_failure", 0) + 1

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

@dataclass
class MetricsAggregator:
    """Aggregates various metrics types."""
    connection_metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    queue_metrics: QueueMetrics = field(default_factory=QueueMetrics)
    system_metrics: List[SystemMetrics] = field(default_factory=list)
    max_history: int = 100  # Maximum number of system metrics to keep
    last_gpu_collection: Optional[datetime] = None
    config: CodeWatchmanConfig = field(default=None)  # Add config field

    def should_collect_gpu(self, interval: float) -> bool:
        """Check if it's time to collect GPU metrics based on interval."""
        if not self.last_gpu_collection:
            return True
        time_since_last = datetime.now() - self.last_gpu_collection
        return time_since_last.total_seconds() >= interval

    def add_system_metrics(self, config: CodeWatchmanConfig) -> None:
        """Collect and add current system metrics."""
        collect_gpu = False
        if config.enable_gpu and self.should_collect_gpu(config.gpu_collect_interval):
            collect_gpu = True
            self.last_gpu_collection = datetime.now()

        metrics = SystemMetrics.collect(enable_gpu=collect_gpu)
        self.system_metrics.append(metrics)

        # Maintain history limit
        if len(self.system_metrics) > self.max_history:
            self.system_metrics = self.system_metrics[-self.max_history:]

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics from all sources."""
        latest = {
            "connection": self.connection_metrics.get_summary(),
            "queue": self.queue_metrics.get_summary(),
            "timestamp": datetime.now().isoformat()
        }

        if self.system_metrics:
            latest_system = self.system_metrics[-1]
            system_dict = latest_system.to_dict()
            latest["system"] = system_dict

        return latest