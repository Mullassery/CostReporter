"""
OpenTelemetry export for observability stacks.
Enables exporting PyCostAudit metrics and traces to observability backends.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import time


class ExportFormat(Enum):
    """Export formats for observability backends"""
    JAEGER = "jaeger"  # Jaeger/OTLP
    PROMETHEUS = "prometheus"  # Prometheus
    DATADOG = "datadog"  # Datadog APM
    NEW_RELIC = "new_relic"  # New Relic
    GENERIC_OTLP = "generic_otlp"  # Generic OTLP


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"  # Total count (monotonically increasing)
    GAUGE = "gauge"  # Current value
    HISTOGRAM = "histogram"  # Distribution
    SUMMARY = "summary"  # Percentiles


@dataclass
class Metric:
    """OpenTelemetry metric"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    attributes: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Span:
    """OpenTelemetry span/trace"""
    trace_id: str
    span_id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    parent_span_id: Optional[str] = None
    status: str = "OK"  # OK, ERROR
    attributes: Dict[str, str] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Log:
    """OpenTelemetry log"""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collect PyCostAudit metrics"""

    def __init__(self):
        self.metrics: List[Metric] = []

    def record_cost_metric(
        self,
        total_cost: float,
        daily_cost: float,
        org_id: str,
        dept_id: Optional[str] = None
    ) -> Metric:
        """Record cost metric"""
        metric = Metric(
            name="pycostaudit.cost.total",
            type=MetricType.GAUGE,
            value=total_cost,
            timestamp=datetime.utcnow(),
            attributes={
                "org_id": org_id,
                "dept_id": dept_id or "root",
                "type": "total"
            },
            unit="USD",
            description="Total cost"
        )

        self.metrics.append(metric)

        # Also record daily cost
        daily_metric = Metric(
            name="pycostaudit.cost.daily",
            type=MetricType.GAUGE,
            value=daily_cost,
            timestamp=datetime.utcnow(),
            attributes={
                "org_id": org_id,
                "dept_id": dept_id or "root"
            },
            unit="USD",
            description="Daily cost"
        )

        self.metrics.append(daily_metric)
        return metric

    def record_token_metric(
        self,
        input_tokens: int,
        output_tokens: int,
        org_id: str,
        provider: str,
        model: str
    ) -> Metric:
        """Record token consumption metric"""
        metric = Metric(
            name="pycostaudit.tokens.total",
            type=MetricType.COUNTER,
            value=input_tokens + output_tokens,
            timestamp=datetime.utcnow(),
            attributes={
                "org_id": org_id,
                "provider": provider,
                "model": model,
                "input_tokens": str(input_tokens),
                "output_tokens": str(output_tokens)
            },
            unit="tokens",
            description="Total tokens consumed"
        )

        self.metrics.append(metric)
        return metric

    def record_operation_metric(
        self,
        operation_type: str,
        duration_ms: float,
        status: str,
        cost: float,
        org_id: str
    ) -> Metric:
        """Record operation metric"""
        metric = Metric(
            name="pycostaudit.operation.duration",
            type=MetricType.HISTOGRAM,
            value=duration_ms,
            timestamp=datetime.utcnow(),
            attributes={
                "operation_type": operation_type,
                "status": status,
                "org_id": org_id,
                "cost": str(cost)
            },
            unit="ms",
            description="Operation duration"
        )

        self.metrics.append(metric)
        return metric

    def record_anomaly_metric(
        self,
        anomaly_count: int,
        org_id: str,
        severity: str = "medium"
    ) -> Metric:
        """Record anomaly detection metric"""
        metric = Metric(
            name="pycostaudit.anomalies.detected",
            type=MetricType.COUNTER,
            value=anomaly_count,
            timestamp=datetime.utcnow(),
            attributes={
                "org_id": org_id,
                "severity": severity
            },
            description="Anomalies detected"
        )

        self.metrics.append(metric)
        return metric

    def record_budget_metric(
        self,
        budget_total: float,
        budget_used: float,
        org_id: str,
        dept_id: str
    ) -> Metric:
        """Record budget utilization metric"""
        percentage = (budget_used / budget_total * 100) if budget_total > 0 else 0

        metric = Metric(
            name="pycostaudit.budget.utilization",
            type=MetricType.GAUGE,
            value=percentage,
            timestamp=datetime.utcnow(),
            attributes={
                "org_id": org_id,
                "dept_id": dept_id,
                "budget_total": str(budget_total),
                "budget_used": str(budget_used)
            },
            unit="%",
            description="Budget utilization percentage"
        )

        self.metrics.append(metric)
        return metric

    def get_all_metrics(self) -> List[Metric]:
        """Get all collected metrics"""
        return self.metrics

    def clear_metrics(self):
        """Clear metrics"""
        self.metrics = []


class TraceCollector:
    """Collect execution traces/spans"""

    def __init__(self):
        self.spans: List[Span] = []
        self.trace_counter = 0

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, str]] = None
    ) -> Span:
        """Start a new span"""
        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            start_time=datetime.utcnow(),
            attributes=attributes or {}
        )

        self.spans.append(span)
        return span

    def end_span(
        self,
        span: Span,
        status: str = "OK",
        error_message: Optional[str] = None
    ):
        """End a span"""
        span.end_time = datetime.utcnow()
        span.status = status

        if error_message:
            span.events.append({
                "name": "exception",
                "timestamp": datetime.utcnow(),
                "attributes": {"exception.message": error_message}
            })

    def add_span_event(
        self,
        span: Span,
        event_name: str,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Add event to span"""
        span.events.append({
            "name": event_name,
            "timestamp": datetime.utcnow(),
            "attributes": attributes or {}
        })

    def get_all_spans(self) -> List[Span]:
        """Get all collected spans"""
        return self.spans

    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        self.trace_counter += 1
        return f"trace_{int(time.time())}_{self.trace_counter}"

    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        return f"span_{int(time.time() * 1000)}"


