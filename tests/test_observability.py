"""
Tests for observability export system.
"""

import pytest
from datetime import datetime, timedelta
from pycostaudit.observability_export import (
    MetricsCollector,
    TraceCollector,
    ObservabilityExporter,
    ExportFormat,
    MetricType,
    Metric,
    ExportConfig
)


@pytest.fixture
def metrics_collector():
    """Create metrics collector"""
    return MetricsCollector()


@pytest.fixture
def trace_collector():
    """Create trace collector"""
    return TraceCollector()


@pytest.fixture
def exporter():
    """Create exporter"""
    return ObservabilityExporter(ExportFormat.PROMETHEUS)


class TestMetricsCollector:
    """Test metrics collection"""

    def test_record_cost_metric(self, metrics_collector):
        """Test recording cost metric"""
        metric = metrics_collector.record_cost_metric(
            total_cost=1000.0,
            daily_cost=50.0,
            org_id="acme"
        )

        assert metric.name == "pycostaudit.cost.total"
        assert metric.value == 1000.0
        assert metric.unit == "USD"

    def test_record_token_metric(self, metrics_collector):
        """Test recording token metric"""
        metric = metrics_collector.record_token_metric(
            input_tokens=10000,
            output_tokens=5000,
            org_id="acme",
            provider="anthropic",
            model="claude-3-5-sonnet"
        )

        assert metric.name == "pycostaudit.tokens.total"
        assert metric.value == 15000  # input + output
        assert metric.type == MetricType.COUNTER

    def test_record_operation_metric(self, metrics_collector):
        """Test recording operation metric"""
        metric = metrics_collector.record_operation_metric(
            operation_type="cost_analysis",
            duration_ms=245.5,
            status="success",
            cost=10.0,
            org_id="acme"
        )

        assert metric.name == "pycostaudit.operation.duration"
        assert metric.value == 245.5
        assert metric.type == MetricType.HISTOGRAM

    def test_record_anomaly_metric(self, metrics_collector):
        """Test recording anomaly metric"""
        metric = metrics_collector.record_anomaly_metric(
            anomaly_count=3,
            org_id="acme",
            severity="high"
        )

        assert metric.name == "pycostaudit.anomalies.detected"
        assert metric.value == 3
        assert metric.type == MetricType.COUNTER

    def test_record_budget_metric(self, metrics_collector):
        """Test recording budget metric"""
        metric = metrics_collector.record_budget_metric(
            budget_total=1000.0,
            budget_used=750.0,
            org_id="acme",
            dept_id="eng"
        )

        assert metric.name == "pycostaudit.budget.utilization"
        assert metric.value == 75.0
        assert metric.unit == "%"

    def test_get_all_metrics(self, metrics_collector):
        """Test retrieving all metrics"""
        metrics_collector.record_cost_metric(100.0, 50.0, "acme")
        metrics_collector.record_token_metric(1000, 500, "acme", "anthropic", "sonnet")

        all_metrics = metrics_collector.get_all_metrics()
        assert len(all_metrics) >= 2

    def test_clear_metrics(self, metrics_collector):
        """Test clearing metrics"""
        metrics_collector.record_cost_metric(100.0, 50.0, "acme")
        assert len(metrics_collector.get_all_metrics()) > 0

        metrics_collector.clear_metrics()
        assert len(metrics_collector.get_all_metrics()) == 0


class TestTraceCollector:
    """Test trace/span collection"""

    def test_start_span(self, trace_collector):
        """Test starting span"""
        span = trace_collector.start_span(
            "cost_analysis",
            {"org_id": "acme"}
        )

        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.name == "cost_analysis"
        assert span.status == "OK"

    def test_end_span(self, trace_collector):
        """Test ending span"""
        span = trace_collector.start_span("operation")
        trace_collector.end_span(span, status="OK")

        assert span.end_time is not None
        assert span.status == "OK"

    def test_end_span_with_error(self, trace_collector):
        """Test ending span with error"""
        span = trace_collector.start_span("operation")
        trace_collector.end_span(span, status="ERROR", error_message="Operation failed")

        assert span.status == "ERROR"
        assert len(span.events) > 0
        assert span.events[0]["name"] == "exception"

    def test_add_span_event(self, trace_collector):
        """Test adding event to span"""
        span = trace_collector.start_span("operation")
        trace_collector.add_span_event(
            span,
            "data_processed",
            {"records": "1000"}
        )

        assert len(span.events) > 0
        assert span.events[0]["name"] == "data_processed"

    def test_get_all_spans(self, trace_collector):
        """Test retrieving all spans"""
        trace_collector.start_span("operation1")
        trace_collector.start_span("operation2")

        all_spans = trace_collector.get_all_spans()
        assert len(all_spans) == 2

    def test_trace_id_uniqueness(self, trace_collector):
        """Test trace ID uniqueness"""
        span1 = trace_collector.start_span("op1")
        span2 = trace_collector.start_span("op2")

        assert span1.trace_id != span2.trace_id


class TestPrometheusExport:
    """Test Prometheus export format"""

    def test_export_metrics_prometheus(self):
        """Test exporting to Prometheus format"""
        exporter = ObservabilityExporter(ExportFormat.PROMETHEUS)

        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")
        exporter.metrics_collector.record_token_metric(
            10000, 5000, "acme", "anthropic", "sonnet"
        )

        result = exporter.export_metrics("http://localhost:9090")

        assert result["format"] == "prometheus"
        assert "pycostaudit_cost_total" in result["output"]
        assert result["metrics_count"] >= 2

    def test_prometheus_format_structure(self):
        """Test Prometheus format structure"""
        exporter = ObservabilityExporter(ExportFormat.PROMETHEUS)
        exporter.metrics_collector.record_cost_metric(500.0, 25.0, "acme", "eng")

        result = exporter.export_metrics("http://localhost:9090")

        # Prometheus format should have metric name and value
        assert "{" in result["output"]  # Should have attributes
        assert "org_id=" in result["output"]


