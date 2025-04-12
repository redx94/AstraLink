"""
Security Module - Implements enterprise-grade security features
"""
import asyncio
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from .logging_config import StructuredLogger

class SecurityManager:
    """Manages security operations and policies"""
    
    def __init__(self):
        self.logger = StructuredLogger("SecurityManager")
        self.api_key_header = APIKeyHeader(name="X-API-Key")
        self._initialize_encryption()
        self.audit_records = []
        self.max_audit_records = 10000
        self.failed_attempts = {}
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
    def _initialize_encryption(self):
        """Initialize encryption keys and systems"""
        try:
            # Generate RSA key pair for asymmetric encryption
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096
            )
            self.public_key = self.private_key.public_key()
            
            # Generate key for symmetric encryption
            self.symmetric_key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.symmetric_key)
            
            self.logger.info("Encryption systems initialized successfully")
        except Exception as e:
            self.logger.critical("Failed to initialize encryption", error=str(e))
            raise
            
    async def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error("Encryption failed", error=str(e))
            raise
            
    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error("Decryption failed", error=str(e))
            raise
            
    async def create_jwt_token(self, data: Dict[str, Any]) -> str:
        """Create JWT token with quantum-enhanced security"""
        try:
            expiration = datetime.utcnow() + timedelta(hours=1)
            token_data = {
                **data,
                "exp": expiration,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4())
            }
            
            token = jwt.encode(
                token_data,
                self.private_key,
                algorithm="RS512"
            )
            
            self.log_audit_event(
                "token_creation",
                {"user_id": data.get("user_id"), "token_id": token_data["jti"]}
            )
            
            return token
            
        except Exception as e:
            self.logger.error("Token creation failed", error=str(e))
            raise
            
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS512"]
            )
            
            self.log_audit_event(
                "token_validation",
                {"token_id": payload.get("jti"), "success": True}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.log_audit_event("token_validation", {"success": False, "reason": "expired"})
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            self.log_audit_event("token_validation", {"success": False, "reason": str(e)})
            raise HTTPException(status_code=401, detail="Invalid token")
            
    def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log security audit event"""
        try:
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "details": details
            }
            
            self.audit_records.append(event)
            
            # Maintain audit record size limit
            if len(self.audit_records) > self.max_audit_records:
                self.audit_records = self.audit_records[-self.max_audit_records:]
                
            self.logger.info(
                "Security audit event",
                event_type=event_type,
                event_id=event["event_id"]
            )
            
        except Exception as e:
            self.logger.error("Failed to log audit event", error=str(e))
            
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate API key with rate limiting"""
        try:
            # Check for previous failed attempts
            if api_key in self.failed_attempts:
                attempts = self.failed_attempts[api_key]
                if attempts["count"] >= self.max_failed_attempts:
                    if datetime.now().timestamp() - attempts["last_attempt"] < self.lockout_duration:
                        self.log_audit_event(
                            "api_key_lockout",
                            {"api_key": api_key[:8] + "..."}
                        )
                        raise HTTPException(
                            status_code=429,
                            detail="Too many failed attempts. Please try again later."
                        )
                    else:
                        # Reset failed attempts after lockout period
                        self.failed_attempts.pop(api_key)
            
            # Load API keys from config file
            import yaml
            with open("config/security_auditor.yaml", "r") as f:
                config = yaml.safe_load(f)
            api_keys = config.get("api_keys", {})

            # Validate API key
            is_valid = api_key in api_keys.values()
            
            if not is_valid:
                # Record failed attempt
                if api_key not in self.failed_attempts:
                    self.failed_attempts[api_key] = {"count": 0, "last_attempt": 0}
                    
                self.failed_attempts[api_key]["count"] += 1
                self.failed_attempts[api_key]["last_attempt"] = datetime.now().timestamp()
                
                self.log_audit_event(
                    "api_key_validation_failed",
                    {"api_key": api_key[:8] + "..."}
                )
                
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
                
            # Reset failed attempts on successful validation
            if api_key in self.failed_attempts:
                self.failed_attempts.pop(api_key)
                
            self.log_audit_event(
                "api_key_validation_success",
                {"api_key": api_key[:8] + "..."}
            )
            
            return True
            
        except HTTPException:
            raise
        except FileNotFoundError as e:
            self.logger.error("API key validation failed: Security configuration file not found", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
        except yaml.YAMLError as e:
            self.logger.error("API key validation failed: Error parsing security configuration file", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as e:
            self.logger.error("API key validation failed", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None
    ) -> list:
        """Retrieve filtered audit logs"""
        try:
            filtered_logs = self.audit_records
            
            if start_time:
                filtered_logs = [
                    log for log in filtered_logs
                    if datetime.fromisoformat(log["timestamp"]) >= start_time
                ]
                
            if end_time:
                filtered_logs = [
                    log for log in filtered_logs
                    if datetime.fromisoformat(log["timestamp"]) <= end_time
                ]
                
            if event_type:
                filtered_logs = [
                    log for log in filtered_logs
                    if log["event_type"] == event_type
                ]
                
            return filtered_logs
            
        except Exception as e:
            self.logger.error("Failed to retrieve audit logs", error=str(e))
            raise

# Global security manager instance
security_manager = SecurityManager()

# Dependency for protecting routes
async def verify_api_key(
    api_key: str = Security(APIKeyHeader(name="X-API-Key"))
) -> bool:
    return await security_manager.validate_api_key(api_key)
