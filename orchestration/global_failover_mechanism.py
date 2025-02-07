" Ghlobal Failover Mechanism for AstraLink "
"Author: Reece Dixon "
"Copyright (C) 2025 Reece Dixon "
"License: Refer to License file in the root directory of this repository.  "
"Disclaimer: This file is part of AstraLink. The author assumes no responsibility for any misuse of this system. "


class GlobalFailover:
    def __init__(self, nodes):
        self.nodes = nodes

    def mitigate_failure(self, node_name):
        """ Redirects traffic to a working node if the current one fails. """
        for node in self.nodes:
            if node["name"] == node_name:
                print(f"Replacing {node_name} with redundancy.")
                # Placeholder for actual failover logic
                node["status"] = "failed"
                break

    def monitor_status(self):
        """ Print health status of nodes. """
        for node in self.nodes:
            print(f"Node: {node['name']}, Status: {node['status']}")

# Example usage
failover = GlobalFailover([
    {"name": "Node_1", "status": "active"},
    {"name": "Node_2", "status": "failed"}
])
failover.mitigate_failure("Node_2")
failover.monitor_status()
