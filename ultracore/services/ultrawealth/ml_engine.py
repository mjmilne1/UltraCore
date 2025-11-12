"""
Advanced ML Engine for ETF Predictions
Fixed feature engineering order
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

class MLPredictionEngine:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_metadata = {}
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced feature engineering - calculate in correct order"""
        df = df.copy()
        
        # Price-based features
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Moving averages (calculate BEFORE using them)
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_10'] = df['Close'].rolling(window=10).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        
        # EMAs (calculate BEFORE using them)
        df['ema_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # Now we can calculate MACD (uses ema_12 and ema_26)
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Volatility
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        df['volatility_50'] = df['returns'].rolling(window=50).std()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['Close'])
        
        # Volume indicators
        df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']
        
        # Bollinger Bands
        df['bb_middle'] = df['Close'].rolling(window=20).mean()
        df['bb_std'] = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
        df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df.dropna()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    async def train_model(self, ticker: str, df: pd.DataFrame) -> Dict:
        """Train ensemble model for a ticker"""
        
        # Feature engineering
        df_features = self._engineer_features(df)
        
        # Select features (only use ones that exist)
        feature_cols = [
            'returns', 'log_returns', 'volatility_20', 'volatility_50',
            'sma_20', 'sma_50', 'macd', 'rsi',
            'volume_ratio', 'bb_position'
        ]
        
        X = df_features[feature_cols].values
        y = df_features['Close'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train-test split
        split = int(0.8 * len(X))
        X_train, X_test = X_scaled[:split], X_scaled[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Train ensemble of models
        rf_model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
        gb_model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        
        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)
        
        # Evaluate
        rf_score = rf_model.score(X_test, y_test)
        gb_score = gb_model.score(X_test, y_test)
        
        # Store models
        self.models[ticker] = {
            'rf': rf_model,
            'gb': gb_model,
            'features': feature_cols
        }
        self.scalers[ticker] = scaler
        
        self.model_metadata[ticker] = {
            'trained_at': pd.Timestamp.now().isoformat(),
            'rf_score': float(rf_score),
            'gb_score': float(gb_score),
            'ensemble_score': float((rf_score + gb_score) / 2),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        return self.model_metadata[ticker]
    
    async def predict(self, ticker: str, df: pd.DataFrame) -> Dict:
        """Make ensemble prediction"""
        
        if ticker not in self.models:
            await self.train_model(ticker, df)
        
        # Feature engineering
        df_features = self._engineer_features(df)
        feature_cols = self.models[ticker]['features']
        
        # Get latest features
        X_latest = df_features[feature_cols].iloc[-1:].values
        X_scaled = self.scalers[ticker].transform(X_latest)
        
        # Ensemble prediction
        rf_pred = self.models[ticker]['rf'].predict(X_scaled)[0]
        gb_pred = self.models[ticker]['gb'].predict(X_scaled)[0]
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        current_price = df['Close'].iloc[-1]
        
        return {
            'ticker': ticker,
            'current_price': float(current_price),
            'rf_prediction': float(rf_pred),
            'gb_prediction': float(gb_pred),
            'ensemble_prediction': float(ensemble_pred),
            'predicted_change_pct': float(((ensemble_pred - current_price) / current_price) * 100),
            'confidence': self.model_metadata[ticker]['ensemble_score']
        }

ml_engine = MLPredictionEngine()
