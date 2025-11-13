"""Tests for Template Service"""
import pytest
from ..services.template_service import TemplateService

def test_get_australian_portfolio_templates():
    """Test Australian portfolio templates"""
    service = TemplateService()
    
    smsf_template = service.get_portfolio_template("smsf_balanced")
    assert smsf_template is not None
    assert smsf_template["is_australian_compliant"] is True
    assert smsf_template["includes_franking_credits"] is True

def test_franking_credit_focus_template():
    """Test franking credit focus template"""
    service = TemplateService()
    
    template = service.get_portfolio_template("franking_credit_focus")
    assert template["strategy"].value == "franking_credit_focus"
    assert template["includes_franking_credits"] is True
