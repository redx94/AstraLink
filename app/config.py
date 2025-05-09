"""
AstraLink - Configuration Module
============================

This module manages application configuration settings using Pydantic,
supporting environment variables and .env file loading.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    api_key: str
    quantum_system_endpoint: str
    ai_system_endpoint: str
    database_url: str
    log_level: str = "INFO"
    environment: str = "development"
    quantum_timeout: int = 30
    ai_model_version: str = "v1"
    max_qubits: int = 50
    security_config_path: str = "config/security_auditor.yaml"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def discover_and_integrate_component(self, component):
        """
        Dynamically discover and integrate a new configuration component into the system.
        """
        component.integrate(self)

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Integrate dynamic configuration components
    for component in settings.components:
        component.integrate(settings)
    return settings
