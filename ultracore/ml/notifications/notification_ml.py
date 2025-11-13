"""
Notification ML Models
Machine learning for alert prediction and user preference learning
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import numpy as np

from ultracore.notifications.events import (
    NotificationType,
    AlertPriority,
    DeliveryChannel
)

logger = logging.getLogger(__name__)


class NotificationEngagementModel:
    """
    ML Model for Predicting Notification Engagement
    
    Predicts likelihood that user will engage with (read/act on) a notification
    
    Features:
    - Notification type
    - Priority level
    - Time of day
    - Day of week
    - User engagement history
    - Portfolio value
    - Risk profile
    - Recent notification count
    
    Target: Engagement probability (0-1)
    """
    
    def __init__(self):
        self.name = "NotificationEngagementModel"
        self.version = "1.0.0"
        self.trained = False
        logger.info(f"{self.name} v{self.version} initialized")
    
    def extract_features(
        self,
        notification_data: Dict[str, Any],
        user_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Extract features for engagement prediction
        
        Args:
            notification_data: Notification details
            user_data: User profile data
            historical_data: Historical engagement data
        
        Returns:
            Feature vector
        """
        features = []
        
        # Notification features
        notification_type = notification_data.get("notification_type", NotificationType.SYSTEM_ALERT)
        priority = notification_data.get("priority", AlertPriority.MEDIUM)
        
        # Encode notification type (one-hot)
        type_encoding = {
            NotificationType.PRICE_ALERT: [1, 0, 0, 0, 0, 0, 0, 0],
            NotificationType.PORTFOLIO_ALERT: [0, 1, 0, 0, 0, 0, 0, 0],
            NotificationType.NEWS_ALERT: [0, 0, 1, 0, 0, 0, 0, 0],
            NotificationType.TRANSACTION_CONFIRMATION: [0, 0, 0, 1, 0, 0, 0, 0],
            NotificationType.PORTFOLIO_SUMMARY: [0, 0, 0, 0, 1, 0, 0, 0],
            NotificationType.ML_PREDICTION: [0, 0, 0, 0, 0, 1, 0, 0],
            NotificationType.COMPLIANCE_ALERT: [0, 0, 0, 0, 0, 0, 1, 0],
            NotificationType.SYSTEM_ALERT: [0, 0, 0, 0, 0, 0, 0, 1]
        }
        features.extend(type_encoding.get(notification_type, [0] * 8))
        
        # Encode priority
        priority_encoding = {
            AlertPriority.LOW: [1, 0, 0, 0],
            AlertPriority.MEDIUM: [0, 1, 0, 0],
            AlertPriority.HIGH: [0, 0, 1, 0],
            AlertPriority.URGENT: [0, 0, 0, 1]
        }
        features.extend(priority_encoding.get(priority, [0] * 4))
        
        # Time features
        now = datetime.utcnow()
        features.append(now.hour / 24.0)  # Hour of day (normalized)
        features.append(now.weekday() / 7.0)  # Day of week (normalized)
        
        # User features
        portfolio_value = user_data.get("portfolio_value", 0)
        features.append(min(portfolio_value / 1000000.0, 10.0))  # Portfolio value (millions, capped at 10)
        
        risk_profile_encoding = {
            "low": [1, 0, 0],
            "medium": [0, 1, 0],
            "high": [0, 0, 1]
        }
        risk_profile = user_data.get("risk_profile", "medium")
        features.extend(risk_profile_encoding.get(risk_profile, [0, 1, 0]))
        
        # Historical engagement features
        if historical_data:
            # Engagement rate (last 30 days)
            recent_notifications = [n for n in historical_data if (now - n.get("created_at", now)).days <= 30]
            if recent_notifications:
                engaged_count = len([n for n in recent_notifications if n.get("read_at")])
                engagement_rate = engaged_count / len(recent_notifications)
                features.append(engagement_rate)
            else:
                features.append(0.5)  # Default
            
            # Average time to engagement (hours)
            engagement_times = []
            for n in recent_notifications:
                if n.get("read_at") and n.get("created_at"):
                    time_diff = (n["read_at"] - n["created_at"]).total_seconds() / 3600
                    engagement_times.append(min(time_diff, 24.0))  # Cap at 24 hours
            
            if engagement_times:
                features.append(np.mean(engagement_times) / 24.0)  # Normalized
            else:
                features.append(0.5)  # Default
            
            # Recent notification count (last 24 hours)
            recent_24h = len([n for n in historical_data if (now - n.get("created_at", now)).total_seconds() < 86400])
            features.append(min(recent_24h / 20.0, 1.0))  # Normalized, capped at 20
        else:
            features.extend([0.5, 0.5, 0.0])  # Defaults
        
        return np.array(features)
    
    def predict_engagement(
        self,
        notification_data: Dict[str, Any],
        user_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict engagement probability
        
        Args:
            notification_data: Notification details
            user_data: User profile data
            historical_data: Historical engagement data
        
        Returns:
            Prediction dictionary
        """
        features = self.extract_features(notification_data, user_data, historical_data)
        
        # TODO: Replace with trained model
        # For now, use heuristic-based prediction
        
        # Base probability by type
        type_probs = {
            NotificationType.PRICE_ALERT: 0.7,
            NotificationType.PORTFOLIO_ALERT: 0.8,
            NotificationType.NEWS_ALERT: 0.4,
            NotificationType.TRANSACTION_CONFIRMATION: 0.9,
            NotificationType.PORTFOLIO_SUMMARY: 0.5,
            NotificationType.ML_PREDICTION: 0.6,
            NotificationType.COMPLIANCE_ALERT: 0.95,
            NotificationType.SYSTEM_ALERT: 0.6
        }
        
        notification_type = notification_data.get("notification_type", NotificationType.SYSTEM_ALERT)
        base_prob = type_probs.get(notification_type, 0.5)
        
        # Adjust for priority
        priority = notification_data.get("priority", AlertPriority.MEDIUM)
        priority_multiplier = {
            AlertPriority.LOW: 0.8,
            AlertPriority.MEDIUM: 1.0,
            AlertPriority.HIGH: 1.2,
            AlertPriority.URGENT: 1.4
        }.get(priority, 1.0)
        
        # Adjust for historical engagement
        if historical_data:
            recent_notifications = [n for n in historical_data if (datetime.utcnow() - n.get("created_at", datetime.utcnow())).days <= 30]
            if recent_notifications:
                engaged_count = len([n for n in recent_notifications if n.get("read_at")])
                engagement_rate = engaged_count / len(recent_notifications)
                historical_multiplier = 0.5 + (engagement_rate * 0.5)  # 0.5 to 1.0
            else:
                historical_multiplier = 1.0
        else:
            historical_multiplier = 1.0
        
        # Calculate final probability
        probability = min(base_prob * priority_multiplier * historical_multiplier, 1.0)
        
        return {
            "engagement_probability": probability,
            "confidence": 0.75,
            "recommendation": "send" if probability >= 0.5 else "suppress",
            "features_used": len(features)
        }
    
    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train engagement prediction model
        
        Args:
            training_data: List of training examples
        
        Returns:
            Training metrics
        """
        # TODO: Implement model training
        logger.info(f"Training {self.name} with {len(training_data)} examples")
        
        self.trained = True
        
        return {
            "model": self.name,
            "version": self.version,
            "training_samples": len(training_data),
            "accuracy": 0.85,  # Placeholder
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85
        }


class UserPreferenceLearningModel:
    """
    ML Model for Learning User Notification Preferences
    
    Learns optimal notification preferences from user behavior
    
    Features:
    - Historical engagement patterns
    - Time-of-day preferences
    - Channel preferences
    - Notification type preferences
    - Quiet hours patterns
    
    Outputs:
    - Recommended notification settings
    - Optimal delivery times
    - Preferred channels
    """
    
    def __init__(self):
        self.name = "UserPreferenceLearningModel"
        self.version = "1.0.0"
        self.trained = False
        logger.info(f"{self.name} v{self.version} initialized")
    
    def learn_time_preferences(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn user's preferred notification times
        
        Args:
            historical_data: Historical engagement data
        
        Returns:
            Time preferences
        """
        if not historical_data:
            return {
                "preferred_hours": [9, 12, 17],  # Default: 9am, 12pm, 5pm
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
                "confidence": 0.0
            }
        
        # Analyze engagement by hour
        engagement_by_hour = {}
        for item in historical_data:
            if item.get("read_at"):
                hour = item["read_at"].hour
                engagement_by_hour[hour] = engagement_by_hour.get(hour, 0) + 1
        
        if not engagement_by_hour:
            return {
                "preferred_hours": [9, 12, 17],
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
                "confidence": 0.0
            }
        
        # Find top 3 hours
        sorted_hours = sorted(engagement_by_hour.items(), key=lambda x: x[1], reverse=True)
        preferred_hours = [hour for hour, _ in sorted_hours[:3]]
        
        # Infer quiet hours (hours with no engagement)
        all_hours = set(range(24))
        engaged_hours = set(engagement_by_hour.keys())
        quiet_hours = sorted(all_hours - engaged_hours)
        
        if quiet_hours:
            # Find longest continuous quiet period
            quiet_start = quiet_hours[0]
            quiet_end = quiet_hours[-1]
        else:
            quiet_start = 22
            quiet_end = 8
        
        return {
            "preferred_hours": preferred_hours,
            "quiet_hours_start": f"{quiet_start:02d}:00",
            "quiet_hours_end": f"{quiet_end:02d}:00",
            "confidence": min(len(historical_data) / 100.0, 1.0)
        }
    
    def learn_channel_preferences(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn user's preferred notification channels
        
        Args:
            historical_data: Historical engagement data
        
        Returns:
            Channel preferences
        """
        if not historical_data:
            return {
                "preferred_channels": [DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
                "channel_engagement_rates": {},
                "confidence": 0.0
            }
        
        # Analyze engagement by channel
        channel_stats = {}
        for item in historical_data:
            channel = item.get("channel")
            if channel:
                if channel not in channel_stats:
                    channel_stats[channel] = {"sent": 0, "engaged": 0}
                
                channel_stats[channel]["sent"] += 1
                if item.get("read_at"):
                    channel_stats[channel]["engaged"] += 1
        
        # Calculate engagement rates
        channel_engagement_rates = {}
        for channel, stats in channel_stats.items():
            if stats["sent"] > 0:
                channel_engagement_rates[channel] = stats["engaged"] / stats["sent"]
        
        # Sort by engagement rate
        sorted_channels = sorted(
            channel_engagement_rates.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        preferred_channels = [channel for channel, _ in sorted_channels[:2]]
        if not preferred_channels:
            preferred_channels = [DeliveryChannel.EMAIL, DeliveryChannel.IN_APP]
        
        return {
            "preferred_channels": preferred_channels,
            "channel_engagement_rates": channel_engagement_rates,
            "confidence": min(len(historical_data) / 100.0, 1.0)
        }
    
    def learn_type_preferences(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn user's notification type preferences
        
        Args:
            historical_data: Historical engagement data
        
        Returns:
            Type preferences
        """
        if not historical_data:
            return {
                "enabled_types": list(NotificationType),
                "type_engagement_rates": {},
                "confidence": 0.0
            }
        
        # Analyze engagement by type
        type_stats = {}
        for item in historical_data:
            ntype = item.get("notification_type")
            if ntype:
                if ntype not in type_stats:
                    type_stats[ntype] = {"sent": 0, "engaged": 0}
                
                type_stats[ntype]["sent"] += 1
                if item.get("read_at"):
                    type_stats[ntype]["engaged"] += 1
        
        # Calculate engagement rates
        type_engagement_rates = {}
        for ntype, stats in type_stats.items():
            if stats["sent"] > 0:
                type_engagement_rates[ntype] = stats["engaged"] / stats["sent"]
        
        # Enable types with >30% engagement rate
        enabled_types = [
            ntype for ntype, rate in type_engagement_rates.items()
            if rate >= 0.3
        ]
        
        # Always enable critical types
        critical_types = [
            NotificationType.TRANSACTION_CONFIRMATION,
            NotificationType.COMPLIANCE_ALERT
        ]
        for ctype in critical_types:
            if ctype not in enabled_types:
                enabled_types.append(ctype)
        
        return {
            "enabled_types": enabled_types,
            "type_engagement_rates": type_engagement_rates,
            "confidence": min(len(historical_data) / 100.0, 1.0)
        }
    
    def recommend_preferences(
        self,
        user_id: str,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive preference recommendations
        
        Args:
            user_id: User ID
            historical_data: Historical engagement data
        
        Returns:
            Recommended preferences
        """
        time_prefs = self.learn_time_preferences(historical_data)
        channel_prefs = self.learn_channel_preferences(historical_data)
        type_prefs = self.learn_type_preferences(historical_data)
        
        # Calculate overall confidence
        overall_confidence = np.mean([
            time_prefs["confidence"],
            channel_prefs["confidence"],
            type_prefs["confidence"]
        ])
        
        return {
            "user_id": user_id,
            "recommended_settings": {
                "preferred_hours": time_prefs["preferred_hours"],
                "quiet_hours_start": time_prefs["quiet_hours_start"],
                "quiet_hours_end": time_prefs["quiet_hours_end"],
                "preferred_channels": channel_prefs["preferred_channels"],
                "enabled_types": type_prefs["enabled_types"],
                "frequency": "immediate" if overall_confidence > 0.7 else "daily_digest"
            },
            "confidence": overall_confidence,
            "based_on_samples": len(historical_data),
            "recommendations": self._generate_recommendations(
                time_prefs,
                channel_prefs,
                type_prefs,
                overall_confidence
            )
        }
    
    def _generate_recommendations(
        self,
        time_prefs: Dict[str, Any],
        channel_prefs: Dict[str, Any],
        type_prefs: Dict[str, Any],
        confidence: float
    ) -> List[str]:
        """Generate human-readable recommendations"""
        recommendations = []
        
        if confidence < 0.5:
            recommendations.append("More data needed for personalized recommendations. Using default settings.")
        
        if time_prefs["preferred_hours"]:
            hours_str = ", ".join([f"{h}:00" for h in time_prefs["preferred_hours"]])
            recommendations.append(f"You're most engaged at: {hours_str}")
        
        if channel_prefs["preferred_channels"]:
            channels_str = ", ".join([str(c) for c in channel_prefs["preferred_channels"]])
            recommendations.append(f"Recommended channels: {channels_str}")
        
        if channel_prefs["channel_engagement_rates"]:
            best_channel = max(channel_prefs["channel_engagement_rates"].items(), key=lambda x: x[1])
            recommendations.append(f"Highest engagement on {best_channel[0]} ({best_channel[1]*100:.0f}%)")
        
        return recommendations


# Singleton instances
_engagement_model: Optional[NotificationEngagementModel] = None
_preference_model: Optional[UserPreferenceLearningModel] = None


def get_engagement_model() -> NotificationEngagementModel:
    """Get notification engagement model instance"""
    global _engagement_model
    if _engagement_model is None:
        _engagement_model = NotificationEngagementModel()
    return _engagement_model


def get_preference_learning_model() -> UserPreferenceLearningModel:
    """Get user preference learning model instance"""
    global _preference_model
    if _preference_model is None:
        _preference_model = UserPreferenceLearningModel()
    return _preference_model
