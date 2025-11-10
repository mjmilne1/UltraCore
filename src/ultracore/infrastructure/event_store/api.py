from fastapi import APIRouter
from typing import List, Optional

from ultracore.infrastructure.event_store.store import get_event_store

router = APIRouter(prefix='/api/v1/events', tags=['Event Store'])


@router.get('/')
async def get_events(limit: int = 100):
    store = get_event_store()
    events = await store.get_all_events(limit=limit)
    return [event.to_dict() for event in events]


@router.get('/aggregate/{aggregate_id}')
async def get_aggregate_events(aggregate_id: str):
    store = get_event_store()
    events = await store.get_events(aggregate_id)
    return [event.to_dict() for event in events]


@router.get('/stats')
async def get_stats():
    store = get_event_store()
    events = await store.get_all_events(limit=10000)
    
    return {
        'total_events': len(events),
        'event_types': len(set(e.event_type for e in events)),
        'unique_aggregates': len(set(e.aggregate_id for e in events))
    }
