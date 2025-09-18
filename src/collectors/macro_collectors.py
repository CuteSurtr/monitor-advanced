"""
Macro Economic Data Collectors for InfluxDB
Supports BEA, FINRA, Treasury, BLS, FRED, ECB, IMF, BIS, World Bank, BoC, OECD
"""

import asyncio
import aiohttp
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


@dataclass
class MacroDataPoint:
    """Standard macro data point structure"""

    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, float]
    timestamp: datetime


class MacroDataCollector:
    """Base class for macro economic data collectors"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        self.influx_client = influx_client
        self.bucket = bucket
        self.write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    async def collect_data(self) -> List[MacroDataPoint]:
        """Override in subclasses"""
        raise NotImplementedError

    async def store_data(self, data_points: List[MacroDataPoint]):
        """Store data points in InfluxDB"""
        points = []
        for dp in data_points:
            point = Point(dp.measurement)
            for tag_key, tag_value in dp.tags.items():
                point = point.tag(tag_key, tag_value)
            for field_key, field_value in dp.fields.items():
                point = point.field(field_key, field_value)
            point = point.time(dp.timestamp)
            points.append(point)

        if points:
            self.write_api.write(bucket=self.bucket, record=points)
            logger.info(
                f"Stored {len(points)} {data_points[0].measurement} data points"
            )


class BEACollector(MacroDataCollector):
    """Bureau of Economic Analysis (GDP, PCE, NIPA) data collector"""

    def __init__(
        self, influx_client: InfluxDBClient, api_key: str, bucket: str = "macro_data"
    ):
        super().__init__(influx_client, bucket)
        self.api_key = api_key
        self.base_url = "https://apps.bea.gov/api/data"

        # Key BEA datasets and tables
        self.datasets = {
            "NIPA": {
                "GDP": {"table": "T10101", "line": "1"},  # GDP
                "PCE": {"table": "T20804", "line": "1"},  # PCE Price Index
                "CORE_PCE": {"table": "T20804", "line": "2"},  # Core PCE
                "CONSUMPTION": {"table": "T20804", "line": "6"},  # Personal Consumption
                "INVESTMENT": {
                    "table": "T10101",
                    "line": "8",
                },  # Gross Private Investment
                "GOVERNMENT": {"table": "T10101", "line": "22"},  # Government Spending
                "TRADE_BALANCE": {"table": "T10101", "line": "14"},  # Net Exports
            }
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect BEA economic data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for indicator, config in self.datasets["NIPA"].items():
                try:
                    params = {
                        "UserID": self.api_key,
                        "method": "GetData",
                        "datasetname": "NIPA",
                        "TableName": config["table"],
                        "LineNumber": config["line"],
                        "Frequency": "Q",  # Quarterly
                        "Year": "ALL",
                        "ResultFormat": "JSON",
                    }

                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_bea_response(data, indicator)
                            data_points.extend(points)
                        else:
                            logger.error(
                                f"BEA API error for {indicator}: {response.status}"
                            )

                except Exception as e:
                    logger.error(f"Error collecting BEA {indicator} data: {e}")

                # Rate limiting
                await asyncio.sleep(0.1)

        return data_points

    def _parse_bea_response(self, data: Dict, indicator: str) -> List[MacroDataPoint]:
        """Parse BEA API response"""
        points = []

        try:
            if "BEAAPI" in data and "Results" in data["BEAAPI"]:
                results = data["BEAAPI"]["Results"]
                if "Data" in results:
                    for item in results["Data"]:
                        try:
                            # Parse date - BEA uses format like "2023Q3"
                            time_period = item.get("TimePeriod", "")
                            if "Q" in time_period:
                                year, quarter = time_period.split("Q")
                                month = int(quarter) * 3  # Q1=3, Q2=6, Q3=9, Q4=12
                                timestamp = datetime(int(year), month, 1)
                            else:
                                timestamp = datetime.strptime(time_period, "%Y")

                            value = float(item.get("DataValue", 0))

                            point = MacroDataPoint(
                                measurement="bea_economic_data",
                                tags={
                                    "indicator": indicator,
                                    "table": item.get("TableName", ""),
                                    "line": item.get("LineNumber", ""),
                                    "frequency": "quarterly",
                                },
                                fields={
                                    "value": value,
                                    "yoy_change": self._calculate_yoy_change(
                                        value, indicator, timestamp
                                    ),
                                },
                                timestamp=timestamp,
                            )
                            points.append(point)

                        except (ValueError, KeyError) as e:
                            logger.warning(f"Error parsing BEA data point: {e}")

        except Exception as e:
            logger.error(f"Error parsing BEA response: {e}")

        return points

    def _calculate_yoy_change(
        self, current_value: float, indicator: str, timestamp: datetime
    ) -> float:
        """Calculate year-over-year change (placeholder - would need historical data)"""
        # In a real implementation, you'd query historical data from InfluxDB
        return 0.0


class FINRACollector(MacroDataCollector):
    """FINRA short interest and volume data collector"""

    def __init__(
        self, influx_client: InfluxDBClient, api_key: str, bucket: str = "macro_data"
    ):
        super().__init__(influx_client, bucket)
        self.api_key = api_key
        self.base_url = "https://api.finra.org/data/group"

        # Key symbols to track
        self.symbols = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "NVDA",
            "META",
            "NFLX",
            "SPY",
            "QQQ",
        ]

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect FINRA short interest and volume data"""
        data_points = []

        # Collect short interest data
        short_data = await self._collect_short_interest()
        data_points.extend(short_data)

        # Collect short sale volume data
        volume_data = await self._collect_short_volume()
        data_points.extend(volume_data)

        return data_points

    async def _collect_short_interest(self) -> List[MacroDataPoint]:
        """Collect consolidated short interest data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            headers = {"X-API-KEY": self.api_key}

            # Get latest settlement date
            url = f"{self.base_url}/otcMarket/consolidatedShortInterest/getFilters"

            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        filters = await response.json()
                        latest_date = max(filters.get("settlementDate", []))

                        # Get short interest for each symbol
                        for symbol in self.symbols:
                            await asyncio.sleep(0.1)  # Rate limiting

                            params = {"symbol": symbol, "settlementDate": latest_date}

                            data_url = f"{self.base_url}/otcMarket/consolidatedShortInterest/getData"
                            async with session.get(
                                data_url, headers=headers, params=params
                            ) as data_response:
                                if data_response.status == 200:
                                    data = await data_response.json()
                                    points = self._parse_short_interest(data, symbol)
                                    data_points.extend(points)

            except Exception as e:
                logger.error(f"Error collecting FINRA short interest: {e}")

        return data_points

    async def _collect_short_volume(self) -> List[MacroDataPoint]:
        """Collect short sale volume data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            headers = {"X-API-KEY": self.api_key}

            try:
                # Get recent dates
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)

                for symbol in self.symbols:
                    await asyncio.sleep(0.1)  # Rate limiting

                    params = {
                        "symbol": symbol,
                        "startDate": start_date.isoformat(),
                        "endDate": end_date.isoformat(),
                    }

                    url = f"{self.base_url}/equity/aggregateShortVolume/getData"
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_short_volume(data, symbol)
                            data_points.extend(points)

            except Exception as e:
                logger.error(f"Error collecting FINRA short volume: {e}")

        return data_points

    def _parse_short_interest(
        self, data: List[Dict], symbol: str
    ) -> List[MacroDataPoint]:
        """Parse FINRA short interest response"""
        points = []

        for item in data:
            try:
                timestamp = datetime.strptime(item["settlementDate"], "%Y-%m-%d")
                short_shares = float(item.get("shortInterestQuantity", 0))
                dtc = float(item.get("daysToCover", 0))

                point = MacroDataPoint(
                    measurement="finra_short_interest",
                    tags={"symbol": symbol, "exchange": item.get("exchange", "")},
                    fields={
                        "short_shares": short_shares,
                        "days_to_cover": dtc,
                        "short_ratio": short_shares
                        / max(float(item.get("averageDailyVolume", 1)), 1),
                    },
                    timestamp=timestamp,
                )
                points.append(point)

            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing short interest data: {e}")

        return points

    def _parse_short_volume(
        self, data: List[Dict], symbol: str
    ) -> List[MacroDataPoint]:
        """Parse FINRA short volume response"""
        points = []

        for item in data:
            try:
                timestamp = datetime.strptime(item["tradeReportDate"], "%Y-%m-%d")
                short_volume = float(item.get("shortVolume", 0))
                total_volume = float(item.get("totalVolume", 1))

                point = MacroDataPoint(
                    measurement="finra_short_volume",
                    tags={"symbol": symbol},
                    fields={
                        "short_volume": short_volume,
                        "total_volume": total_volume,
                        "short_ratio": short_volume / max(total_volume, 1),
                        "short_exempt_volume": float(item.get("shortExemptVolume", 0)),
                    },
                    timestamp=timestamp,
                )
                points.append(point)

            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing short volume data: {e}")

        return points


