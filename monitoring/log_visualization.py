# Centralized Logging and Visualization Module for AstraLink

import json
import matplotlib.pyplot as plt

def generate_log_visualization(log_file):
    """ Load logs, analyze predictions, and visualize any anomalies. """
    with open(log_file, 'r') as f:
        logs = json.load(f)
    anomalies = [entry for entry in logs if entry.get("status") == "alert"]
    return anomalies

def display_log_analysis(log_data):
    # Generate a visual representation of the log data.
    data_points = [d.get("timestamp") for d in log_data]
    anomaly_counts = [1 if d.get("status") == "alert" else 0 for d in log_data]
    plt.plot(data_points, anomaly_counts, label="Anomalies Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Anomaly Count")
    plt.title("Anomalies Over Time")
    plt.legend()
    plt.show()

# Example Usage
log_file = "network_logs.json"
anomaly_data = generate_log_visualization(log_file)
display_log_analysis(anomaly_data)
