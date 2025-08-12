#!/usr/bin/env python3
"""
Simple test script to verify the project setup works correctly.
"""

import sys
import os

def test_imports():
    """Test that all main modules can be imported."""
    try:
        # Add src to path
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Test imports
        print("Testing imports...")
        
        from src.utils.config import get_config
        print("✓ Config module imported successfully")
        
        from src.utils.database import DatabaseManager
        print("✓ Database module imported successfully")
        
        from src.utils.cache import CacheManager
        print("✓ Cache module imported successfully")
        
        from src.celery_app import celery_app
        print("✓ Celery app imported successfully")
        
        print("\nAll imports successful! The project is properly configured.")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from src.utils.config import get_config
        
        config = get_config()
        print(f"\nConfiguration loaded successfully:")
        print(f"  Database host: {config.database.host}")
        print(f"  Redis host: {config.redis.host}")
        print(f"  Dashboard port: {config.dashboard.port}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("Stock Market Monitor - Setup Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_config()
    
    if success:
        print("\n🎉 All tests passed! The project is ready to use.")
        print("\nTo run tests, use:")
        print("  pip install -e .")
        print("  pytest -q")
        print("\nOr run with PYTHONPATH:")
        print("  PYTHONPATH=src pytest -q")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
