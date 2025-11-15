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
  mcpTools
} from '../drizzle/schema';

async function seed() {
  const db = await getDb();
  if (!db) {
    console.error('Database connection failed');
    process.exit(1);
  }

  console.log('🌱 Starting database seeding...');

  try {
    // Seed RL Agents (5 agents)
    console.log('📊 Seeding RL Agents...');
    const agentIds = ['alpha', 'beta', 'gamma', 'delta', 'epsilon'] as const;
    const agentData = {
      alpha: {
        displayName: 'Alpha Agent',
        objective: 'Aggressive growth strategy with high-risk tolerance focused on maximizing returns'
      },
      beta: {
        displayName: 'Beta Agent',
        objective: 'Balanced portfolio optimization with moderate risk and diversified asset allocation'
      },
      gamma: {
        displayName: 'Gamma Agent',
        objective: 'Conservative value investing with capital preservation and steady income generation'
      },
      delta: {
        displayName: 'Delta Agent',
        objective: 'Momentum trading with technical analysis and short-term profit opportunities'
      },
      epsilon: {
        displayName: 'Epsilon Agent',
        objective: 'ESG-focused sustainable investing prioritizing environmental and social impact'
      }
    };

    for (const agentId of agentIds) {
      await db.insert(rlAgents).values({
        name: agentId,
        displayName: agentData[agentId].displayName,
        objective: agentData[agentId].objective,
        modelVersion: `v${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}`,
        status: 'deployed',
        episodesTrained: Math.floor(Math.random() * 100000) + 10000,
        avgReward: (Math.random() * 200 + 50).toFixed(4)
      });
    }

    // Seed Portfolios (50 portfolios)
    console.log('💼 Seeding Portfolios...');
    const portfolioIds: number[] = [];
    const riskLevels = ['low', 'medium', 'high'] as const;
    const statuses = ['active', 'inactive', 'archived'] as const;

    for (let i = 1; i <= 50; i++) {
      const agentId = agentIds[Math.floor(Math.random() * agentIds.length)];
      const riskLevel = riskLevels[Math.floor(Math.random() * riskLevels.length)];
      const status = i <= 42 ? 'active' : statuses[Math.floor(Math.random() * statuses.length)];
      const totalValue = Math.random() * 5000000 + 500000; // $500K - $5.5M
      const returnRate = (Math.random() * 40 - 10).toFixed(2); // -10% to +30%

      const result = await db.insert(portfolios).values({
        name: `Portfolio ${String(i).padStart(3, '0')}`,
        description: `Managed by ${agentNames[agentId as keyof typeof agentNames]} - ${riskLevel} risk strategy`,
        agentId,
        status,
        totalValue: totalValue.toFixed(2),
        returnRate,
        riskLevel,
        rebalanceFrequency: ['daily', 'weekly', 'monthly'][Math.floor(Math.random() * 3)]
      });
      
      portfolioIds.push(result.insertId as unknown as number);
    }

    // Seed Holdings (500+ holdings across portfolios)
    console.log('📈 Seeding Holdings...');
    const tickers = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ',
      'WMT', 'PG', 'UNH', 'HD', 'DIS', 'MA', 'PYPL', 'NFLX', 'ADBE', 'CRM',
      'VZ', 'T', 'CSCO', 'PFE', 'KO', 'PEP', 'MRK', 'ABT', 'TMO', 'COST'
    ];

    for (const portfolioId of portfolioIds) {
      const numHoldings = Math.floor(Math.random() * 15) + 5; // 5-20 holdings per portfolio
      for (let i = 0; i < numHoldings; i++) {
        const ticker = tickers[Math.floor(Math.random() * tickers.length)];
        const quantity = Math.floor(Math.random() * 1000) + 10;
        const purchasePrice = Math.random() * 500 + 50;
        const currentPrice = purchasePrice * (1 + (Math.random() * 0.4 - 0.1));

        await db.insert(portfolioHoldings).values({
          portfolioId,
          ticker,
          quantity,
          purchasePrice: purchasePrice.toFixed(2),
          currentPrice: currentPrice.toFixed(2),
          purchaseDate: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
        });
      }
    }

    // Seed ESG Data (100 companies)
    console.log('🌿 Seeding ESG Data...');
    for (let i = 0; i < 100; i++) {
      const ticker = tickers[i % tickers.length];
      await db.insert(esgData).values({
        companyName: `Company ${ticker}`,
        ticker,
        environmentalScore: Math.floor(Math.random() * 40) + 60,
        socialScore: Math.floor(Math.random() * 40) + 60,
        governanceScore: Math.floor(Math.random() * 40) + 60,
        overallScore: Math.floor(Math.random() * 40) + 60,
        reportingYear: 2024,
        dataSource: 'MSCI ESG Ratings'
      });
    }

    // Seed Loans (80 loans)
    console.log('💰 Seeding UltraGrow Loans...');
    const loanIds: number[] = [];
    const loanStatuses = ['pending', 'approved', 'active', 'completed', 'defaulted'] as const;

    for (let i = 1; i <= 80; i++) {
      const loanAmount = Math.random() * 100000 + 10000; // $10K - $110K
      const portfolioValue = loanAmount * (Math.random() * 2 + 2); // 2x-4x LTV
      const ltv = (loanAmount / portfolioValue * 100).toFixed(2);
      const status = i <= 48 ? 'active' : loanStatuses[Math.floor(Math.random() * loanStatuses.length)];

      const result = await db.insert(loans).values({
        borrowerName: `Borrower ${String(i).padStart(3, '0')}`,
        loanAmount: loanAmount.toFixed(2),
        interestRate: (Math.random() * 5 + 3).toFixed(2), // 3-8%
        term: [12, 24, 36, 48, 60][Math.floor(Math.random() * 5)],
        status,
        portfolioValue: portfolioValue.toFixed(2),
        ltv,
        applicationDate: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000),
        approvalDate: status !== 'pending' ? new Date(Date.now() - Math.random() * 150 * 24 * 60 * 60 * 1000) : null
      });

      loanIds.push(result.insertId as unknown as number);
    }

    // Seed Loan Payments (500+ payments)
    console.log('💳 Seeding Loan Payments...');
    for (const loanId of loanIds.slice(0, 48)) { // Only for active loans
      const numPayments = Math.floor(Math.random() * 12) + 1;
      for (let i = 0; i < numPayments; i++) {
        await db.insert(loanPayments).values({
          loanId,
          amount: (Math.random() * 5000 + 500).toFixed(2),
          paymentDate: new Date(Date.now() - (numPayments - i) * 30 * 24 * 60 * 60 * 1000),
          status: Math.random() > 0.1 ? 'completed' : 'pending'
        });
      }
    }

    // Seed Agent Training Runs (200 runs)
    console.log('🤖 Seeding Agent Training Runs...');
    for (const agentId of agentIds) {
      for (let i = 0; i < 40; i++) {
        await db.insert(trainingRuns).values({
          agentId,
          startTime: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000),
          endTime: new Date(Date.now() - Math.random() * 89 * 24 * 60 * 60 * 1000),
          episodesCompleted: Math.floor(Math.random() * 10000) + 1000,
          avgReward: (Math.random() * 200 - 50).toFixed(2),
          status: ['completed', 'running', 'failed'][Math.floor(Math.random() * 3)],
          metrics: JSON.stringify({
            loss: Math.random() * 0.5,
            accuracy: Math.random() * 0.3 + 0.7
          })
        });
      }
    }

    // Seed Kafka Topics (15 topics)
    console.log('📡 Seeding Kafka Topics...');
    const topics = [
      'portfolio.created', 'portfolio.updated', 'portfolio.rebalanced',
      'trade.executed', 'trade.cancelled', 'trade.settled',
      'loan.applied', 'loan.approved', 'loan.disbursed', 'loan.payment',
      'agent.training.started', 'agent.training.completed', 'agent.prediction',
      'esg.score.updated', 'compliance.alert'
    ];

    const topicIds: number[] = [];
    for (const topic of topics) {
      const result = await db.insert(kafkaTopics).values({
        topicName: topic,
        partitions: Math.floor(Math.random() * 8) + 1,
        replicationFactor: 3,
        retentionMs: 604800000, // 7 days
        config: JSON.stringify({ 'compression.type': 'snappy' })
      });
      topicIds.push(result.insertId as unknown as number);
    }

    // Note: Kafka events are handled by real-time Kafka integration, not stored in DB
    console.log('⚡ Skipping Kafka Events (handled by Kafka broker)...');

    // Seed Data Mesh Products (137 ASX ETF products)
    console.log('📊 Seeding Data Mesh Products...');
    for (let i = 1; i <= 137; i++) {
      await db.insert(dataProducts).values({
        productName: `ASX ETF ${String(i).padStart(3, '0')}`,
        productType: 'parquet',
        description: `Australian Stock Exchange ETF data product #${i}`,
        schema: JSON.stringify({
          fields: ['date', 'open', 'high', 'low', 'close', 'volume']
        }),
        storageLocation: `s3://ultracore-data-mesh/asx-etf-${String(i).padStart(3, '0')}.parquet`,
        owner: 'data-team',
        status: 'active',
        version: `v1.${Math.floor(Math.random() * 10)}`
      });
    }

    // Seed MCP Tools (24 tools)
    console.log('🔧 Seeding MCP Tools...');
    const toolNames = [
      'portfolio_analyzer', 'risk_calculator', 'esg_scorer', 'loan_evaluator',
      'market_data_fetcher', 'news_aggregator', 'sentiment_analyzer', 'price_predictor',
      'rebalance_optimizer', 'tax_calculator', 'compliance_checker', 'report_generator',
      'alert_manager', 'notification_sender', 'data_validator', 'schema_validator',
      'performance_tracker', 'benchmark_comparator', 'correlation_analyzer', 'volatility_calculator',
      'sharpe_ratio_calculator', 'drawdown_analyzer', 'liquidity_checker', 'exposure_analyzer'
    ];

    for (const toolName of toolNames) {
      await db.insert(mcpTools).values({
        toolName,
        description: `MCP tool for ${toolName.replace(/_/g, ' ')}`,
        version: `v${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 10)}`,
        status: 'active',
        endpoint: `https://mcp.ultracore.ai/tools/${toolName}`,
        config: JSON.stringify({
          timeout: 30000,
          retries: 3
        })
      });
    }

    console.log('✅ Database seeding completed successfully!');
    console.log('\n📊 Summary:');
    console.log(`  - 5 RL Agents`);
    console.log(`  - 50 Portfolios`);
    console.log(`  - 500+ Holdings`);
    console.log(`  - 100 ESG Data entries`);
    console.log(`  - 80 Loans`);
    console.log(`  - 500+ Loan Payments`);
    console.log(`  - 200 Agent Training Runs`);
    console.log(`  - 15 Kafka Topics`);

    console.log(`  - 137 Data Mesh Products`);
    console.log(`  - 24 MCP Tools`);

  } catch (error) {
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  }

  process.exit(0);
}

seed();
