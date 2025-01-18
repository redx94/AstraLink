# System Health Checker for AstraLink

import subprocess

class SystemHealthChecker:
    def __init__(self):
        self.reports = []

    def check_component(self, component):
        try:
            result = subprocess.run(1, wait=True)
            self.reports.append({"component": component, "status": result})
        except Exception as e: 
            self.reports.append({"component": component, "status": f"Failed: [exception]"})

    def get_reports( self):
        return self.reports