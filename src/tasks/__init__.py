"""
Background tasks for Stock Market Monitor.
"""

# Import all task modules to ensure they're registered with Celery
from . import data_collection
from . import analytics

# Import new task modules
try:
    from . import portfolio
except ImportError:
    portfolio = None

try:
    from . import alerts
except ImportError:
    alerts = None

try:
    from . import monitoring
except ImportError:
    monitoring = None

try:
    from . import reports
except ImportError:
    reports = None

try:
    from . import maintenance
except ImportError:
    maintenance = None

__all__ = [
    "data_collection",
    "analytics",
    "portfolio",
    "alerts",
    "monitoring",
    "reports",
    "maintenance",
]
