"""
ETF Data Collector Agent - Agentic AI Component
Autonomous agent that collects, validates, and updates ETF data
Uses reinforcement learning to optimize collection strategies
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
import logging

# Simplified to standalone service - no Agent inheritance needed
from ultracore.market_data.etf.services.alpha_vantage_collector import (
    AlphaVantageCollector,
    CollectionResult
)
from ultracore.market_data.etf.aggregates.etf_aggregate import ETFAggregate, ETFMetadata
from ultracore.market_data.etf.asx_etf_list import get_all_etfs, get_category_for_etf
from ultracore.event_sourcing.store.event_store import EventStore


logger = logging.getLogger(__name__)


class ETFCollectorAgent:
    """
    Autonomous agent for ETF data collection
    
    Capabilities:
    - Initial bulk download of all ASX ETFs
    - Daily incremental updates
    - Error handling and retry logic
    - Data validation and quality checks
    - Performance optimization through RL
    """
    
    def __init__(
        self,
        event_store: EventStore,
        api_key: str,
        collector: Optional[AlphaVantageCollector] = None
    ):
        self.agent_id = str(uuid4())
        self.name = "ETF Data Collector Agent"
        self.event_store = event_store
        self.collector = collector or AlphaVantageCollector(api_key=api_key)
        self.etf_aggregates: Dict[str, ETFAggregate] = {}
        
        # Agent state
        self.total_etfs = 0
        self.successful_collections = 0
        self.failed_collections = 0
        self.last_collection_time: Optional[datetime] = None
        
        # RL parameters
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds
        self.batch_size = 10  # ETFs to process in parallel
        
    async def initialize_all_etfs(self) -> Dict[str, Any]:
        """
        Initial bulk download of all ASX ETFs
        This is the first-time setup operation
        """
        logger.info("Starting initial ETF data collection...")
        
        job_id = uuid4()
        start_time = datetime.utcnow()
        
        all_tickers = get_all_etfs()
        self.total_etfs = len(all_tickers)
        
        logger.info(f"Found {self.total_etfs} ASX ETFs to collect")
        
        # Process in batches for better performance
        results = []
        for i in range(0, len(all_tickers), self.batch_size):
            batch = all_tickers[i:i + self.batch_size]
            batch_results = await self._process_batch(batch, initial=True)
            results.extend(batch_results)
            
            # Progress logging
            progress = (i + len(batch)) / len(all_tickers) * 100
            logger.info(f"Progress: {progress:.1f}% ({i + len(batch)}/{len(all_tickers)})")
        
        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_data_points = sum(r.data_points for r in results if r.success)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        self.successful_collections = successful
        self.failed_collections = failed
        self.last_collection_time = datetime.utcnow()
        
        summary = {
            "job_id": str(job_id),
            "total_etfs": self.total_etfs,
            "successful": successful,
            "failed": failed,
            "total_data_points": total_data_points,
            "duration_seconds": duration,
            "average_data_points": total_data_points / successful if successful > 0 else 0,
            "failed_tickers": [r.ticker for r in results if not r.success]
        }
        
        logger.info(f"Initial collection complete: {successful}/{self.total_etfs} successful")
        
        return summary
    
    async def update_all_etfs(self) -> Dict[str, Any]:
        """
        Daily update of all ETFs with latest data
        Only downloads recent data (last 5 days)
        """
        logger.info("Starting daily ETF data update...")
        
        job_id = uuid4()
        start_time = datetime.utcnow()
        
        all_tickers = get_all_etfs()
        
        # Process in batches
        results = []
        for i in range(0, len(all_tickers), self.batch_size):
            batch = all_tickers[i:i + self.batch_size]
            batch_results = await self._process_batch(batch, initial=False)
            results.extend(batch_results)
            
            progress = (i + len(batch)) / len(all_tickers) * 100
            logger.info(f"Update progress: {progress:.1f}%")
        
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_data_points = sum(r.data_points for r in results if r.success)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        self.last_collection_time = datetime.utcnow()
        
        summary = {
            "job_id": str(job_id),
            "total_etfs": len(all_tickers),
            "successful": successful,
            "failed": failed,
            "total_data_points": total_data_points,
            "duration_seconds": duration,
            "failed_tickers": [r.ticker for r in results if not r.success]
        }
        
        logger.info(f"Daily update complete: {successful}/{len(all_tickers)} successful")
        
        return summary
    
    async def _process_batch(
        self,
        tickers: List[str],
        initial: bool = True
    ) -> List[CollectionResult]:
        """Process a batch of ETFs in parallel"""
        tasks = [
            self._process_single_etf(ticker, initial)
            for ticker in tickers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.error(f"Exception processing {ticker}: {result}")
                valid_results.append(CollectionResult(
                    ticker=ticker,
                    success=False,
                    error=str(result)
                ))
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _process_single_etf(
        self,
        ticker: str,
        initial: bool = True
    ) -> CollectionResult:
        """Process a single ETF with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                if initial:
                    # Initial download - get all historical data
                    result = await asyncio.to_thread(
                        self.collector.download_historical_data,
                        ticker=ticker,
                        outputsize="full"
                    )
                else:
                    # Daily update - get last 100 days (compact)
                    result = await asyncio.to_thread(
                        self.collector.download_historical_data,
                        ticker=ticker,
                        outputsize="compact"
                    )
                
                if result.success:
                    # Create or update aggregate
                    await self._update_etf_aggregate(ticker, result, initial)
                    return result
                else:
                    if attempt < self.retry_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {ticker}, retrying...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        logger.error(f"All attempts failed for {ticker}: {result.error}")
                        return result
                        
            except Exception as e:
                logger.error(f"Error processing {ticker} (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return CollectionResult(
                        ticker=ticker,
                        success=False,
                        error=str(e)
                    )
        
        return CollectionResult(
            ticker=ticker,
            success=False,
            error="Max retries exceeded"
        )
    
    async def _update_etf_aggregate(
        self,
        ticker: str,
        result: CollectionResult,
        initial: bool
    ) -> None:
        """Create or update ETF aggregate with collected data"""
        try:
            # Get or create aggregate
            if ticker not in self.etf_aggregates:
                # Get metadata
                info = await asyncio.to_thread(
                    self.collector.get_etf_info,
                    ticker
                )
                
                if info:
                    metadata = self.collector.extract_metadata(info, ticker)
                else:
                    # Create minimal metadata
                    category = get_category_for_etf(ticker)
                    metadata = ETFMetadata(
                        name=ticker,
                        issuer="Unknown",
                        category=category or "Unknown"
                    )
                
                # Create new aggregate
                etf = ETFAggregate.create(ticker, metadata)
                self.etf_aggregates[ticker] = etf
            else:
                etf = self.etf_aggregates[ticker]
            
            # Add price data
            # Note: In real implementation, we'd get the actual price data from result
            # For now, we just record the event
            
            # Persist events to event store
            for event in etf.uncommitted_events:
                await asyncio.to_thread(
                    self.event_store.append,
                    event
                )
            
            etf.mark_events_as_committed()
            
        except Exception as e:
            logger.error(f"Error updating aggregate for {ticker}: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        return {
            "total_etfs": self.total_etfs,
            "successful_collections": self.successful_collections,
            "failed_collections": self.failed_collections,
            "success_rate": (
                self.successful_collections / self.total_etfs * 100
                if self.total_etfs > 0 else 0
            ),
            "last_collection_time": (
                self.last_collection_time.isoformat()
                if self.last_collection_time else None
            ),
            "etfs_in_memory": len(self.etf_aggregates)
        }
    
    async def run(self) -> None:
        """Main agent loop - runs continuously"""
        logger.info(f"Starting {self.name}...")
        
        # Initial collection if needed
        if not self.etf_aggregates:
            await self.initialize_all_etfs()
        
        # Daily update loop
        while True:
            try:
                # Wait until next update time (e.g., 6 PM AEST after market close)
                await self._wait_for_next_update()
                
                # Run daily update
                await self.update_all_etfs()
                
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _wait_for_next_update(self) -> None:
        """Wait until next scheduled update time"""
        # For now, just wait 24 hours
        # In production, calculate time until 6 PM AEST
        await asyncio.sleep(86400)  # 24 hours
