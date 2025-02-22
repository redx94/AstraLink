# Resource Usage Tracker for AstraLink 
import time
import logging

resource_log = []

class ResourceUsageTracker:
    def __init__(self, resources):
        self.resources = resources
        self.start_time = time.time()

    def track_resource_usage(self):
        current_time = time.time()
        for resource, amount in self.resources.items():
            usage = amount * (current_time - self.start_time)
            resource_log.append({resource: usage})

    def view_usage_log(self):
        return resource_log

    def summary_usage(self):
        print("Resource Use Summary")
        for entry in resource_log:
            print(entry)

# Test Example
resources = {"CPU Core": 100, "Storage": 255}
tracker = ResourceUsageTracker(resources)
tracker.track_resource_usage()
tracker.summary_usage()