class ObservabilityExporter:
    """Export metrics and traces to observability backends"""

    def __init__(self, format: ExportFormat):
        self.format = format
        self.metrics_collector = MetricsCollector()
        self.trace_collector = TraceCollector()

    def export_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Export collected metrics"""
        metrics = self.metrics_collector.get_all_metrics()

        if self.format == ExportFormat.PROMETHEUS:
            return self._export_prometheus(metrics, endpoint)
        elif self.format == ExportFormat.JAEGER:
            return self._export_jaeger(metrics, endpoint)
        elif self.format == ExportFormat.DATADOG:
            return self._export_datadog(metrics, endpoint)
        elif self.format == ExportFormat.NEW_RELIC:
            return self._export_new_relic(metrics, endpoint)
        else:
            return self._export_otlp(metrics, endpoint)

    def export_traces(self, endpoint: str) -> Dict[str, Any]:
        """Export collected traces"""
        spans = self.trace_collector.get_all_spans()

        if self.format == ExportFormat.JAEGER:
            return self._export_jaeger_traces(spans, endpoint)
        elif self.format == ExportFormat.DATADOG:
            return self._export_datadog_traces(spans, endpoint)
        elif self.format == ExportFormat.NEW_RELIC:
            return self._export_new_relic_traces(spans, endpoint)
        else:
            return self._export_otlp_traces(spans, endpoint)

    def _export_prometheus(self, metrics: List[Metric], endpoint: str) -> Dict[str, Any]:
        """Export to Prometheus format"""
        output = []

        for metric in metrics:
            # Prometheus text format
            metric_name = metric.name.replace(".", "_")
            attributes_str = ",".join(
                f'{k}="{v}"' for k, v in metric.attributes.items()
            )

            if attributes_str:
                line = f"{metric_name}{{{attributes_str}}} {metric.value}"
            else:
                line = f"{metric_name} {metric.value}"

            output.append(line)

        return {
            "format": "prometheus",
            "endpoint": endpoint,
            "metrics_count": len(metrics),
            "output": "\n".join(output)
        }

    def _export_jaeger(self, metrics: List[Metric], endpoint: str) -> Dict[str, Any]:
        """Export to Jaeger format"""
        return {
            "format": "jaeger",
            "endpoint": endpoint,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "type": m.type.value,
                    "timestamp": m.timestamp.isoformat(),
                    "tags": m.attributes
                }
                for m in metrics
            ]
        }

    def _export_datadog(self, metrics: List[Metric], endpoint: str) -> Dict[str, Any]:
        """Export to Datadog format"""
        return {
            "format": "datadog",
            "endpoint": endpoint,
            "series": [
                {
                    "metric": m.name,
                    "points": [[int(m.timestamp.timestamp()), m.value]],
                    "type": m.type.value,
                    "tags": [f"{k}:{v}" for k, v in m.attributes.items()]
                }
                for m in metrics
            ]
        }

    def _export_new_relic(self, metrics: List[Metric], endpoint: str) -> Dict[str, Any]:
        """Export to New Relic format"""
        return {
            "format": "new_relic",
            "endpoint": endpoint,
            "metrics": [
                {
                    "name": m.name,
                    "type": m.type.value,
                    "value": m.value,
                    "timestamp": int(m.timestamp.timestamp() * 1000),
                    "attributes": m.attributes
                }
                for m in metrics
            ]
        }

    def _export_otlp(self, metrics: List[Metric], endpoint: str) -> Dict[str, Any]:
        """Export to generic OTLP format"""
        return {
            "format": "otlp",
            "endpoint": endpoint,
            "metrics": [
                {
                    "name": m.name,
                    "type": m.type.value,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "unit": m.unit,
                    "attributes": m.attributes,
                    "description": m.description
                }
                for m in metrics
            ]
        }

    def _export_jaeger_traces(self, spans: List[Span], endpoint: str) -> Dict[str, Any]:
        """Export traces to Jaeger"""
        return {
            "format": "jaeger_traces",
            "endpoint": endpoint,
            "traces": [
                {
                    "trace_id": s.trace_id,
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "operation_name": s.name,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "duration_ms": (
                        (s.end_time - s.start_time).total_seconds() * 1000
                        if s.end_time else 0
                    ),
                    "status": s.status,
                    "tags": s.attributes,
                    "logs": s.events
                }
                for s in spans
            ]
        }

    def _export_datadog_traces(self, spans: List[Span], endpoint: str) -> Dict[str, Any]:
        """Export traces to Datadog"""
        return {
            "format": "datadog_traces",
            "endpoint": endpoint,
            "traces": [
                {
                    "trace_id": s.trace_id,
                    "span_id": s.span_id,
                    "parent_id": s.parent_span_id,
                    "name": s.name,
                    "start": int(s.start_time.timestamp() * 1000000),
                    "duration": (
                        int((s.end_time - s.start_time).total_seconds() * 1000000)
                        if s.end_time else 0
                    ),
                    "error": 1 if s.status == "ERROR" else 0,
                    "meta": s.attributes
                }
                for s in spans
            ]
        }

    def _export_new_relic_traces(self, spans: List[Span], endpoint: str) -> Dict[str, Any]:
        """Export traces to New Relic"""
        return {
            "format": "new_relic_traces",
            "endpoint": endpoint,
            "spans": [
                {
                    "trace.id": s.trace_id,
                    "span.id": s.span_id,
                    "parent.id": s.parent_span_id,
                    "name": s.name,
                    "timestamp": int(s.start_time.timestamp() * 1000),
                    "duration.ms": (
                        (s.end_time - s.start_time).total_seconds() * 1000
                        if s.end_time else 0
                    ),
                    "status": s.status,
                    **s.attributes
                }
                for s in spans
            ]
        }

    def _export_otlp_traces(self, spans: List[Span], endpoint: str) -> Dict[str, Any]:
        """Export traces to generic OTLP"""
        return {
            "format": "otlp_traces",
            "endpoint": endpoint,
            "resource_spans": [
                {
                    "trace_id": s.trace_id,
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "start_time_unix_nano": int(s.start_time.timestamp() * 1e9),
                    "end_time_unix_nano": (
                        int(s.end_time.timestamp() * 1e9) if s.end_time else 0
                    ),
                    "status": {
                        "code": 0 if s.status == "OK" else 1,
                        "message": s.status
                    },
                    "attributes": s.attributes,
                    "events": s.events
                }
                for s in spans
            ]
        }


class ExportConfig:
    """Configuration for observability export"""

    def __init__(
        self,
        format: ExportFormat,
        endpoint: str,
        batch_size: int = 100,
        export_interval_seconds: int = 60,
        api_key: Optional[str] = None
    ):
        self.format = format
        self.endpoint = endpoint
        self.batch_size = batch_size
        self.export_interval_seconds = export_interval_seconds
        self.api_key = api_key
        self.enabled = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "format": self.format.value,
            "endpoint": self.endpoint,
            "batch_size": self.batch_size,
            "export_interval_seconds": self.export_interval_seconds,
            "enabled": self.enabled
        }
