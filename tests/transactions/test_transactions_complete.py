"""
Comprehensive Transaction Module Test Suite
Tests all components: Kafka, AI, RL, Orders, Execution, Settlement
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Import all modules
from ultracore.modules.transactions.kafka_events import (
    transaction_kafka, TransactionEventType, OrderStatus, OrderType, OrderSide
)
from ultracore.datamesh.transaction_mesh import transaction_data_mesh
from ultracore.agents.transaction_agent import transaction_agent
from ultracore.ml.rl.execution_agent import execution_rl_agent, ExecutionAction
from ultracore.modules.transactions.order_service import order_management_service
from ultracore.modules.transactions.execution_engine import trade_execution_engine
from ultracore.modules.transactions.settlement_engine import settlement_engine
from ultracore.modules.transactions.history_service import transaction_history_service

class TestTransactionKafka:
    """Test Kafka event streaming for transactions"""
    
    @pytest.mark.asyncio
    async def test_order_event_production(self):
        """Test producing order events"""
        
        order_data = {
            "order_id": "TEST-ORD-001",
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100
        }
        
        event = await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_CREATED,
            order_data
        )
        
        assert event["event_type"] == TransactionEventType.ORDER_CREATED
        assert event["data"]["order_id"] == "TEST-ORD-001"
    
    @pytest.mark.asyncio
    async def test_trade_event_production(self):
        """Test producing trade events"""
        
        trade_data = {
            "trade_id": "TEST-TRD-001",
            "order_id": "TEST-ORD-001",
            "quantity": 100,
            "price": 100.00
        }
        
        event = await transaction_kafka.produce_trade_event(
            TransactionEventType.TRADE_EXECUTED,
            trade_data
        )
        
        assert event["event_type"] == TransactionEventType.TRADE_EXECUTED
        assert event["data"]["trade_id"] == "TEST-TRD-001"
    
    @pytest.mark.asyncio
    async def test_settlement_event_production(self):
        """Test producing settlement events"""
        
        settlement_data = {
            "settlement_id": "TEST-STL-001",
            "trade_id": "TEST-TRD-001",
            "status": "pending"
        }
        
        event = await transaction_kafka.produce_settlement_event(
            TransactionEventType.SETTLEMENT_PENDING,
            settlement_data
        )
        
        assert event["event_type"] == TransactionEventType.SETTLEMENT_PENDING

class TestTransactionDataMesh:
    """Test Data Mesh for transactions"""
    
    @pytest.mark.asyncio
    async def test_ingest_order(self):
        """Test ingesting order into Data Mesh"""
        
        order_data = {
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
        }
        
        result = await transaction_data_mesh.ingest_order(
            order_id="TEST-ORD-001",
            order_data=order_data,
            source="test",
            created_by="test_user"
        )
        
        assert result["quality_score"] > 0
        assert "quality_level" in result
    
    def test_query_order(self):
        """Test querying order from Data Mesh"""
        
        order = transaction_data_mesh.query_order("TEST-ORD-001")
        
        if order:
            assert order["ticker"] == "VAS.AX"
    
    def test_order_quality_calculation(self):
        """Test data quality scoring"""
        
        complete_order = {
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100,
            "order_type": "limit",
            "limit_price": 100.00,
            "time_in_force": "day"
        }
        
        quality = transaction_data_mesh._calculate_order_quality(complete_order)
        assert quality > 80

class TestTransactionAgent:
    """Test AI Transaction Agent"""
    
    @pytest.mark.asyncio
    async def test_order_validation(self):
        """Test AI order validation"""
        
        order = {
            "order_id": "TEST-ORD-001",
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
        }
        
        client_data = {
            "kyc_completed": True,
            "status": "active",
            "trading_enabled": True
        }
        
        portfolio = {
            "total_value": 100000,
            "positions": []
        }
        
        validation = await transaction_agent.validate_order(
            order, client_data, portfolio
        )
        
        assert "decision" in validation
        assert validation["decision"] in ["approved", "rejected", "review", "fraud"]
    
    @pytest.mark.asyncio
    async def test_fraud_detection(self):
        """Test fraud detection"""
        
        order = {
            "order_id": "TEST-ORD-002",
            "ticker": "VAS.AX",
            "quantity": 10000,
            "limit_price": 100.00,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client_history = []
        
        fraud_result = await transaction_agent.detect_fraud(order, client_history)
        
        assert "fraud_detected" in fraud_result
        assert "risk_level" in fraud_result
    
    @pytest.mark.asyncio
    async def test_execution_optimization(self):
        """Test execution optimization"""
        
        order = {
            "ticker": "VAS.AX",
            "quantity": 1000,
            "side": "buy"
        }
        
        market_data = {
            "avg_volume": 1000000,
            "spread": 0.001,
            "volatility": 0.02
        }
        
        optimization = await transaction_agent.optimize_execution(order, market_data)
        
        assert "strategy" in optimization
        assert "recommendation" in optimization

class TestExecutionRLAgent:
    """Test Reinforcement Learning Execution Agent"""
    
    def test_state_representation(self):
        """Test execution state representation"""
        
        order = {
            "quantity": 1000,
            "time_in_force": "day"
        }
        
        market = {
            "volatility": 0.02,
            "spread": 0.001,
            "avg_volume": 1000000
        }
        
        execution_progress = {
            "remaining_quantity": 50
        }
        
        state = execution_rl_agent.get_state(order, market, execution_progress)
        
        assert state is not None
        assert isinstance(state, str)
    
    def test_action_selection(self):
        """Test action selection"""
        
        order = {"quantity": 1000, "time_in_force": "day"}
        market = {"volatility": 0.02, "spread": 0.001, "avg_volume": 1000000}
        
        state = "test-state"
        action = execution_rl_agent.select_action(state, order, market)
        
        assert action in ExecutionAction
    
    def test_training_episode(self):
        """Test RL training episode"""
        
        order = {
            "quantity": 1000,
            "side": "buy",
            "time_in_force": "day"
        }
        
        market_scenarios = [
            {"mid_price": 100, "spread": 0.001, "avg_volume": 1000000}
            for _ in range(10)
        ]
        
        result = execution_rl_agent.train_execution(order, market_scenarios, steps=10)
        
        assert "episode" in result
        assert "total_reward" in result
    
    def test_optimal_execution_plan(self):
        """Test generating optimal execution plan"""
        
        order = {
            "order_id": "TEST-ORD-001",
            "quantity": 1000,
            "time_in_force": "day"
        }
        
        market = {
            "mid_price": 100,
            "spread": 0.001,
            "avg_volume": 1000000
        }
        
        plan = execution_rl_agent.get_optimal_execution_plan(order, market)
        
        assert "plan" in plan
        assert len(plan["plan"]) > 0

class TestOrderManagement:
    """Test Order Management Service"""
    
    @pytest.mark.asyncio
    async def test_create_order(self):
        """Test creating order"""
        
        result = await order_management_service.create_order(
            client_id="TEST-CLIENT",
            ticker="VAS.AX",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        assert "order_id" in result
        assert result["order"]["ticker"] == "VAS.AX"
        assert result["order"]["status"] == OrderStatus.DRAFT
    
    @pytest.mark.asyncio
    async def test_validate_order(self):
        """Test order validation"""
        
        # Create order first
        create_result = await order_management_service.create_order(
            client_id="TEST-CLIENT-2",
            ticker="VGS.AX",
            side=OrderSide.BUY,
            quantity=50,
            order_type=OrderType.LIMIT,
            limit_price=150.00
        )
        
        order_id = create_result["order_id"]
        
        # Validate it
        client_data = {
            "kyc_completed": True,
            "status": "active",
            "trading_enabled": True
        }
        
        portfolio = {"total_value": 100000, "positions": []}
        
        validation = await order_management_service.validate_order(
            order_id=order_id,
            client_data=client_data,
            portfolio=portfolio
        )
        
        assert "decision" in validation
    
    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Test cancelling order"""
        
        # Create order
        create_result = await order_management_service.create_order(
            client_id="TEST-CLIENT-3",
            ticker="VAF.AX",
            side=OrderSide.SELL,
            quantity=200,
            order_type=OrderType.MARKET
        )
        
        order_id = create_result["order_id"]
        
        # Cancel it
        cancel_result = await order_management_service.cancel_order(
            order_id=order_id,
            reason="Test cancellation"
        )
        
        assert cancel_result["status"] == OrderStatus.CANCELLED

