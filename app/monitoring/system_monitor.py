"""
System Monitor Module
Coordinates all monitoring components and provides unified system health checks.
"""

from typing import Dict, Any
from datetime import datetime
from app.config import get_settings
from app.logging_config import get_logger
from .models import HealthStatus
from .resource_monitor import ResourceMonitor
from .network_monitor import NetworkMonitor
from .security_monitor import SecurityMonitor
from .quantum_monitor import QuantumMonitor
from .metrics_aggregator import MetricsAggregator

logger = get_logger(__name__)

class SystemMonitor:
    """System-wide monitoring and health checks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = getattr(self.settings, 'monitoring', {})
        self.thresholds = self.config.get('thresholds', {})
        
        # Initialize monitoring components
        self.resource_monitor = ResourceMonitor(self.thresholds)
        self.network_monitor = NetworkMonitor(self.thresholds)
        self.security_monitor = SecurityMonitor(self.thresholds)
        self.quantum_monitor = QuantumMonitor(self.thresholds)
        self.metrics = MetricsAggregator()

    async def check_system_health(self) -> HealthStatus:
        """Perform comprehensive system health check"""
        try:
            checks = {}
            status = "healthy"
            message = "All systems operational"

            # Perform individual health checks
            checks["resources"] = await self.resource_monitor.check_resource_usage()
            checks["network"] = await self.network_monitor.check_network_health()
            checks["security"] = await self.security_monitor.check_security_status()
            checks["quantum"] = await self.quantum_monitor.check_quantum_health()

            # Determine overall system status
            if any(check.get("status") == "critical" for check in checks.values()):
                status = "critical"
                message = "Critical system issues detected"
            elif any(check.get("status") == "warning" for check in checks.values()):
                status = "warning"
                message = "System warnings detected"

            # Record overall system health metric
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
            logger.error("Health check failed", error=str(e))
            return HealthStatus(
                status="error",
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.utcnow().isoformat(),
                checks={}
            )

    async def collect_metrics(self, interval: int = 60) -> Dict[str, Any]:
        """Collect all system metrics"""
        try:
            metrics = {
                "resources": await self.resource_monitor.check_resource_usage(),
                "network": await self.network_monitor.check_network_health(),
                "security": await self.security_monitor.check_security_status(),
                "quantum": await self.quantum_monitor.check_quantum_health()
            }

            # Record all metrics
            for category, data in metrics.items():
                if isinstance(data, dict) and "metrics" in data:
                    for name, value in data["metrics"].__dict__.items():
                        if not name.startswith("_"):  # Skip private attributes
                            self.metrics.record_metric(
                                f"{category}.{name}",
                                value,
                                labels={"category": category}
                            )

            return metrics

        except Exception as e:
            logger.error("Metrics collection failed", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }

    async def analyze_security_events(self, time_window: int = 3600) -> Dict[str, Any]:
        """Analyze security events within the specified time window"""
        return await self.security_monitor.analyze_security_events(time_window)

    async def collect_and_monitor_quantum_metrics(
        self,
        fidelity: float,
        error_rate: float,
        correction_success_rate: float,
        resource_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """Collect and monitor quantum-specific metrics"""
        return await self.quantum_monitor.collect_and_monitor_metrics(
            fidelity,
            error_rate,
            correction_success_rate,
            resource_usage
        )