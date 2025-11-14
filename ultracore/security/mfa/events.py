"""
MFA Events for Kafka Event Sourcing
All MFA lifecycle events are published to Kafka for audit trail and analytics
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional
import json


# ============================================================================
# MFA Events
# ============================================================================

@dataclass
class MFAEvent:
    """Base class for MFA events"""
    event_id: str
    user_id: UUID
    tenant_id: UUID
    timestamp: datetime
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert event to dictionary for Kafka"""
        return {
            "event_id": self.event_id,
            "user_id": str(self.user_id),
            "tenant_id": str(self.tenant_id),
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "event_type": self.__class__.__name__
        }


@dataclass
class MFAEnabledEvent(MFAEvent):
    """MFA was enabled for a user"""
    backup_codes_generated: int = 10
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["backup_codes_generated"] = self.backup_codes_generated
        return data


@dataclass
class MFADisabledEvent(MFAEvent):
    """MFA was disabled for a user"""
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["reason"] = self.reason
        return data


@dataclass
class MFAVerificationSuccessEvent(MFAEvent):
    """TOTP verification succeeded"""
    verification_method: str = "totp"  # "totp" or "backup_code"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["verification_method"] = self.verification_method
        data["ip_address"] = self.ip_address
        data["user_agent"] = self.user_agent
        data["device_fingerprint"] = self.device_fingerprint
        return data


@dataclass
class MFAVerificationFailedEvent(MFAEvent):
    """TOTP verification failed"""
    verification_method: str = "totp"  # "totp" or "backup_code"
    failure_reason: str = "invalid_token"  # "invalid_token", "replay_attack", "expired", etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["verification_method"] = self.verification_method
        data["failure_reason"] = self.failure_reason
        data["ip_address"] = self.ip_address
        data["user_agent"] = self.user_agent
        data["device_fingerprint"] = self.device_fingerprint
        return data


@dataclass
class BackupCodeUsedEvent(MFAEvent):
    """Backup code was used"""
    codes_remaining: int = 0
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["codes_remaining"] = self.codes_remaining
        return data


@dataclass
class BackupCodesRegeneratedEvent(MFAEvent):
    """Backup codes were regenerated"""
    new_code_count: int = 10
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["new_code_count"] = self.new_code_count
        return data


@dataclass
class MFABruteForceDetectedEvent(MFAEvent):
    """Brute force attack detected on MFA"""
    failed_attempts: int = 0
    time_window_seconds: int = 300
    ip_address: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["failed_attempts"] = self.failed_attempts
        data["time_window_seconds"] = self.time_window_seconds
        data["ip_address"] = self.ip_address
        return data


@dataclass
class MFAAnomalyDetectedEvent(MFAEvent):
    """Anomaly detected in MFA usage"""
    anomaly_type: str = "unknown"  # "unusual_location", "unusual_time", "unusual_device", etc.
    anomaly_score: float = 0.0  # 0.0-1.0
    details: dict = None
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["anomaly_type"] = self.anomaly_type
        data["anomaly_score"] = self.anomaly_score
        data["details"] = self.details
        return data


# ============================================================================
# Kafka Topics
# ============================================================================

class MFATopics:
    """Kafka topics for MFA events"""
    
    MFA_LIFECYCLE = "ultracore.mfa.lifecycle"  # Enable/disable events
    MFA_VERIFICATION = "ultracore.mfa.verification"  # Verification events
    MFA_SECURITY = "ultracore.mfa.security"  # Security events (brute force, anomalies)
    MFA_BACKUP_CODES = "ultracore.mfa.backup_codes"  # Backup code events
