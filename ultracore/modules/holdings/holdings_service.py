"""
Holdings Service - Core CRUD with Kafka, Data Mesh, and AI
Complete position tracking and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ultracore.streaming.kafka_events import kafka_producer, event_store, EventType
from ultracore.datamesh.holdings_mesh import holdings_data_mesh
from ultracore.agents.holdings_agent import holdings_agent
from ultracore.ml.rl.portfolio_agent import portfolio_rl_agent

class HoldingsService:
    """
    Enterprise holdings management service
    
    Features:
    - Event-sourced position tracking
    - Real-time valuation
    - Data Mesh integration
    - AI monitoring
    - RL optimization
    """
    
    def __init__(self):
        self.positions = {}
        self.position_counter = 0
        
        # Subscribe to Kafka events
        kafka_producer.subscribe(
            "holdings.positions",
            self._handle_position_event
        )
    
    async def open_position(
        self,
        client_id: str,
        ticker: str,
        quantity: float,
        purchase_price: float,
        purchase_date: Optional[datetime] = None,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Open new position
        Event-sourced with Kafka
        """
        
        self.position_counter += 1
        position_id = f"POS-{self.position_counter:08d}"
        
        if purchase_date is None:
            purchase_date = datetime.now(timezone.utc)
        
        cost_basis = quantity * purchase_price
        
        position_data = {
            "position_id": position_id,
            "client_id": client_id,
            "ticker": ticker,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "purchase_date": purchase_date.isoformat(),
            "cost_basis": cost_basis,
            "market_value": cost_basis,  # Initial value
            "current_price": purchase_price,
            "unrealized_gl": 0,
            "unrealized_gl_pct": 0,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "transaction_id": transaction_id
        }
        
        # Store position
        self.positions[position_id] = position_data
        
        # Ingest into Data Mesh
        mesh_result = await holdings_data_mesh.ingest_position(
            position_id=position_id,
            position_data=position_data,
            source="trading_system",
            created_by=client_id
        )
        
        # Produce Kafka event
        event = await kafka_producer.produce(
            topic="holdings.positions",
            event_type=EventType.POSITION_OPENED,
            data=position_data,
            key=client_id
        )
        
        # Store in event store
        event_store.append_event(event)
        
        # Create snapshot
        event_store.create_snapshot(position_id, position_data)
        
        print(f"✅ Position opened: {position_id} ({ticker} x {quantity})")
        
        return {
            "position_id": position_id,
            "position": position_data,
            "mesh_quality": mesh_result["quality_score"],
            "event_id": event["event_id"]
        }
    
    async def close_position(
        self,
        position_id: str,
        sale_price: float,
        sale_date: Optional[datetime] = None,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close position
        Calculates realized gain/loss
        """
        
        position = self.positions.get(position_id)
        if not position:
            return {"error": "Position not found"}
        
        if sale_date is None:
            sale_date = datetime.now(timezone.utc)
        
        quantity = position["quantity"]
        cost_basis = position["cost_basis"]
        sale_proceeds = quantity * sale_price
        
        realized_gl = sale_proceeds - cost_basis
        realized_gl_pct = (realized_gl / cost_basis) if cost_basis > 0 else 0
        
        # Update position
        position.update({
            "status": "closed",
            "sale_price": sale_price,
            "sale_date": sale_date.isoformat(),
            "sale_proceeds": sale_proceeds,
            "realized_gl": realized_gl,
            "realized_gl_pct": realized_gl_pct,
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "closing_transaction_id": transaction_id
        })
        
        # Update in Data Mesh
        await holdings_data_mesh.ingest_position(
            position_id=position_id,
            position_data=position,
            source="trading_system",
            created_by=position["client_id"]
        )
        
        # Produce Kafka event
        event = await kafka_producer.produce(
            topic="holdings.positions",
            event_type=EventType.POSITION_CLOSED,
            data={
                "position_id": position_id,
                "realized_gl": realized_gl,
                "realized_gl_pct": realized_gl_pct,
                **position
            },
            key=position["client_id"]
        )
        
        # Store in event store
        event_store.append_event(event)
        
        print(f"✅ Position closed: {position_id} (P&L: ${realized_gl:,.2f})")
        
        return {
            "position_id": position_id,
            "position": position,
            "realized_gl": realized_gl,
            "realized_gl_pct": realized_gl_pct,
            "event_id": event["event_id"]
        }
    
    async def update_position_value(
        self,
        position_id: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Update position with current market price
        Real-time mark-to-market
        """
        
        position = self.positions.get(position_id)
        if not position:
            return {"error": "Position not found"}
        
        if position["status"] != "open":
            return {"error": "Position is closed"}
        
        quantity = position["quantity"]
        cost_basis = position["cost_basis"]
        
        market_value = quantity * current_price
        unrealized_gl = market_value - cost_basis
        unrealized_gl_pct = (unrealized_gl / cost_basis) if cost_basis > 0 else 0
        
        # Update position
        position.update({
            "current_price": current_price,
            "market_value": market_value,
            "unrealized_gl": unrealized_gl,
            "unrealized_gl_pct": unrealized_gl_pct,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        
        # Update in Data Mesh
        await holdings_data_mesh.ingest_position(
            position_id=position_id,
            position_data=position,
            source="market_data",
            created_by="system"
        )
        
        # Produce Kafka event
        await kafka_producer.produce(
            topic="holdings.valuations",
            event_type=EventType.POSITION_VALUED,
            data={
                "position_id": position_id,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_gl": unrealized_gl
            },
            key=position["client_id"]
        )
        
        return {
            "position_id": position_id,
            "market_value": market_value,
            "unrealized_gl": unrealized_gl,
            "unrealized_gl_pct": unrealized_gl_pct
        }
    
    async def get_position(
        self,
        position_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get position with optional lineage"""
        
        position = self.positions.get(position_id)
        if not position:
            return None
        
        if include_lineage:
            # Get from Data Mesh with lineage
            mesh_data = holdings_data_mesh.query_position(
                position_id,
                include_lineage=True
            )
            if mesh_data:
                position = mesh_data
        
        return position
    
    async def get_client_positions(
        self,
        client_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all positions for client"""
        
        # First try Data Mesh materialized view
        positions = holdings_data_mesh.query_client_positions(client_id)
        
        if not positions:
            # Fallback to in-memory
            positions = [
                p for p in self.positions.values()
                if p["client_id"] == client_id
            ]
        
        if status:
            positions = [p for p in positions if p.get("status") == status]
        
        return positions
    
    async def get_portfolio_value(
        self,
        client_id: str,
        real_time: bool = True
    ) -> Dict[str, Any]:
        """
        Get portfolio valuation
        Can use materialized view or real-time pricing
        """
        
        if not real_time:
            # Use materialized view from Data Mesh
            return holdings_data_mesh.get_portfolio_valuation(client_id)
        
        # Real-time valuation
        positions = await self.get_client_positions(client_id, status="open")
        
        if not positions:
            return {
                "client_id": client_id,
                "total_value": 0,
                "total_cost": 0,
                "unrealized_gl": 0,
                "positions_count": 0
            }
        
        # Update all positions with current prices
        from ultracore.services.ultrawealth import ultrawealth_service
        
        tickers = list(set(p["ticker"] for p in positions))
        
        try:
            prices = await ultrawealth_service.get_portfolio_prices(tickers)
            
            # Update each position
            for position in positions:
                ticker = position["ticker"]
                if ticker in prices:
                    await self.update_position_value(
                        position["position_id"],
                        prices[ticker]
                    )
        except Exception as e:
            print(f"Error updating prices: {e}")
        
        # Recalculate totals
        positions = await self.get_client_positions(client_id, status="open")
        
        total_value = sum(p.get("market_value", 0) for p in positions)
        total_cost = sum(p.get("cost_basis", 0) for p in positions)
        unrealized_gl = total_value - total_cost
        
        valuation = {
            "client_id": client_id,
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_gl": unrealized_gl,
            "return_pct": (unrealized_gl / total_cost * 100) if total_cost > 0 else 0,
            "positions_count": len(positions),
            "positions": positions,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        # Produce valuation event
        await kafka_producer.produce(
            topic="holdings.valuations",
            event_type=EventType.PORTFOLIO_VALUED,
            data=valuation,
            key=client_id
        )
        
        return valuation
    
    async def monitor_portfolio_with_ai(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Run AI monitoring on portfolio
        Uses holdings agent for analysis
        """
        
        portfolio = await self.get_portfolio_value(client_id, real_time=True)
        
        # Run AI monitoring
        monitoring = await holdings_agent.monitor_portfolio(client_id, portfolio)
        
        return monitoring
    
    async def get_rebalancing_recommendations(
        self,
        client_id: str,
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Get AI-powered rebalancing recommendations
        """
        
        portfolio = await self.get_portfolio_value(client_id, real_time=True)
        
        # Get AI recommendations
        recommendations = await holdings_agent.recommend_rebalancing(
            portfolio,
            target_allocation
        )
        
        return recommendations
    
    async def reconstruct_position_from_events(
        self,
        position_id: str
    ) -> Dict[str, Any]:
        """
        Reconstruct position state from event stream
        Demonstrates event sourcing capability
        """
        
        # Define event handlers
        def handle_opened(state, data):
            state.update(data)
            return state
        
        def handle_updated(state, data):
            state.update(data)
            return state
        
        def handle_closed(state, data):
            state.update(data)
            return state
        
        event_handlers = {
            EventType.POSITION_OPENED: handle_opened,
            EventType.POSITION_UPDATED: handle_updated,
            EventType.POSITION_CLOSED: handle_closed
        }
        
        # Reconstruct state
        state = event_store.reconstruct_state(position_id, event_handlers)
        
        return state
    
    def _handle_position_event(self, event: Dict[str, Any]):
        """
        Handle position events from Kafka
        This is called when events are produced
        """
        
        event_type = event["event_type"]
        data = event["data"]
        
        # Process event based on type
        if event_type == EventType.POSITION_OPENED:
            print(f"📥 Position opened event: {data.get('position_id')}")
        elif event_type == EventType.POSITION_CLOSED:
            print(f"📥 Position closed event: {data.get('position_id')}")
        elif event_type == EventType.POSITION_VALUED:
            # Could trigger alerts, analytics, etc.
            pass

# Global instance
holdings_service = HoldingsService()
