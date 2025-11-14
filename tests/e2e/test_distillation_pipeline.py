"""End-to-End Test for Tool Calling Distillation"""
import pytest
from ultracore.distillation import (
    AgentDecisionLogger,
    DataCuratorAgent,
    ModelTrainerAgent,
    EvaluationAgent,
    SemDeDup,
    CombinedOptimizer
)


@pytest.mark.asyncio
async def test_complete_distillation_pipeline():
    """Test complete distillation pipeline."""
    
    # Step 1: Log decisions
    logger = AgentDecisionLogger()
    
    for i in range(200):
        await logger.log_decision(
            agent_id="customer_agent",
            context={"customer_id": f"cust_{i}"},
            tools_available=[
                {"name": "check_balance"},
                {"name": "transfer_funds"}
            ],
            tool_selected="check_balance" if i % 2 == 0 else "transfer_funds",
            reasoning=f"Customer request {i}",
            confidence=0.9
        )
    
    raw_decisions = logger.get_history()
    assert len(raw_decisions) == 200
    
    # Step 2: Curate data
    curator = DataCuratorAgent()
    curator_result = await curator.act(
        await curator.decide(
            await curator.perceive({"raw_decisions": raw_decisions})
        )
    )
    
    assert curator_result["status"] == "curated"
    curated_data = curator_result["curated_data"]
    assert len(curated_data) < len(raw_decisions)  # Should be deduplicated
    
    # Step 3: Train model
    trainer = ModelTrainerAgent()
    trainer_result = await trainer.act(
        await trainer.decide(
            await trainer.perceive({
                "training_data": curated_data,
                "teacher_model": "gpt-4"
            })
        )
    )
    
    assert trainer_result["status"] in ["deployed", "retraining"]
    
    # Step 4: Evaluate
    evaluator = EvaluationAgent()
    eval_result = await evaluator.act(
        await evaluator.decide(
            await evaluator.perceive({
                "recent_decisions": raw_decisions[:50]
            })
        )
    )
    
    assert "metrics" in eval_result
    
    print("\n=== Distillation Pipeline Complete ===")
    print(f"Raw decisions: {len(raw_decisions)}")
    print(f"Curated: {len(curated_data)} ({curator_result['stats']['deduplication_rate']:.1%} reduction)")
    print(f"Model status: {trainer_result['status']}")
    print(f"Evaluation: {eval_result['metrics']}")
