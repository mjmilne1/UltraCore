"""
Zero-Trust Network Security
Rate limiting, IP filtering, WAF-like protection
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException
import re

from ultracore.security.audit.audit_logger import AuditLogger, AuditEventType, AuditSeverity


class RateLimiter:
    """
    Rate limiting for API endpoints
    
    Zero-trust: Limit requests even from authenticated users
    """
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_rate_limited(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if identifier is rate limited
        
        identifier: IP address, API key, or user ID
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Record request
        self.requests[identifier].append(now)
        return False


class IPWhitelist:
    """
    IP whitelisting for production environments
    
    Zero-trust: Only allow known IPs in production
    """
    
    def __init__(self):
        self.whitelist: List[str] = [
            '127.0.0.1',  # Localhost
            '::1',  # IPv6 localhost
        ]
        self.blacklist: List[str] = []
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed"""
        
        # Check blacklist first
        if ip_address in self.blacklist:
            return False
        
        # If whitelist is empty, allow all (development mode)
        if not self.whitelist:
            return True
        
        return ip_address in self.whitelist
    
    def add_to_whitelist(self, ip_address: str):
        """Add IP to whitelist"""
        if ip_address not in self.whitelist:
            self.whitelist.append(ip_address)
    
    def add_to_blacklist(self, ip_address: str):
        """Add IP to blacklist"""
        if ip_address not in self.blacklist:
            self.blacklist.append(ip_address)


class WAFProtection:
    """
    Web Application Firewall protection
    
    AWS WAF-like rules for UltraCore
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b.*=.*)",
        r"(;.*drop\b.*table)",
        r"(--)",
        r"(/\*.*\*/)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ]
    
    @classmethod
    def check_sql_injection(cls, input_str: str) -> bool:
        """Check for SQL injection attempts"""
        input_lower = input_str.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_xss(cls, input_str: str) -> bool:
        """Check for XSS attempts"""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    async def validate_request(cls, request: Request):
        """
        Validate incoming request
        
        Raises HTTPException if malicious
        """
        # Check query parameters
        for key, value in request.query_params.items():
            if cls.check_sql_injection(value) or cls.check_xss(value):
                await AuditLogger.log_security_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    severity=AuditSeverity.CRITICAL,
                    description='Malicious request detected',
                    ip_address=request.client.host if request.client else None,
                    metadata={
                        'parameter': key,
                        'value': value,
                        'path': str(request.url.path)
                    }
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Malicious request detected"
                )


class BruteForceProtection:
    """
    Brute force attack protection
    
    Lock accounts after repeated failures
    """
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.locked_accounts: Dict[str, datetime] = {}
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        now = datetime.now(timezone.utc)
        
        # Clean old attempts (last hour)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > now - timedelta(hours=1)
        ]
        
        self.failed_attempts[identifier].append(now)
        
        # Lock if too many attempts
        if len(self.failed_attempts[identifier]) >= 5:
            self.locked_accounts[identifier] = now + timedelta(minutes=30)
    
    def is_locked(self, identifier: str) -> bool:
        """Check if account/IP is locked"""
        if identifier in self.locked_accounts:
            if datetime.now(timezone.utc) < self.locked_accounts[identifier]:
                return True
            else:
                # Unlock
                del self.locked_accounts[identifier]
                return False
        
        return False


# Global instances
_rate_limiter: Optional[RateLimiter] = None
_ip_whitelist: Optional[IPWhitelist] = None
_brute_force_protection: Optional[BruteForceProtection] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_ip_whitelist() -> IPWhitelist:
    global _ip_whitelist
    if _ip_whitelist is None:
        _ip_whitelist = IPWhitelist()
    return _ip_whitelist


def get_brute_force_protection() -> BruteForceProtection:
    global _brute_force_protection
    if _brute_force_protection is None:
        _brute_force_protection = BruteForceProtection()
    return _brute_force_protection
