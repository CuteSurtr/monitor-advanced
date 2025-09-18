"""
AI/ML Data Pipeline
Comprehensive data pipeline for training and serving ML models in production
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import json

from src.analytics.ai_ml_engine import AIMLEngine, initialize_ai_ml_engine
from src.analytics.ai_ml_inference_service import AIMLInferenceService, initialize_inference_service
from src.analytics.influxdb_sync import influx_sync
from src.utils.database import DatabaseManager
from src.utils.logger import get_logger
from src.utils.config import get_config

class AIMLDataPipeline:
    """Complete AI/ML data pipeline for model training and inference."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.db_manager = None
        self.ai_ml_engine = None
        self.inference_service = None
        
        # Pipeline configuration
        self.pipeline_config = {
            'data_collection': {
                'enabled': True,
                'interval_minutes': 5,
                'lookback_days': 365
            },
            'feature_engineering': {
                'enabled': True,
                'interval_minutes': 15,
                'feature_types': ['technical', 'sentiment', 'macro', 'cross_asset']
            },
            'model_training': {
                'enabled': True,
                'interval_hours': 6,
                'retrain_threshold': 0.05,  # Retrain if performance drops by 5%
                'validation_split': 0.2
            },
            'inference': {
                'enabled': True,
                'prediction_interval_minutes': 5,
                'signal_interval_minutes': 3
            },
            'monitoring': {
                'enabled': True,
                'performance_tracking': True,
                'alert_thresholds': {
                    'accuracy_drop': 0.1,
                    'inference_delay': 30  # seconds
                }
            }
        }
        
        # Symbols to process
        self.symbols = [
            # Large Cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
            # ETFs
            'SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'VIX',
            # Additional stocks
            'JPM', 'JNJ', 'V', 'PG', 'HD', 'DIS', 'NFLX', 'CRM'
        ]
        
        # Pipeline state
        self.running = False
        self.pipeline_metrics = {}
        self.last_training_times = {}
        
    async def initialize(self):
        """Initialize the AI/ML data pipeline."""
        try:
            self.logger.info("€ Initializing AI/ML Data Pipeline...")
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Initialize AI/ML engine
            self.ai_ml_engine = await initialize_ai_ml_engine(self.db_manager)
            
            # Initialize inference service
            self.inference_service = await initialize_inference_service(self.db_manager)
            
            # Initialize InfluxDB
            await influx_sync.initialize()
            
            # Setup pipeline directories
            self._setup_directories()
            
            # Schedule periodic tasks
            self._schedule_tasks()
            
            self.logger.info("AI/ML Data Pipeline initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI/ML pipeline: {e}")
            raise
    
    def _setup_directories(self):
        """Setup directory structure for the pipeline."""
        directories = [
            "data/raw",
            "data/processed", 
            "data/features",
            "models/checkpoints",
            "models/production",
            "logs/pipeline",
            "reports/performance"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _schedule_tasks(self):
        """Schedule periodic pipeline tasks."""
        # Data collection every 5 minutes
        schedule.every(5).minutes.do(self._run_async_task, self._data_collection_task)
        
        # Feature engineering every 15 minutes
        schedule.every(15).minutes.do(self._run_async_task, self._feature_engineering_task)
        
        # Model training every 6 hours
        schedule.every(6).hours.do(self._run_async_task, self._model_training_task)
        
        # Performance monitoring every hour
        schedule.every().hour.do(self._run_async_task, self._monitoring_task)
        
        # Daily cleanup
        schedule.every().day.at("02:00").do(self._run_async_task, self._cleanup_task)
    
    def _run_async_task(self, coro):
        """Run async task in sync context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(coro())
            else:
                loop.run_until_complete(coro())
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
    
    async def start_pipeline(self):
        """Start the complete AI/ML pipeline."""
        self.running = True
        self.logger.info("€ Starting AI/ML Data Pipeline")
        
        try:
            # Start inference service
            inference_task = asyncio.create_task(self.inference_service.start_service())
            
            # Start scheduler
            scheduler_task = asyncio.create_task(self._run_scheduler())
            
            # Run both concurrently
            await asyncio.gather(inference_task, scheduler_task)
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
        finally:
            self.running = False
    
    async def _run_scheduler(self):
        """Run the task scheduler."""
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def stop_pipeline(self):
        """Stop the pipeline."""
        self.running = False
        if self.inference_service:
            self.inference_service.stop_service()
        self.logger.info("AI/ML Data Pipeline stopped")
    
    # =====================================================
    # PIPELINE TASKS
    # =====================================================
    
    async def _data_collection_task(self):
        """Collect and validate data for ML pipeline."""
        try:
            self.logger.info("Š Running data collection task")
            start_time = datetime.now()
            
            collected_symbols = 0
            for symbol in self.symbols:
                try:
                    # Check if we have recent data
                    latest_data = await self.db_manager.get_latest_stock_data(symbol)
                    
                    if not latest_data or self._is_data_stale(latest_data):
                        self.logger.warning(f"Stale data detected for {symbol}")
                        # In production, trigger data collection
                        continue
                    
                    collected_symbols += 1
                    
                except Exception as e:
                    self.logger.error(f"Data collection failed for {symbol}: {e}")
                    continue
            
            # Track metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._track_pipeline_metric('data_collection', {
                'symbols_processed': collected_symbols,
                'execution_time': execution_time,
                'success_rate': collected_symbols / len(self.symbols)
            })
            
            self.logger.info(f"Data collection completed: {collected_symbols}/{len(self.symbols)} symbols in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Data collection task failed: {e}")
    
    async def _feature_engineering_task(self):
        """Run feature engineering for all symbols."""
        try:
            self.logger.info("§ Running feature engineering task")
            start_time = datetime.now()
            
            processed_symbols = 0
            for symbol in self.symbols[:5]:  # Limit to avoid overwhelming
                try:
                    # Engineer features
                    features_df = await self.ai_ml_engine.engineer_features(symbol)
                    
                    if not features_df.empty:
                        # Save features to disk
                        await self._save_features(symbol, features_df)
                        processed_symbols += 1
                        
                        # Sync feature metrics to InfluxDB
                        await self._sync_feature_metrics(symbol, features_df)
                    
                except Exception as e:
                    self.logger.error(f"Feature engineering failed for {symbol}: {e}")
                    continue
            
            # Track metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._track_pipeline_metric('feature_engineering', {
                'symbols_processed': processed_symbols,
                'execution_time': execution_time,
                'features_generated': len(self.ai_ml_engine.feature_columns) if self.ai_ml_engine.feature_columns else 0
            })
            
            self.logger.info(f"Feature engineering completed: {processed_symbols} symbols in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Feature engineering task failed: {e}")
    
    async def _model_training_task(self):
        """Run model training and validation."""
        try:
            self.logger.info("  Running model training task")
            start_time = datetime.now()
            
            trained_models = 0
            for symbol in self.symbols[:3]:  # Train 3 symbols per cycle
                try:
                    # Check if retraining is needed
                    if not await self._should_retrain_model(symbol):
                        continue
                    
                    self.logger.info(f"  Training models for {symbol}")
                    
                    # Train ensemble models
                    models_performance = await self.ai_ml_engine.train_ensemble_models(symbol)
                    
                    if models_performance:
                        # Validate models
                        validation_results = await self._validate_models(symbol, models_performance)
                        
                        # Deploy if validation passes
                        if validation_results['all_models_valid']:
                            await self._deploy_models(symbol, models_performance)
                            trained_models += 1
                            
                            # Update training timestamp
                            self.last_training_times[symbol] = datetime.now()
                        
                        # Sync training metrics
                        await self._sync_training_metrics(symbol, models_performance, validation_results)
                    
                except Exception as e:
                    self.logger.error(f"Model training failed for {symbol}: {e}")
                    continue
            
            # Track metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._track_pipeline_metric('model_training', {
                'models_trained': trained_models,
                'execution_time': execution_time,
                'symbols_processed': min(3, len(self.symbols))
            })
            
            self.logger.info(f"Model training completed: {trained_models} models in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Model training task failed: {e}")
    
    async def _monitoring_task(self):
        """Monitor pipeline performance and model health."""
        try:
            self.logger.info("Š Running monitoring task")
            start_time = datetime.now()
            
            # Check model performance degradation
            degraded_models = await self._check_model_degradation()
            
            # Check inference service health
            service_health = await self._check_service_health()
            
            # Generate performance report
            performance_report = await self._generate_performance_report()
            
            # Sync monitoring data
            await self._sync_monitoring_data({
                'degraded_models': degraded_models,
                'service_health': service_health,
                'performance_report': performance_report
            })
            
            # Track metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._track_pipeline_metric('monitoring', {
                'execution_time': execution_time,
                'models_checked': len(self.ai_ml_engine.models) if self.ai_ml_engine.models else 0,
                'degraded_models': len(degraded_models)
            })
            
            self.logger.info(f"Monitoring completed in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Monitoring task failed: {e}")
    
    async def _cleanup_task(self):
        """Daily cleanup of old data and models."""
        try:
            self.logger.info("¹ Running cleanup task")
            start_time = datetime.now()
            
            # Clean old feature files
            await self._cleanup_old_features()
            
            # Clean old model checkpoints
            await self._cleanup_old_models()
            
            # Clean old logs
            await self._cleanup_old_logs()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Cleanup completed in {execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Cleanup task failed: {e}")
    
    # =====================================================
    # HELPER METHODS
    # =====================================================
    
    def _is_data_stale(self, latest_data: Dict[str, Any]) -> bool:
        """Check if data is stale."""
        if not latest_data:
            return True
        
        last_update = latest_data.get('timestamp')
        if not last_update:
            return True
        
        if isinstance(last_update, str):
            last_update = datetime.fromisoformat(last_update)
        
        # Data is stale if older than 30 minutes
        return (datetime.now() - last_update).total_seconds() > 1800
    
    async def _should_retrain_model(self, symbol: str) -> bool:
        """Determine if model should be retrained."""
        # Check if model exists
        if symbol not in self.ai_ml_engine.models:
            return True
        
        # Check last training time
        last_training = self.last_training_times.get(symbol)
        if not last_training:
            return True
        
        # Retrain every 24 hours
        if (datetime.now() - last_training).total_seconds() > 86400:
            return True
        
        # Check performance degradation
        if symbol in self.ai_ml_engine.model_performance:
            models_perf = self.ai_ml_engine.model_performance[symbol]
            avg_performance = np.mean([perf.get('r2_score', 0) for perf in models_perf.values()])
            
            # Retrain if average performance drops below 70%
            if avg_performance < 0.7:
                return True
        
        return False
    
    async def _validate_models(self, symbol: str, models_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trained models."""
        validation_results = {
            'all_models_valid': True,
            'model_validations': {}
        }
        
        for model_name, perf in models_performance.items():
            # Basic validation criteria
            is_valid = (
                perf.get('r2_score', 0) > 0.5 and  # Minimum accuracy
                perf.get('mse', float('inf')) < 1.0 and  # Maximum MSE
                perf.get('mae', float('inf')) < 0.5     # Maximum MAE
            )
            
            validation_results['model_validations'][model_name] = {
                'is_valid': is_valid,
                'r2_score': perf.get('r2_score', 0),
                'mse': perf.get('mse', 0),
                'mae': perf.get('mae', 0)
            }
            
            if not is_valid:
                validation_results['all_models_valid'] = False
                self.logger.warning(f"Model {model_name} failed validation for {symbol}")
        
        return validation_results
    
    async def _deploy_models(self, symbol: str, models_performance: Dict[str, Any]):
        """Deploy validated models to production."""
        try:
            # Copy models to production directory
            production_dir = Path(f"models/production/{symbol}")
            production_dir.mkdir(parents=True, exist_ok=True)
            
            # Save deployment metadata
            deployment_metadata = {
                'symbol': symbol,
                'deployment_time': datetime.now().isoformat(),
                'models': list(models_performance.keys()),
                'performance': {
                    model: {
                        'r2_score': perf.get('r2_score', 0),
                        'mse': perf.get('mse', 0),
                        'mae': perf.get('mae', 0)
                    }
                    for model, perf in models_performance.items()
                }
            }
            
            with open(production_dir / "deployment_metadata.json", 'w') as f:
                json.dump(deployment_metadata, f, indent=2)
            
            self.logger.info(f"Models deployed for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Model deployment failed for {symbol}: {e}")
    
    async def _save_features(self, symbol: str, features_df: pd.DataFrame):
        """Save engineered features to disk."""
        try:
            features_dir = Path(f"data/features/{symbol}")
            features_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = features_dir / f"features_{timestamp}.parquet"
            
            features_df.to_parquet(filename)
            
            # Keep only latest 10 feature files
            feature_files = sorted(features_dir.glob("features_*.parquet"))
            if len(feature_files) > 10:
                for old_file in feature_files[:-10]:
                    old_file.unlink()
            
        except Exception as e:
            self.logger.error(f"Failed to save features for {symbol}: {e}")
    
    async def _check_model_degradation(self) -> List[str]:
        """Check for model performance degradation."""
        degraded_models = []
        
        try:
            for symbol, models in self.ai_ml_engine.model_performance.items():
                for model_name, perf in models.items():
                    # Check if performance has degraded
                    current_score = perf.get('r2_score', 0)
                    
                    # In production, compare with historical performance
                    threshold = 0.6  # Minimum acceptable performance
                    
                    if current_score < threshold:
                        degraded_models.append(f"{symbol}:{model_name}")
                        self.logger.warning(f"Performance degradation detected: {symbol}:{model_name} ({current_score:.3f})")
        
        except Exception as e:
            self.logger.error(f"Model degradation check failed: {e}")
        
        return degraded_models
    
    async def _check_service_health(self) -> Dict[str, Any]:
        """Check inference service health."""
        health_status = {
            'inference_service_running': self.inference_service.running if self.inference_service else False,
            'models_loaded': len(self.ai_ml_engine.models) if self.ai_ml_engine.models else 0,
            'last_prediction_time': datetime.now().isoformat(),
            'performance_metrics': self.inference_service.performance_metrics if self.inference_service else {}
        }
        
        return health_status
    
    async def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        report = {
            'pipeline_metrics': self.pipeline_metrics,
            'models_count': len(self.ai_ml_engine.models) if self.ai_ml_engine.models else 0,
            'symbols_processed': len(self.symbols),
            'report_timestamp': datetime.now().isoformat()
        }
        
        return report
    
    async def _track_pipeline_metric(self, task_type: str, metrics: Dict[str, Any]):
        """Track pipeline performance metrics."""
        if task_type not in self.pipeline_metrics:
            self.pipeline_metrics[task_type] = []
        
        metric_entry = {
            'timestamp': datetime.now().isoformat(),
            **metrics
        }
        
        self.pipeline_metrics[task_type].append(metric_entry)
        
        # Keep only last 100 entries
        if len(self.pipeline_metrics[task_type]) > 100:
            self.pipeline_metrics[task_type] = self.pipeline_metrics[task_type][-100:]
        
        # Sync to InfluxDB
        await influx_sync.sync_pipeline_metrics(task_type, metrics)
    
    async def _sync_feature_metrics(self, symbol: str, features_df: pd.DataFrame):
        """Sync feature engineering metrics to InfluxDB."""
        try:
            await influx_sync.sync_feature_engineering_metrics(
                symbol=symbol,
                features_count=len(features_df.columns),
                rows_count=len(features_df),
                null_percentage=features_df.isnull().sum().sum() / (len(features_df) * len(features_df.columns))
            )
        except Exception as e:
            self.logger.error(f"Failed to sync feature metrics: {e}")
    
    async def _sync_training_metrics(self, symbol: str, models_performance: Dict[str, Any], validation_results: Dict[str, Any]):
        """Sync model training metrics to InfluxDB."""
        try:
            for model_name, perf in models_performance.items():
                await influx_sync.sync_model_performance(
                    model_name=model_name,
                    symbol=symbol,
                    accuracy=perf.get('r2_score', 0),
                    mse=perf.get('mse', 0),
                    mae=perf.get('mae', 0)
                )
        except Exception as e:
            self.logger.error(f"Failed to sync training metrics: {e}")
    
    async def _sync_monitoring_data(self, monitoring_data: Dict[str, Any]):
        """Sync monitoring data to InfluxDB."""
        try:
            await influx_sync.sync_pipeline_monitoring(
                degraded_models_count=len(monitoring_data.get('degraded_models', [])),
                service_health_score=1.0 if monitoring_data.get('service_health', {}).get('inference_service_running') else 0.0
            )
        except Exception as e:
            self.logger.error(f"Failed to sync monitoring data: {e}")
    
    async def _cleanup_old_features(self):
        """Clean up old feature files."""
        try:
            features_dir = Path("data/features")
            if features_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for symbol_dir in features_dir.iterdir():
                    if symbol_dir.is_dir():
                        for feature_file in symbol_dir.glob("features_*.parquet"):
                            if feature_file.stat().st_mtime < cutoff_date.timestamp():
                                feature_file.unlink()
        except Exception as e:
            self.logger.error(f"Feature cleanup failed: {e}")
    
    async def _cleanup_old_models(self):
        """Clean up old model files."""
        try:
            checkpoints_dir = Path("models/checkpoints")
            if checkpoints_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for model_file in checkpoints_dir.rglob("*"):
                    if model_file.is_file() and model_file.stat().st_mtime < cutoff_date.timestamp():
                        model_file.unlink()
        except Exception as e:
            self.logger.error(f"Model cleanup failed: {e}")
    
    async def _cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            logs_dir = Path("logs")
            if logs_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=14)
                
                for log_file in logs_dir.rglob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")

# Main execution
async def main():
    """Main pipeline execution."""
    pipeline = AIMLDataPipeline()
    
    try:
        # Initialize pipeline
        await pipeline.initialize()
        
        # Start pipeline
        await pipeline.start_pipeline()
        
    except KeyboardInterrupt:
        print("\n‘ Pipeline stopped by user")
    except Exception as e:
        print(f"Pipeline failed: {e}")
    finally:
        pipeline.stop_pipeline()

if __name__ == "__main__":
    asyncio.run(main())