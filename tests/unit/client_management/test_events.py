"""
Unit tests for Client Management Events
"""
import pytest
from datetime import datetime
from ultracore.client_management.events import (
    ClientOnboardedEvent,
    ClientUpdatedEvent
)


class TestClientOnboardedEvent:
    """Test ClientOnboardedEvent"""
    
    def test_create_client_onboarded_event(self):
        """Test creating a client onboarded event"""
        event = ClientOnboardedEvent(
            aggregate_id="CLIENT-001",
            tenant_id="TENANT-001",
            client_type="individual"
        )
        
        assert event.aggregate_id == "CLIENT-001"
        assert event.tenant_id == "TENANT-001"
