"""
Event Handlers - Subscribe and handle events
"""
from ultracore.infrastructure.event_bus.bus import Event, EventTopic


class ComplianceEventHandler:
    """Handle compliance-related events"""
    
    @staticmethod
    async def handle_kyc_event(event: Event):
        """Handle KYC verification events"""
        print(f"📋 Compliance: {event.event_type} - {event.aggregate_id}")
        
        # In production: Log to audit system, notify compliance team
        if event.event_type == 'KYCVerified':
            risk_score = event.event_data.get('risk_score', 0)
            if risk_score > 70:
                print(f"⚠️  HIGH RISK customer detected: {event.aggregate_id}")
    
    @staticmethod
    async def handle_aml_event(event: Event):
        """Handle AML/CTF events"""
        print(f"🔍 AML: {event.event_type}")
        
        # Check for suspicious patterns
        if 'aml_flags' in event.event_data:
            flags = event.event_data['aml_flags']
            if flags:
                print(f"🚨 AML FLAGS: {', '.join(flags)}")


class FraudEventHandler:
    """Handle fraud detection events"""
    
    @staticmethod
    async def handle_fraud_alert(event: Event):
        """Handle fraud alerts"""
        print(f"🚨 Fraud Alert: {event.event_type} - {event.aggregate_id}")
        
        fraud_score = event.event_data.get('fraud_score', 0)
        if fraud_score > 60:
            print(f"   Blocking transaction - Score: {fraud_score}")
            # In production: Block card, notify customer, alert fraud team


class OrderEventHandler:
    """Handle trading order events"""
    
    @staticmethod
    async def handle_order_placed(event: Event):
        """Handle order placed"""
        print(f"📊 Order Placed: {event.aggregate_id}")
        print(f"   {event.event_data.get('symbol')} - {event.event_data.get('quantity')} shares")
    
    @staticmethod
    async def handle_order_filled(event: Event):
        """Handle order filled"""
        print(f"✅ Order Filled: {event.aggregate_id}")
        print(f"   Price: ")


class FundingEventHandler:
    """Handle funding events"""
    
    @staticmethod
    async def handle_deposit(event: Event):
        """Handle deposit"""
        print(f"💰 Deposit:  to {event.aggregate_id}")
    
    @staticmethod
    async def handle_withdrawal(event: Event):
        """Handle withdrawal"""
        print(f"💸 Withdrawal:  from {event.aggregate_id}")


async def setup_event_handlers():
    """Setup all event handlers"""
    from ultracore.infrastructure.event_bus.bus import get_event_bus
    
    bus = get_event_bus()
    
    # Compliance handlers
    await bus.subscribe(EventTopic.COMPLIANCE_EVENTS, ComplianceEventHandler.handle_kyc_event)
    await bus.subscribe(EventTopic.COMPLIANCE_EVENTS, ComplianceEventHandler.handle_aml_event)
    
    # Fraud handlers
    await bus.subscribe(EventTopic.FRAUD_EVENTS, FraudEventHandler.handle_fraud_alert)
    
    # Trading handlers
    await bus.subscribe(EventTopic.ORDERS, OrderEventHandler.handle_order_placed)
    await bus.subscribe(EventTopic.FILLS, OrderEventHandler.handle_order_filled)
    
    # Funding handlers
    await bus.subscribe(EventTopic.FUNDING, FundingEventHandler.handle_deposit)
    await bus.subscribe(EventTopic.FUNDING, FundingEventHandler.handle_withdrawal)
    
    print("✓ Event handlers configured")
