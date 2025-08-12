#!/usr/bin/env python3
"""
IoT Data Simulation System for Stock Market Monitoring
Integrates with Azure IoT Hub for telemetry collection testing
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import uuid

# Azure IoT Hub dependencies
try:
    from azure.iot.device import IoTHubDeviceClient, Message
    from azure.iot.device.exceptions import IoTHubError
    AZURE_IOT_AVAILABLE = True
except ImportError:
    AZURE_IOT_AVAILABLE = False
    print("Azure IoT Hub SDK not available. Install with: pip install azure-iot-device")

from src.utils.config import Config
from src.utils.logger import setup_logging

@dataclass
class IoTDevice:
    """Represents an IoT device for stock market data collection."""
    device_id: str
    device_type: str
    location: str
    capabilities: List[str]
    status: str
    last_seen: datetime
    telemetry_interval: int  # seconds

@dataclass
class TelemetryData:
    """Represents telemetry data from IoT devices."""
    device_id: str
    timestamp: datetime
    data_type: str
    values: Dict[str, Any]
    quality_score: float
    location: str

class IoTDataSimulator:
    """Simulates IoT devices for stock market monitoring system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(config)
        self.devices: Dict[str, IoTDevice] = {}
        self.iot_hub_client: Optional[IoTHubDeviceClient] = None
        self.running = False
        self.simulation_tasks = []
        
        # Device types and their capabilities
        self.device_types = {
            'market_data_collector': {
                'capabilities': ['price_collection', 'volume_tracking', 'order_book'],
                'telemetry_interval': 5,
                'data_types': ['stock_price', 'volume', 'bid_ask_spread']
            },
            'news_sentiment_sensor': {
                'capabilities': ['news_aggregation', 'sentiment_analysis', 'trend_detection'],
                'telemetry_interval': 30,
                'data_types': ['sentiment_score', 'news_volume', 'trend_strength']
            },
            'economic_indicator_monitor': {
                'capabilities': ['gdp_tracking', 'inflation_monitoring', 'employment_data'],
                'telemetry_interval': 300,
                'data_types': ['gdp_growth', 'cpi_rate', 'unemployment_rate']
            },
            'technical_analyzer': {
                'capabilities': ['indicator_calculation', 'pattern_recognition', 'signal_generation'],
                'telemetry_interval': 60,
                'data_types': ['rsi_value', 'macd_signal', 'bollinger_position']
            },
            'portfolio_tracker': {
                'capabilities': ['position_monitoring', 'pnl_calculation', 'risk_assessment'],
                'telemetry_interval': 15,
                'data_types': ['portfolio_value', 'daily_pnl', 'risk_metrics']
            }
        }
        
        # Stock symbols for simulation
        self.stock_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 'USO', 'TLT', 'UUP'
        ]
        
        # Market indices
        self.market_indices = {
            'S&P 500': 'SPY',
            'NASDAQ': 'QQQ',
            'Russell 2000': 'IWM',
            'Dow Jones': 'DIA'
        }
        
    async def initialize_azure_iot_hub(self, connection_string: str):
        """Initialize Azure IoT Hub connection."""
        if not AZURE_IOT_AVAILABLE:
            self.logger.warning("Azure IoT Hub SDK not available. Running in simulation mode only.")
            return False
            
        try:
            self.iot_hub_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
            await self.iot_hub_client.connect()
            self.logger.info("Successfully connected to Azure IoT Hub")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Azure IoT Hub: {e}")
            return False
    
    def create_simulated_devices(self, num_devices: int = 50):
        """Create simulated IoT devices for testing."""
        self.logger.info(f"Creating {num_devices} simulated IoT devices...")
        
        locations = ['New York', 'London', 'Tokyo', 'Hong Kong', 'Frankfurt', 'Sydney', 'Toronto']
        
        for i in range(num_devices):
            device_type = random.choice(list(self.device_types.keys()))
            device_config = self.device_types[device_type]
            
            device = IoTDevice(
                device_id=f"device_{device_type}_{i:03d}",
                device_type=device_type,
                location=random.choice(locations),
                capabilities=device_config['capabilities'],
                status='active',
                last_seen=datetime.utcnow(),
                telemetry_interval=device_config['telemetry_interval']
            )
            
            self.devices[device.device_id] = device
            
        self.logger.info(f"Created {len(self.devices)} simulated devices")
    
    def generate_stock_price_data(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic stock price telemetry data."""
        base_price = random.uniform(50, 500)
        volatility = random.uniform(0.01, 0.05)
        
        # Simulate price movement
        price_change = random.gauss(0, volatility)
        new_price = base_price * (1 + price_change)
        
        volume = random.randint(1000, 1000000)
        bid_ask_spread = random.uniform(0.01, 0.50)
        
        return {
            'symbol': symbol,
            'price': round(new_price, 2),
            'volume': volume,
            'bid_ask_spread': round(bid_ask_spread, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'exchange': random.choice(['NYSE', 'NASDAQ', 'AMEX']),
            'market_cap': random.uniform(1e9, 1e12)
        }
    
    def generate_sentiment_data(self) -> Dict[str, Any]:
        """Generate news sentiment telemetry data."""
        sentiment_score = random.uniform(-1.0, 1.0)
        news_volume = random.randint(10, 1000)
        trend_strength = random.uniform(0, 1.0)
        
        return {
            'sentiment_score': round(sentiment_score, 3),
            'news_volume': news_volume,
            'trend_strength': round(trend_strength, 3),
            'positive_articles': int(news_volume * (0.5 + sentiment_score * 0.3)),
            'negative_articles': int(news_volume * (0.5 - sentiment_score * 0.3)),
            'neutral_articles': news_volume - int(news_volume * abs(sentiment_score) * 0.3)
        }
    
    def generate_economic_data(self) -> Dict[str, Any]:
        """Generate economic indicator telemetry data."""
        return {
            'gdp_growth': round(random.uniform(-2.0, 5.0), 2),
            'cpi_rate': round(random.uniform(1.0, 8.0), 2),
            'unemployment_rate': round(random.uniform(3.0, 12.0), 2),
            'interest_rate': round(random.uniform(0.0, 6.0), 2),
            'inflation_expectation': round(random.uniform(1.5, 7.0), 2),
            'consumer_confidence': round(random.uniform(50, 120), 1)
        }
    
    def generate_technical_data(self) -> Dict[str, Any]:
        """Generate technical indicator telemetry data."""
        return {
            'rsi_value': round(random.uniform(20, 80), 2),
            'macd_signal': round(random.uniform(-2, 2), 3),
            'bollinger_position': round(random.uniform(-3, 3), 2),
            'moving_average_50': round(random.uniform(0.8, 1.2), 3),
            'moving_average_200': round(random.uniform(0.8, 1.2), 3),
            'volatility_index': round(random.uniform(10, 50), 2)
        }
    
    def generate_portfolio_data(self) -> Dict[str, Any]:
        """Generate portfolio tracking telemetry data."""
        portfolio_value = random.uniform(10000, 1000000)
        daily_pnl = random.uniform(-0.1, 0.1) * portfolio_value
        
        return {
            'portfolio_value': round(portfolio_value, 2),
            'daily_pnl': round(daily_pnl, 2),
            'daily_return': round(daily_pnl / portfolio_value * 100, 2),
            'total_positions': random.randint(5, 50),
            'cash_balance': round(random.uniform(0, portfolio_value * 0.3), 2),
            'risk_metrics': {
                'var_95': round(random.uniform(0.01, 0.05), 4),
                'sharpe_ratio': round(random.uniform(-1, 2), 3),
                'max_drawdown': round(random.uniform(0.05, 0.25), 3)
            }
        }
    
    def generate_telemetry_data(self, device: IoTDevice) -> TelemetryData:
        """Generate telemetry data based on device type."""
        data_type = random.choice(self.device_types[device.device_type]['data_types'])
        
        if data_type == 'stock_price':
            symbol = random.choice(self.stock_symbols)
            values = self.generate_stock_price_data(symbol)
        elif data_type in ['sentiment_score', 'news_volume', 'trend_strength']:
            values = self.generate_sentiment_data()
        elif data_type in ['gdp_growth', 'cpi_rate', 'unemployment_rate']:
            values = self.generate_economic_data()
        elif data_type in ['rsi_value', 'macd_signal', 'bollinger_position']:
            values = self.generate_technical_data()
        elif data_type in ['portfolio_value', 'daily_pnl', 'risk_metrics']:
            values = self.generate_portfolio_data()
        else:
            values = {'raw_data': random.random()}
        
        return TelemetryData(
            device_id=device.device_id,
            timestamp=datetime.utcnow(),
            data_type=data_type,
            values=values,
            quality_score=random.uniform(0.8, 1.0),
            location=device.location
        )
    
    async def send_to_azure_iot_hub(self, telemetry_data: TelemetryData):
        """Send telemetry data to Azure IoT Hub."""
        if not self.iot_hub_client:
            return False
            
        try:
            message = Message(json.dumps(asdict(telemetry_data)))
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            
            # Add custom properties
            message.custom_properties["deviceType"] = self.devices[telemetry_data.device_id].device_type
            message.custom_properties["dataQuality"] = str(telemetry_data.quality_score)
            message.custom_properties["location"] = telemetry_data.location
            
            await self.iot_hub_client.send_message(message)
            return True
            
        except IoTHubError as e:
            self.logger.error(f"Failed to send message to IoT Hub: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending to IoT Hub: {e}")
            return False
    
    async def simulate_device_telemetry(self, device: IoTDevice):
        """Simulate continuous telemetry from a single device."""
        while self.running:
            try:
                # Generate telemetry data
                telemetry_data = self.generate_telemetry_data(device)
                
                # Update device status
                device.last_seen = datetime.utcnow()
                
                # Send to Azure IoT Hub if available
                if self.iot_hub_client:
                    await self.send_to_azure_iot_hub(telemetry_data)
                
                # Log telemetry data
                self.logger.debug(f"Device {device.device_id} sent {telemetry_data.data_type} data")
                
                # Wait for next telemetry interval
                await asyncio.sleep(device.telemetry_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in device {device.device_id} simulation: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def start_simulation(self, num_devices: int = 50, azure_connection_string: Optional[str] = None):
        """Start the IoT simulation system."""
        self.logger.info("Starting IoT data simulation system...")
        
        # Initialize Azure IoT Hub if connection string provided
        if azure_connection_string:
            await self.initialize_azure_iot_hub(azure_connection_string)
        
        # Create simulated devices
        self.create_simulated_devices(num_devices)
        
        # Start simulation
        self.running = True
        
        # Start telemetry simulation for each device
        for device in self.devices.values():
            task = asyncio.create_task(self.simulate_device_telemetry(device))
            self.simulation_tasks.append(task)
        
        self.logger.info(f"Started simulation for {len(self.devices)} devices")
        
        # Keep simulation running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop_simulation()
    
    async def stop_simulation(self):
        """Stop the IoT simulation system."""
        self.logger.info("Stopping IoT simulation system...")
        self.running = False
        
        # Cancel all simulation tasks
        for task in self.simulation_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.simulation_tasks:
            await asyncio.gather(*self.simulation_tasks, return_exceptions=True)
        
        # Disconnect from Azure IoT Hub
        if self.iot_hub_client:
            await self.iot_hub_client.disconnect()
        
        self.logger.info("IoT simulation system stopped")
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        active_devices = sum(1 for device in self.devices.values() if device.status == 'active')
        
        return {
            'running': self.running,
            'total_devices': len(self.devices),
            'active_devices': active_devices,
            'azure_connected': self.iot_hub_client is not None,
            'simulation_start_time': getattr(self, '_start_time', None),
            'devices_by_type': self._count_devices_by_type()
        }
    
    def _count_devices_by_type(self) -> Dict[str, int]:
        """Count devices by type."""
        counts = {}
        for device in self.devices.values():
            counts[device.device_type] = counts.get(device.device_type, 0) + 1
        return counts

async def main():
    """Main function for testing the IoT simulator."""
    config = Config()
    simulator = IoTDataSimulator(config)
    
    try:
        # Start simulation with 50 devices
        await simulator.start_simulation(num_devices=50)
    except KeyboardInterrupt:
        print("\nShutting down IoT simulator...")
    finally:
        await simulator.stop_simulation()

if __name__ == "__main__":
    asyncio.run(main())

