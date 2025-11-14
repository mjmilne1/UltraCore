"""Template Recommender AI Agent"""
from typing import Dict, List
from datetime import datetime

class TemplateRecommenderAgent:
    """AI agent for personalized template recommendations"""
    
    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm = llm_client
    
    async def recommend_portfolio_template(self, client_profile: Dict) -> Dict:
        """Recommend portfolio template based on client profile"""
        age = client_profile.get('age', 40)
        risk_tolerance = client_profile.get('risk_tolerance', 'moderate')
        investment_horizon_years = client_profile.get('investment_horizon_years', 10)
        goals = client_profile.get('goals', [])
        country = client_profile.get('country', 'AU')
        
        # Rule-based recommendations
        if age < 35 and risk_tolerance == 'high' and investment_horizon_years > 15:
            template = "aggressive_growth"
            confidence = 0.95
        elif age > 60 and 'retirement_income' in goals:
            template = "australian_retirement_income" if country == 'AU' else "conservative_income"
            confidence = 0.92
        elif risk_tolerance == 'low':
            template = "conservative_balanced"
            confidence = 0.88
        elif 'first_home' in goals and country == 'AU':
            template = "australian_first_home_buyer"
            confidence = 0.90
        else:
            template = "balanced_growth"
            confidence = 0.85
        
        return {
            "recommended_template": template,
            "confidence": confidence,
            "reasoning": f"Based on age {age}, {risk_tolerance} risk tolerance, and {investment_horizon_years} year horizon",
            "alternative_templates": [
                {"name": "balanced_growth", "match_score": 0.78},
                {"name": "moderate_growth", "match_score": 0.72}
            ]
        }
    
    async def recommend_rebalancing_strategy(self, portfolio_data: Dict) -> Dict:
        """Recommend rebalancing strategy template"""
        portfolio_size = portfolio_data.get('total_value', 0)
        volatility = portfolio_data.get('volatility', 0.15)
        drift_from_target = portfolio_data.get('drift_percent', 0)
        
        if drift_from_target > 10:
            strategy = "threshold_rebalancing"
            frequency = "immediate"
            confidence = 0.95
        elif portfolio_size > 1000000:
            strategy = "tax_aware_rebalancing"
            frequency = "quarterly"
            confidence = 0.90
        elif volatility > 0.20:
            strategy = "volatility_based_rebalancing"
            frequency = "monthly"
            confidence = 0.88
        else:
            strategy = "calendar_rebalancing"
            frequency = "quarterly"
            confidence = 0.85
        
        return {
            "recommended_strategy": strategy,
            "frequency": frequency,
            "confidence": confidence,
            "reasoning": f"Portfolio drift {drift_from_target}%, volatility {volatility:.2%}",
            "parameters": {
                "threshold_percent": 5 if strategy == "threshold_rebalancing" else None,
                "rebalance_frequency": frequency
            }
        }
    
    async def recommend_alert_rules(self, user_preferences: Dict) -> List[Dict]:
        """Recommend alert rule templates"""
        notification_preference = user_preferences.get('notification_preference', 'moderate')
        focus_areas = user_preferences.get('focus_areas', ['performance', 'risk'])
        
        recommendations = []
        
        if 'performance' in focus_areas:
            recommendations.append({
                "template": "portfolio_performance_alert",
                "parameters": {
                    "threshold_percent": -5 if notification_preference == 'high' else -10,
                    "period": "daily" if notification_preference == 'high' else "weekly"
                },
                "confidence": 0.90
            })
        
        if 'risk' in focus_areas:
            recommendations.append({
                "template": "risk_threshold_alert",
                "parameters": {
                    "var_threshold_percent": 2 if notification_preference == 'high' else 5,
                    "check_frequency": "daily"
                },
                "confidence": 0.88
            })
        
        if 'compliance' in focus_areas:
            recommendations.append({
                "template": "compliance_breach_alert",
                "parameters": {
                    "severity": "all" if notification_preference == 'high' else "high_only"
                },
                "confidence": 0.92
            })
        
        return recommendations
    
    async def personalize_template(self, template_id: str,
                                  user_context: Dict) -> Dict:
        """Personalize a template for specific user"""
        # Extract user context
        portfolio_value = user_context.get('portfolio_value', 0)
        country = user_context.get('country', 'AU')
        tax_status = user_context.get('tax_status', 'individual')
        
        customizations = {}
        
        # Australian-specific customizations
        if country == 'AU':
            customizations['enable_franking_credits'] = True
            customizations['gst_applicable'] = True
            
            if tax_status == 'smsf':
                customizations['smsf_compliance_rules'] = True
                customizations['pension_phase_support'] = True
        
        # Portfolio size-based customizations
        if portfolio_value > 1000000:
            customizations['tax_loss_harvesting'] = True
            customizations['advanced_rebalancing'] = True
        
        return {
            "template_id": template_id,
            "customizations": customizations,
            "personalization_confidence": 0.87,
            "estimated_improvement_percent": 12.5
        }
