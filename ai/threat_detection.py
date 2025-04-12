import json
from datetime import datetime
from ai.task_handler import TaskHandler
from sklearn.ensemble import IsolationForest

class ThreatDetectionTaskHandler(TaskHandler):
    def __init__(self, log_analyzer):
        self.log_analyzer = log_analyzer
        self.model = IsolationForest(n_estimators=100, contamination=0.1)

    def execute_task(self, task):
        log_file = "network_logs_analysis.json" # TODO: Make this configurable
        threats = self.detect_threats_from_logs(log_file)
        return self.trigger_alert(threats)

    def detect_threats_from_logs(self, log_file):
        with open(log_file, 'r') as f:
            logs = json.load(f)
        data = [[self.log_analyzer.extract_metric(log)] for log in logs]
        anomalies = self.model.fit_predict(data)
        return [log for i, log in enumerate(logs) if anomalies[i] == -1]

    def trigger_alert(self, threats):
        alerts = []
        for threat in threats:
            alert = f"Threat Detected: {threat['event']} at file {threat['file']}"
            print(alert)
            alerts.append(alert)
        return alerts

class LogAnalyzer:
    def extract_metric(self, log):
        return log.get("metric")

# Example usage (moved to ai_agent_framework.py)
