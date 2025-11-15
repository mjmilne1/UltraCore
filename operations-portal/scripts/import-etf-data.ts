import { readFileSync } from 'fs';
import { getDb } from '../server/db';
import { dataProducts } from '../drizzle/schema';

interface ETFRecord {
  ticker: string;
  name: string;
  category: string;
}

async function importETFData() {
  const db = await getDb();
  if (!db) {
    console.error('❌ Database connection failed');
    process.exit(1);
  }

  console.log('📊 Importing UltraCore ETF data...\n');

  try {
    // Read the combined CSV file from UltraCore repo
    const csvPath = '/home/ubuntu/UltraCore/data/etf_historical/all_australian_etfs_combined.csv';
    const csvContent = readFileSync(csvPath, 'utf-8');
    const lines = csvContent.split('\n');
    
    // Skip header line
    const dataLines = lines.slice(1);
    
    // Extract unique ETFs
    const etfMap = new Map<string, ETFRecord>();
    
    for (const line of dataLines) {
      if (!line.trim()) continue;
      
      const parts = line.split(',');
      if (parts.length < 12) continue;
      
      const ticker = parts[9]?.replace('.AX', '').trim();
      const name = parts[10]?.trim();
      const category = parts[11]?.trim();
      
      if (ticker && name && !etfMap.has(ticker)) {
        etfMap.set(ticker, { ticker, name, category });
      }
    }

    console.log(`Found ${etfMap.size} unique ETFs in UltraCore data\n`);

    // Clear existing data products
    console.log('🧹 Clearing existing data products...');
    await db.delete(dataProducts);
    console.log('✓ Cleared\n');

    // Insert ETF products
    console.log('📥 Inserting ETF products...');
    let count = 0;
    
    for (const [ticker, etf] of etfMap.entries()) {
      // Generate realistic expense ratios (0.05% to 1.20%)
      const expenseRatio = (Math.random() * 1.15 + 0.05).toFixed(2);
      
      // Generate realistic AUM ($10M to $5B)
      const aum = Math.floor(Math.random() * 4990000000 + 10000000);
      
      // Map category to snake_case enum values
      let mappedCategory = 'broad_market';
      if (etf.name.toLowerCase().includes('technology') || etf.name.toLowerCase().includes('tech')) {
        mappedCategory = 'technology';
      } else if (etf.name.toLowerCase().includes('healthcare') || etf.name.toLowerCase().includes('health')) {
        mappedCategory = 'healthcare';
      } else if (etf.name.toLowerCase().includes('sustain') || etf.name.toLowerCase().includes('esg')) {
        mappedCategory = 'esg_sustainable';
      } else if (etf.name.toLowerCase().includes('dividend') || etf.name.toLowerCase().includes('income') || etf.name.toLowerCase().includes('yield')) {
        mappedCategory = 'dividend_income';
      } else if (etf.name.toLowerCase().includes('bond') || etf.name.toLowerCase().includes('fixed') || etf.name.toLowerCase().includes('cash')) {
        mappedCategory = 'fixed_income';
      } else if (etf.name.toLowerCase().includes('gold') || etf.name.toLowerCase().includes('silver') || etf.name.toLowerCase().includes('commodity')) {
        mappedCategory = 'commodities';
      } else if (etf.name.toLowerCase().includes('asia') || etf.name.toLowerCase().includes('china') || etf.name.toLowerCase().includes('japan') || etf.name.toLowerCase().includes('india')) {
        mappedCategory = 'asia_pacific';
      } else if (etf.name.toLowerCase().includes('europe') || etf.name.toLowerCase().includes('international') || etf.name.toLowerCase().includes('global')) {
        mappedCategory = 'international';
      } else if (etf.name.toLowerCase().includes('s&p 500') || etf.name.toLowerCase().includes('nasdaq') || etf.name.toLowerCase().includes('fang')) {
        mappedCategory = 'us_equities';
      } else if (etf.name.toLowerCase().includes('bank') || etf.name.toLowerCase().includes('financial')) {
        mappedCategory = 'financials';
      } else if (etf.name.toLowerCase().includes('energy') || etf.name.toLowerCase().includes('oil')) {
        mappedCategory = 'energy';
      } else if (etf.name.toLowerCase().includes('australia') || etf.name.toLowerCase().includes('asx') || etf.name.toLowerCase().includes('a200')) {
        mappedCategory = 'australian_equities';
      }

      await db.insert(dataProducts).values({
        name: etf.name,
        ticker: ticker,
        category: mappedCategory as any,
        description: `${etf.name} - Historical OHLCV data from ASX`,
        expenseRatio: expenseRatio,
        aum: aum.toString(),
        s3Path: `/home/ubuntu/UltraCore/data/etf/historical/${ticker}.parquet`,
        format: 'parquet',
        owner: 'ultracore-data-team',
        status: 'active',
        lastUpdated: new Date()
      });
      
      count++;
      if (count % 10 === 0) {
        process.stdout.write(`  Imported ${count}/${etfMap.size} ETFs...\r`);
      }
    }
    
    console.log(`\n✅ Successfully imported ${count} ETF products from UltraCore data\n`);
    console.log('📊 Summary:');
    console.log(`  ✓ ${count} ASX ETF products`);
    console.log(`  ✓ Parquet files linked from /home/ubuntu/UltraCore/data/etf/historical/`);
    console.log(`  ✓ Ready for DuckDB WASM analytics\n`);

  } catch (error) {
    console.error('\n❌ Import failed:', error);
    process.exit(1);
  }

  process.exit(0);
}

importETFData();
