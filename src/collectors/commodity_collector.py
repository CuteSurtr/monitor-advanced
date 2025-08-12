"""
Commodity collector stub - minimal implementation to allow app to boot
"""

class CommodityDataCollector:
    def __init__(self, *args, **kwargs):
        pass
    
    def fetch(self):
        return []
    
    async def start(self):
        """Start the commodity data collector."""
        # Add your commodity collection logic here
        pass
