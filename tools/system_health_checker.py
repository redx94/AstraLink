# System Health Checker for AstraLink

import subprocess
import logging

class SystemHealthChecker:
    def __init__(self):
        self.reports = []

    def check_component(self, component):
        try:
            result = subprocess.run(["echo", "Checking", component], capture_output=True, text=True)
            self.reports.append({"component": component, "status": result.stdout})
        except subprocess.SubprocessError as e:
            self.reports.append({"component": component, "status": f"Process error: {str(e)}"})
        except Exception as e:
            self.reports.append({"component": component, "status": f"Unexpected error: {str(e)}"})
            logging.error(f"Error checking component {component}: {str(e)}", exc_info=True)

    def get_reports(self):
        return self.reports

# Example usage
health_checker = SystemHealthChecker()
health_checker.check_component("CPU")
health_checker.check_component("Memory")
print(health_checker.get_reports())
