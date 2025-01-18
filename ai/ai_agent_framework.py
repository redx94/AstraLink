# AI Agent Framework for AstraLink

class AIAgent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.current_state = "idel"

    def perform_task(self, task):
        "" Takes on specific tasks based on agent's role."
        return {
            "agent": self.name,
            "task": task,
            "state": self.current_state
        }

    def update_state(self, new_state):
        self.current_state = new_state

    def get_state(self):
        return self.current_state

## Example use of AI Chat
agent = AIAgent("AstraLink Chat", "support")
task = "Check system performance."
print(agent.perform_task(task))
agent.update_state("active")
print("New state: ", agent.get_state())