"""
Network Monitoring Module
Handles network health monitoring including latency, bandwidth, and packet loss.
"""
import time
import asyncio
from typing import Dict, Any, Optional
from app.logging_config import get_logger

logger = get_logger(__name__)

# Optional dependencies with fallbacks
try:
    import speedtest as speedtest_cli
    SPEEDTEST_AVAILABLE = True
except ImportError:
    logger.warning("speedtest-cli not available - bandwidth tests will be disabled")
    SPEEDTEST_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    logger.warning("psutil not available - some network metrics will be limited")
    PSUTIL_AVAILABLE = False

class NetworkMonitor:
    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds
        self.speedtest = None
        self._last_bandwidth_check = 0
        self._bandwidth_cache = None
        self._bandwidth_cache_ttl = 300  # 5 minutes

    async def initialize_speedtest(self):
        """Initialize speedtest client"""
        if not SPEEDTEST_AVAILABLE:
            return

        try:
            self.speedtest = speedtest_cli.Speedtest()
            await asyncio.to_thread(self.speedtest.get_best_server)
        except Exception as e:
            logger.error("Failed to initialize speedtest", error=str(e))
            self.speedtest = None

    async def check_network_health(self) -> Dict[str, Any]:
        """Check network health metrics using actual measurements"""
        try:
            metrics = {
                "packets_sent": 0,
                "packets_recv": 0,
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packet_loss": 0.0,
                "bandwidth": None,
                "latency": 0.0,
                "timestamp": time.time()
            }

            # Get network IO statistics if psutil is available
            if PSUTIL_AVAILABLE:
                net_stats = psutil.net_io_counters()
                metrics.update({
                    "packets_sent": net_stats.packets_sent,
                    "packets_recv": net_stats.packets_recv,
                    "bytes_sent": net_stats.bytes_sent,
                    "bytes_recv": net_stats.bytes_recv
                })

                # Calculate packet loss
                if metrics["packets_sent"] > 0:
                    metrics["packet_loss"] = ((metrics["packets_sent"] - metrics["packets_recv"]) 
                                           / metrics["packets_sent"]) * 100

            # Check bandwidth if speedtest is available
            if SPEEDTEST_AVAILABLE:
                bandwidth = await self._check_bandwidth()
                if bandwidth:
                    metrics["bandwidth"] = bandwidth
                    metrics["latency"] = await self._measure_latency()

            # Determine status based on available metrics
            status = "healthy"
            warnings = []

            if metrics["latency"] > self.thresholds.get("latency", 100.0):
                status = "warning"
                warnings.append(f"High latency: {metrics['latency']:.1f}ms")

            if metrics["packet_loss"] > self.thresholds.get("packet_loss", 5.0):
                status = "warning"
                warnings.append(f"High packet loss: {metrics['packet_loss']:.2f}%")

            if (metrics["bandwidth"] and 
                metrics["bandwidth"].get("download", 0) < self.thresholds.get("min_bandwidth", 1.0)):
                status = "warning"
                warnings.append("Low bandwidth detected")

            metrics["status"] = status
            metrics["warnings"] = warnings

            return metrics

        except Exception as e:
            logger.error("Network health check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }

    async def _check_bandwidth(self) -> Optional[Dict[str, float]]:
        """Check network bandwidth with caching"""
        if not SPEEDTEST_AVAILABLE or not self.speedtest:
            return None

        current_time = time.time()
        
        # Return cached result if valid
        if (self._bandwidth_cache and 
            current_time - self._last_bandwidth_check < self._bandwidth_cache_ttl):
            return self._bandwidth_cache

        try:
            # Run speedtest in thread pool to avoid blocking
            download = await asyncio.to_thread(self.speedtest.download)
            upload = await asyncio.to_thread(self.speedtest.upload)

            # Convert to Mbps
            result = {
                "download": download / 1_000_000,
                "upload": upload / 1_000_000
            }

            # Update cache
            self._bandwidth_cache = result
            self._last_bandwidth_check = current_time

            return result

        except Exception as e:
            logger.error("Bandwidth check failed", error=str(e))
            return None

    async def _measure_latency(self) -> float:
        """Measure network latency"""
        if not SPEEDTEST_AVAILABLE or not self.speedtest:
            return 0.0

        try:
            latency = await asyncio.to_thread(lambda: self.speedtest.results.ping)
            return float(latency)
        except Exception as e:
            logger.error("Latency measurement failed", error=str(e))
            return 0.0