"""
UltraCore Base Repository

Abstract base repository with common CRUD operations:
- Create, Read, Update, Delete
- Multi-tenant filtering
- Soft delete support
- Caching integration
- Event sourcing integration
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import json

from ultracore.database.models.base import BaseModel
from ultracore.database.models.events import EventStore
from ultracore.database.config import get_cache_manager
import uuid

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository with common operations
    
    Features:
    - Async operations
    - Multi-tenant filtering
    - Soft delete support
    - Caching
    - Event sourcing integration
    """
    
    def __init__(self, model: Type[T], session: AsyncSession, tenant_id: str):
        self.model = model
        self.session = session
        self.tenant_id = tenant_id
        self.cache = get_cache_manager()
    
    # ========================================================================
    # CREATE
    # ========================================================================
    
    async def create(
        self,
        entity: T,
        created_by: str,
        emit_event: bool = True
    ) -> T:
        """
        Create new entity
        
        Args:
            entity: Entity to create
            created_by: User creating the entity
            emit_event: Whether to emit creation event
        
        Returns:
            Created entity with ID
        """
        # Set tenant and audit fields
        entity.tenant_id = self.tenant_id
        entity.created_by = created_by
        entity.version = 1
        
        # Add to session
        self.session.add(entity)
        await self.session.flush()
        
        # Emit event
        if emit_event:
            await self._emit_event(
                event_type=f"{self.model.__name__}Created",
                aggregate_id=str(entity.id),
                event_data=self._entity_to_dict(entity),
                user_id=created_by
            )
        
        return entity
    
    # ========================================================================
    # READ
    # ========================================================================
    
    async def get_by_id(
        self,
        entity_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[T]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity UUID
            include_deleted: Include soft-deleted records
        
        Returns:
            Entity or None
        """
        # Try cache first
        cache_key = f"{self.model.__name__}:{self.tenant_id}:{entity_id}"
        cached = await self.cache.get(cache_key)
        
        if cached:
            return self._dict_to_entity(json.loads(cached))
        
        # Query database
        query = select(self.model).where(
            and_(
                self.model.id == entity_id,
                self.model.tenant_id == self.tenant_id
            )
        )
        
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()
        
        # Cache result
        if entity:
            await self.cache.set(
                cache_key,
                json.dumps(self._entity_to_dict(entity)),
                expiry=3600
            )
        
        return entity
    
    async def get_by_business_id(
        self,
        business_id: str,
        business_id_field: str = 'customer_id'
    ) -> Optional[T]:
        """
        Get entity by business ID (e.g., CUST-xxx, ACC-xxx)
        
        Args:
            business_id: Business identifier
            business_id_field: Field name for business ID
        
        Returns:
            Entity or None
        """
        query = select(self.model).where(
            and_(
                getattr(self.model, business_id_field) == business_id,
                self.model.tenant_id == self.tenant_id,
                self.model.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[T]:
        """
        List entities with filtering and pagination
        
        Args:
            filters: Dictionary of field:value filters
            offset: Pagination offset
            limit: Maximum results
            order_by: Field to order by
            include_deleted: Include soft-deleted records
        
        Returns:
            List of entities
        """
        query = select(self.model).where(
            self.model.tenant_id == self.tenant_id
        )
        
        # Soft delete filter
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Order by
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by).desc())
        else:
            query = query.order_by(self.model.created_at.desc())
        
        # Pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Count entities matching filters
        
        Args:
            filters: Dictionary of field:value filters
            include_deleted: Include soft-deleted records
        
        Returns:
            Count of matching entities
        """
        query = select(func.count(self.model.id)).where(
            self.model.tenant_id == self.tenant_id
        )
        
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    async def update(
        self,
        entity: T,
        updated_by: str,
        emit_event: bool = True
    ) -> T:
        """
        Update entity
        
        Args:
            entity: Entity to update
            updated_by: User updating the entity
            emit_event: Whether to emit update event
        
        Returns:
            Updated entity
        """
        # Update audit fields
        entity.updated_by = updated_by
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        
        await self.session.flush()
        
        # Invalidate cache
        cache_key = f"{self.model.__name__}:{self.tenant_id}:{entity.id}"
        await self.cache.delete(cache_key)
        
        # Emit event
        if emit_event:
            await self._emit_event(
                event_type=f"{self.model.__name__}Updated",
                aggregate_id=str(entity.id),
                event_data=self._entity_to_dict(entity),
                user_id=updated_by
            )
        
        return entity
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    async def soft_delete(
        self,
        entity_id: uuid.UUID,
        deleted_by: str,
        emit_event: bool = True
    ) -> bool:
        """
        Soft delete entity
        
        Args:
            entity_id: Entity UUID to delete
            deleted_by: User deleting the entity
            emit_event: Whether to emit delete event
        
        Returns:
            True if deleted, False if not found
        """
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = deleted_by
        entity.updated_at = datetime.utcnow()
        
        await self.session.flush()
        
        # Invalidate cache
        cache_key = f"{self.model.__name__}:{self.tenant_id}:{entity_id}"
        await self.cache.delete(cache_key)
        
        # Emit event
        if emit_event:
            await self._emit_event(
                event_type=f"{self.model.__name__}Deleted",
                aggregate_id=str(entity_id),
                event_data={'deleted_at': entity.deleted_at.isoformat()},
                user_id=deleted_by
            )
        
        return True
    
    async def hard_delete(
        self,
        entity_id: uuid.UUID,
        deleted_by: str
    ) -> bool:
        """
        Hard delete entity (permanent)
        
        Args:
            entity_id: Entity UUID to delete
            deleted_by: User deleting the entity
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(
                and_(
                    self.model.id == entity_id,
                    self.model.tenant_id == self.tenant_id
                )
            )
        )
        
        # Invalidate cache
        cache_key = f"{self.model.__name__}:{self.tenant_id}:{entity_id}"
        await self.cache.delete(cache_key)
        
        return result.rowcount > 0
    
    # ========================================================================
    # EVENT SOURCING
    # ========================================================================
    
    async def _emit_event(
        self,
        event_type: str,
        aggregate_id: str,
        event_data: Dict[str, Any],
        user_id: str
    ):
        """
        Emit event to event store
        
        Args:
            event_type: Type of event (e.g., CustomerCreated)
            aggregate_id: ID of aggregate being changed
            event_data: Event payload
            user_id: User triggering the event
        """
        event = EventStore(
            tenant_id=self.tenant_id,
            event_type=event_type,
            aggregate_type=self.model.__name__,
            aggregate_id=aggregate_id,
            aggregate_version=1,  # TODO: Track properly
            event_data=event_data,
            user_id=user_id
        )
        
        self.session.add(event)
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary for caching/events"""
        result = {}
        for column in entity.__table__.columns:
            value = getattr(entity, column.name)
            
            # Handle special types
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        
        return result
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        """Convert dictionary to entity (for cache retrieval)"""
        # This is simplified - in production, properly reconstruct entity
        entity = self.model()
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        return entity
