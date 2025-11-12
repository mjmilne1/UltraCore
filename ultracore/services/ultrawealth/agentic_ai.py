"""
Agentic AI System for Autonomous Portfolio Management
Makes intelligent decisions based on market conditions
"""

from typing import Dict, List
from datetime import datetime
import pandas as pd

class AgenticAI:
    """Autonomous AI agent for portfolio management"""
    
    def __init__(self):
        self.decision_history = []
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict:
        """Initialize decision-making rules"""
        return {
            'rebalance_threshold': 0.05,  # Rebalance if weights drift >5%
            'max_position_size': 0.25,  # Max 25% in single ETF
            'min_position_size': 0.02,  # Min 2% in single ETF
            'stop_loss': -0.15,  # Sell if down 15%
            'take_profit': 0.30,  # Take profit if up 30%
        }
    
    async def analyze_market_conditions(self, etf_predictions: List[Dict]) -> Dict:
        """Analyze overall market conditions"""
        
        if not etf_predictions:
            return {'sentiment': 'neutral', 'confidence': 0}
        
        # Calculate average predicted change
        avg_change = sum(p['predicted_change_pct'] for p in etf_predictions) / len(etf_predictions)
        
        # Determine sentiment
        if avg_change > 2:
            sentiment = 'bullish'
        elif avg_change < -2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence
        confidences = [p.get('confidence', 0.5) for p in etf_predictions]
        avg_confidence = sum(confidences) / len(confidences)
        
        return {
            'sentiment': sentiment,
            'avg_predicted_change': round(avg_change, 2),
            'confidence': round(avg_confidence, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    async def make_decision(
        self,
        current_allocation: Dict,
        predictions: List[Dict],
        portfolio_value: float
    ) -> Dict:
        """Make autonomous portfolio decision"""
        
        market_analysis = await self.analyze_market_conditions(predictions)
        
        recommendations = []
        
        # Analyze each position
        for pred in predictions:
            ticker = pred['ticker']
            predicted_change = pred['predicted_change_pct']
            current_weight = current_allocation.get(ticker, {}).get('weight', 0)
            
            action = 'hold'
            reason = 'Within normal parameters'
            
            # Decision logic
            if predicted_change < -10:
                action = 'reduce'
                reason = f'Predicted decline of {predicted_change:.1f}%'
            elif predicted_change > 10:
                action = 'increase'
                reason = f'Predicted growth of {predicted_change:.1f}%'
            elif current_weight > self.rules['max_position_size']:
                action = 'reduce'
                reason = f'Position too large ({current_weight*100:.1f}%)'
            elif current_weight < self.rules['min_position_size'] and current_weight > 0:
                action = 'increase'
                reason = f'Position too small ({current_weight*100:.1f}%)'
            
            recommendations.append({
                'ticker': ticker,
                'action': action,
                'reason': reason,
                'predicted_change': predicted_change,
                'current_weight': round(current_weight, 4)
            })
        
        decision = {
            'timestamp': datetime.now().isoformat(),
            'market_analysis': market_analysis,
            'recommendations': recommendations,
            'portfolio_value': portfolio_value,
            'should_rebalance': market_analysis['sentiment'] != 'neutral'
        }
        
        self.decision_history.append(decision)
        
        return decision
    
    def get_decision_history(self, limit: int = 10) -> List[Dict]:
        """Get recent decision history"""
        return self.decision_history[-limit:]

agentic_ai = AgenticAI()
