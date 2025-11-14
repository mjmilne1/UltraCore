"""
Dormancy Prediction Model
ML model to predict accounts at risk of becoming dormant
"""

import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import pickle
import os


class DormancyPredictor:
    """
    Dormancy Prediction Model
    
    Uses Random Forest to predict:
    - Dormancy risk score (0-100)
    - Days until likely dormancy
    - Recommended interventions
    
    Features:
    - Days since last transaction
    - Transaction frequency trends
    - Balance trends
    - Customer demographics
    - Product type
    - Seasonal patterns
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize predictor
        
        Args:
            model_path: Path to pre-trained model file (optional)
        """
        self.model = None
        self.model_path = model_path
        self.feature_names = [
            'days_since_last_transaction',
            'avg_days_between_transactions',
            'transaction_frequency_trend',  # Increasing or decreasing
            'current_balance',
            'balance_trend',  # Growing or declining
            'avg_transaction_amount',
            'account_age_months',
            'customer_age',
            'has_tfn',
            'product_type',
            'season',  # 0=summer, 1=autumn, 2=winter, 3=spring
        ]
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def predict_dormancy_risk(
        self,
        account_id: str,
        last_transaction_date: Optional[datetime],
        account_opened_date: datetime,
        transaction_history: List[Dict],
        current_balance: Decimal,
        customer_age: int,
        has_tfn: bool,
        product_type: str
    ) -> Dict:
        """
        Predict dormancy risk for an account
        
        Args:
            account_id: Account identifier
            last_transaction_date: Date of last transaction
            account_opened_date: Account opening date
            transaction_history: List of recent transactions
            current_balance: Current balance
            customer_age: Customer age
            has_tfn: Whether customer has provided TFN
            product_type: Type of savings product
        
        Returns:
            Risk assessment with score and recommendations
        """
        # Extract features
        features = self._extract_features(
            last_transaction_date=last_transaction_date,
            account_opened_date=account_opened_date,
            transaction_history=transaction_history,
            current_balance=current_balance,
            customer_age=customer_age,
            has_tfn=has_tfn,
            product_type=product_type,
        )
        
        # Make prediction
        if self.model:
            # Use trained model
            risk_score = self.model.predict([features])[0]
        else:
            # Use rule-based heuristic
            risk_score = self._heuristic_risk(features)
        
        # Calculate days until likely dormancy
        days_until_dormancy = self._estimate_days_until_dormancy(
            features, risk_score
        )
        
        # Generate interventions
        interventions = self._generate_interventions(
            features, risk_score, days_until_dormancy
        )
        
        # Categorize risk
        risk_category = self._categorize_risk(risk_score)
        
        return {
            "account_id": account_id,
            "risk_score": float(risk_score),
            "risk_category": risk_category,
            "days_until_dormancy": int(days_until_dormancy),
            "recommended_interventions": interventions,
            "features": {
                name: float(value)
                for name, value in zip(self.feature_names, features)
            },
        }
    
    def batch_predict(
        self,
        accounts: List[Dict]
    ) -> List[Dict]:
        """
        Predict dormancy risk for multiple accounts
        
        Args:
            accounts: List of account data dictionaries
        
        Returns:
            List of risk predictions
        """
        predictions = []
        
        for account in accounts:
            prediction = self.predict_dormancy_risk(
                account_id=account.get('account_id'),
                last_transaction_date=account.get('last_transaction_date'),
                account_opened_date=account.get('account_opened_date'),
                transaction_history=account.get('transaction_history', []),
                current_balance=account.get('current_balance', Decimal("0")),
                customer_age=account.get('customer_age', 30),
                has_tfn=account.get('has_tfn', False),
                product_type=account.get('product_type', 'savings'),
            )
            predictions.append(prediction)
        
        # Sort by risk score (highest first)
        predictions.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return predictions
    
    def _extract_features(
        self,
        last_transaction_date: Optional[datetime],
        account_opened_date: datetime,
        transaction_history: List[Dict],
        current_balance: Decimal,
        customer_age: int,
        has_tfn: bool,
        product_type: str
    ) -> List[float]:
        """Extract features for ML model"""
        
        # Days since last transaction
        if last_transaction_date:
            days_since_last = (datetime.utcnow() - last_transaction_date).days
        else:
            days_since_last = (datetime.utcnow() - account_opened_date).days
        
        # Account age
        account_age_months = (datetime.utcnow() - account_opened_date).days / 30
        
        # Transaction frequency metrics
        if len(transaction_history) >= 2:
            transaction_dates = [
                t.get('transaction_date') for t in transaction_history
            ]
            
            # Calculate days between transactions
            days_between = []
            for i in range(1, len(transaction_dates)):
                if isinstance(transaction_dates[i], str):
                    date_i = datetime.fromisoformat(transaction_dates[i])
                    date_prev = datetime.fromisoformat(transaction_dates[i-1])
                else:
                    date_i = transaction_dates[i]
                    date_prev = transaction_dates[i-1]
                days_between.append((date_i - date_prev).days)
            
            avg_days_between = np.mean(days_between)
            
            # Transaction frequency trend (negative = decreasing frequency)
            if len(days_between) >= 4:
                recent_avg = np.mean(days_between[-2:])
                older_avg = np.mean(days_between[:2])
                frequency_trend = (older_avg - recent_avg) / max(1, older_avg)
            else:
                frequency_trend = 0.0
        else:
            avg_days_between = days_since_last
            frequency_trend = 0.0
        
        # Balance trend
        if len(transaction_history) >= 2:
            balances = [float(t.get('balance_after', 0)) for t in transaction_history]
            balance_trend = (balances[-1] - balances[0]) / max(1, balances[0])
        else:
            balance_trend = 0.0
        
        # Average transaction amount
        if transaction_history:
            amounts = [abs(float(t.get('amount', 0))) for t in transaction_history]
            avg_transaction_amount = np.mean(amounts)
        else:
            avg_transaction_amount = 0.0
        
        # Product type encoding
        product_map = {
            'savings': 0,
            'high_interest_savings': 1,
            'youth_saver': 2,
            'pensioner_saver': 3,
            'business_savings': 4,
        }
        product_encoded = product_map.get(product_type.lower(), 0)
        
        # Season (Australian seasons)
        month = datetime.utcnow().month
        if month in [12, 1, 2]:
            season = 0  # Summer
        elif month in [3, 4, 5]:
            season = 1  # Autumn
        elif month in [6, 7, 8]:
            season = 2  # Winter
        else:
            season = 3  # Spring
        
        return [
            float(days_since_last),
            float(avg_days_between),
            float(frequency_trend),
            float(current_balance),
            float(balance_trend),
            float(avg_transaction_amount),
            float(account_age_months),
            float(customer_age),
            float(1 if has_tfn else 0),
            float(product_encoded),
            float(season),
        ]
    
    def _heuristic_risk(self, features: List[float]) -> float:
        """
        Calculate risk score using heuristics
        
        Used when ML model is not trained yet.
        """
        days_since_last, avg_days_between, freq_trend, balance, balance_trend, \
        avg_amount, account_age, customer_age, has_tfn, product_type, season = features
        
        risk_score = 0.0
        
        # Days since last transaction (most important factor)
        if days_since_last > 300:
            risk_score += 50
        elif days_since_last > 180:
            risk_score += 35
        elif days_since_last > 90:
            risk_score += 20
        elif days_since_last > 60:
            risk_score += 10
        
        # Transaction frequency
        if avg_days_between > 90:
            risk_score += 20
        elif avg_days_between > 60:
            risk_score += 10
        
        # Frequency trend (decreasing = higher risk)
        if freq_trend < -0.5:  # Frequency decreasing significantly
            risk_score += 15
        elif freq_trend < 0:
            risk_score += 5
        
        # Balance trend (declining = higher risk)
        if balance_trend < -0.2:  # Balance declining
            risk_score += 10
        
        # Low balance (less incentive to maintain account)
        if balance < 100:
            risk_score += 10
        elif balance < 1000:
            risk_score += 5
        
        # Account age (very old inactive accounts = higher risk)
        if account_age > 24 and days_since_last > 180:
            risk_score += 10
        
        # No TFN (less committed customer)
        if not has_tfn:
            risk_score += 5
        
        return min(100, risk_score)
    
    def _estimate_days_until_dormancy(
        self,
        features: List[float],
        risk_score: float
    ) -> int:
        """Estimate days until account becomes dormant"""
        
        days_since_last = features[0]
        avg_days_between = features[1]
        
        # Dormancy threshold is typically 365 days
        dormancy_threshold = 365
        days_remaining = dormancy_threshold - days_since_last
        
        if days_remaining <= 0:
            return 0
        
        # Adjust based on risk score
        if risk_score > 75:
            # High risk - likely to become dormant sooner
            return max(0, int(days_remaining * 0.5))
        elif risk_score > 50:
            return max(0, int(days_remaining * 0.75))
        else:
            return max(0, int(days_remaining))
    
    def _generate_interventions(
        self,
        features: List[float],
        risk_score: float,
        days_until_dormancy: int
    ) -> List[Dict]:
        """Generate recommended interventions"""
        
        interventions = []
        
        days_since_last = features[0]
        balance = features[3]
        
        if risk_score > 75:
            # Critical risk
            interventions.extend([
                {
                    "priority": "critical",
                    "action": "immediate_contact",
                    "description": "Contact customer immediately via email and SMS",
                    "expected_impact": "high",
                },
                {
                    "priority": "critical",
                    "action": "special_offer",
                    "description": "Offer bonus interest rate for next 3 months",
                    "expected_impact": "high",
                },
                {
                    "priority": "high",
                    "action": "auto_transfer_setup",
                    "description": "Help customer set up automatic transfers",
                    "expected_impact": "medium",
                },
            ])
        
        elif risk_score > 50:
            # High risk
            interventions.extend([
                {
                    "priority": "high",
                    "action": "reminder_email",
                    "description": "Send reminder email about account benefits",
                    "expected_impact": "medium",
                },
                {
                    "priority": "medium",
                    "action": "savings_goal_prompt",
                    "description": "Prompt customer to set up savings goals",
                    "expected_impact": "medium",
                },
            ])
        
        elif risk_score > 25:
            # Medium risk
            interventions.extend([
                {
                    "priority": "medium",
                    "action": "engagement_campaign",
                    "description": "Include in monthly engagement campaign",
                    "expected_impact": "low",
                },
                {
                    "priority": "low",
                    "action": "financial_tips",
                    "description": "Send personalized financial tips",
                    "expected_impact": "low",
                },
            ])
        
        return interventions
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk score"""
        if risk_score >= 75:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 25:
            return "medium"
        else:
            return "low"
    
    def train_model(self, training_data: List[Dict]):
        """
        Train the ML model
        
        Args:
            training_data: List of training examples with features and labels
        """
        # TODO: Implement Random Forest training
        pass
    
    def load_model(self, model_path: str):
        """Load pre-trained model"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def save_model(self, model_path: str):
        """Save trained model"""
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
