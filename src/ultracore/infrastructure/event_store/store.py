from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime

from ultracore.infrastructure.event_store.models import StoredEvent, Base


class EventStore:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def append(
        self,
        aggregate_id: str,
        aggregate_type: str,
        event_type: str,
        event_data: Dict,
        user_id: Optional[str] = None
    ) -> StoredEvent:
        async with self.async_session() as session:
            result = await session.execute(
                select(StoredEvent.sequence)
                .where(StoredEvent.aggregate_id == aggregate_id)
                .order_by(StoredEvent.sequence.desc())
                .limit(1)
            )
            last_sequence = result.scalar()
            next_sequence = (last_sequence or 0) + 1
            
            event = StoredEvent(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                event_type=event_type,
                event_data=event_data,
                sequence=next_sequence,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc)
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event
    
    async def get_events(self, aggregate_id: str) -> List[StoredEvent]:
        async with self.async_session() as session:
            result = await session.execute(
                select(StoredEvent)
                .where(StoredEvent.aggregate_id == aggregate_id)
                .order_by(StoredEvent.sequence)
            )
            return result.scalars().all()
    
    async def get_all_events(self, limit: int = 1000) -> List[StoredEvent]:
        async with self.async_session() as session:
            result = await session.execute(
                select(StoredEvent)
                .order_by(StoredEvent.timestamp.desc())
                .limit(limit)
            )
            return result.scalars().all()


event_store: Optional[EventStore] = None

def get_event_store() -> EventStore:
    global event_store
    if event_store is None:
        # Use default postgres database to avoid corruption issues
        database_url = 'postgresql+asyncpg://postgres:ultracore123@127.0.0.1:5433/postgres'
        event_store = EventStore(database_url)
    return event_store
