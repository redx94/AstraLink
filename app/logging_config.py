import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """Enhanced logging with structured format and severity levels"""
    
    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.service_name = service_name
        self._setup_logger()
        
    def _setup_logger(self):
        """Configure logger with proper formatting"""
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with formatting
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Create structured format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)

        # Create console handler with human-readable formatting
        human_handler = logging.StreamHandler()
        human_handler.setLevel(logging.INFO)
        human_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        human_handler.setFormatter(human_formatter)
        self.logger.addHandler(human_handler)
        
    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """Format log message with metadata"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
            "metadata": kwargs
        }
        return json.dumps(log_data)
        
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self.logger.info(self._format_log("INFO", message, **kwargs))
        
    def error(self, message: str, **kwargs):
        """Log error level message"""
        self.logger.error(self._format_log("ERROR", message, **kwargs))
        
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self.logger.warning(self._format_log("WARNING", message, **kwargs))
        
    def critical(self, message: str, **kwargs):
        """Log critical level message"""
        self.logger.critical(self._format_log("CRITICAL", message, **kwargs))
        
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))

class MetricsCollector:
    """Collect and store system metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        
    def record_metric(self, name: str, value: Any, tags: Dict[str, str] = None):
        """Record a metric with optional tags"""
        if tags is None:
            tags = {}
            
        self.metrics[name] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags
        }
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics"""
        return self.metrics
        
    def clear_metrics(self):
        """Clear all recorded metrics"""
        self.metrics = {}

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)
