"""
VIX Monitoring System - Tracks volatility indices and market fear indicators.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


class VIXRegime(Enum):
    """VIX market regimes."""

    LOW_VOLATILITY = "low_volatility"  # VIX < 20
    MODERATE_VOLATILITY = "moderate"  # VIX 20-30
    HIGH_VOLATILITY = "high_volatility"  # VIX 30-40
    EXTREME_VOLATILITY = "extreme"  # VIX > 40


@dataclass
class VIXReading:
    """VIX data point."""

    timestamp: datetime
    vix_value: float
    vix9d: float = 0.0  # 9-day VIX
    vix3m: float = 0.0  # 3-month VIX
    vix6m: float = 0.0  # 6-month VIX
    vvix: float = 0.0  # VIX of VIX
    regime: VIXRegime = VIXRegime.MODERATE_VOLATILITY


@dataclass
class VolatilityAlert:
    """Volatility alert structure."""

    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    vix_value: float
    threshold: float
    regime_change: Optional[VIXRegime] = None


class VIXMonitor:
    """Comprehensive VIX and volatility monitoring system."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: CacheManager, config=None
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False

        # VIX symbols to monitor
        self.vix_symbols = {
            "VIX": "CBOE Volatility Index",
            "VIX9D": "9-Day Expected Volatility",
            "VIX3M": "3-Month Expected Volatility",
            "VIX6M": "6-Month Expected Volatility",
            "VVIX": "VIX of VIX",
            "SKEW": "CBOE Skew Index",
            "GVZ": "Gold Volatility Index",
            "OVX": "Oil Volatility Index",
            "EVZ": "Euro Currency Volatility",
            "RVX": "Russell 2000 Volatility",
        }

        # Alert thresholds
        self.thresholds = {
            "vix_spike": 30.0,  # VIX spike threshold
            "vix_extreme": 40.0,  # Extreme fear threshold
            "vix_low": 15.0,  # Complacency threshold
            "contango_steep": 0.15,  # Steep contango warning
            "backwardation": -0.05,  # Backwardation alert
            "term_structure_change": 0.10,  # Term structure change
        }

        # Historical data for analysis
        self.vix_history = []
        self.current_regime = VIXRegime.MODERATE_VOLATILITY

        # Monitoring intervals
        self.data_update_interval = 60  # 1 minute
        self.analysis_interval = 300  # 5 minutes

    async def start(self):
        """Start the VIX monitoring system."""
        self.running = True
        self.logger.info("Starting VIX monitoring system")

        try:
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self._monitor_vix_data()),
                asyncio.create_task(self._analyze_volatility_patterns()),
                asyncio.create_task(self._monitor_term_structure()),
            ]

            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            self.logger.info("VIX monitor cancelled")
        except Exception as e:
            self.logger.error(f"Error in VIX monitor: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the VIX monitoring system."""
        self.running = False
        self.logger.info("Stopping VIX monitoring system")

    async def get_current_vix_data(self) -> Dict[str, Any]:
        """
        Get current VIX data and analysis.

        Returns:
            Current VIX metrics and analysis
        """
        try:
            # Get latest VIX readings
            vix_data = await self._fetch_current_vix_data()

            if not vix_data:
                return {"error": "No VIX data available"}

            # Determine current regime
            current_regime = self._determine_vix_regime(vix_data["VIX"])

            # Calculate term structure
            term_structure = await self._calculate_term_structure(vix_data)

            # Get historical context
            historical_context = await self._get_historical_context(vix_data["VIX"])

            # Calculate volatility metrics
            volatility_metrics = await self._calculate_volatility_metrics(vix_data)

            return {
                "timestamp": datetime.now().isoformat(),
                "vix_values": vix_data,
                "current_regime": current_regime.value,
                "regime_description": self._get_regime_description(current_regime),
                "term_structure": term_structure,
                "historical_context": historical_context,
                "volatility_metrics": volatility_metrics,
                "market_stress_level": self._calculate_market_stress_level(vix_data),
                "alerts": await self._check_vix_alerts(vix_data),
            }

        except Exception as e:
            self.logger.error(f"Error getting current VIX data: {e}")
            return {"error": str(e)}

    async def analyze_vix_patterns(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Analyze VIX patterns and trends.

        Args:
            lookback_days: Days to look back for pattern analysis

        Returns:
            VIX pattern analysis
        """
        try:
            # Get historical VIX data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)

            vix_history = await self._get_vix_history(start_time, end_time)

            if not vix_history:
                return {"error": "Insufficient VIX history"}

            # Convert to pandas series for analysis
            vix_series = pd.Series(
                [reading["vix"] for reading in vix_history],
                index=[reading["timestamp"] for reading in vix_history],
            )

            # Pattern analysis
            analysis = {
                "period_days": lookback_days,
                "current_vix": vix_series.iloc[-1],
                "mean_vix": vix_series.mean(),
                "median_vix": vix_series.median(),
                "min_vix": vix_series.min(),
                "max_vix": vix_series.max(),
                "std_vix": vix_series.std(),
                "percentile_rank": self._calculate_percentile_rank(
                    vix_series.iloc[-1], vix_series
                ),
                "trend_analysis": self._analyze_vix_trend(vix_series),
                "spike_analysis": self._analyze_vix_spikes(vix_series),
                "regime_changes": self._count_regime_changes(vix_series),
                "mean_reversion": self._analyze_mean_reversion(vix_series),
                "volatility_clustering": self._analyze_volatility_clustering(
                    vix_series
                ),
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing VIX patterns: {e}")
            return {"error": str(e)}

    async def calculate_implied_volatility_term_structure(self) -> Dict[str, Any]:
        """
        Calculate and analyze the VIX term structure.

        Returns:
            Term structure analysis
        """
        try:
            # Get current VIX term structure data
            vix_data = await self._fetch_current_vix_data()

            if not all(key in vix_data for key in ["VIX", "VIX3M", "VIX6M"]):
                return {"error": "Incomplete term structure data"}

            # Calculate term structure metrics
            vix_1m = vix_data["VIX"]
            vix_3m = vix_data["VIX3M"]
            vix_6m = vix_data["VIX6M"]

            # Term structure slopes
            slope_1m_3m = (vix_3m - vix_1m) / 2  # Per month
            slope_3m_6m = (vix_6m - vix_3m) / 3  # Per month

            # Market condition indicators
            contango = vix_3m > vix_1m
            backwardation = vix_1m > vix_3m

            # Steepness measures
            steepness = (vix_6m - vix_1m) / 5  # Per month over 5 months

            # Historical comparison
            historical_slopes = await self._get_historical_term_structure_slopes()

            analysis = {
                "timestamp": datetime.now().isoformat(),
                "term_structure": {"1m": vix_1m, "3m": vix_3m, "6m": vix_6m},
                "slopes": {
                    "1m_to_3m": slope_1m_3m,
                    "3m_to_6m": slope_3m_6m,
                    "overall": steepness,
                },
                "market_structure": {
                    "is_contango": contango,
                    "is_backwardation": backwardation,
                    "steepness_percentile": self._calculate_steepness_percentile(
                        steepness, historical_slopes
                    ),
                    "structure_description": self._describe_term_structure(
                        slope_1m_3m, slope_3m_6m
                    ),
                },
                "trading_implications": self._get_term_structure_implications(
                    slope_1m_3m, steepness
                ),
                "alerts": self._check_term_structure_alerts(slope_1m_3m, steepness),
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error calculating term structure: {e}")
            return {"error": str(e)}

    async def monitor_volatility_surface_changes(
        self, underlying: str = "SPY"
    ) -> Dict[str, Any]:
        """
        Monitor changes in the volatility surface.

        Args:
            underlying: Underlying asset to monitor

        Returns:
            Volatility surface change analysis
        """
        try:
            # Get current and previous volatility surfaces
            current_surface = await self._get_volatility_surface(underlying)
            previous_surface = await self._get_previous_volatility_surface(underlying)

            if not current_surface or not previous_surface:
                return {"error": "Insufficient volatility surface data"}

            # Calculate surface changes
            changes = {
                "underlying": underlying,
                "timestamp": datetime.now().isoformat(),
                "atm_iv_change": current_surface["atm_iv"] - previous_surface["atm_iv"],
                "iv_skew_change": current_surface["iv_skew"]
                - previous_surface["iv_skew"],
                "term_structure_shift": self._calculate_term_structure_shift(
                    current_surface, previous_surface
                ),
                "volatility_smile_changes": self._analyze_smile_changes(
                    current_surface, previous_surface
                ),
                "surface_stability": self._calculate_surface_stability(
                    current_surface, previous_surface
                ),
            }

            return changes

        except Exception as e:
            self.logger.error(f"Error monitoring volatility surface changes: {e}")
            return {"error": str(e)}

    async def _monitor_vix_data(self):
        """Monitor VIX data updates."""
        while self.running:
            try:
                # Update VIX data
                vix_data = await self._fetch_current_vix_data()

                if vix_data:
                    # Store in history
                    reading = VIXReading(
                        timestamp=datetime.now(),
                        vix_value=vix_data.get("VIX", 0),
                        vix9d=vix_data.get("VIX9D", 0),
                        vix3m=vix_data.get("VIX3M", 0),
                        vix6m=vix_data.get("VIX6M", 0),
                        vvix=vix_data.get("VVIX", 0),
                        regime=self._determine_vix_regime(vix_data.get("VIX", 0)),
                    )

                    await self._store_vix_reading(reading)

                    # Check for alerts
                    alerts = await self._check_vix_alerts(vix_data)
                    for alert in alerts:
                        await self._send_volatility_alert(alert)

                await asyncio.sleep(self.data_update_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring VIX data: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _analyze_volatility_patterns(self):
        """Analyze volatility patterns periodically."""
        while self.running:
            try:
                # Perform pattern analysis
                patterns = await self.analyze_vix_patterns()

                # Cache results
                await self.cache_manager.set("vix_patterns", patterns, ttl=600)

                # Check for significant pattern changes
                await self._check_pattern_alerts(patterns)

                await asyncio.sleep(self.analysis_interval)

            except Exception as e:
                self.logger.error(f"Error analyzing volatility patterns: {e}")
                await asyncio.sleep(300)

    async def _monitor_term_structure(self):
        """Monitor VIX term structure changes."""
        while self.running:
            try:
                # Calculate term structure
                term_structure = (
                    await self.calculate_implied_volatility_term_structure()
                )

                # Cache results
                await self.cache_manager.set(
                    "vix_term_structure", term_structure, ttl=300
                )

                # Check for term structure alerts
                if "alerts" in term_structure:
                    for alert in term_structure["alerts"]:
                        await self._send_term_structure_alert(alert)

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                self.logger.error(f"Error monitoring term structure: {e}")
                await asyncio.sleep(300)

    def _determine_vix_regime(self, vix_value: float) -> VIXRegime:
        """Determine VIX market regime."""
        if vix_value < 20:
            return VIXRegime.LOW_VOLATILITY
        elif vix_value < 30:
            return VIXRegime.MODERATE_VOLATILITY
        elif vix_value < 40:
            return VIXRegime.HIGH_VOLATILITY
        else:
            return VIXRegime.EXTREME_VOLATILITY

    def _get_regime_description(self, regime: VIXRegime) -> str:
        """Get description for VIX regime."""
        descriptions = {
            VIXRegime.LOW_VOLATILITY: "Low volatility - Market complacency",
            VIXRegime.MODERATE_VOLATILITY: "Moderate volatility - Normal market conditions",
            VIXRegime.HIGH_VOLATILITY: "High volatility - Market uncertainty",
            VIXRegime.EXTREME_VOLATILITY: "Extreme volatility - Market panic/crisis",
        }
        return descriptions.get(regime, "Unknown regime")

    def _calculate_market_stress_level(
        self, vix_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate overall market stress level."""
        vix = vix_data.get("VIX", 0)
        vvix = vix_data.get("VVIX", 0)
        skew = vix_data.get("SKEW", 100)

        # Normalized stress components
        vix_stress = min(vix / 40, 1.0)  # Normalize to 40 VIX
        vvix_stress = min(vvix / 150, 1.0) if vvix > 0 else 0  # Normalize to 150 VVIX
        skew_stress = (
            max((skew - 100) / 50, 0) if skew > 100 else 0
        )  # Above 100 indicates stress

        # Weighted stress score
        stress_score = (vix_stress * 0.6 + vvix_stress * 0.3 + skew_stress * 0.1) * 100

        return {
            "stress_score": min(stress_score, 100),
            "stress_level": self._categorize_stress_level(stress_score),
            "components": {
                "vix_contribution": vix_stress * 60,
                "vvix_contribution": vvix_stress * 30,
                "skew_contribution": skew_stress * 10,
            },
        }

    def _categorize_stress_level(self, stress_score: float) -> str:
        """Categorize market stress level."""
        if stress_score < 20:
            return "Very Low"
        elif stress_score < 40:
            return "Low"
        elif stress_score < 60:
            return "Moderate"
        elif stress_score < 80:
            return "High"
        else:
            return "Extreme"

    # Analysis methods
    def _calculate_percentile_rank(self, value: float, series: pd.Series) -> float:
        """Calculate percentile rank of value in series."""
        return (series < value).mean() * 100

    def _analyze_vix_trend(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze VIX trend."""
        # Simple trend analysis using linear regression
        x = np.arange(len(series))
        slope = np.polyfit(x, series.values, 1)[0]

        return {
            "slope": slope,
            "direction": (
                "rising" if slope > 0.1 else "falling" if slope < -0.1 else "flat"
            ),
            "strength": abs(slope),
            "recent_change": (
                series.iloc[-1] - series.iloc[-5] if len(series) >= 5 else 0
            ),
        }

    def _analyze_vix_spikes(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze VIX spikes."""
        # Define spike as >20% increase from previous day
        daily_changes = series.pct_change()
        spikes = daily_changes > 0.20

        return {
            "spike_count": spikes.sum(),
            "avg_spike_size": daily_changes[spikes].mean() if spikes.any() else 0,
            "max_spike": daily_changes.max(),
            "days_since_last_spike": (
                (len(series) - spikes[::-1].idxmax()) if spikes.any() else len(series)
            ),
        }

    def _count_regime_changes(self, series: pd.Series) -> int:
        """Count regime changes in the series."""
        regimes = [self._determine_vix_regime(val) for val in series]
        changes = sum(1 for i in range(1, len(regimes)) if regimes[i] != regimes[i - 1])
        return changes

    def _analyze_mean_reversion(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze mean reversion properties."""
        mean_val = series.mean()
        current_val = series.iloc[-1]

        # Half-life estimation (simplified)
        deviations = series - mean_val
        autocorr = deviations.autocorr()
        half_life = (
            -np.log(2) / np.log(abs(autocorr)) if autocorr != 0 else float("inf")
        )

        return {
            "mean_value": mean_val,
            "current_deviation": current_val - mean_val,
            "autocorrelation": autocorr,
            "half_life_days": half_life,
            "mean_reversion_strength": 1 - abs(autocorr),
        }

    def _analyze_volatility_clustering(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze volatility clustering."""
        returns = series.pct_change().dropna()

        # GARCH-like clustering measure
        squared_returns = returns**2
        clustering = squared_returns.autocorr()

        return {
            "clustering_coefficient": clustering,
            "volatility_persistence": (
                "High"
                if clustering > 0.3
                else "Moderate" if clustering > 0.1 else "Low"
            ),
        }

    # Alert methods
    async def _check_vix_alerts(
        self, vix_data: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Check for VIX-based alerts."""
        alerts = []
        vix = vix_data.get("VIX", 0)

        # VIX spike alert
        if vix > self.thresholds["vix_spike"]:
            alerts.append(
                {
                    "type": "vix_spike",
                    "severity": (
                        "high" if vix > self.thresholds["vix_extreme"] else "medium"
                    ),
                    "message": f"VIX spike detected: {vix:.2f}",
                    "value": vix,
                    "threshold": self.thresholds["vix_spike"],
                }
            )

        # Low VIX alert (complacency)
        if vix < self.thresholds["vix_low"]:
            alerts.append(
                {
                    "type": "vix_low",
                    "severity": "info",
                    "message": f"Low VIX detected - potential complacency: {vix:.2f}",
                    "value": vix,
                    "threshold": self.thresholds["vix_low"],
                }
            )

        return alerts

    # Data access methods (to be implemented based on your data sources)
    async def _fetch_current_vix_data(self) -> Dict[str, float]:
        """Fetch current VIX data from data sources."""
        # This would fetch from CBOE, Yahoo Finance, etc.
        # For now, return sample data
        return {
            "VIX": 25.0,
            "VIX9D": 23.5,
            "VIX3M": 26.5,
            "VIX6M": 28.0,
            "VVIX": 120.0,
            "SKEW": 110.0,
        }

    async def _get_vix_history(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get VIX historical data."""
        return []

    async def _calculate_term_structure(
        self, vix_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate VIX term structure."""
        return {}

    async def _get_historical_context(self, current_vix: float) -> Dict[str, Any]:
        """Get historical context for current VIX."""
        return {}

    async def _calculate_volatility_metrics(
        self, vix_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate additional volatility metrics."""
        return {}

    async def _store_vix_reading(self, reading: VIXReading):
        """Store VIX reading in database."""
        pass

    async def _send_volatility_alert(self, alert: Dict[str, Any]):
        """Send volatility alert."""
        self.logger.info(f"VIX Alert: {alert}")

    async def _check_pattern_alerts(self, patterns: Dict[str, Any]):
        """Check for pattern-based alerts."""
        pass

    async def _send_term_structure_alert(self, alert: Dict[str, Any]):
        """Send term structure alert."""
        self.logger.info(f"Term Structure Alert: {alert}")

    # Placeholder methods for term structure analysis
    async def _get_historical_term_structure_slopes(self) -> List[float]:
        """Get historical term structure slopes."""
        return []

    def _calculate_steepness_percentile(
        self, steepness: float, historical: List[float]
    ) -> float:
        """Calculate steepness percentile."""
        return 50.0

    def _describe_term_structure(self, slope_1m_3m: float, slope_3m_6m: float) -> str:
        """Describe term structure shape."""
        return "Normal contango"

    def _get_term_structure_implications(
        self, slope: float, steepness: float
    ) -> List[str]:
        """Get trading implications of term structure."""
        return []

    def _check_term_structure_alerts(
        self, slope: float, steepness: float
    ) -> List[Dict[str, Any]]:
        """Check term structure alerts."""
        return []

    # Volatility surface methods
    async def _get_volatility_surface(self, underlying: str) -> Dict[str, Any]:
        """Get current volatility surface."""
        return {}

    async def _get_previous_volatility_surface(self, underlying: str) -> Dict[str, Any]:
        """Get previous volatility surface."""
        return {}

    def _calculate_term_structure_shift(self, current: Dict, previous: Dict) -> float:
        """Calculate term structure shift."""
        return 0.0

    def _analyze_smile_changes(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Analyze volatility smile changes."""
        return {}

    def _calculate_surface_stability(self, current: Dict, previous: Dict) -> float:
        """Calculate volatility surface stability."""
        return 0.0

    def is_healthy(self) -> bool:
        """Check if the VIX monitor is healthy."""
        return self.running
