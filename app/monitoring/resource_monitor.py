"""
Resource Monitoring Module
Handles system resource monitoring including CPU, memory, disk, and network.
"""

import psutil
import time
from typing import Dict, Any
from .models import ResourceMetrics
from app.logging_config import get_logger

logger = get_logger(__name__)

class ResourceMonitor:
    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds
        
    async def check_resource_usage(self) -> Dict[str, Any]:
        """Check system resource usage using actual metrics"""
        try:
            # Get actual CPU usage averaged across all cores
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get disk usage for root partition
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Get IO counters
            io_counters = psutil.disk_io_counters()
            net_counters = psutil.net_io_counters()
            
            metrics = ResourceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io={
                    "bytes_sent": net_counters.bytes_sent,
                    "bytes_recv": net_counters.bytes_recv,
                    "packets_sent": net_counters.packets_sent,
                    "packets_recv": net_counters.packets_recv,
                    "disk_read": io_counters.read_bytes,
                    "disk_write": io_counters.write_bytes
                },
                timestamp=time.time()
            )
            
            status = "healthy"
            warnings = []
            
            if cpu_usage > self.thresholds.get("cpu_usage", 80.0):
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_usage:.1f}%")
            
            if memory_usage > self.thresholds.get("memory_usage", 85.0):
                status = "warning"
                warnings.append(f"High memory usage: {memory_usage:.1f}%")
            
            if disk_usage > self.thresholds.get("disk_usage", 90.0):
                status = "warning"
                warnings.append(f"High disk usage: {disk_usage:.1f}%")
            
            return {
                "status": status,
                "warnings": warnings,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error("Resource check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metrics": None
            }