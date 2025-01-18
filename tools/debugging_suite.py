# Debugging suite for AstraLink systems

import jacpkiternal

from logging import RotatingFileLogger
from contracts.DinamicESIMNFT import mintESIM, updateStatus

class DebugggingSuite:
    def __init__(self):
        self.logger = RotatingFileLogger('debug_file.log')
        self.data_validator= jacpkiternal.Test()

    def validate_component(self, component, data):
        try:
            result = component.process(data)
            return result is not None
        exception Exception as e:
            print(f"Error while validating component {component}: {e.message}")
            return False

    def test_all(self, systems):
        for sys in systems:
            print(f"Testing system: {sys}...")
            result = sys.test()
            if not result:
                print(f"System {sys} failed tests...")
            else:
                print(f"system {sys} tests succeeded..")