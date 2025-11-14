"""
Data Catalog API.

API for discovering and accessing data products.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .products import *
from .products.base import DataProduct, DataProductMetadata, DataQualityLevel, RefreshFrequency
from .quality_monitoring import quality_monitor


# Initialize all data products
DATA_PRODUCTS: Dict[str, DataProduct] = {
    "customer360": Customer360(),
    "account_balances": AccountBalances(),
    "transaction_history": TransactionHistory(),
    "payment_analytics": PaymentAnalytics(),
    "loan_portfolio": LoanPortfolio(),
    "investment_performance": InvestmentPerformance(),
    "risk_metrics": RiskMetrics(),
    "fraud_signals": FraudSignals(),
    "compliance_reports": ComplianceReports(),
    "regulatory_reporting": RegulatoryReporting(),
    "customer_segments": CustomerSegments(),
    "product_usage": ProductUsage(),
    "channel_analytics": ChannelAnalytics(),
    "operational_metrics": OperationalMetrics(),
    "financial_reporting": FinancialReporting(),
}


# API Router
router = APIRouter(prefix="/data-mesh", tags=["Data Mesh"])


# Request/Response Models
class DataProductListResponse(BaseModel):
    """Response for list data products."""
    products: List[Dict[str, Any]]
    total_count: int


class DataProductDetailResponse(BaseModel):
    """Response for data product details."""
    metadata: Dict[str, Any]
    schema: Dict[str, Any]
    quality_metrics: Optional[Dict[str, Any]] = None
    lineage: Optional[Dict[str, Any]] = None


class DataProductQueryRequest(BaseModel):
    """Request for querying a data product."""
    filters: Optional[Dict[str, Any]] = None
    limit: int = 100
    offset: int = 0


class DataProductQueryResponse(BaseModel):
    """Response for data product query."""
    data: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int


class QualityReportResponse(BaseModel):
    """Response for quality report."""
    report: Dict[str, Any]


# Endpoints

@router.get("/products", response_model=DataProductListResponse)
async def list_data_products(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    quality_level: Optional[DataQualityLevel] = Query(None, description="Filter by quality level"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all available data products.
    
    Returns metadata for all data products with optional filtering.
    """
    products = []
    
    for product_id, product in DATA_PRODUCTS.items():
        metadata = product.get_metadata()
        
        # Apply filters
        if domain and metadata.domain != domain:
            continue
        if quality_level and metadata.quality_level != quality_level:
            continue
        if status and metadata.status != status:
            continue
        
        products.append({
            "product_id": metadata.product_id,
            "name": metadata.name,
            "description": metadata.description,
            "domain": metadata.domain,
            "owner": metadata.owner,
            "quality_level": metadata.quality_level,
            "refresh_frequency": metadata.refresh_frequency,
            "status": metadata.status,
            "last_refreshed_at": metadata.last_refreshed_at
        })
    
    return DataProductListResponse(
        products=products,
        total_count=len(products)
    )


@router.get("/products/{product_id}", response_model=DataProductDetailResponse)
async def get_data_product(product_id: str):
    """
    Get detailed information about a data product.
    
    Returns metadata, schema, quality metrics, and lineage.
    """
    if product_id not in DATA_PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Data product {product_id} not found")
    
    product = DATA_PRODUCTS[product_id]
    
    # Get metadata
    metadata = product.get_metadata()
    
    # Get schema
    schema = await product.get_schema()
    
    # Get quality metrics
    quality_metrics = await product.measure_quality()
    
    # Get lineage
    lineage = await product.get_lineage()
    
    return DataProductDetailResponse(
        metadata=metadata.dict(),
        schema=schema.dict(),
        quality_metrics=quality_metrics.dict() if quality_metrics else None,
        lineage=lineage.dict() if lineage else None
    )


@router.post("/products/{product_id}/query", response_model=DataProductQueryResponse)
async def query_data_product(product_id: str, request: DataProductQueryRequest):
    """
    Query a data product.
    
    Returns data matching the provided filters.
    """
    if product_id not in DATA_PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Data product {product_id} not found")
    
    product = DATA_PRODUCTS[product_id]
    
    # Query the product
    data = await product.query(filters=request.filters)
    
    # Apply pagination
    total_count = len(data)
    paginated_data = data[request.offset:request.offset + request.limit]
    
    return DataProductQueryResponse(
        data=paginated_data,
        total_count=total_count,
        limit=request.limit,
        offset=request.offset
    )


@router.post("/products/{product_id}/refresh")
async def refresh_data_product(product_id: str):
    """
    Trigger a refresh of a data product.
    
    Returns success status.
    """
    if product_id not in DATA_PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Data product {product_id} not found")
    
    product = DATA_PRODUCTS[product_id]
    
    # Refresh the product
    success = await product.refresh()
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to refresh data product")
    
    return {
        "success": True,
        "product_id": product_id,
        "refreshed_at": datetime.utcnow()
    }


@router.get("/quality/report", response_model=QualityReportResponse)
async def get_quality_report(
    product_id: Optional[str] = Query(None, description="Filter by product ID")
):
    """
    Get data quality report.
    
    Returns quality metrics and alerts for data products.
    """
    report = await quality_monitor.get_quality_report(product_id=product_id)
    
    return QualityReportResponse(report=report)


@router.get("/quality/alerts")
async def get_quality_alerts(
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    Get active quality alerts.
    
    Returns list of active quality alerts.
    """
    from .quality_monitoring import QualityAlertSeverity
    
    severity_enum = None
    if severity:
        try:
            severity_enum = QualityAlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    alerts = quality_monitor.get_active_alerts(
        product_id=product_id,
        severity=severity_enum
    )
    
    return {
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "product_id": alert.product_id,
                "metric_name": alert.metric_name,
                "severity": alert.severity,
                "message": alert.message,
                "current_value": float(alert.current_value),
                "threshold_value": float(alert.threshold_value),
                "created_at": alert.created_at
            }
            for alert in alerts
        ],
        "total_count": len(alerts)
    }


@router.post("/quality/alerts/{alert_id}/resolve")
async def resolve_quality_alert(alert_id: str, resolved_by: str):
    """
    Resolve a quality alert.
    
    Marks the alert as resolved.
    """
    success = quality_monitor.resolve_alert(alert_id, resolved_by)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    return {
        "success": True,
        "alert_id": alert_id,
        "resolved_at": datetime.utcnow(),
        "resolved_by": resolved_by
    }


@router.get("/domains")
async def list_domains():
    """
    List all domains with data products.
    
    Returns list of domains and their product counts.
    """
    domains = {}
    
    for product in DATA_PRODUCTS.values():
        domain = product.metadata.domain
        if domain not in domains:
            domains[domain] = {
                "domain": domain,
                "product_count": 0,
                "products": []
            }
        domains[domain]["product_count"] += 1
        domains[domain]["products"].append(product.metadata.product_id)
    
    return {
        "domains": list(domains.values()),
        "total_domains": len(domains)
    }
