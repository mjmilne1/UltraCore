"""
Event Replay
Rebuild system state from Kafka event log
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ultracore.event_sourcing.store.event_store import EventStore, Event

logger = logging.getLogger(__name__)


class EventReplay:
    """
    Event Replay Engine
    
    Capabilities:
    - Rebuild entire system state from events
    - Replay events for specific aggregates
    - Replay events from a specific point in time
    - Verify event consistency
    - Generate audit reports
    """
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    def replay_all_events(
        self,
        topic: str,
        projection_handler: callable,
        from_offset: int = 0
    ) -> Dict[str, Any]:
        """
        Replay all events from a topic
        
        Args:
            topic: Kafka topic
            projection_handler: Function to process each event
            from_offset: Starting offset
        
        Returns:
            Replay statistics
        """
        logger.info(f"Starting event replay for topic: {topic}")
        
        start_time = datetime.utcnow()
        events_processed = 0
        events_failed = 0
        
        # Get all events
        events = self.event_store.get_all_events(topic, from_offset=from_offset)
        
        # Process each event
        for event in events:
            try:
                projection_handler(event.to_dict())
                events_processed += 1
                
                if events_processed % 100 == 0:
                    logger.info(f"Replayed {events_processed} events...")
                    
            except Exception as e:
                logger.error(f"Failed to replay event {event.event_id}: {e}")
                events_failed += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        stats = {
            "topic": topic,
            "events_processed": events_processed,
            "events_failed": events_failed,
            "duration_seconds": duration,
            "events_per_second": events_processed / duration if duration > 0 else 0,
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Event replay completed: {stats}")
        return stats
    
    def replay_aggregate(
        self,
        topic: str,
        aggregate_id: str,
        aggregate_class: type
    ) -> Any:
        """
        Replay events for a specific aggregate
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID
            aggregate_class: Aggregate class with apply_event method
        
        Returns:
            Rebuilt aggregate instance
        """
        logger.info(f"Replaying aggregate: {aggregate_id}")
        
        # Get events for aggregate
        events = self.event_store.get_events_by_aggregate(topic, aggregate_id)
        
        # Create new aggregate instance
        aggregate = aggregate_class()
        
        # Apply each event
        for event in events:
            if hasattr(aggregate, 'apply_event'):
                aggregate.apply_event(event.to_dict())
        
        logger.info(f"Aggregate rebuilt from {len(events)} events")
        return aggregate
    
    def replay_from_timestamp(
        self,
        topic: str,
        from_timestamp: datetime,
        projection_handler: callable
    ) -> Dict[str, Any]:
        """
        Replay events from a specific timestamp
        
        Args:
            topic: Kafka topic
            from_timestamp: Starting timestamp
            projection_handler: Function to process each event
        
        Returns:
            Replay statistics
        """
        logger.info(f"Replaying events from {from_timestamp}")
        
        start_time = datetime.utcnow()
        events_processed = 0
        events_skipped = 0
        
        # Get all events
        events = self.event_store.get_all_events(topic)
        
        # Filter and process events
        for event in events:
            if event.event_timestamp >= from_timestamp:
                try:
                    projection_handler(event.to_dict())
                    events_processed += 1
                except Exception as e:
                    logger.error(f"Failed to replay event: {e}")
            else:
                events_skipped += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "topic": topic,
            "from_timestamp": from_timestamp.isoformat(),
            "events_processed": events_processed,
            "events_skipped": events_skipped,
            "duration_seconds": duration,
        }
    
    def verify_event_consistency(
        self,
        topic: str,
        aggregate_id: str
    ) -> Dict[str, Any]:
        """
        Verify event consistency for an aggregate
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID
        
        Returns:
            Consistency report
        """
        logger.info(f"Verifying event consistency for {aggregate_id}")
        
        events = self.event_store.get_events_by_aggregate(topic, aggregate_id)
        
        issues = []
        
        # Check event ordering
        for i in range(1, len(events)):
            if events[i].event_timestamp < events[i-1].event_timestamp:
                issues.append({
                    "type": "ordering",
                    "message": f"Event {events[i].event_id} has earlier timestamp than previous event",
                    "event_id": events[i].event_id,
                })
        
        # Check causation chain
        for i in range(1, len(events)):
            if events[i].causation_id and events[i].causation_id != events[i-1].event_id:
                issues.append({
                    "type": "causation",
                    "message": f"Event {events[i].event_id} causation_id doesn't match previous event",
                    "event_id": events[i].event_id,
                })
        
        return {
            "aggregate_id": aggregate_id,
            "total_events": len(events),
            "issues_found": len(issues),
            "issues": issues,
            "consistent": len(issues) == 0,
        }
    
    def generate_audit_report(
        self,
        topic: str,
        aggregate_id: str
    ) -> Dict[str, Any]:
        """
        Generate audit report for an aggregate
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID
        
        Returns:
            Audit report
        """
        events = self.event_store.get_events_by_aggregate(topic, aggregate_id)
        
        if not events:
            return {
                "aggregate_id": aggregate_id,
                "total_events": 0,
                "message": "No events found",
            }
        
        # Group events by type
        events_by_type = {}
        for event in events:
            event_type = event.event_type
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
        
        # Group events by user
        events_by_user = {}
        for event in events:
            user_id = event.user_id
            if user_id not in events_by_user:
                events_by_user[user_id] = []
            events_by_user[user_id].append(event)
        
        return {
            "aggregate_id": aggregate_id,
            "total_events": len(events),
            "first_event": {
                "event_id": events[0].event_id,
                "event_type": events[0].event_type,
                "timestamp": events[0].event_timestamp.isoformat(),
                "user_id": events[0].user_id,
            },
            "last_event": {
                "event_id": events[-1].event_id,
                "event_type": events[-1].event_type,
                "timestamp": events[-1].event_timestamp.isoformat(),
                "user_id": events[-1].user_id,
            },
            "events_by_type": {
                event_type: len(event_list)
                for event_type, event_list in events_by_type.items()
            },
            "events_by_user": {
                user_id: len(event_list)
                for user_id, event_list in events_by_user.items()
            },
            "timeline": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.event_timestamp.isoformat(),
                    "user_id": event.user_id,
                }
                for event in events
            ],
        }


# ============================================================================
# Convenience Functions
# ============================================================================

def replay_savings_events(
    event_store: EventStore,
    projection_handler: callable
) -> Dict[str, Any]:
    """Replay all savings events"""
    replay = EventReplay(event_store)
    
    topics = [
        "ultracore.savings.accounts.lifecycle",
        "ultracore.savings.accounts.transactions",
        "ultracore.savings.interest",
        "ultracore.savings.fees",
    ]
    
    total_stats = {
        "topics_processed": 0,
        "total_events": 0,
        "total_failed": 0,
        "total_duration": 0,
    }
    
    for topic in topics:
        stats = replay.replay_all_events(topic, projection_handler)
        total_stats["topics_processed"] += 1
        total_stats["total_events"] += stats["events_processed"]
        total_stats["total_failed"] += stats["events_failed"]
        total_stats["total_duration"] += stats["duration_seconds"]
    
    return total_stats
