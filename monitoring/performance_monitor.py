from typing import Dict, List
from functools import lru_cache
import time
import psutil

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_time = time.time()

    def record_metric(self, name: str, value: float) -> None:
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    @lru_cache(maxsize=128)
    def get_system_metrics(self) -> Dict[str, float]:
        start_time = time.perf_counter()
        metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'latency': time.perf_counter() - start_time
        }
        return metrics
