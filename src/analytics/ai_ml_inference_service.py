"""
Real-Time AI/ML Inference Service
Continuous model inference and signal generation for trading dashboard
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from dataclasses import asdict

from src.analytics.ai_ml_engine import AIMLEngine, initialize_ai_ml_engine
from src.analytics.influxdb_sync import influx_sync
from src.utils.database import DatabaseManager
from src.utils.logger import get_logger
from src.utils.config import get_config


class AIMLInferenceService:
    """Real-time AI/ML inference service for continuous predictions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = get_config()
        self.logger = get_logger(__name__)

        # Service state
        self.running = False
        self.ai_ml_engine: Optional[AIMLEngine] = None

        # Monitored symbols
        self.symbols = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "AMZN",
            "TSLA",
            "NVDA",
            "META",
            "SPY",
            "QQQ",
            "IWM",
            "GLD",
            "TLT",
            "VIX",
        ]

        # Inference intervals (in seconds)
        self.inference_intervals = {
            "predictions": 300,  # 5 minutes
            "signals": 180,  # 3 minutes
            "sentiment": 600,  # 10 minutes
            "model_training": 3600,  # 1 hour
            "feature_importance": 1800,  # 30 minutes
        }

        # Performance tracking
        self.performance_metrics = {}
        self.last_inference_times = {}

    async def initialize(self):
        """Initialize the inference service."""
        try:
            # Initialize AI/ML engine
            self.ai_ml_engine = await initialize_ai_ml_engine(self.db_manager)

            # Initialize InfluxDB sync
            await influx_sync.initialize()

            # Load or train initial models
            await self._initialize_models()

            self.logger.info("AI/ML Inference Service initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI/ML Inference Service: {e}")
            raise

    async def _initialize_models(self):
        """Initialize or load models for all symbols."""
        try:
            for symbol in self.symbols[:3]:  # Start with first 3 symbols
                self.logger.info(f"  Training initial models for {symbol}")
                await self.ai_ml_engine.train_ensemble_models(symbol)
                await asyncio.sleep(1)  # Prevent overwhelming the system

            self.logger.info("Initial models trained")

        except Exception as e:
            self.logger.error(f"Model initialization failed: {e}")

    async def start_service(self):
        """Start the real-time inference service."""
        self.running = True
        self.logger.info(" Starting AI/ML Inference Service")

        # Start concurrent inference tasks
        tasks = [
            asyncio.create_task(self._prediction_loop()),
            asyncio.create_task(self._signal_generation_loop()),
            asyncio.create_task(self._sentiment_analysis_loop()),
            asyncio.create_task(self._model_training_loop()),
            asyncio.create_task(self._feature_importance_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Inference service error: {e}")
        finally:
            self.running = False

    def stop_service(self):
        """Stop the inference service."""
        self.running = False
        self.logger.info("AI/ML Inference Service stopped")

    # =====================================================
    # INFERENCE LOOPS
    # =====================================================

    async def _prediction_loop(self):
        """Continuous price prediction loop."""
        while self.running:
            try:
                start_time = datetime.now()

                # Generate predictions for all symbols
                prediction_tasks = []
                for symbol in self.symbols:
                    task = asyncio.create_task(
                        self._generate_symbol_predictions(symbol)
                    )
                    prediction_tasks.append(task)

                # Wait for all predictions to complete
                await asyncio.gather(*prediction_tasks, return_exceptions=True)

                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_performance_metric("predictions", execution_time)

                self.logger.info(
                    f" Prediction cycle completed in {execution_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.inference_intervals["predictions"])

            except Exception as e:
                self.logger.error(f"Prediction loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _generate_symbol_predictions(self, symbol: str):
        """Generate predictions for a single symbol."""
        try:
            predictions = await self.ai_ml_engine.generate_predictions(symbol)

            if predictions:
                # Sync predictions to InfluxDB
                for pred in predictions:
                    await influx_sync.sync_ml_prediction(
                        symbol=pred.symbol,
                        model_name=pred.model_name,
                        prediction_type=pred.prediction_type,
                        predicted_value=pred.predicted_value,
                        confidence=pred.confidence,
                        model_accuracy=pred.model_accuracy,
                    )

                self.logger.debug(
                    f"® Generated {len(predictions)} predictions for {symbol}"
                )

        except Exception as e:
            self.logger.error(f"Failed to generate predictions for {symbol}: {e}")

    async def _signal_generation_loop(self):
        """Continuous trading signal generation loop."""
        while self.running:
            try:
                start_time = datetime.now()

                # Generate signals for all symbols
                signal_tasks = []
                for symbol in self.symbols:
                    task = asyncio.create_task(self._generate_symbol_signal(symbol))
                    signal_tasks.append(task)

                # Wait for all signals to complete
                signals = await asyncio.gather(*signal_tasks, return_exceptions=True)

                # Count successful signals
                successful_signals = [
                    s for s in signals if not isinstance(s, Exception) and s is not None
                ]

                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_performance_metric("signals", execution_time)

                self.logger.info(
                    f"¦ Generated {len(successful_signals)} trading signals in {execution_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.inference_intervals["signals"])

            except Exception as e:
                self.logger.error(f"Signal generation loop error: {e}")
                await asyncio.sleep(30)

    async def _generate_symbol_signal(self, symbol: str):
        """Generate trading signal for a single symbol."""
        try:
            signal = await self.ai_ml_engine.generate_trading_signals(symbol)

            if signal:
                # Sync signal to InfluxDB
                await influx_sync.sync_trading_signal(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type,
                    strength=signal.strength,
                    confidence=signal.confidence,
                    expected_return=signal.expected_return,
                    risk_score=signal.risk_score,
                    model_ensemble=",".join(signal.model_ensemble),
                )

                self.logger.debug(
                    f"¦ Generated {signal.signal_type} signal for {symbol} (strength: {signal.strength:.2f})"
                )
                return signal

        except Exception as e:
            self.logger.error(f"Failed to generate signal for {symbol}: {e}")

        return None

    async def _sentiment_analysis_loop(self):
        """Continuous sentiment analysis loop."""
        while self.running:
            try:
                start_time = datetime.now()

                # Analyze market sentiment
                await self._analyze_market_sentiment()

                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_performance_metric("sentiment", execution_time)

                self.logger.info(
                    f" Sentiment analysis completed in {execution_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.inference_intervals["sentiment"])

            except Exception as e:
                self.logger.error(f"Sentiment analysis loop error: {e}")
                await asyncio.sleep(60)

    async def _analyze_market_sentiment(self):
        """Analyze overall market sentiment."""
        try:
            # Sample news headlines (in real implementation, fetch from news APIs)
            sample_texts = [
                "Market rallies on positive economic data",
                "Tech stocks show strong performance",
                "Federal Reserve maintains dovish stance",
                "Inflation concerns weigh on investor sentiment",
                "Corporate earnings exceed expectations",
            ]

            overall_sentiment = 0
            sentiment_count = 0

            for text in sample_texts:
                sentiment_data = await self.ai_ml_engine.analyze_sentiment(text)
                if sentiment_data:
                    overall_sentiment += sentiment_data.get("compound", 0)
                    sentiment_count += 1

            if sentiment_count > 0:
                avg_sentiment = overall_sentiment / sentiment_count

                # Sync to InfluxDB
                await influx_sync.sync_sentiment_analysis(
                    symbol="MARKET",
                    sentiment_score=avg_sentiment,
                    positive=max(0, avg_sentiment),
                    negative=abs(min(0, avg_sentiment)),
                    neutral=1 - abs(avg_sentiment),
                )

                self.logger.debug(f" Market sentiment: {avg_sentiment:.3f}")

        except Exception as e:
            self.logger.error(f"Market sentiment analysis failed: {e}")

    async def _model_training_loop(self):
        """Periodic model retraining loop."""
        while self.running:
            try:
                start_time = datetime.now()

                # Retrain models for one symbol per cycle
                symbol_index = (
                    len(self.last_inference_times.get("training", []))
                ) % len(self.symbols)
                symbol = self.symbols[symbol_index]

                self.logger.info(f"  Retraining models for {symbol}")
                models_performance = await self.ai_ml_engine.train_ensemble_models(
                    symbol
                )

                if models_performance:
                    # Sync model performance to InfluxDB
                    for model_name, perf in models_performance.items():
                        await influx_sync.sync_model_performance(
                            model_name=model_name,
                            symbol=symbol,
                            accuracy=perf.get("r2_score", 0),
                            mse=perf.get("mse", 0),
                            mae=perf.get("mae", 0),
                        )

                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_performance_metric("model_training", execution_time)

                self.logger.info(
                    f"  Model training completed for {symbol} in {execution_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.inference_intervals["model_training"])

            except Exception as e:
                self.logger.error(f"Model training loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _feature_importance_loop(self):
        """Feature importance analysis loop."""
        while self.running:
            try:
                start_time = datetime.now()

                # Sync feature importance for all symbols
                for symbol in self.symbols:
                    if symbol in self.ai_ml_engine.feature_importance:
                        importance_data = self.ai_ml_engine.feature_importance[symbol]

                        for feature, importance in importance_data.items():
                            await influx_sync.sync_feature_importance(
                                feature_name=feature,
                                importance_score=importance
                                * 100,  # Convert to percentage
                                symbol=symbol,
                            )

                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._update_performance_metric(
                    "feature_importance", execution_time
                )

                self.logger.info(
                    f" Feature importance analysis completed in {execution_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.inference_intervals["feature_importance"])

            except Exception as e:
                self.logger.error(f"Feature importance loop error: {e}")
                await asyncio.sleep(60)

    async def _performance_monitoring_loop(self):
        """Monitor and log service performance metrics."""
        while self.running:
            try:
                # Log performance summary every 5 minutes
                await asyncio.sleep(300)

                if self.performance_metrics:
                    self.logger.info(" AI/ML Service Performance Summary:")
                    for task_type, metrics in self.performance_metrics.items():
                        avg_time = sum(metrics) / len(metrics) if metrics else 0
                        self.logger.info(
                            f"  {task_type}: {avg_time:.2f}s avg, {len(metrics)} cycles"
                        )

            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")

    # =====================================================
    # PERFORMANCE TRACKING
    # =====================================================

    async def _update_performance_metric(self, task_type: str, execution_time: float):
        """Update performance metrics for a task type."""
        if task_type not in self.performance_metrics:
            self.performance_metrics[task_type] = []

        # Keep only last 20 measurements
        metrics = self.performance_metrics[task_type]
        metrics.append(execution_time)
        if len(metrics) > 20:
            metrics.pop(0)

        # Sync performance to InfluxDB
        await influx_sync.sync_service_performance(
            service_name="ai_ml_inference",
            task_type=task_type,
            execution_time=execution_time,
            success=True,
        )

    # =====================================================
    # API ENDPOINTS
    # =====================================================

    async def get_latest_predictions(
        self, symbol: str = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Get latest predictions for symbol(s)."""
        try:
            if symbol:
                predictions = await self.ai_ml_engine.generate_predictions(symbol)
                return {
                    "symbol": symbol,
                    "predictions": [asdict(pred) for pred in predictions],
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # Get predictions for all symbols
                all_predictions = {}
                for sym in self.symbols[:5]:  # Limit to avoid timeout
                    predictions = await self.ai_ml_engine.generate_predictions(sym)
                    all_predictions[sym] = [asdict(pred) for pred in predictions]

                return {
                    "all_symbols": all_predictions,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Failed to get predictions: {e}")
            return {}

    async def get_latest_signals(self, symbol: str = None) -> Dict[str, Any]:
        """Get latest trading signals."""
        try:
            if symbol:
                signal = await self.ai_ml_engine.generate_trading_signals(symbol)
                return {
                    "symbol": symbol,
                    "signal": asdict(signal) if signal else None,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # Get signals for all symbols
                all_signals = {}
                for sym in self.symbols[:5]:
                    signal = await self.ai_ml_engine.generate_trading_signals(sym)
                    all_signals[sym] = asdict(signal) if signal else None

                return {
                    "all_symbols": all_signals,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Failed to get signals: {e}")
            return {}

    async def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        try:
            performance_data = {}

            for symbol, models in self.ai_ml_engine.model_performance.items():
                performance_data[symbol] = {}
                for model_name, perf in models.items():
                    performance_data[symbol][model_name] = {
                        "r2_score": perf.get("r2_score", 0),
                        "mse": perf.get("mse", 0),
                        "mae": perf.get("mae", 0),
                    }

            return {
                "model_performance": performance_data,
                "feature_importance": self.ai_ml_engine.feature_importance,
                "service_performance": self.performance_metrics,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to get model performance: {e}")
            return {}


# Global service instance
inference_service = None


async def initialize_inference_service(
    db_manager: DatabaseManager,
) -> AIMLInferenceService:
    """Initialize the global inference service."""
    global inference_service
    inference_service = AIMLInferenceService(db_manager)
    await inference_service.initialize()
    return inference_service
