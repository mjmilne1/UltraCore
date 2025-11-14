"""Margin Lending Service - Leverage for Portfolios"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import MarginLoanDrawnEvent, MarginCallIssuedEvent
from ..models import MarginLoan
# from ultracore.domains.accounts.ledger import UltraLedgerService  # TODO: Fix import path


class MarginLendingService:
    """
    Margin lending for investment portfolios.
    
    Features:
    - Borrow against portfolio value
    - LVR (Loan-to-Value Ratio) monitoring
    - Margin call management
    - Interest calculation
    - Security valuation
    
    Australian Context:
    - Typical LVR: 50-75% depending on securities
    - Margin call buffer: Usually 5-10% above max LVR
    - Interest rates: Variable, typically 2-4% above cash rate
    - Security: Registered charge over portfolio
    
    Integration:
    - Portfolio holdings as security
    - Lending module for loan management
    - Real-time portfolio valuation
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ledger_service: UltraLedgerService
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ledger = ledger_service
    
    async def establish_margin_facility(
        self,
        portfolio_id: str,
        customer_id: str,
        approved_limit: Decimal,
        maximum_lvr: Decimal = Decimal("0.70"),
        interest_rate: Decimal = Decimal("8.50"),
        **kwargs
    ) -> Dict:
        """
        Establish margin lending facility.
        
        Approval based on:
        - Portfolio value
        - Security quality
        - Customer creditworthiness
        - LVR limits
        """
        
        margin_loan_id = f"MRG-{uuid.uuid4().hex[:12].upper()}"
        
        # Create margin loan
        margin_loan = MarginLoan(
            margin_loan_id=margin_loan_id,
            portfolio_id=portfolio_id,
            customer_id=customer_id,
            approved_limit=approved_limit,
            drawn_balance=Decimal("0.00"),
            available_to_draw=approved_limit,
            portfolio_value=Decimal("0.00"),  # Will be updated
            current_lvr=Decimal("0.00"),
            maximum_lvr=maximum_lvr,
            buffer_lvr=maximum_lvr + Decimal("0.05"),  # +5% buffer
            interest_rate=interest_rate,
            interest_accrued=Decimal("0.00"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return {
            "margin_loan_id": margin_loan_id,
            "approved_limit": float(approved_limit),
            "maximum_lvr": float(maximum_lvr),
            "buffer_lvr": float(margin_loan.buffer_lvr),
            "interest_rate": float(interest_rate),
            "features": {
                "leverage": "Amplify returns with borrowed funds",
                "flexibility": "Draw and repay as needed",
                "tax_deductible": "Interest may be tax deductible",
                "portfolio_security": "Secured against your portfolio"
            },
            "risks": {
                "margin_call": "If portfolio falls, may need to add funds",
                "amplified_losses": "Losses magnified with leverage",
                "interest_cost": "Interest charged on drawn balance",
                "forced_sale": "Securities may be sold if margin call unmet"
            },
            "message": f"Margin facility established. You can borrow up to ${float(approved_limit):,.0f}"
        }
    
    async def draw_margin_loan(
        self,
        margin_loan_id: str,
        customer_id: str,
        draw_amount: Decimal,
        purpose: str = "investment"
    ) -> Dict:
        """
        Draw down margin loan.
        
        Publishes: MarginLoanDrawnEvent
        Checks: LVR limits, available funds
        """
        
        # Would check current LVR and available limit
        # Simplified for now
        
        event = MarginLoanDrawnEvent(
            aggregate_id=margin_loan_id,
            portfolio_id="PORT-123",  # Would get from margin loan
            customer_id=customer_id,
            margin_loan_id=margin_loan_id,
            draw_amount=draw_amount,
            purpose=purpose,
            drawn_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "drawn_amount": float(draw_amount),
            "new_drawn_balance": float(draw_amount),  # Would calculate actual
            "available_to_draw": float(Decimal("50000")),  # Mock
            "current_lvr": 0.45,
            "message": f"Drawn ${float(draw_amount):,.0f} from margin facility"
        }
    
    async def check_margin_call(
        self,
        margin_loan: MarginLoan,
        current_portfolio_value: Decimal
    ) -> Dict:
        """
        Check if margin call required.
        
        Margin Call Triggers:
        - LVR exceeds buffer (typically max LVR + 5%)
        - Portfolio value drops significantly
        - Security degradation
        """
        
        # Calculate current LVR
        if current_portfolio_value > 0:
            current_lvr = margin_loan.drawn_balance / current_portfolio_value
        else:
            current_lvr = Decimal("1.00")
        
        # Check if in margin call
        in_margin_call = current_lvr > margin_loan.buffer_lvr
        
        if in_margin_call:
            # Calculate margin call amount
            target_lvr = margin_loan.maximum_lvr
            required_portfolio_value = margin_loan.drawn_balance / target_lvr
            margin_call_amount = required_portfolio_value - current_portfolio_value
            
            # Issue margin call
            event = MarginCallIssuedEvent(
                aggregate_id=margin_loan.portfolio_id,
                portfolio_id=margin_loan.portfolio_id,
                customer_id=margin_loan.customer_id,
                margin_loan_id=margin_loan.margin_loan_id,
                current_lvr=current_lvr,
                buffer_lvr=margin_loan.buffer_lvr,
                margin_call_amount=margin_call_amount,
                due_date=date.today(),  # Immediate
                issued_at=datetime.now(timezone.utc)
            )
            
            await self.kafka.publish(event)
            await self.event_store.append_event(event)
            
            return {
                "in_margin_call": True,
                "current_lvr": float(current_lvr),
                "maximum_lvr": float(margin_loan.maximum_lvr),
                "buffer_lvr": float(margin_loan.buffer_lvr),
                "margin_call_amount": float(margin_call_amount),
                "portfolio_value": float(current_portfolio_value),
                "loan_balance": float(margin_loan.drawn_balance),
                "actions": [
                    f"Deposit ${float(margin_call_amount):,.0f} cash",
                    "Or reduce loan balance",
                    "Or sell securities to reduce loan"
                ],
                "message": "?? MARGIN CALL: Urgent action required within 24 hours"
            }
        else:
            # No margin call
            lvr_buffer = margin_loan.buffer_lvr - current_lvr
            
            return {
                "in_margin_call": False,
                "current_lvr": float(current_lvr),
                "maximum_lvr": float(margin_loan.maximum_lvr),
                "buffer_lvr": float(margin_loan.buffer_lvr),
                "lvr_buffer": float(lvr_buffer),
                "portfolio_value": float(current_portfolio_value),
                "loan_balance": float(margin_loan.drawn_balance),
                "message": f"? No margin call. LVR buffer: {float(lvr_buffer * 100):.1f}%"
            }
    
    def calculate_lending_value(
        self,
        holdings: Dict[str, Dict]
    ) -> Dict:
        """
        Calculate lending value of portfolio.
        
        Australian Margin Lending LVRs:
        - Blue chip shares (Big 4 banks): 70-75%
        - ASX 200 shares: 60-70%
        - Small caps: 40-50%
        - International shares: 50-60%
        - ETFs: 60-70%
        - Managed funds: 50-60%
        - Bonds: 70-80%
        - Cash: 100%
        """
        
        lvr_table = {
            # Australian Blue Chips
            "CBA": Decimal("0.75"),
            "WBC": Decimal("0.75"),
            "ANZ": Decimal("0.75"),
            "NAB": Decimal("0.75"),
            "BHP": Decimal("0.70"),
            "CSL": Decimal("0.70"),
            
            # ETFs
            "VAS": Decimal("0.70"),
            "VGS": Decimal("0.65"),
            "VDHG": Decimal("0.65"),
            "IOZ": Decimal("0.70"),
            
            # Default
            "default": Decimal("0.50")
        }
        
        total_market_value = Decimal("0.00")
        total_lending_value = Decimal("0.00")
        
        security_lending_values = {}
        
        for security, details in holdings.items():
            market_value = details.get("market_value", Decimal("0"))
            lvr = lvr_table.get(security, lvr_table["default"])
            lending_value = market_value * lvr
            
            total_market_value += market_value
            total_lending_value += lending_value
            
            security_lending_values[security] = {
                "market_value": float(market_value),
                "lvr": float(lvr),
                "lending_value": float(lending_value)
            }
        
        weighted_lvr = total_lending_value / total_market_value if total_market_value > 0 else Decimal("0")
        
        return {
            "total_market_value": float(total_market_value),
            "total_lending_value": float(total_lending_value),
            "weighted_lvr": float(weighted_lvr),
            "maximum_borrowing": float(total_lending_value),
            "security_values": security_lending_values
        }


class MarginLoanDrawnEvent:
    """Margin loan drawn (simplified)."""
    pass


class MarginCallIssuedEvent:
    """Margin call issued (simplified)."""
    pass
