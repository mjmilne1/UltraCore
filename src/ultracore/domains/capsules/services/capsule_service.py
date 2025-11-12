"""Capsule Service - Core Operations"""
from typing import Dict, List, Optional
from decimal import Decimal
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..models import Capsule, RiskLevel, InvestmentGoal
from ..events import CapsuleSubscribedEvent


class CapsuleService:
    """
    Capsule Service - Manage capsules and subscriptions.
    
    From TuringMachines:
    - 500 capsules migrated
    - 2,428 holdings available
    - Goal-based portfolio allocation
    
    Features:
    - Browse capsules
    - Filter by risk/goal
    - Subscribe to capsule
    - Performance tracking
    - Automatic rebalancing
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
    
    async def list_capsules(
        self,
        risk_level: Optional[RiskLevel] = None,
        investment_goal: Optional[InvestmentGoal] = None,
        min_investment: Optional[Decimal] = None,
        esg_only: bool = False
    ) -> List[Dict]:
        """
        List available capsules with filtering.
        
        Returns capsules matching criteria.
        """
        
        # Simplified - would query database
        # For now, return example capsules
        
        capsules = self._get_example_capsules()
        
        # Filter
        filtered = capsules
        
        if risk_level:
            filtered = [c for c in filtered if c["risk_level"] == risk_level.value]
        
        if investment_goal:
            filtered = [c for c in filtered if investment_goal.value in c["investment_goals"]]
        
        if esg_only:
            filtered = [c for c in filtered if c.get("esg_focused", False)]
        
        if min_investment:
            filtered = [c for c in filtered if Decimal(str(c["minimum_investment"])) <= min_investment]
        
        return {
            "total_capsules": len(filtered),
            "capsules": filtered,
            "filters_applied": {
                "risk_level": risk_level.value if risk_level else None,
                "investment_goal": investment_goal.value if investment_goal else None,
                "esg_only": esg_only,
                "min_investment": float(min_investment) if min_investment else None
            }
        }
    
    async def get_capsule_details(
        self,
        capsule_id: str
    ) -> Dict:
        """Get detailed capsule information."""
        
        # Simplified - would query database
        capsule = self._find_capsule(capsule_id)
        
        if not capsule:
            return {"error": "Capsule not found"}
        
        # Add performance data
        performance = self._get_capsule_performance(capsule_id)
        
        return {
            "capsule": capsule,
            "performance": performance,
            "holdings": self._get_capsule_holdings(capsule_id),
            "similar_capsules": self._get_similar_capsules(capsule_id)
        }
    
    async def subscribe_to_capsule(
        self,
        capsule_id: str,
        customer_id: str,
        portfolio_id: str,
        investment_amount: Decimal,
        recurring: bool = False,
        recurring_amount: Optional[Decimal] = None,
        recurring_frequency: Optional[str] = None
    ) -> Dict:
        """
        Subscribe customer to capsule.
        
        One-click investing!
        """
        
        subscription_id = f"SUB-{uuid.uuid4().hex[:12].upper()}"
        
        # Get capsule
        capsule = self._find_capsule(capsule_id)
        
        if not capsule:
            return {"error": "Capsule not found"}
        
        # Check minimum investment
        if investment_amount < Decimal(str(capsule["minimum_investment"])):
            return {
                "error": f"Minimum investment is ${capsule['minimum_investment']}"
            }
        
        # Publish event
        event = CapsuleSubscribedEvent(
            aggregate_id=subscription_id,
            subscription_id=subscription_id,
            capsule_id=capsule_id,
            customer_id=customer_id,
            portfolio_id=portfolio_id,
            investment_amount=investment_amount,
            recurring=recurring,
            recurring_amount=recurring_amount,
            recurring_frequency=recurring_frequency,
            target_allocations=capsule["target_allocations"]
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "capsule": {
                "name": capsule["name"],
                "risk_level": capsule["risk_level"],
                "expected_return": capsule["expected_return_annual"]
            },
            "investment": {
                "initial_amount": float(investment_amount),
                "recurring": recurring,
                "recurring_amount": float(recurring_amount) if recurring_amount else None,
                "recurring_frequency": recurring_frequency
            },
            "next_steps": [
                "Orders will be placed for all holdings",
                "Portfolio will be rebalanced automatically",
                "Performance tracked daily",
                f"Next rebalance: {capsule['rebalance_frequency']}"
            ],
            "message": f"?? Subscribed to {capsule['name']}! Your portfolio is being built..."
        }
    
    def _get_example_capsules(self) -> List[Dict]:
        """Get example capsules (from TuringMachines migration)."""
        
        return [
            {
                "capsule_id": "CAP-001",
                "name": "Aussie Dividend Champion",
                "description": "High dividend yield ASX stocks for income investors",
                "risk_level": "medium",
                "investment_goals": ["income_generation", "capital_preservation"],
                "expected_return_annual": 0.09,
                "dividend_yield": 0.055,
                "minimum_investment": 1000,
                "management_fee": 0.006,
                "total_holdings": 10,
                "esg_focused": False,
                "rebalance_frequency": "quarterly",
                "target_allocations": {
                    "CBA.AX": 15, "BHP.AX": 15, "WBC.AX": 10,
                    "ANZ.AX": 10, "TLS.AX": 10, "WES.AX": 10,
                    "WOW.AX": 10, "NAB.AX": 10, "RIO.AX": 5, "FMG.AX": 5
                }
            },
            {
                "capsule_id": "CAP-002",
                "name": "Tech Titans",
                "description": "Global technology growth stocks (FAANG+)",
                "risk_level": "high",
                "investment_goals": ["wealth_accumulation", "speculation"],
                "expected_return_annual": 0.175,
                "dividend_yield": 0.01,
                "minimum_investment": 1000,
                "management_fee": 0.006,
                "total_holdings": 7,
                "esg_focused": False,
                "rebalance_frequency": "monthly",
                "target_allocations": {
                    "AAPL": 20, "MSFT": 20, "GOOGL": 15,
                    "AMZN": 15, "META": 10, "TSLA": 10, "NVDA": 10
                }
            },
            {
                "capsule_id": "CAP-003",
                "name": "ESG Future",
                "description": "Sustainable investing for positive impact",
                "risk_level": "medium_high",
                "investment_goals": ["esg_impact", "wealth_accumulation"],
                "expected_return_annual": 0.135,
                "dividend_yield": 0.02,
                "minimum_investment": 1000,
                "management_fee": 0.006,
                "total_holdings": 15,
                "esg_focused": True,
                "esg_score": 85,
                "rebalance_frequency": "quarterly",
                "target_allocations": {
                    "Clean Energy": 30, "Sustainable Materials": 20,
                    "Electric Vehicles": 15, "Green Bonds": 15,
                    "Water Infrastructure": 10, "Waste Management": 10
                }
            },
            {
                "capsule_id": "CAP-004",
                "name": "Property Exposure",
                "description": "Real estate investment via REITs",
                "risk_level": "medium",
                "investment_goals": ["income_generation", "wealth_accumulation"],
                "expected_return_annual": 0.10,
                "dividend_yield": 0.045,
                "minimum_investment": 1000,
                "management_fee": 0.006,
                "total_holdings": 8,
                "esg_focused": False,
                "rebalance_frequency": "semi_annually",
                "target_allocations": {
                    "GMG.AX": 20, "SCG.AX": 15, "GPT.AX": 15,
                    "SGP.AX": 15, "MGR.AX": 10, "CHC.AX": 10,
                    "DXS.AX": 10, "VCX.AX": 5
                }
            },
            {
                "capsule_id": "CAP-005",
                "name": "Global Diversifier",
                "description": "Worldwide geographic diversification",
                "risk_level": "medium",
                "investment_goals": ["wealth_accumulation", "capital_preservation"],
                "expected_return_annual": 0.11,
                "dividend_yield": 0.025,
                "minimum_investment": 1000,
                "management_fee": 0.006,
                "total_holdings": 6,
                "esg_focused": False,
                "rebalance_frequency": "quarterly",
                "target_allocations": {
                    "US (S&P 500)": 40, "Australia (ASX 200)": 20,
                    "Europe (Euro Stoxx)": 15, "Asia-Pacific": 10,
                    "Japan (Nikkei)": 5, "Emerging Markets": 10
                }
            },
            {
                "capsule_id": "CAP-006",
                "name": "Bitcoin Futures",
                "description": "Cryptocurrency exposure via regulated futures",
                "risk_level": "very_high",
                "investment_goals": ["speculation"],
                "expected_return_annual": 0.50,  # Highly volatile!
                "dividend_yield": 0.0,
                "minimum_investment": 5000,
                "management_fee": 0.006,
                "total_holdings": 3,
                "esg_focused": False,
                "rebalance_frequency": "weekly",
                "target_allocations": {
                    "Bitcoin Futures": 60,
                    "Ethereum Futures": 30,
                    "Cash (USD)": 10
                }
            }
        ]
    
    def _find_capsule(self, capsule_id: str) -> Optional[Dict]:
        """Find capsule by ID."""
        capsules = self._get_example_capsules()
        return next((c for c in capsules if c["capsule_id"] == capsule_id), None)
    
    def _get_capsule_performance(self, capsule_id: str) -> Dict:
        """Get capsule performance metrics."""
        return {
            "return_1d": 0.0012,
            "return_1w": 0.0089,
            "return_1m": 0.0234,
            "return_3m": 0.0567,
            "return_1y": 0.0923,
            "volatility": 0.145,
            "sharpe_ratio": 0.85,
            "max_drawdown": -0.089
        }
    
    def _get_capsule_holdings(self, capsule_id: str) -> List[Dict]:
        """Get capsule holdings details."""
        return []  # Simplified
    
    def _get_similar_capsules(self, capsule_id: str) -> List[str]:
        """Get similar capsules."""
        return []  # Simplified
