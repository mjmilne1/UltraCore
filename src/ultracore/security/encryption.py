"""
Encryption Service - Event-Sourced
Provides encryption and decryption functionality following UltraCore's event-sourcing architecture
"""
from typing import Optional, Union
import base64
import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
from uuid import UUID, uuid4

from ultracore.security.events import create_data_encrypted_event


class EncryptionService:
    """
    Event-sourced encryption service for data encryption and decryption
    
    Publishes DataEncrypted events for audit trail
    """
    
    def __init__(self, encryption_key: Optional[str] = None, event_store=None, tenant_id: str = "default"):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Base64-encoded encryption key (optional)
            event_store: Kafka event store for publishing events
            tenant_id: Tenant identifier for multi-tenancy
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Try to get from environment
            env_key = os.environ.get('ENCRYPTION_KEY')
            if env_key:
                self.key = env_key.encode()
            else:
                # Generate a new key
                self.key = Fernet.generate_key()
        
        self.fernet = Fernet(self.key)
        self.event_store = event_store
        self.tenant_id = tenant_id
    
    async def encrypt(
        self, 
        data: Union[str, bytes],
        user_id: str = "system",
        data_type: str = "generic",
        field_name: str = "data",
        correlation_id: Optional[UUID] = None
    ) -> str:
        """
        Encrypt data using Fernet symmetric encryption and publish DataEncrypted event
        
        Args:
            data: Data to encrypt (string or bytes)
            user_id: User performing the encryption
            data_type: Type of data being encrypted
            field_name: Name of the field being encrypted
            correlation_id: Correlation ID for event tracking
            
        Returns:
            Base64-encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self.fernet.encrypt(data)
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        # Publish DataEncrypted event
        if self.event_store:
            event = create_data_encrypted_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                data_type=data_type,
                field_name=field_name,
                encryption_algorithm="Fernet",
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="EncryptedData",
                event_type="data.encrypted",
                event_data=event.data,
                aggregate_id=f"{data_type}-{field_name}",
                user_id=user_id,
                idempotency_key=str(event.metadata.event_id)
            )
        
        return encrypted_b64
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet symmetric encryption
        
        Note: Decryption events are not published to avoid excessive event volume
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted data as string
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    async def encrypt_field(
        self, 
        field_value: str, 
        field_name: str = "",
        user_id: str = "system",
        data_type: str = "field",
        correlation_id: Optional[UUID] = None
    ) -> str:
        """
        Encrypt a specific field value
        
        Args:
            field_value: Value to encrypt
            field_name: Name of the field (for logging/auditing)
            user_id: User performing the encryption
            data_type: Type of data being encrypted
            correlation_id: Correlation ID for event tracking
            
        Returns:
            Encrypted field value
        """
        return await self.encrypt(
            field_value, 
            user_id=user_id,
            data_type=data_type,
            field_name=field_name or "unknown",
            correlation_id=correlation_id
        )
    
    def decrypt_field(self, encrypted_value: str, field_name: str = "") -> str:
        """
        Decrypt a specific field value
        
        Args:
            encrypted_value: Encrypted value
            field_name: Name of the field (for logging/debugging)
            
        Returns:
            Decrypted field value
        """
        return self.decrypt(encrypted_value)
    
    def hash_data(self, data: Union[str, bytes], algorithm: str = "sha256") -> str:
        """
        Create a hash of data (one-way encryption)
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm to use (sha256, sha512, etc.)
            
        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(data).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def generate_key(self) -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode('utf-8')
    
    def derive_key_from_password(
        self, 
        password: str, 
        salt: Optional[bytes] = None
    ) -> tuple[str, str]:
        """
        Derive an encryption key from a password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (optional, will generate if not provided)
            
        Returns:
            Tuple of (key, salt) both as base64-encoded strings
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        return key.decode('utf-8'), salt_b64
    
    async def encrypt_sensitive_data(
        self, 
        data: dict,
        user_id: str = "system",
        correlation_id: Optional[UUID] = None
    ) -> dict:
        """
        Encrypt sensitive fields in a dictionary
        
        Automatically encrypts fields with common sensitive names
        
        Args:
            data: Dictionary with potentially sensitive data
            user_id: User performing the encryption
            correlation_id: Correlation ID for event tracking
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        sensitive_fields = {
            'password', 'ssn', 'social_security', 'credit_card', 
            'card_number', 'cvv', 'pin', 'secret', 'api_key',
            'private_key', 'token', 'account_number'
        }
        
        encrypted_data = data.copy()
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(value, str):
                    encrypted_data[key] = await self.encrypt(
                        value,
                        user_id=user_id,
                        data_type="sensitive_field",
                        field_name=key,
                        correlation_id=correlation_id
                    )
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, data: dict) -> dict:
        """
        Decrypt sensitive fields in a dictionary
        
        Args:
            data: Dictionary with encrypted sensitive data
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        sensitive_fields = {
            'password', 'ssn', 'social_security', 'credit_card', 
            'card_number', 'cvv', 'pin', 'secret', 'api_key',
            'private_key', 'token', 'account_number'
        }
        
        decrypted_data = data.copy()
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(value, str):
                    try:
                        decrypted_data[key] = self.decrypt(value)
                    except ValueError:
                        # If decryption fails, keep original value
                        pass
        
        return decrypted_data
    
    def get_key(self) -> str:
        """
        Get the current encryption key
        
        Returns:
            Base64-encoded encryption key
        """
        return self.key.decode('utf-8')
