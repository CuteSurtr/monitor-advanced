"""
Advanced Options Chain Analysis and Greeks Calculator
Real-time options monitoring with volatility analysis
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf
from scipy.stats import norm
import logging

from src.utils.config import get_config
from src.utils.logger import get_logger


@dataclass
class OptionData:
    """Option data structure."""

    symbol: str
    underlying: str
    strike: float
    expiry: datetime
    option_type: str  # 'call' or 'put'
    price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class OptionsChainAnalysis:
    """Options chain analysis results."""

    underlying_symbol: str
    underlying_price: float
    analysis_timestamp: datetime
    total_call_volume: int
    total_put_volume: int
    call_put_ratio: float
    max_pain: float
    implied_volatility_rank: float
    volatility_skew: Dict[str, float]
    gamma_exposure: float
    dealer_positioning: str


class OptionsAnalyzer:
    """Advanced options chain analysis and Greeks calculation."""

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.risk_free_rate = 0.045  # Current risk-free rate (4.5%)

        # Key symbols to monitor
        self.monitored_symbols = [
            "SPY",
            "QQQ",
            "IWM",  # ETFs
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",  # Large caps
            "NVDA",
            "META",
            "NFLX",  # Tech
        ]

        # Cache for performance
        self.options_cache = {}

    async def collect_options_data(self, symbol: str) -> List[OptionData]:
        """Collect options chain data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)

            # Get stock price
            stock_info = ticker.history(period="1d")
            if stock_info.empty:
                return []

            current_price = stock_info["Close"].iloc[-1]

            # Get options expirations
            expirations = ticker.options
            if not expirations:
                return []

            options_data = []

            for expiry in expirations[:2]:  # First 2 expirations
                try:
                    option_chain = ticker.option_chain(expiry)
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d")

                    # Process calls
                    if not option_chain.calls.empty:
                        for _, call in option_chain.calls.iterrows():
                            greeks = self._calculate_greeks(
                                current_price,
                                call["strike"],
                                expiry_date,
                                call.get("impliedVolatility", 0.2),
                                "call",
                            )

                            option_data = OptionData(
                                symbol=call["contractSymbol"],
                                underlying=symbol,
                                strike=call["strike"],
                                expiry=expiry_date,
                                option_type="call",
                                price=call.get("lastPrice", 0),
                                bid=call.get("bid", 0),
                                ask=call.get("ask", 0),
                                volume=call.get("volume", 0),
                                open_interest=call.get("openInterest", 0),
                                implied_volatility=call.get("impliedVolatility", 0),
                                delta=greeks["delta"],
                                gamma=greeks["gamma"],
                                theta=greeks["theta"],
                                vega=greeks["vega"],
                                rho=greeks["rho"],
                            )
                            options_data.append(option_data)

                except Exception as e:
                    self.logger.error(f"Error processing expiry {expiry}: {e}")
                    continue

            return options_data

        except Exception as e:
            self.logger.error(f"Failed to collect options data for {symbol}: {e}")
            return []

    def _calculate_greeks(
        self, spot: float, strike: float, expiry: datetime, iv: float, option_type: str
    ) -> Dict[str, float]:
        """Calculate option Greeks using Black-Scholes model."""
        try:
            t = (expiry - datetime.now()).days / 365.0
            if t <= 0:
                return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

            d1 = (np.log(spot / strike) + (self.risk_free_rate + 0.5 * iv**2) * t) / (
                iv * np.sqrt(t)
            )
            d2 = d1 - iv * np.sqrt(t)

            if option_type == "call":
                delta = norm.cdf(d1)
                rho = strike * t * np.exp(-self.risk_free_rate * t) * norm.cdf(d2) / 100
            else:
                delta = -norm.cdf(-d1)
                rho = (
                    -strike * t * np.exp(-self.risk_free_rate * t) * norm.cdf(-d2) / 100
                )

            gamma = norm.pdf(d1) / (spot * iv * np.sqrt(t))
            theta = (
                -spot * norm.pdf(d1) * iv / (2 * np.sqrt(t))
                - self.risk_free_rate
                * strike
                * np.exp(-self.risk_free_rate * t)
                * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
            ) / 365
            vega = spot * norm.pdf(d1) * np.sqrt(t) / 100

            return {
                "delta": delta,
                "gamma": gamma,
                "theta": theta,
                "vega": vega,
                "rho": rho,
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate Greeks: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    async def analyze_options_chain(
        self, symbol: str
    ) -> Optional[OptionsChainAnalysis]:
        """Perform comprehensive options chain analysis."""
        try:
            options_data = await self.collect_options_data(symbol)
            if not options_data:
                return None

            # Get current price
            ticker = yf.Ticker(symbol)
            stock_info = ticker.history(period="1d")
            underlying_price = (
                stock_info["Close"].iloc[-1] if not stock_info.empty else 0
            )

            # Separate calls and puts
            calls = [opt for opt in options_data if opt.option_type == "call"]
            puts = [opt for opt in options_data if opt.option_type == "put"]

            # Calculate basic metrics
            total_call_volume = sum(opt.volume for opt in calls)
            total_put_volume = sum(opt.volume for opt in puts)
            call_put_ratio = (
                total_call_volume / total_put_volume if total_put_volume > 0 else 0
            )

            # Calculate max pain
            max_pain = self._calculate_max_pain(options_data, underlying_price)

            # Simple volatility skew
            vol_skew = {"put_skew": 0, "call_skew": 0, "total_skew": 0, "atm_iv": 0}

            # Calculate gamma exposure
            gamma_exposure = sum(opt.gamma * opt.open_interest for opt in options_data)

            analysis = OptionsChainAnalysis(
                underlying_symbol=symbol,
                underlying_price=underlying_price,
                analysis_timestamp=datetime.now(),
                total_call_volume=total_call_volume,
                total_put_volume=total_put_volume,
                call_put_ratio=call_put_ratio,
                max_pain=max_pain,
                implied_volatility_rank=50.0,  # Simplified
                volatility_skew=vol_skew,
                gamma_exposure=gamma_exposure,
                dealer_positioning="neutral",
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze options chain for {symbol}: {e}")
            return None

    def _calculate_max_pain(
        self, options_data: List[OptionData], underlying_price: float
    ) -> float:
        """Calculate max pain point."""
        try:
            strikes = list(set([opt.strike for opt in options_data]))
            strikes.sort()

            max_pain_strike = underlying_price
            min_total_pain = float("inf")

            for strike in strikes:
                total_pain = 0

                for opt in options_data:
                    if opt.open_interest == 0:
                        continue

                    if opt.option_type == "call" and strike > opt.strike:
                        total_pain += (strike - opt.strike) * opt.open_interest
                    elif opt.option_type == "put" and strike < opt.strike:
                        total_pain += (opt.strike - strike) * opt.open_interest

                if total_pain < min_total_pain:
                    min_total_pain = total_pain
                    max_pain_strike = strike

            return max_pain_strike

        except Exception as e:
            self.logger.error(f"Failed to calculate max pain: {e}")
            return underlying_price


# Global instance
options_analyzer = OptionsAnalyzer()
