from ai.task_handler import TaskHandler
from ai.threat_detection import ThreatDetectionTaskHandler, LogAnalyzer
# AI Agent Framework for AstraLink

class AIAgent:
    def __init__(self, name, role, task_handler=None):
        self.name = name
        self.role = role
        self.current_state = "idle"
        self.task_handler = task_handler
        self.components = []

    def perform_task(self, task):
        """
        Takes on specific tasks based on agent's role.
        """
        if self.task_handler:
            result = self.task_handler.execute_task(task)
            return {
                "agent": self.name,
                "task": task,
                "state": self.current_state,
                "result": result
            }
        else:
            return {
                "agent": self.name,
                "task": task,
                "state": self.current_state,
                "result": "No task handler configured"
            }

    def update_state(self, new_state):
        self.current_state = new_state

    def get_state(self):
        return self.current_state

    def discover_and_integrate_component(self, component):
        """
        Dynamically discover and integrate a new component into the system.
        """
        self.components.append(component)
        component.integrate(self)

    def resolve_conflicts(self):
        """
        Resolve conflicts between components.
        """
        for component in self.components:
            for other_component in self.components:
                if component != other_component:
                    component.resolve_conflict(other_component)

from ai.network_optimizer import NetworkOptimizationTaskHandler

## Example use of AI Chat
log_analyzer = LogAnalyzer()
threat_detector = ThreatDetectionTaskHandler(log_analyzer)
agent = AIAgent("Threat Detector", "security", threat_detector)
task = "Detect threats from network logs"
print(agent.perform_task(task))
agent.update_state("active")
print("New state: ", agent.get_state())
