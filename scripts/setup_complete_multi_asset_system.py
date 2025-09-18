#!/usr/bin/env python3
"""
Complete Multi-Asset Trading System Setup Script
Sets up PostgreSQL database, InfluxDB buckets, and populates with sample data
"""

import subprocess
import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    try:
        logger.info(f"Running {description}...")
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, check=True)
        logger.info(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with error code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"{description} failed with exception: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['psycopg2-binary', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Installing missing packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, check=True)
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    return True

def wait_for_services():
    """Wait for Docker services to be ready"""
    logger.info("Waiting for Docker services to be ready...")
    
    # Wait for PostgreSQL
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            result = subprocess.run([
                'docker', 'exec', 'stock_monitor_postgres_desktop', 
                'pg_isready', '-U', 'stock_user', '-d', 'stock_monitor'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("PostgreSQL is ready")
                break
        except:
            pass
        
        attempt += 1
        logger.info(f"Waiting for PostgreSQL... (attempt {attempt}/{max_attempts})")
        time.sleep(2)
    
    if attempt >= max_attempts:
        logger.error("PostgreSQL service not ready after maximum attempts")
        return False
    
    # Wait for InfluxDB
    attempt = 0
    while attempt < max_attempts:
        try:
            result = subprocess.run([
                'curl', '-s', 'http://localhost:8086/health'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and 'ready' in result.stdout.lower():
                logger.info("InfluxDB is ready")
                break
        except:
            pass
        
        attempt += 1
        logger.info(f"Waiting for InfluxDB... (attempt {attempt}/{max_attempts})")
        time.sleep(2)
    
    if attempt >= max_attempts:
        logger.error("InfluxDB service not ready after maximum attempts")
        return False
    
    return True

def main():
    """Main setup function"""
    logger.info("Ä Starting Complete Multi-Asset Trading System Setup")
    logger.info("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('scripts/setup_multi_asset_database.py'):
        logger.error("Please run this script from the project root directory")
        return False
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        return False
    
    # Wait for services
    if not wait_for_services():
        logger.error("Service readiness check failed")
        return False
    
    # Step 1: Set up PostgreSQL database
    logger.info("\nä Step 1: Setting up PostgreSQL database...")
    if not run_script('scripts/setup_multi_asset_database.py', 'PostgreSQL database setup'):
        logger.error("PostgreSQL setup failed")
        return False
    
    # Step 2: Set up InfluxDB buckets
    logger.info("\nà Step 2: Setting up InfluxDB buckets...")
    if not run_script('scripts/setup_influxdb_buckets_multi_asset.py', 'InfluxDB bucket setup'):
        logger.error("InfluxDB setup failed")
        return False
    
    # Step 3: Populate with sample data
    logger.info("\nä Step 3: Populating with sample data...")
    if not run_script('scripts/generate_high_frequency_data.py', 'Sample data generation'):
        logger.error("Sample data generation failed")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("â Multi-Asset Trading System Setup Completed Successfully!")
    logger.info("\nã What was set up:")
    logger.info("   PostgreSQL database with multi-asset schemas")
    logger.info("   InfluxDB buckets for different asset types")
    logger.info("   Sample data for stocks, forex, crypto, and commodities")
    logger.info("   TimescaleDB hypertables for time-series optimization")
    logger.info("\nä Available Dashboards:")
    logger.info("   Ø Multi-Asset Trading Dashboard (InfluxDB)")
    logger.info("   Ø PostgreSQL HFT Analytics Dashboard")
    logger.info("\nß Next Steps:")
    logger.info("   1. Access Grafana at http://localhost:3000")
    logger.info("   2. Import the new dashboards")
    logger.info("   3. Configure data sources if needed")
    logger.info("   4. Start monitoring your multi-asset trading system!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        sys.exit(1)







