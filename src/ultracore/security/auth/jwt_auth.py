"""
JWT Authentication System
Secure token-based authentication with refresh tokens
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import uuid

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


# Security configuration
# SECURITY FIX: Load JWT secret from environment variable
import os

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")

if len(SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters for security")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class PasswordHasher:
    """Password hashing utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Short-lived token for API access
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create refresh token
        
        Long-lived token for obtaining new access tokens
        """
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID for revocation
        }
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify and decode JWT token
        
        Raises HTTPException if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class User:
    """User model"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        hashed_password: str,
        roles: list = None,
        is_active: bool = True,
        mfa_enabled: bool = False
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.roles = roles or []
        self.is_active = is_active
        self.mfa_enabled = mfa_enabled
        self.created_at = datetime.now(timezone.utc)
        self.last_login: Optional[datetime] = None


class UserRepository:
    """User storage and retrieval"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Create default admin user"""
        admin_id = "USR-ADMIN-001"
        admin = User(
            user_id=admin_id,
            username="admin",
            email="admin@ultracore.com",
            hashed_password=PasswordHasher.hash_password("UltraCore2024!"),
            roles=["SUPER_ADMIN"],
            is_active=True
        )
        self.users[admin_id] = admin
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: list = None
    ) -> User:
        """Create new user"""
        user_id = f"USR-{uuid.uuid4().hex[:12].upper()}"
        
        # Check if username/email exists
        if any(u.username == username for u in self.users.values()):
            raise ValueError(f"Username '{username}' already exists")
        
        if any(u.email == email for u in self.users.values()):
            raise ValueError(f"Email '{email}' already registered")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=PasswordHasher.hash_password(password),
            roles=roles or ["USER"]
        )
        
        self.users[user_id] = user
        
        # Publish to Kafka
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='security',
            event_type='user_created',
            event_data={
                'user_id': user_id,
                'username': username,
                'email': email,
                'roles': user.roles,
                'created_at': user.created_at.isoformat()
            },
            aggregate_id=user_id
        )
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return next((u for u in self.users.values() if u.username == username), None)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return next((u for u in self.users.values() if u.email == email), None)


class AuthenticationService:
    """Authentication service"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.token_manager = TokenManager()
        self.revoked_tokens: set = set()  # In production: use Redis
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Returns User if valid, None otherwise
        """
        user = self.user_repo.get_user_by_username(username)
        
        if not user:
            return None
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        if not PasswordHasher.verify_password(password, user.hashed_password):
            # Log failed attempt
            await self._log_failed_login(username)
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Log successful login
        await self._log_successful_login(user.user_id)
        
        return user
    
    async def login(self, username: str, password: str) -> Dict:
        """
        Login and return tokens
        
        Returns access token and refresh token
        """
        user = await self.authenticate_user(username, password)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            data={"sub": user.user_id, "username": user.username, "roles": user.roles}
        )
        
        refresh_token = self.token_manager.create_refresh_token(user.user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles
            }
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token
        
        Returns new access token
        """
        # Verify refresh token
        payload = self.token_manager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Check if revoked
        jti = payload.get("jti")
        if jti in self.revoked_tokens:
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Get user
        user_id = payload.get("sub")
        user = self.user_repo.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Create new access token
        access_token = self.token_manager.create_access_token(
            data={"sub": user.user_id, "username": user.username, "roles": user.roles}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    async def logout(self, refresh_token: str):
        """
        Logout and revoke refresh token
        
        Adds token to revocation list
        """
        payload = self.token_manager.verify_token(refresh_token)
        jti = payload.get("jti")
        
        if jti:
            self.revoked_tokens.add(jti)
        
        # Log logout
        user_id = payload.get("sub")
        await self._log_logout(user_id)
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> User:
        """
        Get current authenticated user from token
        
        FastAPI dependency for protected routes
        """
        token = credentials.credentials
        
        payload = self.token_manager.verify_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        user = self.user_repo.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user
    
    async def _log_successful_login(self, user_id: str):
        """Log successful login event"""
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='security',
            event_type='login_successful',
            event_data={
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=user_id
        )
    
    async def _log_failed_login(self, username: str):
        """Log failed login attempt"""
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='security',
            event_type='login_failed',
            event_data={
                'username': username,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=username
        )
    
    async def _log_logout(self, user_id: str):
        """Log logout event"""
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='security',
            event_type='logout',
            event_data={
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=user_id
        )


# Global authentication service
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service


# FastAPI dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """FastAPI dependency for protected routes"""
    auth_service = get_auth_service()
    return await auth_service.get_current_user(credentials)
