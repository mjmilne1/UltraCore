"""
Customer API Schemas

Pydantic models for customer endpoints
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime

from ultracore.api.schemas.common import CustomerTypeEnum


# ============================================================================
# Request Models
# ============================================================================

class CustomerCreateRequest(BaseModel):
    """Create customer request"""
    customer_type: CustomerTypeEnum
    
    # Individual fields
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    
    # Business fields
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_registration: Optional[str] = None
    abn: Optional[str] = Field(None, pattern=r'^\d{11}$')
    
    # Contact
    email: EmailStr
    mobile: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    
    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "AU"
    
    @validator('first_name', 'last_name')
    def validate_individual_fields(cls, v, values):
        if values.get('customer_type') == CustomerTypeEnum.INDIVIDUAL and not v:
            raise ValueError('Required for individual customers')
        return v
    
    @validator('business_name')
    def validate_business_fields(cls, v, values):
        if values.get('customer_type') == CustomerTypeEnum.BUSINESS and not v:
            raise ValueError('Required for business customers')
        return v


class CustomerUpdateRequest(BaseModel):
    """Update customer request"""
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


# ============================================================================
# Response Models
# ============================================================================

class CustomerResponse(BaseModel):
    """Customer response"""
    customer_id: str
    customer_type: str
    status: str
    
    # Individual
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    # Business
    business_name: Optional[str] = None
    business_registration: Optional[str] = None
    abn: Optional[str] = None
    
    # Contact
    email: str
    mobile: str
    
    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """List of customers"""
    customers: List[CustomerResponse]
    total: int
