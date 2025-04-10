"""
AstraLink - Exception Handling Module
==================================

This module defines the custom exception hierarchy used throughout the AstraLink
system for standardized error handling and reporting.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from typing import Optional, Dict, Any
from datetime import datetime

class AstraLinkException(Exception):
    """Base exception for AstraLink with enhanced context."""
    def __init__(
        self,
        message: str,
        error_code: str,
        correlation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.correlation_id = correlation_id
        self.context = context or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a structured dictionary format."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }

class QuantumSystemError(AstraLinkException):
    """Raised when quantum system operations fail."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QUANTUM_ERROR",
            **kwargs
        )

class AISystemError(AstraLinkException):
    """Raised when AI system operations fail."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="AI_ERROR",
            **kwargs
        )

class DatabaseError(AstraLinkException):
    """Raised when database operations fail."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            **kwargs
        )

class ValidationError(AstraLinkException):
    """Raised when input validation fails."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            **kwargs
        )

class ResourceExhaustedError(AstraLinkException):
    """Raised when system resources are exhausted."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="RESOURCE_EXHAUSTED",
            **kwargs
        )

class ConfigurationError(AstraLinkException):
    """Raised when there are configuration issues."""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            **kwargs
        )
