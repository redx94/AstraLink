class AstraLinkException(Exception):
    """Base exception for AstraLink"""
    pass

class QuantumSystemError(AstraLinkException):
    """Raised when quantum system operations fail"""
    pass

class AISystemError(AstraLinkException):
    """Raised when AI system operations fail"""
    pass

class DatabaseError(AstraLinkException):
    """Raised when database operations fail"""
    pass
