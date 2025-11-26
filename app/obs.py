from contextlib import contextmanager
from typing import Dict, Iterator, Optional

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from .config import Settings


class Observability:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tracer_provider = TracerProvider()
        self._meter_provider = MeterProvider()
        trace.set_tracer_provider(self._tracer_provider)
        metrics.set_meter_provider(self._meter_provider)
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)

        self.request_counter = self.meter.create_counter(
            name="requests_total",
            description="Total requests",
        )
        self.latency_hist = self.meter.create_histogram(
            name="request_latency_ms",
            description="Request latency in ms",
            unit="ms",
        )
        self.inference_latency = self.meter.create_histogram(
            name="inference_latency_ms",
            description="Inference latency in ms",
            unit="ms",
        )
        self.rate_limit_hits = self.meter.create_counter(
            name="rate_limit_hits_total",
            description="Rate limit rejections",
        )

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict] = None) -> Iterator[None]:
        span = self.tracer.start_span(name=name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield
        finally:
            span.end()