class TreasuryCollector(MacroDataCollector):
    """Treasury FiscalData yield curve and auction data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = (
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
        )

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect Treasury yield curve and auction data"""
        data_points = []

        # Collect yield curve data
        yield_data = await self._collect_yield_curve()
        data_points.extend(yield_data)

        # Collect auction results
        auction_data = await self._collect_auction_results()
        data_points.extend(auction_data)

        return data_points

    async def _collect_yield_curve(self) -> List[MacroDataPoint]:
        """Collect daily Treasury yield curve data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            try:
                # Get recent 30 days of yield curve data
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)

                params = {
                    "filter": f"record_date:gte:{start_date},record_date:lte:{end_date}",
                    "sort": "-record_date",
                    "format": "json",
                }

                url = f"{self.base_url}/v1/accounting/od/daily_treasury_yield_curve"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        points = self._parse_yield_curve(data)
                        data_points.extend(points)

            except Exception as e:
                logger.error(f"Error collecting Treasury yield curve: {e}")

        return data_points

    async def _collect_auction_results(self) -> List[MacroDataPoint]:
        """Collect Treasury auction results"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            try:
                # Get recent 90 days of auction results
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=90)

                params = {
                    "filter": f"auction_date:gte:{start_date},auction_date:lte:{end_date}",
                    "sort": "-auction_date",
                    "format": "json",
                }

                url = f"{self.base_url}/v1/accounting/od/auction_results"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        points = self._parse_auction_results(data)
                        data_points.extend(points)

            except Exception as e:
                logger.error(f"Error collecting Treasury auctions: {e}")

        return data_points

    def _parse_yield_curve(self, data: Dict) -> List[MacroDataPoint]:
        """Parse Treasury yield curve data"""
        points = []

        try:
            for item in data.get("data", []):
                timestamp = datetime.strptime(item["record_date"], "%Y-%m-%d")

                # Create point for each tenor
                tenors = {
                    "1mo": item.get("1_mo"),
                    "2mo": item.get("2_mo"),
                    "3mo": item.get("3_mo"),
                    "6mo": item.get("6_mo"),
                    "1y": item.get("1_yr"),
                    "2y": item.get("2_yr"),
                    "3y": item.get("3_yr"),
                    "5y": item.get("5_yr"),
                    "7y": item.get("7_yr"),
                    "10y": item.get("10_yr"),
                    "20y": item.get("20_yr"),
                    "30y": item.get("30_yr"),
                }

                for tenor, yield_value in tenors.items():
                    if yield_value and yield_value != "":
                        try:
                            yield_float = float(yield_value)

                            point = MacroDataPoint(
                                measurement="treasury_yield_curve",
                                tags={"tenor": tenor, "curve_type": "nominal"},
                                fields={"yield": yield_float},
                                timestamp=timestamp,
                            )
                            points.append(point)

                        except ValueError:
                            continue

                # Calculate curve metrics
                if tenors.get("10y") and tenors.get("2y"):
                    try:
                        spread_10y2y = float(tenors["10y"]) - float(tenors["2y"])
                        inversion_flag = 1.0 if spread_10y2y < 0 else 0.0

                        point = MacroDataPoint(
                            measurement="treasury_curve_metrics",
                            tags={"metric": "10y2y_spread"},
                            fields={"spread": spread_10y2y, "inverted": inversion_flag},
                            timestamp=timestamp,
                        )
                        points.append(point)

                    except ValueError:
                        pass

        except Exception as e:
            logger.error(f"Error parsing yield curve data: {e}")

        return points

    def _parse_auction_results(self, data: Dict) -> List[MacroDataPoint]:
        """Parse Treasury auction results"""
        points = []

        try:
            for item in data.get("data", []):
                timestamp = datetime.strptime(item["auction_date"], "%Y-%m-%d")

                try:
                    high_yield = float(item.get("high_yield", 0))
                    bid_to_cover = float(item.get("bid_to_cover_ratio", 0))

                    # Calculate tail (high yield - median yield)
                    median_yield = float(item.get("median_yield", high_yield))
                    tail_bp = (
                        high_yield - median_yield
                    ) * 100  # Convert to basis points

                    point = MacroDataPoint(
                        measurement="treasury_auctions",
                        tags={
                            "security_type": item.get("security_type", ""),
                            "security_term": item.get("security_term", ""),
                            "cusip": item.get("cusip", ""),
                        },
                        fields={
                            "high_yield": high_yield,
                            "bid_to_cover": bid_to_cover,
                            "tail_bp": tail_bp,
                            "total_accepted": float(item.get("total_accepted", 0)),
                            "competitive_accepted": float(
                                item.get("competitive_accepted", 0)
                            ),
                        },
                        timestamp=timestamp,
                    )
                    points.append(point)

                except ValueError as e:
                    logger.warning(f"Error parsing auction data: {e}")

        except Exception as e:
            logger.error(f"Error parsing auction results: {e}")

        return points


