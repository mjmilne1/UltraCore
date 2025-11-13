"""
Comprehensive Holdings Module Test Suite
Tests all components: Kafka, Data Mesh, AI Agents, RL, Services
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Import all modules
from ultracore.streaming.kafka_events import kafka_producer, event_store, EventType
from ultracore.datamesh.holdings_mesh import holdings_data_mesh
from ultracore.agents.holdings_agent import holdings_agent
from ultracore.ml.rl.portfolio_agent import portfolio_rl_agent, Action
from ultracore.modules.holdings.holdings_service import holdings_service
from ultracore.modules.holdings.position_tracker import position_tracker, CostBasisMethod
from ultracore.modules.holdings.performance_analytics import performance_analytics
from ultracore.modules.holdings.rebalancing_engine import rebalancing_engine

class TestKafkaEventStreaming:
    """Test Kafka event streaming"""
    
    @pytest.mark.asyncio
    async def test_produce_event(self):
        """Test producing events to Kafka"""
        
        event = await kafka_producer.produce(
            topic="holdings.positions",
            event_type=EventType.POSITION_OPENED,
            data={"position_id": "TEST-001", "ticker": "VAS.AX"},
            key="TEST-CLIENT"
        )
        
        assert event["event_type"] == EventType.POSITION_OPENED
        assert event["topic"] == "holdings.positions"
        assert "event_id" in event
    
    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test subscribing to Kafka topics"""
        
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        kafka_producer.subscribe("holdings.test", handler)
        
        await kafka_producer.produce(
            topic="holdings.test",
            event_type=EventType.POSITION_UPDATED,
            data={"test": "data"},
            key="test"
        )
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]["data"]["test"] == "data"
    
    def test_event_store(self):
        """Test event sourcing store"""
        
        event = {
            "event_id": "evt-123",
            "event_type": EventType.POSITION_OPENED,
            "key": "POS-001",
            "data": {"quantity": 100}
        }
        
        event_store.append_event(event)
        
        events = event_store.get_events_for_aggregate("POS-001")
        assert len(events) > 0

class TestDataMesh:
    """Test Data Mesh integration"""
    
    @pytest.mark.asyncio
    async def test_ingest_position(self):
        """Test ingesting position into Data Mesh"""
        
        position_data = {
            "ticker": "VAS.AX",
            "quantity": 100,
            "cost_basis": 10000,
            "client_id": "CLT-001"
        }
        
        result = await holdings_data_mesh.ingest_position(
            position_id="POS-TEST-001",
            position_data=position_data,
            source="test",
            created_by="test_user"
        )
        
        assert result["quality_score"] > 0
        assert result["quality_level"] in ["excellent", "good", "acceptable", "poor"]
    
    def test_query_position(self):
        """Test querying position from Data Mesh"""
        
        position = holdings_data_mesh.query_position("POS-TEST-001")
        
        if position:
            assert position["ticker"] == "VAS.AX"
    
    def test_data_quality_calculation(self):
        """Test data quality scoring"""
        
        # Complete data
        complete_data = {
            "ticker": "VAS.AX",
            "quantity": 100,
            "cost_basis": 10000,
            "client_id": "CLT-001",
            "purchase_date": "2024-01-01",
            "market_value": 11000,
            "current_price": 110
        }
        
        quality = holdings_data_mesh._calculate_position_quality(complete_data)
        assert quality > 80

class TestRLAgent:
    """Test Reinforcement Learning agent"""
    
    def test_state_representation(self):
        """Test portfolio state representation"""
        
        portfolio = {
            "total_value": 100000,
            "positions": [
                {"ticker": "VAS.AX", "market_value": 50000},
                {"ticker": "VGS.AX", "market_value": 50000}
            ]
        }
        
        state = portfolio_rl_agent.get_state(portfolio)
        assert state is not None
        assert isinstance(state, str)
    
    def test_action_selection(self):
        """Test RL action selection"""
        
        portfolio = {
            "total_value": 100000,
            "positions": []
        }
        
        state = portfolio_rl_agent.get_state(portfolio)
        action = portfolio_rl_agent.select_action(state, portfolio)
        
        assert action in Action
    
    def test_reward_calculation(self):
        """Test reward calculation"""
        
        prev_portfolio = {"total_value": 100000}
        curr_portfolio = {"total_value": 105000, "positions": []}
        
        reward = portfolio_rl_agent.calculate_reward(
            prev_portfolio,
            curr_portfolio,
            Action.HOLD
        )
        
        assert isinstance(reward, float)
    
    def test_training_episode(self):
        """Test RL training episode"""
        
        initial_portfolio = {
            "total_value": 100000,
            "positions": []
        }
        
        market_simulation = [
            {"return": 0.01},
            {"return": -0.005},
            {"return": 0.02}
        ]
        
        result = portfolio_rl_agent.train_episode(
            initial_portfolio,
            market_simulation,
            steps=3
        )
        
        assert "total_reward" in result
        assert "q_table_size" in result

