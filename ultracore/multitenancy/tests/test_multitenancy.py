"""Multi-Tenancy System Tests"""
import pytest
from datetime import datetime
from decimal import Decimal

from ..events import TenantTier, TenantStatus
from ..models import TenantConfig
from ..aggregates.tenant_aggregate import TenantAggregate
from ..encryption import PasswordEncryption, hash_master_password

def test_tenant_aggregate_creation():
    """Test tenant aggregate creation"""
    aggregate = TenantAggregate(tenant_id="test-123")
    aggregate = aggregate.create_tenant(
        tenant_name="Test Tenant",
        tier=TenantTier.ENTERPRISE,
        owner_email="test@example.com",
        created_by="test_user"
    )
    
    assert aggregate.tenant_name == "Test Tenant"
    assert aggregate.tier == TenantTier.ENTERPRISE
    assert aggregate.status == TenantStatus.PROVISIONING
    assert len(aggregate.events) == 1

def test_password_encryption():
    """Test password encryption/decryption"""
    master_password = "super_secret_master_password"
    encryption = PasswordEncryption(master_password)
    
    original_password = "tenant_db_password_123"
    encrypted = encryption.encrypt(original_password)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == original_password
    assert encrypted != original_password

def test_tenant_config_model():
    """Test tenant configuration model"""
    config = TenantConfig(
        tenant_id="test-456",
        tenant_name="Test Config",
        tier=TenantTier.STANDARD,
        status=TenantStatus.ACTIVE,
        owner_email="config@example.com",
        db_host="localhost",
        db_port=5432,
        db_name="test_db",
        schema_name="tenant_test"
    )
    
    assert config.tenant_id == "test-456"
    assert config.tier == TenantTier.STANDARD
    assert config.schema_name == "tenant_test"
    
    # Test to_dict
    config_dict = config.to_dict()
    assert config_dict["tenant_id"] == "test-456"
    assert config_dict["tier"] == "standard"

def test_tenant_lifecycle():
    """Test complete tenant lifecycle"""
    aggregate = TenantAggregate(tenant_id="lifecycle-test")
    
    # Create
    aggregate = aggregate.create_tenant(
        "Lifecycle Test",
        TenantTier.ENTERPRISE,
        "lifecycle@example.com",
        "admin"
    )
    assert aggregate.status == TenantStatus.PROVISIONING
    
    # Provision
    aggregate = aggregate.start_provisioning(
        TenantTier.ENTERPRISE,
        db_name="ultracore_lifecycle_test"
    )
    
    # Complete database creation
    aggregate = aggregate.complete_database_creation(
        "localhost", 5432, "ultracore_lifecycle_test", "uc_lifecycle"
    )
    
    # Complete migrations
    aggregate = aggregate.complete_migrations("1.0.0", 50)
    
    # Activate
    aggregate = aggregate.activate()
    assert aggregate.status == TenantStatus.ACTIVE
    
    # Suspend
    aggregate = aggregate.suspend("Payment overdue", "admin")
    assert aggregate.status == TenantStatus.SUSPENDED
    
    # Reactivate
    aggregate = aggregate.reactivate("admin")
    assert aggregate.status == TenantStatus.ACTIVE
    
    # Verify event count
    assert len(aggregate.events) == 7

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
