"""Semantic Deduplication (SemDeDup) for Training Data"""
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class SemDeDup:
    """Semantic deduplication using embeddings."""
    
    def __init__(self, similarity_threshold: float = 0.95, embedding_model: str = "text-embedding-3-small"):
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        logger.info(f"SemDeDup initialized with threshold={similarity_threshold}")
    
    async def deduplicate(
        self,
        examples: List[Dict[str, Any]],
        embedding_function=None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Deduplicate examples using semantic similarity.
        
        Args:
            examples: List of training examples
            embedding_function: Function to generate embeddings (optional)
        
        Returns:
            Tuple of (deduplicated_examples, statistics)
        """
        if not examples:
            return [], {"original_count": 0, "deduplicated_count": 0, "reduction_rate": 0.0}
        
        logger.info(f"Starting deduplication of {len(examples)} examples")
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(examples, embedding_function)
        
        # Compute similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find duplicates
        keep_indices = self._find_unique_indices(similarity_matrix)
        
        # Filter examples
        deduplicated = [examples[i] for i in keep_indices]
        
        stats = {
            "original_count": len(examples),
            "deduplicated_count": len(deduplicated),
            "reduction_rate": 1.0 - (len(deduplicated) / len(examples)),
            "duplicates_removed": len(examples) - len(deduplicated)
        }
        
        logger.info(
            f"Deduplication complete: {stats['original_count']} → {stats['deduplicated_count']} "
            f"({stats['reduction_rate']:.1%} reduction)"
        )
        
        return deduplicated, stats
    
    async def _generate_embeddings(
        self,
        examples: List[Dict[str, Any]],
        embedding_function=None
    ) -> np.ndarray:
        """Generate embeddings for examples."""
        
        embeddings = []
        
        for i, example in enumerate(examples):
            # Create text representation
            text = self._example_to_text(example)
            
            # Check cache
            if text in self.embeddings_cache:
                embedding = self.embeddings_cache[text]
            else:
                # Generate embedding
                if embedding_function:
                    embedding = await embedding_function(text)
                else:
                    embedding = self._default_embedding(text)
                
                self.embeddings_cache[text] = embedding
            
            embeddings.append(embedding)
            
            if (i + 1) % 100 == 0:
                logger.debug(f"Generated {i + 1}/{len(examples)} embeddings")
        
        return np.array(embeddings)
    
    def _example_to_text(self, example: Dict[str, Any]) -> str:
        """Convert example to text for embedding."""
        
        # Combine context, tools, and reasoning
        parts = []
        
        # Context
        context = example.get("context", {})
        if context:
            context_str = " ".join(f"{k}:{v}" for k, v in context.items())
            parts.append(f"Context: {context_str}")
        
        # Tools available
        tools = example.get("tools_available", [])
        if tools:
            tool_names = [t.get("name", "") for t in tools]
            parts.append(f"Tools: {', '.join(tool_names)}")
        
        # Tool selected
        tool_selected = example.get("tool_selected", "")
        if tool_selected:
            parts.append(f"Selected: {tool_selected}")
        
        # Reasoning
        reasoning = example.get("reasoning", "")
        if reasoning:
            parts.append(f"Reasoning: {reasoning}")
        
        return " | ".join(parts)
    
    def _default_embedding(self, text: str) -> np.ndarray:
        """Generate a simple embedding (for testing without API)."""
        # Simple hash-based embedding for testing
        # In production, use OpenAI embeddings API
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float array
        embedding = np.frombuffer(hash_bytes, dtype=np.uint8).astype(float)
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        # Pad or truncate to 1536 dimensions (OpenAI embedding size)
        if len(embedding) < 1536:
            embedding = np.pad(embedding, (0, 1536 - len(embedding)))
        else:
            embedding = embedding[:1536]
        
        return embedding
    
    def _find_unique_indices(self, similarity_matrix: np.ndarray) -> List[int]:
        """Find indices of unique examples."""
        
        n = len(similarity_matrix)
        keep = [True] * n
        
        for i in range(n):
            if not keep[i]:
                continue
            
            for j in range(i + 1, n):
                if not keep[j]:
                    continue
                
                # Check similarity
                if similarity_matrix[i, j] >= self.similarity_threshold:
                    # Mark j as duplicate
                    keep[j] = False
        
        # Return indices of examples to keep
        return [i for i in range(n) if keep[i]]
    
    def clear_cache(self) -> None:
        """Clear embeddings cache."""
        self.embeddings_cache.clear()
        logger.debug("Cleared embeddings cache")
    
    def get_cache_size(self) -> int:
        """Get size of embeddings cache."""
        return len(self.embeddings_cache)


class OpenAISemDeDup(SemDeDup):
    """SemDeDup using OpenAI embeddings API."""
    
    def __init__(self, api_key: str, similarity_threshold: float = 0.95):
        super().__init__(similarity_threshold)
        self.api_key = api_key
        logger.info("OpenAISemDeDup initialized")
    
    async def _generate_embeddings(
        self,
        examples: List[Dict[str, Any]],
        embedding_function=None
    ) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            texts = [self._example_to_text(ex) for ex in examples]
            
            # Batch API calls (max 2048 texts per call)
            batch_size = 2048
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Generated embeddings for batch {i//batch_size + 1}")
            
            return np.array(all_embeddings)
            
        except Exception as e:
            logger.warning(f"Failed to use OpenAI embeddings: {e}, falling back to default")
            return await super()._generate_embeddings(examples, embedding_function)
