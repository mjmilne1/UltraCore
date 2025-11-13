"""
Australian Compliance API Routes
Complete RESTful API for compliance management
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ultracore.compliance.australia.compliance_integration import australian_compliance
from ultracore.compliance.australia.asic_compliance import asic_compliance
from ultracore.compliance.australia.austrac_compliance import austrac_compliance
from ultracore.compliance.australia.asx_compliance import asx_compliance
from ultracore.compliance.australia.ato_compliance import ato_compliance
from ultracore.compliance.australia.privacy_compliance import privacy_compliance

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

# ============================================================================
# COMPLIANCE DASHBOARD
# ============================================================================

@router.get("/dashboard")
async def get_compliance_dashboard():
    """Get comprehensive compliance dashboard"""
    dashboard = await australian_compliance.generate_compliance_dashboard()
    return dashboard

# ============================================================================
# CLIENT ONBOARDING
# ============================================================================

@router.post("/onboard-client")
async def onboard_client_compliant(client_data: dict):
    """Perform compliant client onboarding"""
    try:
        result = await australian_compliance.onboard_client_compliant(client_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ASIC COMPLIANCE
# ============================================================================

@router.post("/asic/categorize-client")
async def categorize_client(client_data: dict):
    """Categorize client per ASIC rules"""
    category = asic_compliance.categorize_client(client_data)
    return {"client_category": category}

@router.post("/asic/check-best-interests")
async def check_best_interests(advice_data: dict):
    """Check best interests duty compliance"""
    result = asic_compliance.check_best_interests_duty(advice_data)
    return result

@router.get("/asic/fsg")
async def get_fsg_requirements():
    """Get FSG requirements"""
    fsg = asic_compliance.generate_fsg()
    return fsg

# ============================================================================
# AUSTRAC COMPLIANCE
# ============================================================================

@router.post("/austrac/cdd")
async def perform_cdd(client_data: dict):
    """Perform Customer Due Diligence"""
    result = austrac_compliance.perform_cdd(client_data)
    return result

@router.post("/austrac/edd")
async def perform_edd(client_data: dict, risk_factors: list):
    """Perform Enhanced Due Diligence"""
    result = austrac_compliance.perform_edd(client_data, risk_factors)
    return result

@router.post("/austrac/check-suspicious")
async def check_suspicious(transaction: dict, client_history: list):
    """Check for suspicious matter"""
    result = austrac_compliance.check_suspicious_matter(transaction, client_history)
    return result

# ============================================================================
# ASX COMPLIANCE
# ============================================================================

@router.post("/asx/validate-order")
async def validate_order(order: dict, market_data: dict, client_holdings: dict):
    """Validate order per ASX rules"""
    result = asx_compliance.validate_order(order, market_data, client_holdings)
    return result

@router.get("/asx/trading-hours")
async def check_trading_hours(security_code: str):
    """Check trading hours"""
    result = asx_compliance.check_trading_hours(datetime.now(timezone.utc), security_code)
    return result

# ============================================================================
# ATO COMPLIANCE
# ============================================================================

@router.post("/ato/calculate-cgt")
async def calculate_cgt(sale: dict, purchase_history: list):
    """Calculate Capital Gains Tax"""
    result = ato_compliance.calculate_cgt(sale, purchase_history)
    return result

@router.get("/ato/tax-report/{financial_year}")
async def get_tax_report(financial_year: int):
    """Generate tax report"""
    result = ato_compliance.generate_tax_report(financial_year)
    return result

@router.post("/ato/validate-tfn")
async def validate_tfn(tfn: str):
    """Validate Tax File Number"""
    result = ato_compliance.validate_tfn(tfn)
    return result

# ============================================================================
# PRIVACY COMPLIANCE
# ============================================================================

@router.get("/privacy/notice")
async def get_privacy_notice(entity_name: str):
    """Get privacy notice"""
    notice = privacy_compliance.generate_privacy_notice(entity_name)
    return notice

@router.post("/privacy/record-consent")
async def record_consent(
    client_id: str,
    data_type: str,
    purpose: str,
    consent_type: str
):
    """Record client consent"""
    from ultracore.compliance.australia.privacy_compliance import DataType, ConsentType
    
    result = privacy_compliance.record_consent(
        client_id,
        DataType(data_type),
        purpose,
        ConsentType(consent_type)
    )
    return result

@router.post("/privacy/data-breach")
async def report_data_breach(breach: dict):
    """Report data breach"""
    result = privacy_compliance.report_data_breach(breach)
    return result
