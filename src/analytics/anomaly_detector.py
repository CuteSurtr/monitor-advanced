"""
Anomaly Detection Module

This module provides machine learning-based anomaly detection for financial markets,
identifying unusual trading patterns, price movements, and market anomalies.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.svm import OneClassSVM
import warnings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnomalyResult:
    """Container for anomaly detection results"""
    anomalies: pd.Series
    anomaly_scores: pd.Series
    features_used: List[str]
    model_info: Dict
    metadata: Optional[Dict] = None


class AnomalyDetector:
    """
    Machine learning-based anomaly detection for financial markets
    
    Provides methods for detecting unusual trading patterns, price movements,
    volume anomalies, and other market irregularities.
    """
    
    def __init__(self):
        self.logger = logger
        self.scaler = StandardScaler()
        self.models = {}
    
    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for anomaly detection
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with extracted features
        """
        try:
            features = pd.DataFrame(index=data.index)
            
            # Price-based features
            features['returns'] = data['close'].pct_change()
            features['log_returns'] = np.log(data['close'] / data['close'].shift(1))
            features['price_change'] = data['close'] - data['close'].shift(1)
            features['price_range'] = data['high'] - data['low']
            features['price_range_pct'] = (data['high'] - data['low']) / data['close']
            
            # Volume-based features
            features['volume_change'] = data['volume'].pct_change()
            features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
            features['volume_std'] = data['volume'].rolling(20).std()
            
            # Technical features
            features['rsi'] = self._calculate_rsi(data['close'])
            features['volatility'] = features['returns'].rolling(20).std()
            features['price_momentum'] = data['close'] / data['close'].shift(5) - 1
            
            # OHLC relationships
            features['open_close_ratio'] = data['open'] / data['close']
            features['high_low_ratio'] = data['high'] / data['low']
            features['body_size'] = abs(data['close'] - data['open']) / data['close']
            features['upper_shadow'] = (data['high'] - np.maximum(data['open'], data['close'])) / data['close']
            features['lower_shadow'] = (np.minimum(data['open'], data['close']) - data['low']) / data['close']
            
            # Time-based features
            features['day_of_week'] = data.index.dayofweek
            features['month'] = data.index.month
            features['quarter'] = data.index.quarter
            
            # Remove infinite and NaN values
            features = features.replace([np.inf, -np.inf], np.nan)
            features = features.fillna(method='ffill').fillna(0)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return pd.DataFrame()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI for feature extraction"""
        try:
            delta = prices.diff()
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            avg_gains = gains.rolling(window=period).mean()
            avg_losses = losses.rolling(window=period).mean()
            
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(50, index=prices.index)
    
    def detect_price_anomalies(self, data: pd.DataFrame,
                             method: str = 'isolation_forest',
                             contamination: float = 0.1) -> AnomalyResult:
        """
        Detect price anomalies using various ML methods
        
        Args:
            data: DataFrame with OHLCV data
            method: Anomaly detection method
            contamination: Expected proportion of anomalies
            
        Returns:
            AnomalyResult with detected anomalies
        """
        try:
            # Extract features
            features = self.extract_features(data)
            
            if features.empty:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=[],
                    model_info={}
                )
            
            # Select relevant features for price anomaly detection
            price_features = [
                'returns', 'log_returns', 'price_change', 'price_range_pct',
                'volatility', 'price_momentum', 'body_size'
            ]
            
            feature_data = features[price_features].dropna()
            
            if len(feature_data) < 50:
                self.logger.warning("Insufficient data for anomaly detection")
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=price_features,
                    model_info={}
                )
            
            # Scale features
            scaled_features = self.scaler.fit_transform(feature_data)
            
            # Apply anomaly detection
            if method == 'isolation_forest':
                model = IsolationForest(
                    contamination=contamination,
                    random_state=42,
                    n_estimators=100
                )
                
            elif method == 'local_outlier_factor':
                model = LocalOutlierFactor(
                    contamination=contamination,
                    n_neighbors=20
                )
                
            elif method == 'one_class_svm':
                model = OneClassSVM(
                    nu=contamination,
                    kernel='rbf',
                    gamma='scale'
                )
                
            elif method == 'dbscan':
                model = DBSCAN(
                    eps=0.5,
                    min_samples=5
                )
                
            else:
                raise ValueError(f"Unknown anomaly detection method: {method}")
            
            # Fit and predict
            if method == 'local_outlier_factor':
                anomaly_scores = model.fit_predict(scaled_features)
                # LOF returns -1 for anomalies, 1 for normal points
                anomalies = anomaly_scores == -1
                scores = model.negative_outlier_factor_
            else:
                model.fit(scaled_features)
                if method == 'dbscan':
                    anomaly_scores = model.fit_predict(scaled_features)
                    anomalies = anomaly_scores == -1
                    scores = np.full(len(scaled_features), 0.5)  # Placeholder
                else:
                    anomaly_scores = model.predict(scaled_features)
                    anomalies = anomaly_scores == -1
                    scores = model.decision_function(scaled_features)
            
            # Create result series
            anomaly_series = pd.Series(anomalies, index=feature_data.index)
            score_series = pd.Series(scores, index=feature_data.index)
            
            model_info = {
                'method': method,
                'contamination': contamination,
                'n_features': len(price_features),
                'n_samples': len(feature_data),
                'n_anomalies': anomalies.sum()
            }
            
            return AnomalyResult(
                anomalies=anomaly_series,
                anomaly_scores=score_series,
                features_used=price_features,
                model_info=model_info
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting price anomalies: {e}")
            return AnomalyResult(
                anomalies=pd.Series(dtype=bool),
                anomaly_scores=pd.Series(dtype=float),
                features_used=[],
                model_info={}
            )
    
    def detect_volume_anomalies(self, data: pd.DataFrame,
                              method: str = 'isolation_forest',
                              contamination: float = 0.1) -> AnomalyResult:
        """
        Detect volume anomalies
        
        Args:
            data: DataFrame with OHLCV data
            method: Anomaly detection method
            contamination: Expected proportion of anomalies
            
        Returns:
            AnomalyResult with detected volume anomalies
        """
        try:
            # Extract features
            features = self.extract_features(data)
            
            if features.empty:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=[],
                    model_info={}
                )
            
            # Select volume-related features
            volume_features = [
                'volume_change', 'volume_ratio', 'volume_std',
                'returns', 'price_range_pct'  # Include price context
            ]
            
            feature_data = features[volume_features].dropna()
            
            if len(feature_data) < 50:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=volume_features,
                    model_info={}
                )
            
            # Scale features
            scaled_features = self.scaler.fit_transform(feature_data)
            
            # Apply anomaly detection
            if method == 'isolation_forest':
                model = IsolationForest(
                    contamination=contamination,
                    random_state=42
                )
            elif method == 'local_outlier_factor':
                model = LocalOutlierFactor(
                    contamination=contamination,
                    n_neighbors=20
                )
            else:
                model = IsolationForest(contamination=contamination, random_state=42)
            
            # Fit and predict
            if method == 'local_outlier_factor':
                anomaly_scores = model.fit_predict(scaled_features)
                anomalies = anomaly_scores == -1
                scores = model.negative_outlier_factor_
            else:
                model.fit(scaled_features)
                anomaly_scores = model.predict(scaled_features)
                anomalies = anomaly_scores == -1
                scores = model.decision_function(scaled_features)
            
            # Create result series
            anomaly_series = pd.Series(anomalies, index=feature_data.index)
            score_series = pd.Series(scores, index=feature_data.index)
            
            model_info = {
                'method': method,
                'contamination': contamination,
                'n_features': len(volume_features),
                'n_samples': len(feature_data),
                'n_anomalies': anomalies.sum()
            }
            
            return AnomalyResult(
                anomalies=anomaly_series,
                anomaly_scores=score_series,
                features_used=volume_features,
                model_info=model_info
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting volume anomalies: {e}")
            return AnomalyResult(
                anomalies=pd.Series(dtype=bool),
                anomaly_scores=pd.Series(dtype=float),
                features_used=[],
                model_info={}
            )
    
    def detect_pattern_anomalies(self, data: pd.DataFrame,
                               pattern_window: int = 20,
                               method: str = 'isolation_forest') -> AnomalyResult:
        """
        Detect anomalies in price patterns
        
        Args:
            data: DataFrame with OHLCV data
            pattern_window: Window size for pattern analysis
            method: Anomaly detection method
            
        Returns:
            AnomalyResult with detected pattern anomalies
        """
        try:
            # Extract pattern features
            pattern_features = pd.DataFrame(index=data.index)
            
            # Price pattern features
            pattern_features['price_trend'] = data['close'].rolling(pattern_window).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            
            pattern_features['price_volatility'] = data['close'].pct_change().rolling(pattern_window).std()
            
            pattern_features['volume_trend'] = data['volume'].rolling(pattern_window).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            
            # Candlestick pattern features
            pattern_features['body_size_avg'] = abs(data['close'] - data['open']).rolling(pattern_window).mean()
            pattern_features['shadow_ratio'] = (
                (data['high'] - np.maximum(data['open'], data['close'])) /
                (np.minimum(data['open'], data['close']) - data['low'])
            ).rolling(pattern_window).mean()
            
            # Momentum features
            pattern_features['momentum'] = data['close'] / data['close'].shift(pattern_window) - 1
            pattern_features['momentum_std'] = data['close'].pct_change().rolling(pattern_window).std()
            
            # Remove infinite and NaN values
            pattern_features = pattern_features.replace([np.inf, -np.inf], np.nan)
            pattern_features = pattern_features.fillna(method='ffill').fillna(0)
            
            if pattern_features.empty:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=[],
                    model_info={}
                )
            
            # Scale features
            scaled_features = self.scaler.fit_transform(pattern_features)
            
            # Apply anomaly detection
            if method == 'isolation_forest':
                model = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
            else:
                model = IsolationForest(contamination=0.1, random_state=42)
            
            model.fit(scaled_features)
            anomaly_scores = model.predict(scaled_features)
            anomalies = anomaly_scores == -1
            scores = model.decision_function(scaled_features)
            
            # Create result series
            anomaly_series = pd.Series(anomalies, index=pattern_features.index)
            score_series = pd.Series(scores, index=pattern_features.index)
            
            model_info = {
                'method': method,
                'pattern_window': pattern_window,
                'n_features': len(pattern_features.columns),
                'n_samples': len(pattern_features),
                'n_anomalies': anomalies.sum()
            }
            
            return AnomalyResult(
                anomalies=anomaly_series,
                anomaly_scores=score_series,
                features_used=list(pattern_features.columns),
                model_info=model_info
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting pattern anomalies: {e}")
            return AnomalyResult(
                anomalies=pd.Series(dtype=bool),
                anomaly_scores=pd.Series(dtype=float),
                features_used=[],
                model_info={}
            )
    
    def detect_market_regime_anomalies(self, data: pd.DataFrame,
                                     window: int = 60,
                                     method: str = 'isolation_forest') -> AnomalyResult:
        """
        Detect anomalies in market regime changes
        
        Args:
            data: DataFrame with OHLCV data
            window: Window size for regime analysis
            method: Anomaly detection method
            
        Returns:
            AnomalyResult with detected regime anomalies
        """
        try:
            # Extract regime features
            regime_features = pd.DataFrame(index=data.index)
            
            # Volatility regime
            returns = data['close'].pct_change()
            regime_features['volatility_regime'] = returns.rolling(window).std()
            regime_features['volatility_change'] = regime_features['volatility_regime'].pct_change()
            
            # Volume regime
            regime_features['volume_regime'] = data['volume'].rolling(window).mean()
            regime_features['volume_regime_change'] = regime_features['volume_regime'].pct_change()
            
            # Price regime
            regime_features['price_regime'] = data['close'].rolling(window).mean()
            regime_features['price_regime_change'] = regime_features['price_regime'].pct_change()
            
            # Correlation regime (simplified)
            regime_features['price_volume_corr'] = (
                data['close'].rolling(window).corr(data['volume'])
            )
            
            # Market efficiency features
            regime_features['hurst_exponent'] = self._calculate_hurst_exponent(data['close'], window)
            
            # Remove infinite and NaN values
            regime_features = regime_features.replace([np.inf, -np.inf], np.nan)
            regime_features = regime_features.fillna(method='ffill').fillna(0)
            
            if regime_features.empty:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=[],
                    model_info={}
                )
            
            # Scale features
            scaled_features = self.scaler.fit_transform(regime_features)
            
            # Apply anomaly detection
            if method == 'isolation_forest':
                model = IsolationForest(
                    contamination=0.05,  # Lower contamination for regime anomalies
                    random_state=42
                )
            else:
                model = IsolationForest(contamination=0.05, random_state=42)
            
            model.fit(scaled_features)
            anomaly_scores = model.predict(scaled_features)
            anomalies = anomaly_scores == -1
            scores = model.decision_function(scaled_features)
            
            # Create result series
            anomaly_series = pd.Series(anomalies, index=regime_features.index)
            score_series = pd.Series(scores, index=regime_features.index)
            
            model_info = {
                'method': method,
                'window': window,
                'n_features': len(regime_features.columns),
                'n_samples': len(regime_features),
                'n_anomalies': anomalies.sum()
            }
            
            return AnomalyResult(
                anomalies=anomaly_series,
                anomaly_scores=score_series,
                features_used=list(regime_features.columns),
                model_info=model_info
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting regime anomalies: {e}")
            return AnomalyResult(
                anomalies=pd.Series(dtype=bool),
                anomaly_scores=pd.Series(dtype=float),
                features_used=[],
                model_info={}
            )
    
    def _calculate_hurst_exponent(self, prices: pd.Series, window: int) -> pd.Series:
        """Calculate Hurst exponent for market efficiency"""
        try:
            def hurst(ts):
                if len(ts) < 10:
                    return 0.5
                
                # Calculate price changes
                lags = range(2, min(20, len(ts)//2))
                tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
                
                if len(tau) < 2:
                    return 0.5
                
                # Linear fit to double-log graph
                reg = np.polyfit(np.log(lags), np.log(tau), 1)
                return reg[0]
            
            hurst_values = prices.rolling(window).apply(hurst)
            return hurst_values.fillna(0.5)
            
        except Exception as e:
            self.logger.error(f"Error calculating Hurst exponent: {e}")
            return pd.Series(0.5, index=prices.index)
    
    def combine_anomaly_results(self, results: List[AnomalyResult],
                              weights: Optional[List[float]] = None) -> AnomalyResult:
        """
        Combine multiple anomaly detection results
        
        Args:
            results: List of AnomalyResult objects
            weights: Optional weights for each result
            
        Returns:
            Combined AnomalyResult
        """
        try:
            if not results:
                return AnomalyResult(
                    anomalies=pd.Series(dtype=bool),
                    anomaly_scores=pd.Series(dtype=float),
                    features_used=[],
                    model_info={}
                )
            
            # Use equal weights if not provided
            if weights is None:
                weights = [1.0 / len(results)] * len(results)
            
            # Normalize weights
            weights = np.array(weights) / np.sum(weights)
            
            # Combine anomaly scores
            combined_scores = pd.Series(0.0, index=results[0].anomaly_scores.index)
            for result, weight in zip(results, weights):
                # Align indices
                aligned_scores = result.anomaly_scores.reindex(combined_scores.index, fill_value=0)
                combined_scores += weight * aligned_scores
            
            # Determine anomalies based on combined scores
            # Use threshold based on weighted average of individual thresholds
            threshold = np.percentile(combined_scores, 90)  # Top 10% as anomalies
            combined_anomalies = combined_scores > threshold
            
            # Combine features and model info
            all_features = []
            for result in results:
                all_features.extend(result.features_used)
            all_features = list(set(all_features))  # Remove duplicates
            
            combined_model_info = {
                'method': 'combined',
                'n_models': len(results),
                'weights': weights.tolist(),
                'threshold': threshold,
                'n_anomalies': combined_anomalies.sum()
            }
            
            return AnomalyResult(
                anomalies=combined_anomalies,
                anomaly_scores=combined_scores,
                features_used=all_features,
                model_info=combined_model_info
            )
            
        except Exception as e:
            self.logger.error(f"Error combining anomaly results: {e}")
            return AnomalyResult(
                anomalies=pd.Series(dtype=bool),
                anomaly_scores=pd.Series(dtype=float),
                features_used=[],
                model_info={}
            )
    
    def generate_anomaly_report(self, results: Dict[str, AnomalyResult]) -> str:
        """
        Generate comprehensive anomaly detection report
        
        Args:
            results: Dictionary of anomaly detection results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("ANOMALY DETECTION REPORT")
        report.append("=" * 60)
        report.append("")
        
        try:
            for analysis_name, result in results.items():
                report.append(f"Analysis: {analysis_name.upper()}")
                report.append("-" * 40)
                
                if not result.anomalies.empty:
                    report.append(f"Detection Method: {result.model_info.get('method', 'Unknown')}")
                    report.append(f"Number of Anomalies: {result.model_info.get('n_anomalies', 0)}")
                    report.append(f"Anomaly Rate: {result.model_info.get('n_anomalies', 0) / len(result.anomalies):.2%}")
                    report.append(f"Features Used: {len(result.features_used)}")
                    report.append("")
                    
                    # Show recent anomalies
                    recent_anomalies = result.anomalies.tail(10)
                    if recent_anomalies.any():
                        report.append("Recent Anomalies:")
                        for date, is_anomaly in recent_anomalies.items():
                            if is_anomaly:
                                score = result.anomaly_scores.get(date, 0)
                                report.append(f"  {date.strftime('%Y-%m-%d')}: Score = {score:.3f}")
                        report.append("")
                    
                    # Feature importance (simplified)
                    if result.features_used:
                        report.append("Features Used:")
                        for feature in result.features_used[:5]:  # Show first 5
                            report.append(f"  - {feature}")
                        if len(result.features_used) > 5:
                            report.append(f"  ... and {len(result.features_used) - 5} more")
                        report.append("")
                
                report.append("")
            
        except Exception as e:
            self.logger.error(f"Error generating anomaly report: {e}")
            report.append("Error generating report")
        
        return "\n".join(report)
    
    def export_anomaly_data(self, results: Dict[str, AnomalyResult],
                          output_dir: str = "data/anomalies") -> None:
        """
        Export anomaly detection results to files
        
        Args:
            results: Dictionary of anomaly detection results
            output_dir: Output directory for files
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for analysis_name, result in results.items():
                # Export anomalies
                if not result.anomalies.empty:
                    result.anomalies.to_csv(f"{output_dir}/{analysis_name}_anomalies.csv")
                
                # Export anomaly scores
                if not result.anomaly_scores.empty:
                    result.anomaly_scores.to_csv(f"{output_dir}/{analysis_name}_scores.csv")
                
                # Export model info
                if result.model_info:
                    import json
                    with open(f"{output_dir}/{analysis_name}_model_info.json", 'w') as f:
                        json.dump(result.model_info, f, indent=2)
            
            self.logger.info(f"Anomaly data exported to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error exporting anomaly data: {e}") 