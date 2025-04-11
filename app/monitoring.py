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
            # Mock quantum system metrics
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
            # Mock network metrics
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
            # Mock security metrics
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
