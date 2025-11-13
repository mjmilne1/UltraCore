"""MFA Security Module"""

from ultracore.security.mfa.totp_service import TOTPService, create_totp_service
from ultracore.security.mfa.event_producer import MFAEventProducer, create_mfa_event_producer
from ultracore.security.mfa.events import (
    MFAEnabledEvent,
    MFADisabledEvent,
    MFAVerificationSuccessEvent,
    MFAVerificationFailedEvent,
    BackupCodeUsedEvent,
    BackupCodesRegeneratedEvent,
    MFABruteForceDetectedEvent,
    MFAAnomalyDetectedEvent,
    MFATopics
)

__all__ = [
    "TOTPService",
    "create_totp_service",
    "MFAEventProducer",
    "create_mfa_event_producer",
    "MFAEnabledEvent",
    "MFADisabledEvent",
    "MFAVerificationSuccessEvent",
    "MFAVerificationFailedEvent",
    "BackupCodeUsedEvent",
    "BackupCodesRegeneratedEvent",
    "MFABruteForceDetectedEvent",
    "MFAAnomalyDetectedEvent",
    "MFATopics"
]
