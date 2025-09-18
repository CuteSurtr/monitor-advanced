"""
Anomaly detector stub - minimal implementation to allow app to boot
"""


class AnomalyDetector:
    def __init__(self, *args, **kwargs):
        pass

    def detect(self, data):
        return {"anomalies": [], "score": 0.0}

    async def start(self):
        """Start the anomaly detector."""
        # Add your anomaly detection logic here
        pass
