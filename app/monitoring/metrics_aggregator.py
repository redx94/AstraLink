"""
Metrics Aggregator Module
Collects and analyzes metrics from all monitoring subsystems with caching support.
"""

import time
import asyncio
import dataclasses
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from .models import MetricType, MetricSeverity, MetricThreshold, Alert
from .cache_manager import cache_manager
from app.logging_config import get_logger
from app.config import config_manager
import numpy as np

logger = get_logger(__name__)

class MetricsAggregator:
    def __init__(self):
        self.config = config_manager.get_value('monitoring', {})
        self._metrics = defaultdict(dict)
        self._rate_limits = {}
        self._thresholds = self._load_thresholds()
        self._active_alerts = set()
        self._alert_history = []
        self._aggregation_intervals = [60, 300, 900]  # 1min, 5min, 15min

        # Start background tasks
        asyncio.create_task(self._aggregate_metrics_loop())
        asyncio.create_task(self._cleanup_old_metrics_loop())
        asyncio.create_task(self._check_alerts_loop())

    def _load_thresholds(self) -> Dict[str, MetricThreshold]:
        """Load metric thresholds from configuration"""
        thresholds = {}
        config_thresholds = self.config.get('thresholds', {})
        
        for metric_name, values in config_thresholds.items():
            thresholds[metric_name] = MetricThreshold(
                warning=values.get('warning', float('inf')),
                critical=values.get('critical', float('inf')),
                lookback_window=values.get('window', 300),
                evaluation_periods=values.get('periods', 3)
            )
        
        return thresholds

    async def _aggregate_window(self, window: int):
        """Aggregate metrics for a specific time window"""
        try:
            current_time = time.time()
            cutoff = current_time - window

            # Group metrics by name
            window_metrics = defaultdict(list)
            for name in self._metrics:
                values = [
                    data['value']
                    for ts, data in self._metrics[name].items()
                    if ts >= cutoff and isinstance(data['value'], (int, float))
                ]
                if values:
                    window_metrics[name] = values

            # Calculate aggregates for each metric
            aggregates = {}
            for name, values in window_metrics.items():
                agg = {
                    'count': len(values),
                    'sum': sum(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'stddev': np.std(values) if len(values) > 1 else 0,
                    'timestamp': current_time
                }
                aggregates[name] = agg

                # Cache aggregates
                await cache_manager.set(
                    f"agg:{name}:{window}",
                    agg,
                    ttl=window * 2
                )

        except Exception as e:
            logger.error(f"Failed to aggregate {window}s window", error=str(e))

    async def record_metric(
        self, 
        name: str, 
        value: Any, 
        metric_type: MetricType = MetricType.GAUGE,
        labels: Dict = None
    ):
        """Record a metric with caching"""
        try:
            timestamp = time.time()
            metric_key = f"metric:{name}"
            
            # Store in local cache
            self._metrics[name][timestamp] = {
                'value': value,
                'type': metric_type.value,
                'labels': labels or {}
            }
            
            # Store in Redis cache
            await cache_manager.set(
                metric_key,
                {
                    'value': value,
                    'timestamp': timestamp,
                    'type': metric_type.value,
                    'labels': labels or {}
                },
                ttl=self._get_metric_ttl(metric_type)
            )
            
            # Update cached aggregates
            if isinstance(value, (int, float)):
                await self._update_cached_aggregates(name, float(value), timestamp)
            
            # Check thresholds
            await self._check_threshold(name, value)
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}", error=str(e))

    def _get_metric_ttl(self, metric_type: MetricType) -> int:
        """Get TTL for metric type"""
        ttls = {
            MetricType.COUNTER: 86400,    # 24 hours
            MetricType.GAUGE: 3600,       # 1 hour
            MetricType.HISTOGRAM: 7200,    # 2 hours
            MetricType.SUMMARY: 7200      # 2 hours
        }
        return ttls.get(metric_type, 3600)

    async def _update_cached_aggregates(self, name: str, value: float, timestamp: float):
        """Update metric aggregates in cache"""
        try:
            for window in self._aggregation_intervals:
                window_key = f"agg:{name}:{window}"
                
                # Get existing aggregates
                agg = await cache_manager.get(window_key) or {
                    'count': 0,
                    'sum': 0.0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'values': []
                }
                
                # Update aggregates
                agg['count'] += 1
                agg['sum'] += value
                agg['min'] = min(agg['min'], value)
                agg['max'] = max(agg['max'], value)
                agg['values'].append(value)
                
                # Trim old values
                cutoff = timestamp - window
                agg['values'] = [v for v in agg['values'] if v[1] >= cutoff]
                
                # Calculate mean and stddev
                if agg['values']:
                    values = [v for v in agg['values']]
                    agg['mean'] = np.mean(values)
                    agg['stddev'] = np.std(values) if len(values) > 1 else 0
                
                await cache_manager.set(window_key, agg, ttl=window * 2)
                
        except Exception as e:
            logger.error(f"Failed to update aggregates for {name}", error=str(e))

    async def _check_threshold(self, metric_name: str, value: float):
        """Check if metric value exceeds thresholds"""
        if metric_name not in self._thresholds:
            return

        threshold = self._thresholds[metric_name]
        
        if value >= threshold.critical:
            await self._create_alert(
                metric_name,
                MetricSeverity.CRITICAL,
                value,
                threshold.critical
            )
        elif value >= threshold.warning:
            await self._create_alert(
                metric_name,
                MetricSeverity.WARNING,
                value,
                threshold.warning
            )

    async def _create_alert(
        self,
        metric_name: str,
        severity: MetricSeverity,
        current_value: float,
        threshold_value: float
    ):
        """Create and process a new alert with caching"""
        try:
            alert = Alert(
                metric_name=metric_name,
                severity=severity,
                threshold_value=threshold_value,
                current_value=current_value,
                timestamp=time.time(),
                message=f"{metric_name} exceeded {severity.value} threshold: {current_value:.2f} >= {threshold_value:.2f}"
            )
            
            # Check if similar alert is already active
            alert_key = f"{metric_name}:{severity.value}"
            if alert_key in self._active_alerts:
                return
            
            # Add to active alerts
            self._active_alerts.add(alert_key)
            self._alert_history.append(alert)
            
            # Cache alert
            await cache_manager.set(
                f"alert:{alert_key}",
                dataclasses.asdict(alert),
                ttl=3600
            )
            
            # Notify alert handlers
            logger.warning(f"Alert triggered: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert for {metric_name}", error=str(e))

    async def _aggregate_metrics_loop(self):
        """Background task to aggregate metrics"""
        while True:
            try:
                # Aggregate metrics for each interval
                for window in self._aggregation_intervals:
                    await self._aggregate_window(window)
                
                await asyncio.sleep(60)  # Aggregate every minute
                
            except Exception as e:
                logger.error("Metrics aggregation failed", error=str(e))
                await asyncio.sleep(60)

    async def _cleanup_old_metrics_loop(self):
        """Background task to clean up old metrics"""
        while True:
            try:
                current_time = time.time()
                
                # Clean up local metrics
                for name in list(self._metrics.keys()):
                    self._metrics[name] = {
                        ts: data
                        for ts, data in self._metrics[name].items()
                        if current_time - ts < 3600  # Keep last hour
                    }
                
                # Clean up cached metrics
                # Note: Redis TTL handles this automatically
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error("Metrics cleanup failed", error=str(e))
                await asyncio.sleep(3600)

    async def _check_alerts_loop(self):
        """Background task to check and clear resolved alerts"""
        while True:
            try:
                current_time = time.time()
                
                # Check active alerts
                for alert_key in list(self._active_alerts):
                    metric_name, severity = alert_key.split(":")
                    if metric_name in self._metrics:
                        recent_values = [
                            data['value']
                            for ts, data in self._metrics[metric_name].items()
                            if current_time - ts < 300  # Last 5 minutes
                        ]
                        
                        if recent_values:
                            avg_value = sum(recent_values) / len(recent_values)
                            threshold = self._thresholds[metric_name]
                            
                            # Clear alert if value is back to normal
                            if avg_value < (
                                threshold.critical if severity == "CRITICAL"
                                else threshold.warning
                            ):
                                self._active_alerts.remove(alert_key)
                                await cache_manager.delete(f"alert:{alert_key}")
                                
                                logger.info(f"Alert resolved: {alert_key}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Alert check failed", error=str(e))
                await asyncio.sleep(60)