class BLSCollector(MacroDataCollector):
    """Bureau of Labor Statistics (CPI, employment) data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data"

        # Key BLS series IDs
        self.series = {
            "CPI_ALL": "CUUR0000SA0",  # CPI All Items
            "CPI_CORE": "CUUR0000SA0L1E",  # CPI Core (less food & energy)
            "UNEMPLOYMENT": "LNS14000000",  # Unemployment Rate
            "PAYROLLS": "CES0000000001",  # Total Nonfarm Payrolls
            "PARTICIPATION": "LNS11300000",  # Labor Force Participation Rate
            "HOURLY_EARNINGS": "CES0500000003",  # Average Hourly Earnings
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect BLS economic data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            # Collect data for each series
            for indicator, series_id in self.series.items():
                try:
                    # Get recent 2 years of data
                    current_year = datetime.now().year

                    payload = {
                        "seriesid": [series_id],
                        "startyear": str(current_year - 2),
                        "endyear": str(current_year),
                        "registrationkey": None,  # Free tier
                    }

                    async with session.post(self.base_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_bls_response(
                                data, indicator, series_id
                            )
                            data_points.extend(points)
                        else:
                            logger.error(
                                f"BLS API error for {indicator}: {response.status}"
                            )

                except Exception as e:
                    logger.error(f"Error collecting BLS {indicator} data: {e}")

                # Rate limiting for free tier
                await asyncio.sleep(1)

        return data_points

    def _parse_bls_response(
        self, data: Dict, indicator: str, series_id: str
    ) -> List[MacroDataPoint]:
        """Parse BLS API response"""
        points = []

        try:
            if data.get("status") == "REQUEST_SUCCEEDED":
                series_data = data.get("Results", {}).get("series", [])

                for series in series_data:
                    if series.get("seriesID") == series_id:
                        for item in series.get("data", []):
                            try:
                                # Parse date - BLS uses year/period format
                                year = int(item["year"])
                                period = item["period"]

                                if period.startswith("M"):  # Monthly data
                                    month = int(period[1:])
                                    timestamp = datetime(year, month, 1)
                                elif period.startswith("Q"):  # Quarterly data
                                    quarter = int(period[1:])
                                    month = quarter * 3
                                    timestamp = datetime(year, month, 1)
                                else:
                                    continue  # Skip annual or other periods

                                value = float(item["value"])

                                # Calculate year-over-year change
                                yoy_change = 0.0
                                if "calculations" in item:
                                    calcs = item["calculations"]
                                    if "pct_changes" in calcs:
                                        pct_data = calcs["pct_changes"]
                                        if "12" in pct_data:  # 12-month change
                                            yoy_change = float(pct_data["12"])

                                point = MacroDataPoint(
                                    measurement="bls_economic_data",
                                    tags={
                                        "indicator": indicator,
                                        "series_id": series_id,
                                        "frequency": "monthly",
                                    },
                                    fields={"value": value, "yoy_change": yoy_change},
                                    timestamp=timestamp,
                                )
                                points.append(point)

                            except (ValueError, KeyError) as e:
                                logger.warning(f"Error parsing BLS data point: {e}")

        except Exception as e:
            logger.error(f"Error parsing BLS response: {e}")

        return points


class MacroDataManager:
    """Unified manager for all macro data collectors"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        self.influx_client = influx_client
        self.bucket = bucket
        self.collectors = {}

    def add_collector(self, name: str, collector: MacroDataCollector):
        """Add a data collector"""
        self.collectors[name] = collector

    async def collect_all_data(self) -> Dict[str, int]:
        """Collect data from all registered collectors"""
        results = {}

        for name, collector in self.collectors.items():
            try:
                logger.info(f"Collecting {name} data...")
                data_points = await collector.collect_data()

                if data_points:
                    await collector.store_data(data_points)
                    results[name] = len(data_points)
                else:
                    results[name] = 0

            except Exception as e:
                logger.error(f"Error collecting {name} data: {e}")
                results[name] = -1

        return results

    async def collect_specific(self, collector_names: List[str]) -> Dict[str, int]:
        """Collect data from specific collectors only"""
        results = {}

        for name in collector_names:
            if name in self.collectors:
                try:
                    logger.info(f"Collecting {name} data...")
                    collector = self.collectors[name]
                    data_points = await collector.collect_data()

                    if data_points:
                        await collector.store_data(data_points)
                        results[name] = len(data_points)
                    else:
                        results[name] = 0

                except Exception as e:
                    logger.error(f"Error collecting {name} data: {e}")
                    results[name] = -1
            else:
                logger.warning(f"Collector {name} not found")
                results[name] = -1

        return results


