"""
Dashboard API Module

Provides FastAPI routes for the web dashboard, including data endpoints
for charts, portfolio overview, market statistics, and real-time updates.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd

from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.portfolio.portfolio_manager import PortfolioManager
from src.alerts.alert_manager import AlertManager

router = APIRouter()


# Pydantic models for API responses
class StockDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str


class TechnicalIndicator(BaseModel):
    name: str
    values: List[float]
    timestamps: List[datetime]
    signals: Optional[Dict[str, str]] = None


class PortfolioSummary(BaseModel):
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    top_gainers: List[Dict[str, Any]]
    top_losers: List[Dict[str, Any]]


class MarketOverview(BaseModel):
    total_symbols: int
    gainers: int
    losers: int
    unchanged: int
    top_movers: List[Dict[str, Any]]
    sector_performance: Dict[str, float]


class AlertSummary(BaseModel):
    total_alerts: int
    active_alerts: int
    triggered_today: int
    recent_alerts: List[Dict[str, Any]]


# Global dashboard manager instance
dashboard_manager = None

def set_dashboard_manager(manager):
    """Set the dashboard manager instance."""
    global dashboard_manager
    dashboard_manager = manager

# Dependency injection
async def get_dashboard_manager():
    """Get dashboard manager from the main application."""
    if dashboard_manager is None:
        raise HTTPException(status_code=500, detail="Dashboard manager not initialized")
    return dashboard_manager


@router.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve the main dashboard HTML page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Market Monitor Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            .dashboard-card {
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            }
            .dashboard-card:hover {
                transform: translateY(-2px);
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
            .chart-container {
                height: 400px;
                margin: 20px 0;
            }
            .navbar-brand {
                font-weight: bold;
                font-size: 1.5rem;
            }
            .sidebar {
                background: #f8f9fa;
                min-height: 100vh;
                padding: 20px;
            }
            .main-content {
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-chart-line me-2"></i>
                    Stock Market Monitor
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text">
                        <i class="fas fa-clock me-1"></i>
                        <span id="current-time"></span>
                    </span>
                </div>
            </div>
        </nav>

        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 sidebar">
                    <h5 class="mb-3">Navigation</h5>
                    <div class="list-group">
                        <a href="#" class="list-group-item list-group-item-action active" data-section="overview">
                            <i class="fas fa-tachometer-alt me-2"></i>Overview
                        </a>
                        <a href="#" class="list-group-item list-group-item-action" data-section="portfolio">
                            <i class="fas fa-briefcase me-2"></i>Portfolio
                        </a>
                        <a href="#" class="list-group-item list-group-item-action" data-section="analytics">
                            <i class="fas fa-chart-bar me-2"></i>Analytics
                        </a>
                        <a href="#" class="list-group-item list-group-item-action" data-section="alerts">
                            <i class="fas fa-bell me-2"></i>Alerts
                        </a>
                        <a href="#" class="list-group-item list-group-item-action" data-section="market">
                            <i class="fas fa-globe me-2"></i>Market
                        </a>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="col-md-10 main-content">
                    <!-- Overview Section -->
                    <div id="overview-section" class="dashboard-section">
                        <h2 class="mb-4">Market Overview</h2>
                        
                        <!-- Key Metrics -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <h4 id="total-symbols">0</h4>
                                    <p class="mb-0">Total Symbols</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <h4 id="gainers">0</h4>
                                    <p class="mb-0">Gainers</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <h4 id="losers">0</h4>
                                    <p class="mb-0">Losers</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <h4 id="active-alerts">0</h4>
                                    <p class="mb-0">Active Alerts</p>
                                </div>
                            </div>
                        </div>

                        <!-- Charts Row -->
                        <div class="row">
                            <div class="col-md-8">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Market Performance</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="market-chart" class="chart-container"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Top Movers</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="top-movers"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Portfolio Section -->
                    <div id="portfolio-section" class="dashboard-section" style="display: none;">
                        <h2 class="mb-4">Portfolio Overview</h2>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Portfolio Summary</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="portfolio-summary"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Portfolio Allocation</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="portfolio-pie-chart" class="chart-container"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-4">
                            <div class="col-12">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Portfolio Performance</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="portfolio-performance-chart" class="chart-container"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Analytics Section -->
                    <div id="analytics-section" class="dashboard-section" style="display: none;">
                        <h2 class="mb-4">Analytics</h2>
                        
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <select id="symbol-select" class="form-select">
                                    <option value="">Select Symbol</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <select id="indicator-select" class="form-select">
                                    <option value="rsi">RSI</option>
                                    <option value="macd">MACD</option>
                                    <option value="bollinger">Bollinger Bands</option>
                                    <option value="sma">Simple Moving Average</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <button id="analyze-btn" class="btn btn-primary">Analyze</button>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Technical Analysis</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="technical-chart" class="chart-container"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Alerts Section -->
                    <div id="alerts-section" class="dashboard-section" style="display: none;">
                        <h2 class="mb-4">Alerts</h2>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Recent Alerts</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="recent-alerts"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Alert Statistics</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="alert-stats"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Market Section -->
                    <div id="market-section" class="dashboard-section" style="display: none;">
                        <h2 class="mb-4">Market Data</h2>
                        
                        <div class="row">
                            <div class="col-12">
                                <div class="card dashboard-card">
                                    <div class="card-header">
                                        <h5>Market Heatmap</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="market-heatmap" class="chart-container"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Dashboard JavaScript functionality
            let currentSection = 'overview';
            
            // Navigation
            document.querySelectorAll('[data-section]').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const section = e.target.closest('a').dataset.section;
                    showSection(section);
                });
            });

            function showSection(section) {
                // Hide all sections
                document.querySelectorAll('.dashboard-section').forEach(s => {
                    s.style.display = 'none';
                });
                
                // Show selected section
                document.getElementById(section + '-section').style.display = 'block';
                
                // Update navigation
                document.querySelectorAll('[data-section]').forEach(link => {
                    link.classList.remove('active');
                });
                document.querySelector(`[data-section="${section}"]`).classList.add('active');
                
                currentSection = section;
                loadSectionData(section);
            }

            function loadSectionData(section) {
                switch(section) {
                    case 'overview':
                        loadOverviewData();
                        break;
                    case 'portfolio':
                        loadPortfolioData();
                        break;
                    case 'analytics':
                        loadAnalyticsData();
                        break;
                    case 'alerts':
                        loadAlertsData();
                        break;
                    case 'market':
                        loadMarketData();
                        break;
                }
            }

            async function loadOverviewData() {
                try {
                    const response = await fetch('/api/dashboard/overview');
                    const data = await response.json();
                    
                    document.getElementById('total-symbols').textContent = data.total_symbols;
                    document.getElementById('gainers').textContent = data.gainers;
                    document.getElementById('losers').textContent = data.losers;
                    document.getElementById('active-alerts').textContent = data.active_alerts;
                    
                    // Update charts
                    updateMarketChart(data.market_data);
                    updateTopMovers(data.top_movers);
                } catch (error) {
                    console.error('Error loading overview data:', error);
                }
            }

            async function loadPortfolioData() {
                try {
                    const response = await fetch('/api/dashboard/portfolio');
                    const data = await response.json();
                    
                    updatePortfolioSummary(data.summary);
                    updatePortfolioCharts(data);
                } catch (error) {
                    console.error('Error loading portfolio data:', error);
                }
            }

            async function loadAnalyticsData() {
                try {
                    const response = await fetch('/api/dashboard/symbols');
                    const symbols = await response.json();
                    
                    const select = document.getElementById('symbol-select');
                    select.innerHTML = '<option value="">Select Symbol</option>';
                    symbols.forEach(symbol => {
                        const option = document.createElement('option');
                        option.value = symbol;
                        option.textContent = symbol;
                        select.appendChild(option);
                    });
                } catch (error) {
                    console.error('Error loading symbols:', error);
                }
            }

            async function loadAlertsData() {
                try {
                    const response = await fetch('/api/dashboard/alerts');
                    const data = await response.json();
                    
                    updateAlertsList(data.recent_alerts);
                    updateAlertStats(data.stats);
                } catch (error) {
                    console.error('Error loading alerts data:', error);
                }
            }

            async function loadMarketData() {
                try {
                    const response = await fetch('/api/dashboard/market-heatmap');
                    const data = await response.json();
                    
                    updateMarketHeatmap(data);
                } catch (error) {
                    console.error('Error loading market data:', error);
                }
            }

            function updateMarketChart(data) {
                const trace = {
                    x: data.timestamps,
                    y: data.prices,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Market Index',
                    line: { color: '#667eea' }
                };

                const layout = {
                    title: 'Market Performance',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Price' },
                    height: 350
                };

                Plotly.newPlot('market-chart', [trace], layout);
            }

            function updateTopMovers(movers) {
                const container = document.getElementById('top-movers');
                container.innerHTML = '';
                
                movers.forEach(mover => {
                    const div = document.createElement('div');
                    div.className = 'd-flex justify-content-between align-items-center mb-2';
                    div.innerHTML = `
                        <span>${mover.symbol}</span>
                        <span class="${mover.change_percent >= 0 ? 'text-success' : 'text-danger'}">
                            ${mover.change_percent >= 0 ? '+' : ''}${mover.change_percent.toFixed(2)}%
                        </span>
                    `;
                    container.appendChild(div);
                });
            }

            function updatePortfolioSummary(summary) {
                const container = document.getElementById('portfolio-summary');
                container.innerHTML = `
                    <div class="row">
                        <div class="col-6">
                            <h4>$${summary.total_value.toLocaleString()}</h4>
                            <p>Total Value</p>
                        </div>
                        <div class="col-6">
                            <h4 class="${summary.total_pnl >= 0 ? 'text-success' : 'text-danger'}">
                                ${summary.total_pnl >= 0 ? '+' : ''}$${summary.total_pnl.toLocaleString()}
                            </h4>
                            <p>Total P&L</p>
                        </div>
                    </div>
                `;
            }

            function updatePortfolioCharts(data) {
                // Portfolio allocation pie chart
                const pieData = [{
                    values: data.allocations.values,
                    labels: data.allocations.labels,
                    type: 'pie',
                    hole: 0.4
                }];

                const pieLayout = {
                    title: 'Portfolio Allocation',
                    height: 350
                };

                Plotly.newPlot('portfolio-pie-chart', pieData, pieLayout);

                // Portfolio performance chart
                const perfTrace = {
                    x: data.performance.timestamps,
                    y: data.performance.values,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Portfolio Value',
                    line: { color: '#28a745' }
                };

                const perfLayout = {
                    title: 'Portfolio Performance',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Value ($)' },
                    height: 350
                };

                Plotly.newPlot('portfolio-performance-chart', [perfTrace], perfLayout);
            }

            function updateAlertsList(alerts) {
                const container = document.getElementById('recent-alerts');
                container.innerHTML = '';
                
                alerts.forEach(alert => {
                    const div = document.createElement('div');
                    div.className = 'alert alert-warning mb-2';
                    div.innerHTML = `
                        <strong>${alert.symbol}</strong> - ${alert.message}
                        <small class="text-muted d-block">${alert.timestamp}</small>
                    `;
                    container.appendChild(div);
                });
            }

            function updateAlertStats(stats) {
                const container = document.getElementById('alert-stats');
                container.innerHTML = `
                    <div class="mb-3">
                        <h6>Total Alerts</h6>
                        <h4>${stats.total_alerts}</h4>
                    </div>
                    <div class="mb-3">
                        <h6>Active Alerts</h6>
                        <h4>${stats.active_alerts}</h4>
                    </div>
                    <div class="mb-3">
                        <h6>Triggered Today</h6>
                        <h4>${stats.triggered_today}</h4>
                    </div>
                `;
            }

            function updateMarketHeatmap(data) {
                const heatmapData = [{
                    z: data.values,
                    x: data.symbols,
                    y: data.metrics,
                    type: 'heatmap',
                    colorscale: 'RdYlGn'
                }];

                const layout = {
                    title: 'Market Heatmap',
                    xaxis: { title: 'Symbols' },
                    yaxis: { title: 'Metrics' },
                    height: 400
                };

                Plotly.newPlot('market-heatmap', heatmapData, layout);
            }

            // Update current time
            function updateTime() {
                const now = new Date();
                document.getElementById('current-time').textContent = now.toLocaleTimeString();
            }

            setInterval(updateTime, 1000);
            updateTime();

            // Auto-refresh data every 30 seconds
            setInterval(() => {
                loadSectionData(currentSection);
            }, 30000);

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', () => {
                loadOverviewData();
            });

            // Analytics button handler
            document.getElementById('analyze-btn').addEventListener('click', async () => {
                const symbol = document.getElementById('symbol-select').value;
                const indicator = document.getElementById('indicator-select').value;
                
                if (!symbol) {
                    alert('Please select a symbol');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/dashboard/analytics/${symbol}?indicator=${indicator}`);
                    const data = await response.json();
                    
                    // Update technical analysis chart
                    const trace = {
                        x: data.timestamps,
                        y: data.values,
                        type: 'scatter',
                        mode: 'lines',
                        name: indicator.toUpperCase(),
                        line: { color: '#ff6b6b' }
                    };

                    const layout = {
                        title: `${symbol} - ${indicator.toUpperCase()}`,
                        xaxis: { title: 'Time' },
                        yaxis: { title: 'Value' },
                        height: 350
                    };

                    Plotly.newPlot('technical-chart', [trace], layout);
                } catch (error) {
                    console.error('Error analyzing symbol:', error);
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/overview")
async def get_market_overview():
    """Get market overview data for the dashboard."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_market_overview()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market overview: {str(e)}")


