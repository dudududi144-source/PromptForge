"""Tests for observability module."""
import pytest
from promptforge.core.observability import MetricsCollector, generate_request_id


class TestMetricsCollector:
    def test_record_metric(self):
        mc = MetricsCollector()
        mc.record("test.metric", 42.0)
        metrics = mc.get_metrics("test.metric")
        assert len(metrics) == 1
        assert metrics[0]["value"] == 42.0

    def test_generate_request_id(self):
        rid = generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 36