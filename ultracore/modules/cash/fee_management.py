"""
Fee Management Module
Transaction fees, account fees, and fee schedules
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

class FeeType(str, Enum):
    """Fee types"""
    ACCOUNT_MAINTENANCE = "account_maintenance"
    TRANSACTION_FEE = "transaction_fee"
    WITHDRAWAL_FEE = "withdrawal_fee"
    FOREIGN_EXCHANGE = "foreign_exchange"
    OVERDRAFT = "overdraft"
    WIRE_TRANSFER = "wire_transfer"
    EARLY_CLOSURE = "early_closure"
    PAPER_STATEMENT = "paper_statement"

class FeeSchedule:
    """
    Fee Schedule Configuration
    """
    
    def __init__(self):
        self.fee_schedule = self._initialize_schedule()
        self.fee_history = []
        
    def _initialize_schedule(self) -> Dict[str, Dict[str, Any]]:
        """Initialize fee schedule"""
        
        return {
            FeeType.ACCOUNT_MAINTENANCE: {
                "amount": Decimal("0.00"),  # No monthly fee
                "frequency": "monthly",
                "waived_if_balance_above": Decimal("5000.00")
            },
            FeeType.TRANSACTION_FEE: {
                "amount": Decimal("0.00"),  # No transaction fee
                "per_transaction": True
            },
            FeeType.WITHDRAWAL_FEE: {
                "amount": Decimal("2.50"),
                "per_transaction": True,
                "free_monthly_limit": 5  # First 5 free
            },
            FeeType.FOREIGN_EXCHANGE: {
                "percentage": 2.5,  # 2.5% markup
                "per_transaction": True
            },
            FeeType.OVERDRAFT: {
                "amount": Decimal("15.00"),
                "per_occurrence": True
            },
            FeeType.WIRE_TRANSFER: {
                "amount": Decimal("25.00"),
                "per_transaction": True
            },
            FeeType.PAPER_STATEMENT: {
                "amount": Decimal("2.00"),
                "frequency": "monthly"
            }
        }
    
    def calculate_transaction_fee(
        self,
        transaction_type: str,
        amount: Decimal,
        is_domestic: bool = True
    ) -> Decimal:
        """Calculate transaction fee"""
        
        if transaction_type == "withdrawal":
            fee_config = self.fee_schedule[FeeType.WITHDRAWAL_FEE]
            return fee_config["amount"]
        
        elif transaction_type == "wire_transfer":
            fee_config = self.fee_schedule[FeeType.WIRE_TRANSFER]
            return fee_config["amount"]
        
        elif transaction_type == "foreign_exchange":
            fee_config = self.fee_schedule[FeeType.FOREIGN_EXCHANGE]
            return amount * Decimal(str(fee_config["percentage"])) / Decimal("100")
        
        else:
            return Decimal("0.00")
    
    def apply_fee(
        self,
        account_id: str,
        fee_type: FeeType,
        amount: Decimal,
        description: str,
        transaction_id: str = None
    ) -> Dict[str, Any]:
        """Apply fee to account"""
        
        fee_record = {
            "fee_id": f"FEE-{len(self.fee_history) + 1:08d}",
            "account_id": account_id,
            "fee_type": fee_type.value,
            "amount": float(amount),
            "description": description,
            "transaction_id": transaction_id,
            "applied_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.fee_history.append(fee_record)
        
        return fee_record
    
    def calculate_monthly_fees(
        self,
        account_id: str,
        account_balance: Decimal,
        monthly_withdrawal_count: int,
        has_paper_statements: bool
    ) -> List[Dict[str, Any]]:
        """Calculate monthly account fees"""
        
        fees = []
        
        # Account maintenance fee
        maintenance_config = self.fee_schedule[FeeType.ACCOUNT_MAINTENANCE]
        
        if account_balance < maintenance_config["waived_if_balance_above"]:
            fees.append({
                "fee_type": FeeType.ACCOUNT_MAINTENANCE,
                "amount": float(maintenance_config["amount"]),
                "description": "Monthly account maintenance fee"
            })
        
        # Excess withdrawal fees
        withdrawal_config = self.fee_schedule[FeeType.WITHDRAWAL_FEE]
        free_limit = withdrawal_config["free_monthly_limit"]
        
        if monthly_withdrawal_count > free_limit:
            excess_withdrawals = monthly_withdrawal_count - free_limit
            withdrawal_fee = withdrawal_config["amount"] * excess_withdrawals
            
            fees.append({
                "fee_type": FeeType.WITHDRAWAL_FEE,
                "amount": float(withdrawal_fee),
                "description": f"Excess withdrawal fee ({excess_withdrawals} transactions)"
            })
        
        # Paper statement fee
        if has_paper_statements:
            paper_config = self.fee_schedule[FeeType.PAPER_STATEMENT]
            
            fees.append({
                "fee_type": FeeType.PAPER_STATEMENT,
                "amount": float(paper_config["amount"]),
                "description": "Paper statement fee"
            })
        
        return fees
    
    def get_fee_summary(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get fee summary for period"""
        
        period_fees = [
            f for f in self.fee_history
            if f["account_id"] == account_id
            and start_date <= datetime.fromisoformat(f["applied_at"]) <= end_date
        ]
        
        # Group by fee type
        fees_by_type = {}
        
        for fee in period_fees:
            fee_type = fee["fee_type"]
            if fee_type not in fees_by_type:
                fees_by_type[fee_type] = {
                    "count": 0,
                    "total": 0.0
                }
            
            fees_by_type[fee_type]["count"] += 1
            fees_by_type[fee_type]["total"] += fee["amount"]
        
        total_fees = sum(f["amount"] for f in period_fees)
        
        return {
            "account_id": account_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_fees": total_fees,
            "fee_count": len(period_fees),
            "fees_by_type": fees_by_type,
            "details": period_fees
        }

# Global fee schedule
fee_schedule = FeeSchedule()
