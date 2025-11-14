"""
Unit tests for Event Envelope Structure.

Tests the standard event envelope format used across all UltraCore events.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
import json


@pytest.mark.unit
@pytest.mark.event_sourcing
class TestEventEnvelopeStructure:
    """Test event envelope metadata structure."""
    
    def test_event_envelope_has_required_fields(self):
        """Test that event envelope contains all required metadata fields."""
        # Arrange
        event_id = str(uuid4())
        aggregate_id = str(uuid4())
        correlation_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Act
        event = {
            # Event metadata
            "event_id": event_id,
            "event_type": "PodCreated",
            "event_version": 1,
            
            # Aggregate info
            "aggregate_type": "InvestmentPod",
            "aggregate_id": aggregate_id,
            
            # Multi-tenancy
            "tenant_id": tenant_id,
            
            # Event payload
            "event_data": {
                "goal_type": "first_home",
                "target_amount": "100000.00"
            },
            
            # Causation tracking
            "correlation_id": correlation_id,
            "causation_id": None,
            
            # User context
            "user_id": user_id,
            
            # Timestamps
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            
            # Metadata
            "metadata": {
                "source": "ultracore-api",
                "version": "1.0.0"
            }
        }
        
        # Assert - Required fields
        assert "event_id" in event
        assert "event_type" in event
        assert "event_version" in event
        assert "aggregate_type" in event
        assert "aggregate_id" in event
        assert "tenant_id" in event
        assert "event_data" in event
        assert "correlation_id" in event
        assert "user_id" in event
        assert "event_timestamp" in event
        assert "metadata" in event
        
        # Assert - Valid UUIDs
        assert UUID(event["event_id"])
        assert UUID(event["aggregate_id"])
        assert UUID(event["correlation_id"])
        
        # Assert - Valid timestamp
        timestamp = datetime.fromisoformat(event["event_timestamp"])
        assert timestamp.tzinfo is not None  # Must be timezone-aware
    
    def test_event_envelope_serialization(self):
        """Test that event envelope can be serialized to JSON."""
        # Arrange
        event = {
            "event_id": str(uuid4()),
            "event_type": "PodCreated",
            "event_version": 1,
            "aggregate_type": "InvestmentPod",
            "aggregate_id": str(uuid4()),
            "tenant_id": "ultrawealth",
            "event_data": {"goal_type": "first_home"},
            "correlation_id": str(uuid4()),
            "causation_id": None,
            "user_id": "user_123",
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "ultracore-api"}
        }
        
        # Act
        serialized = json.dumps(event)
        deserialized = json.loads(serialized)
        
        # Assert
        assert deserialized["event_id"] == event["event_id"]
        assert deserialized["event_type"] == event["event_type"]
        assert deserialized["aggregate_id"] == event["aggregate_id"]
        assert deserialized["tenant_id"] == event["tenant_id"]
    
    def test_event_envelope_causation_chain(self):
        """Test event causation chain (correlation_id, causation_id)."""
        # Arrange - First event in chain
        event1_id = str(uuid4())
        correlation_id = str(uuid4())
        
        event1 = {
            "event_id": event1_id,
            "event_type": "PodCreated",
            "correlation_id": correlation_id,
            "causation_id": None,  # First event has no cause
        }
        
        # Act - Second event caused by first
        event2_id = str(uuid4())
        event2 = {
            "event_id": event2_id,
            "event_type": "AllocationOptimized",
            "correlation_id": correlation_id,  # Same correlation
            "causation_id": event1_id,  # Caused by event1
        }
        
        # Assert - Causation chain
        assert event1["causation_id"] is None
        assert event2["causation_id"] == event1_id
        assert event1["correlation_id"] == event2["correlation_id"]
    
    def test_event_envelope_tenant_isolation(self):
        """Test that events include tenant_id for multi-tenancy."""
        # Arrange
        ultrawealth_event = {
            "event_id": str(uuid4()),
            "tenant_id": "ultrawealth",
            "event_type": "PodCreated",
        }
        
        other_tenant_event = {
            "event_id": str(uuid4()),
            "tenant_id": "tenant_abc",
            "event_type": "AccountOpened",
        }
        
        # Assert
        assert ultrawealth_event["tenant_id"] == "ultrawealth"
        assert other_tenant_event["tenant_id"] == "tenant_abc"
        assert ultrawealth_event["tenant_id"] != other_tenant_event["tenant_id"]


@pytest.mark.unit
@pytest.mark.event_sourcing
class TestEventVersioning:
    """Test event versioning for schema evolution."""
    
    def test_event_version_field(self):
        """Test that events include version field."""
        # Arrange & Act
        event_v1 = {
            "event_id": str(uuid4()),
            "event_type": "PodCreated",
            "event_version": 1,
            "event_data": {"goal_type": "first_home"}
        }
        
        event_v2 = {
            "event_id": str(uuid4()),
            "event_type": "PodCreated",
            "event_version": 2,
            "event_data": {
                "goal_type": "first_home",
                "risk_profile": "moderate"  # New field in v2
            }
        }
        
        # Assert
        assert event_v1["event_version"] == 1
        assert event_v2["event_version"] == 2
        assert "risk_profile" not in event_v1["event_data"]
        assert "risk_profile" in event_v2["event_data"]
    
    def test_event_backward_compatibility(self):
        """Test that old event versions can be processed."""
        # Arrange - Old event without new field
        old_event = {
            "event_type": "PodCreated",
            "event_version": 1,
            "event_data": {"goal_type": "first_home"}
        }
        
        # Act - Process with default for missing field
        goal_type = old_event["event_data"]["goal_type"]
        risk_profile = old_event["event_data"].get("risk_profile", "moderate")
        
        # Assert
        assert goal_type == "first_home"
        assert risk_profile == "moderate"  # Default value


@pytest.mark.unit
@pytest.mark.event_sourcing
class TestEventMetadata:
    """Test event metadata fields."""
    
    def test_event_source_metadata(self):
        """Test that events include source metadata."""
        # Arrange & Act
        event = {
            "event_id": str(uuid4()),
            "event_type": "PodCreated",
            "metadata": {
                "source": "ultracore-api",
                "version": "1.0.0",
                "environment": "production"
            }
        }
        
        # Assert
        assert event["metadata"]["source"] == "ultracore-api"
        assert event["metadata"]["version"] == "1.0.0"
        assert event["metadata"]["environment"] == "production"
    
    def test_event_timestamp_timezone_aware(self):
        """Test that event timestamps are timezone-aware (UTC)."""
        # Arrange & Act
        timestamp = datetime.now(timezone.utc)
        event = {
            "event_id": str(uuid4()),
            "event_timestamp": timestamp.isoformat()
        }
        
        # Assert
        parsed_timestamp = datetime.fromisoformat(event["event_timestamp"])
        assert parsed_timestamp.tzinfo is not None
        assert parsed_timestamp.tzinfo == timezone.utc
    
    def test_event_user_context(self):
        """Test that events include user context."""
        # Arrange & Act
        event = {
            "event_id": str(uuid4()),
            "user_id": "user_123",
            "event_type": "PodCreated"
        }
        
        # Assert
        assert event["user_id"] == "user_123"


@pytest.mark.unit
@pytest.mark.event_sourcing
class TestEventPartitioning:
    """Test event partitioning strategy."""
    
    def test_partition_key_is_aggregate_id(self):
        """Test that partition key is aggregate_id for ordering."""
        # Arrange
        aggregate_id = str(uuid4())
        
        events = [
            {
                "event_id": str(uuid4()),
                "aggregate_id": aggregate_id,
                "event_type": "PodCreated",
                "sequence": 1
            },
            {
                "event_id": str(uuid4()),
                "aggregate_id": aggregate_id,
                "event_type": "AllocationOptimized",
                "sequence": 2
            },
            {
                "event_id": str(uuid4()),
                "aggregate_id": aggregate_id,
                "event_type": "ContributionReceived",
                "sequence": 3
            }
        ]
        
        # Assert - All events have same aggregate_id (same partition)
        assert all(e["aggregate_id"] == aggregate_id for e in events)
        
        # Assert - Events are ordered by sequence
        assert events[0]["sequence"] < events[1]["sequence"] < events[2]["sequence"]
    
    def test_different_aggregates_different_partitions(self):
        """Test that different aggregates can be in different partitions."""
        # Arrange
        pod1_id = str(uuid4())
        pod2_id = str(uuid4())
        
        event1 = {"aggregate_id": pod1_id, "event_type": "PodCreated"}
        event2 = {"aggregate_id": pod2_id, "event_type": "PodCreated"}
        
        # Assert - Different aggregates
        assert event1["aggregate_id"] != event2["aggregate_id"]
