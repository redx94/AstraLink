from functools import lru_cache
from typing import Any, Dict, Optional
import yaml
import os
from pathlib import Path
from schema import Schema, SchemaError
import threading

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, config_dir: str = "config"):
        if not hasattr(self, 'initialized'):
            self.config_dir = Path(config_dir)
            self.config: Dict[str, Any] = {}
            self._schema = self._create_schema()
            self._load_configs()
            self.initialized = True

    def _create_schema(self) -> Schema:
        return Schema({
            'database': {
                'host': str,
                'port': int,
                'credentials': dict
            },
            'api': {
                'version': str,
                'rate_limit': int,
                'timeout': int
            },
            'logging': {
                'level': str,
                'path': str
            }
        })

    def _load_configs(self) -> None:
        try:
            for config_file in self.config_dir.glob("*.yml"):
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
                    self._validate_config(config_data)
                    self.config.update(config_data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configs: {str(e)}")

    def _validate_config(self, config: Dict) -> None:
        try:
            self._schema.validate(config)
        except SchemaError as e:
            raise ConfigurationError(f"Invalid configuration: {str(e)}")

    @lru_cache(maxsize=32)
    def get(self, key: str, default: Any = None) -> Any:
        value = os.getenv(f"ASTRALINK_{key.upper()}")
        return value or self.config.get(key, default)

    def reload(self) -> None:
        with self._lock:
            self.config.clear()
            self.get.cache_clear()
            self._load_configs()

class ConfigurationError(Exception):
    pass
