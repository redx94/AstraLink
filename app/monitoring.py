from prometheus_client import Counter, Histogram, Gauge, Summary
from opentelemetry import trace
import logging
import time

logger = logging.getLogger(__name__)

class Metrics:
    def __init__(self):
        self.request_counter = Counter(
            'astralink_requests_total',
            'Total requests',
            ['method', 'path', 'status_code']
        )
        self.request_duration = Histogram(
            'astralink_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'path']
        )
        self.quantum_operations = Counter(
            'astralink_quantum_operations_total',
            'Total quantum operations',
            ['operation_type']
        )
        self.active_connections = Gauge(
            'astralink_active_connections',
            'Number of active connections'
        )
        self.latency_summary = Summary(
            'astralink_latency_summary',
            'Request latency summary',
            ['endpoint']
        )
        self.error_histogram = Histogram(
            'astralink_error_histogram',
            'Error distribution histogram',
            ['error_type']
        )

    def observe_request(self, request_id: str, path: str, method: str, 
                       status_code: int, duration: float):
        self.request_counter.labels(method=method, path=path, 
                                  status_code=status_code).inc()
        self.request_duration.labels(method=method, path=path).observe(duration)
        logger.info(f"Request {request_id} completed: {method} {path} {status_code} {duration:.2f}s")

    def observe_error(self, request_id: str, error: str):
        logger.error(f"Request {request_id} failed: {error}")

    async def track_operation(self, operation_name: str, callback):
        start_time = time.time()
        try:
            result = await callback()
            self.latency_summary.labels(operation_name).observe(
                time.time() - start_time
            )
            return result
        except Exception as e:
            self.error_histogram.labels(type(e).__name__).observe(
                time.time() - start_time
            )
            raise

metrics = Metrics()
