"""
Health Monitor - Distributed health monitoring system with real-time alerts
"""
import asyncio
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
import json
import aiohttp
from ..app.logging_config import get_logger
from ..app.config import config_manager
from ..app.monitoring import metrics_collector
from ..core.rate_limiter import rate_limiter
from ..core.error_recovery import error_recovery_manager, ResourceType, OperationType

logger = get_logger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    FAILED = "failed"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    BLOCKCHAIN = "blockchain"
    QUANTUM = "quantum"
    NETWORK = "network"
    SECURITY = "security"

@dataclass
class HealthCheck:
    component_type: ComponentType
    check_interval: float
    timeout: float
    retries: int
    thresholds: Dict[str, float]

@dataclass
class Alert:
    component_type: ComponentType
    status: HealthStatus
    message: str
    severity: int
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None

class HealthMonitor:
    """Health monitoring system with real-time alerts"""
    def __init__(self):
        self.config = config_manager.get_value('health_monitoring', {})
        self.health_checks: Dict[str, HealthCheck] = {}
        self.component_status: Dict[str, HealthStatus] = {}
        self.alert_handlers: List[callable] = []
        self.alert_history: List[Alert] = []
        self._setup_monitoring()
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_components())
        asyncio.create_task(self._cleanup_alert_history())

    def _setup_monitoring(self):
        """Initialize health monitoring configuration"""
        try:
            # Load health check configurations
            checks = self.config.get('checks', {})
            for component, check_config in checks.items():
                self.health_checks[component] = HealthCheck(
                    component_type=ComponentType(check_config.get('type', 'api')),
                    check_interval=check_config.get('interval', 60),
                    timeout=check_config.get('timeout', 10),
                    retries=check_config.get('retries', 3),
                    thresholds=check_config.get('thresholds', {
                        'latency': 1.0,
                        'error_rate': 0.01,
                        'load': 0.8
                    })
                )
                self.component_status[component] = HealthStatus.UNKNOWN
                
            # Setup rate limiting
            rate_limiter.create_rule(
                key="health_checks",
                algorithm="token_bucket",
                capacity=self.config.get('rate_limit', {}).get('capacity', 1000),
                refill_rate=self.config.get('rate_limit', {}).get('refill_rate', 100.0)
            )
            
        except Exception as e:
            logger.error(f"Failed to setup health monitoring: {e}")

    async def _monitor_components(self):
        """Monitor health of all components"""
        while True:
            try:
                tasks = []
                current_time = time.time()
                
                # Check each component
                for component, check in self.health_checks.items():
                    tasks.append(self._check_component_health(component))
                    
                # Run checks in parallel
                await asyncio.gather(*tasks)
                
                await asyncio.sleep(1)  # Small delay between check cycles
                
            except Exception as e:
                logger.error(f"Health monitoring loop failed: {e}")
                await asyncio.sleep(5)

    async def _check_component_health(self, component: str):
        """Check health of a specific component"""
        try:
            check = self.health_checks[component]
            old_status = self.component_status[component]
            
            # Check rate limit
            if not await rate_limiter.check_limit("health_checks"):
                logger.warning(f"Rate limit exceeded for health checks")
                return
                
            # Get component metrics
            metrics = await self._get_component_metrics(component)
            
            # Evaluate health status
            status = await self._evaluate_health(component, metrics)
            self.component_status[component] = status
            
            # Record metric
            await metrics_collector.record_metric(
                f"component_health",
                1 if status == HealthStatus.HEALTHY else 0,
                labels={'component': component}
            )
            
            # Generate alert if status changed
            if status != old_status:
                await self._generate_alert(
                    component,
                    status,
                    f"Component {component} health changed: {old_status.value} -> {status.value}",
                    self._get_alert_severity(status)
                )
                
        except Exception as e:
            logger.error(f"Health check failed for {component}: {e}")
            self.component_status[component] = HealthStatus.UNKNOWN

    async def _get_component_metrics(self, component: str) -> Dict[str, float]:
        """Get metrics for a component"""
        try:
            check = self.health_checks[component]
            
            # Get metrics with error recovery
            metrics = await error_recovery_manager.execute_quantum_operation(
                lambda: self._fetch_metrics(component),
                OperationType.READ,
                fallback=lambda: self._get_default_metrics()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get component metrics: {e}")
            return self._get_default_metrics()

    async def _fetch_metrics(self, component: str) -> Dict[str, float]:
        """Fetch metrics from component"""
        try:
            # Simulate metrics collection
            # Replace with actual metrics collection logic
            return {
                'latency': 0.1,
                'error_rate': 0.001,
                'load': 0.5
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            raise

    def _get_default_metrics(self) -> Dict[str, float]:
        """Get default metrics when collection fails"""
        return {
            'latency': 0.0,
            'error_rate': 0.0,
            'load': 0.0
        }

    async def _evaluate_health(self, component: str, metrics: Dict[str, float]) -> HealthStatus:
        """Evaluate component health based on metrics"""
        try:
            check = self.health_checks[component]
            thresholds = check.thresholds
            
            # Check each metric against thresholds
            if metrics['error_rate'] > thresholds['error_rate']:
                return HealthStatus.FAILING
            elif metrics['latency'] > thresholds['latency']:
                return HealthStatus.DEGRADED
            elif metrics['load'] > thresholds['load']:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Health evaluation failed: {e}")
            return HealthStatus.UNKNOWN

    def _get_alert_severity(self, status: HealthStatus) -> int:
        """Get alert severity based on health status"""
        severity_map = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 1,
            HealthStatus.FAILING: 2,
            HealthStatus.FAILED: 3,
            HealthStatus.UNKNOWN: 2
        }
        return severity_map.get(status, 2)

    async def _generate_alert(self,
                            component: str,
                            status: HealthStatus,
                            message: str,
                            severity: int):
        """Generate and process health alert"""
        try:
            alert = Alert(
                component_type=self.health_checks[component].component_type,
                status=status,
                message=message,
                severity=severity,
                timestamp=time.time()
            )
            
            # Add to history
            self.alert_history.append(alert)
            
            # Process alert through handlers
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
                    
            # Record alert metric
            await metrics_collector.record_metric(
                f"health_alert",
                1,
                labels={
                    'component': component,
                    'status': status.value,
                    'severity': severity
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate alert: {e}")

    async def _cleanup_alert_history(self):
        """Clean up old alerts from history"""
        while True:
            try:
                current_time = time.time()
                retention_period = self.config.get('alert_retention_period', 86400)  # 24 hours
                
                self.alert_history = [
                    alert for alert in self.alert_history
                    if current_time - alert.timestamp <= retention_period
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Alert history cleanup failed: {e}")
                await asyncio.sleep(300)

    def register_alert_handler(self, handler: callable):
        """Register a new alert handler"""
        try:
            self.alert_handlers.append(handler)
            logger.info(f"Registered new alert handler: {handler.__name__}")
        except Exception as e:
            logger.error(f"Failed to register alert handler: {e}")

    def get_component_health(self, component: str) -> Dict[str, Any]:
        """Get current health status of a component"""
        try:
            if component not in self.component_status:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'last_check': None,
                    'metrics': None
                }
                
            return {
                'status': self.component_status[component].value,
                'last_check': time.time(),
                'metrics': self._get_default_metrics()  # Replace with actual metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get component health: {e}")
            return {
                'status': HealthStatus.UNKNOWN.value,
                'last_check': None,
                'metrics': None
            }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            component_states = {
                component: status.value
                for component, status in self.component_status.items()
            }
            
            # Determine overall status
            if any(status == HealthStatus.FAILED for status in self.component_status.values()):
                overall = HealthStatus.FAILED
            elif any(status == HealthStatus.FAILING for status in self.component_status.values()):
                overall = HealthStatus.FAILING
            elif any(status == HealthStatus.DEGRADED for status in self.component_status.values()):
                overall = HealthStatus.DEGRADED
            elif all(status == HealthStatus.HEALTHY for status in self.component_status.values()):
                overall = HealthStatus.HEALTHY
            else:
                overall = HealthStatus.DEGRADED
                
            return {
                'overall_status': overall.value,
                'components': component_states,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                'overall_status': HealthStatus.UNKNOWN.value,
                'components': {},
                'timestamp': time.time()
            }

# Global health monitor instance
health_monitor = HealthMonitor()