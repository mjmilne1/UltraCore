"""Template Recommender ML Model"""
import numpy as np
from typing import Dict, List
from datetime import datetime

class TemplateRecommenderModel:
    """ML model for template usage prediction and recommendation"""
    
    def __init__(self):
        """Initialize model"""
        self.model_version = "1.0.0"
        self.trained_at = datetime.utcnow()
    
    def predict_template_usage(self, user_features: Dict) -> Dict:
        """Predict which templates user is likely to use"""
        # Extract features
        age = user_features.get('age', 40)
        risk_score = user_features.get('risk_score', 5)  # 1-10
        portfolio_value = user_features.get('portfolio_value', 0)
        country = user_features.get('country', 'AU')
        
        # Simple scoring model
        template_scores = {}
        
        # Aggressive Growth
        aggressive_score = 0.0
        if age < 40:
            aggressive_score += 0.3
        if risk_score > 7:
            aggressive_score += 0.4
        if portfolio_value > 500000:
            aggressive_score += 0.2
        template_scores['aggressive_growth'] = min(aggressive_score, 1.0)
        
        # Conservative Balanced
        conservative_score = 0.0
        if age > 55:
            conservative_score += 0.3
        if risk_score < 4:
            conservative_score += 0.4
        if portfolio_value < 100000:
            conservative_score += 0.2
        template_scores['conservative_balanced'] = min(conservative_score, 1.0)
        
        # Australian Retirement Income
        if country == 'AU' and age > 60:
            template_scores['australian_retirement_income'] = 0.85
        else:
            template_scores['australian_retirement_income'] = 0.1
        
        # Balanced Growth (default)
        template_scores['balanced_growth'] = 0.6
        
        # Sort by score
        sorted_templates = sorted(template_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "predictions": [
                {"template": name, "probability": score}
                for name, score in sorted_templates[:3]
            ],
            "top_recommendation": sorted_templates[0][0],
            "confidence": sorted_templates[0][1],
            "model_version": self.model_version
        }
    
    def predict_template_success(self, template_id: str,
                                 user_profile: Dict,
                                 market_conditions: Dict) -> float:
        """Predict likelihood of template success for user"""
        # Feature engineering
        age = user_profile.get('age', 40)
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
        market_volatility = market_conditions.get('volatility', 0.15)
        
        # Base success rate
        success_probability = 0.7
        
        # Adjust based on template-user fit
        if template_id == 'aggressive_growth':
            if age < 40 and risk_tolerance == 'high':
                success_probability += 0.2
            if market_volatility > 0.25:
                success_probability -= 0.15
        
        elif template_id == 'conservative_balanced':
            if age > 55 and risk_tolerance == 'low':
                success_probability += 0.2
            if market_volatility > 0.20:
                success_probability += 0.1  # Conservative does better in volatile markets
        
        return min(max(success_probability, 0.0), 1.0)
    
    def cluster_users_by_template_preference(self, users: List[Dict]) -> Dict:
        """Cluster users by template preferences"""
        # Simple clustering based on age and risk
        clusters = {
            "young_aggressive": [],
            "mid_balanced": [],
            "senior_conservative": [],
            "high_net_worth": []
        }
        
        for user in users:
            age = user.get('age', 40)
            risk_score = user.get('risk_score', 5)
            portfolio_value = user.get('portfolio_value', 0)
            
            if portfolio_value > 1000000:
                clusters['high_net_worth'].append(user)
            elif age < 40 and risk_score > 6:
                clusters['young_aggressive'].append(user)
            elif age > 60 and risk_score < 5:
                clusters['senior_conservative'].append(user)
            else:
                clusters['mid_balanced'].append(user)
        
        return {
            "clusters": {
                name: {
                    "user_count": len(users),
                    "avg_age": np.mean([u.get('age', 40) for u in users]) if users else 0,
                    "avg_risk_score": np.mean([u.get('risk_score', 5) for u in users]) if users else 0,
                    "recommended_templates": self._get_cluster_templates(name)
                }
                for name, users in clusters.items()
            },
            "total_users": len(users)
        }
    
    def _get_cluster_templates(self, cluster_name: str) -> List[str]:
        """Get recommended templates for cluster"""
        cluster_templates = {
            "young_aggressive": ["aggressive_growth", "growth_focused"],
            "mid_balanced": ["balanced_growth", "moderate_growth"],
            "senior_conservative": ["conservative_balanced", "income_focused"],
            "high_net_worth": ["tax_optimized", "sophisticated_investor"]
        }
        return cluster_templates.get(cluster_name, ["balanced_growth"])
    
    def evaluate_template_performance(self, template_id: str,
                                     historical_data: List[Dict]) -> Dict:
        """Evaluate template performance metrics"""
        if not historical_data:
            return {"error": "No historical data"}
        
        returns = [d.get('return', 0) for d in historical_data]
        
        avg_return = np.mean(returns)
        volatility = np.std(returns)
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0
        
        return {
            "template_id": template_id,
            "avg_return_percent": avg_return * 100,
            "volatility_percent": volatility * 100,
            "sharpe_ratio": sharpe_ratio,
            "sample_size": len(historical_data),
            "performance_rating": "excellent" if sharpe_ratio > 1.5 else "good" if sharpe_ratio > 1.0 else "average"
        }
