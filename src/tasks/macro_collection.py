"""
Macro Economic Data Collection Tasks
Celery tasks for automated collection of macro economic data
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
from celery import Celery
from influxdb_client import InfluxDBClient

# Import our macro collectors
from src.collectors.macro_collectors import (
    MacroDataManager,
    BEACollector,
    FINRACollector,
    TreasuryCollector,
    BLSCollector,
    create_macro_manager,
)

logger = logging.getLogger(__name__)

# InfluxDB configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv(
    "INFLUXDB_TOKEN",
    "xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew==",
)
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "stock_monitor")

# API Keys
API_KEYS = {
    "bea_api_key": os.getenv("BEA_API_KEY", ""),
    "finra_api_key": os.getenv("FINRA_API_KEY", ""),
    "fred_api_key": os.getenv("FRED_API_KEY", ""),
}

# Celery app - will be imported from main celery_app
try:
    from src.celery_app import app as celery_app
except ImportError:
    # Fallback for standalone usage
    celery_app = Celery("macro_collection")


def get_influx_client() -> InfluxDBClient:
    """Get InfluxDB client"""
    return InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)


@celery_app.task(name="collect_all_macro_data")
def collect_all_macro_data() -> Dict[str, int]:
    """
    Collect data from all macro economic data sources
    Runs daily to gather latest economic indicators
    """
    logger.info("Starting comprehensive macro data collection")

    try:
        # Run async collection in sync context
        return asyncio.run(_async_collect_all_macro_data())
    except Exception as e:
        logger.error(f"Error in macro data collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="collect_treasury_data")
def collect_treasury_data() -> Dict[str, int]:
    """
    Collect Treasury yield curve and auction data
    Runs daily at market close
    """
    logger.info("Starting Treasury data collection")

    try:
        return asyncio.run(_async_collect_treasury_data())
    except Exception as e:
        logger.error(f"Error in Treasury data collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="collect_bea_data")
def collect_bea_data() -> Dict[str, int]:
    """
    Collect BEA economic data (GDP, PCE, etc.)
    Runs weekly as BEA data is typically monthly/quarterly
    """
    logger.info("Starting BEA data collection")

    try:
        return asyncio.run(_async_collect_bea_data())
    except Exception as e:
        logger.error(f"Error in BEA data collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="collect_bls_data")
def collect_bls_data() -> Dict[str, int]:
    """
    Collect BLS employment and inflation data
    Runs daily to catch monthly releases
    """
    logger.info("Starting BLS data collection")

    try:
        return asyncio.run(_async_collect_bls_data())
    except Exception as e:
        logger.error(f"Error in BLS data collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="collect_finra_data")
def collect_finra_data() -> Dict[str, int]:
    """
    Collect FINRA short interest and volume data
    Runs daily for short volume, bi-weekly for short interest
    """
    logger.info("Starting FINRA data collection")

    try:
        return asyncio.run(_async_collect_finra_data())
    except Exception as e:
        logger.error(f"Error in FINRA data collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="collect_economic_indicators")
def collect_economic_indicators() -> Dict[str, int]:
    """
    Collect key economic indicators for dashboard tiles
    Runs multiple times daily for timely updates
    """
    logger.info("Starting economic indicators collection")

    try:
        return asyncio.run(_async_collect_indicators())
    except Exception as e:
        logger.error(f"Error in economic indicators collection: {e}")
        return {"error": str(e)}


@celery_app.task(name="calculate_macro_metrics")
def calculate_macro_metrics() -> Dict[str, int]:
    """
    Calculate derived macro metrics and signals
    Runs after data collection to compute indicators
    """
    logger.info("Starting macro metrics calculation")

    try:
        return asyncio.run(_async_calculate_macro_metrics())
    except Exception as e:
        logger.error(f"Error calculating macro metrics: {e}")
        return {"error": str(e)}


# Async implementations


async def _async_collect_all_macro_data() -> Dict[str, int]:
    """Async implementation of comprehensive macro data collection"""

    client = get_influx_client()
    try:
        manager = create_macro_manager(client, API_KEYS)
        results = await manager.collect_all_data()

        logger.info(f"Macro data collection results: {results}")
        return results

    finally:
        client.close()


async def _async_collect_treasury_data() -> Dict[str, int]:
    """Async implementation of Treasury data collection"""

    client = get_influx_client()
    try:
        collector = TreasuryCollector(client, bucket="treasury_data")
        data_points = await collector.collect_data()

        if data_points:
            await collector.store_data(data_points)
            return {"treasury": len(data_points)}
        else:
            return {"treasury": 0}

    finally:
        client.close()


async def _async_collect_bea_data() -> Dict[str, int]:
    """Async implementation of BEA data collection"""

    if "bea_api_key" not in API_KEYS:
        logger.warning("BEA API key not available")
        return {"bea": -1}

    client = get_influx_client()
    try:
        collector = BEACollector(
            client, API_KEYS["bea_api_key"], bucket="economic_indicators"
        )
        data_points = await collector.collect_data()

        if data_points:
            await collector.store_data(data_points)
            return {"bea": len(data_points)}
        else:
            return {"bea": 0}

    finally:
        client.close()


async def _async_collect_bls_data() -> Dict[str, int]:
    """Async implementation of BLS data collection"""

    client = get_influx_client()
    try:
        collector = BLSCollector(client, bucket="economic_indicators")
        data_points = await collector.collect_data()

        if data_points:
            await collector.store_data(data_points)
            return {"bls": len(data_points)}
        else:
            return {"bls": 0}

    finally:
        client.close()


async def _async_collect_finra_data() -> Dict[str, int]:
    """Async implementation of FINRA data collection"""

    if "finra_api_key" not in API_KEYS:
        logger.warning("FINRA API key not available")
        return {"finra": -1}

    client = get_influx_client()
    try:
        collector = FINRACollector(
            client, API_KEYS["finra_api_key"], bucket="finra_data"
        )
        data_points = await collector.collect_data()

        if data_points:
            await collector.store_data(data_points)
            return {"finra": len(data_points)}
        else:
            return {"finra": 0}

    finally:
        client.close()


async def _async_collect_indicators() -> Dict[str, int]:
    """Async implementation of key indicators collection"""

    # Focus on most important daily indicators
    client = get_influx_client()
    try:
        # Collect Treasury yields (daily)
        treasury_collector = TreasuryCollector(client, bucket="economic_indicators")
        treasury_data = await treasury_collector.collect_data()

        # Store data
        total_points = 0
        if treasury_data:
            await treasury_collector.store_data(treasury_data)
            total_points += len(treasury_data)

        return {"indicators": total_points}

    finally:
        client.close()


async def _async_calculate_macro_metrics() -> Dict[str, int]:
    """Calculate derived macro metrics from collected data"""

    client = get_influx_client()
    try:
        query_api = client.query_api()
        write_api = client.write_api()

        calculated_metrics = 0

        # Calculate yield curve metrics
        calculated_metrics += await _calculate_yield_curve_metrics(query_api, write_api)

        # Calculate recession probability
        calculated_metrics += await _calculate_recession_signals(query_api, write_api)

        # Calculate inflation trends
        calculated_metrics += await _calculate_inflation_metrics(query_api, write_api)

        return {"calculated_metrics": calculated_metrics}

    finally:
        client.close()


async def _calculate_yield_curve_metrics(query_api, write_api) -> int:
    """Calculate yield curve derived metrics"""

    try:
        # Query recent yield curve data
        query = """
        from(bucket: "treasury_data")
        |> range(start: -30d)
        |> filter(fn: (r) => r._measurement == "treasury_yield_curve")
        |> filter(fn: (r) => r.tenor == "10y" or r.tenor == "2y")
        |> pivot(rowKey:["_time"], columnKey: ["tenor"], valueColumn: "_value")
        """

        tables = query_api.query(query)

        # Calculate spreads and inversion signals
        from influxdb_client import Point

        points = []

        for table in tables:
            for record in table.records:
                if hasattr(record, "10y") and hasattr(record, "2y"):
                    spread_10y2y = getattr(record, "10y") - getattr(record, "2y")
                    inversion = 1.0 if spread_10y2y < 0 else 0.0

                    point = (
                        Point("yield_curve_metrics")
                        .tag("metric", "10y2y_spread")
                        .field("spread", spread_10y2y)
                        .field("inverted", inversion)
                        .time(record.get_time())
                    )
                    points.append(point)

        if points:
            write_api.write(bucket="economic_indicators", record=points)
            return len(points)

    except Exception as e:
        logger.error(f"Error calculating yield curve metrics: {e}")

    return 0


async def _calculate_recession_signals(query_api, write_api) -> int:
    """Calculate recession probability signals"""

    try:
        # Simple recession signal based on yield curve inversion
        # In a real implementation, this would include multiple indicators

        query = """
        from(bucket: "economic_indicators")
        |> range(start: -90d)
        |> filter(fn: (r) => r._measurement == "yield_curve_metrics")
        |> filter(fn: (r) => r._field == "inverted")
        |> aggregateWindow(every: 1d, fn: mean)
        """

        tables = query_api.query(query)

        from influxdb_client import Point

        points = []

        for table in tables:
            for record in table.records:
                # Simple recession probability based on inversion duration
                inversion_level = record.get_value()
                recession_prob = min(inversion_level * 0.3, 1.0)  # Simple model

                point = (
                    Point("recession_indicators")
                    .tag("model", "yield_curve_simple")
                    .field("recession_probability", recession_prob)
                    .field("signal_strength", inversion_level)
                    .time(record.get_time())
                )
                points.append(point)

        if points:
            write_api.write(bucket="market_regime", record=points)
            return len(points)

    except Exception as e:
        logger.error(f"Error calculating recession signals: {e}")

    return 0


async def _calculate_inflation_metrics(query_api, write_api) -> int:
    """Calculate inflation trend metrics"""

    try:
        # Query recent CPI data
        query = """
        from(bucket: "economic_indicators")
        |> range(start: -365d)
        |> filter(fn: (r) => r._measurement == "bls_economic_data")
        |> filter(fn: (r) => r.indicator == "CPI_ALL" or r.indicator == "CPI_CORE")
        |> filter(fn: (r) => r._field == "yoy_change")
        """

        tables = query_api.query(query)

        from influxdb_client import Point

        points = []

        for table in tables:
            records = list(table.records)
            if len(records) >= 3:  # Need at least 3 months for trend
                recent_values = [r.get_value() for r in records[-3:]]
                trend = "rising" if recent_values[-1] > recent_values[0] else "falling"
                trend_strength = abs(recent_values[-1] - recent_values[0])

                point = (
                    Point("inflation_metrics")
                    .tag("indicator", records[-1].values.get("indicator", ""))
                    .tag("trend", trend)
                    .field("latest_yoy", recent_values[-1])
                    .field("trend_strength", trend_strength)
                    .time(records[-1].get_time())
                )
                points.append(point)

        if points:
            write_api.write(bucket="economic_indicators", record=points)
            return len(points)

    except Exception as e:
        logger.error(f"Error calculating inflation metrics: {e}")

    return 0


# Celery beat schedule configuration
MACRO_SCHEDULE = {
    "collect-treasury-data-daily": {
        "task": "collect_treasury_data",
        "schedule": 60 * 60 * 24,  # Daily at midnight
    },
    "collect-economic-indicators": {
        "task": "collect_economic_indicators",
        "schedule": 60 * 60 * 6,  # Every 6 hours
    },
    "collect-bea-data-weekly": {
        "task": "collect_bea_data",
        "schedule": 60 * 60 * 24 * 7,  # Weekly
    },
    "collect-bls-data-daily": {
        "task": "collect_bls_data",
        "schedule": 60 * 60 * 24,  # Daily
    },
    "collect-finra-data-daily": {
        "task": "collect_finra_data",
        "schedule": 60 * 60 * 24,  # Daily
    },
    "calculate-macro-metrics": {
        "task": "calculate_macro_metrics",
        "schedule": 60 * 60 * 12,  # Twice daily
    },
    "comprehensive-macro-collection": {
        "task": "collect_all_macro_data",
        "schedule": 60 * 60 * 24 * 7,  # Weekly comprehensive collection
    },
}

# Manual execution for testing
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("� Testing macro data collection...")

    # Test Treasury data collection
    print("\n� Testing Treasury data collection...")
    result = asyncio.run(_async_collect_treasury_data())
    print(f"Treasury result: {result}")

    # Test BLS data collection
    print("\n� Testing BLS data collection...")
    result = asyncio.run(_async_collect_bls_data())
    print(f"BLS result: {result}")

    # Test metric calculations
    print("\n� Testing metric calculations...")
    result = asyncio.run(_async_calculate_macro_metrics())
    print(f"Metrics result: {result}")

    print("\nMacro data collection testing complete!")
