"""Insurance Policy API Endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from ..services import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])


class QuoteRequest(BaseModel):
    customer_id: str
    product_type: str
    cover_amount: float
    age: int
    gender: str
    smoker: bool
    occupation: str


@router.post("/quote")
async def get_quote(request: QuoteRequest):
    """
    POST /insurance/policies/quote
    
    Get instant insurance quote.
    
    Example:
    {
        "customer_id": "CUST-123",
        "product_type": "term_life",
        "cover_amount": 500000,
        "age": 35,
        "gender": "male",
        "smoker": false,
        "occupation": "accountant"
    }
    
    Returns:
    {
        "quote_id": "QTE-ABC123",
        "premium": {
            "annual": 1200,
            "monthly": 100
        },
        "commission_estimate": {...}
    }
    """
    try:
        service = PolicyService(None, None)
        result = await service.request_quote(
            customer_id=request.customer_id,
            product_type=request.product_type,
            cover_amount=Decimal(str(request.cover_amount)),
            age=request.age,
            gender=request.gender,
            smoker=request.smoker,
            occupation=request.occupation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{policy_id}")
async def get_policy(policy_id: str):
    """
    GET /insurance/policies/{policy_id}
    
    Get policy details.
    """
    return {
        "policy_id": policy_id,
        "policy_number": "INS123456",
        "product": "Term Life Insurance",
        "cover_amount": 500000,
        "annual_premium": 1200,
        "status": "active"
    }
