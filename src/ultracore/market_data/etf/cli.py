#!/usr/bin/env python3
"""
ETF Data System CLI
Command-line interface for managing ETF data collection and updates
"""
import asyncio
import click
import logging
from pathlib import Path
from datetime import datetime

from ultracore.market_data.etf.etf_data_system import ETFDataSystem, get_etf_system
from ultracore.market_data.etf.asx_etf_list import get_all_etfs, get_etfs_by_category


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """ETF Data System - Manage ASX ETF historical data"""
    pass


@cli.command()
@click.option('--data-dir', default='/data/etf', help='Data directory path')
@click.option('--api-key', envvar='ALPHA_VANTAGE_API_KEY', required=True, help='Alpha Vantage API key')
@click.option('--force', is_flag=True, help='Force re-initialization')
def initialize(data_dir: str, api_key: str, force: bool):
    """Initialize ETF data system with complete historical data"""
    click.echo("🚀 Initializing ETF Data System...")
    click.echo(f"📁 Data directory: {data_dir}")
    click.echo(f"📊 ETFs to collect: {len(get_all_etfs())}")
    
    if force:
        click.echo("⚠️  Force mode: Will re-download all data")
    
    async def run():
        system = ETFDataSystem(data_dir=data_dir, alpha_vantage_api_key=api_key)
        result = await system.initialize(force=force)
        return result
    
    result = asyncio.run(run())
    
    click.echo("\n✅ Initialization Complete!")
    click.echo(f"   Total ETFs: {result['total_etfs']}")
    click.echo(f"   Successful: {result['successful']}")
    click.echo(f"   Failed: {result['failed']}")
    click.echo(f"   Data points: {result['total_data_points']:,}")
    click.echo(f"   Duration: {result['duration_seconds']:.1f}s")
    click.echo(f"   Parquet files: {result['parquet_files_created']}")
    
    if result['failed'] > 0:
        click.echo(f"\n⚠️  Failed tickers: {', '.join(result['failed_tickers'][:10])}")


@cli.command()
@click.option('--data-dir', default='/data/etf', help='Data directory path')
@click.option('--api-key', envvar='ALPHA_VANTAGE_API_KEY', required=True, help='Alpha Vantage API key')
def update(data_dir: str, api_key: str):
    """Update ETF data with latest prices"""
    click.echo("🔄 Updating ETF data...")
    
    async def run():
        system = ETFDataSystem(data_dir=data_dir, alpha_vantage_api_key=api_key)
        result = await system.update()
        return result
    
    result = asyncio.run(run())
    
    click.echo("\n✅ Update Complete!")
    click.echo(f"   Total ETFs: {result['total_etfs']}")
    click.echo(f"   Successful: {result['successful']}")
    click.echo(f"   Failed: {result['failed']}")
    click.echo(f"   Duration: {result['duration_seconds']:.1f}s")


@cli.command()
@click.option('--data-dir', default='/data/etf', help='Data directory path')
@click.option('--time', default='18:00', help='Update time (HH:MM)')
def scheduler(data_dir: str, time: str):
    """Run continuous scheduler for daily updates"""
    from datetime import time as dt_time
    
    hour, minute = map(int, time.split(':'))
    update_time = dt_time(hour, minute)
    
    click.echo(f"⏰ Starting ETF Data Scheduler")
    click.echo(f"   Data directory: {data_dir}")
    click.echo(f"   Update time: {time}")
    click.echo(f"   Press Ctrl+C to stop\n")
    
    async def run():
        system = ETFDataSystem(data_dir=data_dir)
        system.update_time = update_time
        await system.run_scheduler()
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        click.echo("\n\n👋 Scheduler stopped")


