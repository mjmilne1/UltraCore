"""
Health Check Router

System health and status endpoints
"""

from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any
import psutil
import platform

from ultracore import __version__

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    
    Returns system health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
        "checks": {
            "api": "operational",
            "managers": "operational"
        }
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check
    
    Returns comprehensive system status including:
    - System info
    - Resource usage
    - Component status
    """
    
    # Get system info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": disk.percent
            }
        },
        "components": {
            "api": "operational",
            "customer_manager": "operational",
            "account_manager": "operational",
            "loan_manager": "operational",
            "general_ledger": "operational",
            "audit_store": "operational"
        }
    }


@router.get("/version", status_code=status.HTTP_200_OK)
async def get_version() -> Dict[str, str]:
    """Get API version"""
    return {
        "version": __version__,
        "api_version": "v1"
    }
