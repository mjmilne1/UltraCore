"""
UltraCore Customer Management - Graph Database

Graph operations for customer relationships:
- Relationship management (create, query, traverse)
- Beneficial ownership resolution
- Network analysis
- Fraud ring detection
- Community detection
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from decimal import Decimal
from collections import defaultdict, deque
import networkx as nx

from ultracore.customers.core.customer_models import (
    Customer, CustomerRelationship, RelationshipType
)


# ============================================================================
# Graph Data Structures
# ============================================================================

@dataclass
class GraphNode:
    """Node in customer graph"""
    node_id: str  # customer_id
    node_type: str  # CUSTOMER, COMPANY, TRUST, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.node_id == other.node_id


@dataclass
class GraphEdge:
    """Edge in customer graph"""
    edge_id: str  # relationship_id
    from_node: str  # customer_id
    to_node: str  # customer_id
    edge_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: Decimal = Decimal('1.0')
    bidirectional: bool = False


@dataclass
class GraphPath:
    """Path through graph"""
    nodes: List[str] = field(default_factory=list)
    edges: List[str] = field(default_factory=list)
    total_weight: Decimal = Decimal('0.00')
    path_length: int = 0


@dataclass
class BeneficialOwner:
    """Beneficial owner discovered through graph traversal"""
    customer_id: str
    ownership_percentage: Decimal
    control_percentage: Decimal
    path: GraphPath
    direct: bool = False
    ultimate: bool = False


# ============================================================================
# Customer Graph Manager
# ============================================================================

class CustomerGraph:
    """
    Graph database for customer relationships
    
    Implements graph operations similar to Neo4j:
    - Cypher-like queries
    - Path finding
    - Centrality metrics
    - Community detection
    - Fraud ring detection
    """
    
    def __init__(self):
        # Graph storage (in-memory for now, would use Neo4j/TigerGraph in production)
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        
        # Adjacency lists for efficient traversal
        self.outgoing: Dict[str, List[str]] = defaultdict(list)  # node -> [edge_ids]
        self.incoming: Dict[str, List[str]] = defaultdict(list)  # node -> [edge_ids]
        
        # NetworkX graph for advanced algorithms
        self.nx_graph = nx.DiGraph()
        
        # Relationship type index
        self.relationship_index: Dict[RelationshipType, Set[str]] = defaultdict(set)
    
    def add_node(self, customer: Customer) -> GraphNode:
        """Add customer as node"""
        
        node = GraphNode(
            node_id=customer.customer_id,
            node_type=customer.customer_type.value,
            properties={
                'name': customer.get_full_name(),
                'segment': customer.segment.value,
                'risk_rating': customer.risk_rating.value,
                'status': customer.customer_status.value,
                'created_at': customer.created_at.isoformat()
            }
        )
        
        self.nodes[node.node_id] = node
        self.nx_graph.add_node(node.node_id, **node.properties)
        
        return node
    
    def add_edge(self, relationship: CustomerRelationship) -> GraphEdge:
        """Add relationship as edge"""
        
        edge = GraphEdge(
            edge_id=relationship.relationship_id,
            from_node=relationship.from_customer_id,
            to_node=relationship.to_customer_id,
            edge_type=relationship.relationship_type,
            properties={
                'ownership_percentage': float(relationship.ownership_percentage) if relationship.ownership_percentage else 0.0,
                'control_percentage': float(relationship.control_percentage) if relationship.control_percentage else 0.0,
                'verified': relationship.verified,
                'active': relationship.is_active
            },
            weight=relationship.strength,
            bidirectional=relationship.bidirectional
        )
        
        self.edges[edge.edge_id] = edge
        
        # Update adjacency lists
        self.outgoing[edge.from_node].append(edge.edge_id)
        self.incoming[edge.to_node].append(edge.edge_id)
        
        # Update NetworkX graph
        self.nx_graph.add_edge(
            edge.from_node,
            edge.to_node,
            edge_id=edge.edge_id,
            relationship_type=edge.edge_type.value,
            weight=float(edge.weight),
            **edge.properties
        )
        
        if edge.bidirectional:
            self.nx_graph.add_edge(
                edge.to_node,
                edge.from_node,
                edge_id=edge.edge_id,
                relationship_type=edge.edge_type.value,
                weight=float(edge.weight),
                **edge.properties
            )
        
        # Index by relationship type
        self.relationship_index[edge.edge_type].add(edge.edge_id)
        
        return edge
    
    def get_neighbors(
        self,
        customer_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        direction: str = "OUTGOING"  # OUTGOING, INCOMING, BOTH
    ) -> List[str]:
        """Get neighboring customers"""
        
        neighbors = []
        
        if direction in ["OUTGOING", "BOTH"]:
            for edge_id in self.outgoing.get(customer_id, []):
                edge = self.edges[edge_id]
                if not relationship_types or edge.edge_type in relationship_types:
                    neighbors.append(edge.to_node)
        
        if direction in ["INCOMING", "BOTH"]:
            for edge_id in self.incoming.get(customer_id, []):
                edge = self.edges[edge_id]
                if not relationship_types or edge.edge_type in relationship_types:
                    neighbors.append(edge.from_node)
        
        return list(set(neighbors))  # Remove duplicates
    
    def find_path(
        self,
        from_customer_id: str,
        to_customer_id: str,
        max_depth: int = 5
    ) -> Optional[GraphPath]:
        """
        Find shortest path between two customers
        BFS algorithm
        """
        
        if from_customer_id == to_customer_id:
            return GraphPath(nodes=[from_customer_id], path_length=0)
        
        if from_customer_id not in self.nodes or to_customer_id not in self.nodes:
            return None
        
        # BFS
        queue = deque([(from_customer_id, [from_customer_id], [])])
        visited = {from_customer_id}
        
        while queue:
            current, path_nodes, path_edges = queue.popleft()
            
            if len(path_nodes) > max_depth:
                continue
            
            # Get outgoing edges
            for edge_id in self.outgoing.get(current, []):
                edge = self.edges[edge_id]
                next_node = edge.to_node
                
                if next_node == to_customer_id:
                    # Found path!
                    final_path = GraphPath(
                        nodes=path_nodes + [next_node],
                        edges=path_edges + [edge_id],
                        path_length=len(path_nodes)
                    )
                    # Calculate total weight
                    final_path.total_weight = sum(
                        self.edges[eid].weight for eid in final_path.edges
                    )
                    return final_path
                
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((
                        next_node,
                        path_nodes + [next_node],
                        path_edges + [edge_id]
                    ))
        
        return None  # No path found
    
    def find_beneficial_owners(
        self,
        customer_id: str,
        ownership_threshold: Decimal = Decimal('25.0'),  # 25% ownership
        max_depth: int = 5
    ) -> List[BeneficialOwner]:
        """
        Find beneficial owners through ownership chains
        Critical for AML/CTF compliance (AUSTRAC)
        """
        
        beneficial_owners = []
        
        # Track visited to avoid cycles
        visited = set()
        
        def traverse_ownership(
            current_id: str,
            cumulative_ownership: Decimal,
            path: GraphPath,
            depth: int
        ):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Check if this is a beneficial owner
            if cumulative_ownership >= ownership_threshold:
                # Check if this is a natural person (ultimate beneficial owner)
                node = self.nodes.get(current_id)
                is_ultimate = node and node.node_type == "INDIVIDUAL"
                
                beneficial_owners.append(BeneficialOwner(
                    customer_id=current_id,
                    ownership_percentage=cumulative_ownership,
                    control_percentage=cumulative_ownership,  # Simplified
                    path=path,
                    direct=(depth == 1),
                    ultimate=is_ultimate
                ))
            
            # Traverse ownership edges
            for edge_id in self.incoming.get(current_id, []):
                edge = self.edges[edge_id]
                
                if edge.edge_type in [
                    RelationshipType.SHAREHOLDER,
                    RelationshipType.BENEFICIAL_OWNER,
                    RelationshipType.TRUSTEE
                ]:
                    ownership_pct = edge.properties.get('ownership_percentage', 0.0)
                    if ownership_pct > 0:
                        # Calculate cascading ownership
                        new_ownership = cumulative_ownership * (Decimal(str(ownership_pct)) / Decimal('100'))
                        
                        new_path = GraphPath(
                            nodes=path.nodes + [edge.from_node],
                            edges=path.edges + [edge_id],
                            path_length=path.path_length + 1
                        )
                        
                        traverse_ownership(
                            edge.from_node,
                            new_ownership,
                            new_path,
                            depth + 1
                        )
        
        # Start traversal
        initial_path = GraphPath(nodes=[customer_id], path_length=0)
        traverse_ownership(customer_id, Decimal('100.0'), initial_path, 0)
        
        return beneficial_owners
    
    def find_connected_component(
        self,
        customer_id: str,
        max_size: int = 100
    ) -> Set[str]:
        """
        Find all customers connected to this customer
        Useful for fraud ring detection
        """
        
        if customer_id not in self.nodes:
            return set()
        
        connected = {customer_id}
        queue = deque([customer_id])
        
        while queue and len(connected) < max_size:
            current = queue.popleft()
            
            # Get all neighbors (both directions)
            neighbors = self.get_neighbors(current, direction="BOTH")
            
            for neighbor in neighbors:
                if neighbor not in connected:
                    connected.add(neighbor)
                    queue.append(neighbor)
        
        return connected
    
    def calculate_centrality(
        self,
        customer_id: str,
        centrality_type: str = "DEGREE"
    ) -> Decimal:
        """
        Calculate customer's centrality in network
        
        Types:
        - DEGREE: Number of connections
        - BETWEENNESS: How often on shortest paths
        - CLOSENESS: Average distance to others
        - EIGENVECTOR: Influence based on neighbors
        """
        
        if customer_id not in self.nx_graph:
            return Decimal('0.0')
        
        if centrality_type == "DEGREE":
            return Decimal(str(self.nx_graph.degree(customer_id)))
        
        elif centrality_type == "BETWEENNESS":
            centrality = nx.betweenness_centrality(self.nx_graph)
            return Decimal(str(centrality.get(customer_id, 0.0)))
        
        elif centrality_type == "CLOSENESS":
            if nx.is_strongly_connected(self.nx_graph):
                centrality = nx.closeness_centrality(self.nx_graph)
                return Decimal(str(centrality.get(customer_id, 0.0)))
            return Decimal('0.0')
        
        elif centrality_type == "EIGENVECTOR":
            try:
                centrality = nx.eigenvector_centrality(self.nx_graph, max_iter=100)
                return Decimal(str(centrality.get(customer_id, 0.0)))
            except:
                return Decimal('0.0')
        
        return Decimal('0.0')
    
    def detect_communities(
        self,
        algorithm: str = "LOUVAIN"
    ) -> Dict[str, int]:
        """
        Detect communities in customer network
        Useful for: segmentation, fraud detection, marketing
        """
        
        # Convert to undirected for community detection
        undirected = self.nx_graph.to_undirected()
        
        if algorithm == "LOUVAIN":
            # Louvain community detection (requires python-louvain package)
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(undirected)
                return communities
            except ImportError:
                pass
        
        # Fallback: simple connected components
        communities = {}
        for i, component in enumerate(nx.connected_components(undirected)):
            for node in component:
                communities[node] = i
        
        return communities
    
    def find_fraud_rings(
        self,
        min_ring_size: int = 3,
        suspicious_patterns: Optional[List[RelationshipType]] = None
    ) -> List[Set[str]]:
        """
        Detect potential fraud rings
        
        Looks for:
        - Tightly connected groups
        - Unusual relationship patterns
        - High transaction overlap
        """
        
        if suspicious_patterns is None:
            suspicious_patterns = [
                RelationshipType.GUARANTOR,
                RelationshipType.CO_APPLICANT,
                RelationshipType.AUTHORISED_REP
            ]
        
        # Find communities
        communities = self.detect_communities()
        
        # Group customers by community
        community_groups = defaultdict(set)
        for customer_id, community_id in communities.items():
            community_groups[community_id].add(customer_id)
        
        # Analyze communities for suspicious patterns
        fraud_rings = []
        
        for community_id, members in community_groups.items():
            if len(members) < min_ring_size:
                continue
            
            # Count suspicious relationship types
            suspicious_count = 0
            for member in members:
                for edge_id in self.outgoing.get(member, []) + self.incoming.get(member, []):
                    edge = self.edges[edge_id]
                    if edge.edge_type in suspicious_patterns:
                        suspicious_count += 1
            
            # High ratio of suspicious relationships = potential fraud ring
            total_edges = sum(len(self.outgoing.get(m, [])) for m in members)
            if total_edges > 0:
                suspicious_ratio = suspicious_count / total_edges
                if suspicious_ratio > 0.5:  # More than 50% suspicious
                    fraud_rings.append(members)
        
        return fraud_rings
    
    def get_relationship_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get summary of customer's relationships"""
        
        summary = {
            'total_relationships': 0,
            'by_type': {},
            'outgoing': 0,
            'incoming': 0,
            'degree_centrality': 0.0,
            'has_beneficial_owners': False
        }
        
        if customer_id not in self.nodes:
            return summary
        
        outgoing_count = len(self.outgoing.get(customer_id, []))
        incoming_count = len(self.incoming.get(customer_id, []))
        
        summary['total_relationships'] = outgoing_count + incoming_count
        summary['outgoing'] = outgoing_count
        summary['incoming'] = incoming_count
        summary['degree_centrality'] = float(self.calculate_centrality(customer_id))
        
        # Count by type
        for edge_id in self.outgoing.get(customer_id, []) + self.incoming.get(customer_id, []):
            edge = self.edges[edge_id]
            rel_type = edge.edge_type.value
            summary['by_type'][rel_type] = summary['by_type'].get(rel_type, 0) + 1
        
        # Check for beneficial owners
        beneficial_owners = self.find_beneficial_owners(customer_id)
        summary['has_beneficial_owners'] = len(beneficial_owners) > 0
        summary['beneficial_owner_count'] = len(beneficial_owners)
        
        return summary


# ============================================================================
# Global Graph Instance
# ============================================================================

_customer_graph: Optional[CustomerGraph] = None

def get_customer_graph() -> CustomerGraph:
    """Get singleton customer graph"""
    global _customer_graph
    if _customer_graph is None:
        _customer_graph = CustomerGraph()
    return _customer_graph
