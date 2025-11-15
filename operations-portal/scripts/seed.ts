import { getDb } from '../server/db';
import { 
  portfolios, 
  portfolioHoldings, 
  esgData, 
  loans, 
  loanPayments,
  rlAgents,
  trainingRuns,
  kafkaTopics,
  dataProducts,
  mcpTools,
  mcpExecutions
} from '../drizzle/schema';

async function seed() {
  const db = await getDb();
  if (!db) {
    console.error('❌ Database connection failed');
    process.exit(1);
  }

  console.log('🌱 Starting database seeding...\n');

  try {
    // Clear all tables first
    console.log('🧹 Clearing existing data...');
    await db.delete(mcpExecutions);
    await db.delete(mcpTools);
    await db.delete(dataProducts);
    await db.delete(trainingRuns);
    await db.delete(loanPayments);
    await db.delete(loans);
    await db.delete(portfolioHoldings);
    await db.delete(portfolios);
    await db.delete(esgData);
    await db.delete(kafkaTopics);
    await db.delete(rlAgents);
    console.log('✓ Tables cleared\n');
    // 1. Seed RL Agents
    console.log('🤖 Seeding RL Agents (5)...');
    const agents = [
      {
        name: 'alpha' as const,
        displayName: 'Alpha Agent',
        objective: 'Aggressive growth strategy with high-risk tolerance focused on maximizing returns through momentum trading',
        modelVersion: 'v3.2',
        episodesTrained: 45230,
        avgReward: '142.5600'
      },
      {
        name: 'beta' as const,
        displayName: 'Beta Agent',
        objective: 'Balanced portfolio optimization with moderate risk and diversified asset allocation across sectors',
        modelVersion: 'v2.8',
        episodesTrained: 38910,
        avgReward: '98.3400'
      },
      {
        name: 'gamma' as const,
        displayName: 'Gamma Agent',
        objective: 'Conservative value investing with capital preservation and steady income generation from dividends',
        modelVersion: 'v4.1',
        episodesTrained: 52100,
        avgReward: '76.2300'
      },
      {
        name: 'delta' as const,
        displayName: 'Delta Agent',
        objective: 'Momentum trading with technical analysis identifying short-term profit opportunities in volatile markets',
        modelVersion: 'v3.5',
        episodesTrained: 41850,
        avgReward: '125.8900'
      },
      {
        name: 'epsilon' as const,
        displayName: 'Epsilon Agent',
        objective: 'ESG-focused sustainable investing prioritizing environmental and social impact alongside financial returns',
        modelVersion: 'v2.9',
        episodesTrained: 35670,
        avgReward: '89.4500'
      }
    ];

    for (const agent of agents) {
      await db.insert(rlAgents).values(agent);
    }

    // 2. Seed Portfolios (50)
    console.log('💼 Seeding Portfolios (50)...');
    const agentNames = ['alpha', 'beta', 'gamma', 'delta', 'epsilon'] as const;
    
    for (let i = 1; i <= 50; i++) {
      const agent = agentNames[i % 5];
      const initialInv = Math.random() * 2000000 + 500000; // $500K-$2.5M
      const returnPct = (Math.random() * 0.4 - 0.1); // -10% to +30%
      const currentValue = initialInv * (1 + returnPct);
      
      await db.insert(portfolios).values({
        id: `PF-${String(i).padStart(4, '0')}`,
        investorId: 1000 + i,
        investorName: `Investor ${String(i).padStart(3, '0')}`,
        agent,
        value: currentValue.toFixed(2),
        initialInvestment: initialInv.toFixed(2),
        return30d: (returnPct * 100).toFixed(4),
        return1y: ((returnPct * 1.2) * 100).toFixed(4),
        sharpeRatio: (Math.random() * 2 + 0.5).toFixed(4),
        volatility: (Math.random() * 0.4 + 0.05).toFixed(4),
        maxDrawdown: (Math.random() * -0.3).toFixed(4),
        status: i <= 42 ? 'active' : (i <= 47 ? 'paused' : 'closed')
      });
    }

    // 3. Seed Holdings (300)
    console.log('📈 Seeding Portfolio Holdings (300)...');
    const tickers = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ',
      'WMT', 'PG', 'UNH', 'HD', 'DIS', 'MA', 'PYPL', 'NFLX', 'ADBE', 'CRM'
    ];

    for (let i = 1; i <= 50; i++) {
      const portfolioId = `PF-${String(i).padStart(4, '0')}`;
      const numHoldings = Math.floor(Math.random() * 8) + 3; // 3-10 holdings
      
      for (let j = 0; j < numHoldings; j++) {
        const ticker = tickers[Math.floor(Math.random() * tickers.length)];
        const weight = Math.random() * 0.25 + 0.02; // 2%-27% weight
        const holdingValue = Math.random() * 200000 + 10000; // $10K-$210K
        
        await db.insert(portfolioHoldings).values({
          portfolioId,
          ticker,
          weight: weight.toFixed(6),
          value: holdingValue.toFixed(2)
        });
      }
    }

    // 4. Seed ESG Data (100)
    console.log('🌿 Seeding ESG Data (100)...');
    for (let i = 0; i < 100; i++) {
      const ticker = tickers[i % tickers.length];
      const uniqueTicker = `${ticker}${i >= tickers.length ? Math.floor(i / tickers.length) : ''}`;
      const esgScore = Math.floor(Math.random() * 40) + 60;
      
      await db.insert(esgData).values({
        ticker: uniqueTicker,
        name: `Company ${ticker} ${Math.floor(i / tickers.length) + 1}`,
        esgRating: esgScore >= 85 ? 'AAA' : esgScore >= 70 ? 'AA' : 'A',
        esgScore,
        environmentScore: Math.floor(Math.random() * 40) + 60,
        socialScore: Math.floor(Math.random() * 40) + 60,
        governanceScore: Math.floor(Math.random() * 40) + 60,
        carbonIntensity: (Math.random() * 500 + 50).toFixed(2),
        controversyScore: Math.floor(Math.random() * 5),
        provider: 'MSCI ESG Ratings'
      });
    }

    // 5. Seed Loans (80)
    console.log('💰 Seeding UltraGrow Loans (80)...');
    const loanStatuses = ['pending', 'active', 'paid', 'defaulted', 'liquidated'] as const;
    
    for (let i = 1; i <= 80; i++) {
      const loanAmt = Math.random() * 100000 + 10000;
      const portfolioVal = loanAmt * (Math.random() * 2 + 2);
      const ltv = loanAmt / portfolioVal;
      const termMonths = [12, 24, 36, 48, 60][Math.floor(Math.random() * 5)];
      const feeRate = Math.random() * 0.05 + 0.02; // 2-7%
      const monthlyPayment = (loanAmt * (1 + feeRate)) / termMonths;
      const monthsPaid = Math.floor(Math.random() * termMonths * 0.5);
      const remainingBalance = loanAmt * (1 + feeRate) - (monthlyPayment * monthsPaid);
      const status = i <= 48 ? 'active' : loanStatuses[Math.floor(Math.random() * loanStatuses.length)];
      const portfolioId = `PF-${String((i % 50) + 1).padStart(4, '0')}`;
      
      await db.insert(loans).values({
        id: `LOAN-${String(i).padStart(4, '0')}`,
        portfolioId,
        investorId: 1000 + (i % 50) + 1,
        amount: loanAmt.toFixed(2),
        portfolioValue: portfolioVal.toFixed(2),
        ltv: ltv.toFixed(4),
        termMonths,
        feeRate: feeRate.toFixed(4),
        monthlyPayment: monthlyPayment.toFixed(2),
        remainingBalance: remainingBalance.toFixed(2),
        status,
        approvedAt: status !== 'pending' ? new Date(Date.now() - Math.random() * 150 * 24 * 60 * 60 * 1000) : null
      });
    }

    // 6. Seed Loan Payments (400)
    console.log('💳 Seeding Loan Payments (400)...');
    for (let loanNum = 1; loanNum <= 48; loanNum++) {
      const loanId = `LOAN-${String(loanNum).padStart(4, '0')}`;
      const numPayments = Math.floor(Math.random() * 10) + 2;
      
      for (let i = 0; i < numPayments; i++) {
        const paymentAmt = Math.random() * 5000 + 500;
        const feeAmt = paymentAmt * 0.05;
        const principalAmt = paymentAmt - feeAmt;
        const dueDate = new Date(Date.now() - (numPayments - i) * 30 * 24 * 60 * 60 * 1000);
        const isPaid = Math.random() > 0.1;
        
        await db.insert(loanPayments).values({
          loanId,
          amount: paymentAmt.toFixed(2),
          principal: principalAmt.toFixed(2),
          fee: feeAmt.toFixed(2),
          dueDate,
          paidDate: isPaid ? new Date(dueDate.getTime() + Math.random() * 5 * 24 * 60 * 60 * 1000) : null,
          status: isPaid ? 'paid' : (Math.random() > 0.5 ? 'pending' : 'late')
        });
      }
    }

    // 7. Seed Training Runs (200)
    console.log('🎯 Seeding Agent Training Runs (200)...');
    for (const agentName of agentNames) {
      for (let i = 0; i < 40; i++) {
        const startTime = new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000);
        const duration = Math.floor(Math.random() * 7200) + 600; // 10min-2hr
        
        await db.insert(trainingRuns).values({
          agentName,
          episodes: Math.floor(Math.random() * 5000) + 1000,
          avgReward: (Math.random() * 200 - 50).toFixed(4),
          finalReward: (Math.random() * 250 - 25).toFixed(4),
          duration,
          status: Math.random() > 0.1 ? 'completed' : (Math.random() > 0.5 ? 'running' : 'failed'),
          startedAt: startTime,
          completedAt: Math.random() > 0.2 ? new Date(startTime.getTime() + duration * 1000) : null
        });
      }
    }

    // 8. Seed Kafka Topics (15)
    console.log('📡 Seeding Kafka Topics (15)...');
    const topics = [
      'portfolio.created', 'portfolio.updated', 'portfolio.rebalanced',
      'trade.executed', 'trade.cancelled', 'trade.settled',
      'loan.applied', 'loan.approved', 'loan.disbursed', 'loan.payment',
      'agent.training.started', 'agent.training.completed', 'agent.prediction',
      'esg.score.updated', 'compliance.alert'
    ];

    for (const topic of topics) {
      await db.insert(kafkaTopics).values({
        topicName: topic,
        partitions: Math.floor(Math.random() * 8) + 1,
        replicationFactor: 3,
        retentionMs: 604800000,
        config: JSON.stringify({ 'compression.type': 'snappy' })
      });
    }

    // 9. Seed Data Products (137 ASX ETFs)
    console.log('📊 Seeding Data Mesh Products (137)...');
    for (let i = 1; i <= 137; i++) {
      await db.insert(dataProducts).values({
        productName: `ASX ETF ${String(i).padStart(3, '0')}`,
        productType: 'parquet',
        description: `Australian Stock Exchange ETF data product #${i} with daily OHLCV data`,
        schema: JSON.stringify({
          fields: ['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        }),
        storageLocation: `s3://ultracore-data-mesh/asx-etf-${String(i).padStart(3, '0')}.parquet`,
        owner: 'data-team',
        status: 'active',
        version: `v1.${Math.floor(Math.random() * 10)}`
      });
    }

    // 10. Seed MCP Tools (24)
    console.log('🔧 Seeding MCP Tools (24)...');
    const tools = [
      'portfolio_analyzer', 'risk_calculator', 'esg_scorer', 'loan_evaluator',
      'market_data_fetcher', 'news_aggregator', 'sentiment_analyzer', 'price_predictor',
      'rebalance_optimizer', 'tax_calculator', 'compliance_checker', 'report_generator',
      'alert_manager', 'notification_sender', 'data_validator', 'schema_validator',
      'performance_tracker', 'benchmark_comparator', 'correlation_analyzer', 'volatility_calculator',
      'sharpe_ratio_calculator', 'drawdown_analyzer', 'liquidity_checker', 'exposure_analyzer'
    ];

    for (const toolName of tools) {
      await db.insert(mcpTools).values({
        toolName,
        description: `MCP tool for ${toolName.replace(/_/g, ' ')}`,
        version: `v${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 10)}`,
        status: 'active',
        endpoint: `https://mcp.ultracore.ai/tools/${toolName}`,
        config: JSON.stringify({ timeout: 30000, retries: 3 })
      });
    }

    console.log('\n✅ Database seeding completed successfully!');
    console.log('\n📊 Summary:');
    console.log(`  ✓ 5 RL Agents`);
    console.log(`  ✓ 50 Portfolios`);
    console.log(`  ✓ 300+ Holdings`);
    console.log(`  ✓ 100 ESG Data entries`);
    console.log(`  ✓ 80 Loans`);
    console.log(`  ✓ 400+ Loan Payments`);
    console.log(`  ✓ 200 Agent Training Runs`);
    console.log(`  ✓ 15 Kafka Topics`);
    console.log(`  ✓ 137 Data Mesh Products`);
    console.log(`  ✓ 24 MCP Tools`);
    console.log('\n🚀 Ready to explore the UltraCore Operations Portal!\n');

  } catch (error) {
    console.error('\n❌ Seeding failed:', error);
    process.exit(1);
  }

  process.exit(0);
}

seed();
