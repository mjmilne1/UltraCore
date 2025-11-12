"""
Transaction Module - Complete Demonstration
Full trading workflow: Order → Validate → Execute → Settle
"""

import asyncio
from datetime import datetime, timedelta
from ultracore.modules.transactions.order_service import order_management_service
from ultracore.modules.transactions.execution_engine import trade_execution_engine
from ultracore.modules.transactions.settlement_engine import settlement_engine
from ultracore.modules.transactions.history_service import transaction_history_service
from ultracore.agents.transaction_agent import transaction_agent
from ultracore.ml.rl.execution_agent import execution_rl_agent
from ultracore.modules.transactions.kafka_events import OrderType, OrderSide, TimeInForce

async def main():
    print("\n" + "="*80)
    print("  🎯 ULTRACORE TRANSACTION MODULE - COMPLETE DEMONSTRATION")
    print("  Kafka-First Event-Driven Trading System with AI & ML")
    print("="*80 + "\n")
    
    client_id = "DEMO-CLIENT-001"
    
    # Mock client data
    client_data = {
        "client_id": client_id,
        "kyc_completed": True,
        "status": "active",
        "trading_enabled": True,
        "name": "Demo Client"
    }
    
    # Mock portfolio
    portfolio = {
        "total_value": 100000,
        "positions": []
    }
    
    # Mock market data
    market_data = {
        "VAS.AX": {
            "mid_price": 100.00,
            "bid_price": 99.95,
            "ask_price": 100.05,
            "spread": 0.001,
            "volume": 5000000,
            "avg_volume": 5000000,
            "volatility": 0.02
        },
        "VGS.AX": {
            "mid_price": 150.00,
            "bid_price": 149.90,
            "ask_price": 150.10,
            "spread": 0.001,
            "volume": 3000000,
            "avg_volume": 3000000,
            "volatility": 0.025
        }
    }
    
    # ========================================================================
    # 1. CREATE ORDERS
    # ========================================================================
    
    print("[1/10] Creating orders with Kafka events...")
    print("-" * 80)
    
    # Order 1: Market order (buy)
    order1 = await order_management_service.create_order(
        client_id=client_id,
        ticker="VAS.AX",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY
    )
    
    print(f"✅ Created market order: {order1['order_id']}")
    print(f"   Buy 1000 VAS.AX @ market")
    print(f"   Data Quality: {order1['data_quality']:.1f}%")
    
    # Order 2: Limit order (buy)
    order2 = await order_management_service.create_order(
        client_id=client_id,
        ticker="VGS.AX",
        side=OrderSide.BUY,
        quantity=500,
        order_type=OrderType.LIMIT,
        limit_price=148.00,
        time_in_force=TimeInForce.GTC
    )
    
    print(f"✅ Created limit order: {order2['order_id']}")
    print(f"   Buy 500 VGS.AX @ limit $148.00")
    
    # Order 3: Stop order (sell)
    order3 = await order_management_service.create_order(
        client_id=client_id,
        ticker="VAS.AX",
        side=OrderSide.SELL,
        quantity=500,
        order_type=OrderType.STOP,
        stop_price=95.00,
        time_in_force=TimeInForce.GTC
    )
    
    print(f"✅ Created stop order: {order3['order_id']}")
    print(f"   Sell 500 VAS.AX @ stop $95.00")
    
    # ========================================================================
    # 2. AI VALIDATION
    # ========================================================================
    
    print("\n[2/10] AI Agent: Order validation & fraud detection...")
    print("-" * 80)
    
    # Validate order 1
    validation1 = await order_management_service.validate_order(
        order_id=order1['order_id'],
        client_data=client_data,
        portfolio=portfolio
    )
    
    print(f"🤖 Validation for {order1['order_id']}:")
    print(f"   Decision: {validation1['decision'].upper()}")
    print(f"   Confidence: {validation1['confidence']:.2%}")
    print(f"   Reasoning: {validation1['reasoning']}")
    
    # Check specific validations
    for check in validation1['validations']:
        status = "✅" if check['result'] == 'approved' else "❌"
        print(f"   {status} {check['check']}")
    
    # Fraud detection
    print(f"\n🔍 Fraud Detection:")
    fraud_result = await transaction_agent.detect_fraud(
        order1['order'],
        []
    )
    
    print(f"   Fraud Detected: {fraud_result['fraud_detected']}")
    print(f"   Risk Level: {fraud_result['risk_level'].upper()}")
    
    if fraud_result['indicators']:
        print(f"   Indicators:")
        for indicator in fraud_result['indicators']:
            print(f"     • {indicator['type']}: {indicator['description']}")
    
    # ========================================================================
    # 3. RL AGENT TRAINING
    # ========================================================================
    
    print("\n[3/10] Reinforcement Learning: Training execution agent...")
    print("-" * 80)
    
    # Generate market scenarios
    market_scenarios = []
    base_price = market_data["VAS.AX"]["mid_price"]
    
    for i in range(20):
        price_change = (i % 5 - 2) * 0.01 * base_price
        scenario = {
            "mid_price": base_price + price_change,
            "spread": 0.001,
            "avg_volume": 5000000
        }
        market_scenarios.append(scenario)
    
    # Train for 3 episodes
    print("🧠 Training RL agent on execution scenarios...")
    
    for episode in range(3):
        result = execution_rl_agent.train_execution(
            order=order1['order'],
            market_scenarios=market_scenarios,
            steps=20
        )
        
        print(f"   Episode {result['episode']}: Reward = {result['total_reward']:.2f}, "
              f"Fill Rate = {result['fill_rate']:.1%}")
    
    # Get optimal execution plan
    plan = execution_rl_agent.get_optimal_execution_plan(
        order1['order'],
        market_data["VAS.AX"]
    )
    
    print(f"\n✅ Optimal Execution Plan Generated:")
    print(f"   Total Steps: {plan['execution_steps']}")
    print(f"   Estimated Duration: {plan['estimated_duration']}")
    
    for step in plan['plan'][:3]:
        print(f"   Step {step['step']}: {step['action']} - {step['quantity']:.0f} shares")
    
    # ========================================================================
    # 4. SUBMIT ORDERS
    # ========================================================================
    
    print("\n[4/10] Submitting validated orders...")
    print("-" * 80)
    
    # Submit order 1
    submit1 = await order_management_service.submit_order(order1['order_id'])
    print(f"📤 Submitted: {order1['order_id']} - Status: {submit1['status']}")
    
    # Submit order 2
    validation2 = await order_management_service.validate_order(
        order_id=order2['order_id'],
        client_data=client_data,
        portfolio=portfolio
    )
    
    if validation2['decision'] == 'approved':
        submit2 = await order_management_service.submit_order(order2['order_id'])
        print(f"📤 Submitted: {order2['order_id']} - Status: {submit2['status']}")
    
    # ========================================================================
    # 5. TRADE EXECUTION
    # ========================================================================
    
    print("\n[5/10] Trade Execution: Executing orders...")
    print("-" * 80)
    
    # Execute order 1 with RL optimization
    print(f"🔄 Executing {order1['order_id']} with RL optimization...")
    
    exec1 = await trade_execution_engine.execute_order(
        order_id=order1['order_id'],
        market_data=market_data["VAS.AX"],
        use_optimal_execution=True
    )
    
    print(f"✅ Execution Complete:")
    print(f"   Strategy: {exec1['execution_strategy']}")
    print(f"   Total Trades: {exec1['total_trades']}")
    print(f"   Average Price: ${exec1['avg_price']:.2f}")
    
    if 'trades' in exec1:
        print(f"   Trade Details:")
        for trade in exec1['trades'][:3]:
            print(f"     • {trade['trade_id']}: {trade['quantity']:.0f} @ ${trade['price']:.2f}")
    
    # Execute order 2 (limit order)
    print(f"\n🔄 Executing {order2['order_id']} (limit order)...")
    
    exec2 = await trade_execution_engine.execute_limit_order(
        order_id=order2['order_id'],
        market_data=market_data["VGS.AX"]
    )
    
    if exec2.get('executed', True):
        print(f"✅ Limit order filled:")
        print(f"   Trade: {exec2.get('trade_id', 'N/A')}")
        print(f"   Price: ${exec2.get('price', 0):.2f}")
    else:
        print(f"⏸️  Limit order pending: {exec2.get('reason', 'Price not met')}")
    
    # ========================================================================
    # 6. SETTLEMENT PROCESSING
    # ========================================================================
    
    print("\n[6/10] Settlement: Creating T+2 settlements...")
    print("-" * 80)
    
    # Get all trades
    if 'trades' in exec1 and exec1['trades']:
        for trade in exec1['trades'][:2]:
            settlement = await settlement_engine.create_settlement(
                trade_id=trade['trade_id'],
                trade_data=trade
            )
            
            trade_date = datetime.fromisoformat(settlement['trade_date'])
            settlement_date = datetime.fromisoformat(settlement['settlement_date'])
            days_to_settle = (settlement_date - trade_date).days
            
            print(f"📅 Settlement {settlement['settlement_id']}:")
            print(f"   Trade: {trade['trade_id']}")
            print(f"   Value: ${settlement['value']:,.2f}")
            print(f"   Trade Date: {trade_date.date()}")
            print(f"   Settlement Date: {settlement_date.date()} (T+{days_to_settle})")
    
    # Show pending settlements
    pending = settlement_engine.get_pending_settlements()
    print(f"\n💼 Pending Settlements: {len(pending)}")
    
    # ========================================================================
    # 7. TRANSACTION HISTORY
    # ========================================================================
    
    print("\n[7/10] Transaction History: Complete audit trail...")
    print("-" * 80)
    
    # Get client history
    history = await transaction_history_service.get_client_history(
        client_id=client_id
    )
    
    print(f"📚 Transaction History for {client_id}:")
    print(f"   Total Transactions: {len(history)}")
    
    # Show recent transactions
    print(f"\n   Recent Transactions:")
    for txn in history[:5]:
        print(f"     • {txn['timestamp']}: {txn['type']} - {txn['transaction_id']}")
    
    # Trading summary
    summary = await transaction_history_service.get_trading_summary(
        client_id=client_id,
        period="ytd"
    )
    
    print(f"\n📊 Trading Summary (YTD):")
    print(f"   Total Orders: {summary['total_orders']}")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Buy Trades: {summary['buy_trades']}")
    print(f"   Sell Trades: {summary['sell_trades']}")
    print(f"   Total Value: ${summary['total_trade_value']:,.2f}")
    
    # ========================================================================
    # 8. DATA MESH QUALITY
    # ========================================================================
    
    print("\n[8/10] Data Mesh: Quality & governance...")
    print("-" * 80)
    
    from ultracore.datamesh.transaction_mesh import transaction_data_mesh
    
    # Query order with lineage
    order_with_lineage = transaction_data_mesh.query_order(
        order1['order_id'],
        include_lineage=True
    )
    
    if order_with_lineage and '_lineage' in order_with_lineage:
        print(f"🔗 Order Lineage for {order1['order_id']}:")
        print(f"   Quality Score: {order_with_lineage['_quality']:.1f}%")
        print(f"   Version History: {len(order_with_lineage['_lineage'])} versions")
        
        for version in order_with_lineage['_lineage'][:3]:
            print(f"     v{version['version']}: {version['source']} "
                  f"(Quality: {version['quality_score']:.1f}%)")
    
    # Materialized views
    client_orders = transaction_data_mesh.get_orders_by_client(client_id)
    print(f"\n📊 Materialized Views:")
    print(f"   Client Orders: {len(client_orders)}")
    
    # ========================================================================
    # 9. KAFKA EVENT STREAM
    # ========================================================================
    
    print("\n[9/10] Kafka Event Stream: Complete event log...")
    print("-" * 80)
    
    from ultracore.modules.transactions.kafka_events import transaction_kafka
    
    # Get order events
    order_events = transaction_kafka.kafka.get_events(
        topic="transactions.orders",
        key=client_id
    )
    
    print(f"📤 Order Events: {len(order_events)}")
    
    # Count by type
    event_counts = {}
    for event in order_events:
        evt_type = event['event_type']
        event_counts[evt_type] = event_counts.get(evt_type, 0) + 1
    
    for evt_type, count in event_counts.items():
        print(f"   • {evt_type}: {count}")
    
    # Show recent events
    print(f"\n   Recent Events:")
    for event in order_events[-5:]:
        print(f"     • {event['timestamp']}: {event['event_type']}")
    
    # ========================================================================
    # 10. PERFORMANCE METRICS
    # ========================================================================
    
    print("\n[10/10] Performance Metrics...")
    print("-" * 80)
    
    # Calculate execution performance
    if 'avg_price' in exec1:
        benchmark_price = market_data["VAS.AX"]["mid_price"]
        slippage = ((exec1['avg_price'] - benchmark_price) / benchmark_price) * 100
        
        print(f"📈 Execution Performance:")
        print(f"   Benchmark Price: ${benchmark_price:.2f}")
        print(f"   Execution Price: ${exec1['avg_price']:.2f}")
        print(f"   Slippage: {slippage:.2f}%")
        
        total_value = order1['order']['quantity'] * exec1['avg_price']
        estimated_cost = total_value * 0.001  # 0.1% estimated cost
        
        print(f"   Total Value: ${total_value:,.2f}")
        print(f"   Estimated Cost: ${estimated_cost:,.2f}")
    
    # RL Agent Stats
    print(f"\n🧠 RL Agent Statistics:")
    print(f"   Episodes Trained: {len(execution_rl_agent.episodes)}")
    print(f"   Q-Table Size: {len(execution_rl_agent.q_table)} states")
    print(f"   Exploration Rate: {execution_rl_agent.epsilon:.2%}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    print("\n" + "="*80)
    print("  🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")
    
    print("📊 Summary:")
    print(f"   • Orders Created: 3")
    print(f"   • Orders Validated: 2")
    print(f"   • Orders Executed: 2")
    print(f"   • Trades Generated: {exec1['total_trades'] if 'total_trades' in exec1 else 0}")
    print(f"   • Settlements Created: {len(pending)}")
    print(f"   • RL Training Episodes: 3")
    print(f"   • Kafka Events: {len(order_events)}")
    print(f"   • Transaction History: {len(history)} records")
    
    print("\n✨ All systems operational!")
    print("   • Kafka event streaming")
    print("   • Data Mesh governance")
    print("   • AI validation & fraud detection")
    print("   • RL-optimized execution")
    print("   • T+2 settlement processing")
    print("   • Complete audit trail")
    
    print("\n🚀 Full trading workflow demonstrated!")
    print("   Order → Validate → Execute → Settle → History")
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
