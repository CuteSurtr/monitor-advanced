#!/usr/bin/env python3
"""
Simple test script to debug Celery import issues.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")

try:
    print("Trying to import src.celery_app...")
    from src.celery_app import app
    print("✓ Successfully imported src.celery_app.app")
    print(f"Celery app: {app}")
    print(f"Celery app name: {app.main}")
except ImportError as e:
    print(f"✗ Failed to import src.celery_app: {e}")
    
    # Try to import individual components
    try:
        print("Trying to import src...")
        import src
        print("✓ Successfully imported src")
    except ImportError as e2:
        print(f"✗ Failed to import src: {e2}")
    
    try:
        print("Trying to import src.utils.config...")
        from src.utils.config import get_config
        print("✓ Successfully imported src.utils.config")
    except ImportError as e3:
        print(f"✗ Failed to import src.utils.config: {e3}")

print("Test completed.")