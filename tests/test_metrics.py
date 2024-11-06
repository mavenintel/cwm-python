import pytest
from datetime import datetime, timedelta
from codewatchman.core.config import CodeWatchmanConfig
from codewatchman.utils.metrics import MetricsAggregator

@pytest.fixture
def config():
    return CodeWatchmanConfig(
        project_id="test123",
        project_secret="secret456",
        enable_gpu=True,
        gpu_collect_interval=1.0
    )

def test_gpu_metrics_collection(config):
    aggregator = MetricsAggregator()

    # First collection should always collect GPU metrics
    aggregator.add_system_metrics(config)
    assert len(aggregator.system_metrics) == 1

    # Get metrics
    metrics = aggregator.get_latest_metrics()
    assert "system" in metrics

    # Verify GPU metrics format
    if metrics["system"].get("gpus"):
        for gpu in metrics["system"]["gpus"]:
            assert "vendor" in gpu
            assert "name" in gpu
            assert "memory_total" in gpu
            assert "memory_used" in gpu
            assert "utilization" in gpu

def test_gpu_collection_interval(config):
    aggregator = MetricsAggregator()

    # First collection
    assert aggregator.should_collect_gpu(config.gpu_collect_interval)
    aggregator.last_gpu_collection = datetime.now()

    # Immediate second collection should be skipped
    assert not aggregator.should_collect_gpu(config.gpu_collect_interval)

    # After interval, collection should be allowed
    aggregator.last_gpu_collection = datetime.now() - timedelta(seconds=config.gpu_collect_interval + 0.1)
    assert aggregator.should_collect_gpu(config.gpu_collect_interval)