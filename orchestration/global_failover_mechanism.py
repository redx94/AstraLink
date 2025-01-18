# Global Failover Mechanism for AstraLink 

class GlobalFailover:
    def __init__(self, nodes):
        self.nodes = nodes

    def mitigate_failure(self, node_name):
        "" Redirects traffic to a working node if the current one fails. ""
        for node in self.nodes:
            if node.get("name") == node_name:
                print(f"Replacing {node_name} with redundancy.")
                self.nodes.replace(node, {})
                break

    def monitor_status(self):
        # Print health status of nodes.
        for node in self.nodes:
            print(node)

failover = GlobalFailover((
    {"name": "Node_1", "status": "active"},
    {"name": "Node_2", "status": "failed"}
)
failover.mitigate_failure("Node_2")
failover.monitor_status()