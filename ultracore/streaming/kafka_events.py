"""
Kafka Event Streaming for Holdings
Event-driven architecture for real-time position tracking
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json
import asyncio
from collections import defaultdict

class EventType(str, Enum):
    # Position Events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    POSITION_REBALANCED = "position_rebalanced"
    
    # Trade Events
    TRADE_EXECUTED = "trade_executed"
    TRADE_SETTLED = "trade_settled"
    TRADE_CANCELLED = "trade_cancelled"
    
    # Corporate Action Events
    DIVIDEND_RECEIVED = "dividend_received"
    STOCK_SPLIT = "stock_split"
    RIGHTS_ISSUE = "rights_issue"
    
    # Valuation Events
    POSITION_VALUED = "position_valued"
    PORTFOLIO_VALUED = "portfolio_valued"
    
    # Rebalancing Events
    REBALANCING_TRIGGERED = "rebalancing_triggered"
    REBALANCING_COMPLETED = "rebalancing_completed"

class KafkaEventProducer:
    """
    Kafka-like event producer for holdings events
    In production, this would use actual Kafka (kafka-python or confluent-kafka)
    """
    
    def __init__(self):
        self.topics = {
            "holdings.positions": [],
            "holdings.trades": [],
            "holdings.valuations": [],
            "holdings.corporate_actions": [],
            "holdings.rebalancing": []
        }
        self.subscribers = defaultdict(list)
    
    async def produce(
        self,
        topic: str,
        event_type: EventType,
        data: Dict[str, Any],
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Produce event to Kafka topic
        
        Args:
            topic: Kafka topic name
            event_type: Type of event
            data: Event payload
            key: Partition key (e.g., client_id or position_id)
        """
        
        event = {
            "event_id": f"evt-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "event_type": event_type,
            "topic": topic,
            "key": key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "version": "1.0"
        }
        
        # Store event (in production, send to Kafka)
        if topic not in self.topics:
            self.topics[topic] = []
        
        self.topics[topic].append(event)
        
        # Notify subscribers (simulating Kafka consumers)
        await self._notify_subscribers(topic, event)
        
        print(f"📤 Event produced: {event_type} → {topic}")
        
        return event
    
    def subscribe(
        self,
        topic: str,
        callback: Callable
    ):
        """Subscribe to topic (simulating Kafka consumer)"""
        self.subscribers[topic].append(callback)
        print(f"📥 Subscribed to: {topic}")
    
    async def _notify_subscribers(self, topic: str, event: Dict[str, Any]):
        """Notify all subscribers of new event"""
        for callback in self.subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"❌ Subscriber error: {e}")
    
    def get_events(
        self,
        topic: str,
        event_type: Optional[EventType] = None,
        key: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query events from topic
        (In production, use Kafka Streams or KSQL)
        """
        events = self.topics.get(topic, [])
        
        # Filter by event type
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        # Filter by key
        if key:
            events = [e for e in events if e["key"] == key]
        
        return events[-limit:]
    
    def get_event_stream(
        self,
        topic: str,
        from_timestamp: Optional[str] = None
    ):
        """
        Get event stream (generator)
        Simulates Kafka consumer reading stream
        """
        events = self.topics.get(topic, [])
        
        if from_timestamp:
            events = [
                e for e in events 
                if e["timestamp"] >= from_timestamp
            ]
        
        for event in events:
            yield event

# Global Kafka producer
kafka_producer = KafkaEventProducer()


class EventSourcingStore:
    """
    Event sourcing store for position state reconstruction
    Implements CQRS pattern
    """
    
    def __init__(self):
        self.event_store = []
        self.snapshots = {}
    
    def append_event(self, event: Dict[str, Any]):
        """Append event to event store"""
        self.event_store.append(event)
    
    def get_events_for_aggregate(
        self,
        aggregate_id: str,
        aggregate_type: str = "position"
    ) -> List[Dict[str, Any]]:
        """Get all events for an aggregate (e.g., position)"""
        return [
            e for e in self.event_store
            if e.get("key") == aggregate_id
        ]
    
    def create_snapshot(
        self,
        aggregate_id: str,
        state: Dict[str, Any]
    ):
        """Create snapshot of current state for performance"""
        self.snapshots[aggregate_id] = {
            "aggregate_id": aggregate_id,
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_count": len(self.get_events_for_aggregate(aggregate_id))
        }
    
    def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Get latest snapshot"""
        return self.snapshots.get(aggregate_id)
    
    def reconstruct_state(
        self,
        aggregate_id: str,
        event_handlers: Dict[EventType, Callable]
    ) -> Dict[str, Any]:
        """
        Reconstruct current state from events
        This is the core of Event Sourcing
        """
        
        # Start with snapshot if available
        snapshot = self.get_snapshot(aggregate_id)
        if snapshot:
            state = snapshot["state"].copy()
            events = self.get_events_for_aggregate(aggregate_id)
            # Only replay events after snapshot
            events = [
                e for e in events
                if e["timestamp"] > snapshot["timestamp"]
            ]
        else:
            state = {}
            events = self.get_events_for_aggregate(aggregate_id)
        
        # Replay events to reconstruct state
        for event in events:
            event_type = event["event_type"]
            if event_type in event_handlers:
                state = event_handlers[event_type](state, event["data"])
        
        return state

# Global event sourcing store
event_store = EventSourcingStore()
