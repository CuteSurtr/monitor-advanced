"""
Risk Analytics API endpoints for real-time risk metrics access.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from src.analytics.risk_analytics import RiskAnalytics, RiskMetrics
from src.utils.logger import get_logger


# Pydantic models for API responses
class VaRResponse(BaseModel):
    """VaR calculation response."""

    var_95_historical: float
    var_95_parametric: float
    var_95_monte_carlo: float
    var_99_historical: float
    var_99_parametric: float
    var_99_monte_carlo: float
    cvar_95_historical: float
    cvar_95_parametric: float
    cvar_95_monte_carlo: float
    cvar_99_historical: float
    cvar_99_parametric: float
    cvar_99_monte_carlo: float
    confidence_levels: List[float]
    methods: List[str]
    timestamp: datetime


class VolatilityResponse(BaseModel):
    """Volatility metrics response."""

    volatility_historical: float
    volatility_ewma: float
    volatility_garch: float
    daily_volatility: float
    methods: List[str]
    timestamp: datetime


class RiskMetricsResponse(BaseModel):
    """Comprehensive risk metrics response."""

    portfolio_id: int
    var_metrics: VaRResponse
    volatility_metrics: VolatilityResponse
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    beta: float
    component_var: Dict[str, float]
    correlation_matrix: Dict[str, Dict[str, float]]
    risk_alerts: List[Dict[str, Any]]
    calculation_timestamp: datetime


class AssetRiskResponse(BaseModel):
    """Single asset risk metrics response."""

    symbol: str
    var_95: float
    cvar_95: float
    var_99: float
    cvar_99: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    mean_return: float
    std_return: float
    skewness: float
    kurtosis: float
    observations: int
    timestamp: datetime


class StressTestResponse(BaseModel):
    """Stress test results response."""

    portfolio_id: int
    original_value: float
    stressed_value: float
    total_impact: float
    impact_percentage: float
    detailed_impacts: Dict[str, Dict[str, Any]]
    shock_scenarios: Dict[str, float]
    timestamp: datetime


class RiskDashboardResponse(BaseModel):
    """Risk dashboard data response."""

    portfolio_id: int
    risk_metrics: Dict[str, Any]
    correlation_matrix: Dict[str, Dict[str, float]]
    positions_count: int
    total_value: float
    top_positions: List[Dict[str, Any]]
    risk_alerts: List[Dict[str, Any]]
    timestamp: datetime


# Create router
router = APIRouter(prefix="/api/risk", tags=["Risk Analytics"])
logger = get_logger(__name__)


# Dependency to get risk analytics instance
def get_risk_analytics() -> RiskAnalytics:
    """Get risk analytics instance."""
    # This would be injected with proper database and cache managers
    # For now, return a placeholder
    from src.utils.database import get_database_manager
    from src.utils.cache import CacheManager
    from src.utils.config import get_config

    config = get_config()
    db_manager = get_database_manager()
    cache_manager = CacheManager(config)

    return RiskAnalytics(db_manager, cache_manager, config)


@router.get("/portfolio/{portfolio_id}/var", response_model=VaRResponse)
async def get_portfolio_var(
    portfolio_id: int,
    confidence_levels: List[float] = Query(default=[0.95, 0.99]),
    lookback_days: int = Query(default=252),
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Calculate Value at Risk (VaR) and Conditional VaR for a portfolio.

    - **portfolio_id**: Portfolio identifier
    - **confidence_levels**: List of confidence levels (default: [0.95, 0.99])
    - **lookback_days**: Historical data lookback period (default: 252)
    """
    try:
        risk_metrics = await risk_analytics.calculate_portfolio_risk(
            portfolio_id, lookback_days, confidence_levels
        )

        return VaRResponse(
            var_95_historical=risk_metrics.var_95_historical,
            var_95_parametric=risk_metrics.var_95_parametric,
            var_95_monte_carlo=risk_metrics.var_95_monte_carlo,
            var_99_historical=risk_metrics.var_99_historical,
            var_99_parametric=risk_metrics.var_99_parametric,
            var_99_monte_carlo=risk_metrics.var_99_monte_carlo,
            cvar_95_historical=risk_metrics.cvar_95_historical,
            cvar_95_parametric=risk_metrics.cvar_95_parametric,
            cvar_95_monte_carlo=risk_metrics.cvar_95_monte_carlo,
            cvar_99_historical=risk_metrics.cvar_99_historical,
            cvar_99_parametric=risk_metrics.cvar_99_parametric,
            cvar_99_monte_carlo=risk_metrics.cvar_99_monte_carlo,
            confidence_levels=confidence_levels,
            methods=["historical", "parametric", "monte_carlo"],
            timestamp=risk_metrics.timestamp,
        )

    except Exception as e:
        logger.error(f"Error calculating portfolio VaR: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating VaR: {str(e)}")