@router.get("/portfolio")
async def get_portfolio_data():
    """Get portfolio data for the dashboard."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_portfolio_data()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio data: {str(e)}")


@router.get("/symbols")
async def get_available_symbols():
    """Get list of available stock symbols."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_available_symbols()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching symbols: {str(e)}")


@router.get("/analytics/{symbol}")
async def get_technical_analysis(
    symbol: str,
    indicator: str = Query(..., description="Technical indicator to analyze"),
    period: int = Query(30, description="Analysis period in days")
):
    """Get technical analysis for a specific symbol."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_technical_analysis(symbol, indicator, period)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing {symbol}: {str(e)}")


@router.get("/alerts")
async def get_alerts_data():
    """Get alerts data for the dashboard."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_alerts_data()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts data: {str(e)}")


@router.get("/market-heatmap")
async def get_market_heatmap():
    """Get market heatmap data."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_market_heatmap()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market heatmap: {str(e)}")


@router.get("/real-time/{symbol}")
async def get_real_time_data(symbol: str):
    """Get real-time data for a specific symbol."""
    try:
        manager = await get_dashboard_manager()
        return await manager.get_real_time_data(symbol)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching real-time data: {str(e)}")


def create_dashboard_app():
    """Create and configure the dashboard FastAPI application."""
    app = FastAPI(
        title="Stock Market Monitor Dashboard",
        description="Web dashboard for the 24/7 Global Stock Market Monitoring System",
        version="1.0.0"
    )
    
    app.include_router(router, prefix="/api/dashboard")
    
    return app 