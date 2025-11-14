"""
Base Repository
Common CRUD operations for all repositories
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations
    
    Provides:
    - Create
    - Read (get by ID, get by filters, list all)
    - Update
    - Delete
    - Soft delete (if model supports it)
    """
    
    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    # ========================================================================
    # Create
    # ========================================================================
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with generated ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info(f"Created {self.model.__name__}: {getattr(entity, 'id', 'unknown')}")
        
        return entity
    
    async def create_many(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of created entities
        """
        self.session.add_all(entities)
        await self.session.flush()
        
        for entity in entities:
            await self.session.refresh(entity)
        
        logger.info(f"Created {len(entities)} {self.model.__name__} entities")
        
        return entities
    
    # ========================================================================
    # Read
    # ========================================================================
    
    async def get(self, id: UUID) -> Optional[T]:
        """
        Get entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        
        entity = result.scalar_one_or_none()
        
        if entity:
            logger.debug(f"Found {self.model.__name__}: {id}")
        else:
            logger.debug(f"{self.model.__name__} not found: {id}")
        
        return entity
    
    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Get entity by a specific field
        
        Args:
            field_name: Field name
            value: Field value
            
        Returns:
            Entity or None if not found
        """
        field = getattr(self.model, field_name)
        
        result = await self.session.execute(
            select(self.model).where(field == value)
        )
        
        return result.scalar_one_or_none()
    
    async def get_many_by_field(self, field_name: str, value: Any) -> List[T]:
        """
        Get multiple entities by a specific field
        
        Args:
            field_name: Field name
            value: Field value
            
        Returns:
            List of entities
        """
        field = getattr(self.model, field_name)
        
        result = await self.session.execute(
            select(self.model).where(field == value)
        )
        
        return list(result.scalars().all())
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        List entities with optional filters, pagination, and ordering
        
        Args:
            filters: Dictionary of field:value filters
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by
            
        Returns:
            List of entities
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            conditions = []
            for field_name, value in filters.items():
                field = getattr(self.model, field_name)
                conditions.append(field == value)
            
            query = query.where(and_(*conditions))
        
        # Apply ordering
        if order_by:
            order_field = getattr(self.model, order_by)
            query = query.order_by(order_field)
        
        # Apply pagination
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filters
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Count of entities
        """
        from sqlalchemy import func
        
        query = select(func.count()).select_from(self.model)
        
        # Apply filters
        if filters:
            conditions = []
            for field_name, value in filters.items():
                field = getattr(self.model, field_name)
                conditions.append(field == value)
            
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        
        return result.scalar()
    
    # ========================================================================
    # Update
    # ========================================================================
    
    async def update(self, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """
        Update entity by ID
        
        Args:
            id: Entity ID
            data: Dictionary of fields to update
            
        Returns:
            Updated entity or None if not found
        """
        # Get entity first
        entity = await self.get(id)
        
        if not entity:
            return None
        
        # Update fields
        for field, value in data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info(f"Updated {self.model.__name__}: {id}")
        
        return entity
    
    async def update_many(
        self,
        filters: Dict[str, Any],
        data: Dict[str, Any]
    ) -> int:
        """
        Update multiple entities matching filters
        
        Args:
            filters: Dictionary of field:value filters
            data: Dictionary of fields to update
            
        Returns:
            Number of entities updated
        """
        conditions = []
        for field_name, value in filters.items():
            field = getattr(self.model, field_name)
            conditions.append(field == value)
        
        stmt = update(self.model).where(and_(*conditions)).values(**data)
        
        result = await self.session.execute(stmt)
        
        logger.info(f"Updated {result.rowcount} {self.model.__name__} entities")
        
        return result.rowcount
    
    # ========================================================================
    # Delete
    # ========================================================================
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(self.model).where(self.model.id == id)
        
        result = await self.session.execute(stmt)
        
        if result.rowcount > 0:
            logger.info(f"Deleted {self.model.__name__}: {id}")
            return True
        else:
            logger.debug(f"{self.model.__name__} not found for deletion: {id}")
            return False
    
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """
        Delete multiple entities matching filters
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Number of entities deleted
        """
        conditions = []
        for field_name, value in filters.items():
            field = getattr(self.model, field_name)
            conditions.append(field == value)
        
        stmt = delete(self.model).where(and_(*conditions))
        
        result = await self.session.execute(stmt)
        
        logger.info(f"Deleted {result.rowcount} {self.model.__name__} entities")
        
        return result.rowcount
    
    # ========================================================================
    # Soft Delete (if model supports it)
    # ========================================================================
    
    async def soft_delete(self, id: UUID) -> Optional[T]:
        """
        Soft delete entity by setting is_active=False or deleted_at
        
        Args:
            id: Entity ID
            
        Returns:
            Updated entity or None if not found
        """
        entity = await self.get(id)
        
        if not entity:
            return None
        
        # Try to set is_active=False
        if hasattr(entity, 'is_active'):
            entity.is_active = False
        
        # Try to set deleted_at
        if hasattr(entity, 'deleted_at'):
            from datetime import datetime
            entity.deleted_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info(f"Soft deleted {self.model.__name__}: {id}")
        
        return entity
    
    # ========================================================================
    # Exists
    # ========================================================================
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        from sqlalchemy import func
        
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        
        result = await self.session.execute(query)
        
        return result.scalar() > 0
    
    async def exists_by_field(self, field_name: str, value: Any) -> bool:
        """
        Check if entity exists by field
        
        Args:
            field_name: Field name
            value: Field value
            
        Returns:
            True if exists, False otherwise
        """
        from sqlalchemy import func
        
        field = getattr(self.model, field_name)
        
        query = select(func.count()).select_from(self.model).where(field == value)
        
        result = await self.session.execute(query)
        
        return result.scalar() > 0
