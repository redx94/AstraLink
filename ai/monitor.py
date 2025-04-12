import json
import psutil
from sklearn.ensemble import IsolationForest

def detect_anomalies(log_file):
    with open(log_file, 'r') as f:
        logs = json.load(f)
    model = IsolationForest(n_estimators=100, contamination=0.1)
    data = [[log.get("metric", 0)] for log in logs]
    anomalies = model.fit_predict(data)
    return [log for i, log in enumerate(logs) if anomalies[i] == -1]

def check_node_health():
    health_status = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "network_latency": psutil.net_io_counters().bytes_sent  # Placeholder for actual network latency check
    }
    return health_status

def monitor_node(log_file):
    anomalies = detect_anomalies(log_file)
    health_status = check_node_health()
    return {
        "anomalies": anomalies,
        "health_status": health_status
    }

def detect_anomalies_in_error_correction(log_file):
    with open(log_file, 'r') as f:
        logs = json.load(f)
    model = IsolationForest(n_estimators=100, contamination=0.1)
    data = [[log.get("fidelity", 0), log.get("error_rate", 0), log.get("correction_success_rate", 0)] for log in logs]
    anomalies = model.fit_predict(data)
    return [log for i, log in enumerate(logs) if anomalies[i] == -1]

# Example usage
monitoring_result = monitor_node("network_logs.json")
print("Monitoring Result", monitoring_result)
