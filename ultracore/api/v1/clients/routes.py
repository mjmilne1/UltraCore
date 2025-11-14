"""
Clients API Router
Handles client management, KYC, and onboarding
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])

# Models
class RiskProfile(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    BALANCED = "BALANCED"
    GROWTH = "GROWTH"
    AGGRESSIVE = "AGGRESSIVE"

class ClientStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    risk_profile: RiskProfile
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: str = "AU"

class ClientResponse(BaseModel):
    client_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: date
    risk_profile: RiskProfile
    status: ClientStatus
    created_at: datetime
    kyc_verified: bool
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: str

class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    risk_profile: Optional[RiskProfile] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None

# In-memory storage (replace with database in production)
clients_db = {}

@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(client: ClientCreate):
    """
    Create a new client
    
    - **first_name**: Client's first name
    - **last_name**: Client's last name
    - **email**: Client's email address
    - **phone**: Client's phone number
    - **date_of_birth**: Client's date of birth
    - **risk_profile**: Investment risk profile
    """
    import uuid
    
    client_id = str(uuid.uuid4())
    
    client_data = {
        "client_id": client_id,
        **client.model_dump(),
        "status": ClientStatus.PENDING,
        "created_at": datetime.now(),
        "kyc_verified": False
    }
    
    clients_db[client_id] = client_data
    
    return ClientResponse(**client_data)

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    status: Optional[ClientStatus] = None,
    risk_profile: Optional[RiskProfile] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List all clients with optional filtering
    
    - **status**: Filter by client status
    - **risk_profile**: Filter by risk profile
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    filtered_clients = list(clients_db.values())
    
    if status:
        filtered_clients = [c for c in filtered_clients if c["status"] == status]
    
    if risk_profile:
        filtered_clients = [c for c in filtered_clients if c["risk_profile"] == risk_profile]
    
    return [ClientResponse(**c) for c in filtered_clients[skip:skip+limit]]

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """
    Get a specific client by ID
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientResponse(**clients_db[client_id])

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client_update: ClientUpdate):
    """
    Update client information
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = clients_db[client_id]
    
    # Update only provided fields
    update_data = client_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        client_data[field] = value
    
    clients_db[client_id] = client_data
    
    return ClientResponse(**client_data)

@router.post("/{client_id}/verify-kyc", response_model=ClientResponse)
async def verify_kyc(client_id: str):
    """
    Mark client as KYC verified
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = clients_db[client_id]
    client_data["kyc_verified"] = True
    client_data["status"] = ClientStatus.ACTIVE
    
    clients_db[client_id] = client_data
    
    return ClientResponse(**client_data)

@router.post("/{client_id}/suspend", response_model=ClientResponse)
async def suspend_client(client_id: str):
    """
    Suspend a client account
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = clients_db[client_id]
    client_data["status"] = ClientStatus.SUSPENDED
    
    clients_db[client_id] = client_data
    
    return ClientResponse(**client_data)

@router.post("/{client_id}/activate", response_model=ClientResponse)
async def activate_client(client_id: str):
    """
    Activate a suspended client account
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = clients_db[client_id]
    
    if not client_data["kyc_verified"]:
        raise HTTPException(status_code=400, detail="Cannot activate client without KYC verification")
    
    client_data["status"] = ClientStatus.ACTIVE
    
    clients_db[client_id] = client_data
    
    return ClientResponse(**client_data)

@router.delete("/{client_id}", status_code=204)
async def close_client(client_id: str):
    """
    Close a client account
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = clients_db[client_id]
    client_data["status"] = ClientStatus.CLOSED
    
    clients_db[client_id] = client_data
    
    return None

@router.get("/{client_id}/summary")
async def get_client_summary(client_id: str):
    """
    Get a comprehensive summary of client information
    """
    if client_id not in clients_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = clients_db[client_id]
    
    return {
        "client": ClientResponse(**client),
        "summary": {
            "account_age_days": (datetime.now() - client["created_at"]).days,
            "kyc_status": "Verified" if client["kyc_verified"] else "Pending",
            "account_status": client["status"],
            "risk_profile": client["risk_profile"]
        }
    }
