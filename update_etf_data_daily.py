#!/usr/bin/env python3
"""
Daily ETF Data Update Script

This script updates ETF data daily by downloading the latest prices
and appending them to existing historical data files.

Usage:
    python3 update_etf_data_daily.py

Can be scheduled with cron for automated daily updates.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add UltraCore to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ultracore.market_data.etf.asx_etf_list import get_all_etfs
from ultracore.market_data.etf.services.manus_yahoo_collector import ManusYahooFinanceCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etf_daily_update.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def update_etf_data():
    """Update ETF data with latest prices."""
    
    print("=" * 80)
    print("ASX ETF Daily Data Update")
    print("=" * 80)
    print(f"Update time: {datetime.now()}")
    print()
    
    # Get all ETF symbols
    all_etfs = get_all_etfs()
    print(f"Total ETFs to update: {len(all_etfs)}")
    print()
    
    # Initialize collector
    try:
        collector = ManusYahooFinanceCollector()
    except RuntimeError as e:
        logger.error(f"Failed to initialize collector: {e}")
        sys.exit(1)
    
    # Data directory
    data_dir = Path('data/etf/historical')
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.info("Run download_all_etfs.py first to create initial data")
        sys.exit(1)
    
    # Get date range for update (last 5 days to ensure we don't miss anything)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    print(f"Fetching data from {start_date} to {end_date}")
    print("-" * 80)
    
    results = {
        'updated': [],
        'created': [],
        'failed': [],
        'errors': {}
    }
    
    for i, symbol in enumerate(all_etfs, 1):
        print(f"\n[{i}/{len(all_etfs)}] Updating {symbol}...")
        
        try:
            # Check if file exists
            clean_symbol = symbol.replace('.AX', '')
            file_path = data_dir / f"{clean_symbol}.parquet"
            
            # Download latest data
            new_df = collector.collect_etf_data(symbol, start_date=start_date, end_date=end_date)
            
            if new_df is None or len(new_df) == 0:
                results['failed'].append(symbol)
                results['errors'][symbol] = "No new data returned"
                print(f"  ⚠️  No new data")
                continue
            
            if file_path.exists():
                # Load existing data
                existing_df = pd.read_parquet(file_path)
                
                # Combine and deduplicate
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df['Date'] = pd.to_datetime(combined_df['Date'])
                combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
                combined_df = combined_df.sort_values('Date')
                
                # Save updated data
                combined_df.to_parquet(file_path, index=False)
                
                new_rows = len(combined_df) - len(existing_df)
                results['updated'].append({
                    'symbol': symbol,
                    'new_rows': new_rows,
                    'total_rows': len(combined_df),
                    'latest_date': str(combined_df['Date'].max())
                })
                
                print(f"  ✅ Updated: +{new_rows} rows (total: {len(combined_df)})")
            else:
                # Create new file
                new_df.to_parquet(file_path, index=False)
                
                results['created'].append({
                    'symbol': symbol,
                    'rows': len(new_df),
                    'latest_date': str(new_df['Date'].max())
                })
                
                print(f"  ✨ Created: {len(new_df)} rows")
                
        except Exception as e:
            error_msg = str(e)
            results['failed'].append(symbol)
            results['errors'][symbol] = error_msg
            print(f"  ❌ Failed: {error_msg}")
            logger.error(f"Error updating {symbol}: {error_msg}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print(f"Total ETFs: {len(all_etfs)}")
    print(f"Updated: {len(results['updated'])}")
    print(f"Created: {len(results['created'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Success rate: {(len(results['updated']) + len(results['created']))/len(all_etfs)*100:.1f}%")
    print(f"End time: {datetime.now()}")
    
    if results['updated']:
        total_new_rows = sum(r['new_rows'] for r in results['updated'])
        print(f"\n✅ Updated {len(results['updated'])} ETFs with {total_new_rows} new data points")
    
    if results['created']:
        print(f"\n✨ Created {len(results['created'])} new ETF files")
    
    if results['failed']:
        print(f"\n❌ Failed to update {len(results['failed'])} ETFs:")
        for symbol in results['failed'][:10]:
            print(f"  - {symbol}: {results['errors'].get(symbol, 'Unknown error')}")
        if len(results['failed']) > 10:
            print(f"  ... and {len(results['failed']) - 10} more")
    
    # Save results to file
    import json
    results_file = f'etf_update_results_{datetime.now().strftime("%Y%m%d")}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Log file: etf_daily_update.log")
    
    return len(results['updated']) + len(results['created'])


if __name__ == '__main__':
    try:
        success_count = update_etf_data()
        sys.exit(0 if success_count > 0 else 1)
    except KeyboardInterrupt:
        print("\n\nUpdate interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
