"""
Notification Preferences Management
Customer control over notification channels and types

Features:
- Channel preferences (email, SMS, push)
- Category preferences (marketing, transactional, etc.)
- Frequency controls
- Do Not Disturb schedules
- Quiet hours
- GDPR/Privacy compliance
"""
from typing import Dict, List, Optional, Set
from datetime import datetime, time
from enum import Enum

from ultracore.notifications.notification_service import NotificationChannel, NotificationCategory
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class PreferenceLevel(str, Enum):
    OPT_IN = 'OPT_IN'
    OPT_OUT = 'OPT_OUT'
    DEFAULT = 'DEFAULT'


class FrequencyLimit(str, Enum):
    IMMEDIATE = 'IMMEDIATE'  # Real-time
    DAILY_DIGEST = 'DAILY_DIGEST'  # Once per day
    WEEKLY_DIGEST = 'WEEKLY_DIGEST'  # Once per week
    NEVER = 'NEVER'


class NotificationPreferences:
    """
    Customer notification preferences
    """
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        
        # Channel preferences
        self.channel_preferences: Dict[NotificationChannel, PreferenceLevel] = {
            NotificationChannel.EMAIL: PreferenceLevel.DEFAULT,
            NotificationChannel.SMS: PreferenceLevel.DEFAULT,
            NotificationChannel.PUSH: PreferenceLevel.DEFAULT,
            NotificationChannel.IN_APP: PreferenceLevel.DEFAULT,
        }
        
        # Category preferences
        self.category_preferences: Dict[NotificationCategory, PreferenceLevel] = {
            NotificationCategory.TRANSACTIONAL: PreferenceLevel.OPT_IN,  # Always on
            NotificationCategory.SECURITY: PreferenceLevel.OPT_IN,  # Always on
            NotificationCategory.REGULATORY: PreferenceLevel.OPT_IN,  # Always on
            NotificationCategory.PROMOTIONAL: PreferenceLevel.DEFAULT,
            NotificationCategory.OPERATIONAL: PreferenceLevel.DEFAULT,
            NotificationCategory.MARKETING: PreferenceLevel.DEFAULT,
        }
        
        # Frequency limits (by category)
        self.frequency_limits: Dict[NotificationCategory, FrequencyLimit] = {
            NotificationCategory.TRANSACTIONAL: FrequencyLimit.IMMEDIATE,
            NotificationCategory.SECURITY: FrequencyLimit.IMMEDIATE,
            NotificationCategory.REGULATORY: FrequencyLimit.IMMEDIATE,
            NotificationCategory.PROMOTIONAL: FrequencyLimit.DAILY_DIGEST,
            NotificationCategory.OPERATIONAL: FrequencyLimit.IMMEDIATE,
            NotificationCategory.MARKETING: FrequencyLimit.WEEKLY_DIGEST,
        }
        
        # Quiet hours (Do Not Disturb)
        self.quiet_hours_enabled = False
        self.quiet_hours_start: Optional[time] = time(22, 0)  # 10 PM
        self.quiet_hours_end: Optional[time] = time(8, 0)  # 8 AM
        
        # Timezone
        self.timezone = 'Australia/Sydney'
        
        # Global opt-out
        self.global_opt_out = False
        
        # Last updated
        self.updated_at = datetime.now(timezone.utc)
    
    def allows_notification(
        self,
        channel: NotificationChannel,
        category: NotificationCategory,
        check_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if notification is allowed based on preferences
        """
        # Global opt-out check
        if self.global_opt_out:
            return False
        
        # Critical categories always allowed
        if category in [
            NotificationCategory.TRANSACTIONAL,
            NotificationCategory.SECURITY,
            NotificationCategory.REGULATORY
        ]:
            return True
        
        # Check channel preference
        channel_pref = self.channel_preferences.get(channel, PreferenceLevel.DEFAULT)
        if channel_pref == PreferenceLevel.OPT_OUT:
            return False
        
        # Check category preference
        category_pref = self.category_preferences.get(category, PreferenceLevel.DEFAULT)
        if category_pref == PreferenceLevel.OPT_OUT:
            return False
        
        # Check quiet hours (except urgent notifications)
        if check_time and self.quiet_hours_enabled:
            if self._is_in_quiet_hours(check_time):
                return False
        
        return True
    
    def _is_in_quiet_hours(self, check_time: datetime) -> bool:
        """Check if time is within quiet hours"""
        current_time = check_time.time()
        
        # Handle overnight quiet hours (e.g., 10 PM to 8 AM)
        if self.quiet_hours_start > self.quiet_hours_end:
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end


class PreferencesService:
    """
    Notification preferences management service
    """
    
    def __init__(self):
        self.preferences: Dict[str, NotificationPreferences] = {}
    
    async def get_preferences(self, customer_id: str) -> NotificationPreferences:
        """Get customer preferences (create default if not exists)"""
        if customer_id not in self.preferences:
            self.preferences[customer_id] = NotificationPreferences(customer_id)
        
        return self.preferences[customer_id]
    
    async def update_channel_preference(
        self,
        customer_id: str,
        channel: NotificationChannel,
        preference: PreferenceLevel
    ) -> Dict:
        """Update channel preference"""
        prefs = await self.get_preferences(customer_id)
        prefs.channel_preferences[channel] = preference
        prefs.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='notification_preferences',
            event_type='channel_preference_updated',
            event_data={
                'customer_id': customer_id,
                'channel': channel.value,
                'preference': preference.value,
                'updated_at': prefs.updated_at.isoformat()
            },
            aggregate_id=customer_id
        )
        
        return {
            'success': True,
            'customer_id': customer_id,
            'channel': channel.value,
            'preference': preference.value
        }
    
    async def update_category_preference(
        self,
        customer_id: str,
        category: NotificationCategory,
        preference: PreferenceLevel
    ) -> Dict:
        """Update category preference"""
        prefs = await self.get_preferences(customer_id)
        
        # Prevent opting out of critical categories
        if category in [
            NotificationCategory.TRANSACTIONAL,
            NotificationCategory.SECURITY,
            NotificationCategory.REGULATORY
        ]:
            return {
                'success': False,
                'error': f'Cannot opt out of {category.value} notifications'
            }
        
        prefs.category_preferences[category] = preference
        prefs.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='notification_preferences',
            event_type='category_preference_updated',
            event_data={
                'customer_id': customer_id,
                'category': category.value,
                'preference': preference.value,
                'updated_at': prefs.updated_at.isoformat()
            },
            aggregate_id=customer_id
        )
        
        return {
            'success': True,
            'customer_id': customer_id,
            'category': category.value,
            'preference': preference.value
        }
    
    async def set_quiet_hours(
        self,
        customer_id: str,
        enabled: bool,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None
    ) -> Dict:
        """Set quiet hours (Do Not Disturb)"""
        prefs = await self.get_preferences(customer_id)
        
        prefs.quiet_hours_enabled = enabled
        if start_time:
            prefs.quiet_hours_start = start_time
        if end_time:
            prefs.quiet_hours_end = end_time
        
        prefs.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='notification_preferences',
            event_type='quiet_hours_updated',
            event_data={
                'customer_id': customer_id,
                'enabled': enabled,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'updated_at': prefs.updated_at.isoformat()
            },
            aggregate_id=customer_id
        )
        
        return {
            'success': True,
            'customer_id': customer_id,
            'quiet_hours_enabled': enabled
        }
    
    async def global_opt_out(self, customer_id: str) -> Dict:
        """
        Global opt-out from all non-critical notifications
        
        GDPR/Privacy compliance
        """
        prefs = await self.get_preferences(customer_id)
        prefs.global_opt_out = True
        prefs.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='notification_preferences',
            event_type='global_opt_out',
            event_data={
                'customer_id': customer_id,
                'opted_out_at': prefs.updated_at.isoformat()
            },
            aggregate_id=customer_id
        )
        
        return {
            'success': True,
            'customer_id': customer_id,
            'message': 'You have been unsubscribed from all marketing and promotional communications'
        }


# Global service
_preferences_service: Optional[PreferencesService] = None


def get_preferences_service() -> PreferencesService:
    global _preferences_service
    if _preferences_service is None:
        _preferences_service = PreferencesService()
    return _preferences_service
