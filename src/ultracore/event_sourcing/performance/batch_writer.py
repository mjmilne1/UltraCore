"""Batch Event Writer for High Throughput"""
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class BatchEventWriter:
    """Batch event writer for high throughput."""
    
    def __init__(self, producer, batch_size: int = 100, batch_timeout: float = 1.0):
        self.producer = producer
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.batch: List = []
        self.lock = asyncio.Lock()
        self._flush_task = None
        self.stats = {"batches_flushed": 0, "events_written": 0}
        logger.info(f"BatchEventWriter initialized (size={batch_size}, timeout={batch_timeout}s)")
    
    async def write(self, event):
        """Write event with batching."""
        async with self.lock:
            self.batch.append(event)
            
            if len(self.batch) >= self.batch_size:
                await self._flush()
            elif self._flush_task is None:
                self._flush_task = asyncio.create_task(self._auto_flush())
    
    async def _flush(self):
        """Flush batch to producer."""
        if not self.batch:
            return
        
        batch_copy = self.batch.copy()
        self.batch.clear()
        
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None
        
        # Send batch
        await self.producer.send_batch(batch_copy)
        
        self.stats["batches_flushed"] += 1
        self.stats["events_written"] += len(batch_copy)
        logger.debug(f"Flushed batch of {len(batch_copy)} events")
    
    async def _auto_flush(self):
        """Auto-flush after timeout."""
        try:
            await asyncio.sleep(self.batch_timeout)
            async with self.lock:
                await self._flush()
        except asyncio.CancelledError:
            pass
    
    def get_stats(self) -> dict:
        """Get writer statistics."""
        return {**self.stats, "pending": len(self.batch)}
