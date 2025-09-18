"""
Configuration management for the stock monitoring system.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    type: str = "dual"  # "postgresql", "influxdb", or "dual"
    host: str = "localhost"
    port: int = 5432
    name: str = "stock_monitor"
    user: str = "stock_user"
    password: str = ""

    class InfluxDBConfig(BaseModel):
        url: str = "http://localhost:8086"
        token: str = ""
        org: str = "stock_monitor"
        bucket: str = "market_data"

    influxdb: InfluxDBConfig = InfluxDBConfig()


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0


class APIConfig(BaseModel):
    alpha_vantage: str = ""
    polygon: str = ""
    finnhub: str = ""
    news_api: str = ""
    quandl: str = ""


class DataCollectionConfig(BaseModel):
    stock_data_interval: int = 60
    commodity_data_interval: int = 300
    news_interval: int = 900
    sentiment_interval: int = 1800
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000

    class ExchangesConfig(BaseModel):
        us: list[str] = ["NYSE", "NASDAQ", "AMEX"]
        europe: list[str] = ["LSE", "FRA", "AMS", "SWX"]
        asia: list[str] = ["TSE", "HKG", "SSE", "SZSE", "NSE", "BSE"]

    exchanges: ExchangesConfig = ExchangesConfig()


class CommoditiesConfig(BaseModel):
    metals: list[str] = ["GC=F", "SI=F", "PL=F", "PA=F", "HG=F"]
    energy: list[str] = ["CL=F", "NG=F", "BZ=F"]
    agriculture: list[str] = ["ZC=F", "ZS=F", "ZW=F", "KC=F", "CT=F"]


class TechnicalIndicatorsConfig(BaseModel):
    class RSIConfig(BaseModel):
        period: int = 14
        overbought: int = 70
        oversold: int = 30

    class MACDConfig(BaseModel):
        fast_period: int = 12
        slow_period: int = 26
        signal_period: int = 9

    class BollingerBandsConfig(BaseModel):
        period: int = 20
        std_dev: int = 2

    rsi: RSIConfig = RSIConfig()
    macd: MACDConfig = MACDConfig()
    bollinger_bands: BollingerBandsConfig = BollingerBandsConfig()
    moving_averages: list[int] = [10, 20, 50, 200]


class AlertConfig(BaseModel):
    price_change_threshold: float = 5.0
    volume_spike_threshold: float = 200.0
    volatility_threshold: float = 3.0
    correlation_threshold: float = 0.8

    class EmailConfig(BaseModel):
        enabled: bool = False
        smtp_server: str = "smtp.gmail.com"
        smtp_port: int = 587
        username: str = ""
        password: str = ""

    class TelegramConfig(BaseModel):
        enabled: bool = False
        bot_token: str = ""
        chat_id: str = ""

    class WebhookConfig(BaseModel):
        enabled: bool = False
        url: str = ""

    email: EmailConfig = EmailConfig()
    telegram: TelegramConfig = TelegramConfig()
    webhook: WebhookConfig = WebhookConfig()


class PortfolioConfig(BaseModel):
    default_currency: str = "USD"
    rebalancing_frequency: str = "monthly"
    risk_tolerance: str = "moderate"
    max_position_size: float = 0.1
    stop_loss_percentage: float = 0.05


class MLConfig(BaseModel):
    class AnomalyDetectionConfig(BaseModel):
        enabled: bool = True
        algorithm: str = Field("isolation_forest", alias="model_type")
        contamination: float = 0.1
        update_frequency: str = "daily"

    class SentimentAnalysisConfig(BaseModel):
        enabled: bool = True
        algorithm: str = Field("vader", alias="model_type")
        update_frequency: str = "hourly"

    class CorrelationAnalysisConfig(BaseModel):
        enabled: bool = True
        lookback_period: int = 30
        update_frequency: str = "daily"

    model_config = {
        "populate_by_name": True,
        "protected_namespaces": (),  # silence "model_" warning
    }

    anomaly_detection: AnomalyDetectionConfig = AnomalyDetectionConfig()
    sentiment_analysis: SentimentAnalysisConfig = SentimentAnalysisConfig()
    correlation_analysis: CorrelationAnalysisConfig = CorrelationAnalysisConfig()


class DashboardConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    reload: bool = False

    class AuthConfig(BaseModel):
        enabled: bool = True
        secret_key: str = "your_secret_key_here"
        token_expire_minutes: int = 60

    auth: AuthConfig = AuthConfig()


class PrometheusConfig(BaseModel):
    enabled: bool = True
    port: int = 9090
    metrics_path: str = "/metrics"
    custom_metrics: list[str] = [
        "stock_price",
        "portfolio_value",
        "alert_count",
        "api_request_count",
        "data_collection_latency",
    ]


class GrafanaConfig(BaseModel):
    enabled: bool = True
    port: int = 3000
    admin_user: str = "admin"
    admin_password: str = "admin"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    file: str = "logs/stock_monitor.log"
    max_size: str = "100MB"
    backup_count: int = 5


class PerformanceConfig(BaseModel):
    max_workers: int = 4
    memory_limit: str = "2GB"
    cpu_limit: float = 0.8
    cache_ttl: int = 300
    max_cache_size: str = "500MB"
    batch_size: int = 1000
    connection_pool_size: int = 10


class TimezoneConfig(BaseModel):
    default: str = "UTC"

    class MarketsConfig(BaseModel):
        us: str = "America/New_York"
        europe: str = "Europe/London"
        asia: str = "Asia/Tokyo"

    markets: MarketsConfig = MarketsConfig()


class EconomicCalendarConfig(BaseModel):
    enabled: bool = True
    sources: list[str] = ["investing.com", "fxstreet.com"]
    update_frequency: str = "hourly"
    event_types: list[str] = ["GDP", "CPI", "Employment", "Interest Rate", "Earnings"]


class Config(BaseModel):
    """Main configuration class for the stock monitoring system."""

    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api_keys: APIConfig = APIConfig()
    data_collection: DataCollectionConfig = DataCollectionConfig()
    commodities: CommoditiesConfig = CommoditiesConfig()
    technical_indicators: TechnicalIndicatorsConfig = TechnicalIndicatorsConfig()
    alerts: AlertConfig = AlertConfig()
    portfolio: PortfolioConfig = PortfolioConfig()
    ml: MLConfig = MLConfig()
    dashboard: DashboardConfig = DashboardConfig()
    prometheus: PrometheusConfig = PrometheusConfig()
    grafana: GrafanaConfig = GrafanaConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    timezone: TimezoneConfig = TimezoneConfig()
    economic_calendar: EconomicCalendarConfig = EconomicCalendarConfig()

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config/config.yaml")

        config_file = Path(config_path)

        if not config_file.exists():
            # Try to load from example config
            example_config = Path("config/config.example.yaml")
            if example_config.exists():
                config_file = example_config
            else:
                # Return default config
                return cls()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            return cls(**config_data)

        except Exception as e:
            print(f"Error loading config from {config_file}: {e}")
            return cls()

    def save_to_file(self, config_path: str = "config/config.yaml"):
        """Save configuration to YAML file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(self.dict(), f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {config_file}: {e}")

    def get_database_url(self) -> str:
        """Get database connection URL."""
        if self.database.type in ["postgresql", "dual"]:
            return f"postgresql+asyncpg://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"
        elif self.database.type == "influxdb":
            return f"influxdb://{self.database.influxdb.url}"
        else:
            raise ValueError(f"Unsupported database type: {self.database.type}")

    def get_sync_database_url(self) -> str:
        """Get synchronous database connection URL for Celery tasks."""
        if self.database.type in ["postgresql", "dual"]:
            return f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"
        elif self.database.type == "influxdb":
            return f"influxdb://{self.database.influxdb.url}"
        else:
            raise ValueError(f"Unsupported database type: {self.database.type}")

    def use_postgresql(self) -> bool:
        """Check if PostgreSQL should be used."""
        return self.database.type in ["postgresql", "dual"]

    def use_influxdb(self) -> bool:
        """Check if InfluxDB should be used."""
        return self.database.type in ["influxdb", "dual"]

    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis.password:
            return f"redis://:{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"
        else:
            return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load_from_file()
    return _config


def set_config(config: Config):
    """Set global configuration instance."""
    global _config
    _config = config
