"""
API Key Management System
For service-to-service authentication and external integrations
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import secrets
import hashlib
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.security.rbac.permissions import Role


class APIKeyScope(str, Enum):
    READ_ONLY = 'READ_ONLY'
    PAYMENTS = 'PAYMENTS'
    ACCOUNTS = 'ACCOUNTS'
    GENERAL_LEDGER = 'GENERAL_LEDGER'
    FULL_ACCESS = 'FULL_ACCESS'


class APIKey:
    """API Key model"""
    
    def __init__(
        self,
        key_id: str,
        key_hash: str,
        owner_id: str,
        name: str,
        scopes: List[APIKeyScope],
        environment: str = 'PRODUCTION'
    ):
        self.key_id = key_id
        self.key_hash = key_hash
        self.owner_id = owner_id
        self.name = name
        self.scopes = scopes
        self.environment = environment
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.last_used: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None
        self.rate_limit_per_minute = 100
        self.allowed_ips: List[str] = []  # IP whitelist


class APIKeyManager:
    """
    API Key Management
    
    Zero-trust principle: API keys have limited scope and expire
    """
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
    
    def generate_api_key(
        self,
        owner_id: str,
        name: str,
        scopes: List[APIKeyScope],
        environment: str = 'PRODUCTION',
        expires_in_days: Optional[int] = 90,
        allowed_ips: Optional[List[str]] = None
    ) -> tuple[str, APIKey]:
        """
        Generate new API key
        
        Returns: (raw_key, APIKey)
        Only the raw key is shown once - never stored in plain text
        """
        # Generate secure random key
        raw_key = f"uk_{'prod' if environment == 'PRODUCTION' else 'dev'}_{secrets.token_urlsafe(32)}"
        
        # Hash the key (only hash is stored)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Generate key ID
        key_id = f"KEY-{secrets.token_hex(8).upper()}"
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            owner_id=owner_id,
            name=name,
            scopes=scopes,
            environment=environment
        )
        
        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        if allowed_ips:
            api_key.allowed_ips = allowed_ips
        
        self.api_keys[key_id] = api_key
        
        # Log key creation
        kafka_store = get_production_kafka_store()
        asyncio.create_task(kafka_store.append_event(
            entity='security',
            event_type='api_key_created',
            event_data={
                'key_id': key_id,
                'owner_id': owner_id,
                'name': name,
                'scopes': [s.value for s in scopes],
                'environment': environment,
                'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None
            },
            aggregate_id=key_id
        ))
        
        return raw_key, api_key
    
    def verify_api_key(self, raw_key: str, request_ip: Optional[str] = None) -> Optional[APIKey]:
        """
        Verify API key
        
        Zero-trust: Check hash, expiry, IP whitelist, active status
        """
        # Hash the provided key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Find matching key
        api_key = next((k for k in self.api_keys.values() if k.key_hash == key_hash), None)
        
        if not api_key:
            return None
        
        # Check if active
        if not api_key.is_active:
            return None
        
        # Check expiry
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            return None
        
        # Check IP whitelist (zero-trust)
        if api_key.allowed_ips and request_ip:
            if request_ip not in api_key.allowed_ips:
                return None
        
        # Update last used
        api_key.last_used = datetime.utcnow()
        
        return api_key
    
    def revoke_api_key(self, key_id: str):
        """Revoke API key"""
        if key_id in self.api_keys:
            self.api_keys[key_id].is_active = False
            
            # Log revocation
            kafka_store = get_production_kafka_store()
            asyncio.create_task(kafka_store.append_event(
                entity='security',
                event_type='api_key_revoked',
                event_data={
                    'key_id': key_id,
                    'revoked_at': datetime.utcnow().isoformat()
                },
                aggregate_id=key_id
            ))


# Global API key manager
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager

