"""
UltraCore Document Management - Data Mesh Architecture

Implements data mesh principles for document management:
- Domain-oriented document ownership
- Documents as data products
- Self-serve data infrastructure
- Federated computational governance
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import asyncio

from ultracore.documents.document_core import (
    Document, DocumentStore, get_document_store,
    DocumentType, DocumentStatus
)
from ultracore.events.kafka_store import get_production_kafka_store


# ============================================================================
# Data Mesh Enums
# ============================================================================

class DocumentDomain(str, Enum):
    """Document domains aligned with business domains"""
    CUSTOMER = "customer"
    COMPLIANCE = "compliance"
    FINANCE = "finance"
    OPERATIONS = "operations"
    LEGAL = "legal"
    RISK = "risk"
    TECHNOLOGY = "technology"


class DataProductQuality(str, Enum):
    """Data product quality levels"""
    RAW = "RAW"  # Unprocessed
    BRONZE = "BRONZE"  # Basic validation
    SILVER = "SILVER"  # Enriched and cleaned
    GOLD = "GOLD"  # Analytics-ready


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DocumentDataProduct:
    """
    Document as a data product
    Encapsulates documents with ownership, SLAs, and quality metrics
    """
    product_id: str
    domain: DocumentDomain
    product_name: str
    description: str
    owner: str
    
    # Documents in this product
    document_ids: List[str] = field(default_factory=list)
    
    # Quality and SLA
    quality_level: DataProductQuality = DataProductQuality.RAW
    sla_availability: float = 99.9  # %
    sla_response_time_ms: int = 100
    
    # Governance
    data_classification: str = "CONFIDENTIAL"
    retention_policy_days: int = 2555  # 7 years default
    compliance_tags: List[str] = field(default_factory=list)
    
    # Mesh metadata
    input_ports: List[str] = field(default_factory=list)  # Data sources
    output_ports: List[str] = field(default_factory=list)  # Consumers
    
    # Metrics
    total_documents: int = 0
    total_size_bytes: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Discovery
    tags: List[str] = field(default_factory=list)
    schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainOwnership:
    """Domain ownership and accountability"""
    domain: DocumentDomain
    owner: str
    team: List[str]
    responsibilities: List[str]
    data_products: List[str] = field(default_factory=list)


# ============================================================================
# Data Mesh Layer
# ============================================================================

class DocumentDataMesh:
    """
    Data Mesh implementation for document management
    Enables domain-driven document organization and governance
    """
    
    def __init__(self):
        self.document_store = get_document_store()
        self._data_products: Dict[str, DocumentDataProduct] = {}
        self._domain_owners: Dict[DocumentDomain, DomainOwnership] = {}
        
        # Initialize default domain ownerships
        self._initialize_domains()
    
    def _initialize_domains(self):
        """Initialize default domain ownerships"""
        
        domains = {
            DocumentDomain.CUSTOMER: DomainOwnership(
                domain=DocumentDomain.CUSTOMER,
                owner="customer_success_team",
                team=["cs_manager", "kyc_analyst"],
                responsibilities=[
                    "Customer identity documents",
                    "KYC/AML documentation",
                    "Customer communications"
                ]
            ),
            DocumentDomain.COMPLIANCE: DomainOwnership(
                domain=DocumentDomain.COMPLIANCE,
                owner="compliance_officer",
                team=["compliance_analyst", "regulatory_specialist"],
                responsibilities=[
                    "Regulatory filings",
                    "Compliance reports",
                    "Audit documentation"
                ]
            ),
            DocumentDomain.FINANCE: DomainOwnership(
                domain=DocumentDomain.FINANCE,
                owner="cfo",
                team=["finance_manager", "accountant"],
                responsibilities=[
                    "Financial statements",
                    "Invoices and receipts",
                    "Tax documents"
                ]
            ),
            DocumentDomain.OPERATIONS: DomainOwnership(
                domain=DocumentDomain.OPERATIONS,
                owner="operations_manager",
                team=["ops_lead", "process_analyst"],
                responsibilities=[
                    "Policies and procedures",
                    "Training materials",
                    "Meeting minutes"
                ]
            ),
            DocumentDomain.LEGAL: DomainOwnership(
                domain=DocumentDomain.LEGAL,
                owner="general_counsel",
                team=["legal_counsel", "contracts_manager"],
                responsibilities=[
                    "Contracts and agreements",
                    "Legal opinions",
                    "Terms and conditions"
                ]
            ),
            DocumentDomain.RISK: DomainOwnership(
                domain=DocumentDomain.RISK,
                owner="risk_manager",
                team=["risk_analyst", "security_specialist"],
                responsibilities=[
                    "Risk assessments",
                    "Security policies",
                    "Incident reports"
                ]
            ),
            DocumentDomain.TECHNOLOGY: DomainOwnership(
                domain=DocumentDomain.TECHNOLOGY,
                owner="cto",
                team=["tech_lead", "architect"],
                responsibilities=[
                    "Technical specifications",
                    "Architecture documents",
                    "API documentation"
                ]
            )
        }
        
        self._domain_owners = domains
    
    async def create_data_product(
        self,
        domain: DocumentDomain,
        product_name: str,
        description: str,
        quality_level: DataProductQuality = DataProductQuality.RAW
    ) -> DocumentDataProduct:
        """Create a new document data product"""
        
        # Check domain ownership
        domain_owner = self._domain_owners.get(domain)
        if not domain_owner:
            raise ValueError(f"Domain {domain} has no owner assigned")
        
        # Generate product ID
        product_id = f"DP-{domain.value.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create data product
        product = DocumentDataProduct(
            product_id=product_id,
            domain=domain,
            product_name=product_name,
            description=description,
            owner=domain_owner.owner,
            quality_level=quality_level
        )
        
        # Register product
        self._data_products[product_id] = product
        domain_owner.data_products.append(product_id)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='data_mesh',
            event_type='data_product_created',
            event_data={
                'product_id': product_id,
                'domain': domain,
                'product_name': product_name,
                'owner': product.owner,
                'quality_level': quality_level
            },
            aggregate_id=product_id
        )
        
        return product
    
    async def add_document_to_product(
        self,
        product_id: str,
        document_id: str
    ) -> DocumentDataProduct:
        """Add a document to a data product"""
        
        product = self._data_products.get(product_id)
        if not product:
            raise ValueError(f"Data product {product_id} not found")
        
        document = await self.document_store.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Add document to product
        if document_id not in product.document_ids:
            product.document_ids.append(document_id)
            product.total_documents += 1
            
            # Update document with product reference
            document.data_product_id = product_id
            document.domain = product.domain.value
            
            # Update metrics
            latest_version = document.versions[-1]
            product.total_size_bytes += latest_version.file_size_bytes
            product.last_updated = datetime.utcnow()
            
            # Publish event
            kafka_store = get_production_kafka_store()
            await kafka_store.append_event(
                entity='data_mesh',
                event_type='document_added_to_product',
                event_data={
                    'product_id': product_id,
                    'document_id': document_id,
                    'domain': product.domain
                },
                aggregate_id=product_id
            )
        
        return product
    
    async def get_domain_catalog(
        self,
        domain: DocumentDomain
    ) -> Dict[str, Any]:
        """Get catalog of data products for a domain"""
        
        domain_owner = self._domain_owners.get(domain)
        if not domain_owner:
            return {}
        
        products = [
            self._data_products[pid]
            for pid in domain_owner.data_products
            if pid in self._data_products
        ]
        
        return {
            'domain': domain,
            'owner': domain_owner.owner,
            'team': domain_owner.team,
            'responsibilities': domain_owner.responsibilities,
            'data_products': [
                {
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'description': p.description,
                    'quality_level': p.quality_level,
                    'total_documents': p.total_documents,
                    'total_size_mb': round(p.total_size_bytes / (1024 * 1024), 2),
                    'last_updated': p.last_updated.isoformat()
                }
                for p in products
            ]
        }
    
    async def discover_data_products(
        self,
        search_query: Optional[str] = None,
        domain: Optional[DocumentDomain] = None,
        quality_level: Optional[DataProductQuality] = None,
        tags: Optional[List[str]] = None
    ) -> List[DocumentDataProduct]:
        """Discover data products across the mesh"""
        
        results = list(self._data_products.values())
        
        # Filter by domain
        if domain:
            results = [p for p in results if p.domain == domain]
        
        # Filter by quality level
        if quality_level:
            results = [p for p in results if p.quality_level == quality_level]
        
        # Filter by tags
        if tags:
            results = [
                p for p in results 
                if any(tag in p.tags for tag in tags)
            ]
        
        # Search in name and description
        if search_query:
            query_lower = search_query.lower()
            results = [
                p for p in results
                if (query_lower in p.product_name.lower() or
                    query_lower in p.description.lower())
            ]
        
        return results
    
    async def promote_quality_level(
        self,
        product_id: str,
        new_quality: DataProductQuality
    ) -> DocumentDataProduct:
        """Promote a data product to higher quality level"""
        
        product = self._data_products.get(product_id)
        if not product:
            raise ValueError(f"Data product {product_id} not found")
        
        quality_levels = [
            DataProductQuality.RAW,
            DataProductQuality.BRONZE,
            DataProductQuality.SILVER,
            DataProductQuality.GOLD
        ]
        
        current_idx = quality_levels.index(product.quality_level)
        new_idx = quality_levels.index(new_quality)
        
        if new_idx <= current_idx:
            raise ValueError(f"Cannot downgrade quality from {product.quality_level} to {new_quality}")
        
        old_quality = product.quality_level
        product.quality_level = new_quality
        product.last_updated = datetime.utcnow()
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='data_mesh',
            event_type='quality_level_promoted',
            event_data={
                'product_id': product_id,
                'old_quality': old_quality,
                'new_quality': new_quality
            },
            aggregate_id=product_id
        )
        
        return product
    
    async def get_mesh_overview(self) -> Dict[str, Any]:
        """Get overview of the entire document data mesh"""
        
        total_products = len(self._data_products)
        total_documents = sum(p.total_documents for p in self._data_products.values())
        total_size = sum(p.total_size_bytes for p in self._data_products.values())
        
        by_domain = {}
        for domain in DocumentDomain:
            products = [p for p in self._data_products.values() if p.domain == domain]
            by_domain[domain.value] = {
                'products': len(products),
                'documents': sum(p.total_documents for p in products),
                'owner': self._domain_owners.get(domain).owner if domain in self._domain_owners else None
            }
        
        by_quality = {}
        for quality in DataProductQuality:
            products = [p for p in self._data_products.values() if p.quality_level == quality]
            by_quality[quality.value] = len(products)
        
        return {
            'total_data_products': total_products,
            'total_documents': total_documents,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_domain': by_domain,
            'by_quality': by_quality,
            'domains': len(self._domain_owners)
        }


# Global mesh instance
_data_mesh: Optional[DocumentDataMesh] = None

def get_document_data_mesh() -> DocumentDataMesh:
    """Get the singleton document data mesh instance"""
    global _data_mesh
    if _data_mesh is None:
        _data_mesh = DocumentDataMesh()
    return _data_mesh
