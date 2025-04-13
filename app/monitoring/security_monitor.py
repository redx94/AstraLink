"""
Security Monitoring Module
Handles security system monitoring including encryption, authentication, and audit logging.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List
from app.security import security_manager
from .models import SecurityMetrics
from app.logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)

class SecurityMonitor:
    def __init__(self, thresholds: Dict[str, Any]):
        self.thresholds = thresholds
        self.audit_log_max_lines = 1000  # Maximum number of log lines to analyze

    async def check_security_status(self) -> Dict[str, Any]:
        """Check security systems status using actual security metrics"""
        try:
            # Check encryption key status
            current_time = time.time()
            key_age = current_time - security_manager._last_rotation
            key_age_minutes = key_age / 60

            # Check audit logs for recent failed authentication attempts
            audit_log_path = security_manager._secure_dir / 'audit.log'
            failed_auth_attempts = 0
            recent_auth_failures = []

            if audit_log_path.exists():
                with open(audit_log_path, 'r') as f:
                    # Look at last n lines maximum for recent events
                    lines = f.readlines()[-self.audit_log_max_lines:]
                    check_time = current_time - 3600  # Last hour

                    for line in lines:
                        try:
                            event = json.loads(line)
                            if (event['type'] == 'auth_failure' and 
                                datetime.fromisoformat(event['timestamp']).timestamp() > check_time):
                                failed_auth_attempts += 1
                                recent_auth_failures.append(event)
                        except (json.JSONDecodeError, KeyError):
                            continue

            # Check if master key exists and is accessible
            master_key_path = security_manager._secure_dir / 'master.key'
            encryption_status = "active" if master_key_path.exists() and master_key_path.stat().st_mode & 0o600 == 0o600 else "inactive"

            # Check secure storage permissions
            secure_dir = security_manager._secure_dir
            secure_dir_perms = secure_dir.stat().st_mode & 0o777
            storage_secure = secure_dir_perms == 0o700

            metrics = SecurityMetrics(
                encryption_status=encryption_status,
                key_age=key_age,
                failed_auth_attempts=failed_auth_attempts,
                storage_secure=storage_secure,
                timestamp=current_time
            )

            status = "healthy"
            warnings = []

            # Check security thresholds
            if failed_auth_attempts >= self.thresholds.get("failed_auth_attempts", 5):
                status = "warning"
                warnings.append(f"High number of authentication failures: {failed_auth_attempts}")

            if key_age > security_manager.rotation_interval:
                status = "warning"
                warnings.append("Encryption key rotation overdue")

            if not storage_secure:
                status = "critical"
                warnings.append("Secure storage permissions are incorrect")

            if encryption_status != "active":
                status = "critical"
                warnings.append("Encryption system is inactive")

            return {
                "status": status,
                "warnings": warnings,
                "metrics": metrics,
                "recent_auth_failures": recent_auth_failures[-5:]  # Last 5 failures only
            }

        except Exception as e:
            logger.error("Security check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metrics": None
            }

    async def analyze_security_events(self, time_window: int = 3600) -> Dict[str, Any]:
        """Analyze security events within the specified time window"""
        try:
            current_time = time.time()
            check_time = current_time - time_window
            events = []

            audit_log_path = security_manager._secure_dir / 'audit.log'
            if audit_log_path.exists():
                with open(audit_log_path, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if datetime.fromisoformat(event['timestamp']).timestamp() > check_time:
                                events.append(event)
                        except (json.JSONDecodeError, KeyError):
                            continue

            # Analyze event patterns
            event_types = {}
            ip_addresses = {}
            users = {}

            for event in events:
                event_type = event.get('type', 'unknown')
                ip = event.get('ip_address', 'unknown')
                user = event.get('user', 'unknown')

                event_types[event_type] = event_types.get(event_type, 0) + 1
                ip_addresses[ip] = ip_addresses.get(ip, 0) + 1
                users[user] = users.get(user, 0) + 1

            return {
                "total_events": len(events),
                "event_types": event_types,
                "ip_frequencies": ip_addresses,
                "user_frequencies": users,
                "timeframe": time_window,
                "timestamp": current_time
            }

        except Exception as e:
            logger.error("Security event analysis failed", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }