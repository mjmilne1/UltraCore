#!/usr/bin/env python3
"""
Download Historical Data for All ASX ETFs

This script uses the Manus Yahoo Finance collector to download complete
historical data for all ASX-listed ETFs and save them to Parquet format.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add UltraCore to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ultracore.market_data.etf.asx_etf_list import get_all_etfs
from ultracore.market_data.etf.services.manus_yahoo_collector import ManusYahooFinanceCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etf_download.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Download all ASX ETF historical data."""
    
    print("=" * 80)
    print("ASX ETF Historical Data Download")
    print("=" * 80)
    print(f"Start time: {datetime.now()}")
    print()
    
    # Get all ETF symbols
    all_etfs = get_all_etfs()
    print(f"Total ETFs to download: {len(all_etfs)}")
    print()
    
    # Initialize collector
    try:
        collector = ManusYahooFinanceCollector()
    except RuntimeError as e:
        logger.error(f"Failed to initialize collector: {e}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path('data/etf/historical')
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # Download data for all ETFs
    print("Starting download...")
    print("-" * 80)
    
    results = {
        'success': [],
        'failed': [],
        'errors': {}
    }
    
    for i, symbol in enumerate(all_etfs, 1):
        print(f"\n[{i}/{len(all_etfs)}] Processing {symbol}...")
        
        try:
            # Download data
            df = collector.collect_etf_data(symbol)
            
            if df is not None and len(df) > 0:
                # Save to Parquet
                output_file = collector.save_to_parquet(df, symbol, output_dir)
                
                results['success'].append({
                    'symbol': symbol,
                    'rows': len(df),
                    'start_date': str(df['Date'].min()),
                    'end_date': str(df['Date'].max()),
                    'file': str(output_file)
                })
                
                print(f"  ✅ Success: {len(df)} rows ({df['Date'].min().date()} to {df['Date'].max().date()})")
            else:
                results['failed'].append(symbol)
                results['errors'][symbol] = "No data returned"
                print(f"  ❌ Failed: No data returned")
                
        except Exception as e:
            error_msg = str(e)
            results['failed'].append(symbol)
            results['errors'][symbol] = error_msg
            print(f"  ❌ Failed: {error_msg}")
            logger.error(f"Error processing {symbol}: {error_msg}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"Total ETFs: {len(all_etfs)}")
    print(f"Successful: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Success rate: {len(results['success'])/len(all_etfs)*100:.1f}%")
    print(f"End time: {datetime.now()}")
    
    if results['success']:
        print("\n✅ Successfully downloaded ETFs:")
        total_rows = sum(r['rows'] for r in results['success'])
        print(f"  Total data points: {total_rows:,}")
        
        # Show some examples
        print("\n  Sample ETFs:")
        for etf in results['success'][:10]:
            print(f"    {etf['symbol']}: {etf['rows']} rows ({etf['start_date'][:10]} to {etf['end_date'][:10]})")
        
        if len(results['success']) > 10:
            print(f"    ... and {len(results['success']) - 10} more")
    
    if results['failed']:
        print(f"\n❌ Failed ETFs ({len(results['failed'])}):")
        for symbol in results['failed'][:20]:
            print(f"  - {symbol}: {results['errors'].get(symbol, 'Unknown error')}")
        
        if len(results['failed']) > 20:
            print(f"  ... and {len(results['failed']) - 20} more")
    
    # Save results to file
    import json
    results_file = 'etf_download_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Log file: etf_download.log")
    
    return len(results['success'])


if __name__ == '__main__':
    try:
        success_count = main()
        sys.exit(0 if success_count > 0 else 1)
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
