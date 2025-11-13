"""
Compliance Service

Ensures ASIC RG 179 compliance and generates required documents
"""

from typing import Dict, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from ultrawealth.models.wealth_models import (
    WealthClient, WealthPortfolio, WealthSOA, SOAType
)
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class ComplianceService:
    """Compliance and reporting service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.kafka_store = get_production_kafka_store()
        self.afsl_number = "123456"  # Australian Financial Services License
    
    async def validate_mda_compliance(
        self,
        client_id: str,
        portfolio_id: Optional[str] = None
    ) -> Dict:
        """
        Validate MDA compliance for a client
        
        Args:
            client_id: Client ID
            portfolio_id: Optional portfolio ID
            
        Returns:
            Dict: Compliance validation result
        """
        
        client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        # ASIC RG 179 compliance checks
        checks = {
            'mda_contract_signed': client.mda_contract_signed,
            'soa_provided': client.soa_provided,
            'best_interests_confirmed': client.best_interests_confirmed,
            'risk_profile_documented': client.risk_profile is not None,
            'investment_goals_documented': client.investment_goals is not None,
            'time_horizon_documented': client.time_horizon_years is not None
        }
        
        if portfolio_id:
            portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
            if portfolio:
                checks['investment_mandate_clear'] = portfolio.target_allocation is not None
                checks['portfolio_strategy_documented'] = portfolio.strategy_type is not None
        
        all_compliant = all(checks.values())
        
        return {
            'compliant': all_compliant,
            'checks': checks,
            'missing': [k for k, v in checks.items() if not v],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'regulatory_guide': 'ASIC RG 179'
        }
    
    async def generate_soa(
        self,
        client_id: str,
        portfolio_id: str,
        soa_type: str = "initial",
        advisor_id: str = "ADV-001",
        advisor_name: str = "UltraWealth Advisory"
    ) -> WealthSOA:
        """
        Generate Statement of Advice
        
        Args:
            client_id: Client ID
            portfolio_id: Portfolio ID
            soa_type: SOA type (initial, review, variation)
            advisor_id: Advisor ID
            advisor_name: Advisor name
            
        Returns:
            WealthSOA: Generated SOA
        """
        
        # Get client and portfolio
        client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Validate SOA type
        soa_type_enum = SOAType(soa_type.lower())
        
        # Generate SOA ID
        soa_id = f"SOA-{uuid.uuid4().hex[:12].upper()}"
        
        # Build SOA content
        soa_content = self._build_soa_content(
            client=client,
            portfolio=portfolio,
            soa_type=soa_type_enum,
            advisor_name=advisor_name
        )
        
        # Create SOA record
        soa = WealthSOA(
            soa_id=soa_id,
            client_id=client_id,
            portfolio_id=portfolio_id,
            soa_type=soa_type_enum,
            content=soa_content,
            advisor_id=advisor_id,
            advisor_name=advisor_name,
            afsl_number=self.afsl_number
        )
        
        self.db.add(soa)
        
        # Update client record
        client.soa_provided = True
        
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='soa_generated',
            event_data={
                'soa_id': soa_id,
                'client_id': client_id,
                'portfolio_id': portfolio_id,
                'soa_type': soa_type,
                'advisor_id': advisor_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=soa_id
        )
        
        return soa
    
    def _build_soa_content(
        self,
        client: WealthClient,
        portfolio: WealthPortfolio,
        soa_type: SOAType,
        advisor_name: str
    ) -> Dict:
        """Build SOA content"""
        
        return {
            'document_type': 'Statement of Advice',
            'soa_type': soa_type.value,
            'date': datetime.now(timezone.utc).isoformat(),
            
            # Advisor information
            'advisor': {
                'name': advisor_name,
                'afsl_number': self.afsl_number,
                'contact': 'contact@ultrawealth.com.au'
            },
            
            # Client information
            'client': {
                'client_id': client.client_id,
                'risk_profile': client.risk_profile.value,
                'investment_goals': client.investment_goals,
                'time_horizon_years': client.time_horizon_years
            },
            
            # Portfolio recommendation
            'recommendation': {
                'portfolio_name': portfolio.portfolio_name,
                'strategy_type': portfolio.strategy_type,
                'target_allocation': portfolio.target_allocation,
                'rationale': f"Based on your {client.risk_profile.value} risk profile and {client.time_horizon_years}-year time horizon, we recommend a diversified portfolio strategy."
            },
            
            # Fees and costs
            'fees': {
                'management_fee': '0.50% p.a.',
                'platform_fee': '0.10% p.a.',
                'underlying_etf_fees': '0.05-0.30% p.a.',
                'total_estimated_cost': '0.65-0.90% p.a.'
            },
            
            # Risks
            'risks': [
                'Market risk - value of investments may go down as well as up',
                'Currency risk - international investments subject to FX fluctuations',
                'Liquidity risk - ability to sell investments quickly',
                'Concentration risk - over-exposure to particular sectors'
            ],
            
            # Best interests duty
            'best_interests': {
                'confirmed': True,
                'basis': 'This advice is provided in your best interests and is appropriate for your circumstances, objectives and financial situation.',
                'conflicts_of_interest': 'None identified'
            },
            
            # Cooling off period
            'cooling_off': {
                'period_days': 14,
                'notice': 'You have 14 days from the date you receive this SOA to consider the advice and ask questions.'
            },
            
            # Disclaimer
            'disclaimer': 'This is general advice only and does not take into account your personal circumstances. Past performance is not indicative of future results.'
        }
    
    async def mark_soa_provided(self, soa_id: str) -> WealthSOA:
        """Mark SOA as provided to client"""
        
        soa = self.db.query(WealthSOA).filter_by(soa_id=soa_id).first()
        if not soa:
            raise ValueError(f"SOA {soa_id} not found")
        
        soa.provided_to_client_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='soa_provided_to_client',
            event_data={
                'soa_id': soa_id,
                'client_id': soa.client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=soa_id
        )
        
        return soa
    
    async def mark_soa_acknowledged(self, soa_id: str) -> WealthSOA:
        """Mark SOA as acknowledged by client"""
        
        soa = self.db.query(WealthSOA).filter_by(soa_id=soa_id).first()
        if not soa:
            raise ValueError(f"SOA {soa_id} not found")
        
        soa.client_acknowledged_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='soa_acknowledged_by_client',
            event_data={
                'soa_id': soa_id,
                'client_id': soa.client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=soa_id
        )
        
        return soa
    
    async def generate_compliance_report(self, client_id: str) -> Dict:
        """Generate compliance report for a client"""
        
        client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        # Get all SOAs
        soas = self.db.query(WealthSOA).filter_by(client_id=client_id).all()
        
        # Get all portfolios
        portfolios = self.db.query(WealthPortfolio).filter_by(client_id=client_id).all()
        
        # Validate compliance
        compliance_status = await self.validate_mda_compliance(client_id)
        
        return {
            'client_id': client_id,
            'report_date': datetime.now(timezone.utc).isoformat(),
            'compliance_status': compliance_status,
            'mda_contract': {
                'signed': client.mda_contract_signed,
                'date': client.mda_contract_date.isoformat() if client.mda_contract_date else None
            },
            'soas': [
                {
                    'soa_id': soa.soa_id,
                    'type': soa.soa_type.value,
                    'generated_at': soa.generated_at.isoformat(),
                    'provided_to_client': soa.provided_to_client_at is not None,
                    'acknowledged_by_client': soa.client_acknowledged_at is not None
                }
                for soa in soas
            ],
            'portfolios': [
                {
                    'portfolio_id': p.portfolio_id,
                    'name': p.portfolio_name,
                    'status': p.status.value,
                    'current_value': float(p.current_value)
                }
                for p in portfolios
            ],
            'regulatory_framework': 'ASIC RG 179',
            'afsl_number': self.afsl_number
        }
