"""
Security Manager - Handles encryption, key management, and audit logging
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Dict, Any, Optional
import json
import time
from datetime import datetime
import yaml
from .logging_config import get_logger
import hashlib
import secrets
import asyncio
from pathlib import Path

logger = get_logger(__name__)

class SecurityManager:
    def __init__(self):
        self.config = self._load_config()
        self._key_cache = {}
        self._last_rotation = time.time()
        self.rotation_interval = self.config.get('key_rotation_interval', 86400)  # 24 hours
        self._initialize_secure_storage()
        
    def _load_config(self) -> Dict:
        """Load security configuration"""
        try:
            with open('config/security_auditor.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load security config: {e}")
            return {}

    def _initialize_secure_storage(self):
        """Initialize secure storage for sensitive data"""
        self._secure_dir = Path.home() / '.astralink' / 'secure'
        self._secure_dir.mkdir(parents=True, exist_ok=True)
        self._secure_dir.chmod(0o700)  # Restrict permissions
        
        # Initialize master key if needed
        master_key_path = self._secure_dir / 'master.key'
        if not master_key_path.exists():
            master_key = self._generate_master_key()
            self._save_master_key(master_key)

    def _generate_master_key(self) -> bytes:
        """Generate a new master key"""
        return AESGCM.generate_key(bit_length=256)

    def _save_master_key(self, key: bytes):
        """Securely save master key"""
        key_path = self._secure_dir / 'master.key'
        key_path.write_bytes(key)
        key_path.chmod(0o400)  # Read-only by owner

    def _load_master_key(self) -> bytes:
        """Load master key from secure storage"""
        try:
            key_path = self._secure_dir / 'master.key'
            return key_path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to load master key: {e}")
            raise

    async def encrypt_data(self, data: str) -> str:
        """Encrypt data using current encryption key"""
        try:
            if not isinstance(data, str):
                data = json.dumps(data)
            
            # Generate a new nonce for each encryption
            nonce = os.urandom(12)
            
            # Get current encryption key
            key = await self._get_current_key()
            
            # Create AESGCM instance
            aesgcm = AESGCM(key)
            
            # Encrypt the data
            ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
            
            # Combine nonce and ciphertext
            encrypted = base64.b64encode(nonce + ciphertext)
            return encrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using appropriate key"""
        try:
            # Decode from base64
            raw_data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract nonce and ciphertext
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            
            # Get appropriate key
            key = await self._get_current_key()
            
            # Create AESGCM instance
            aesgcm = AESGCM(key)
            
            # Decrypt the data
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    async def _get_current_key(self) -> bytes:
        """Get current encryption key, rotating if needed"""
        current_time = time.time()
        
        # Check if key rotation is needed
        if current_time - self._last_rotation >= self.rotation_interval:
            await self._rotate_keys()
            
        # Get current key from cache
        key_id = self._get_current_key_id()
        return self._key_cache.get(key_id)

    async def _rotate_keys(self):
        """Rotate encryption keys"""
        try:
            # Generate new key
            new_key = AESGCM.generate_key(bit_length=256)
            new_key_id = self._generate_key_id()
            
            # Store new key
            await self._store_key(new_key_id, new_key)
            
            # Update key cache
            self._key_cache[new_key_id] = new_key
            
            # Clean up old keys
            await self._cleanup_old_keys()
            
            self._last_rotation = time.time()
            logger.info("Key rotation completed successfully")
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise

    def _generate_key_id(self) -> str:
        """Generate a unique key identifier"""
        return f"key_{int(time.time())}_{secrets.token_hex(4)}"

    async def _store_key(self, key_id: str, key: bytes):
        """Store encryption key securely"""
        try:
            # Encrypt key with master key
            master_key = self._load_master_key()
            aesgcm = AESGCM(master_key)
            nonce = os.urandom(12)
            
            # Encrypt key
            encrypted_key = aesgcm.encrypt(nonce, key, None)
            
            # Store encrypted key
            key_path = self._secure_dir / f"{key_id}.key"
            key_path.write_bytes(nonce + encrypted_key)
            key_path.chmod(0o400)  # Read-only by owner
            
        except Exception as e:
            logger.error(f"Failed to store key: {e}")
            raise

    def _get_current_key_id(self) -> str:
        """Get current key identifier"""
        try:
            key_files = list(self._secure_dir.glob('key_*.key'))
            if not key_files:
                raise ValueError("No encryption keys found")
            return key_files[-1].stem
        except Exception as e:
            logger.error(f"Failed to get current key ID: {e}")
            raise

    async def _cleanup_old_keys(self):
        """Clean up old encryption keys"""
        try:
            key_files = list(self._secure_dir.glob('key_*.key'))
            key_files.sort()
            
            # Keep last 3 keys for decrypting old data
            keys_to_remove = key_files[:-3]
            
            for key_file in keys_to_remove:
                key_file.unlink()
                key_id = key_file.stem
                self._key_cache.pop(key_id, None)
                
        except Exception as e:
            logger.error(f"Failed to cleanup old keys: {e}")

    def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log security audit event"""
        try:
            timestamp = datetime.now().isoformat()
            event_id = f"evt_{int(time.time())}_{secrets.token_hex(4)}"
            
            audit_event = {
                "event_id": event_id,
                "timestamp": timestamp,
                "type": event_type,
                "details": details
            }
            
            # Add event hash for integrity
            event_hash = self._hash_event(audit_event)
            audit_event["hash"] = event_hash
            
            # Write to audit log
            self._write_audit_log(audit_event)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def _hash_event(self, event: Dict) -> str:
        """Create hash of audit event for integrity verification"""
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()

    def _write_audit_log(self, event: Dict):
        """Write audit event to secure log file"""
        try:
            log_path = self._secure_dir / 'audit.log'
            with open(log_path, 'a') as f:
                json.dump(event, f)
                f.write('\n')
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            raise

    def verify_client_access(self, client_id: str, access_token: str) -> bool:
        """Verify client access credentials"""
        try:
            # Add your access verification logic here
            return True
        except Exception as e:
            logger.error(f"Access verification failed: {e}")
            return False

# Global security manager instance
security_manager = SecurityManager()
