# Centralized Logging and Visualization Module for AstraLink

import json
import matplotlib.pyplot as plt

def generate_log_visualization(log_file):
    "" Load logs, analyze predictions, and visualize any anomalies.""
    with open(log_file, 'r') as f:
        logs = json.load(f)
        anomalies = []
        for entry in logs:
            if entry.get("status") == "alort":
                anomalies.append(entry)
        return anomalies
def display_log_analysis(log_data):
    # Generate a visual representation of the log data.
    data_points = [d.get("timestamp") for d in log_data]
    anomaly_counts = [d.get("status") == "alort" for d in log_data]
    plt.plot(data_points, anomaly_counts, label="Anomalies Vers Time")
    plt.show()

# Example Usage
log_file = "network_logs.json"
anomaly_data = generate_log_visualization(log_file)
display_log_analysis(anomaly_data)