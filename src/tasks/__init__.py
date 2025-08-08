"""
Background tasks for Stock Market Monitor.
"""

# Import all task modules to ensure they're registered with Celery
from . import data_collection
from . import analytics
from . import portfolio
from . import alerts
from . import monitoring
from . import reports
from . import maintenance

__all__ = [
    'data_collection',
    'analytics',
    'portfolio', 
    'alerts',
    'monitoring',
    'reports',
    'maintenance'
]