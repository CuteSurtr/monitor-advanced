#!/usr/bin/env python3
"""
IoT System Configuration for Stock Market Monitoring
Azure IoT Hub integration settings
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class IoTConfig:
    """Configuration for IoT system."""
    
    # Azure IoT Hub Configuration
    azure_iot_hub: Dict[str, Any] = None
    
    # Device Simulation Settings
    simulation: Dict[str, Any] = None
    
    # Telemetry Configuration
    telemetry: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.azure_iot_hub is None:
            self.azure_iot_hub = {
                'enabled': os.environ.get('AZURE_IOT_ENABLED', 'false').lower() == 'true',
                'connection_string': os.environ.get('AZURE_IOT_CONNECTION_STRING', ''),
                'hub_name': os.environ.get('AZURE_IOT_HUB_NAME', ''),
                'device_id': os.environ.get('AZURE_IOT_DEVICE_ID', ''),
                'shared_access_key': os.environ.get('AZURE_IOT_SHARED_ACCESS_KEY', ''),
                'endpoint': os.environ.get('AZURE_IOT_ENDPOINT', ''),
                'max_retries': int(os.environ.get('AZURE_IOT_MAX_RETRIES', '3')),
                'retry_delay': int(os.environ.get('AZURE_IOT_RETRY_DELAY', '5')),
                'message_timeout': int(os.environ.get('AZURE_IOT_MESSAGE_TIMEOUT', '60'))
            }
        
        if self.simulation is None:
            self.simulation = {
                'enabled': os.environ.get('IOT_SIMULATION_ENABLED', 'true').lower() == 'true',
                'num_devices': int(os.environ.get('IOT_NUM_DEVICES', '50')),
                'telemetry_interval_min': int(os.environ.get('IOT_TELEMETRY_INTERVAL_MIN', '5')),
                'telemetry_interval_max': int(os.environ.get('IOT_TELEMETRY_INTERVAL_MAX', '300')),
                'data_quality_range': (
                    float(os.environ.get('IOT_DATA_QUALITY_MIN', '0.8')),
                    float(os.environ.get('IOT_DATA_QUALITY_MAX', '1.0'))
                ),
                'enable_random_failures': os.environ.get('IOT_ENABLE_FAILURES', 'false').lower() == 'true',
                'failure_rate': float(os.environ.get('IOT_FAILURE_RATE', '0.01')),
                'max_concurrent_devices': int(os.environ.get('IOT_MAX_CONCURRENT', '100'))
            }
        
        if self.telemetry is None:
            self.telemetry = {
                'batch_size': int(os.environ.get('IOT_BATCH_SIZE', '100')),
                'max_queue_size': int(os.environ.get('IOT_MAX_QUEUE_SIZE', '1000')),
                'compression_enabled': os.environ.get('IOT_COMPRESSION_ENABLED', 'true').lower() == 'true',
                'encryption_enabled': os.environ.get('IOT_ENCRYPTION_ENABLED', 'true').lower() == 'true',
                'data_retention_days': int(os.environ.get('IOT_DATA_RETENTION_DAYS', '30')),
                'enable_analytics': os.environ.get('IOT_ENABLE_ANALYTICS', 'true').lower() == 'true',
                'real_time_processing': os.environ.get('IOT_REAL_TIME_PROCESSING', 'true').lower() == 'true'
            }
    
    def get_azure_iot_connection_string(self) -> Optional[str]:
        """Get Azure IoT Hub connection string."""
        if not self.azure_iot_hub['enabled']:
            return None
        
        connection_string = self.azure_iot_hub['connection_string']
        if connection_string:
            return connection_string
        
        # Build connection string from components
        if all([
            self.azure_iot_hub['hub_name'],
            self.azure_iot_hub['device_id'],
            self.azure_iot_hub['shared_access_key']
        ]):
            return (
                f"HostName={self.azure_iot_hub['hub_name']}.azure-devices.net;"
                f"DeviceId={self.azure_iot_hub['device_id']};"
                f"SharedAccessKey={self.azure_iot_hub['shared_access_key']}"
            )
        
        return None
    
    def validate_config(self) -> bool:
        """Validate IoT configuration."""
        if self.azure_iot_hub['enabled']:
            if not self.get_azure_iot_connection_string():
                print("Warning: Azure IoT Hub enabled but connection string not configured")
                return False
        
        if self.simulation['num_devices'] > self.simulation['max_concurrent_devices']:
            print(f"Warning: Number of devices ({self.simulation['num_devices']}) exceeds max concurrent limit ({self.simulation['max_concurrent_devices']})")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'azure_iot_hub': self.azure_iot_hub,
            'simulation': self.simulation,
            'telemetry': self.telemetry
        }

# Default IoT configuration
DEFAULT_IOT_CONFIG = IoTConfig()

def load_iot_config(config_path: Optional[str] = None) -> IoTConfig:
    """Load IoT configuration from file or environment."""
    if config_path and os.path.exists(config_path):
        # Load from YAML/JSON file if provided
        import yaml
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Update default config with file data
        config = IoTConfig()
        if 'azure_iot_hub' in config_data:
            config.azure_iot_hub.update(config_data['azure_iot_hub'])
        if 'simulation' in config_data:
            config.simulation.update(config_data['simulation'])
        if 'telemetry' in config_data:
            config.telemetry.update(config_data['telemetry'])
        
        return config
    
    return DEFAULT_IOT_CONFIG

