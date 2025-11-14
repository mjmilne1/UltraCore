"""
Notification API
REST endpoints for notification management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time

from ultracore.notifications.notification_service import (
    get_notification_service, NotificationChannel, NotificationCategory, NotificationPriority
)
from ultracore.notifications.preferences.preferences_service import (
    get_preferences_service, PreferenceLevel
)
from ultracore.notifications.agents.intelligence_agent import (
    NotificationIntelligenceAgent, NotificationAnalytics
)
from ultracore.security.auth.jwt_auth import User, get_current_user
from ultracore.security.rbac.permissions import Permission, PermissionChecker


router = APIRouter()


# Request Models
class SendNotificationRequest(BaseModel):
    template_id: str
    recipient_id: str
    variables: dict
    channel_override: Optional[str] = None
    priority: str = 'NORMAL'
    schedule_for: Optional[str] = None


class UpdateChannelPreferenceRequest(BaseModel):
    channel: str
    preference: str


class UpdateCategoryPreferenceRequest(BaseModel):
    category: str
    preference: str


class SetQuietHoursRequest(BaseModel):
    enabled: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# Endpoints
@router.post('/send')
async def send_notification(
    request: SendNotificationRequest,
    user: User = Depends(get_current_user)
):
    """
    Send notification
    
    Requires: ACCOUNT_CREATE permission (or admin)
    """
    notification_service = get_notification_service()
    
    # Parse optional fields
    channel = NotificationChannel(request.channel_override) if request.channel_override else None
    priority = NotificationPriority(request.priority)
    schedule_for = datetime.fromisoformat(request.schedule_for) if request.schedule_for else None
    
    result = await notification_service.send_notification(
        template_id=request.template_id,
        recipient_id=request.recipient_id,
        variables=request.variables,
        channel_override=channel,
        priority=priority,
        schedule_for=schedule_for
    )
    
    return result


@router.get('/preferences')
async def get_preferences(
    user: User = Depends(get_current_user)
):
    """Get notification preferences for current user"""
    preferences_service = get_preferences_service()
    prefs = await preferences_service.get_preferences(user.user_id)
    
    return {
        'customer_id': prefs.customer_id,
        'channel_preferences': {k.value: v.value for k, v in prefs.channel_preferences.items()},
        'category_preferences': {k.value: v.value for k, v in prefs.category_preferences.items()},
        'quiet_hours_enabled': prefs.quiet_hours_enabled,
        'quiet_hours_start': prefs.quiet_hours_start.isoformat() if prefs.quiet_hours_start else None,
        'quiet_hours_end': prefs.quiet_hours_end.isoformat() if prefs.quiet_hours_end else None,
        'global_opt_out': prefs.global_opt_out
    }


@router.put('/preferences/channel')
async def update_channel_preference(
    request: UpdateChannelPreferenceRequest,
    user: User = Depends(get_current_user)
):
    """Update channel preference"""
    preferences_service = get_preferences_service()
    
    channel = NotificationChannel(request.channel)
    preference = PreferenceLevel(request.preference)
    
    result = await preferences_service.update_channel_preference(
        customer_id=user.user_id,
        channel=channel,
        preference=preference
    )
    
    return result


@router.put('/preferences/category')
async def update_category_preference(
    request: UpdateCategoryPreferenceRequest,
    user: User = Depends(get_current_user)
):
    """Update category preference"""
    preferences_service = get_preferences_service()
    
    category = NotificationCategory(request.category)
    preference = PreferenceLevel(request.preference)
    
    result = await preferences_service.update_category_preference(
        customer_id=user.user_id,
        category=category,
        preference=preference
    )
    
    return result


@router.put('/preferences/quiet-hours')
async def set_quiet_hours(
    request: SetQuietHoursRequest,
    user: User = Depends(get_current_user)
):
    """Set quiet hours (Do Not Disturb)"""
    preferences_service = get_preferences_service()
    
    start_time = time.fromisoformat(request.start_time) if request.start_time else None
    end_time = time.fromisoformat(request.end_time) if request.end_time else None
    
    result = await preferences_service.set_quiet_hours(
        customer_id=user.user_id,
        enabled=request.enabled,
        start_time=start_time,
        end_time=end_time
    )
    
    return result


@router.post('/preferences/opt-out')
async def global_opt_out(
    user: User = Depends(get_current_user)
):
    """Global opt-out from all marketing notifications"""
    preferences_service = get_preferences_service()
    
    result = await preferences_service.global_opt_out(user.user_id)
    
    return result


@router.get('/analytics/channel/{channel}')
async def get_channel_analytics(
    channel: str,
    date_from: str,
    date_to: str,
    user: User = Depends(get_current_user)
):
    """
    Get channel performance analytics
    
    Requires: ANALYTICS_READ permission
    """
    if not PermissionChecker.has_permission(user, Permission.ANALYTICS_READ):
        raise HTTPException(status_code=403, detail='No permission to view analytics')
    
    channel_enum = NotificationChannel(channel)
    from_date = datetime.fromisoformat(date_from)
    to_date = datetime.fromisoformat(date_to)
    
    metrics = await NotificationAnalytics.get_channel_performance(
        channel_enum,
        from_date,
        to_date
    )
    
    return metrics


@router.get('/analytics/template/{template_id}')
async def get_template_analytics(
    template_id: str,
    user: User = Depends(get_current_user)
):
    """
    Get template performance analytics
    
    Requires: ANALYTICS_READ permission
    """
    if not PermissionChecker.has_permission(user, Permission.ANALYTICS_READ):
        raise HTTPException(status_code=403, detail='No permission to view analytics')
    
    performance = await NotificationAnalytics.get_template_performance(template_id)
    
    return performance


@router.get('/health')
async def health_check():
    """Notification service health check"""
    return {
        'status': 'healthy',
        'service': 'notifications',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
