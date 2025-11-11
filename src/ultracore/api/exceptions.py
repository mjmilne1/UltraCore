"""
UltraCore API Exceptions

Custom exception classes for API error handling
"""

from typing import Optional, Dict, Any


class UltraCoreException(Exception):
    """Base exception for UltraCore"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(UltraCoreException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class ValidationException(UltraCoreException):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class BusinessRuleException(UltraCoreException):
    """Business rule violation"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BUSINESS_RULE_VIOLATION",
            details=details
        )


class InsufficientFundsException(UltraCoreException):
    """Insufficient funds for transaction"""
    
    def __init__(self, account_id: str, requested: str, available: str):
        super().__init__(
            message="Insufficient funds for transaction",
            status_code=400,
            error_code="INSUFFICIENT_FUNDS",
            details={
                "account_id": account_id,
                "requested_amount": requested,
                "available_balance": available
            }
        )


class UnauthorizedException(UltraCoreException):
    """Unauthorized access"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(UltraCoreException):
    """Forbidden access"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )


class ConflictException(UltraCoreException):
    """Resource conflict (e.g., duplicate)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )
