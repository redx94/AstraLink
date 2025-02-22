# Security Audit Tool for AstraLink 

class SecurityAuditTool:
    def __init__(self):
        self.reports = []

    def check_component(self, component):
        result = self.test_component(component)
        self.reports.append({
            "component": component,
            "status": result
        })

    def get_component_status(self):
        return self.reports

    def test_component(self, component):
        # Placeholder for actual component testing logic
        return "Passed" if component == "secure_component" else "Failed"

# Example usage
audit_tool = SecurityAuditTool()
audit_tool.check_component("secure_component")
audit_tool.check_component("insecure_component")
print(audit_tool.get_component_status())
