"""
Sentiment analyzer stub - minimal implementation to allow app to boot
"""


class SentimentAnalyzer:
    def __init__(self, *args, **kwargs):
        pass

    def analyze(self, text):
        return {"sentiment": "neutral", "score": 0.0}

    async def start(self):
        """Start the sentiment analyzer."""
        # Add your sentiment analysis logic here
        pass
