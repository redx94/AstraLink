# Debugging suite for AstraLink systems

import logging
from logging.handlers import RotatingFileHandler
from typing import Any, List
import sys
import os

# Add project root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from blockchain.contracts import mintESIM, updateStatus

class DebuggingSuite:
    def __init__(self):
        # Proper logging setup
        self.logger = logging.getLogger('debugging_suite')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler setup
        file_handler = RotatingFileHandler('debug_file.log', maxBytes=2000000, backupCount=5)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    def validate_component(self, component: Any, data: Any) -> bool:
        """Validate a component with proper error handling and logging"""
        try:
            if not hasattr(component, 'process'):
                self.logger.error(f"Component {component} does not have a process method")
                return False
                
            result = component.process(data)
            if result is not None:
                self.logger.info(f"Component {component} validation successful")
                return True
            else:
                self.logger.warning(f"Component {component} returned None")
                return False
                
        except Exception as e:
            self.logger.exception(f"Error while validating component {component}")
            return False

    def test_all(self, systems: List[Any]) -> dict:
        """Test all systems and return results dictionary"""
        results = {}
        for sys in systems:
            self.logger.info(f"Testing system: {sys}...")
            try:
                result = sys.test()
                results[str(sys)] = result
                if not result:
                    self.logger.error(f"System {sys} failed tests")
                else:
                    self.logger.info(f"System {sys} tests succeeded")
            except Exception as e:
                self.logger.exception(f"Error testing system {sys}")
                results[str(sys)] = False
                
        return results