# Example usage and configuration
def create_macro_manager(
    influx_client: InfluxDBClient, api_keys: Dict[str, str]
) -> MacroDataManager:
    """Create and configure macro data manager"""
    manager = MacroDataManager(influx_client)

    # Add BEA collector
    if "bea_api_key" in api_keys:
        bea_collector = BEACollector(influx_client, api_keys["bea_api_key"])
        manager.add_collector("bea", bea_collector)

    # Add FINRA collector
    if "finra_api_key" in api_keys:
        finra_collector = FINRACollector(influx_client, api_keys["finra_api_key"])
        manager.add_collector("finra", finra_collector)

    # Add Treasury collector (no API key needed)
    treasury_collector = TreasuryCollector(influx_client)
    manager.add_collector("treasury", treasury_collector)

    # Add BLS collector (no API key needed for basic usage)
    bls_collector = BLSCollector(influx_client)
    manager.add_collector("bls", bls_collector)

    return manager


class FREDCollector(MacroDataCollector):
    """Federal Reserve Economic Data (FRED) collector with vintage support"""

    def __init__(
        self, influx_client: InfluxDBClient, api_key: str, bucket: str = "macro_data"
    ):
        super().__init__(influx_client, bucket)
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"

        # Key FRED series
        self.series = {
            "FEDFUNDS": "Federal Funds Rate",
            "DGS10": "10-Year Treasury Rate",
            "DGS2": "2-Year Treasury Rate",
            "UNRATE": "Unemployment Rate",
            "CPIAUCSL": "CPI All Items",
            "GDPC1": "Real GDP",
            "DEXUSEU": "US/EUR Exchange Rate",
            "VIXCLS": "VIX",
            "NFCI": "National Financial Conditions Index",
            "TEDRATE": "TED Spread",
            "HOUST": "Housing Starts",
            "INDPRO": "Industrial Production",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect FRED economic data with vintage support"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for series_id, description in self.series.items():
                try:
                    # Get current data
                    current_data = await self._fetch_series(
                        session, series_id, vintage=False
                    )
                    data_points.extend(current_data)

                    # Get vintage data for key series
                    if series_id in ["FEDFUNDS", "DGS10", "UNRATE", "CPIAUCSL"]:
                        vintage_data = await self._fetch_series(
                            session, series_id, vintage=True
                        )
                        data_points.extend(vintage_data)

                    await asyncio.sleep(0.1)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error collecting FRED {series_id} data: {e}")

        return data_points

    async def _fetch_series(
        self, session: aiohttp.ClientSession, series_id: str, vintage: bool = False
    ) -> List[MacroDataPoint]:
        """Fetch data for a specific FRED series"""
        points = []

        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 1000,
            }

            if vintage:
                # Get vintage data with realtime dates
                params["realtime_start"] = "2020-01-01"
                params["realtime_end"] = datetime.now().strftime("%Y-%m-%d")
                url = f"{self.base_url}/series/observations"
            else:
                url = f"{self.base_url}/series/observations"

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    points = self._parse_fred_response(data, series_id, vintage)

        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")

        return points

    def _parse_fred_response(
        self, data: Dict, series_id: str, vintage: bool
    ) -> List[MacroDataPoint]:
        """Parse FRED API response"""
        points = []

        try:
            for obs in data.get("observations", []):
                if obs["value"] == ".":
                    continue

                try:
                    timestamp = datetime.strptime(obs["date"], "%Y-%m-%d")
                    value = float(obs["value"])

                    tags = {
                        "series_id": series_id,
                        "units": data.get("units", ""),
                        "frequency": data.get("frequency", ""),
                    }

                    if vintage:
                        tags["vintage"] = obs.get("realtime_start", "")
                        measurement = "fred_vintage_data"
                    else:
                        measurement = "fred_economic_data"

                    point = MacroDataPoint(
                        measurement=measurement,
                        tags=tags,
                        fields={"value": value},
                        timestamp=timestamp,
                    )
                    points.append(point)

                except (ValueError, KeyError):
                    continue

        except Exception as e:
            logger.error(f"Error parsing FRED response: {e}")

        return points


