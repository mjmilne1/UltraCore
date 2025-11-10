"""
Event Publishers - Domain Event Publishing
"""
from ultracore.infrastructure.event_bus.bus import get_event_bus, Event, EventTopic


class DomainEventPublisher:
    """Publish domain events to event bus"""
    
    @staticmethod
    async def publish_loan_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish loan event"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.LOAN_EVENTS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_payment_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish payment event"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.PAYMENT_EVENTS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_fraud_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish fraud detection event"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.FRAUD_EVENTS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_compliance_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish compliance event"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.COMPLIANCE_EVENTS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_order_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish order event (trading/investment)"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.ORDERS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_fill_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish fill event (order execution)"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.FILLS,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
    
    @staticmethod
    async def publish_funding_event(event_type: str, aggregate_id: str, event_data: dict):
        """Publish funding event"""
        bus = get_event_bus()
        event = Event(
            topic=EventTopic.FUNDING,
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id
        )
        await bus.publish(event)
