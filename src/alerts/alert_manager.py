"""
Alert manager stub - minimal implementation to allow app to boot
"""

class AlertManager:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_alerts(self):
        return {"alerts": "stub", "count": 0}
    
    async def start_monitoring(self):
        """Start alert monitoring."""
        # Add your alert monitoring logic here
        pass 