class TestTradeExecution:
    """Test Trade Execution Engine"""
    
    @pytest.mark.asyncio
    async def test_execute_market_order(self):
        """Test executing market order"""
        
        # Create and submit order
        create_result = await order_management_service.create_order(
            client_id="TEST-CLIENT-4",
            ticker="VAS.AX",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        order_id = create_result["order_id"]
        
        # Submit for execution
        await order_management_service.submit_order(order_id)
        
        # Execute
        market_data = {
            "mid_price": 100.00,
            "bid_price": 99.95,
            "ask_price": 100.05,
            "spread": 0.001
        }
        
        result = await trade_execution_engine.execute_market_order(
            order_id=order_id,
            market_data=market_data
        )
        
        assert "trade_id" in result
    
    @pytest.mark.asyncio
    async def test_rl_optimized_execution(self):
        """Test RL-optimized execution"""
        
        # Create order
        create_result = await order_management_service.create_order(
            client_id="TEST-CLIENT-5",
            ticker="VGS.AX",
            side=OrderSide.BUY,
            quantity=1000,
            order_type=OrderType.MARKET
        )
        
        order_id = create_result["order_id"]
        await order_management_service.submit_order(order_id)
        
        # Execute with RL
        market_data = {
            "mid_price": 150.00,
            "spread": 0.001,
            "avg_volume": 1000000,
            "volatility": 0.02
        }
        
        result = await trade_execution_engine.execute_order(
            order_id=order_id,
            market_data=market_data,
            use_optimal_execution=True
        )
        
        assert "execution_strategy" in result

class TestSettlement:
    """Test Settlement Engine"""
    
    @pytest.mark.asyncio
    async def test_create_settlement(self):
        """Test creating settlement"""
        
        trade_data = {
            "trade_id": "TRD-TEST-001",
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100,
            "price": 100.00,
            "value": 10000,
            "executed_at": datetime.utcnow().isoformat()
        }
        
        settlement = await settlement_engine.create_settlement(
            trade_id="TRD-TEST-001",
            trade_data=trade_data
        )
        
        assert settlement["status"] == "pending"
        assert "settlement_date" in settlement
    
    @pytest.mark.asyncio
    async def test_settlement_date_calculation(self):
        """Test T+2 settlement date calculation"""
        
        trade_date = datetime(2025, 1, 15)  # Wednesday
        settlement_date = settlement_engine._calculate_settlement_date(trade_date)
        
        # T+2 = Friday
        assert settlement_date.date() == datetime(2025, 1, 17).date()
    
    @pytest.mark.asyncio
    async def test_process_settlements(self):
        """Test processing settlements"""
        
        # Create a settlement that's due
        trade_data = {
            "trade_id": "TRD-TEST-002",
            "client_id": "TEST-CLIENT",
            "ticker": "VGS.AX",
            "side": "buy",
            "quantity": 50,
            "price": 150.00,
            "value": 7500,
            "executed_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
        }
        
        await settlement_engine.create_settlement("TRD-TEST-002", trade_data)
        
        # Process settlements
        result = await settlement_engine.process_settlements()
        
        assert "processed" in result

class TestTransactionHistory:
    """Test Transaction History Service"""
    
    @pytest.mark.asyncio
    async def test_record_transaction(self):
        """Test recording transaction"""
        
        transaction_data = {
            "order_id": "ORD-TEST-001",
            "client_id": "TEST-CLIENT",
            "ticker": "VAS.AX"
        }
        
        await transaction_history_service.record_transaction(
            "order",
            transaction_data
        )
        
        assert len(transaction_history_service.history) > 0
    
    @pytest.mark.asyncio
    async def test_get_client_history(self):
        """Test getting client history"""
        
        history = await transaction_history_service.get_client_history(
            client_id="TEST-CLIENT"
        )
        
        assert isinstance(history, list)
    
    @pytest.mark.asyncio
    async def test_trading_summary(self):
        """Test trading summary"""
        
        summary = await transaction_history_service.get_trading_summary(
            client_id="TEST-CLIENT",
            period="ytd"
        )
        
        assert "total_orders" in summary
        assert "total_trades" in summary

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("  🧪 RUNNING TRANSACTION MODULE TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

if __name__ == "__main__":
    run_all_tests()
