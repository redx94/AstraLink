import json
from datetime import datetime
from sklearn.ensemble import IsolationForest

def detect_threats_from_logs(log_file):
    with open(log_file, 'r') as f:
        logs = json.load(f)
    model = IsolationForest(n_estimators=100, contamination=0.1)
    data = [[log.get("metric")] for log in logs]
    anomalies = model.fit_predict(data)
    return [log for i, log in enumerate(logs) if anomalies[i] == -1]

def trigger_alert(threats):
    for threat in threats:
        print(f"Threat Detected: {threat['event']} at file {threat['file']}")

# Example usage
log_path = "network_logs_analysis.json"
threats = detect_threats_from_logs(log_path)
trigger_alert(threats)
