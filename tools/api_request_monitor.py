# API Request Monitor for AstraLink 

import datetime

class APIRequestMonitor:
    def __init__(self):
        self.request_log = []

    def log_request(self, endpoint, data):
        record = {
            "endpoint": endpoint,
            "data": data,
            "timestamp": datetime.datetime.now()
        }
        self.request_log.append(record)

    def get_report(self, start_date=None, end_date=None):
        if start_date and end_date:
            return [rec for rec in self.request_log if start_date <= rec["timestamp"] <= end_date]
        else:
            return self.request_log

    def view_report(self):
        for rec in self.request_log:
            print(f"Endpoint: {rec['endpoint']}, Data: {rec['data']}, Timestamp: {rec['timestamp']}")

# Testing the monitor
monitor = APIRequestMonitor()
monitor.log_request("/api/example", {"key": "example_value"})
monitor.view_report()
