"""Market Regime Detection using Hidden Markov Models and ML"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from hmmlearn import hmm
from sklearn.preprocessing import StandardScaler

from ultracore.ml.base import BaseMLModel
from ..events import MarketDataReceivedEvent


class MarketRegimeDetector(BaseMLModel):
    """
    Detect market regimes using Hidden Markov Models.
    
    Market Regimes:
    1. Bull Market: Rising prices, low volatility
    2. Bear Market: Falling prices, high volatility
    3. High Volatility: Large price swings
    4. Low Volatility: Stable, range-bound
    5. Crisis: Extreme volatility, flight to safety
    
    Applications:
    - Adaptive trading strategies
    - Dynamic risk management
    - Portfolio rebalancing triggers
    - Stop-loss adjustment
    """
    
    def __init__(self, n_regimes: int = 5):
        super().__init__(
            model_name="market_regime_detector",
            model_type="regime_detection",
            version="1.0.0"
        )
        
        self.n_regimes = n_regimes
        
        # Gaussian HMM with n_regimes hidden states
        self.hmm_model = hmm.GaussianHMM(
            n_components=n_regimes,
            covariance_type="full",
            n_iter=1000,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        
        # Regime labels (learned from data)
        self.regime_labels = [
            "Bull Market",
            "Bear Market",
            "High Volatility",
            "Low Volatility",
            "Crisis"
        ]
    
    async def train(
        self,
        market_data_events: List[MarketDataReceivedEvent],
        lookback_window: int = 20
    ) -> Dict:
        """
        Train HMM on historical market data.
        
        Args:
            market_data_events: Historical market data
            lookback_window: Window size for feature calculation
        
        Returns:
            Training metrics
        """
        # Convert to DataFrame
        df = self._events_to_dataframe(market_data_events)
        
        # Calculate features
        features_df = self._calculate_regime_features(df, lookback_window)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features_df.values)
        
        # Train HMM
        self.hmm_model.fit(scaled_features)
        
        # Predict regimes on training data to label them
        predicted_regimes = self.hmm_model.predict(scaled_features)
        
        # Analyze characteristics of each regime
        regime_characteristics = self._analyze_regime_characteristics(
            features_df, predicted_regimes
        )
        
        # Assign meaningful labels based on characteristics
        self._assign_regime_labels(regime_characteristics)
        
        return {
            "n_regimes": self.n_regimes,
            "training_samples": len(scaled_features),
            "converged": self.hmm_model.monitor_.converged,
            "regime_characteristics": regime_characteristics,
            "regime_labels": self.regime_labels
        }
    
    async def detect_current_regime(
        self,
        recent_data: List[MarketDataReceivedEvent],
        lookback_window: int = 20
    ) -> Dict:
        """
        Detect current market regime.
        
        Args:
            recent_data: Recent market data
            lookback_window: Window size for feature calculation
        
        Returns:
            Current regime and transition probabilities
        """
        # Convert to DataFrame
        df = self._events_to_dataframe(recent_data)
        
        # Calculate features
        features_df = self._calculate_regime_features(df, lookback_window)
        
        # Scale features
        scaled_features = self.scaler.transform(features_df.values)
        
        # Predict regime
        predicted_regime = self.hmm_model.predict(scaled_features)[-1]
        
        # Get state probabilities
        log_prob, state_probs = self.hmm_model.score_samples(scaled_features)
        current_prob = state_probs[-1]
        
        # Get transition matrix
        transition_matrix = self.hmm_model.transmat_
        next_regime_probs = transition_matrix[predicted_regime]
        
        # Identify most likely next regime
        most_likely_next = int(np.argmax(next_regime_probs))
        
        return {
            "current_regime": self.regime_labels[predicted_regime],
            "regime_id": int(predicted_regime),
            "confidence": float(current_prob[predicted_regime]),
            "regime_probabilities": {
                self.regime_labels[i]: float(current_prob[i])
                for i in range(self.n_regimes)
            },
            "next_regime_probabilities": {
                self.regime_labels[i]: float(next_regime_probs[i])
                for i in range(self.n_regimes)
            },
            "most_likely_next_regime": self.regime_labels[most_likely_next],
            "transition_probability": float(next_regime_probs[most_likely_next]),
            "trading_recommendation": self._get_trading_recommendation(predicted_regime)
        }
    
    async def detect_regime_transition(
        self,
        recent_data: List[MarketDataReceivedEvent]
    ) -> Dict:
        """
        Detect if a regime transition is likely occurring.
        
        Returns:
            Transition detection results
        """
        # Get regime predictions over time
        df = self._events_to_dataframe(recent_data)
        features_df = self._calculate_regime_features(df, 20)
        scaled_features = self.scaler.transform(features_df.values)
        
        predicted_regimes = self.hmm_model.predict(scaled_features)
        
        # Check for recent regime changes
        recent_regimes = predicted_regimes[-10:]  # Last 10 periods
        
        if len(set(recent_regimes)) > 1:
            # Regime change detected
            prev_regime = recent_regimes[0]
            current_regime = recent_regimes[-1]
            
            transition_detected = prev_regime != current_regime
            
            return {
                "transition_detected": transition_detected,
                "from_regime": self.regime_labels[prev_regime],
                "to_regime": self.regime_labels[current_regime],
                "transition_strength": float(np.mean(recent_regimes != prev_regime)),
                "recommendation": self._get_transition_recommendation(prev_regime, current_regime)
            }
        
        return {
            "transition_detected": False,
            "current_regime": self.regime_labels[recent_regimes[-1]],
            "stability": "HIGH"
        }
    
    def _events_to_dataframe(self, events: List[MarketDataReceivedEvent]) -> pd.DataFrame:
        """Convert market data events to DataFrame."""
        data = []
        for event in events:
            data.append({
                "timestamp": event.timestamp,
                "price": float(event.last_price),
                "volume": event.volume,
                "vwap": float(event.vwap)
            })
        df = pd.DataFrame(data)
        df = df.sort_values("timestamp")
        return df
    
    def _calculate_regime_features(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Calculate features for regime detection."""
        features = pd.DataFrame(index=df.index)
        
        # Returns
        features["returns"] = df["price"].pct_change()
        
        # Volatility (rolling standard deviation of returns)
        features["volatility"] = features["returns"].rolling(window=window).std()
        
        # Trend (moving average slope)
        features["ma_short"] = df["price"].rolling(window=5).mean()
        features["ma_long"] = df["price"].rolling(window=20).mean()
        features["trend"] = (features["ma_short"] - features["ma_long"]) / features["ma_long"]
        
        # Volume trend
        features["volume_ma"] = df["volume"].rolling(window=window).mean()
        features["volume_ratio"] = df["volume"] / features["volume_ma"]
        
        # Price momentum
        features["momentum"] = df["price"].pct_change(periods=window)
        
        # RSI (Relative Strength Index)
        delta = df["price"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features["rsi"] = 100 - (100 / (1 + rs))
        
        # Drop NaN values
        features = features.dropna()
        
        return features
    
    def _analyze_regime_characteristics(
        self,
        features_df: pd.DataFrame,
        regimes: np.ndarray
    ) -> Dict:
        """Analyze characteristics of each regime."""
        characteristics = {}
        
        for regime_id in range(self.n_regimes):
            regime_mask = regimes == regime_id
            regime_data = features_df[regime_mask]
            
            characteristics[regime_id] = {
                "avg_return": float(regime_data["returns"].mean()),
                "avg_volatility": float(regime_data["volatility"].mean()),
                "avg_trend": float(regime_data["trend"].mean()),
                "avg_volume_ratio": float(regime_data["volume_ratio"].mean()),
                "frequency": float(regime_mask.sum() / len(regimes))
            }
        
        return characteristics
    
    def _assign_regime_labels(self, characteristics: Dict):
        """Assign meaningful labels to regimes based on characteristics."""
        # Sort regimes by key characteristics
        regimes_sorted = sorted(
            characteristics.items(),
            key=lambda x: (x[1]["avg_return"], -x[1]["avg_volatility"])
        )
        
        # Assign labels (this is simplified - in production would use more sophisticated logic)
        self.regime_labels = [""] * self.n_regimes
        
        for idx, (regime_id, chars) in enumerate(regimes_sorted):
            if chars["avg_volatility"] > 0.03:
                if chars["avg_return"] < -0.01:
                    self.regime_labels[regime_id] = "Crisis"
                else:
                    self.regime_labels[regime_id] = "High Volatility"
            elif chars["avg_return"] > 0.005:
                self.regime_labels[regime_id] = "Bull Market"
            elif chars["avg_return"] < -0.005:
                self.regime_labels[regime_id] = "Bear Market"
            else:
                self.regime_labels[regime_id] = "Low Volatility"
    
    def _get_trading_recommendation(self, regime_id: int) -> Dict:
        """Get trading recommendations for current regime."""
        recommendations = {
            "Bull Market": {
                "strategy": "LONG_BIAS",
                "risk_level": "MODERATE",
                "actions": ["Increase equity exposure", "Use trend-following strategies", "Set trailing stops"]
            },
            "Bear Market": {
                "strategy": "SHORT_BIAS",
                "risk_level": "HIGH",
                "actions": ["Reduce equity exposure", "Consider defensive sectors", "Tighten stop losses"]
            },
            "High Volatility": {
                "strategy": "VOLATILITY_TRADING",
                "risk_level": "HIGH",
                "actions": ["Reduce position sizes", "Use options for hedging", "Focus on high-quality stocks"]
            },
            "Low Volatility": {
                "strategy": "RANGE_TRADING",
                "risk_level": "LOW",
                "actions": ["Mean reversion strategies", "Income generation", "Wider stops acceptable"]
            },
            "Crisis": {
                "strategy": "DEFENSIVE",
                "risk_level": "EXTREME",
                "actions": ["Reduce all risk", "Flight to quality", "Preserve capital"]
            }
        }
        
        regime_label = self.regime_labels[regime_id]
        return recommendations.get(regime_label, {
            "strategy": "CAUTIOUS",
            "risk_level": "MODERATE",
            "actions": ["Monitor closely"]
        })
    
    def _get_transition_recommendation(self, from_regime: int, to_regime: int) -> str:
        """Get recommendations during regime transitions."""
        from_label = self.regime_labels[from_regime]
        to_label = self.regime_labels[to_regime]
        
        if "Crisis" in to_label:
            return "URGENT: Reduce risk immediately, move to defensive positions"
        elif "Bear" in to_label:
            return "Consider taking profits, increase cash position"
        elif "Bull" in to_label:
            return "Opportunity: Gradually increase equity exposure"
        else:
            return "Monitor transition, adjust risk accordingly"
