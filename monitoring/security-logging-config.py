"""
UltraCore Security Logging Configuration
Implements structured security logging with proper sanitization and audit trails
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import hashlib

# ============================================================================
# Security Event Types
# ============================================================================
class SecurityEventType:
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_ISSUED = "auth.token.issued"
    TOKEN_EXPIRED = "auth.token.expired"
    TOKEN_REVOKED = "auth.token.revoked"
    
    # Authorization
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PRIVILEGE_ESCALATION = "authz.privilege.escalation"
    
    # Data Access
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    SENSITIVE_DATA_ACCESS = "data.sensitive.access"
    
    # Security Incidents
    SQL_INJECTION_ATTEMPT = "incident.sql_injection"
    XSS_ATTEMPT = "incident.xss"
    CSRF_ATTEMPT = "incident.csrf"
    PATH_TRAVERSAL_ATTEMPT = "incident.path_traversal"
    RATE_LIMIT_EXCEEDED = "incident.rate_limit"
    
    # Infrastructure
    DB_CONNECTION_FAILURE = "infra.db.connection.failure"
    KAFKA_AUTH_FAILURE = "infra.kafka.auth.failure"
    REDIS_AUTH_FAILURE = "infra.redis.auth.failure"
    
    # Compliance
    AUDIT_LOG_FAILURE = "compliance.audit.failure"
    PII_ACCESS = "compliance.pii.access"
    GDPR_REQUEST = "compliance.gdpr.request"

# ============================================================================
# Security Logger
# ============================================================================
class SecurityLogger:
    """
    Structured security logger with PII sanitization and audit trail
    """
    
    def __init__(self, name: str = "ultracore.security"):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configure log handlers with proper formatting"""
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for audit trail
        file_handler = logging.FileHandler('/var/log/ultracore/security.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    @staticmethod
    def _sanitize_pii(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or hash PII from log data"""
        sensitive_fields = [
            'password', 'token', 'secret', 'api_key', 'credit_card',
            'ssn', 'tax_file_number', 'bank_account'
        ]
        
        sanitized = data.copy()
        for key in sanitized:
            if any(field in key.lower() for field in sensitive_fields):
                # Hash sensitive data instead of logging plaintext
                if isinstance(sanitized[key], str):
                    sanitized[key] = hashlib.sha256(
                        sanitized[key].encode()
                    ).hexdigest()[:16] + "..."
        
        return sanitized
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """
        Log a security event with structured data
        
        Args:
            event_type: Type of security event (use SecurityEventType constants)
            user_id: ID of the user involved
            ip_address: Source IP address
            tenant_id: Tenant ID for multi-tenant systems
            resource: Resource being accessed
            action: Action being performed
            result: Result of the action (success/failure)
            details: Additional details (will be sanitized)
            severity: Log severity (info/warning/error/critical)
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "tenant_id": tenant_id,
            "resource": resource,
            "action": action,
            "result": result,
            "details": self._sanitize_pii(details) if details else {}
        }
        
        log_message = json.dumps(event_data)
        
        # Log at appropriate level
        if severity == "critical":
            self.logger.critical(log_message)
        elif severity == "error":
            self.logger.error(log_message)
        elif severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_authentication(
        self,
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication events"""
        self.log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            action="authenticate",
            result="success" if success else "failure",
            details=details,
            severity="info" if success else "warning"
        )
    
    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log authorization decisions"""
        self.log_security_event(
            event_type=SecurityEventType.ACCESS_GRANTED if granted else SecurityEventType.ACCESS_DENIED,
            user_id=user_id,
            ip_address=ip_address,
            tenant_id=tenant_id,
            resource=resource,
            action=action,
            result="granted" if granted else "denied",
            severity="info" if granted else "warning"
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        is_sensitive: bool = False
    ):
        """Log data access events"""
        event_type = SecurityEventType.SENSITIVE_DATA_ACCESS if is_sensitive else SecurityEventType.DATA_READ
        
        self.log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            tenant_id=tenant_id,
            resource=resource,
            action=action,
            result="success",
            severity="warning" if is_sensitive else "info"
        )
    
    def log_security_incident(
        self,
        incident_type: str,
        ip_address: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        """Log security incidents"""
        self.log_security_event(
            event_type=incident_type,
            user_id=user_id,
            ip_address=ip_address,
            tenant_id=tenant_id,
            result="blocked",
            details=details,
            severity="critical"
        )

# ============================================================================
# Security Logging Decorators
# ============================================================================
def log_authentication_attempt(security_logger: SecurityLogger):
    """Decorator to log authentication attempts"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                security_logger.log_authentication(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=kwargs.get('user_id'),
                    ip_address=kwargs.get('ip_address', 'unknown'),
                    success=True
                )
                return result
            except Exception as e:
                security_logger.log_authentication(
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    user_id=kwargs.get('user_id'),
                    ip_address=kwargs.get('ip_address', 'unknown'),
                    success=False,
                    details={"error": str(e)}
                )
                raise
        return wrapper
    return decorator

def log_data_access_attempt(security_logger: SecurityLogger, is_sensitive: bool = False):
    """Decorator to log data access attempts"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            security_logger.log_data_access(
                user_id=kwargs.get('user_id', 'unknown'),
                resource=kwargs.get('resource', func.__name__),
                action='read',
                tenant_id=kwargs.get('tenant_id'),
                ip_address=kwargs.get('ip_address'),
                is_sensitive=is_sensitive
            )
            return result
        return wrapper
    return decorator

# ============================================================================
# Global Security Logger Instance
# ============================================================================
security_logger = SecurityLogger()

# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # Example: Log successful login
    security_logger.log_authentication(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        user_id="user_123",
        ip_address="203.0.113.42",
        success=True,
        details={"login_method": "email"}
    )
    
    # Example: Log failed authorization
    security_logger.log_authorization(
        user_id="user_123",
        resource="/api/admin/users",
        action="read",
        granted=False,
        tenant_id="tenant_456",
        ip_address="203.0.113.42"
    )
    
    # Example: Log SQL injection attempt
    security_logger.log_security_incident(
        incident_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
        ip_address="198.51.100.23",
        details={
            "endpoint": "/api/users",
            "payload": "' OR '1'='1",
            "blocked": True
        }
    )
    
    # Example: Log sensitive data access
    security_logger.log_data_access(
        user_id="user_123",
        resource="/api/clients/client_789/financial_data",
        action="read",
        tenant_id="tenant_456",
        ip_address="203.0.113.42",
        is_sensitive=True
    )
