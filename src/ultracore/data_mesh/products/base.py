"""
Data Product Base Framework.

Base classes and interfaces for data products in the Data Mesh.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class DataQualityLevel(str, Enum):
    """Data quality levels."""
    GOLD = "gold"  # Production-ready, high quality
    SILVER = "silver"  # Validated, good quality
    BRONZE = "bronze"  # Raw, unvalidated


class RefreshFrequency(str, Enum):
    """Data refresh frequency."""
    REALTIME = "realtime"  # Streaming, < 1 second
    NEAR_REALTIME = "near_realtime"  # < 1 minute
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class DataProductStatus(str, Enum):
    """Data product status."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    MAINTENANCE = "maintenance"


class DataProductMetadata(BaseModel):
    """Metadata for a data product."""
    product_id: str
    name: str
    description: str
    domain: str
    owner: str
    owner_team: str
    
    # Quality
    quality_level: DataQualityLevel
    refresh_frequency: RefreshFrequency
    
    # Status
    status: DataProductStatus = DataProductStatus.ACTIVE
    version: str = "1.0.0"
    
    # Compliance
    contains_pii: bool = False
    data_classification: str = "internal"  # public, internal, confidential, restricted
    retention_days: Optional[int] = None
    
    # SLA
    availability_sla: Decimal = Decimal("99.9")  # 99.9%
    latency_sla_ms: Optional[int] = None
    
    # Lineage
    source_systems: List[str] = []
    dependent_products: List[str] = []
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_refreshed_at: Optional[datetime] = None


class DataQualityMetrics(BaseModel):
    """Data quality metrics for a data product."""
    product_id: str
    
    # Completeness
    completeness_score: Decimal = Field(..., ge=0, le=100)
    missing_values_count: int = 0
    missing_values_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    
    # Accuracy
    accuracy_score: Decimal = Field(..., ge=0, le=100)
    validation_errors_count: int = 0
    
    # Consistency
    consistency_score: Decimal = Field(..., ge=0, le=100)
    inconsistency_count: int = 0
    
    # Timeliness
    timeliness_score: Decimal = Field(..., ge=0, le=100)
    avg_latency_ms: Optional[int] = None
    max_latency_ms: Optional[int] = None
    
    # Uniqueness
    uniqueness_score: Decimal = Field(..., ge=0, le=100)
    duplicate_count: int = 0
    
    # Overall
    overall_quality_score: Decimal = Field(..., ge=0, le=100)
    
    # Timestamps
    measured_at: datetime
    measurement_period_hours: int = 24


class DataLineage(BaseModel):
    """Data lineage information."""
    product_id: str
    
    # Upstream (sources)
    upstream_products: List[str] = []
    upstream_tables: List[str] = []
    upstream_apis: List[str] = []
    
    # Downstream (consumers)
    downstream_products: List[str] = []
    downstream_services: List[str] = []
    downstream_reports: List[str] = []
    
    # Transformations
    transformation_steps: List[Dict[str, Any]] = []
    
    # Timestamps
    lineage_captured_at: datetime


class DataProductSchema(BaseModel):
    """Schema definition for a data product."""
    product_id: str
    version: str
    
    # Fields
    fields: List[Dict[str, Any]]
    
    # Indexes
    indexes: List[str] = []
    
    # Partitioning
    partition_key: Optional[str] = None
    
    # Timestamps
    schema_version: str = "1.0.0"
    created_at: datetime


class DataProduct(ABC):
    """
    Base class for all data products.
    
    A data product is a self-contained, discoverable, and addressable
    data asset that provides value to data consumers.
    """
    
    def __init__(self, metadata: DataProductMetadata):
        self.metadata = metadata
        self._quality_metrics: Optional[DataQualityMetrics] = None
        self._lineage: Optional[DataLineage] = None
    
    @abstractmethod
    async def refresh(self) -> bool:
        """
        Refresh the data product.
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query the data product.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of records matching the query
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> DataProductSchema:
        """
        Get the schema of the data product.
        
        Returns:
            DataProductSchema: Schema definition
        """
        pass
    
    async def measure_quality(self) -> DataQualityMetrics:
        """
        Measure data quality metrics.
        
        Returns:
            DataQualityMetrics: Quality metrics
        """
        # Default implementation - override for specific metrics
        return DataQualityMetrics(
            product_id=self.metadata.product_id,
            completeness_score=Decimal("100"),
            accuracy_score=Decimal("100"),
            consistency_score=Decimal("100"),
            timeliness_score=Decimal("100"),
            uniqueness_score=Decimal("100"),
            overall_quality_score=Decimal("100"),
            measured_at=datetime.utcnow()
        )
    
    async def get_lineage(self) -> DataLineage:
        """
        Get data lineage information.
        
        Returns:
            DataLineage: Lineage information
        """
        if self._lineage is None:
            self._lineage = DataLineage(
                product_id=self.metadata.product_id,
                upstream_products=self.metadata.source_systems,
                downstream_products=self.metadata.dependent_products,
                lineage_captured_at=datetime.utcnow()
            )
        return self._lineage
    
    async def validate(self) -> List[str]:
        """
        Validate the data product.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check metadata
        if not self.metadata.product_id:
            errors.append("Product ID is required")
        if not self.metadata.name:
            errors.append("Product name is required")
        if not self.metadata.owner:
            errors.append("Product owner is required")
        
        # Check quality
        quality = await self.measure_quality()
        if quality.overall_quality_score < Decimal("70"):
            errors.append(f"Quality score too low: {quality.overall_quality_score}")
        
        return errors
    
    def get_metadata(self) -> DataProductMetadata:
        """Get product metadata."""
        return self.metadata
    
    def update_metadata(self, **kwargs) -> None:
        """Update product metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.metadata.updated_at = datetime.utcnow()


class AggregatedDataProduct(DataProduct):
    """
    Base class for aggregated data products.
    
    Aggregated products combine data from multiple sources
    and apply transformations/aggregations.
    """
    
    def __init__(self, metadata: DataProductMetadata, source_products: List[str]):
        super().__init__(metadata)
        self.source_products = source_products
    
    @abstractmethod
    async def aggregate(self) -> bool:
        """
        Perform aggregation from source products.
        
        Returns:
            bool: True if aggregation successful, False otherwise
        """
        pass


class StreamingDataProduct(DataProduct):
    """
    Base class for streaming data products.
    
    Streaming products provide real-time or near-real-time data.
    """
    
    def __init__(self, metadata: DataProductMetadata, stream_topic: str):
        super().__init__(metadata)
        self.stream_topic = stream_topic
        metadata.refresh_frequency = RefreshFrequency.REALTIME
    
    @abstractmethod
    async def subscribe(self, callback) -> None:
        """
        Subscribe to the data stream.
        
        Args:
            callback: Function to call when new data arrives
        """
        pass
    
    @abstractmethod
    async def publish(self, data: Dict[str, Any]) -> bool:
        """
        Publish data to the stream.
        
        Args:
            data: Data to publish
            
        Returns:
            bool: True if publish successful, False otherwise
        """
        pass
