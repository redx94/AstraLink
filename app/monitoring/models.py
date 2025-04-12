"""
Monitoring System Data Models
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

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
    critical: float
    lookback_window: int = 300  # 5 minutes default
    evaluation_periods: int = 3

@dataclass
class Alert:
    metric_name: str
    severity: MetricSeverity
    threshold_value: float
    current_value: float
    timestamp: float
    message: str
    labels: Optional[Dict[str, str]] = None

@dataclass
class HealthStatus:
    status: str
    message: str
    timestamp: str
    checks: Dict[str, Any]

@dataclass
class ResourceMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    timestamp: float

@dataclass
class SecurityMetrics:
    encryption_status: str
    key_age: float
    failed_auth_attempts: int
    storage_secure: bool
    timestamp: float

@dataclass
class QuantumMetrics:
    error_rate: float
    fidelity: float
    coherence_time: float
    gate_fidelity: float
    timestamp: float