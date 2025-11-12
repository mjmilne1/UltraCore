"""
Auto-Update System for UltraWealth
Keeps ETF data fresh with daily updates
"""

import schedule
import time
import asyncio
from datetime import datetime

class AutoUpdateScheduler:
    """Automatic data update scheduler"""
    
    def __init__(self):
        self.is_running = False
        self.datamesh = None
        self.etf_universe = None
    
    def initialize(self, datamesh, etf_universe):
        """Initialize with dependencies (avoids circular import)"""
        self.datamesh = datamesh
        self.etf_universe = etf_universe
    
    async def update_all_etfs(self):
        """Update all ETFs in universe"""
        if not self.datamesh or not self.etf_universe:
            print("Auto-updater not initialized")
            return {"status": "not_initialized"}
        
        print(f"[{datetime.now()}] Starting daily ETF update...")
        
        all_tickers = self.etf_universe.get_all_tickers()
        result = await self.datamesh.batch_ingest(all_tickers, "2y")
        
        print(f"[{datetime.now()}] Update complete: {result['successful']}/{result['total']} successful")
        return result
    
    def start_scheduler(self):
        """Start the daily update scheduler"""
        if not self.datamesh or not self.etf_universe:
            print("Cannot start scheduler - not initialized")
            return
        
        # Schedule daily update at 6 PM AEST (after market close)
        schedule.every().day.at("18:00").do(
            lambda: asyncio.run(self.update_all_etfs())
        )
        
        print("Auto-update scheduler configured. Updates at 6 PM AEST daily.")
        self.is_running = True
        
        # Run scheduler in background
        import threading
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False

auto_updater = AutoUpdateScheduler()
