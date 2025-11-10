"""
Event Bus API - Monitor and manage event streams
"""
from fastapi import APIRouter
from ultracore.infrastructure.event_bus.bus import get_event_bus, EventTopic, EventBusType

router = APIRouter()


@router.get('/event-bus/status')
async def get_event_bus_status():
    '''Get event bus status'''
    bus = get_event_bus()
    
    bus_type = type(bus).__name__
    
    # Get metrics for in-memory bus
    if hasattr(bus, 'event_log'):
        event_count = len(bus.event_log)
        subscriber_count = sum(len(handlers) for handlers in bus.subscribers.values())
    else:
        event_count = 0
        subscriber_count = 0
    
    return {
        'bus_type': bus_type,
        'status': 'running' if bus.running else 'stopped',
        'total_events_published': event_count,
        'total_subscribers': subscriber_count,
        'topics': [topic.value for topic in EventTopic]
    }


@router.get('/event-bus/events')
async def get_recent_events(topic: str = None, limit: int = 100):
    '''Get recent events from event bus'''
    bus = get_event_bus()
    
    if not hasattr(bus, 'event_log'):
        return {
            'message': 'Event log only available for In-Memory bus',
            'events': []
        }
    
    events = bus.event_log[-limit:]
    
    if topic:
        events = [e for e in events if e.topic.value == topic]
    
    return {
        'total_events': len(events),
        'events': [
            {
                'topic': e.topic.value,
                'event_type': e.event_type,
                'aggregate_id': e.aggregate_id,
                'timestamp': e.timestamp
            }
            for e in events
        ]
    }


@router.get('/event-bus/topics')
async def get_topics():
    '''Get all event topics'''
    return {
        'topics': [
            {
                'name': topic.value,
                'category': topic.name.split('_')[0]
            }
            for topic in EventTopic
        ]
    }
