"""Cluster and Retrieve (CaR) for Representative Example Selection"""
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
import logging

logger = logging.getLogger(__name__)


class CaR:
    """Cluster and Retrieve representative examples."""
    
    def __init__(
        self,
        n_clusters: int = 10,
        clustering_method: str = "kmeans",
        examples_per_cluster: int = 5
    ):
        self.n_clusters = n_clusters
        self.clustering_method = clustering_method
        self.examples_per_cluster = examples_per_cluster
        logger.info(
            f"CaR initialized: {n_clusters} clusters, "
            f"{examples_per_cluster} examples per cluster"
        )
    
    async def select_representatives(
        self,
        examples: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Select representative examples using clustering.
        
        Args:
            examples: List of training examples
            embeddings: Embeddings for examples
        
        Returns:
            Tuple of (representative_examples, statistics)
        """
        if not examples or len(examples) == 0:
            return [], {"cluster_count": 0, "selected_count": 0}
        
        logger.info(f"Selecting representatives from {len(examples)} examples")
        
        # Perform clustering
        cluster_labels, cluster_centers = await self._cluster(embeddings)
        
        # Select representatives from each cluster
        representatives = []
        cluster_stats = []
        
        for cluster_id in range(self.n_clusters):
            # Get examples in this cluster
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            # Select representatives
            cluster_reps = self._select_from_cluster(
                examples,
                embeddings,
                cluster_indices,
                cluster_centers[cluster_id]
            )
            
            representatives.extend(cluster_reps)
            
            cluster_stats.append({
                "cluster_id": cluster_id,
                "size": len(cluster_indices),
                "representatives": len(cluster_reps)
            })
        
        # Calculate statistics
        stats = {
            "original_count": len(examples),
            "cluster_count": self.n_clusters,
            "selected_count": len(representatives),
            "selection_rate": len(representatives) / len(examples),
            "cluster_stats": cluster_stats,
            "silhouette_score": self._calculate_silhouette(embeddings, cluster_labels)
        }
        
        logger.info(
            f"Selected {stats['selected_count']} representatives "
            f"from {stats['cluster_count']} clusters "
            f"(silhouette={stats['silhouette_score']:.3f})"
        )
        
        return representatives, stats
    
    async def _cluster(self, embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Perform clustering on embeddings."""
        
        if self.clustering_method == "kmeans":
            return self._kmeans_cluster(embeddings)
        elif self.clustering_method == "dbscan":
            return self._dbscan_cluster(embeddings)
        else:
            raise ValueError(f"Unknown clustering method: {self.clustering_method}")
    
    def _kmeans_cluster(self, embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Perform K-means clustering."""
        
        # Adjust n_clusters if needed
        n_clusters = min(self.n_clusters, len(embeddings))
        
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        
        labels = kmeans.fit_predict(embeddings)
        centers = kmeans.cluster_centers_
        
        logger.debug(f"K-means clustering complete: {n_clusters} clusters")
        
        return labels, centers
    
    def _dbscan_cluster(self, embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Perform DBSCAN clustering."""
        
        dbscan = DBSCAN(
            eps=0.3,
            min_samples=5,
            metric='cosine'
        )
        
        labels = dbscan.fit_predict(embeddings)
        
        # Calculate cluster centers
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # Remove noise label
        
        centers = []
        for label in sorted(unique_labels):
            cluster_points = embeddings[labels == label]
            center = cluster_points.mean(axis=0)
            centers.append(center)
        
        centers = np.array(centers)
        
        logger.debug(f"DBSCAN clustering complete: {len(centers)} clusters")
        
        return labels, centers
    
    def _select_from_cluster(
        self,
        examples: List[Dict[str, Any]],
        embeddings: np.ndarray,
        cluster_indices: np.ndarray,
        cluster_center: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Select representative examples from a cluster."""
        
        # Get embeddings for this cluster
        cluster_embeddings = embeddings[cluster_indices]
        
        # Calculate distances to cluster center
        distances = np.linalg.norm(cluster_embeddings - cluster_center, axis=1)
        
        # Select examples closest to center
        n_select = min(self.examples_per_cluster, len(cluster_indices))
        closest_indices = np.argsort(distances)[:n_select]
        
        # Get original indices
        selected_indices = cluster_indices[closest_indices]
        
        # Add representativeness score
        representatives = []
        for idx, dist in zip(selected_indices, distances[closest_indices]):
            example = examples[idx].copy()
            example["cluster_id"] = int(cluster_indices[0])  # Use first index as cluster ID
            example["representativeness_score"] = float(1.0 / (1.0 + dist))
            representatives.append(example)
        
        return representatives
    
    def _calculate_silhouette(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> float:
        """Calculate silhouette score for clustering quality."""
        
        try:
            # Need at least 2 clusters
            unique_labels = len(set(labels))
            if unique_labels < 2 or len(embeddings) < 2:
                return 0.0
            
            score = silhouette_score(embeddings, labels)
            return float(score)
        except Exception as e:
            logger.warning(f"Failed to calculate silhouette score: {e}")
            return 0.0
    
    def optimize_n_clusters(
        self,
        embeddings: np.ndarray,
        min_clusters: int = 2,
        max_clusters: int = 20
    ) -> int:
        """Find optimal number of clusters using elbow method."""
        
        inertias = []
        silhouettes = []
        
        for n in range(min_clusters, min(max_clusters + 1, len(embeddings))):
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            inertias.append(kmeans.inertia_)
            
            if n >= 2:
                silhouettes.append(silhouette_score(embeddings, labels))
            else:
                silhouettes.append(0.0)
        
        # Find elbow point (maximum silhouette score)
        optimal_n = min_clusters + np.argmax(silhouettes)
        
        logger.info(f"Optimal number of clusters: {optimal_n}")
        
        return optimal_n


class AdaptiveCaR(CaR):
    """CaR with adaptive cluster count."""
    
    def __init__(self, examples_per_cluster: int = 5):
        super().__init__(n_clusters=10, examples_per_cluster=examples_per_cluster)
        logger.info("AdaptiveCaR initialized")
    
    async def select_representatives(
        self,
        examples: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Select representatives with adaptive clustering."""
        
        # Optimize number of clusters
        optimal_n = self.optimize_n_clusters(embeddings)
        self.n_clusters = optimal_n
        
        # Call parent method
        return await super().select_representatives(examples, embeddings)
