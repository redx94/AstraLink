import asyncio
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from app.logging_config import StructuredLogger, MetricsCollector

@dataclass
class HealthStatus:
    status: str
    message: str
    timestamp: str
    checks: Dict[str, Any]

class SystemMonitor:
    """System-wide monitoring and health checks"""
    
    def __init__(self):
        self.logger = StructuredLogger("SystemMonitor")
        self.metrics = MetricsCollector()
        self.health_checks = {}
        self.alert_thresholds = {
            "cpu_usage": 80.0,  # 80%
            "memory_usage": 85.0,  # 85%
            "latency": 100.0,  # 100ms
            "error_rate": 1.0,  # 1%
            "quantum_error_rate": 0.1  # 0.1%
        }
    
    async def check_system_health(self) -> HealthStatus:
        """Perform comprehensive system health check"""
        try:
            checks = {}
            status = "healthy"
            message = "All systems operational"
            
            # Perform individual health checks
            checks["quantum_system"] = await self._check_quantum_health()
            checks["network"] = await self._check_network_health()
            checks["resources"] = await self._check_resource_usage()
            checks["security"] = await self._check_security_status()
            
            # Determine overall system status
            if any(check.get("status") == "critical" for check in checks.values()):
                status = "critical"
                message = "Critical system issues detected"
            elif any(check.get("status") == "warning" for check in checks.values()):
                status = "warning"
                message = "System warnings detected"
                
            self.metrics.record_metric("system_health", {
                "status": status,
                "checks_performed": len(checks)
            })
            
            return HealthStatus(
                status=status,
                message=message,
                timestamp=datetime.utcnow().isoformat(),
                checks=checks
            )
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return HealthStatus(
                status="error",
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.utcnow().isoformat(),
                checks={}
            )
    
    async def _check_quantum_health(self) -> Dict[str, Any]:
        """Check quantum system health"""
        try:
            # TODO: Replace mock metrics with actual quantum system metrics
            error_rate = 0.05  # 0.05% error rate
            coherence_time = 100  # 100 microseconds
            gate_fidelity = 0.9995  # 99.95% fidelity
            
            status = "healthy"
            if error_rate > self.alert_thresholds["quantum_error_rate"]:
                status = "warning"
                
            return {
                "status": status,
                "error_rate": error_rate,
                "coherence_time": coherence_time,
                "gate_fidelity": gate_fidelity,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error("Quantum health check failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """Check network health metrics"""
        try:
            # TODO: Replace mock metrics with actual network metrics
            latency = 15.0  # ms
            packet_loss = 0.01  # 0.01%
            bandwidth_usage = 65.0  # 65%
            
            status = "healthy"
            if latency > self.alert_thresholds["latency"]:
                status = "warning"
                
            return {
                "status": status,
                "latency": latency,
                "packet_loss": packet_loss,
                "bandwidth_usage": bandwidth_usage,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error("Network health check failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _check_resource_usage(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # TODO: Replace mock metrics with actual system metrics using psutil
            # Example:
            # cpu_usage = psutil.cpu_percent()
            # memory_usage = psutil.virtual_memory().percent
            # disk_usage = psutil.disk_usage('/').percent

            # Mock resource metrics
            cpu_usage = 45.0  # 45%
            memory_usage = 60.0  # 60%
            disk_usage = 55.0  # 55%
            
            status = "healthy"
            if cpu_usage > self.alert_thresholds["cpu_usage"]:
                status = "warning"
            if memory_usage > self.alert_thresholds["memory_usage"]:
                status = "warning"
                
            return {
                "status": status,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error("Resource check failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _check_security_status(self) -> Dict[str, Any]:
        """Check security systems status"""
        try:
            # TODO: Replace mock metrics with actual security system metrics
            encryption_status = "active"
            key_age = 120  # 2 minutes
            failed_auth_attempts = 0
            
            status = "healthy"
            if failed_auth_attempts > 5:
                status = "warning"
                
            return {
                "status": status,
                "encryption": encryption_status,
                "key_age": key_age,
                "failed_auth_attempts": failed_auth_attempts,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error("Security check failed", error=str(e))
            return {"status": "error", "error": str(e)}

    def collect_and_monitor_metrics(self, fidelity: float, error_rate: float, correction_success_rate: float, resource_usage: Dict[str, float]):
        """Collect and monitor specific metrics to evaluate the effectiveness of quantum error correction"""
        self.metrics.track_performance(
            latency=resource_usage.get("latency", 0.0),
            throughput=resource_usage.get("throughput", 0.0),
            reliability=resource_usage.get("reliability", 0.0)
        )
        self.metrics.record_event({
            "name": "quantum_error_correction_fidelity",
            "value": fidelity,
            "labels": {"metric": "fidelity"}
        })
        self.metrics.record_event({
            "name": "quantum_error_correction_error_rate",
            "value": error_rate,
            "labels": {"metric": "error_rate"}
        })
        self.metrics.record_event({
            "name": "quantum_error_correction_success_rate",
            "value": correction_success_rate,
            "labels": {"metric": "correction_success_rate"}
        })

class MetricsAggregator:
    """Aggregate and analyze system metrics"""
    
    def __init__(self):
        self.logger = StructuredLogger("MetricsAggregator")
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    def add_metrics(self, metrics: Dict[str, Any]):
        """Add new metrics to history"""
        metrics["timestamp"] = time.time()
        self.metrics_history.append(metrics)
        
        # Maintain history size limit
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
            
    def get_aggregated_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """Get aggregated metrics for specified time window"""
        try:
            current_time = time.time()
            window_metrics = [
                m for m in self.metrics_history
                if current_time - m["timestamp"] <= time_window
            ]
            
            if not window_metrics:
                return {}
                
            # Calculate aggregated statistics
            aggregated = {
                "timeframe": time_window,
                "samples": len(window_metrics),
                "timestamp": current_time
            }
            
            # Aggregate numeric metrics
            for key in window_metrics[0].keys():
                if key != "timestamp" and isinstance(window_metrics[0][key], (int, float)):
                    values = [m[key] for m in window_metrics]
                    aggregated[f"{key}_avg"] = sum(values) / len(values)
                    aggregated[f"{key}_max"] = max(values)
                    aggregated[f"{key}_min"] = min(values)
                    
            return aggregated
            
        except Exception as e:
            self.logger.error("Metrics aggregation failed", error=str(e))
            return {}

"""
Monitoring System - Enhanced with Redis caching
"""
from typing import Dict, Any, List, Optional
import time
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
from .logging_config import get_logger
from .config import config_manager
from .monitoring.cache_manager import cache_manager

logger = get_logger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MetricSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricThreshold:
    warning: float
    error: float
    critical: float
    comparison: str = "greater"  # or "less"
    duration: int = 0  # Duration in seconds for the condition to persist

@dataclass
class Alert:
    id: str
    severity: MetricSeverity
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: float

class MetricsCollector:
    def __init__(self):
        self.config = config_manager.get_value('monitoring', {})
        self._metrics = defaultdict(dict)
        self._rate_limits = {}
        self._thresholds = self._load_thresholds()
        self._active_alerts = set()
        self._alert_history = []
        self._aggregation_intervals = [60, 300, 900]  # 1min, 5min, 15min
        self._initialize_rate_limits()
        
        # Start background tasks
        asyncio.create_task(self._aggregate_metrics_loop())
        asyncio.create_task(self._cleanup_old_metrics_loop())
        asyncio.create_task(self._check_alerts_loop())

    def _load_thresholds(self) -> Dict[str, MetricThreshold]:
        """Load metric thresholds from configuration"""
        try:
            thresholds = {}
            for metric, config in self.config.get('thresholds', {}).items():
                thresholds[metric] = MetricThreshold(
                    warning=config.get('warning', 0.0),
                    error=config.get('error', 0.0),
                    critical=config.get('critical', 0.0),
                    comparison=config.get('comparison', 'greater'),
                    duration=config.get('duration', 0)
                )
            return thresholds
        except Exception as e:
            logger.error(f"Failed to load thresholds: {e}")
            return {}

    async def record_metric(self, name: str, value: Any, metric_type: MetricType = MetricType.GAUGE, labels: Dict = None):
        """Record a metric with caching"""
        try:
            current_time = time.time()
            rate_limit = self._rate_limits[metric_type]
            
            # Check rate limit window
            if current_time - rate_limit['last_reset'] >= rate_limit['window']:
                rate_limit['current'] = 0
                rate_limit['last_reset'] = current_time
            
            # Check rate limit
            if rate_limit['current'] >= rate_limit['limit']:
                logger.warning(f"Rate limit exceeded for metric {name}")
                return
            
            rate_limit['current'] += 1
            
            # Prepare metric data
            metric_data = {
                'value': value,
                'timestamp': current_time,
                'type': metric_type.value,
                'labels': labels or {}
            }
            
            # Store in local metrics
            if name not in self._metrics:
                self._metrics[name] = {
                    'current': metric_data,
                    'history': [],
                    'aggregates': defaultdict(list)
                }
            else:
                self._metrics[name]['history'].append(self._metrics[name]['current'])
                self._metrics[name]['current'] = metric_data
            
            # Cache metric data
            cache_key = f"metric:{name}:{int(current_time)}"
            await cache_manager.set(
                cache_key,
                metric_data,
                ttl=self._get_metric_ttl(metric_type)
            )
            
            # Update aggregates in cache
            await self._update_cached_aggregates(name, value, current_time)
            
            # Check for alerts
            if name in self._thresholds:
                await self._check_threshold(name, value)
                
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")

    def _get_metric_ttl(self, metric_type: MetricType) -> int:
        """Get TTL for metric type"""
        ttl_map = {
            MetricType.COUNTER: cache_manager.ttl_config['high_frequency'],
            MetricType.GAUGE: cache_manager.ttl_config['medium_frequency'],
            MetricType.HISTOGRAM: cache_manager.ttl_config['medium_frequency'],
            MetricType.SUMMARY: cache_manager.ttl_config['low_frequency']
        }
        return ttl_map.get(metric_type, cache_manager.default_ttl)

    async def _update_cached_aggregates(self, name: str, value: float, timestamp: float):
        """Update metric aggregates in cache"""
        try:
            for interval in self._aggregation_intervals:
                # Get existing aggregates from cache
                cache_key = f"aggregate:{name}:{interval}"
                aggregates = await cache_manager.get(cache_key, {})
                
                if not aggregates:
                    aggregates = {
                        'count': 0,
                        'sum': 0,
                        'min': float('inf'),
                        'max': float('-inf'),
                        'values': []
                    }
                
                # Update aggregates
                aggregates['count'] += 1
                aggregates['sum'] += value
                aggregates['min'] = min(aggregates['min'], value)
                aggregates['max'] = max(aggregates['max'], value)
                aggregates['values'].append(value)
                
                # Keep only recent values
                cutoff_time = timestamp - interval
                aggregates['values'] = aggregates['values'][-1000:]  # Limit history size
                
                # Calculate statistics
                if aggregates['values']:
                    aggregates['mean'] = aggregates['sum'] / aggregates['count']
                    aggregates['std'] = float(np.std(aggregates['values']))
                
                # Store updated aggregates
                await cache_manager.set(cache_key, aggregates, ttl=interval * 2)
                
        except Exception as e:
            logger.error(f"Failed to update cached aggregates for {name}: {e}")

    async def _check_threshold(self, metric_name: str, value: float):
        """Check if metric value exceeds thresholds"""
        threshold = self._thresholds.get(metric_name)
        if not threshold:
            return
            
        severity = None
        threshold_value = None
        
        if threshold.comparison == "greater":
            if value >= threshold.critical:
                severity = MetricSeverity.CRITICAL
                threshold_value = threshold.critical
            elif value >= threshold.error:
                severity = MetricSeverity.ERROR
                threshold_value = threshold.error
            elif value >= threshold.warning:
                severity = MetricSeverity.WARNING
                threshold_value = threshold.warning
        else:  # less than
            if value <= threshold.critical:
                severity = MetricSeverity.CRITICAL
                threshold_value = threshold.critical
            elif value <= threshold.error:
                severity = MetricSeverity.ERROR
                threshold_value = threshold.error
            elif value <= threshold.warning:
                severity = MetricSeverity.WARNING
                threshold_value = threshold.warning
                
        if severity:
            await self._create_alert(
                metric_name=metric_name,
                severity=severity,
                current_value=value,
                threshold_value=threshold_value
            )

    async def _create_alert(self, metric_name: str, severity: MetricSeverity, 
                          current_value: float, threshold_value: float):
        """Create and process a new alert with caching"""
        try:
            alert = Alert(
                id=f"alert_{int(time.time())}_{metric_name}",
                severity=severity,
                message=f"{metric_name} is {current_value}, threshold is {threshold_value}",
                metric_name=metric_name,
                current_value=current_value,
                threshold_value=threshold_value,
                timestamp=time.time()
            )
            
            # Add to active alerts if not already present
            alert_key = f"{metric_name}_{severity.value}"
            if alert_key not in self._active_alerts:
                self._active_alerts.add(alert_key)
                self._alert_history.append(alert)
                
                # Cache alert
                cache_key = f"alert:{alert.id}"
                await cache_manager.set(
                    cache_key,
                    dataclasses.asdict(alert),
                    ttl=cache_manager.ttl_config['medium_frequency']
                )
                
                # Update active alerts cache
                await cache_manager.set(
                    "active_alerts",
                    list(self._active_alerts),
                    ttl=cache_manager.ttl_config['high_frequency']
                )
                
                # Send alert notification
                await self._send_alert_notification(alert)
                
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    async def get_metrics(self, names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get metrics with caching"""
        try:
            if names:
                # Get metrics from cache
                metrics = {}
                for name in names:
                    # Try to get from cache first
                    cached_data = await cache_manager.get(f"metric:{name}:current")
                    if cached_data:
                        metrics[name] = cached_data
                    elif name in self._metrics:
                        metrics[name] = self._metrics[name]
                return metrics
                
            return self._metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

    async def get_aggregated_metrics(self, 
                                   names: Optional[List[str]] = None,
                                   interval: int = 300) -> Dict[str, Any]:
        """Get aggregated metrics from cache"""
        try:
            results = {}
            metrics = names if names else list(self._metrics.keys())
            
            for name in metrics:
                cache_key = f"aggregate:{name}:{interval}"
                aggregates = await cache_manager.get(cache_key)
                if aggregates:
                    results[name] = aggregates
                    
            return results
            
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            return {}

    async def get_alerts(self, 
                        from_time: Optional[float] = None,
                        to_time: Optional[float] = None,
                        severity: Optional[MetricSeverity] = None) -> List[Alert]:
        """Get filtered alerts from cache"""
        try:
            # Try to get alerts from cache
            cached_alerts = await cache_manager.get("alert_history")
            alerts = cached_alerts if cached_alerts else self._alert_history
            
            if from_time:
                alerts = [a for a in alerts if a.timestamp >= from_time]
            if to_time:
                alerts = [a for a in alerts if a.timestamp <= to_time]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
                
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

# Global metrics collector instance
metrics_collector = MetricsCollector()
