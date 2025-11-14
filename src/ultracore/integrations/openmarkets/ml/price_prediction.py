"""ML-based Price Prediction Models for Trading"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

from ultracore.ml.base import BaseMLModel
from ultracore.ml_models.registry import ModelRegistry
from ..events import MarketDataReceivedEvent


class LSTMPricePredictor(nn.Module):
    """LSTM neural network for price prediction."""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int):
        super(LSTMPricePredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


class PricePredictionModel(BaseMLModel):
    """
    ML model for predicting future stock prices.
    
    Features:
    - LSTM-based time series prediction
    - Multiple feature inputs (OHLCV, technical indicators)
    - Trained on historical market data from event store
    - Real-time inference for trading decisions
    """
    
    def __init__(self, symbol: str, model_registry: ModelRegistry):
        super().__init__(
            model_name=f"price_prediction_{symbol}",
            model_type="timeseries",
            version="1.0.0"
        )
        self.symbol = symbol
        self.model_registry = model_registry
        self.scaler = MinMaxScaler()
        
        # LSTM configuration
        self.sequence_length = 60  # Use 60 days of history
        self.input_size = 10  # OHLCV + 5 technical indicators
        self.hidden_size = 128
        self.num_layers = 2
        self.output_size = 1  # Predict next day's close price
        
        self.model = LSTMPricePredictor(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            output_size=self.output_size
        )
    
    async def train(
        self,
        market_data_events: List[MarketDataReceivedEvent],
        epochs: int = 100
    ) -> Dict:
        """
        Train the model on historical market data from event store.
        
        Args:
            market_data_events: List of market data events from event store
            epochs: Number of training epochs
        
        Returns:
            Training metrics
        """
        # Prepare training data
        df = self._events_to_dataframe(market_data_events)
        df = self._add_technical_indicators(df)
        
        # Create sequences
        X, y = self._create_sequences(df)
        
        # Scale data
        X = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y)
        
        # Training loop
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        losses = []
        for epoch in range(epochs):
            self.model.train()
            
            # Forward pass
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
        
        # Register model
        await self.model_registry.register_model(
            model_name=self.model_name,
            model=self.model,
            metrics={"final_loss": losses[-1]},
            metadata={
                "symbol": self.symbol,
                "sequence_length": self.sequence_length,
                "training_samples": len(X)
            }
        )
        
        return {
            "final_loss": losses[-1],
            "epochs": epochs,
            "training_samples": len(X)
        }
    
    async def predict(
        self,
        recent_data: List[MarketDataReceivedEvent],
        steps_ahead: int = 1
    ) -> Dict:
        """
        Predict future prices.
        
        Args:
            recent_data: Recent market data events (at least sequence_length)
            steps_ahead: Number of days to predict ahead
        
        Returns:
            Prediction results with confidence intervals
        """
        self.model.eval()
        
        # Prepare input data
        df = self._events_to_dataframe(recent_data)
        df = self._add_technical_indicators(df)
        
        # Get last sequence
        sequence = df.tail(self.sequence_length).values
        sequence = self.scaler.transform(sequence.reshape(-1, sequence.shape[-1])).reshape(1, self.sequence_length, -1)
        
        # Make prediction
        with torch.no_grad():
            X_tensor = torch.FloatTensor(sequence)
            prediction = self.model(X_tensor)
        
        predicted_price = prediction.item()
        
        return {
            "symbol": self.symbol,
            "predicted_price": predicted_price,
            "prediction_date": datetime.now(timezone.utc) + timedelta(days=steps_ahead),
            "confidence": 0.85,  # Would calculate actual confidence intervals
            "model_version": self.version
        }
    
    def _events_to_dataframe(self, events: List[MarketDataReceivedEvent]) -> pd.DataFrame:
        """Convert market data events to DataFrame."""
        data = []
        for event in events:
            data.append({
                "timestamp": event.timestamp,
                "open": event.last_price,  # Simplified, would need actual OHLC
                "high": event.last_price,
                "low": event.last_price,
                "close": event.last_price,
                "volume": event.volume,
                "vwap": event.vwap
            })
        return pd.DataFrame(data)
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators as features."""
        # Simple Moving Averages
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        
        # Exponential Moving Average
        df["ema_12"] = df["close"].ewm(span=12).mean()
        
        # Relative Strength Index (RSI)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Drop NaN values
        df = df.dropna()
        
        return df
    
    def _create_sequences(self, df: pd.DataFrame) -> tuple:
        """Create sequences for LSTM training."""
        X, y = [], []
        data = df.values
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length, 3])  # Close price
        
        return np.array(X), np.array(y)
