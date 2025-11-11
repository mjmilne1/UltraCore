"""
UltraCore Banking Platform - FastAPI Application

Main entry point for the REST API
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import time

from ultracore.api.config import get_settings
from ultracore.api.exceptions import UltraCoreException
from ultracore.api.middleware.error_handlers import (
    ultracore_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Import routers (will create these next)
from ultracore.api.routers import (
    health,
    customers,
    accounts,
    transactions,
    payments,
    loans,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events
    
    Startup: Initialize connections, load data
    Shutdown: Cleanup resources
    """
    # Startup
    logger.info("🚀 Starting UltraCore API...")
    logger.info("✓ Initializing managers...")
    
    # Initialize managers (they're singletons)
    from ultracore.customers.core.customer_manager import get_customer_manager
    from ultracore.accounts.core.account_manager import get_account_manager
    
    get_customer_manager()
    get_account_manager()
    
    logger.info("✓ Managers initialized")
    logger.info("✅ UltraCore API ready!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down UltraCore API...")


# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
app.add_exception_handler(UltraCoreException, ultracore_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["Health"])
app.include_router(customers.router, prefix=settings.api_prefix, tags=["Customers"])
app.include_router(accounts.router, prefix=settings.api_prefix, tags=["Accounts"])
app.include_router(transactions.router, prefix=settings.api_prefix, tags=["Transactions"])
app.include_router(payments.router, prefix=settings.api_prefix, tags=["Payments"])
app.include_router(loans.router, prefix=settings.api_prefix, tags=["Loans"])


# Root endpoint
@app.get("/")
async def root():
    """API root - basic info"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": f"{settings.api_prefix}/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "ultracore.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
