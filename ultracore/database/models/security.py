"""
Security Database Models
Comprehensive PostgreSQL schema for security entities
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, DECIMAL, ForeignKey, Index, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ultracore.database.base import Base


# ============================================================================
# Users & Authentication
# ============================================================================

class User(Base):
    """User account with authentication"""
    __tablename__ = "users"
    
    # Primary key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    # Authentication
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(50))
    
    # Role & Permissions
    role = Column(String(50), nullable=False, index=True)  # super_admin, admin, manager, officer, customer
    permissions = Column(ARRAY(String), default=[])
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_locked = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))  # TOTP secret (encrypted)
    
    # Password policy
    password_changed_at = Column(DateTime)
    password_expires_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Trust score (for AI-powered access control)
    trust_score = Column(DECIMAL(5, 2), default=50.0)  # 0-100
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    last_login_ip = Column(INET)
    
    # Relationships
    mfa_backup_codes = relationship("MFABackupCode", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="user")
    devices = relationship("TrustedDevice", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_tenant_role", "tenant_id", "role"),
        Index("idx_users_email_active", "email", "is_active"),
    )


class MFABackupCode(Base):
    """MFA backup codes for account recovery"""
    __tablename__ = "mfa_backup_codes"
    
    code_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    code_hash = Column(String(255), nullable=False)  # Hashed backup code
    used_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="mfa_backup_codes")


class RefreshToken(Base):
    """JWT refresh tokens"""
    __tablename__ = "refresh_tokens"
    
    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime)
    
    # Device info
    device_fingerprint = Column(String(255))
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    # Indexes
    __table_args__ = (
        Index("idx_refresh_tokens_user_expires", "user_id", "expires_at"),
    )


class TrustedDevice(Base):
    """Trusted devices for users"""
    __tablename__ = "trusted_devices"
    
    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    device_fingerprint = Column(String(255), nullable=False, index=True)
    device_name = Column(String(255))  # e.g., "iPhone 13 Pro"
    device_type = Column(String(50))  # mobile, desktop, tablet
    
    trust_score = Column(DECIMAL(5, 2), default=50.0)  # 0-100
    is_trusted = Column(Boolean, default=False)
    
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    last_ip_address = Column(INET)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="devices")


# ============================================================================
# Security Events & Audit
# ============================================================================

class SecurityEvent(Base):
    """Security events for audit trail and threat detection"""
    __tablename__ = "security_events"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # login_attempt, access_denied, fraud_detected, etc.
    event_category = Column(String(50), nullable=False, index=True)  # authentication, authorization, threat, incident
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Context
    ip_address = Column(INET, index=True)
    device_fingerprint = Column(String(255))
    user_agent = Column(Text)
    geolocation = Column(JSON)  # {latitude, longitude, city, country}
    
    # Details
    description = Column(Text)
    metadata = Column(JSON)  # Additional event-specific data
    
    # Risk assessment
    risk_score = Column(DECIMAL(5, 2))  # 0-100
    fraud_score = Column(DECIMAL(5, 2))  # 0-1
    anomaly_score = Column(DECIMAL(5, 2))  # 0-1
    
    # Response
    action_taken = Column(String(50))  # allow, deny, challenge, block, lock
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="security_events")
    
    # Indexes
    __table_args__ = (
        Index("idx_security_events_tenant_type", "tenant_id", "event_type"),
        Index("idx_security_events_user_timestamp", "user_id", "timestamp"),
        Index("idx_security_events_severity_timestamp", "severity", "timestamp"),
        Index("idx_security_events_ip", "ip_address"),
    )


class ThreatEvent(Base):
    """Detected security threats"""
    __tablename__ = "threat_events"
    
    threat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    # Threat details
    threat_type = Column(String(100), nullable=False, index=True)  # fraud, brute_force, account_takeover, etc.
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    status = Column(String(50), nullable=False, index=True)  # detected, investigating, mitigated, resolved
    
    # Description
    description = Column(Text, nullable=False)
    indicators = Column(ARRAY(String))  # List of threat indicators
    
    # Affected entities
    affected_user_ids = Column(ARRAY(UUID(as_uuid=True)))
    affected_account_ids = Column(ARRAY(UUID(as_uuid=True)))
    affected_transaction_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    # Detection
    detection_method = Column(String(100))  # ml_model, rule_based, manual
    confidence = Column(DECIMAL(5, 2))  # 0-100
    
    # Response
    response_action = Column(String(100))  # block, lock, alert, escalate
    response_status = Column(String(50))  # pending, executed, failed
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    mitigated_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index("idx_threat_events_tenant_type", "tenant_id", "threat_type"),
        Index("idx_threat_events_severity_status", "severity", "status"),
    )


class SecurityIncident(Base):
    """Security incidents requiring investigation"""
    __tablename__ = "security_incidents"
    
    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    # Incident details
    incident_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # open, investigating, resolved, closed
    priority = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Description
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"))
    
    # Related events
    related_threat_ids = Column(ARRAY(UUID(as_uuid=True)))
    related_event_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    # Timeline
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index("idx_security_incidents_tenant_status", "tenant_id", "status"),
        Index("idx_security_incidents_severity_priority", "severity", "priority"),
    )


# ============================================================================
# Threat Intelligence
# ============================================================================

class ThreatIntelligence(Base):
    """Threat intelligence data"""
    __tablename__ = "threat_intelligence"
    
    intel_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Indicator
    indicator_type = Column(String(50), nullable=False, index=True)  # ip, domain, email, hash
    indicator_value = Column(String(500), nullable=False, index=True)
    
    # Threat info
    threat_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(DECIMAL(5, 2), nullable=False)  # 0-100
    
    # Source
    source = Column(String(100), nullable=False)  # internal, virustotal, abuseipdb, etc.
    source_url = Column(Text)
    
    # Details
    description = Column(Text)
    metadata = Column(JSON)
    
    # Validity
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_threat_intel_indicator", "indicator_type", "indicator_value"),
        Index("idx_threat_intel_active_expires", "is_active", "expires_at"),
    )


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimitEntry(Base):
    """Rate limit tracking"""
    __tablename__ = "rate_limit_entries"
    
    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ip_address = Column(INET, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    
    # Limits
    request_count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False)
    
    # Adaptive limits (ML-based)
    base_limit = Column(Integer, nullable=False)
    adaptive_limit = Column(Integer, nullable=False)
    trust_multiplier = Column(DECIMAL(5, 2), default=1.0)
    
    # Status
    is_blocked = Column(Boolean, default=False)
    blocked_until = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_rate_limit_user_endpoint", "user_id", "endpoint"),
        Index("idx_rate_limit_ip_endpoint", "ip_address", "endpoint"),
        Index("idx_rate_limit_window", "window_start", "window_end"),
    )


# ============================================================================
# Audit Log
# ============================================================================

class AuditLog(Base):
    """Comprehensive audit log for compliance"""
    __tablename__ = "audit_log"
    
    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), index=True)
    
    # Action
    action = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)
    
    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_log_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_audit_log_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_log_entity", "entity_type", "entity_id"),
    )
