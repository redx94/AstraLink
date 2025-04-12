"""
Configuration Manager - Centralized configuration management with validation
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import json
from dataclasses import dataclass
from dotenv import load_dotenv
import re
import logging
from schema import Schema, And, Or, Use, Optional as SchemaOptional

logger = logging.getLogger(__name__)

@dataclass
class NetworkConfig:
    max_bandwidth: int
    connection_timeout: int
    quantum_error_threshold: float
    handshake_domain: str

@dataclass
class SecurityConfig:
    key_rotation_interval: int
    encryption_algorithm: str
    quantum_safe: bool
    min_key_size: int

@dataclass
class BlockchainConfig:
    chain_id: int
    network: str
    contract_addresses: Dict[str, str]
    gas_limit: int

class ConfigManager:
    def __init__(self):
        self._load_env()
        self.config_dir = Path('config')
        self.config_schema = self._load_schema()
        self.config = self._load_all_configs()
        self._validate_config()

    def _load_env(self):
        """Load environment variables"""
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
        
        # Load environment-specific config
        env = os.getenv('ASTRALINK_ENV', 'development')
        env_file = Path(f'.env.{env}')
        if env_file.exists():
            load_dotenv(env_file, override=True)

    def _load_schema(self) -> Dict:
        """Load configuration schema"""
        try:
            schema_path = self.config_dir / 'schema.yaml'
            if schema_path.exists():
                with open(schema_path) as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return {}

    def _load_all_configs(self) -> Dict[str, Any]:
        """Load and merge all configuration files"""
        config = {}
        
        try:
            # Load base config
            base_config = self._load_yaml('base.yaml')
            config.update(base_config)
            
            # Load environment specific config
            env = os.getenv('ASTRALINK_ENV', 'development')
            env_config = self._load_yaml(f'{env}.yaml')
            config = self._deep_merge(config, env_config)
            
            # Load network config
            network_config = self._load_yaml('cellular_network.yaml')
            config['network'] = network_config
            
            # Load blockchain config
            blockchain_config = self._load_yaml('blockchain_network.yaml')
            config['blockchain'] = blockchain_config
            
            # Load security config
            security_config = self._load_yaml('security_auditor.yaml')
            config['security'] = security_config
            
            # Resolve environment variables
            config = self._resolve_env_vars(config)
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise

    def _load_yaml(self, filename: str) -> Dict:
        """Load a YAML configuration file"""
        try:
            filepath = self.config_dir / filename
            if not filepath.exists():
                logger.warning(f"Config file not found: {filename}")
                return {}
                
            with open(filepath) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return {}

    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result

    def _resolve_env_vars(self, config: Dict) -> Dict:
        """Resolve environment variables in configuration"""
        def _resolve(value):
            if isinstance(value, str):
                # Find all ${VAR} or $VAR patterns
                matches = re.finditer(r'\${([^}]+)}|\$([a-zA-Z_][a-zA-Z0-9_]*)', value)
                
                for match in matches:
                    var_name = match.group(1) or match.group(2)
                    env_value = os.getenv(var_name)
                    
                    if env_value is None:
                        logger.warning(f"Environment variable not found: {var_name}")
                        continue
                        
                    # Replace the variable with its value
                    pattern = match.group(0)
                    value = value.replace(pattern, env_value)
                    
                return value
            elif isinstance(value, dict):
                return {k: _resolve(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve(item) for item in value]
            return value
            
        return _resolve(config)

    def _validate_config(self):
        """Validate configuration against schema"""
        if not self.config_schema:
            logger.warning("No schema found for validation")
            return
            
        try:
            schema = Schema(self.config_schema)
            schema.validate(self.config)
            logger.info("Configuration validation successful")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def get_network_config(self) -> NetworkConfig:
        """Get network configuration"""
        network = self.config.get('network', {})
        return NetworkConfig(
            max_bandwidth=network.get('max_bandwidth', 10000),
            connection_timeout=network.get('connection_timeout', 3600),
            quantum_error_threshold=network.get('quantum', {}).get('error_threshold', 0.001),
            handshake_domain=network.get('handshake', {}).get('domain', 'quantum.api')
        )

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        security = self.config.get('security', {})
        return SecurityConfig(
            key_rotation_interval=security.get('key_rotation_interval', 86400),
            encryption_algorithm=security.get('encryption', {}).get('algorithm', 'AES-256-GCM'),
            quantum_safe=security.get('quantum_safe', True),
            min_key_size=security.get('min_key_size', 256)
        )

    def get_blockchain_config(self) -> BlockchainConfig:
        """Get blockchain configuration"""
        blockchain = self.config.get('blockchain', {})
        return BlockchainConfig(
            chain_id=blockchain.get('chain_id', 22625),
            network=blockchain.get('network', 'mainnet'),
            contract_addresses=blockchain.get('contracts', {}).get('addresses', {}),
            gas_limit=blockchain.get('smart_contracts', {}).get('gas_limit', 2000000)
        )

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation path"""
        try:
            value = self.config
            for key in key_path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def validate_required_env_vars(self, required_vars: list):
        """Validate that required environment variables are set"""
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def get_env_specific_value(self, key_path: str, default: Any = None) -> Any:
        """Get environment-specific configuration value"""
        env = os.getenv('ASTRALINK_ENV', 'development')
        env_key = f"{env}.{key_path}"
        
        return self.get_value(env_key, self.get_value(key_path, default))

# Global configuration manager instance
config_manager = ConfigManager()

class ConfigurationError(Exception):
    pass
