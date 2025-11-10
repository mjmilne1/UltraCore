from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/api/v1/data-mesh", tags=["Data Mesh"])

CATALOG = {
    "customer_360": {
        "domain": "client",
        "name": "customer_360",
        "description": "Complete customer view",
        "owner": "client-team@turingdynamics.com.au"
    },
    "loan_portfolio": {
        "domain": "loan", 
        "name": "loan_portfolio",
        "description": "Loan portfolio analytics",
        "owner": "loan-team@turingdynamics.com.au"
    },
    "account_balances": {
        "domain": "account",
        "name": "account_balances", 
        "description": "Real-time balances",
        "owner": "account-team@turingdynamics.com.au"
    }
}

@router.get("/catalog")
async def get_catalog() -> List[Dict]:
    return list(CATALOG.values())

@router.get("/catalog/search")
async def search_catalog(q: str) -> List[Dict]:
    results = []
    for product in CATALOG.values():
        if q.lower() in product["name"].lower() or q.lower() in product["description"].lower():
            results.append(product)
    return results

@router.get("/health")
async def health() -> Dict:
    return {"status": "healthy", "products": len(CATALOG)}
