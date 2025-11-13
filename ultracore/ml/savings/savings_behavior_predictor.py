"""
Savings Behavior Prediction Model
ML model to predict customer savings patterns and propensity
"""

import numpy as np
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pickle
import os


class SavingsBehaviorPredictor:
    """
    Savings Behavior Prediction Model
    
    Uses XGBoost to predict:
    - Savings propensity score (0-100)
    - Recommended monthly deposit amount
    - Likelihood of maintaining regular deposits
    - Product affinity scores
    
    Features:
    - Customer demographics (age, income, employment)
    - Transaction history (deposits, withdrawals, frequency)
    - Balance trends (growth rate, volatility)
    - Product usage patterns
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
            'age',
            'monthly_income',
            'employment_status',  # 0=unemployed, 1=employed, 2=self-employed
            'current_balance',
            'avg_monthly_deposit',
            'deposit_frequency',  # deposits per month
            'avg_monthly_withdrawal',
            'withdrawal_frequency',  # withdrawals per month
            'balance_growth_rate',  # % growth per month
            'balance_volatility',  # std dev of daily balances
            'account_age_months',
            'has_tfn',  # 0=no, 1=yes
            'product_type',  # 0=savings, 1=high_interest, 2=youth, etc.
        ]
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def predict_savings_propensity(
        self,
        age: int,
        monthly_income: Decimal,
        employment_status: str,
        current_balance: Decimal,
        transaction_history: List[Dict],
        account_age_months: int,
        has_tfn: bool,
        product_type: str
    ) -> Dict:
        """
        Predict savings propensity and recommended deposit amount
        
        Args:
            age: Customer age
            monthly_income: Monthly income
            employment_status: Employment status (unemployed, employed, self_employed)
            current_balance: Current savings balance
            transaction_history: List of recent transactions
            account_age_months: Account age in months
            has_tfn: Whether customer has provided TFN
            product_type: Type of savings product
        
        Returns:
            Prediction with propensity score and recommendations
        """
        # Extract features from transaction history
        features = self._extract_features(
            age=age,
            monthly_income=monthly_income,
            employment_status=employment_status,
            current_balance=current_balance,
            transaction_history=transaction_history,
            account_age_months=account_age_months,
            has_tfn=has_tfn,
            product_type=product_type,
        )
        
        # Make prediction
        if self.model:
            # Use trained model
            propensity_score = self.model.predict([features])[0]
        else:
            # Use rule-based heuristic if model not trained
            propensity_score = self._heuristic_propensity(features)
        
        # Calculate recommended deposit amount
        recommended_deposit = self._calculate_recommended_deposit(
            monthly_income=monthly_income,
            current_balance=current_balance,
            propensity_score=propensity_score,
        )
        
        # Generate insights
        insights = self._generate_insights(features, propensity_score)
        
        return {
            "propensity_score": float(propensity_score),
            "propensity_category": self._categorize_propensity(propensity_score),
            "recommended_monthly_deposit": float(recommended_deposit),
            "insights": insights,
            "features": {
                name: float(value)
                for name, value in zip(self.feature_names, features)
            },
        }
    
    def predict_deposit_consistency(
        self,
        transaction_history: List[Dict],
        months_to_predict: int = 3
    ) -> Dict:
        """
        Predict likelihood of maintaining regular deposits
        
        Args:
            transaction_history: List of recent transactions
            months_to_predict: Number of months to predict
        
        Returns:
            Prediction of deposit consistency
        """
        # Analyze deposit patterns
        deposits = [
            t for t in transaction_history
            if t.get('transaction_type') == 'deposit'
        ]
        
        if len(deposits) < 3:
            return {
                "consistency_score": 0.0,
                "likelihood": "low",
                "reason": "Insufficient transaction history",
            }
        
        # Calculate deposit regularity
        deposit_amounts = [float(d.get('amount', 0)) for d in deposits]
        deposit_dates = [d.get('transaction_date') for d in deposits]
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_deposit = np.mean(deposit_amounts)
        std_deposit = np.std(deposit_amounts)
        cv = std_deposit / mean_deposit if mean_deposit > 0 else 1.0
        
        # Calculate time regularity
        if len(deposit_dates) >= 2:
            time_diffs = []
            for i in range(1, len(deposit_dates)):
                if isinstance(deposit_dates[i], str):
                    date_i = datetime.fromisoformat(deposit_dates[i])
                    date_prev = datetime.fromisoformat(deposit_dates[i-1])
                else:
                    date_i = deposit_dates[i]
                    date_prev = deposit_dates[i-1]
                time_diffs.append((date_i - date_prev).days)
            
            avg_days_between = np.mean(time_diffs)
            std_days_between = np.std(time_diffs)
            time_cv = std_days_between / avg_days_between if avg_days_between > 0 else 1.0
        else:
            time_cv = 1.0
        
        # Calculate consistency score (0-100)
        # Lower CV = higher consistency
        amount_consistency = max(0, 100 - (cv * 100))
        time_consistency = max(0, 100 - (time_cv * 50))
        consistency_score = (amount_consistency + time_consistency) / 2
        
        # Categorize likelihood
        if consistency_score >= 75:
            likelihood = "high"
        elif consistency_score >= 50:
            likelihood = "medium"
        elif consistency_score >= 25:
            likelihood = "low"
        else:
            likelihood = "very_low"
        
        return {
            "consistency_score": float(consistency_score),
            "likelihood": likelihood,
            "average_deposit": float(mean_deposit),
            "deposit_variability": float(cv),
            "average_days_between_deposits": float(avg_days_between) if len(deposit_dates) >= 2 else None,
            "recommendation": self._get_consistency_recommendation(likelihood),
        }
    
    def _extract_features(
        self,
        age: int,
        monthly_income: Decimal,
        employment_status: str,
        current_balance: Decimal,
        transaction_history: List[Dict],
        account_age_months: int,
        has_tfn: bool,
        product_type: str
    ) -> List[float]:
        """Extract features for ML model"""
        
        # Employment status encoding
        employment_map = {
            'unemployed': 0,
            'employed': 1,
            'self_employed': 2,
        }
        employment_encoded = employment_map.get(employment_status.lower(), 0)
        
        # Product type encoding
        product_map = {
            'savings': 0,
            'high_interest_savings': 1,
            'youth_saver': 2,
            'pensioner_saver': 3,
            'business_savings': 4,
        }
        product_encoded = product_map.get(product_type.lower(), 0)
        
        # Calculate transaction metrics
        deposits = [t for t in transaction_history if t.get('transaction_type') == 'deposit']
        withdrawals = [t for t in transaction_history if t.get('transaction_type') == 'withdrawal']
        
        avg_monthly_deposit = np.mean([float(d.get('amount', 0)) for d in deposits]) if deposits else 0.0
        deposit_frequency = len(deposits) / max(1, account_age_months)
        
        avg_monthly_withdrawal = np.mean([float(w.get('amount', 0)) for w in withdrawals]) if withdrawals else 0.0
        withdrawal_frequency = len(withdrawals) / max(1, account_age_months)
        
        # Calculate balance growth rate
        if transaction_history:
            initial_balance = float(transaction_history[0].get('balance_before', current_balance))
            balance_growth_rate = (
                (float(current_balance) - initial_balance) / max(1, initial_balance) * 100
            ) / max(1, account_age_months)
        else:
            balance_growth_rate = 0.0
        
        # Calculate balance volatility
        balances = [float(t.get('balance_after', current_balance)) for t in transaction_history]
        balance_volatility = np.std(balances) if len(balances) > 1 else 0.0
        
        return [
            float(age),
            float(monthly_income),
            float(employment_encoded),
            float(current_balance),
            float(avg_monthly_deposit),
            float(deposit_frequency),
            float(avg_monthly_withdrawal),
            float(withdrawal_frequency),
            float(balance_growth_rate),
            float(balance_volatility),
            float(account_age_months),
            float(1 if has_tfn else 0),
            float(product_encoded),
        ]
    
    def _heuristic_propensity(self, features: List[float]) -> float:
        """
        Calculate propensity score using heuristics
        
        Used when ML model is not trained yet.
        """
        age, monthly_income, employment, balance, avg_deposit, deposit_freq, \
        avg_withdrawal, withdrawal_freq, growth_rate, volatility, account_age, \
        has_tfn, product_type = features
        
        score = 50.0  # Base score
        
        # Income factor (higher income = higher propensity)
        if monthly_income > 10000:
            score += 15
        elif monthly_income > 5000:
            score += 10
        elif monthly_income > 2000:
            score += 5
        
        # Employment factor
        if employment == 1:  # Employed
            score += 10
        elif employment == 2:  # Self-employed
            score += 5
        
        # Balance factor
        if balance > 50000:
            score += 10
        elif balance > 10000:
            score += 5
        
        # Deposit behavior factor
        if avg_deposit > 1000:
            score += 10
        elif avg_deposit > 500:
            score += 5
        
        if deposit_freq > 2:  # More than 2 deposits per month
            score += 10
        elif deposit_freq > 1:
            score += 5
        
        # Growth factor
        if growth_rate > 5:  # 5% monthly growth
            score += 10
        elif growth_rate > 2:
            score += 5
        
        # Penalty for high withdrawals
        if withdrawal_freq > deposit_freq:
            score -= 10
        
        # TFN bonus (shows commitment)
        if has_tfn:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_recommended_deposit(
        self,
        monthly_income: Decimal,
        current_balance: Decimal,
        propensity_score: float
    ) -> Decimal:
        """Calculate recommended monthly deposit amount"""
        
        # Base recommendation: 10-20% of income based on propensity
        base_percentage = Decimal("0.10") + (Decimal(propensity_score) / Decimal("1000"))
        recommended = monthly_income * base_percentage
        
        # Adjust based on current balance
        if current_balance < Decimal("1000"):
            # Encourage building emergency fund
            recommended = max(recommended, Decimal("100"))
        
        return recommended.quantize(Decimal("0.01"))
    
    def _categorize_propensity(self, score: float) -> str:
        """Categorize propensity score"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "moderate"
        elif score >= 20:
            return "low"
        else:
            return "very_low"
    
    def _generate_insights(self, features: List[float], propensity_score: float) -> List[str]:
        """Generate insights based on features and score"""
        insights = []
        
        age, monthly_income, employment, balance, avg_deposit, deposit_freq, \
        avg_withdrawal, withdrawal_freq, growth_rate, volatility, account_age, \
        has_tfn, product_type = features
        
        # Income insights
        if monthly_income > 10000:
            insights.append("Your income level supports strong savings potential")
        elif monthly_income < 2000:
            insights.append("Focus on building an emergency fund first")
        
        # Deposit behavior insights
        if deposit_freq < 1:
            insights.append("Try to make at least one deposit per month to build consistency")
        elif deposit_freq > 2:
            insights.append("Great job maintaining regular deposits!")
        
        # Balance insights
        if balance < 1000:
            insights.append("Aim to build an emergency fund of 3-6 months expenses")
        elif balance > 50000:
            insights.append("Consider diversifying into term deposits for higher returns")
        
        # TFN insights
        if not has_tfn:
            insights.append("Provide your TFN to avoid 47% withholding tax on interest")
        
        # Growth insights
        if growth_rate < 0:
            insights.append("Your balance is declining - review your spending and savings strategy")
        elif growth_rate > 5:
            insights.append("Excellent savings growth! Keep up the momentum")
        
        return insights
    
    def _get_consistency_recommendation(self, likelihood: str) -> str:
        """Get recommendation based on consistency likelihood"""
        recommendations = {
            "high": "Excellent! Your regular deposits show strong financial discipline. Consider increasing your deposit amount.",
            "medium": "You're doing well. Try to make deposits on a fixed schedule to improve consistency.",
            "low": "Set up automatic transfers to help maintain regular deposits.",
            "very_low": "Start with a small, manageable amount and set up automatic transfers to build the habit.",
        }
        return recommendations.get(likelihood, "")
    
    def train_model(self, training_data: List[Dict]):
        """
        Train the ML model
        
        Args:
            training_data: List of training examples with features and labels
        """
        # TODO: Implement XGBoost training
        # This would require xgboost library and training data
        pass
    
    def load_model(self, model_path: str):
        """Load pre-trained model"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def save_model(self, model_path: str):
        """Save trained model"""
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
