from typing import Dict, Optional
import threading
from datetime import datetime

class ServiceRegistry:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.services = {}
                cls._instance.health_checks = {}
        return cls._instance

    def register_service(self, name: str, endpoint: str, health_check_url: Optional[str] = None):
        self.services[name] = {
            "endpoint": endpoint,
            "health_check_url": health_check_url,
            "registered_at": datetime.utcnow()
        }

    def get_service(self, name: str) -> Optional[Dict]:
        return self.services.get(name)
