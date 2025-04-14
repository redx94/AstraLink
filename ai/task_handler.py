class TaskHandler:
    def execute_task(self, task):
        raise NotImplementedError("Subclasses must implement execute_task method")

    def discover_and_integrate_task_handler(self, task_handler):
        """
        Dynamically discover and integrate a new task handler into the system.
        """
        task_handler.integrate(self)