class EIACollector(MacroDataCollector):
    """Energy Information Administration (EIA) data collector"""

    def __init__(
        self, influx_client: InfluxDBClient, api_key: str, bucket: str = "macro_data"
    ):
        super().__init__(influx_client, bucket)
        self.api_key = api_key
        self.base_url = "https://api.eia.gov/v2"

        # Key EIA series
        self.series = {
            "PET.WCRSTUS1.W": "Crude Oil Inventories",
            "PET.WGTSTUS1.W": "Gasoline Inventories",
            "NG.NW2_EPG0_SWO_R48_BCF.W": "Natural Gas Inventories",
            "PET.RWTC.D": "WTI Crude Oil Price",
            "NG.RNGWHHD.D": "Henry Hub Natural Gas Price",
            "ELEC.GEN.ALL-US-99.M": "Total Electricity Generation",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect EIA energy data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for series_id, description in self.series.items():
                try:
                    params = {
                        "api_key": self.api_key,
                        "frequency": (
                            "weekly"
                            if ".W" in series_id
                            else "daily" if ".D" in series_id else "monthly"
                        ),
                        "data[0]": "value",
                        "facets[seriesId][]": series_id,
                        "start": "2023-01-01",
                        "sort[0][column]": "period",
                        "sort[0][direction]": "desc",
                        "offset": "0",
                        "length": "500",
                    }

                    url = (
                        f"{self.base_url}/petroleum/stoc/wstoc/data"
                        if "PET" in series_id
                        else (
                            f"{self.base_url}/natural-gas/stor/wkly/data"
                            if "NG" in series_id
                            else f"{self.base_url}/electricity/rto/daily-fuel-type-data/data"
                        )
                    )

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_eia_response(
                                data, series_id, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.2)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error collecting EIA {series_id} data: {e}")

        return data_points

    def _parse_eia_response(
        self, data: Dict, series_id: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse EIA API response"""
        points = []

        try:
            for item in data.get("response", {}).get("data", []):
                try:
                    period = item.get("period")
                    if "-" in period:
                        timestamp = datetime.strptime(period, "%Y-%m-%d")
                    else:
                        timestamp = datetime.strptime(period, "%Y-%m")

                    value = float(item.get("value", 0))

                    point = MacroDataPoint(
                        measurement="eia_energy_data",
                        tags={
                            "series_id": series_id,
                            "description": description,
                            "units": item.get("units", ""),
                        },
                        fields={"value": value},
                        timestamp=timestamp,
                    )
                    points.append(point)

                except (ValueError, KeyError):
                    continue

        except Exception as e:
            logger.error(f"Error parsing EIA response: {e}")

        return points


class CensusCollector(MacroDataCollector):
    """US Census Bureau EITS data collector"""

    def __init__(
        self, influx_client: InfluxDBClient, api_key: str, bucket: str = "macro_data"
    ):
        super().__init__(influx_client, bucket)
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data/timeseries/eits"

        # Key Census datasets
        self.datasets = {
            "MARTS": "Monthly Retail Trade Survey",
            "M3": "Manufacturers' Shipments, Inventories, and Orders",
            "RESSALES": "New Residential Sales",
            "QSS": "Quarterly Services Survey",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect Census economic indicator data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for dataset, description in self.datasets.items():
                try:
                    params = {
                        "get": "cell_value,data_type_code,time_slot_id,error_data,category_code,seasonally_adj",
                        "for": "us:*",
                        "time": "2023,2024",
                        "key": self.api_key,
                    }

                    url = f"{self.base_url}/{dataset.lower()}"

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_census_response(
                                data, dataset, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error collecting Census {dataset} data: {e}")

        return data_points

    def _parse_census_response(
        self, data: List, dataset: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse Census API response"""
        points = []

        try:
            headers = data[0] if data else []

            for row in data[1:]:
                try:
                    record = dict(zip(headers, row))

                    # Parse time slot
                    time_slot = record.get("time_slot_id", "")
                    if len(time_slot) >= 6:
                        year = int(time_slot[:4])
                        month = int(time_slot[4:6])
                        timestamp = datetime(year, month, 1)
                    else:
                        continue

                    cell_value = record.get("cell_value")
                    if cell_value and cell_value != "(S)":
                        value = float(cell_value)

                        point = MacroDataPoint(
                            measurement="census_economic_data",
                            tags={
                                "dataset": dataset,
                                "category": record.get("category_code", ""),
                                "seasonally_adjusted": record.get("seasonally_adj", ""),
                                "data_type": record.get("data_type_code", ""),
                            },
                            fields={"value": value},
                            timestamp=timestamp,
                        )
                        points.append(point)

                except (ValueError, KeyError):
                    continue

        except Exception as e:
            logger.error(f"Error parsing Census response: {e}")

        return points


class ECBCollector(MacroDataCollector):
    """European Central Bank SDMX data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://data-api.ecb.europa.eu/service/data"

        # Key ECB series
        self.series = {
            "EXR.D.USD.EUR.SP00.A": "EUR/USD Exchange Rate",
            "FM.B.U2.EUR.4F.KR.MRR_FR.LEV": "ECB Main Refinancing Rate",
            "ICP.M.U2.N.000000.4.ANR": "HICP All Items Euro Area",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect ECB economic data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for series_key, description in self.series.items():
                try:
                    params = {
                        "startPeriod": "2023-01-01",
                        "endPeriod": datetime.now().strftime("%Y-%m-%d"),
                        "format": "jsondata",
                    }

                    url = f"{self.base_url}/{series_key}"

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_ecb_response(
                                data, series_key, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.2)

                except Exception as e:
                    logger.error(f"Error collecting ECB {series_key} data: {e}")

        return data_points

    def _parse_ecb_response(
        self, data: Dict, series_key: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse ECB SDMX response"""
        points = []

        try:
            datasets = data.get("dataSets", [])
            if datasets:
                observations = datasets[0].get("observations", {})
                structure = data.get("structure", {})
                dimensions = structure.get("dimensions", {}).get("observation", [])

                time_dimension = next(
                    (d for d in dimensions if d.get("id") == "TIME_PERIOD"), None
                )
                time_values = time_dimension.get("values", []) if time_dimension else []

                for obs_key, obs_values in observations.items():
                    try:
                        time_index = int(obs_key.split(":")[0])
                        if time_index < len(time_values):
                            time_str = time_values[time_index].get("id", "")
                            timestamp = datetime.strptime(time_str, "%Y-%m-%d")
                            value = float(obs_values[0])

                            point = MacroDataPoint(
                                measurement="ecb_economic_data",
                                tags={
                                    "series_key": series_key,
                                    "description": description,
                                },
                                fields={"value": value},
                                timestamp=timestamp,
                            )
                            points.append(point)

                    except (ValueError, KeyError, IndexError):
                        continue

        except Exception as e:
            logger.error(f"Error parsing ECB response: {e}")

        return points


class WorldBankCollector(MacroDataCollector):
    """World Bank WDI data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://api.worldbank.org/v2"

        # Key indicators
        self.indicators = {
            "NY.GDP.MKTP.KD.ZG": "GDP Growth",
            "FP.CPI.TOTL.ZG": "Inflation Rate",
            "SL.UEM.TOTL.ZS": "Unemployment Rate",
        }

        # Key countries
        self.countries = ["US", "CN", "JP", "DE", "GB", "FR", "IT", "BR", "CA", "AU"]

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect World Bank WDI data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for indicator, description in self.indicators.items():
                for country in self.countries:
                    try:
                        params = {
                            "format": "json",
                            "date": "2020:2024",
                            "per_page": "100",
                        }

                        url = f"{self.base_url}/country/{country}/indicator/{indicator}"

                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                points = self._parse_wb_response(
                                    data, indicator, description, country
                                )
                                data_points.extend(points)

                        await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.error(
                            f"Error collecting WB {indicator} data for {country}: {e}"
                        )

        return data_points

    def _parse_wb_response(
        self, data: List, indicator: str, description: str, country: str
    ) -> List[MacroDataPoint]:
        """Parse World Bank API response"""
        points = []

        try:
            if len(data) > 1:
                for item in data[1]:
                    if item.get("value") is not None:
                        try:
                            year = int(item["date"])
                            timestamp = datetime(year, 1, 1)
                            value = float(item["value"])

                            point = MacroDataPoint(
                                measurement="worldbank_data",
                                tags={
                                    "indicator": indicator,
                                    "description": description,
                                    "country": country,
                                },
                                fields={"value": value},
                                timestamp=timestamp,
                            )
                            points.append(point)

                        except (ValueError, KeyError):
                            continue

        except Exception as e:
            logger.error(f"Error parsing World Bank response: {e}")

        return points


class SECCollector(MacroDataCollector):
    """SEC EDGAR filings data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://data.sec.gov"
        self.headers = {"User-Agent": "macro-collector admin@yourcompany.com"}

        # Key CIKs to track (major companies)
        self.ciks = [
            "0000320193",  # Apple
            "0000789019",  # Microsoft
            "0001652044",  # Alphabet
            "0001018724",  # Amazon
            "0001326801",  # Meta
            "0001065280",  # Netflix
            "0001045810",  # Nvidia
        ]

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect SEC EDGAR filings data"""
        data_points = []

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for cik in self.ciks:
                try:
                    # Get company submissions
                    url = f"{self.base_url}/submissions/CIK{cik}.json"

                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_sec_submissions(data, cik)
                            data_points.extend(points)

                    await asyncio.sleep(0.1)  # SEC rate limiting

                except Exception as e:
                    logger.error(f"Error collecting SEC data for CIK {cik}: {e}")

        return data_points

    def _parse_sec_submissions(self, data: Dict, cik: str) -> List[MacroDataPoint]:
        """Parse SEC submissions data"""
        points = []

        try:
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            filing_dates = filings.get("filingDate", [])

            # Count filings by form type and quarter
            form_counts = {}
            for i, form in enumerate(forms):
                if i < len(filing_dates):
                    filing_date = filing_dates[i]
                    try:
                        date_obj = datetime.strptime(filing_date, "%Y-%m-%d")
                        quarter = f"{date_obj.year}Q{((date_obj.month - 1) // 3) + 1}"

                        key = (form, quarter)
                        form_counts[key] = form_counts.get(key, 0) + 1

                    except ValueError:
                        continue

            # Create data points for each form type/quarter
            for (form, quarter), count in form_counts.items():
                try:
                    year, q = quarter.split("Q")
                    month = int(q) * 3  # Q1=3, Q2=6, Q3=9, Q4=12
                    timestamp = datetime(int(year), month, 1)

                    point = MacroDataPoint(
                        measurement="sec_filings",
                        tags={"cik": cik, "form_type": form, "quarter": quarter},
                        fields={"filing_count": float(count)},
                        timestamp=timestamp,
                    )
                    points.append(point)

                except ValueError:
                    continue

        except Exception as e:
            logger.error(f"Error parsing SEC submissions: {e}")

        return points


class IMFCollector(MacroDataCollector):
    """IMF SDMX data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://sdmxdata.imf.org/api/v1/data"

        # Key IMF indicators
        self.indicators = {
            "IFS.A.US.GGXWDG_NGDP": "US Government Debt to GDP",
            "IFS.Q.US.NGDP_SA_XDC": "US Nominal GDP",
            "IFS.M.US.PMP_IX": "US Import Price Index",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect IMF economic data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for indicator, description in self.indicators.items():
                try:
                    params = {
                        "startPeriod": "2020",
                        "endPeriod": str(datetime.now().year),
                        "format": "json",
                    }

                    url = f"{self.base_url}/{indicator}"

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_imf_response(
                                data, indicator, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.5)  # IMF rate limiting

                except Exception as e:
                    logger.error(f"Error collecting IMF {indicator} data: {e}")

        return data_points

    def _parse_imf_response(
        self, data: Dict, indicator: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse IMF SDMX response"""
        points = []

        try:
            datasets = data.get("dataSets", [])
            if datasets:
                observations = datasets[0].get("observations", {})
                structure = data.get("structure", {})

                # Extract time dimension
                dimensions = structure.get("dimensions", {}).get("observation", [])
                time_dim = next(
                    (d for d in dimensions if d.get("id") == "TIME_PERIOD"), None
                )
                time_values = time_dim.get("values", []) if time_dim else []

                for obs_key, obs_values in observations.items():
                    try:
                        time_index = int(obs_key.split(":")[0])
                        if time_index < len(time_values):
                            time_str = time_values[time_index].get("id", "")

                            # Parse different time formats
                            if "Q" in time_str:
                                year, quarter = time_str.split("-Q")
                                month = int(quarter) * 3
                                timestamp = datetime(int(year), month, 1)
                            else:
                                timestamp = datetime(int(time_str), 1, 1)

                            value = float(obs_values[0])

                            point = MacroDataPoint(
                                measurement="imf_economic_data",
                                tags={
                                    "indicator": indicator,
                                    "description": description,
                                },
                                fields={"value": value},
                                timestamp=timestamp,
                            )
                            points.append(point)

                    except (ValueError, KeyError, IndexError):
                        continue

        except Exception as e:
            logger.error(f"Error parsing IMF response: {e}")

        return points


class BISCollector(MacroDataCollector):
    """Bank for International Settlements (BIS) SDMX data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://stats.bis.org/api/v2/data"

        # Key BIS indicators
        self.indicators = {
            "CBS.Q.US.S.A.A40.A.5J.N": "US Credit to Private Sector",
            "WEBSTATS_DER_DATAFLOW.D.US.USD.A.A.A.5J.N": "US Derivatives Statistics",
            "WS_LONG_CPI_DATAFLOW.M.US.628.N": "US Long CPI Series",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect BIS financial data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for indicator, description in self.indicators.items():
                try:
                    params = {
                        "startPeriod": "2020-Q1",
                        "endPeriod": f"{datetime.now().year}-Q4",
                        "format": "json",
                    }

                    url = f"{self.base_url}/{indicator}"

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            points = self._parse_bis_response(
                                data, indicator, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.3)  # BIS rate limiting

                except Exception as e:
                    logger.error(f"Error collecting BIS {indicator} data: {e}")

        return data_points

    def _parse_bis_response(
        self, data: Dict, indicator: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse BIS SDMX response"""
        points = []

        try:
            datasets = data.get("dataSets", [])
            if datasets:
                observations = datasets[0].get("observations", {})
                structure = data.get("structure", {})

                # Extract time dimension
                dimensions = structure.get("dimensions", {}).get("observation", [])
                time_dim = next(
                    (d for d in dimensions if d.get("id") == "TIME_PERIOD"), None
                )
                time_values = time_dim.get("values", []) if time_dim else []

                for obs_key, obs_values in observations.items():
                    try:
                        time_index = int(obs_key.split(":")[0])
                        if time_index < len(time_values):
                            time_str = time_values[time_index].get("id", "")

                            # Parse quarterly data format
                            if "Q" in time_str:
                                year, quarter = time_str.split("-Q")
                                month = int(quarter) * 3
                                timestamp = datetime(int(year), month, 1)
                            else:
                                timestamp = datetime.strptime(time_str, "%Y-%m")

                            value = float(obs_values[0])

                            point = MacroDataPoint(
                                measurement="bis_financial_data",
                                tags={
                                    "indicator": indicator,
                                    "description": description,
                                },
                                fields={"value": value},
                                timestamp=timestamp,
                            )
                            points.append(point)

                    except (ValueError, KeyError, IndexError):
                        continue

        except Exception as e:
            logger.error(f"Error parsing BIS response: {e}")

        return points


class OECDCollector(MacroDataCollector):
    """OECD SDMX data collector"""

    def __init__(self, influx_client: InfluxDBClient, bucket: str = "macro_data"):
        super().__init__(influx_client, bucket)
        self.base_url = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData"

        # Key OECD indicators
        self.indicators = {
            "CLI_LIAI.M.USA.LOLITOTR_GYSARATE": "US Composite Leading Indicator",
            "BCI_CSDB.M.USA.BS_CSCONF.LOLITOBC_GYRATE": "US Business Confidence",
            "PRICES_CPI.M.USA.CP01A1.IXOB": "US House Price Index",
        }

    async def collect_data(self) -> List[MacroDataPoint]:
        """Collect OECD economic data"""
        data_points = []

        async with aiohttp.ClientSession() as session:
            for indicator, description in self.indicators.items():
                try:
                    dataset, filter_expr = indicator.split(".", 1)

                    params = {
                        "dataset": dataset,
                        "filter": filter_expr,
                        "startTime": "2020-01",
                        "endTime": datetime.now().strftime("%Y-%m"),
                    }

                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            # OECD returns XML
                            content = await response.text()
                            points = self._parse_oecd_xml(
                                content, indicator, description
                            )
                            data_points.extend(points)

                    await asyncio.sleep(0.5)  # OECD rate limiting

                except Exception as e:
                    logger.error(f"Error collecting OECD {indicator} data: {e}")

        return data_points

    def _parse_oecd_xml(
        self, xml_content: str, indicator: str, description: str
    ) -> List[MacroDataPoint]:
        """Parse OECD XML response"""
        points = []

        try:
            root = ET.fromstring(xml_content)

            # Find observation elements
            for obs in root.iter():
                if obs.tag.endswith("Obs"):
                    try:
                        # Extract time and value
                        time_attr = obs.get("TIME_PERIOD") or obs.get("TIME")
                        value_attr = obs.get("OBS_VALUE")

                        if time_attr and value_attr:
                            if (
                                "-" in time_attr and len(time_attr) == 7
                            ):  # YYYY-MM format
                                timestamp = datetime.strptime(time_attr, "%Y-%m")
                            else:
                                timestamp = datetime.strptime(time_attr, "%Y")

                            value = float(value_attr)

                            point = MacroDataPoint(
                                measurement="oecd_economic_data",
                                tags={
                                    "indicator": indicator,
                                    "description": description,
                                },
                                fields={"value": value},
                                timestamp=timestamp,
                            )
                            points.append(point)

                    except (ValueError, ET.ParseError):
                        continue

        except Exception as e:
            logger.error(f"Error parsing OECD XML: {e}")

        return points


# Update the create_macro_manager function
def create_macro_manager(
    influx_client: InfluxDBClient, api_keys: Dict[str, str]
) -> MacroDataManager:
    """Create and configure comprehensive macro data manager"""
    manager = MacroDataManager(influx_client)

    # Add collectors requiring API keys
    if "bea_api_key" in api_keys:
        manager.add_collector(
            "bea", BEACollector(influx_client, api_keys["bea_api_key"])
        )

    if "finra_api_key" in api_keys:
        manager.add_collector(
            "finra", FINRACollector(influx_client, api_keys["finra_api_key"])
        )

    if "fred_api_key" in api_keys:
        manager.add_collector(
            "fred", FREDCollector(influx_client, api_keys["fred_api_key"])
        )

    if "eia_api_key" in api_keys:
        manager.add_collector(
            "eia", EIACollector(influx_client, api_keys["eia_api_key"])
        )

    if "census_api_key" in api_keys:
        manager.add_collector(
            "census", CensusCollector(influx_client, api_keys["census_api_key"])
        )

    # Add collectors that don't need API keys
    manager.add_collector("treasury", TreasuryCollector(influx_client))
    manager.add_collector("bls", BLSCollector(influx_client))
    manager.add_collector("ecb", ECBCollector(influx_client))
    manager.add_collector("worldbank", WorldBankCollector(influx_client))
    manager.add_collector("sec", SECCollector(influx_client))
    manager.add_collector("imf", IMFCollector(influx_client))
    manager.add_collector("bis", BISCollector(influx_client))
    manager.add_collector("oecd", OECDCollector(influx_client))

    return manager


if __name__ == "__main__":
    # Example standalone usage
    import os
    from influxdb_client import InfluxDBClient

    # InfluxDB configuration
    client = InfluxDBClient(
        url="http://localhost:8086",
        token=os.getenv("INFLUXDB_TOKEN", "your_influxdb_token"),
        org="69a6563b80682691",
    )

    # API keys
    api_keys = {
        "bea_api_key": os.getenv("BEA_API_KEY", ""),
        "finra_api_key": os.getenv("FINRA_API_KEY", ""),
        "fred_api_key": os.getenv("FRED_API_KEY", ""),
        "eia_api_key": os.getenv("EIA_API_KEY", ""),
        "census_api_key": os.getenv("CENSUS_API_KEY", ""),
    }

    # Create manager and run collection
    async def main():
        manager = create_macro_manager(client, api_keys)
        results = await manager.collect_all_data()
        print("Collection results:", results)

    asyncio.run(main())
