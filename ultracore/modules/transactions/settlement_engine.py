"""
Settlement Engine
T+2 settlement processing with cash and position updates
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ultracore.modules.transactions.kafka_events import transaction_kafka, TransactionEventType
from ultracore.modules.holdings.holdings_service import holdings_service

class SettlementStatus(str):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SettlementEngine:
    """
    T+2 Settlement Engine
    
    Features:
    - T+2 settlement cycle
    - Cash movement
    - Position updates
    - Settlement reconciliation
    - Failed settlement handling
    """
    
    def __init__(self):
        self.settlements = {}
        self.settlement_counter = 0
        self.settlement_queue = []
        
        # Subscribe to settlement events
        transaction_kafka.subscribe_to_settlement(self._handle_settlement_event)
    
    async def create_settlement(
        self,
        trade_id: str,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create settlement for executed trade
        """
        
        self.settlement_counter += 1
        settlement_id = f"STL-{self.settlement_counter:08d}"
        
        # Calculate settlement date (T+2)
        trade_date = datetime.fromisoformat(trade_data["executed_at"])
        settlement_date = self._calculate_settlement_date(trade_date)
        
        settlement_data = {
            "settlement_id": settlement_id,
            "trade_id": trade_id,
            "client_id": trade_data["client_id"],
            "ticker": trade_data["ticker"],
            "side": trade_data["side"],
            "quantity": trade_data["quantity"],
            "price": trade_data["price"],
            "value": trade_data["value"],
            "trade_date": trade_date.isoformat(),
            "settlement_date": settlement_date.isoformat(),
            "status": SettlementStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store settlement
        self.settlements[settlement_id] = settlement_data
        
        # Add to queue
        self.settlement_queue.append(settlement_data)
        
        # Ingest into Data Mesh
        from ultracore.datamesh.transaction_mesh import transaction_data_mesh
        await transaction_data_mesh.ingest_settlement(
            settlement_id=settlement_id,
            settlement_data=settlement_data
        )
        
        # Produce Kafka event
        await transaction_kafka.produce_settlement_event(
            TransactionEventType.SETTLEMENT_PENDING,
            settlement_data
        )
        
        print(f"📅 Settlement created: {settlement_id} (settles on {settlement_date.date()})")
        
        return settlement_data
    
    async def process_settlements(
        self,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Process settlements due for settlement
        """
        
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)
        
        # Find settlements due
        due_settlements = [
            s for s in self.settlement_queue
            if datetime.fromisoformat(s["settlement_date"]) <= as_of_date
            and s["status"] == SettlementStatus.PENDING
        ]
        
        results = {
            "processed": 0,
            "completed": 0,
            "failed": 0,
            "settlements": []
        }
        
        for settlement in due_settlements:
            try:
                result = await self._settle_trade(settlement)
                
                if result["status"] == SettlementStatus.COMPLETED:
                    results["completed"] += 1
                else:
                    results["failed"] += 1
                
                results["settlements"].append(result)
                results["processed"] += 1
                
            except Exception as e:
                print(f"❌ Settlement failed: {settlement['settlement_id']} - {e}")
                results["failed"] += 1
        
        return results
    
    async def _settle_trade(
        self,
        settlement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Settle individual trade
        """
        
        settlement_id = settlement["settlement_id"]
        
        # Update status
        settlement["status"] = SettlementStatus.IN_PROGRESS
        settlement["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Produce event
        await transaction_kafka.produce_settlement_event(
            TransactionEventType.SETTLEMENT_IN_PROGRESS,
            settlement
        )
        
        try:
            # 1. Process cash movement
            cash_result = await self._process_cash_movement(settlement)
            
            # 2. Update positions
            position_result = await self._update_position(settlement)
            
            # 3. Mark as completed
            settlement["status"] = SettlementStatus.COMPLETED
            settlement["completed_at"] = datetime.now(timezone.utc).isoformat()
            settlement["cash_movement"] = cash_result
            settlement["position_update"] = position_result
            
            # Produce completion event
            await transaction_kafka.produce_settlement_event(
                TransactionEventType.SETTLEMENT_COMPLETED,
                settlement
            )
            
            # Remove from queue
            self.settlement_queue = [
                s for s in self.settlement_queue
                if s["settlement_id"] != settlement_id
            ]
            
            print(f"✅ Settlement completed: {settlement_id}")
            
            return settlement
            
        except Exception as e:
            # Mark as failed
            settlement["status"] = SettlementStatus.FAILED
            settlement["failure_reason"] = str(e)
            settlement["failed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Produce failure event
            await transaction_kafka.produce_settlement_event(
                TransactionEventType.SETTLEMENT_FAILED,
                settlement
            )
            
            print(f"❌ Settlement failed: {settlement_id} - {e}")
            
            return settlement
    
    async def _process_cash_movement(
        self,
        settlement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process cash debit/credit
        """
        
        client_id = settlement["client_id"]
        side = settlement["side"]
        value = settlement["value"]
        
        if side == "buy":
            # Debit cash for purchase
            movement_type = "debit"
            amount = -value
        else:
            # Credit cash for sale
            movement_type = "credit"
            amount = value
        
        # Produce cash event
        await transaction_kafka.produce_cash_event(
            TransactionEventType.CASH_DEBITED if side == "buy" else TransactionEventType.CASH_CREDITED,
            {
                "client_id": client_id,
                "settlement_id": settlement["settlement_id"],
                "amount": amount,
                "type": movement_type,
                "ticker": settlement["ticker"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "client_id": client_id,
            "movement_type": movement_type,
            "amount": amount
        }
    
    async def _update_position(
        self,
        settlement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update holdings positions
        """
        
        client_id = settlement["client_id"]
        ticker = settlement["ticker"]
        side = settlement["side"]
        quantity = settlement["quantity"]
        price = settlement["price"]
        
        if side == "buy":
            # Open or add to position
            result = await holdings_service.open_position(
                client_id=client_id,
                ticker=ticker,
                quantity=quantity,
                purchase_price=price,
                purchase_date=datetime.fromisoformat(settlement["trade_date"]),
                transaction_id=settlement["settlement_id"]
            )
            
            return {
                "action": "position_opened",
                "position_id": result["position_id"]
            }
        else:
            # Close or reduce position
            # Find existing position
            positions = await holdings_service.get_client_positions(
                client_id=client_id,
                status="open"
            )
            
            position = next(
                (p for p in positions if p["ticker"] == ticker),
                None
            )
            
            if position:
                result = await holdings_service.close_position(
                    position_id=position["position_id"],
                    sale_price=price,
                    sale_date=datetime.fromisoformat(settlement["trade_date"]),
                    transaction_id=settlement["settlement_id"]
                )
                
                return {
                    "action": "position_closed",
                    "position_id": position["position_id"],
                    "realized_gl": result.get("realized_gl", 0)
                }
            else:
                return {
                    "action": "no_position_found",
                    "message": "Cannot close position - no existing position found"
                }
    
    def _calculate_settlement_date(self, trade_date: datetime) -> datetime:
        """
        Calculate T+2 settlement date
        Skips weekends
        """
        
        settlement_date = trade_date + timedelta(days=2)
        
        # Skip weekends
        while settlement_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            settlement_date += timedelta(days=1)
        
        return settlement_date
    
    def get_settlement(self, settlement_id: str) -> Optional[Dict[str, Any]]:
        """Get settlement details"""
        return self.settlements.get(settlement_id)
    
    def get_pending_settlements(self) -> List[Dict[str, Any]]:
        """Get all pending settlements"""
        return [
            s for s in self.settlement_queue
            if s["status"] == SettlementStatus.PENDING
        ]
    
    def get_settlements_due_today(self) -> List[Dict[str, Any]]:
        """Get settlements due today"""
        today = datetime.now(timezone.utc).date()
        
        return [
            s for s in self.settlement_queue
            if datetime.fromisoformat(s["settlement_date"]).date() == today
            and s["status"] == SettlementStatus.PENDING
        ]
    
    def _handle_settlement_event(self, event: Dict[str, Any]):
        """Handle settlement events from Kafka"""
        
        event_type = event["event_type"]
        data = event["data"]
        
        print(f"📥 Settlement event: {event_type} - {data.get('settlement_id')}")

# Global instance
settlement_engine = SettlementEngine()
