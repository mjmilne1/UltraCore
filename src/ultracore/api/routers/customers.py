"""
Customer Router

Customer management endpoints
"""

from fastapi import APIRouter, status, Query, Path
from typing import List, Optional

from ultracore.api.schemas.customers import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerResponse,
    CustomerListResponse
)
from ultracore.api.schemas.common import SuccessResponse
from ultracore.api.exceptions import NotFoundException, ValidationException
from ultracore.customers.core.customer_manager import get_customer_manager
from ultracore.customers.core.customer_models import CustomerType

router = APIRouter(prefix="/customers")


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(request: CustomerCreateRequest) -> CustomerResponse:
    """
    Create a new customer
    
    Creates either an individual or business customer
    """
    manager = get_customer_manager()
    
    # Map request to manager call
    customer_type = CustomerType[request.customer_type.value]
    
    customer = manager.create_customer(
        customer_type=customer_type,
        first_name=request.first_name,
        last_name=request.last_name,
        business_name=request.business_name,
        email=request.email,
        mobile=request.mobile,
        date_of_birth=request.date_of_birth,
        business_registration=request.business_registration,
        abn=request.abn,
        created_by="API"
    )
    
    # Update address if provided
    if request.street_address:
        manager.update_customer_address(
            customer_id=customer.customer_id,
            street_address=request.street_address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country
        )
        # Refresh customer
        customer = manager.get_customer(customer.customer_id)
    
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str = Path(..., description="Customer ID")
) -> CustomerResponse:
    """
    Get customer by ID
    
    Returns complete customer information
    """
    manager = get_customer_manager()
    
    customer = manager.get_customer(customer_id)
    if not customer:
        raise NotFoundException("Customer", customer_id)
    
    return CustomerResponse.model_validate(customer)


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    customer_type: Optional[str] = Query(None, description="Filter by customer type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> CustomerListResponse:
    """
    List customers
    
    Returns paginated list of customers with optional filtering
    """
    manager = get_customer_manager()
    
    # Get all customers (in production: would filter in database)
    all_customers = list(manager.customers.values())
    
    # Apply filters
    if customer_type:
        all_customers = [c for c in all_customers if c.customer_type.value == customer_type]
    
    if status:
        all_customers = [c for c in all_customers if c.status.value == status]
    
    # Apply pagination
    total = len(all_customers)
    customers = all_customers[offset:offset + limit]
    
    return CustomerListResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        total=total
    )


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest
) -> CustomerResponse:
    """
    Update customer information
    
    Allows updating contact and address information
    """
    manager = get_customer_manager()
    
    customer = manager.get_customer(customer_id)
    if not customer:
        raise NotFoundException("Customer", customer_id)
    
    # Update contact if provided
    if request.email or request.mobile:
        manager.update_customer_contact(
            customer_id=customer_id,
            email=request.email or customer.email,
            mobile=request.mobile or customer.mobile
        )
    
    # Update address if provided
    if any([request.street_address, request.city, request.state, request.postal_code]):
        manager.update_customer_address(
            customer_id=customer_id,
            street_address=request.street_address or customer.street_address,
            city=request.city or customer.city,
            state=request.state or customer.state,
            postal_code=request.postal_code or customer.postal_code,
            country=customer.country
        )
    
    # Get updated customer
    customer = manager.get_customer(customer_id)
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", response_model=SuccessResponse)
async def deactivate_customer(customer_id: str) -> SuccessResponse:
    """
    Deactivate customer
    
    Soft deletes customer (changes status to INACTIVE)
    """
    manager = get_customer_manager()
    
    customer = manager.get_customer(customer_id)
    if not customer:
        raise NotFoundException("Customer", customer_id)
    
    manager.deactivate_customer(customer_id, reason="Deactivated via API")
    
    return SuccessResponse(
        message="Customer deactivated successfully",
        data={"customer_id": customer_id}
    )


@router.get("/{customer_id}/accounts")
async def get_customer_accounts(customer_id: str):
    """
    Get customer's accounts
    
    Returns all accounts linked to this customer
    """
    from ultracore.accounts.core.account_manager import get_account_manager
    
    manager = get_customer_manager()
    customer = manager.get_customer(customer_id)
    if not customer:
        raise NotFoundException("Customer", customer_id)
    
    account_manager = get_account_manager()
    accounts = await account_manager.get_customer_accounts(customer_id)
    
    return {
        "customer_id": customer_id,
        "accounts": [
            {
                "account_id": acc.account_id,
                "account_number": acc.account_number,
                "account_type": acc.account_type.value,
                "status": acc.status.value,
                "balance": float(acc.balance.ledger_balance),
                "currency": acc.currency
            }
            for acc in accounts
        ],
        "total": len(accounts)
    }