class TestHoldingsAgent:
    """Test AI Holdings Agent"""
    
    @pytest.mark.asyncio
    async def test_portfolio_monitoring(self):
        """Test AI portfolio monitoring"""
        
        portfolio = {
            "total_value": 100000,
            "positions": [
                {
                    "ticker": "VAS.AX",
                    "market_value": 40000,
                    "cost_basis": 35000,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                },
                {
                    "ticker": "VGS.AX",
                    "market_value": 60000,
                    "cost_basis": 55000,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        monitoring = await holdings_agent.monitor_portfolio("TEST-CLIENT", portfolio)
        
        assert "alerts" in monitoring
        assert "recommendations" in monitoring
        assert "portfolio_health_score" in monitoring
    
    @pytest.mark.asyncio
    async def test_rebalancing_recommendation(self):
        """Test AI rebalancing recommendations"""
        
        portfolio = {
            "total_value": 100000,
            "positions": [
                {"ticker": "VAS.AX", "market_value": 70000},
                {"ticker": "VGS.AX", "market_value": 30000}
            ]
        }
        
        target = {
            "VAS.AX": 0.50,
            "VGS.AX": 0.50
        }
        
        recommendation = await holdings_agent.recommend_rebalancing(portfolio, target)
        
        assert "recommended" in recommendation
        assert "trades" in recommendation

class TestHoldingsService:
    """Test Holdings Service"""
    
    @pytest.mark.asyncio
    async def test_open_position(self):
        """Test opening position"""
        
        result = await holdings_service.open_position(
            client_id="TEST-CLIENT-001",
            ticker="VAS.AX",
            quantity=100,
            purchase_price=100.50
        )
        
        assert "position_id" in result
        assert result["position"]["ticker"] == "VAS.AX"
        assert result["position"]["quantity"] == 100
    
    @pytest.mark.asyncio
    async def test_close_position(self):
        """Test closing position"""
        
        # First open a position
        open_result = await holdings_service.open_position(
            client_id="TEST-CLIENT-002",
            ticker="VGS.AX",
            quantity=50,
            purchase_price=150.00
        )
        
        position_id = open_result["position_id"]
        
        # Now close it
        close_result = await holdings_service.close_position(
            position_id=position_id,
            sale_price=160.00
        )
        
        assert close_result["realized_gl"] == (160.00 - 150.00) * 50
        assert close_result["position"]["status"] == "closed"
    
    @pytest.mark.asyncio
    async def test_update_position_value(self):
        """Test updating position value"""
        
        # Open position
        open_result = await holdings_service.open_position(
            client_id="TEST-CLIENT-003",
            ticker="VAF.AX",
            quantity=200,
            purchase_price=50.00
        )
        
        position_id = open_result["position_id"]
        
        # Update value
        update_result = await holdings_service.update_position_value(
            position_id=position_id,
            current_price=55.00
        )
        
        assert update_result["market_value"] == 200 * 55.00
        assert update_result["unrealized_gl"] == (55.00 - 50.00) * 200
    
    @pytest.mark.asyncio
    async def test_get_portfolio_value(self):
        """Test getting portfolio valuation"""
        
        valuation = await holdings_service.get_portfolio_value(
            "TEST-CLIENT-001",
            real_time=False
        )
        
        assert "total_value" in valuation
        assert "unrealized_gl" in valuation

class TestPositionTracker:
    """Test Position Tracker with Cost Basis"""
    
    def test_add_purchase(self):
        """Test adding purchase lot"""
        
        lot = position_tracker.add_purchase(
            ticker="TEST.AX",
            quantity=100,
            purchase_price=50.00,
            purchase_date=datetime.now(timezone.utc),
            transaction_id="TXN-001"
        )
        
        assert lot.ticker == "TEST.AX"
        assert lot.quantity == 100
        assert lot.remaining_quantity == 100
    
    def test_sell_position_fifo(self):
        """Test selling with FIFO method"""
        
        # Add two lots
        position_tracker.add_purchase(
            ticker="FIFO.AX",
            quantity=100,
            purchase_price=50.00,
            purchase_date=datetime.now(timezone.utc) - timedelta(days=30),
            transaction_id="TXN-001"
        )
        
        position_tracker.add_purchase(
            ticker="FIFO.AX",
            quantity=100,
            purchase_price=60.00,
            purchase_date=datetime.now(timezone.utc),
            transaction_id="TXN-002"
        )
        
        # Sell 150 shares
        result = position_tracker.sell_position(
            ticker="FIFO.AX",
            quantity=150,
            sale_price=70.00,
            sale_date=datetime.now(timezone.utc),
            method=CostBasisMethod.FIFO
        )
        
        # Should sell all of first lot (100 @ $50) and 50 of second lot (50 @ $60)
        expected_cost_basis = (100 * 50.00) + (50 * 60.00)
        
        assert abs(result["total_cost_basis"] - expected_cost_basis) < 0.01
    
    def test_tax_loss_harvesting(self):
        """Test tax loss harvesting identification"""
        
        position_tracker.add_purchase(
            ticker="LOSS.AX",
            quantity=100,
            purchase_price=100.00,
            purchase_date=datetime.now(timezone.utc) - timedelta(days=60),
            transaction_id="TXN-003"
        )
        
        opportunities = position_tracker.tax_loss_harvest_opportunities(
            ticker="LOSS.AX",
            current_price=80.00,  # $20 loss per share
            min_loss=1000
        )
        
        assert len(opportunities) == 1
        assert opportunities[0]["potential_loss"] == -2000  # 100 shares * $20 loss

class TestPerformanceAnalytics:
    """Test Performance Analytics"""
    
    def test_total_return(self):
        """Test total return calculation"""
        
        result = performance_analytics.calculate_total_return(
            start_value=100000,
            end_value=120000
        )
        
        assert result["total_return"] == 20000
        assert result["total_return_pct"] == 0.20
    
    def test_cagr(self):
        """Test CAGR calculation"""
        
        cagr = performance_analytics.calculate_cagr(
            start_value=100000,
            end_value=121000,
            years=2
        )
        
        # Should be approximately 10% per year
        assert 0.09 < cagr < 0.11
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, 0.02]
        
        sharpe = performance_analytics.calculate_sharpe_ratio(returns)
        
        assert isinstance(sharpe, float)
    
    def test_max_drawdown(self):
        """Test maximum drawdown calculation"""
        
        values = [100, 110, 105, 120, 100, 130]
        
        result = performance_analytics.calculate_max_drawdown(values)
        
        assert result["max_drawdown_pct"] < 0  # Should be negative
    
    def test_comprehensive_metrics(self):
        """Test comprehensive metrics calculation"""
        
        history = [
            {"date": "2024-01-01", "total_value": 100000},
            {"date": "2024-03-01", "total_value": 105000},
            {"date": "2024-06-01", "total_value": 110000},
            {"date": "2024-09-01", "total_value": 108000},
            {"date": "2024-12-01", "total_value": 115000}
        ]
        
        metrics = performance_analytics.calculate_comprehensive_metrics(history)
        
        assert "returns" in metrics
        assert "risk" in metrics
        assert metrics["returns"]["total_return_pct"] > 0

class TestRebalancingEngine:
    """Test Rebalancing Engine"""
    
    @pytest.mark.asyncio
    async def test_evaluate_rebalancing_need(self):
        """Test evaluating rebalancing need"""
        
        current = {
            "VAS.AX": 0.60,
            "VGS.AX": 0.40
        }
        
        target = {
            "VAS.AX": 0.50,
            "VGS.AX": 0.50
        }
        
        evaluation = await rebalancing_engine.evaluate_rebalancing_need(
            current_allocation=current,
            target_allocation=target
        )
        
        assert "needs_rebalancing" in evaluation
        assert "max_drift" in evaluation
    
    @pytest.mark.asyncio
    async def test_generate_rebalancing_trades(self):
        """Test generating rebalancing trades"""
        
        positions = [
            {"ticker": "VAS.AX", "market_value": 60000, "current_price": 100},
            {"ticker": "VGS.AX", "market_value": 40000, "current_price": 80}
        ]
        
        target = {
            "VAS.AX": 0.50,
            "VGS.AX": 0.50
        }
        
        plan = await rebalancing_engine.generate_rebalancing_trades(
            current_positions=positions,
            target_allocation=target,
            total_value=100000
        )
        
        assert "trades" in plan
        assert len(plan["trades"]) > 0

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("  🧪 RUNNING HOLDINGS MODULE TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

if __name__ == "__main__":
    run_all_tests()
