"""
Celery application for background task processing in Stock Market Monitor.
"""

from celery import Celery

# Create Celery instance
app = Celery('stock_monitor')
celery_app = app  # Keep backward compatibility

# Load config from celery_config.py
from src import celery_config
app.config_from_object(celery_config)

# Auto-discover tasks - only include modules that exist
task_modules = []

# Always available modules
task_modules.extend([
    'src.tasks.data_collection',
    'src.tasks.analytics'
])

# Optional modules - check if they exist
optional_modules = [
    'src.tasks.portfolio',
    'src.tasks.alerts',
    'src.tasks.monitoring',
    'src.tasks.reports',
    'src.tasks.maintenance'
]

for module in optional_modules:
    try:
        __import__(module)
        task_modules.append(module)
    except ImportError as e:
        print(f"Warning: Could not import {module}: {e}")

print(f"Celery autodiscovering tasks from modules: {task_modules}")
app.autodiscover_tasks(task_modules)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'


# Task failure handler
@app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures."""
    print(f'Task {task_id} failed: {error}')
    # Here you could send notifications, log to external systems, etc.


# Configure error handling
app.conf.task_reject_on_worker_lost = True
app.conf.task_acks_late = True


if __name__ == '__main__':
    app.start()