@router.get("/portfolio/{portfolio_id}/volatility", response_model=VolatilityResponse)
async def get_portfolio_volatility(
    portfolio_id: int,
    lookback_days: int = Query(default=252),
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Calculate volatility metrics for a portfolio using different methods.

    - **portfolio_id**: Portfolio identifier
    - **lookback_days**: Historical data lookback period (default: 252)
    """
    try:
        risk_metrics = await risk_analytics.calculate_portfolio_risk(
            portfolio_id, lookback_days
        )

        return VolatilityResponse(
            volatility_historical=risk_metrics.volatility,
            volatility_ewma=risk_metrics.volatility_ewma,
            volatility_garch=risk_metrics.volatility_garch,
            daily_volatility=risk_metrics.volatility / (252**0.5),  # Convert to daily
            methods=["historical", "ewma", "garch"],
            timestamp=risk_metrics.timestamp,
        )

    except Exception as e:
        logger.error(f"Error calculating portfolio volatility: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating volatility: {str(e)}"
        )


@router.get(
    "/portfolio/{portfolio_id}/comprehensive", response_model=RiskMetricsResponse
)
async def get_comprehensive_risk_metrics(
    portfolio_id: int,
    lookback_days: int = Query(default=252),
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Get comprehensive risk metrics for a portfolio.

    - **portfolio_id**: Portfolio identifier
    - **lookback_days**: Historical data lookback period (default: 252)
    """
    try:
        risk_metrics = await risk_analytics.calculate_portfolio_risk(
            portfolio_id, lookback_days
        )
        risk_alerts = await risk_analytics._generate_risk_alerts(risk_metrics)

        var_response = VaRResponse(
            var_95_historical=risk_metrics.var_95_historical,
            var_95_parametric=risk_metrics.var_95_parametric,
            var_95_monte_carlo=risk_metrics.var_95_monte_carlo,
            var_99_historical=risk_metrics.var_99_historical,
            var_99_parametric=risk_metrics.var_99_parametric,
            var_99_monte_carlo=risk_metrics.var_99_monte_carlo,
            cvar_95_historical=risk_metrics.cvar_95_historical,
            cvar_95_parametric=risk_metrics.cvar_95_parametric,
            cvar_95_monte_carlo=risk_metrics.cvar_95_monte_carlo,
            cvar_99_historical=risk_metrics.cvar_99_historical,
            cvar_99_parametric=risk_metrics.cvar_99_parametric,
            cvar_99_monte_carlo=risk_metrics.cvar_99_monte_carlo,
            confidence_levels=[0.95, 0.99],
            methods=["historical", "parametric", "monte_carlo"],
            timestamp=risk_metrics.timestamp,
        )

        vol_response = VolatilityResponse(
            volatility_historical=risk_metrics.volatility,
            volatility_ewma=risk_metrics.volatility_ewma,
            volatility_garch=risk_metrics.volatility_garch,
            daily_volatility=risk_metrics.volatility / (252**0.5),
            methods=["historical", "ewma", "garch"],
            timestamp=risk_metrics.timestamp,
        )

        return RiskMetricsResponse(
            portfolio_id=portfolio_id,
            var_metrics=var_response,
            volatility_metrics=vol_response,
            sharpe_ratio=risk_metrics.sharpe_ratio,
            max_drawdown=risk_metrics.max_drawdown,
            current_drawdown=risk_metrics.current_drawdown,
            beta=risk_metrics.beta,
            component_var=risk_metrics.component_var,
            correlation_matrix=risk_metrics.correlation_matrix,
            risk_alerts=risk_alerts,
            calculation_timestamp=risk_metrics.timestamp,
        )

    except Exception as e:
        logger.error(f"Error calculating comprehensive risk metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating risk metrics: {str(e)}"
        )


@router.get("/asset/{symbol}/risk", response_model=AssetRiskResponse)
async def get_asset_risk_metrics(
    symbol: str,
    lookback_days: int = Query(default=252),
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Calculate risk metrics for a single asset.

    - **symbol**: Asset symbol (supports stocks, forex, crypto, commodities)
    - **lookback_days**: Historical data lookback period (default: 252)
    """
    try:
        risk_data = await risk_analytics.calculate_asset_risk(symbol, lookback_days)

        if not risk_data:
            raise HTTPException(
                status_code=404, detail=f"No data found for asset: {symbol}"
            )

        return AssetRiskResponse(
            symbol=symbol,
            var_95=risk_data.get("var_95_historical", 0),
            cvar_95=risk_data.get("cvar_95_historical", 0),
            var_99=risk_data.get("var_99_historical", 0),
            cvar_99=risk_data.get("cvar_99_historical", 0),
            volatility=risk_data.get("volatility_historical", 0),
            sharpe_ratio=risk_data.get("sharpe_ratio", 0),
            max_drawdown=risk_data.get("max_drawdown", 0),
            mean_return=risk_data.get("mean_return", 0),
            std_return=risk_data.get("std_return", 0),
            skewness=risk_data.get("skewness", 0),
            kurtosis=risk_data.get("kurtosis", 0),
            observations=risk_data.get("observations", 0),
            timestamp=datetime.fromisoformat(
                risk_data.get("timestamp", datetime.now().isoformat())
            ),
        )

    except Exception as e:
        logger.error(f"Error calculating asset risk for {symbol}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating asset risk: {str(e)}"
        )


@router.post("/portfolio/{portfolio_id}/stress-test", response_model=StressTestResponse)
async def run_stress_test(
    portfolio_id: int,
    shock_scenarios: Dict[str, float],
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Run stress test on a portfolio with specified shock scenarios.

    - **portfolio_id**: Portfolio identifier
    - **shock_scenarios**: Dictionary of asset -> shock percentage (e.g., {"AAPL": -0.20})
    """
    try:
        stress_results = await risk_analytics.calculate_stress_test(
            portfolio_id, shock_scenarios
        )

        if not stress_results:
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio {portfolio_id} not found or no positions",
            )

        return StressTestResponse(
            portfolio_id=portfolio_id,
            original_value=stress_results["original_portfolio_value"],
            stressed_value=stress_results["stressed_portfolio_value"],
            total_impact=stress_results["total_impact"],
            impact_percentage=stress_results["impact_percentage"],
            detailed_impacts=stress_results["detailed_impacts"],
            shock_scenarios=stress_results["shock_scenarios"],
            timestamp=datetime.fromisoformat(stress_results["timestamp"]),
        )

    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error running stress test: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/dashboard", response_model=RiskDashboardResponse)
async def get_risk_dashboard(
    portfolio_id: int, risk_analytics: RiskAnalytics = Depends(get_risk_analytics)
):
    """
    Get comprehensive risk dashboard data for a portfolio.

    - **portfolio_id**: Portfolio identifier
    """
    try:
        dashboard_data = await risk_analytics.get_risk_dashboard_data(portfolio_id)

        if not dashboard_data:
            raise HTTPException(
                status_code=404, detail=f"Portfolio {portfolio_id} not found"
            )

        return RiskDashboardResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"Error getting risk dashboard: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting risk dashboard: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/correlation")
async def get_correlation_matrix(
    portfolio_id: int,
    lookback_days: int = Query(default=252),
    risk_analytics: RiskAnalytics = Depends(get_risk_analytics),
):
    """
    Get correlation matrix for portfolio assets.

    - **portfolio_id**: Portfolio identifier
    - **lookback_days**: Historical data lookback period (default: 252)
    """
    try:
        correlation_matrix = (
            await risk_analytics.calculate_portfolio_correlation_matrix(
                portfolio_id, lookback_days
            )
        )

        return {
            "portfolio_id": portfolio_id,
            "correlation_matrix": (
                correlation_matrix.to_dict() if not correlation_matrix.empty else {}
            ),
            "lookback_days": lookback_days,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating correlation matrix: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for risk analytics API."""
    return {
        "status": "healthy",
        "service": "risk_analytics_api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }
