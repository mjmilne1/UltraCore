"""
Common API Schemas

Shared Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ============================================================================
# Common Response Models
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: Dict[str, Any]


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    pagination: PaginationMetadata


# ============================================================================
# Enums (matching core models)
# ============================================================================

class CustomerTypeEnum(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class AccountTypeEnum(str, Enum):
    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    TERM_DEPOSIT = "TERM_DEPOSIT"
    LOAN = "LOAN"
    CREDIT_CARD = "CREDIT_CARD"


class TransactionTypeEnum(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    INTEREST = "INTEREST"
    FEE = "FEE"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"


class LoanTypeEnum(str, Enum):
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    AUTO = "AUTO"
    BUSINESS = "BUSINESS"
    STUDENT = "STUDENT"


# ============================================================================
# Helper Functions
# ============================================================================

def decimal_to_float(value: Optional[Decimal]) -> Optional[float]:
    """Convert Decimal to float for JSON serialization"""
    return float(value) if value is not None else None
