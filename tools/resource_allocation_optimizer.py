# Resource Allocation Optimizer for AstraLink

class ResourceAllocationOptimizer:
    def __init__(self, resources):
        self.resources = resources

    def optimize_allocation(self):
        """ Redistribute resources based on needs. """
        allocation_results = {}
        for resource, need in self.resources.items():
            if need == "High":
                allocation_results[resource] = "Priority assigned to high need paths"
            else:
                allocation_results[resource] = "Low priority or customized solutions"
        return allocation_results

# Test example
resources = {"server_1": "High", "server_2": "Low"}
optimizer = ResourceAllocationOptimizer(resources)
results = optimizer.optimize_allocation()
print(results)
