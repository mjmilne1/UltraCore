"""Anomaly Detection for Trading Fraud and Market Manipulation"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn

from ultracore.ml.base import BaseMLModel
from ..events import OrderPlacedEvent, OrderExecutedEvent, MarketDataReceivedEvent


class AutoencoderAnomalyDetector(nn.Module):
    """Deep autoencoder for anomaly detection in trading patterns."""
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        super(AutoencoderAnomalyDetector, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class TradingAnomalyDetector(BaseMLModel):
    """
    ML-based anomaly detection for identifying:
    - Fraudulent trading patterns
    - Market manipulation attempts
    - Unusual trading behavior
    - System errors or bugs
    - Account compromise indicators
    
    Uses both:
    - Isolation Forest for traditional anomaly detection
    - Deep Autoencoders for complex pattern recognition
    """
    
    def __init__(self):
        super().__init__(
            model_name="trading_anomaly_detector",
            model_type="anomaly_detection",
            version="1.0.0"
        )
        
        # Isolation Forest for traditional anomaly detection
        self.isolation_forest = IsolationForest(
            contamination=0.01,  # Expect 1% anomalies
            random_state=42,
            n_estimators=200
        )
        
        # Deep autoencoder for complex patterns
        self.input_dim = 20  # Feature dimension
        self.autoencoder = AutoencoderAnomalyDetector(
            input_dim=self.input_dim,
            encoding_dim=8
        )
        
        self.scaler = StandardScaler()
        self.reconstruction_threshold = 0.1  # Will be calibrated during training
    
    async def train(
        self,
        normal_trades: List[OrderExecutedEvent],
        epochs: int = 50
    ) -> Dict:
        """
        Train on normal trading patterns to learn what's normal.
        
        Args:
            normal_trades: Historical trades known to be legitimate
            epochs: Training epochs for autoencoder
        
        Returns:
            Training metrics
        """
        # Extract features from normal trades
        features = self._extract_features(normal_trades)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Train Isolation Forest
        self.isolation_forest.fit(scaled_features)
        
        # Train Autoencoder
        X_tensor = torch.FloatTensor(scaled_features)
        optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        losses = []
        for epoch in range(epochs):
            self.autoencoder.train()
            
            # Forward pass
            reconstructed = self.autoencoder(X_tensor)
            loss = criterion(reconstructed, X_tensor)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
        
        # Calibrate reconstruction threshold (95th percentile of reconstruction errors)
        self.autoencoder.eval()
        with torch.no_grad():
            reconstructed = self.autoencoder(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).numpy()
            self.reconstruction_threshold = np.percentile(reconstruction_errors, 95)
        
        return {
            "final_loss": losses[-1],
            "reconstruction_threshold": float(self.reconstruction_threshold),
            "training_samples": len(features)
        }
    
    async def detect_anomaly(
        self,
        trade_event: OrderExecutedEvent,
        recent_trades: Optional[List[OrderExecutedEvent]] = None
    ) -> Dict:
        """
        Detect if a trade is anomalous.
        
        Args:
            trade_event: Trade to analyze
            recent_trades: Recent trading history for context
        
        Returns:
            Anomaly detection results with risk score
        """
        # Extract features
        features = self._extract_single_trade_features(trade_event, recent_trades)
        scaled_features = self.scaler.transform([features])
        
        # Isolation Forest detection
        isolation_score = self.isolation_forest.score_samples(scaled_features)[0]
        is_anomaly_if = self.isolation_forest.predict(scaled_features)[0] == -1
        
        # Autoencoder detection
        self.autoencoder.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(scaled_features)
            reconstructed = self.autoencoder(X_tensor)
            reconstruction_error = torch.mean((X_tensor - reconstructed) ** 2).item()
        
        is_anomaly_ae = reconstruction_error > self.reconstruction_threshold
        
        # Combined decision (both models agree = high confidence)
        is_anomaly = is_anomaly_if or is_anomaly_ae
        confidence = 0.9 if (is_anomaly_if and is_anomaly_ae) else 0.6
        
        # Calculate anomaly score (0-100)
        anomaly_score = (
            (1 - isolation_score) * 50 +  # Normalize IF score
            (reconstruction_error / self.reconstruction_threshold) * 50
        )
        anomaly_score = min(100, max(0, anomaly_score))
        
        # Identify specific anomaly patterns
        anomaly_reasons = self._identify_anomaly_reasons(trade_event, features)
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": float(anomaly_score),
            "confidence": confidence,
            "detection_methods": {
                "isolation_forest": is_anomaly_if,
                "autoencoder": is_anomaly_ae,
                "reconstruction_error": float(reconstruction_error)
            },
            "anomaly_reasons": anomaly_reasons,
            "risk_level": "HIGH" if anomaly_score > 80 else "MEDIUM" if anomaly_score > 50 else "LOW",
            "recommended_action": self._get_recommended_action(anomaly_score)
        }
    
    async def detect_market_manipulation(
        self,
        symbol: str,
        trades: List[OrderExecutedEvent],
        market_data: List[MarketDataReceivedEvent]
    ) -> Dict:
        """
        Detect potential market manipulation patterns.
        
        Patterns detected:
        - Spoofing (placing and quickly canceling large orders)
        - Layering (multiple orders at different prices)
        - Wash trading (self-trading)
        - Pump and dump
        - Unusual volume spikes
        """
        manipulation_signals = []
        
        # Check for unusual volume
        volumes = [md.volume for md in market_data]
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        for md in market_data[-10:]:  # Check last 10 data points
            if md.volume > avg_volume + 3 * std_volume:
                manipulation_signals.append({
                    "type": "unusual_volume",
                    "severity": "HIGH",
                    "details": f"Volume spike: {md.volume} vs avg {avg_volume:.0f}"
                })
        
        # Check for rapid price movements
        prices = [md.last_price for md in market_data]
        price_changes = np.diff(prices) / prices[:-1] * 100
        
        for i, change in enumerate(price_changes[-10:]):
            if abs(change) > 5:  # 5% move
                manipulation_signals.append({
                    "type": "rapid_price_movement",
                    "severity": "MEDIUM",
                    "details": f"Price moved {change:.2f}% rapidly"
                })
        
        # Check for wash trading patterns (simplified)
        trade_times = [t.executed_at for t in trades]
        if len(trade_times) > 1:
            time_diffs = [(trade_times[i+1] - trade_times[i]).total_seconds() 
                         for i in range(len(trade_times)-1)]
            
            # Many trades in rapid succession
            if len([d for d in time_diffs if d < 1.0]) > 10:
                manipulation_signals.append({
                    "type": "potential_wash_trading",
                    "severity": "HIGH",
                    "details": "Multiple rapid trades detected"
                })
        
        manipulation_detected = len(manipulation_signals) > 0
        
        return {
            "manipulation_detected": manipulation_detected,
            "symbol": symbol,
            "signals": manipulation_signals,
            "risk_score": len(manipulation_signals) * 25,  # Max 100
            "recommended_action": "ALERT_COMPLIANCE" if manipulation_detected else "CONTINUE_MONITORING"
        }
    
    def _extract_features(self, trades: List[OrderExecutedEvent]) -> np.ndarray:
        """Extract feature matrix from trades."""
        features = []
        for trade in trades:
            features.append(self._extract_single_trade_features(trade, None))
        return np.array(features)
    
    def _extract_single_trade_features(
        self,
        trade: OrderExecutedEvent,
        recent_trades: Optional[List[OrderExecutedEvent]]
    ) -> np.ndarray:
        """Extract features for a single trade."""
        features = [
            float(trade.quantity),
            float(trade.price),
            float(trade.net_value),
            float(trade.commission),
            1.0 if trade.side == "BUY" else 0.0,
            trade.executed_at.hour,  # Time of day
            trade.executed_at.weekday(),  # Day of week
        ]
        
        # Add statistical features if recent trades available
        if recent_trades:
            recent_values = [float(t.net_value) for t in recent_trades[-20:]]
            features.extend([
                np.mean(recent_values) if recent_values else 0,
                np.std(recent_values) if recent_values else 0,
                float(trade.net_value) / np.mean(recent_values) if recent_values and np.mean(recent_values) > 0 else 1.0
            ])
        else:
            features.extend([0, 0, 1.0])
        
        # Pad to input_dim
        while len(features) < self.input_dim:
            features.append(0.0)
        
        return np.array(features[:self.input_dim])
    
    def _identify_anomaly_reasons(
        self,
        trade: OrderExecutedEvent,
        features: np.ndarray
    ) -> List[str]:
        """Identify specific reasons for anomaly."""
        reasons = []
        
        # Large trade
        if trade.quantity > 10000:
            reasons.append("Unusually large quantity")
        
        # High value
        if float(trade.net_value) > 100000:
            reasons.append("High trade value")
        
        # Unusual time
        if trade.executed_at.hour < 6 or trade.executed_at.hour > 20:
            reasons.append("Trading outside normal hours")
        
        return reasons or ["General pattern anomaly detected"]
    
    def _get_recommended_action(self, anomaly_score: float) -> str:
        """Get recommended action based on anomaly score."""
        if anomaly_score > 80:
            return "BLOCK_AND_INVESTIGATE"
        elif anomaly_score > 50:
            return "FLAG_FOR_REVIEW"
        else:
            return "LOG_AND_MONITOR"
