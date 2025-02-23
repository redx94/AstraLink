from typing import Dict, Type, Any, Optional
from dataclasses import dataclass
import inspect
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServiceDescriptor:
    service_class: Type
    singleton: bool = True
    instance: Optional[Any] = None
    dependencies: Dict[str, Type] = None

class ServiceContainer:
    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._initializing: Set[str] = set()

    def register(self, interface: Type, implementation: Type, singleton: bool = True, dependencies: Dict[str, Type] = None):
        self._services[interface.__name__] = ServiceDescriptor(
            implementation, 
            singleton,
            dependencies=dependencies or {}
        )

    def resolve(self, interface: Type) -> Any:
        service_name = interface.__name__
        
        if service_name not in self._services:
            raise KeyError(f"No service registered for {service_name}")

        if service_name in self._initializing:
            raise ValueError(f"Circular dependency detected for {service_name}")

        descriptor = self._services[service_name]
        
        if descriptor.singleton and descriptor.instance:
            return descriptor.instance

        self._initializing.add(service_name)
        try:
            instance = self._create_instance(descriptor)
            if descriptor.singleton:
                descriptor.instance = instance
            return instance
        finally:
            self._initializing.remove(service_name)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        try:
            dependencies = {}
            for param_name, param_type in descriptor.dependencies.items():
                dependencies[param_name] = self.resolve(param_type)
            
            return descriptor.service_class(**dependencies)
        except Exception as e:
            logger.error(f"Failed to create instance of {descriptor.service_class.__name__}: {str(e)}")
            raise

@lru_cache()
def get_container() -> ServiceContainer:
    container = ServiceContainer()
    # Register core services
    container.register(IQuantumSystem, QuantumSystem)
    container.register(IAISystem, AISystem)
    return container
