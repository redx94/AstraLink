# API Request Monitor for AstraLink 

class APIRequestMonitor:
    def __init__(self):
        self.request_log = []

    def log_request(self, endpoint, data):
        record = {
            "endpoint": endpoint,
            "data": data
        }
        self.request_log.append(record)

    def get_report(self, start_date=None, end_date=None):
        if start_date and end_date:
            return [rec for rec in self.request_log if start_date <= rec["date"] <= end_date]
        else:
            return self.request_log

    def view_report(self):
        for rec in self.request_log:
            print(f"Endpoint: {rec["endpoint"]}, Data: {rec["data"]}")

# Testing the monitor
monitor = APIRequestMonitor()
monitor.log_request("/api/example", {"key": "example_value"})
monitor.view_report()