"""Simplified ML Pipeline - Self-Contained"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import Dict
import yfinance as yf

class FinancialMLPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.models = {}
        self.training_data = {}  # Store training data
    
    def _get_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features from raw data"""
        df = df.copy()
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['volatility_5'] = df['returns'].rolling(window=5).std()
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['ema_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['rsi'] = self._calculate_rsi(df['Close'])
        df['volume_sma'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma']
        return df.dropna()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    async def train_price_predictor(self, ticker: str) -> Dict:
        # Fetch fresh data directly
        stock = yf.Ticker(ticker)
        df = stock.history(period="2y")
        
        # Calculate features
        df = self._get_features(df)
        
        # Store for later use
        self.training_data[ticker] = df
        
        features = ['returns', 'log_returns', 'volatility_5', 'volatility_20',
                   'sma_5', 'sma_20', 'sma_50', 'macd', 'rsi', 'volume_ratio']
        
        X = df[features].values
        y = df['Close'].values
        
        X_scaled = self.scaler.fit_transform(X)
        
        split = int(0.8 * len(X))
        X_train, X_test = X_scaled[:split], X_scaled[split:]
        y_train, y_test = y[:split], y[split:]
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        self.models[ticker] = model
        
        return {
            "ticker": ticker,
            "model_type": "random_forest_enhanced",
            "train_score": float(model.score(X_train, y_train)),
            "test_score": float(model.score(X_test, y_test)),
            "status": "trained",
            "records": len(df)
        }
    
    async def predict_next_price(self, ticker: str) -> float:
        # Ensure model exists
        if ticker not in self.models:
            await self.train_price_predictor(ticker)
        
        # Get fresh data for prediction
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        df = self._get_features(df)
        
        features = ['returns', 'log_returns', 'volatility_5', 'volatility_20',
                   'sma_5', 'sma_20', 'sma_50', 'macd', 'rsi', 'volume_ratio']
        
        latest = df[features].iloc[-1:].values
        scaled = self.scaler.transform(latest)
        
        return float(self.models[ticker].predict(scaled)[0])

ml_pipeline = FinancialMLPipeline()
