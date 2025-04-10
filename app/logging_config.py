"""
AstraLink - Logging Configuration Module
=====================================

This module provides a centralized logging configuration with JSON formatting,
correlation IDs, and contextual information for comprehensive system monitoring.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

import os
import logging.config
from pythonjsonlogger import jsonlogger

class ContextualJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(ContextualJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.created
        if not log_record.get('level'):
            log_record['level'] = record.levelname
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        if hasattr(record, 'context'):
            log_record['context'] = record.context

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": ContextualJsonFormatter,
            "format": "%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s %(context)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s - %(context)s - [%(filename)s:%(lineno)d]"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "json",
            "filename": "logs/error.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "level": "ERROR",
        },
        "app_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "json",
            "filename": "logs/app.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
        },
        "debug_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": "logs/debug.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "DEBUG",
        }
    },
    "loggers": {
        "": {  # Root logger
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "handlers": ["console", "app_file", "error_file"],
            "propagate": True
        },
        "astralink.debug": {  # Debug logger
            "level": "DEBUG",
            "handlers": ["debug_file"],
            "propagate": False
        }
    }
}

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    logger = logging.getLogger(name)
    
    def log_with_context(msg, correlation_id=None, context=None, *args, **kwargs):
        """Add correlation ID and context to log records."""
        extra = kwargs.get('extra', {})
        if correlation_id:
            extra['correlation_id'] = correlation_id
        if context:
            extra['context'] = context
        kwargs['extra'] = extra
        return msg, args, kwargs
    
    original_debug = logger.debug
    original_info = logger.info
    original_warning = logger.warning
    original_error = logger.error
    original_critical = logger.critical
    
    def debug_with_context(msg, *args, correlation_id=None, context=None, **kwargs):
        msg, args, kwargs = log_with_context(msg, correlation_id, context, *args, **kwargs)
        original_debug(msg, *args, **kwargs)
    
    def info_with_context(msg, *args, correlation_id=None, context=None, **kwargs):
        msg, args, kwargs = log_with_context(msg, correlation_id, context, *args, **kwargs)
        original_info(msg, *args, **kwargs)
    
    def warning_with_context(msg, *args, correlation_id=None, context=None, **kwargs):
        msg, args, kwargs = log_with_context(msg, correlation_id, context, *args, **kwargs)
        original_warning(msg, *args, **kwargs)
    
    def error_with_context(msg, *args, correlation_id=None, context=None, **kwargs):
        msg, args, kwargs = log_with_context(msg, correlation_id, context, *args, **kwargs)
        original_error(msg, *args, **kwargs)
    
    def critical_with_context(msg, *args, correlation_id=None, context=None, **kwargs):
        msg, args, kwargs = log_with_context(msg, correlation_id, context, *args, **kwargs)
        original_critical(msg, *args, **kwargs)
    
    logger.debug = debug_with_context
    logger.info = info_with_context
    logger.warning = warning_with_context
    logger.error = error_with_context
    logger.critical = critical_with_context
    
    return logger
