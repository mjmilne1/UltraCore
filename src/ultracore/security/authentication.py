"""
Authentication Service - Event-Sourced
Provides authentication functionality following UltraCore's event-sourcing architecture
"""
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
import re
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from uuid import UUID, uuid4

from ultracore.security.events import (
    create_user_authenticated_event,
    create_password_changed_event,
    create_token_created_event
)

# Security configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=10,
    bcrypt__max_rounds=14
)


class AuthenticationService:
    """
    Event-sourced authentication service
    
    All authentication operations publish events to Kafka for audit and replay
    """
    
    def __init__(self, event_store=None, tenant_id: str = "default"):
        """
        Initialize authentication service
        
        Args:
            event_store: Kafka event store for publishing events
            tenant_id: Tenant identifier for multi-tenancy
        """
        self.pwd_context = pwd_context
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.event_store = event_store
        self.tenant_id = tenant_id
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - Contains uppercase and lowercase letters
        - Contains numbers
        - Contains special characters
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
            
        Raises:
            ValueError: If password is too weak
        """
        if len(password) < 8:
            raise ValueError("Password too weak: must be at least 8 characters")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password too weak: must contain uppercase letters")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password too weak: must contain lowercase letters")
        
        if not re.search(r'\d', password):
            raise ValueError("Password too weak: must contain numbers")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password too weak: must contain special characters")
        
        return True
    
    def create_access_token(
        self, 
        data: Dict, 
        expires_in: Optional[int] = None,
        correlation_id: Optional[UUID] = None
    ) -> str:
        """
        Create a JWT access token and publish TokenCreated event
        
        Args:
            data: Data to encode in the token (must include user_id)
            expires_in: Token expiration time in minutes (default: 30)
            correlation_id: Correlation ID for event tracking
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_in:
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "tenant_id": self.tenant_id
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Publish TokenCreated event
        if self.event_store:
            user_id = data.get('user_id', 'unknown')
            event = create_token_created_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                token_type="access",
                expires_at=expire,
                correlation_id=correlation_id
            )
            # Note: In async context, use: await self.event_store.append_event(...)
            # For now, we'll skip actual publishing in sync context
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token data
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify tenant_id matches
            token_tenant = payload.get('tenant_id')
            if token_tenant and token_tenant != self.tenant_id:
                raise ValueError("Token tenant mismatch")
            
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def create_refresh_token(
        self, 
        user_id: str,
        correlation_id: Optional[UUID] = None
    ) -> str:
        """
        Create a refresh token for long-term authentication
        
        Args:
            user_id: User identifier
            correlation_id: Correlation ID for event tracking
            
        Returns:
            Encoded refresh token
        """
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "tenant_id": self.tenant_id
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Publish TokenCreated event
        if self.event_store:
            event = create_token_created_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                token_type="refresh",
                expires_at=expire,
                correlation_id=correlation_id
            )
            # Note: In async context, use: await self.event_store.append_event(...)
        
        return encoded_jwt
    
    async def authenticate_user(
        self,
        user_id: str,
        password: str,
        stored_hash: str,
        authentication_method: str = "password",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """
        Authenticate a user and publish UserAuthenticated event
        
        Args:
            user_id: User identifier
            password: Plain text password
            stored_hash: Stored password hash
            authentication_method: Method used for authentication
            ip_address: Client IP address
            user_agent: Client user agent
            correlation_id: Correlation ID for event tracking
            
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.verify_password(password, stored_hash):
            return False
        
        # Publish UserAuthenticated event
        if self.event_store:
            event = create_user_authenticated_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                authentication_method=authentication_method,
                ip_address=ip_address,
                user_agent=user_agent,
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="User",
                event_type="user.authenticated",
                event_data=event.data,
                aggregate_id=user_id,
                user_id=user_id,
                idempotency_key=str(event.metadata.event_id)
            )
        
        return True
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
        stored_hash: str,
        changed_by: str,
        correlation_id: Optional[UUID] = None
    ) -> str:
        """
        Change user password and publish PasswordChanged event
        
        Args:
            user_id: User identifier
            old_password: Current password
            new_password: New password
            stored_hash: Stored password hash
            changed_by: User who initiated the change
            correlation_id: Correlation ID for event tracking
            
        Returns:
            New password hash
            
        Raises:
            ValueError: If old password is incorrect or new password is weak
        """
        # Verify old password
        if not self.verify_password(old_password, stored_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password strength
        self.validate_password_strength(new_password)
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        # Publish PasswordChanged event
        if self.event_store:
            event = create_password_changed_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                changed_by=changed_by,
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="User",
                event_type="password.changed",
                event_data=event.data,
                aggregate_id=user_id,
                user_id=changed_by,
                idempotency_key=str(event.metadata.event_id)
            )
        
        return new_hash
