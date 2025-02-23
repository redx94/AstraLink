from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
import prometheus_client as prom
import asyncio
import logging

@dataclass
class MetricEvent:
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime = datetime.utcnow()

class MetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, prom.Counter] = {}
        self._gauges: Dict[str, prom.Gauge] = {}
        self._histograms: Dict[str, prom.Histogram] = {}
        self._events: List[MetricEvent] = []
        self._setup_default_metrics()

    def _setup_default_metrics(self):
        self._metrics["quantum_operations"] = prom.Counter(
            "quantum_operations_total",
            "Total number of quantum operations",
            ["operation_type", "status"]
        )
        
        self._gauges["system_health"] = prom.Gauge(
            "system_health",
            "System health status",
            ["component"]
        )

        self._histograms["operation_latency"] = prom.Histogram(
            "operation_latency_seconds",
            "Operation latency in seconds",
            ["operation_type"]
        )

    async def collect_metrics(self):
        while True:
            try:
                await self._process_metrics()
                await asyncio.sleep(10)
            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")

    async def _process_metrics(self):
        # Process collected metrics
        for event in self._events:
            if event.name in self._metrics:
                self._metrics[event.name].labels(**event.labels).inc(event.value)
            elif event.name in self._gauges:
                self._gauges[event.name].labels(**event.labels).set(event.value)

        self._events.clear()

    def record_event(self, event: MetricEvent):
        self._events.append(event)
