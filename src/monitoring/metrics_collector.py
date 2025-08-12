"""
Metrics collector stub - minimal implementation to allow app to boot
"""

class MetricsCollector:
    def __init__(self, *args, **kwargs):
        pass
    
    def collect_metrics(self):
        return {"metrics": "stub", "status": "collecting"}
    
    async def start(self):
        """Start the metrics collector."""
        # Add your metrics collection logic here
        pass