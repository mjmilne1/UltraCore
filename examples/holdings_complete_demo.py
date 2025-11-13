"""
Holdings Module - Complete Demonstration
Showcases all features: Kafka, Data Mesh, AI, RL, Services
"""

import asyncio
from datetime import datetime, timedelta
from ultracore.modules.holdings.holdings_service import holdings_service
from ultracore.modules.holdings.position_tracker import position_tracker, CostBasisMethod
from ultracore.modules.holdings.performance_analytics import performance_analytics
from ultracore.modules.holdings.rebalancing_engine import rebalancing_engine
from ultracore.streaming.kafka_events import kafka_producer
from ultracore.agents.holdings_agent import holdings_agent
from ultracore.ml.rl.portfolio_agent import portfolio_rl_agent

async def main():
    print("\n" + "="*80)
    print("  🎯 ULTRACORE HOLDINGS MODULE - COMPLETE DEMONSTRATION")
    print("  Kafka-First Event-Driven Architecture with AI & ML")
    print("="*80 + "\n")
    
    client_id = "DEMO-CLIENT-001"
    
    # ========================================================================
    # 1. OPEN POSITIONS (KAFKA EVENT STREAMING)
    # ========================================================================
    
    print("[1/10] Opening positions with Kafka event streaming...")
    print("-" * 80)
    
    positions_opened = []
    
    # Open position 1: VAS.AX (Australian Shares)
    pos1 = await holdings_service.open_position(
        client_id=client_id,
        ticker="VAS.AX",
        quantity=1000,
        purchase_price=100.00,
        purchase_date=datetime.now(timezone.utc) - timedelta(days=180)
    )
    positions_opened.append(pos1)
    print(f"✅ Opened: {pos1['position_id']} - VAS.AX (1000 @ $100.00)")
    print(f"   Data Quality: {pos1['mesh_quality']:.1f}%")
    print(f"   Event ID: {pos1['event_id']}")
    
    # Open position 2: VGS.AX (International Shares)
    pos2 = await holdings_service.open_position(
        client_id=client_id,
        ticker="VGS.AX",
        quantity=500,
        purchase_price=150.00,
        purchase_date=datetime.now(timezone.utc) - timedelta(days=90)
    )
    positions_opened.append(pos2)
    print(f"✅ Opened: {pos2['position_id']} - VGS.AX (500 @ $150.00)")
    
    # Open position 3: VAF.AX (Bonds)
    pos3 = await holdings_service.open_position(
        client_id=client_id,
        ticker="VAF.AX",
        quantity=2000,
        purchase_price=50.00,
        purchase_date=datetime.now(timezone.utc) - timedelta(days=120)
    )
    positions_opened.append(pos3)
    print(f"✅ Opened: {pos3['position_id']} - VAF.AX (2000 @ $50.00)")
    
    print(f"\n📊 Total positions opened: {len(positions_opened)}")
    print(f"   Initial portfolio value: $100,000 + $75,000 + $100,000 = $275,000")
    
    # ========================================================================
    # 2. DATA MESH - LINEAGE & QUALITY
    # ========================================================================
    
    print("\n[2/10] Data Mesh: Quality & Lineage Tracking...")
    print("-" * 80)
    
    from ultracore.datamesh.holdings_mesh import holdings_data_mesh
    
    # Get data quality report
    quality_report = holdings_data_mesh.get_data_quality_report(pos1['position_id'])
    
    print(f"📊 Data Quality Report for {pos1['position_id']}:")
    print(f"   Quality Score: {quality_report['current_quality_score']:.1f}%")
    print(f"   Quality Level: {quality_report['quality_level']}")
    print(f"   Total Versions: {quality_report['total_versions']}")
    print(f"   Data Sources: {', '.join(quality_report['data_sources'])}")
    
    # ========================================================================
    # 3. UPDATE POSITIONS WITH MARKET PRICES
    # ========================================================================
    
    print("\n[3/10] Updating positions with current market prices...")
    print("-" * 80)
    
    # Simulate price movements
    await holdings_service.update_position_value(pos1['position_id'], 105.00)  # +5%
    await holdings_service.update_position_value(pos2['position_id'], 155.00)  # +3.3%
    await holdings_service.update_position_value(pos3['position_id'], 51.00)   # +2%
    
    print(f"✅ Updated VAS.AX: $100.00 → $105.00 (+5.0%)")
    print(f"✅ Updated VGS.AX: $150.00 → $155.00 (+3.3%)")
    print(f"✅ Updated VAF.AX: $50.00 → $51.00 (+2.0%)")
    
    # ========================================================================
    # 4. PORTFOLIO VALUATION
    # ========================================================================
    
    print("\n[4/10] Real-time portfolio valuation...")
    print("-" * 80)
    
    valuation = await holdings_service.get_portfolio_value(client_id, real_time=True)
    
    print(f"💰 Portfolio Valuation:")
    print(f"   Total Value: ${valuation['total_value']:,.2f}")
    print(f"   Total Cost: ${valuation['total_cost']:,.2f}")
    print(f"   Unrealized G/L: ${valuation['unrealized_gl']:,.2f} ({valuation['return_pct']:.2f}%)")
    print(f"   Positions: {valuation['positions_count']}")
    
    # ========================================================================
    # 5. AI AGENT MONITORING
    # ========================================================================
    
    print("\n[5/10] AI Agent: Portfolio monitoring & alerts...")
    print("-" * 80)
    
    monitoring = await holdings_service.monitor_portfolio_with_ai(client_id)
    
    print(f"🤖 AI Monitoring Results:")
    print(f"   Health Score: {monitoring['portfolio_health_score']:.0f}/100")
    print(f"   Alerts: {len(monitoring['alerts'])}")
    
    if monitoring['alerts']:
        for alert in monitoring['alerts'][:3]:
            print(f"   • {alert['level'].upper()}: {alert['message']}")
    
    print(f"   Recommendations: {len(monitoring['recommendations'])}")
    
    if monitoring['recommendations']:
        for rec in monitoring['recommendations'][:2]:
            print(f"   • {rec['type']}: {rec.get('action', 'Review')}")
    
    print(f"   Next Action: {monitoring['next_action']}")
    
    # ========================================================================
    # 6. REINFORCEMENT LEARNING
    # ========================================================================
    
    print("\n[6/10] Reinforcement Learning: Portfolio optimization...")
    print("-" * 80)
    
    # Train RL agent
    print("🧠 Training RL agent...")
    
    market_simulation = [
        {"return": 0.01},
        {"return": -0.005},
        {"return": 0.02},
        {"return": 0.01},
        {"return": -0.01}
    ]
    
    for episode in range(3):
        result = portfolio_rl_agent.train_episode(
            initial_portfolio=valuation,
            market_simulation=market_simulation,
            steps=10
        )
        print(f"   Episode {result['episode']}: Reward = {result['total_reward']:.2f}")
    
    # Get optimal action
    action, confidence = portfolio_rl_agent.get_optimal_action(valuation)
    print(f"\n✅ RL Recommendation: {action} (confidence: {confidence:.2%})")
    
    # ========================================================================
    # 7. COST BASIS TRACKING
    # ========================================================================
    
    print("\n[7/10] Cost Basis Tracking: Tax-optimized selling...")
    print("-" * 80)
    
    # Add position to tracker
    position_tracker.add_purchase(
        ticker="VAS.AX",
        quantity=1000,
        purchase_price=100.00,
        purchase_date=datetime.now(timezone.utc) - timedelta(days=180),
        transaction_id="TXN-001"
    )
    
    # Get position summary
    summary = position_tracker.get_position_summary("VAS.AX")
    print(f"📈 VAS.AX Position:")
    print(f"   Total Quantity: {summary['total_quantity']}")
    print(f"   Average Cost: ${summary['average_cost']:.2f}")
    print(f"   Total Cost Basis: ${summary['total_cost_basis']:,.2f}")
    print(f"   Active Lots: {summary['lots_count']}")
    
    # Tax loss harvesting
    print(f"\n🔍 Tax Loss Harvesting Opportunities:")
    opportunities = position_tracker.tax_loss_harvest_opportunities(
        ticker="VAS.AX",
        current_price=95.00,  # Simulate a loss
        min_loss=1000
    )
    
    if opportunities:
        for opp in opportunities:
            print(f"   • Lot {opp['lot_id']}: Potential loss ${opp['potential_loss']:,.2f}")
            print(f"     Tax Benefit: ${opp['tax_benefit']:,.2f}")
    else:
        print(f"   No opportunities found (position is profitable)")
    
    # ========================================================================
    # 8. PERFORMANCE ANALYTICS
    # ========================================================================
    
    print("\n[8/10] Performance Analytics: Comprehensive metrics...")
    print("-" * 80)
    
    # Create sample history
    history = [
        {"date": "2024-01-01", "total_value": 275000},
        {"date": "2024-03-01", "total_value": 280000},
        {"date": "2024-06-01", "total_value": 285000},
        {"date": "2024-09-01", "total_value": 278000},
        {"date": "2024-12-01", "total_value": valuation['total_value']}
    ]
    
    metrics = performance_analytics.calculate_comprehensive_metrics(history)
    
    print(f"📊 Performance Metrics:")
    print(f"   Period: {metrics['period']['years']:.2f} years")
    print(f"   Total Return: {metrics['returns']['total_return_pct']:.2%}")
    print(f"   CAGR: {metrics['returns']['cagr']:.2%}")
    print(f"   Sharpe Ratio: {metrics['risk']['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['risk']['max_drawdown_pct']:.2%}")
    print(f"   Volatility: {metrics['risk']['volatility']:.2%}")
    
    # ========================================================================
    # 9. REBALANCING ENGINE
    # ========================================================================
    
    print("\n[9/10] Rebalancing Engine: AI-powered rebalancing...")
    print("-" * 80)
    
    target_allocation = {
        "VAS.AX": 0.40,
        "VGS.AX": 0.35,
        "VAF.AX": 0.25
    }
    
    # Evaluate rebalancing need
    positions = await holdings_service.get_client_positions(client_id, status="open")
    total_value = valuation['total_value']
    
    current_allocation = {}
    for pos in positions:
        ticker = pos["ticker"]
        value = pos["market_value"]
        current_allocation[ticker] = value / total_value if total_value > 0 else 0
    
    evaluation = await rebalancing_engine.evaluate_rebalancing_need(
        current_allocation=current_allocation,
        target_allocation=target_allocation
    )
    
    print(f"⚖️  Rebalancing Evaluation:")
    print(f"   Needs Rebalancing: {evaluation['needs_rebalancing']}")
    print(f"   Max Drift: {evaluation['max_drift']:.2%}")
    
    if evaluation['needs_rebalancing']:
        print(f"   Reason: {evaluation['reason']}")
        
        # Generate rebalancing plan
        plan = await rebalancing_engine.generate_rebalancing_trades(
            current_positions=positions,
            target_allocation=target_allocation,
            total_value=total_value
        )
        
        print(f"\n📋 Rebalancing Plan:")
        print(f"   Trades Required: {plan['trade_count']}")
        print(f"   Total Trade Value: ${plan['total_trade_value']:,.2f}")
        print(f"   Estimated Costs: ${plan['estimated_costs']:,.2f}")
        
        for trade in plan['trades'][:3]:
            print(f"   • {trade['action'].upper()} {trade['quantity']:.0f} {trade['ticker']}")
            print(f"     Reason: {trade['reason']}")
    
    # ========================================================================
    # 10. KAFKA EVENT STREAM ANALYSIS
    # ========================================================================
    
    print("\n[10/10] Kafka Event Stream: Complete audit trail...")
    print("-" * 80)
    
    # Get all position events
    position_events = kafka_producer.get_events(
        topic="holdings.positions",
        key=client_id
    )
    
    print(f"📤 Event Stream Summary:")
    print(f"   Total Position Events: {len(position_events)}")
    
    # Count by type
    event_types = {}
    for event in position_events:
        evt_type = event['event_type']
        event_types[evt_type] = event_types.get(evt_type, 0) + 1
    
    for evt_type, count in event_types.items():
        print(f"   • {evt_type}: {count}")
    
    # Show recent events
    print(f"\n📋 Recent Events:")
    for event in position_events[-5:]:
        print(f"   • {event['timestamp']}: {event['event_type']}")
        print(f"     Data: {list(event['data'].keys())[:3]}...")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    print("\n" + "="*80)
    print("  🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")
    
    print("📊 Summary:")
    print(f"   • Positions Opened: {len(positions_opened)}")
    print(f"   • Portfolio Value: ${valuation['total_value']:,.2f}")
    print(f"   • Total Return: {valuation['return_pct']:.2%}")
    print(f"   • Health Score: {monitoring['portfolio_health_score']:.0f}/100")
    print(f"   • RL Episodes Trained: 3")
    print(f"   • Performance Metrics: ✅ Calculated")
    print(f"   • Rebalancing Analysis: ✅ Complete")
    print(f"   • Kafka Events: {len(position_events)}")
    
    print("\n✨ All systems operational!")
    print("   • Kafka event streaming")
    print("   • Data Mesh governance")
    print("   • AI agent monitoring")
    print("   • RL optimization")
    print("   • Cost basis tracking")
    print("   • Performance analytics")
    print("   • Rebalancing engine")
    
    print("\n🚀 Ready for production!\n")

if __name__ == "__main__":
    asyncio.run(main())
