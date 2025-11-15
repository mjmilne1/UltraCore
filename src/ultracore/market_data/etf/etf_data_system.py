"""
ETF Data System - Main Orchestrator
Coordinates all components: agents, data collection, storage, and updates
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4

from ultracore.market_data.etf.agents.etf_collector_agent import ETFCollectorAgent
from ultracore.market_data.etf.services.yahoo_finance_collector import YahooFinanceCollector
from ultracore.market_data.etf.data_mesh.etf_data_product import ETFDataProduct
from ultracore.market_data.etf.asx_etf_list import get_all_etfs
from ultracore.event_sourcing.store.event_store import EventStore


logger = logging.getLogger(__name__)


class ETFDataSystem:
    """
    Main ETF Data System
    
    Responsibilities:
    - Initialize and coordinate all components
    - Schedule daily updates
    - Provide unified API for data access
    - Ensure data quality and consistency
    """
    
    def __init__(
        self,
        data_dir: str = "/data/etf",
        event_store: Optional[EventStore] = None
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.collector = YahooFinanceCollector()
        self.event_store = event_store or self._create_event_store()
        self.agent = ETFCollectorAgent(
            event_store=self.event_store,
            collector=self.collector
        )
        self.data_product = ETFDataProduct()
        
        # System state
        self.initialized = False
        self.last_update: Optional[datetime] = None
        self.update_time = time(18, 0)  # 6 PM AEST (after market close)
        
        logger.info(f"ETF Data System initialized with data_dir: {self.data_dir}")
    
    def _create_event_store(self) -> EventStore:
        """Create event store for event sourcing"""
        # In production, this would connect to a real event store
        # For now, return a mock or in-memory store
        # Use a simple in-memory implementation
        from ultracore.event_sourcing.base import EventStore, Event, ConcurrencyError
        from typing import Dict, List, Optional
        
        class SimpleEventStore(EventStore):
            """Simple in-memory event store for development/testing"""
            
            def __init__(self):
                self.events: Dict[str, List[Event]] = {}
                self.versions: Dict[str, int] = {}
            
            async def save_events(
                self,
                aggregate_id: str,
                events: List[Event],
                expected_version: Optional[int] = None
            ) -> None:
                """Save events to in-memory store"""
                current_version = self.versions.get(aggregate_id, 0)
                
                if expected_version is not None and current_version != expected_version:
                    raise ConcurrencyError(
                        f"Expected version {expected_version}, got {current_version}"
                    )
                
                if aggregate_id not in self.events:
                    self.events[aggregate_id] = []
                
                self.events[aggregate_id].extend(events)
                self.versions[aggregate_id] = current_version + len(events)
            
            async def get_events(
                self,
                aggregate_id: str,
                from_version: int = 0,
                to_version: Optional[int] = None
            ) -> List[Event]:
                """Get events for aggregate"""
                events = self.events.get(aggregate_id, [])
                
                filtered = [
                    e for e in events
                    if e.metadata.version >= from_version
                ]
                
                if to_version is not None:
                    filtered = [e for e in filtered if e.metadata.version <= to_version]
                
                return filtered
            
            async def get_events_by_type(
                self,
                event_type,
                from_timestamp: Optional[datetime] = None,
                to_timestamp: Optional[datetime] = None,
                limit: int = 100
            ) -> List[Event]:
                """Get events by type"""
                all_events = []
                for events in self.events.values():
                    all_events.extend(events)
                
                filtered = [e for e in all_events if e.metadata.event_type == event_type]
                
                if from_timestamp:
                    filtered = [e for e in filtered if e.metadata.timestamp >= from_timestamp]
                
                if to_timestamp:
                    filtered = [e for e in filtered if e.metadata.timestamp <= to_timestamp]
                
                return filtered[:limit]
            
            async def get_aggregate_version(self, aggregate_id: str) -> int:
                """Get current aggregate version"""
                return self.versions.get(aggregate_id, 0)
        
        return SimpleEventStore()
    
    async def initialize(self, force: bool = False) -> Dict[str, Any]:
        """
        Initialize the system with complete historical data
        
        Args:
            force: Force re-initialization even if data exists
        
        Returns:
            Summary of initialization
        """
        if self.initialized and not force:
            logger.info("System already initialized")
            return {"status": "already_initialized"}
        
        logger.info("Starting system initialization...")
        
        # Run initial data collection
        summary = await self.agent.initialize_all_etfs()
        
        # Load data into data product
        for ticker, etf in self.agent.etf_aggregates.items():
            self.data_product.add_etf(etf)
        
        # Export to parquet for ML/RL training
        parquet_dir = self.data_dir / "parquet"
        created_files = self.data_product.export_to_parquet(str(parquet_dir))
        
        self.initialized = True
        self.last_update = datetime.utcnow()
        
        logger.info(f"Initialization complete: {summary['successful']} ETFs collected")
        
        return {
            **summary,
            "parquet_files_created": len(created_files),
            "data_directory": str(self.data_dir),
            "status": "initialized"
        }
    
    async def update(self) -> Dict[str, Any]:
        """
        Run daily update to get latest data
        
        Returns:
            Summary of update operation
        """
        if not self.initialized:
            logger.warning("System not initialized, running initialization first")
            return await self.initialize()
        
        logger.info("Starting daily update...")
        
        # Run update
        summary = await self.agent.update_all_etfs()
        
        # Update data product
        for ticker, etf in self.agent.etf_aggregates.items():
            self.data_product.add_etf(etf)
        
        # Export updated data
        parquet_dir = self.data_dir / "parquet"
        created_files = self.data_product.export_to_parquet(str(parquet_dir))
        
        self.last_update = datetime.utcnow()
        
        logger.info(f"Update complete: {summary['successful']} ETFs updated")
        
        return {
            **summary,
            "parquet_files_updated": len(created_files),
            "status": "updated"
        }
    
    async def run_scheduler(self) -> None:
        """
        Run continuous scheduler for daily updates
        Updates run at specified time each day
        """
        logger.info(f"Starting scheduler - updates at {self.update_time}")
        
        # Initial setup if needed
        if not self.initialized:
            await self.initialize()
        
        while True:
            try:
                # Calculate time until next update
                now = datetime.now()
                target = datetime.combine(now.date(), self.update_time)
                
                # If target time has passed today, schedule for tomorrow
                if now >= target:
                    target = datetime.combine(
                        now.date() + timedelta(days=1),
                        self.update_time
                    )
                
                wait_seconds = (target - now).total_seconds()
                logger.info(f"Next update in {wait_seconds / 3600:.1f} hours at {target}")
                
                # Wait until update time
                await asyncio.sleep(wait_seconds)
                
                # Run update
                await self.update()
                
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                # Wait 1 hour before retry
                await asyncio.sleep(3600)
    
    def get_data_product(self) -> ETFDataProduct:
        """Get the data product for ML/RL access"""
        return self.data_product
    
    def get_etf_data(
        self,
        ticker: str,
        format: str = "dataframe"
    ) -> Any:
        """
        Get ETF data in specified format
        
        Args:
            ticker: ETF ticker symbol
            format: "dataframe", "dict", "aggregate"
        
        Returns:
            Data in requested format
        """
        if format == "aggregate":
            return self.data_product.get_etf(ticker)
        elif format == "dataframe":
            return self.data_product.get_price_data_df(ticker)
        elif format == "dict":
            etf = self.data_product.get_etf(ticker)
            return etf.to_dict() if etf else None
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def get_ml_features(
        self,
        ticker: str,
        include_technical: bool = True
    ):
        """Get ML-ready features for a ticker"""
        return self.data_product.get_ml_features(
            ticker,
            include_technical=include_technical
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        agent_stats = self.agent.get_statistics()
        data_stats = self.data_product.get_summary_statistics()
        
        return {
            "initialized": self.initialized,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "next_update_time": self.update_time.isoformat(),
            "data_directory": str(self.data_dir),
            "agent_statistics": agent_stats,
            "data_product_statistics": data_stats
        }
    
    def export_for_ml(
        self,
        output_dir: Optional[str] = None,
        tickers: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Export data in ML-ready formats
        
        Creates:
        - Parquet files (one per ETF)
        - Combined CSV for all ETFs
        - Metadata JSON
        
        Returns:
            Summary of exported files
        """
        if output_dir is None:
            output_dir = str(self.data_dir / "ml_export")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Export parquet files
        parquet_files = self.data_product.export_to_parquet(
            output_dir,
            tickers=tickers
        )
        
        # Export metadata
        import json
        metadata = {
            "export_date": datetime.utcnow().isoformat(),
            "total_etfs": len(parquet_files),
            "tickers": tickers or self.data_product.get_all_tickers(),
            "data_product": self.data_product.get_summary_statistics()
        }
        
        metadata_path = Path(output_dir) / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Exported {len(parquet_files)} ETFs to {output_dir}")
        
        return {
            "output_directory": output_dir,
            "parquet_files": len(parquet_files),
            "metadata_file": str(metadata_path),
            "tickers": metadata["tickers"]
        }


# Convenience functions for easy access
_system_instance: Optional[ETFDataSystem] = None


def get_etf_system(data_dir: str = "/data/etf") -> ETFDataSystem:
    """Get or create the global ETF data system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = ETFDataSystem(data_dir=data_dir)
    return _system_instance


async def initialize_etf_data() -> Dict[str, Any]:
    """Initialize ETF data system"""
    system = get_etf_system()
    return await system.initialize()


async def update_etf_data() -> Dict[str, Any]:
    """Update ETF data"""
    system = get_etf_system()
    return await system.update()


def get_etf_dataframe(ticker: str):
    """Get ETF data as pandas DataFrame"""
    system = get_etf_system()
    return system.get_data_product().get_price_data_df(ticker)


def get_ml_features(ticker: str, include_technical: bool = True):
    """Get ML features for a ticker"""
    system = get_etf_system()
    return system.get_ml_features(ticker, include_technical=include_technical)
