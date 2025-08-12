#!/usr/bin/env python3
"""
Azure App Service Deployment Script
Deploys the Stock Monitor Flask API to Azure App Service
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

class AzureDeployer:
    """Handles Azure App Service deployment."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.desktop.yaml"
        self.config = self.load_config()
        self.azure_config = self.config.get('azure', {})
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Configuration file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing configuration: {e}")
            return {}
    
    def check_azure_cli(self) -> bool:
        """Check if Azure CLI is installed and authenticated."""
        try:
            result = subprocess.run(['az', 'account', 'show'], 
                                  capture_output=True, text=True, check=True)
            account_info = json.loads(result.stdout)
            print(f"✅ Authenticated with Azure account: {account_info.get('name', 'Unknown')}")
            return True
        except subprocess.CalledProcessError:
            print("❌ Azure CLI not authenticated. Please run 'az login' first.")
            return False
        except FileNotFoundError:
            print("❌ Azure CLI not installed. Please install Azure CLI first.")
            return False
    
    def create_resource_group(self, name: str, location: str) -> bool:
        """Create Azure resource group if it doesn't exist."""
        try:
            print(f"Creating resource group: {name} in {location}")
            subprocess.run(['az', 'group', 'create', '--name', name, '--location', location], 
                          check=True, capture_output=True)
            print(f"✅ Resource group '{name}' created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create resource group: {e}")
            return False
    
    def create_app_service_plan(self, name: str, resource_group: str, location: str, 
                               sku: str = "B1") -> bool:
        """Create Azure App Service plan."""
        try:
            print(f"Creating App Service plan: {name}")
            subprocess.run([
                'az', 'appservice', 'plan', 'create',
                '--name', name,
                '--resource-group', resource_group,
                '--location', location,
                '--sku', sku,
                '--is-linux'
            ], check=True, capture_output=True)
            print(f"✅ App Service plan '{name}' created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create App Service plan: {e}")
            return False
    
    def create_web_app(self, name: str, resource_group: str, plan_name: str, 
                       runtime: str = "python:3.9") -> bool:
        """Create Azure Web App."""
        try:
            print(f"Creating Web App: {name}")
            subprocess.run([
                'az', 'webapp', 'create',
                '--name', name,
                '--resource-group', resource_group,
                '--plan', plan_name,
                '--runtime', runtime
            ], check=True, capture_output=True)
            print(f"✅ Web App '{name}' created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create Web App: {e}")
            return False
    
    def configure_web_app(self, name: str, resource_group: str) -> bool:
        """Configure Web App settings."""
        try:
            print(f"Configuring Web App: {name}")
            
            # Set startup command
            startup_command = "gunicorn --bind=0.0.0.0 --workers 4 src.flask_api.app:app"
            subprocess.run([
                'az', 'webapp', 'config', 'set',
                '--name', name,
                '--resource-group', resource_group,
                '--startup-file', startup_command
            ], check=True, capture_output=True)
            
            # Set Python version
            subprocess.run([
                'az', 'webapp', 'config', 'appsettings', 'set',
                '--name', name,
                '--resource-group', resource_group,
                '--settings', 'PYTHON_VERSION=3.9'
            ], check=True, capture_output=True)
            
            # Set environment variables
            env_vars = [
                'FLASK_ENV=production',
                'SECRET_KEY=your-secret-key-here',
                'DATABASE_URL=your-database-url',
                'REDIS_URL=your-redis-url'
            ]
            
            for env_var in env_vars:
                key, value = env_var.split('=', 1)
                subprocess.run([
                    'az', 'webapp', 'config', 'appsettings', 'set',
                    '--name', name,
                    '--resource-group', resource_group,
                    '--settings', f"{key}={value}"
                ], check=True, capture_output=True)
            
            print(f"✅ Web App '{name}' configured successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to configure Web App: {e}")
            return False
    
    def deploy_code(self, name: str, resource_group: str, source_path: str = ".") -> bool:
        """Deploy code to Web App."""
        try:
            print(f"Deploying code to Web App: {name}")
            
            # Create deployment package
            deployment_dir = Path("deployment")
            deployment_dir.mkdir(exist_ok=True)
            
            # Copy source files
            subprocess.run(['cp', '-r', 'src', str(deployment_dir)], check=True)
            subprocess.run(['cp', '-r', 'config', str(deployment_dir)], check=True)
            subprocess.run(['cp', 'requirements.txt', str(deployment_dir)], check=True)
            subprocess.run(['cp', '-r', 'azure', str(deployment_dir)], check=True)
            
            # Create startup file
            startup_file = deployment_dir / "startup.txt"
            with open(startup_file, 'w') as f:
                f.write("gunicorn --bind=0.0.0.0 --workers 4 src.flask_api.app:app")
            
            # Deploy using Azure CLI
            subprocess.run([
                'az', 'webapp', 'deployment', 'source', 'config-zip',
                '--name', name,
                '--resource-group', resource_group,
                '--src', str(deployment_dir)
            ], check=True, capture_output=True)
            
            print(f"✅ Code deployed successfully to '{name}'")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy code: {e}")
            return False
    
    def get_web_app_url(self, name: str, resource_group: str) -> Optional[str]:
        """Get the URL of the deployed Web App."""
        try:
            result = subprocess.run([
                'az', 'webapp', 'show',
                '--name', name,
                '--resource-group', resource_group,
                '--query', 'defaultHostName',
                '--output', 'tsv'
            ], check=True, capture_output=True, text=True)
            
            hostname = result.stdout.strip()
            return f"https://{hostname}"
        except subprocess.CalledProcessError:
            return None
    
    def deploy(self, app_name: str, resource_group: str, location: str = "eastus") -> bool:
        """Complete deployment process."""
        print(f"🚀 Starting deployment of '{app_name}' to Azure...")
        
        # Check Azure CLI
        if not self.check_azure_cli():
            return False
        
        # Create resource group
        if not self.create_resource_group(resource_group, location):
            return False
        
        # Create App Service plan
        plan_name = f"{app_name}-plan"
        if not self.create_app_service_plan(plan_name, resource_group, location):
            return False
        
        # Create Web App
        if not self.create_web_app(app_name, resource_group, plan_name):
            return False
        
        # Configure Web App
        if not self.configure_web_app(app_name, resource_group):
            return False
        
        # Deploy code
        if not self.deploy_code(app_name, resource_group):
            return False
        
        # Get deployment URL
        url = self.get_web_app_url(app_name, resource_group)
        if url:
            print(f"🎉 Deployment completed successfully!")
            print(f"🌐 Your app is available at: {url}")
            print(f"📊 Health check: {url}/health")
            print(f"📈 API docs: {url}/api/v1/analytics/market/overview")
        else:
            print("⚠️ Deployment completed but couldn't retrieve the URL")
        
        return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy Stock Monitor to Azure App Service")
    parser.add_argument("--app-name", default="stock-monitor-api", help="Name of the Web App")
    parser.add_argument("--resource-group", default="stock-monitor-rg", help="Resource group name")
    parser.add_argument("--location", default="eastus", help="Azure region")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    deployer = AzureDeployer(args.config)
    
    if deployer.deploy(args.app_name, args.resource_group, args.location):
        print("✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

