"""
Options Chain Analysis Module with Greeks calculation and volatility surface analysis.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import math

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


@dataclass
class OptionContract:
    """Option contract data structure."""
    symbol: str
    underlying: str
    expiration: datetime
    strike: float
    option_type: str  # 'call' or 'put'
    bid: float = 0.0
    ask: float = 0.0
    last_price: float = 0.0
    volume: int = 0
    open_interest: int = 0
    implied_volatility: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0


@dataclass
class VolatilitySurface:
    """Implied volatility surface data."""
    underlying: str
    strikes: List[float]
    expirations: List[datetime]
    volatilities: np.ndarray  # 2D array: strikes x expirations
    timestamp: datetime


class OptionsAnalyzer:
    """Comprehensive options chain analysis with Greeks and volatility surfaces."""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager, config=None):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False
        
        # Risk-free rate (would be fetched from Fed API in production)
        self.risk_free_rate = 0.05
        
        # Options data sources
        self.data_sources = ['polygon', 'alpha_vantage', 'yahoo']
        
        # Greeks calculation parameters
        self.spot_bump = 0.01  # 1% for delta/gamma calculation
        self.vol_bump = 0.01   # 1% for vega calculation
        self.time_bump = 1/365  # 1 day for theta calculation
    
    async def start(self):
        """Start the options analyzer background tasks."""
        self.running = True
        self.logger.info("Starting options analyzer")
        
        try:
            while self.running:
                await self._analyze_options_cycle()
                await asyncio.sleep(300)  # Run every 5 minutes
                
        except asyncio.CancelledError:
            self.logger.info("Options analyzer cancelled")
        except Exception as e:
            self.logger.error(f"Error in options analyzer: {e}")
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the options analyzer."""
        self.running = False
        self.logger.info("Stopping options analyzer")
    
    async def get_options_chain(self, underlying: str, 
                              expiration: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get complete options chain for an underlying asset.
        
        Args:
            underlying: Underlying asset symbol
            expiration: Specific expiration date (optional)
            
        Returns:
            Complete options chain with Greeks
        """
        try:
            # Get options data from cache or API
            options_data = await self._fetch_options_data(underlying, expiration)
            
            if not options_data:
                return {'error': f'No options data found for {underlying}'}
            
            # Get current underlying price
            underlying_price = await self._get_underlying_price(underlying)
            
            # Calculate Greeks for all options
            options_with_greeks = []
            for option_data in options_data:
                option = await self._create_option_contract(option_data, underlying_price)
                options_with_greeks.append(option)
            
            # Organize by expiration and type
            chain = self._organize_options_chain(options_with_greeks)
            
            # Add summary statistics
            chain['summary'] = await self._calculate_chain_summary(options_with_greeks, underlying_price)
            chain['underlying_price'] = underlying_price
            chain['timestamp'] = datetime.now().isoformat()
            
            return chain
            
        except Exception as e:
            self.logger.error(f"Error getting options chain for {underlying}: {e}")
            return {'error': str(e)}
    
    async def calculate_implied_volatility_surface(self, underlying: str) -> VolatilitySurface:
        """
        Calculate implied volatility surface for an underlying.
        
        Args:
            underlying: Underlying asset symbol
            
        Returns:
            VolatilitySurface object
        """
        try:
            # Get all options for the underlying
            options_data = await self._fetch_options_data(underlying)
            underlying_price = await self._get_underlying_price(underlying)
            
            # Extract unique strikes and expirations
            strikes = sorted(list(set(opt['strike'] for opt in options_data)))
            expirations = sorted(list(set(opt['expiration'] for opt in options_data)))
            
            # Create volatility matrix
            vol_matrix = np.zeros((len(strikes), len(expirations)))
            
            for i, strike in enumerate(strikes):
                for j, expiration in enumerate(expirations):
                    # Find option with this strike and expiration
                    option = next((opt for opt in options_data 
                                 if opt['strike'] == strike and opt['expiration'] == expiration), None)
                    
                    if option and option.get('last_price', 0) > 0:
                        # Calculate implied volatility
                        iv = await self._calculate_implied_volatility(
                            underlying_price, strike, option['last_price'],
                            self._time_to_expiration(expiration), option['option_type']
                        )
                        vol_matrix[i, j] = iv
                    else:
                        # Interpolate or use neighboring values
                        vol_matrix[i, j] = self._interpolate_volatility(vol_matrix, i, j)
            
            return VolatilitySurface(
                underlying=underlying,
                strikes=strikes,
                expirations=expirations,
                volatilities=vol_matrix,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility surface for {underlying}: {e}")
            return VolatilitySurface(
                underlying=underlying,
                strikes=[],
                expirations=[],
                volatilities=np.array([]),
                timestamp=datetime.now()
            )
    
    async def calculate_option_greeks(self, underlying_price: float, strike: float, 
                                    time_to_expiration: float, volatility: float,
                                    option_type: str, risk_free_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate option Greeks using Black-Scholes model.
        
        Args:
            underlying_price: Current price of underlying
            strike: Strike price
            time_to_expiration: Time to expiration in years
            volatility: Implied volatility
            option_type: 'call' or 'put'
            risk_free_rate: Risk-free rate (optional)
            
        Returns:
            Dictionary with all Greeks
        """
        try:
            r = risk_free_rate or self.risk_free_rate
            
            if time_to_expiration <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
            # Black-Scholes parameters
            S = underlying_price
            K = strike
            T = time_to_expiration
            sigma = volatility
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # Calculate Greeks
            greeks = {}
            
            if option_type.lower() == 'call':
                greeks['delta'] = norm.cdf(d1)
                greeks['rho'] = K * T * np.exp(-r * T) * norm.cdf(d2)
            else:  # put
                greeks['delta'] = -norm.cdf(-d1)
                greeks['rho'] = -K * T * np.exp(-r * T) * norm.cdf(-d2)
            
            # Common Greeks for both calls and puts
            greeks['gamma'] = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            greeks['vega'] = S * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for percentage point
            greeks['theta'] = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                             r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type.lower() == 'call' else norm.cdf(-d2))) / 365
            
            return greeks
            
        except Exception as e:
            self.logger.error(f"Error calculating Greeks: {e}")
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    async def analyze_options_flow(self, underlying: str, 
                                 lookback_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze options flow and unusual activity.
        
        Args:
            underlying: Underlying asset symbol
            lookback_hours: Hours to look back for flow analysis
            
        Returns:
            Options flow analysis
        """
        try:
            # Get recent options transactions
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # This would get options transaction data
            flow_data = await self._get_options_flow_data(underlying, start_time, end_time)
            
            if not flow_data:
                return {'error': 'No flow data available'}
            
            # Analyze flow patterns
            analysis = {
                'underlying': underlying,
                'period_hours': lookback_hours,
                'total_volume': sum(trade['volume'] for trade in flow_data),
                'total_premium': sum(trade['premium'] for trade in flow_data),
                'call_volume': sum(trade['volume'] for trade in flow_data if trade['option_type'] == 'call'),
                'put_volume': sum(trade['volume'] for trade in flow_data if trade['option_type'] == 'put'),
                'unusual_activity': [],
                'top_strikes': {},
                'expiration_analysis': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate put/call ratio
            if analysis['call_volume'] > 0:
                analysis['put_call_ratio'] = analysis['put_volume'] / analysis['call_volume']
            else:
                analysis['put_call_ratio'] = float('inf') if analysis['put_volume'] > 0 else 0
            
            # Identify unusual activity
            analysis['unusual_activity'] = self._identify_unusual_activity(flow_data)
            
            # Analyze by strike
            analysis['top_strikes'] = self._analyze_strike_activity(flow_data)
            
            # Analyze by expiration
            analysis['expiration_analysis'] = self._analyze_expiration_activity(flow_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing options flow: {e}")
            return {'error': str(e)}
    
    async def calculate_portfolio_greeks(self, portfolio_options: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate portfolio-level Greeks for options positions.
        
        Args:
            portfolio_options: List of options positions
            
        Returns:
            Aggregated portfolio Greeks
        """
        try:
            portfolio_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
            for position in portfolio_options:
                underlying_price = await self._get_underlying_price(position['underlying'])
                
                # Get option Greeks
                greeks = await self.calculate_option_greeks(
                    underlying_price=underlying_price,
                    strike=position['strike'],
                    time_to_expiration=self._time_to_expiration(position['expiration']),
                    volatility=position.get('implied_volatility', 0.2),
                    option_type=position['option_type']
                )
                
                # Weight by position size
                position_size = position.get('quantity', 0)
                multiplier = position.get('multiplier', 100)  # Standard option multiplier
                
                for greek, value in greeks.items():
                    portfolio_greeks[greek] += value * position_size * multiplier
            
            return portfolio_greeks
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio Greeks: {e}")
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    async def screen_options(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Screen options based on specific criteria.
        
        Args:
            criteria: Screening criteria
                - min_volume: Minimum volume
                - max_bid_ask_spread: Maximum bid-ask spread
                - min_open_interest: Minimum open interest
                - delta_range: (min_delta, max_delta)
                - theta_range: (min_theta, max_theta)
                - iv_rank_min: Minimum IV rank
                
        Returns:
            List of options matching criteria
        """
        try:
            # Get options universe (this would be all tracked options)
            all_options = await self._get_all_tracked_options()
            
            filtered_options = []
            
            for option in all_options:
                # Check volume criteria
                if criteria.get('min_volume', 0) > 0:
                    if option.get('volume', 0) < criteria['min_volume']:
                        continue
                
                # Check bid-ask spread
                if criteria.get('max_bid_ask_spread'):
                    bid = option.get('bid', 0)
                    ask = option.get('ask', 0)
                    if ask > 0 and bid > 0:
                        spread_pct = (ask - bid) / ((ask + bid) / 2)
                        if spread_pct > criteria['max_bid_ask_spread']:
                            continue
                
                # Check open interest
                if criteria.get('min_open_interest', 0) > 0:
                    if option.get('open_interest', 0) < criteria['min_open_interest']:
                        continue
                
                # Check delta range
                if criteria.get('delta_range'):
                    delta = option.get('delta', 0)
                    min_delta, max_delta = criteria['delta_range']
                    if not (min_delta <= abs(delta) <= max_delta):
                        continue
                
                # Check theta range
                if criteria.get('theta_range'):
                    theta = option.get('theta', 0)
                    min_theta, max_theta = criteria['theta_range']
                    if not (min_theta <= theta <= max_theta):
                        continue
                
                # Check IV rank
                if criteria.get('iv_rank_min'):
                    iv_rank = await self._calculate_iv_rank(option['underlying'], option.get('implied_volatility', 0))
                    if iv_rank < criteria['iv_rank_min']:
                        continue
                
                filtered_options.append(option)
            
            # Sort by specified criteria
            sort_by = criteria.get('sort_by', 'volume')
            reverse = criteria.get('sort_descending', True)
            
            filtered_options.sort(
                key=lambda x: x.get(sort_by, 0),
                reverse=reverse
            )
            
            # Limit results
            limit = criteria.get('limit', 100)
            return filtered_options[:limit]
            
        except Exception as e:
            self.logger.error(f"Error screening options: {e}")
            return []
    
    async def _analyze_options_cycle(self):
        """Run periodic options analysis."""
        try:
            # Get list of actively traded underlyings
            underlyings = await self._get_active_underlyings()
            
            for underlying in underlyings:
                # Update volatility surface
                vol_surface = await self.calculate_implied_volatility_surface(underlying)
                
                # Cache the surface
                await self._cache_volatility_surface(vol_surface)
                
                # Analyze unusual activity
                flow_analysis = await self.analyze_options_flow(underlying)
                
                # Cache flow analysis
                await self._cache_flow_analysis(underlying, flow_analysis)
                
                await asyncio.sleep(1)  # Small delay between underlyings
                
        except Exception as e:
            self.logger.error(f"Error in options analysis cycle: {e}")
    
    async def _calculate_implied_volatility(self, spot: float, strike: float, 
                                          option_price: float, time_to_exp: float, 
                                          option_type: str) -> float:
        """Calculate implied volatility using Newton-Raphson method."""
        try:
            if option_price <= 0 or time_to_exp <= 0:
                return 0.0
            
            def black_scholes_price(vol):
                d1 = (np.log(spot / strike) + (self.risk_free_rate + 0.5 * vol ** 2) * time_to_exp) / (vol * np.sqrt(time_to_exp))
                d2 = d1 - vol * np.sqrt(time_to_exp)
                
                if option_type.lower() == 'call':
                    price = spot * norm.cdf(d1) - strike * np.exp(-self.risk_free_rate * time_to_exp) * norm.cdf(d2)
                else:
                    price = strike * np.exp(-self.risk_free_rate * time_to_exp) * norm.cdf(-d2) - spot * norm.cdf(-d1)
                
                return price
            
            def objective(vol):
                return (black_scholes_price(vol) - option_price) ** 2
            
            # Use scalar minimization to find implied volatility
            result = minimize_scalar(objective, bounds=(0.01, 5.0), method='bounded')
            
            return result.x if result.success else 0.2  # Default to 20% if calculation fails
            
        except Exception as e:
            self.logger.error(f"Error calculating implied volatility: {e}")
            return 0.2  # Default volatility
    
    def _time_to_expiration(self, expiration: datetime) -> float:
        """Calculate time to expiration in years."""
        now = datetime.now()
        if expiration <= now:
            return 0.0
        
        time_diff = expiration - now
        return time_diff.total_seconds() / (365.25 * 24 * 3600)
    
    async def _create_option_contract(self, option_data: Dict[str, Any], 
                                    underlying_price: float) -> OptionContract:
        """Create OptionContract object with calculated Greeks."""
        try:
            # Calculate time to expiration
            time_to_exp = self._time_to_expiration(option_data['expiration'])
            
            # Calculate implied volatility if not provided
            iv = option_data.get('implied_volatility')
            if not iv and option_data.get('last_price', 0) > 0:
                iv = await self._calculate_implied_volatility(
                    underlying_price, option_data['strike'], option_data['last_price'],
                    time_to_exp, option_data['option_type']
                )
            
            # Calculate Greeks
            greeks = await self.calculate_option_greeks(
                underlying_price, option_data['strike'], time_to_exp,
                iv or 0.2, option_data['option_type']
            )
            
            return OptionContract(
                symbol=option_data['symbol'],
                underlying=option_data['underlying'],
                expiration=option_data['expiration'],
                strike=option_data['strike'],
                option_type=option_data['option_type'],
                bid=option_data.get('bid', 0),
                ask=option_data.get('ask', 0),
                last_price=option_data.get('last_price', 0),
                volume=option_data.get('volume', 0),
                open_interest=option_data.get('open_interest', 0),
                implied_volatility=iv or 0,
                delta=greeks['delta'],
                gamma=greeks['gamma'],
                theta=greeks['theta'],
                vega=greeks['vega'],
                rho=greeks['rho']
            )
            
        except Exception as e:
            self.logger.error(f"Error creating option contract: {e}")
            return OptionContract(
                symbol=option_data.get('symbol', ''),
                underlying=option_data.get('underlying', ''),
                expiration=option_data.get('expiration', datetime.now()),
                strike=option_data.get('strike', 0),
                option_type=option_data.get('option_type', 'call')
            )
    
    def _organize_options_chain(self, options: List[OptionContract]) -> Dict[str, Any]:
        """Organize options by expiration and strike."""
        chain = {'expirations': {}}
        
        for option in options:
            exp_str = option.expiration.strftime('%Y-%m-%d')
            
            if exp_str not in chain['expirations']:
                chain['expirations'][exp_str] = {'calls': {}, 'puts': {}}
            
            strike_key = str(option.strike)
            
            option_data = {
                'symbol': option.symbol,
                'bid': option.bid,
                'ask': option.ask,
                'last_price': option.last_price,
                'volume': option.volume,
                'open_interest': option.open_interest,
                'implied_volatility': option.implied_volatility,
                'delta': option.delta,
                'gamma': option.gamma,
                'theta': option.theta,
                'vega': option.vega,
                'rho': option.rho
            }
            
            if option.option_type.lower() == 'call':
                chain['expirations'][exp_str]['calls'][strike_key] = option_data
            else:
                chain['expirations'][exp_str]['puts'][strike_key] = option_data
        
        return chain
    
    # Helper methods - these would be implemented based on your data sources
    async def _fetch_options_data(self, underlying: str, 
                                expiration: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch options data from external sources."""
        # This would fetch from Polygon, Alpha Vantage, etc.
        return []
    
    async def _get_underlying_price(self, symbol: str) -> float:
        """Get current underlying asset price."""
        try:
            # Use existing price fetching logic
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            data = await self.db_manager.get_stock_data(symbol, start_time, end_time)
            return data[-1]['close'] if data else 0
        except:
            return 0
    
    async def _get_options_flow_data(self, underlying: str, start_time: datetime, 
                                   end_time: datetime) -> List[Dict[str, Any]]:
        """Get options flow data."""
        return []
    
    async def _get_all_tracked_options(self) -> List[Dict[str, Any]]:
        """Get all tracked options."""
        return []
    
    async def _get_active_underlyings(self) -> List[str]:
        """Get actively traded underlyings."""
        return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ']  # Example list
    
    def _interpolate_volatility(self, vol_matrix: np.ndarray, i: int, j: int) -> float:
        """Interpolate volatility for missing data points."""
        # Simple interpolation - in practice would use more sophisticated methods
        return 0.2  # Default 20% volatility
    
    def _identify_unusual_activity(self, flow_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify unusual options activity."""
        return []
    
    def _analyze_strike_activity(self, flow_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze activity by strike."""
        return {}
    
    def _analyze_expiration_activity(self, flow_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze activity by expiration."""
        return {}
    
    async def _calculate_iv_rank(self, underlying: str, current_iv: float) -> float:
        """Calculate IV rank (percentile of current IV vs historical)."""
        return 50.0  # Default 50th percentile
    
    async def _calculate_chain_summary(self, options: List[OptionContract], 
                                     underlying_price: float) -> Dict[str, Any]:
        """Calculate summary statistics for options chain."""
        return {
            'total_options': len(options),
            'total_call_volume': sum(opt.volume for opt in options if opt.option_type == 'call'),
            'total_put_volume': sum(opt.volume for opt in options if opt.option_type == 'put'),
            'avg_implied_volatility': np.mean([opt.implied_volatility for opt in options if opt.implied_volatility > 0])
        }
    
    async def _cache_volatility_surface(self, surface: VolatilitySurface):
        """Cache volatility surface data."""
        cache_key = f"vol_surface:{surface.underlying}"
        await self.cache_manager.set(cache_key, surface.__dict__, ttl=900)
    
    async def _cache_flow_analysis(self, underlying: str, analysis: Dict[str, Any]):
        """Cache flow analysis data."""
        cache_key = f"flow_analysis:{underlying}"
        await self.cache_manager.set(cache_key, analysis, ttl=300)
    
    def is_healthy(self) -> bool:
        """Check if the options analyzer is healthy."""
        return self.running