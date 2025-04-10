"""
AstraLink - System Monitoring Module
================================

This module implements system monitoring using Prometheus metrics and OpenTelemetry
tracing for request tracking, latency measurement, and error observation.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Enum
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import logging
import time
from typing import Optional, Dict, Any
from app.exceptions import AstraLinkException

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
        
        # Enhanced error metrics
        self.error_counter = Counter(
            'astralink_errors_total',
            'Total number of errors by type and severity',
            ['error_type', 'severity']
        )
        self.error_histogram = Histogram(
            'astralink_error_duration_seconds',
            'Error resolution time in seconds',
            ['error_type', 'severity']
        )
        self.error_severity = Enum(
            'astralink_error_severity',
            'Current highest error severity level',
            states=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )

    def observe_request(self, request_id: str, path: str, method: str, 
                       status_code: int, duration: float):
        self.request_counter.labels(method=method, path=path, 
                                  status_code=status_code).inc()
        self.request_duration.labels(method=method, path=path).observe(duration)
        logger.info(f"Request {request_id} completed: {method} {path} {status_code} {duration:.2f}s")

    def observe_error(self, error: Exception, correlation_id: Optional[str] = None, 
                     context: Optional[Dict[str, Any]] = None) -> None:
        """Enhanced error observation with severity tracking and context"""
        error_type = type(error).__name__
        severity = 'HIGH'  # Default severity
        
        if isinstance(error, AstraLinkException):
            error_type = error.error_code
            severity = self._get_error_severity(error)
            
        # Increment error counter with severity
        self.error_counter.labels(error_type=error_type, severity=severity).inc()
        
        # Update current error severity state
        self.error_severity.state(severity)
        
        # Log error with correlation ID and context
        log_context = {
            'error_type': error_type,
            'severity': severity,
            'correlation_id': correlation_id
        }
        if context:
            log_context.update(context)
        
        logger.error(
            f"Error occurred: {str(error)}", 
            extra={
                'correlation_id': correlation_id,
                'context': log_context
            }
        )
        
    def _get_error_severity(self, error: AstraLinkException) -> str:
        """Map exception types to severity levels"""
        if error.error_code.startswith(('SYSTEM_', 'CRITICAL_')):
            return 'CRITICAL'
        elif error.error_code.startswith(('QUANTUM_', 'AI_')):
            return 'HIGH'
        elif error.error_code.startswith('VALIDATION_'):
            return 'MEDIUM'
        return 'LOW'

    async def track_operation(self, operation_name: str, callback, correlation_id: Optional[str] = None):
        """Enhanced operation tracking with error handling"""
        start_time = time.time()
        span = trace.get_current_span()
        
        try:
            result = await callback()
            duration = time.time() - start_time
            
            self.latency_summary.labels(operation_name).observe(duration)
            span.set_status(Status(StatusCode.OK))
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Track error metrics
            self.observe_error(
                error=e,
                correlation_id=correlation_id,
                context={'operation': operation_name, 'duration': duration}
            )
            
            # Update span with error information
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            
            # Track error duration
            if isinstance(e, AstraLinkException):
                self.error_histogram.labels(
                    error_type=e.error_code,
                    severity=self._get_error_severity(e)
                ).observe(duration)
            else:
                self.error_histogram.labels(
                    error_type=type(e).__name__,
                    severity='HIGH'
                ).observe(duration)
            
            raise

metrics = Metrics()
