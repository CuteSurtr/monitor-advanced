#!/usr/bin/env python3
"""
Flask REST API for Stock Analytics
Deployable to Azure App Service
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from datetime import datetime, timedelta
import json

# Add src to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.config import Config
from src.utils.logger import setup_logging
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.portfolio.portfolio_manager import PortfolioManager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enable CORS for Azure deployment
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Global variables for components
config = None
db_manager = None
cache_manager = None
analytics_engine = None
portfolio_manager = None
logger = None

@app.before_first_request
def initialize_components():
    """Initialize system components on first request."""
    global config, db_manager, cache_manager, analytics_engine, portfolio_manager, logger
    
    try:
        # Initialize configuration
        config = Config()
        logger = setup_logging(config)
        
        # Initialize database and cache
        db_manager = DatabaseManager(config)
        cache_manager = CacheManager(config)
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine(db_manager, cache_manager)
        
        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(db_manager, cache_manager, analytics_engine)
        
        logger.info("Flask API components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Flask API components: {e}")
        raise

@app.route('/health', methods=['GET'])
@limiter.limit("100 per minute")
def health_check():
    """Health check endpoint for Azure App Service."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Stock Analytics API',
        'version': '1.0.0'
    })

@app.route('/api/v1/analytics/stock/<symbol>', methods=['GET'])
@limiter.limit("100 per minute")
def get_stock_analytics(symbol):
    """Get comprehensive stock analytics for a given symbol."""
    try:
        # Get query parameters
        period = request.args.get('period', '1d')
        indicators = request.args.get('indicators', 'all')
        
        # Get stock data from cache or database
        stock_data = cache_manager.get(f"stock_data_{symbol}")
        if not stock_data:
            # Fetch from database if not in cache
            stock_data = db_manager.get_stock_data(symbol, period)
            if stock_data:
                cache_manager.set(f"stock_data_{symbol}", stock_data, ttl=300)
        
        if not stock_data:
            return jsonify({'error': 'Stock data not found'}), 404
        
        # Calculate technical indicators
        technical_analysis = analytics_engine.calculate_technical_indicators(stock_data)
        
        # Calculate sentiment analysis
        sentiment_score = analytics_engine.analyze_sentiment(symbol)
        
        # Calculate correlation with market indices
        correlation = analytics_engine.calculate_correlation(symbol, 'SPY')
        
        return jsonify({
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'period': period,
            'technical_analysis': technical_analysis,
            'sentiment_score': sentiment_score,
            'market_correlation': correlation,
            'data_points': len(stock_data) if stock_data else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting stock analytics for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/portfolio/<portfolio_id>', methods=['GET'])
@limiter.limit("50 per minute")
def get_portfolio_analytics(portfolio_id):
    """Get portfolio analytics and performance metrics."""
    try:
        # Get portfolio data
        portfolio_data = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio_data:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Calculate portfolio metrics
        portfolio_metrics = portfolio_manager.calculate_portfolio_metrics(portfolio_id)
        
        # Get risk analysis
        risk_analysis = portfolio_manager.analyze_risk(portfolio_id)
        
        # Get performance comparison
        performance_comparison = portfolio_manager.compare_performance(portfolio_id)
        
        return jsonify({
            'portfolio_id': portfolio_id,
            'timestamp': datetime.utcnow().isoformat(),
            'portfolio_data': portfolio_data,
            'metrics': portfolio_metrics,
            'risk_analysis': risk_analysis,
            'performance_comparison': performance_comparison
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio analytics for {portfolio_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/market/overview', methods=['GET'])
@limiter.limit("100 per minute")
def get_market_overview():
    """Get overall market overview and sentiment."""
    try:
        # Get market indices data
        market_indices = cache_manager.get('market_indices')
        if not market_indices:
            market_indices = db_manager.get_market_indices()
            if market_indices:
                cache_manager.set('market_indices', market_indices, ttl=600)
        
        # Get market sentiment
        market_sentiment = analytics_engine.get_market_sentiment()
        
        # Get sector performance
        sector_performance = analytics_engine.get_sector_performance()
        
        # Get volatility index
        volatility_index = analytics_engine.get_volatility_index()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'market_indices': market_indices,
            'market_sentiment': market_sentiment,
            'sector_performance': sector_performance,
            'volatility_index': volatility_index
        })
        
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/predictions/<symbol>', methods=['GET'])
@limiter.limit("50 per minute")
def get_stock_predictions(symbol):
    """Get ML-based stock price predictions."""
    try:
        # Get prediction horizon
        horizon = request.args.get('horizon', '5')  # days
        
        # Get predictions from analytics engine
        predictions = analytics_engine.get_price_predictions(symbol, int(horizon))
        
        if not predictions:
            return jsonify({'error': 'Predictions not available'}), 404
        
        return jsonify({
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'prediction_horizon': horizon,
            'predictions': predictions,
            'confidence_score': analytics_engine.get_prediction_confidence(symbol)
        })
        
    except Exception as e:
        logger.error(f"Error getting predictions for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/anomalies', methods=['GET'])
@limiter.limit("50 per minute")
def get_market_anomalies():
    """Get detected market anomalies and unusual patterns."""
    try:
        # Get anomaly detection results
        anomalies = analytics_engine.detect_anomalies()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies
        })
        
    except Exception as e:
        logger.error(f"Error getting market anomalies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/analytics/correlation', methods=['POST'])
@limiter.limit("30 per minute")
def calculate_correlation():
    """Calculate correlation between multiple assets."""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        period = data.get('period', '30d')
        
        if len(symbols) < 2:
            return jsonify({'error': 'At least 2 symbols required'}), 400
        
        # Calculate correlation matrix
        correlation_matrix = analytics_engine.calculate_correlation_matrix(symbols, period)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'symbols': symbols,
            'period': period,
            'correlation_matrix': correlation_matrix
        })
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    # For Azure App Service deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

