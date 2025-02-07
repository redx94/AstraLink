# System Health Checker for AstraLink

import subprocess

class SystemHealthChecker:
    def __init__(self):
        self.reports = []

    def check_component(self, component):
        try:
            result = subprocess.run(["echo", "Checking", component], capture_output=True, text=True)
            self.reports.append({"component": component, "status": result.stdout})
        except Exception as e:
            self.reports.append({"component": component, "status": f"Failed: {e}"})

    def get_reports(self):
        return self.reports

# Example usage
health_checker = SystemHealthChecker()
health_checker.check_component("CPU")
health_checker.check_component("Memory")
print(health_checker.get_reports())