class TestJaegerExport:
    """Test Jaeger export format"""

    def test_export_traces_jaeger(self):
        """Test exporting traces to Jaeger"""
        exporter = ObservabilityExporter(ExportFormat.JAEGER)

        span = exporter.trace_collector.start_span(
            "cost_analysis",
            {"org_id": "acme"}
        )
        exporter.trace_collector.end_span(span)

        result = exporter.export_traces("http://localhost:14268/api/traces")

        assert result["format"] == "jaeger_traces"
        assert len(result["traces"]) > 0
        assert result["traces"][0]["operation_name"] == "cost_analysis"

    def test_jaeger_metrics_export(self):
        """Test exporting metrics to Jaeger"""
        exporter = ObservabilityExporter(ExportFormat.JAEGER)
        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")

        result = exporter.export_metrics("http://localhost:14268")

        assert result["format"] == "jaeger"
        assert "metrics" in result


class TestDatadogExport:
    """Test Datadog export format"""

    def test_export_metrics_datadog(self):
        """Test exporting to Datadog format"""
        exporter = ObservabilityExporter(ExportFormat.DATADOG)
        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")

        result = exporter.export_metrics("http://localhost/api/v1/series")

        assert result["format"] == "datadog"
        assert "series" in result
        assert len(result["series"]) > 0

    def test_export_traces_datadog(self):
        """Test exporting traces to Datadog"""
        exporter = ObservabilityExporter(ExportFormat.DATADOG)

        span = exporter.trace_collector.start_span("operation")
        exporter.trace_collector.end_span(span)

        result = exporter.export_traces("http://localhost/api/v1/traces")

        assert result["format"] == "datadog_traces"
        assert "traces" in result


class TestNewRelicExport:
    """Test New Relic export format"""

    def test_export_metrics_new_relic(self):
        """Test exporting to New Relic format"""
        exporter = ObservabilityExporter(ExportFormat.NEW_RELIC)
        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")

        result = exporter.export_metrics("http://localhost/api/v1/metrics")

        assert result["format"] == "new_relic"
        assert "metrics" in result
        assert len(result["metrics"]) > 0

    def test_export_traces_new_relic(self):
        """Test exporting traces to New Relic"""
        exporter = ObservabilityExporter(ExportFormat.NEW_RELIC)

        span = exporter.trace_collector.start_span("operation")
        exporter.trace_collector.end_span(span)

        result = exporter.export_traces("http://localhost/api/v1/traces")

        assert result["format"] == "new_relic_traces"
        assert "spans" in result


class TestOTLPExport:
    """Test generic OTLP export format"""

    def test_export_metrics_otlp(self):
        """Test exporting to generic OTLP format"""
        exporter = ObservabilityExporter(ExportFormat.GENERIC_OTLP)
        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")

        result = exporter.export_metrics("http://localhost:4317")

        assert result["format"] == "otlp"
        assert "metrics" in result

    def test_export_traces_otlp(self):
        """Test exporting traces to OTLP"""
        exporter = ObservabilityExporter(ExportFormat.GENERIC_OTLP)

        span = exporter.trace_collector.start_span("operation")
        exporter.trace_collector.end_span(span)

        result = exporter.export_traces("http://localhost:4317")

        assert result["format"] == "otlp_traces"
        assert "resource_spans" in result


class TestExportConfig:
    """Test export configuration"""

    def test_create_export_config(self):
        """Test creating export config"""
        config = ExportConfig(
            format=ExportFormat.PROMETHEUS,
            endpoint="http://localhost:9090",
            batch_size=100,
            export_interval_seconds=60
        )

        assert config.format == ExportFormat.PROMETHEUS
        assert config.endpoint == "http://localhost:9090"
        assert config.enabled is True

    def test_export_config_to_dict(self):
        """Test exporting config to dict"""
        config = ExportConfig(
            format=ExportFormat.JAEGER,
            endpoint="http://localhost:14268",
            batch_size=50,
            export_interval_seconds=30
        )

        config_dict = config.to_dict()

        assert config_dict["format"] == "jaeger"
        assert config_dict["batch_size"] == 50
        assert config_dict["export_interval_seconds"] == 30


class TestIntegration:
    """Integration tests"""

    def test_full_observability_pipeline(self):
        """Test complete observability pipeline"""
        exporter = ObservabilityExporter(ExportFormat.PROMETHEUS)

        # Record metrics
        exporter.metrics_collector.record_cost_metric(1000.0, 50.0, "acme")
        exporter.metrics_collector.record_token_metric(
            10000, 5000, "acme", "anthropic", "sonnet"
        )

        # Record traces
        span = exporter.trace_collector.start_span("cost_analysis")
        exporter.trace_collector.add_span_event(span, "data_collected")
        exporter.trace_collector.end_span(span)

        # Export
        metrics_export = exporter.export_metrics("http://localhost:9090")
        traces_export = exporter.export_traces("http://localhost:9090")

        assert metrics_export["metrics_count"] >= 2
        assert len(traces_export) > 0

    def test_multiple_exporters(self):
        """Test using multiple exporters"""
        exporters = [
            ObservabilityExporter(ExportFormat.PROMETHEUS),
            ObservabilityExporter(ExportFormat.JAEGER),
            ObservabilityExporter(ExportFormat.DATADOG)
        ]

        for exporter in exporters:
            exporter.metrics_collector.record_cost_metric(100.0, 50.0, "acme")

        # Each exporter has its own metrics
        for exporter in exporters:
            assert len(exporter.metrics_collector.get_all_metrics()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
