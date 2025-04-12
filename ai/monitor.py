import json

from sklearn.ensemble import IsolationForest

def detect_anomalies(log_file):
    with open(log_file, 'r') as f:
        logs = json.load(f)
    model = IsolationForest(n_estimators=100, contamination=0.1)
    data = [[log.get("metric", 0)] for log in logs]
    anomalies = model.fit_predict(data)
    return [log for i, log in enumerate(logs) if anomalies[i] == -1]

# Example usage
anomalies = detect_anomalies("network_logs.json")
print("Detected Analomies", anomalies)
