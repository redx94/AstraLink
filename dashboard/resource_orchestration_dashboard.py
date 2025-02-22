# Resource Orchestration Dashboard for AstraLink

class ResourceOrchestrationDashboard:
    def __init__(self):
        self.resource_log = []
        self.last_update = None

    def add_resource(self, resource):
        self.resource_log.append(resource)
        self.last_update = {"time": "add", "resource": resource}

    def update_resource(self, old_resource, new_resource):
        for item in self.resource_log:
            if item == old_resource:
                item = new_resource
        self.last_update = {"time": "update", "old_resource": old_resource, "new_resource": new_resource}

    def get_summary(self):
        return {
            "resource_log": self.resource_log,
            "last_update": self.last_update
        }

dashboard = ResourceOrchestrationDashboard()
dashboard.add_resource("server_1")
dashboard.update_resource("server_1", "server_2")
print(dashboard.get_summary())