@cli.command()
@click.option('--data-dir', default='/data/etf', help='Data directory path')
def status(data_dir: str):
    """Show system status"""
    system = ETFDataSystem(data_dir=data_dir)
    status = system.get_system_status()
    
    click.echo("📊 ETF Data System Status\n")
    click.echo(f"Initialized: {'✅ Yes' if status['initialized'] else '❌ No'}")
    click.echo(f"Last Update: {status['last_update'] or 'Never'}")
    click.echo(f"Next Update: {status['next_update_time']}")
    click.echo(f"Data Directory: {status['data_directory']}")
    
    if 'agent_statistics' in status:
        stats = status['agent_statistics']
        click.echo(f"\n📈 Agent Statistics:")
        click.echo(f"   Total ETFs: {stats['total_etfs']}")
        click.echo(f"   Successful: {stats['successful_collections']}")
        click.echo(f"   Failed: {stats['failed_collections']}")
        click.echo(f"   Success Rate: {stats['success_rate']:.1f}%")
    
    if 'data_product_statistics' in status:
        stats = status['data_product_statistics']
        click.echo(f"\n💾 Data Product Statistics:")
        click.echo(f"   Total ETFs: {stats['total_etfs']}")
        click.echo(f"   Data Points: {stats['total_data_points']:,}")
        click.echo(f"   Avg per ETF: {stats['average_data_points_per_etf']:.0f}")
        click.echo(f"   Date Range: {stats['earliest_date']} to {stats['latest_date']}")


@cli.command()
@click.argument('ticker')
@click.option('--data-dir', default='/data/etf', help='Data directory path')
def show(ticker: str, data_dir: str):
    """Show data for a specific ETF"""
    system = ETFDataSystem(data_dir=data_dir)
    
    etf = system.get_etf_data(ticker, format='aggregate')
    
    if not etf:
        click.echo(f"❌ ETF {ticker} not found")
        return
    
    click.echo(f"\n📊 {ticker} - {etf.metadata.name if etf.metadata else 'Unknown'}\n")
    
    if etf.metadata:
        click.echo(f"Issuer: {etf.metadata.issuer}")
        click.echo(f"Category: {etf.metadata.category}")
        if etf.metadata.management_fee:
            click.echo(f"Management Fee: {etf.metadata.management_fee}%")
    
    click.echo(f"\nData Points: {len(etf.price_history)}")
    
    if etf.price_history:
        earliest = etf.price_history[0]
        latest = etf.price_history[-1]
        
        click.echo(f"Date Range: {earliest.date} to {latest.date}")
        click.echo(f"\nLatest Price ({latest.date}):")
        click.echo(f"   Open: ${latest.open}")
        click.echo(f"   High: ${latest.high}")
        click.echo(f"   Low: ${latest.low}")
        click.echo(f"   Close: ${latest.close}")
        click.echo(f"   Volume: {latest.volume:,}")


@cli.command()
@click.option('--data-dir', default='/data/etf', help='Data directory path')
@click.option('--output', default=None, help='Output directory')
@click.option('--tickers', default=None, help='Comma-separated list of tickers')
def export(data_dir: str, output: str, tickers: str):
    """Export data for ML/RL training"""
    system = ETFDataSystem(data_dir=data_dir)
    
    ticker_list = tickers.split(',') if tickers else None
    
    click.echo("📦 Exporting data for ML/RL training...")
    
    result = system.export_for_ml(
        output_dir=output,
        tickers=ticker_list
    )
    
    click.echo(f"\n✅ Export Complete!")
    click.echo(f"   Output Directory: {result['output_directory']}")
    click.echo(f"   Parquet Files: {result['parquet_files']}")
    click.echo(f"   Metadata File: {result['metadata_file']}")
    click.echo(f"   Tickers: {len(result['tickers'])}")


@cli.command()
def list_etfs():
    """List all available ETFs"""
    from ultracore.market_data.etf.asx_etf_list import ETF_CATEGORIES
    
    click.echo("📋 Available ASX ETFs\n")
    
    for category, etfs in ETF_CATEGORIES.items():
        click.echo(f"\n{category} ({len(etfs)} ETFs):")
        for etf in sorted(etfs):
            click.echo(f"   {etf}")
    
    click.echo(f"\n📊 Total: {len(get_all_etfs())} ETFs")


@cli.command()
@click.argument('ticker')
@click.option('--data-dir', default='/data/etf', help='Data directory path')
@click.option('--output', default=None, help='Output CSV file')
def export_ticker(ticker: str, data_dir: str, output: str):
    """Export single ETF to CSV"""
    system = ETFDataSystem(data_dir=data_dir)
    
    df = system.get_ml_features(ticker, include_technical=True)
    
    if df.empty:
        click.echo(f"❌ No data found for {ticker}")
        return
    
    if output is None:
        output = f"{ticker}_data.csv"
    
    df.to_csv(output)
    
    click.echo(f"✅ Exported {len(df)} rows to {output}")
    click.echo(f"   Columns: {len(df.columns)}")
    click.echo(f"   Date Range: {df.index[0]} to {df.index[-1]}")


if __name__ == '__main__':
    cli()
