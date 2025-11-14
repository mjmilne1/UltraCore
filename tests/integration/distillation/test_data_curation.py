"""Tests for Data Curation (SemDeDup + CaR)"""
import pytest
import numpy as np
from ultracore.distillation.optimization import SemDeDup, CaR


@pytest.mark.asyncio
async def test_semdedup_basic():
    """Test semantic deduplication."""
    semdedup = SemDeDup(similarity_threshold=0.95)
    
    examples = [
        {"context": {"type": "balance"}, "tool_selected": "check_balance"},
        {"context": {"type": "balance"}, "tool_selected": "check_balance"},  # Duplicate
        {"context": {"type": "transfer"}, "tool_selected": "transfer_funds"},
    ]
    
    deduplicated, stats = await semdedup.deduplicate(examples)
    
    assert len(deduplicated) < len(examples)
    assert stats["reduction_rate"] > 0


@pytest.mark.asyncio
async def test_car_clustering():
    """Test cluster and retrieve."""
    car = CaR(n_clusters=2, examples_per_cluster=2)
    
    examples = [
        {"context": {"type": "balance"}, "tool_selected": "check_balance"},
        {"context": {"type": "balance"}, "tool_selected": "check_balance"},
        {"context": {"type": "transfer"}, "tool_selected": "transfer_funds"},
        {"context": {"type": "transfer"}, "tool_selected": "transfer_funds"},
    ]
    
    # Create simple embeddings
    embeddings = np.random.rand(len(examples), 128)
    
    representatives, stats = await car.select_representatives(examples, embeddings)
    
    assert len(representatives) <= len(examples)
    assert stats["cluster_count"] == 2
