"""
Machine learning-based cost forecasting service.
Uses ARIMA, exponential smoothing, and ensemble methods for accurate projections.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import warnings

warnings.filterwarnings('ignore')


class ForecastAlgorithm(Enum):
    """Supported forecasting algorithms"""
    ARIMA = "arima"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    ENSEMBLE = "ensemble"  # Weighted average of all methods


@dataclass
class ForecastPoint:
    """Single forecast data point"""
    date: str
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float  # 0.0-1.0


@dataclass
class ForecastResult:
    """Complete forecast result with metadata"""
    algorithm: str
    forecast_points: List[ForecastPoint]
    rmse: float  # Root mean squared error
    mape: float  # Mean absolute percentage error
    trend: str  # 'increasing', 'decreasing', 'stable'
    seasonality_detected: bool
    anomalies: List[Tuple[str, float]]  # (date, anomaly_score)
    metadata: Dict


class TimeSeriesForecaster:
    """Advanced time series forecasting for cost data"""

    def __init__(self, history_days: int = 90):
        """
        Initialize forecaster.

        Args:
            history_days: Number of historical days to use for training
        """
        self.history_days = history_days
        self.min_history = 14  # Need at least 2 weeks of data

    def forecast_costs(
        self,
        daily_costs: List[Tuple[str, float]],  # [(date, cost), ...]
        forecast_days: int = 30,
        algorithm: ForecastAlgorithm = ForecastAlgorithm.ENSEMBLE,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Forecast future costs using time series analysis.

        Args:
            daily_costs: Historical daily costs as (date, cost) tuples
            forecast_days: Number of days to forecast
            algorithm: Forecasting algorithm to use
            confidence_level: Confidence level for prediction intervals (0.95 = 95%)

        Returns:
            ForecastResult with predictions and metadata
        """
        # Prepare data
        if len(daily_costs) < self.min_history:
            return self._fallback_forecast(daily_costs, forecast_days)

        costs = np.array([c[1] for c in daily_costs], dtype=float)
        dates = [c[0] for c in daily_costs]

        # Detect anomalies and seasonality
        anomalies = self._detect_anomalies(costs, dates)
        seasonality = self._detect_seasonality(costs)

        # Choose forecasting method
        if algorithm == ForecastAlgorithm.ARIMA:
            result = self._forecast_arima(costs, dates, forecast_days, confidence_level, seasonality)
        elif algorithm == ForecastAlgorithm.EXPONENTIAL_SMOOTHING:
            result = self._forecast_exponential_smoothing(costs, dates, forecast_days, confidence_level)
        elif algorithm == ForecastAlgorithm.LINEAR_REGRESSION:
            result = self._forecast_linear_regression(costs, dates, forecast_days, confidence_level)
        else:  # ENSEMBLE
            result = self._forecast_ensemble(costs, dates, forecast_days, confidence_level, seasonality)

        # Add anomalies and seasonality metadata
        result.anomalies = anomalies
        result.seasonality_detected = seasonality
        result.metadata = {
            "historical_days": len(daily_costs),
            "forecast_days": forecast_days,
            "confidence_level": confidence_level,
            "mean_daily_cost": float(np.mean(costs)),
            "std_daily_cost": float(np.std(costs)),
        }

        return result

    def _forecast_arima(
        self,
        costs: np.ndarray,
        dates: List[str],
        forecast_days: int,
        confidence_level: float,
        seasonality: bool
    ) -> ForecastResult:
        """ARIMA-style forecast using exponential smoothing with trend"""
        # Fit exponential smoothing
        alpha = 0.3  # Smoothing factor
        smoothed = np.zeros_like(costs)
        smoothed[0] = costs[0]

        for i in range(1, len(costs)):
            smoothed[i] = alpha * costs[i] + (1 - alpha) * smoothed[i - 1]

        # Calculate trend
        trend = np.polyfit(np.arange(len(costs)), costs, 1)[0]
        level = smoothed[-1]

        # Generate forecast
        forecast_points = []
        residuals = costs - smoothed
        forecast_std = np.std(residuals)

        # Z-score for confidence interval
        z_score = 1.96 if confidence_level >= 0.95 else 1.645

        last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
        for i in range(1, forecast_days + 1):
            pred_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            pred_cost = level + (trend * i)
            std_error = forecast_std * np.sqrt(i)

            forecast_points.append(ForecastPoint(
                date=pred_date,
                predicted_cost=max(0, float(pred_cost)),
                lower_bound=max(0, float(pred_cost - z_score * std_error)),
                upper_bound=float(pred_cost + z_score * std_error),
                confidence=confidence_level
            ))

        # Calculate metrics
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        mape = float(np.mean(np.abs(residuals / (costs + 1e-6))))
        trend_direction = "increasing" if trend > 0 else ("decreasing" if trend < 0 else "stable")

        return ForecastResult(
            algorithm="arima",
            forecast_points=forecast_points,
            rmse=rmse,
            mape=mape,
            trend=trend_direction,
            seasonality_detected=seasonality,
            anomalies=[],
            metadata={}
        )

    def _forecast_exponential_smoothing(
        self,
        costs: np.ndarray,
        dates: List[str],
        forecast_days: int,
        confidence_level: float
    ) -> ForecastResult:
        """Holt-Winters exponential smoothing forecast"""
        # Simple exponential smoothing with trend
        alpha = 0.2  # Level smoothing
        beta = 0.1   # Trend smoothing

        level = costs[0]
        trend = costs[1] - costs[0]
        forecast_points = []

        residuals = []
        for i in range(len(costs)):
            if i > 0:
                residuals.append(costs[i] - (level + trend))
            level_prev = level
            level = alpha * costs[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - level_prev) + (1 - beta) * trend

        forecast_std = np.std(residuals) if residuals else np.std(costs) * 0.1
        z_score = 1.96 if confidence_level >= 0.95 else 1.645

        last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
        for i in range(1, forecast_days + 1):
            pred_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            pred_cost = level + (trend * i)
            std_error = forecast_std * np.sqrt(i)

            forecast_points.append(ForecastPoint(
                date=pred_date,
                predicted_cost=max(0, float(pred_cost)),
                lower_bound=max(0, float(pred_cost - z_score * std_error)),
                upper_bound=float(pred_cost + z_score * std_error),
                confidence=confidence_level
            ))

        rmse = float(np.sqrt(np.mean(np.array(residuals) ** 2))) if residuals else 0.0
        mape = float(np.mean(np.abs(np.array(residuals) / (costs + 1e-6)))) if residuals else 0.0

        return ForecastResult(
            algorithm="exponential_smoothing",
            forecast_points=forecast_points,
            rmse=rmse,
            mape=mape,
            trend="increasing" if trend > 0 else ("decreasing" if trend < 0 else "stable"),
            seasonality_detected=False,
            anomalies=[],
            metadata={}
        )

    def _forecast_linear_regression(
        self,
        costs: np.ndarray,
        dates: List[str],
        forecast_days: int,
        confidence_level: float
    ) -> ForecastResult:
        """Simple linear regression forecast"""
        # Fit linear model
        x = np.arange(len(costs))
        coeffs = np.polyfit(x, costs, 1)
        poly = np.poly1d(coeffs)

        # Calculate residuals
        predictions = poly(x)
        residuals = costs - predictions
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        mape = float(np.mean(np.abs(residuals / (costs + 1e-6))))

        forecast_std = np.std(residuals)
        z_score = 1.96 if confidence_level >= 0.95 else 1.645

        # Generate forecast
        forecast_points = []
        last_date = datetime.strptime(dates[-1], "%Y-%m-%d")

        for i in range(1, forecast_days + 1):
            pred_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            x_val = len(costs) + i - 1
            pred_cost = poly(x_val)
            std_error = forecast_std * np.sqrt(1 + 1/len(costs) + (x_val - np.mean(x))**2 / np.sum((x - np.mean(x))**2))

            forecast_points.append(ForecastPoint(
                date=pred_date,
                predicted_cost=max(0, float(pred_cost)),
                lower_bound=max(0, float(pred_cost - z_score * std_error)),
                upper_bound=float(pred_cost + z_score * std_error),
                confidence=confidence_level
            ))

        return ForecastResult(
            algorithm="linear_regression",
            forecast_points=forecast_points,
            rmse=rmse,
            mape=mape,
            trend="increasing" if coeffs[0] > 0 else ("decreasing" if coeffs[0] < 0 else "stable"),
            seasonality_detected=False,
            anomalies=[],
            metadata={}
        )

    def _forecast_ensemble(
        self,
        costs: np.ndarray,
        dates: List[str],
        forecast_days: int,
        confidence_level: float,
        seasonality: bool
    ) -> ForecastResult:
        """Ensemble forecast combining multiple methods"""
        # Get individual forecasts
        arima_result = self._forecast_arima(costs, dates, forecast_days, confidence_level, seasonality)
        exp_result = self._forecast_exponential_smoothing(costs, dates, forecast_days, confidence_level)
        linear_result = self._forecast_linear_regression(costs, dates, forecast_days, confidence_level)

        # Weight by inverse of MAPE (lower error = higher weight)
        weights = [1/(arima_result.mape + 0.01), 1/(exp_result.mape + 0.01), 1/(linear_result.mape + 0.01)]
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]

        # Combine forecasts
        forecast_points = []
        for i in range(forecast_days):
            point = ForecastPoint(
                date=arima_result.forecast_points[i].date,
                predicted_cost=(
                    weights[0] * arima_result.forecast_points[i].predicted_cost +
                    weights[1] * exp_result.forecast_points[i].predicted_cost +
                    weights[2] * linear_result.forecast_points[i].predicted_cost
                ),
                lower_bound=min(
                    arima_result.forecast_points[i].lower_bound,
                    exp_result.forecast_points[i].lower_bound,
                    linear_result.forecast_points[i].lower_bound,
                ),
                upper_bound=max(
                    arima_result.forecast_points[i].upper_bound,
                    exp_result.forecast_points[i].upper_bound,
                    linear_result.forecast_points[i].upper_bound,
                ),
                confidence=confidence_level
            )
            forecast_points.append(point)

        # Ensemble metrics (average)
        avg_rmse = (arima_result.rmse + exp_result.rmse + linear_result.rmse) / 3
        avg_mape = (arima_result.mape + exp_result.mape + linear_result.mape) / 3

        return ForecastResult(
            algorithm="ensemble",
            forecast_points=forecast_points,
            rmse=avg_rmse,
            mape=avg_mape,
            trend=arima_result.trend,  # Use ARIMA's trend assessment
            seasonality_detected=seasonality,
            anomalies=[],
            metadata={"model_weights": {"arima": weights[0], "exponential": weights[1], "linear": weights[2]}}
        )

    def _detect_seasonality(self, costs: np.ndarray) -> bool:
        """Detect if data has seasonal patterns"""
        if len(costs) < 28:
            return False

        # Check for weekly seasonality (7-day cycle)
        weekly_pattern = costs[-7:] - np.mean(costs)
        if np.std(weekly_pattern) > np.std(costs) * 0.2:
            return True

        return False

    def _detect_anomalies(self, costs: np.ndarray, dates: List[str]) -> List[Tuple[str, float]]:
        """Detect anomalous cost spikes"""
        anomalies = []

        if len(costs) < 3:
            return anomalies

        # Calculate z-scores
        mean = np.mean(costs)
        std = np.std(costs)
        z_scores = np.abs((costs - mean) / (std + 1e-6))

        # Find anomalies (z-score > 2.5)
        for i, z in enumerate(z_scores):
            if z > 2.5:
                anomalies.append((dates[i], float(z)))

        return sorted(anomalies, key=lambda x: x[1], reverse=True)[:5]  # Top 5

    def _fallback_forecast(
        self,
        daily_costs: List[Tuple[str, float]],
        forecast_days: int
    ) -> ForecastResult:
        """Fallback forecast when insufficient historical data"""
        if not daily_costs:
            return ForecastResult(
                algorithm="fallback",
                forecast_points=[],
                rmse=0.0,
                mape=0.0,
                trend="stable",
                seasonality_detected=False,
                anomalies=[],
                metadata={"reason": "No historical data"}
            )

        avg_cost = np.mean([c[1] for c in daily_costs])
        last_date = datetime.strptime(daily_costs[-1][0], "%Y-%m-%d")

        forecast_points = []
        for i in range(1, forecast_days + 1):
            pred_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
            forecast_points.append(ForecastPoint(
                date=pred_date,
                predicted_cost=float(avg_cost),
                lower_bound=float(avg_cost * 0.8),
                upper_bound=float(avg_cost * 1.2),
                confidence=0.68
            ))

        return ForecastResult(
            algorithm="fallback",
            forecast_points=forecast_points,
            rmse=0.0,
            mape=0.0,
            trend="stable",
            seasonality_detected=False,
            anomalies=[],
            metadata={"reason": "Insufficient historical data (< 2 weeks)"}
        )

    def get_forecast_summary(self, forecast_result: ForecastResult) -> Dict:
        """Get summary statistics from forecast"""
        if not forecast_result.forecast_points:
            return {}

        predicted_costs = [p.predicted_cost for p in forecast_result.forecast_points]
        total_forecast = sum(predicted_costs)
        avg_daily = total_forecast / len(predicted_costs)

        return {
            "total_projected": float(total_forecast),
            "average_daily": float(avg_daily),
            "min_projected": float(min(predicted_costs)),
            "max_projected": float(max(predicted_costs)),
            "trend": forecast_result.trend,
            "confidence": forecast_result.forecast_points[0].confidence,
            "rmse": forecast_result.rmse,
            "mape": forecast_result.mape,
            "days_forecast": len(predicted_costs),
        }
