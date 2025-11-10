"""
ML Model Monitoring API
Track model performance, drift, and metrics
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from ultracore.ml_models.scoring_engine import (
    get_scoring_engine,
    get_model_monitor,
    ModelType
)
from ultracore.ml_models.registry.model_registry import get_model_registry

router = APIRouter()


class ScoreRequest(BaseModel):
    model_type: ModelType
    input_data: dict
    cache_key: Optional[str] = None


class BatchScoreRequest(BaseModel):
    model_type: ModelType
    inputs: List[dict]


class GroundTruthRequest(BaseModel):
    prediction_id: str
    actual_outcome: any


@router.post('/score')
async def score(request: ScoreRequest):
    '''
    Real-time ML scoring
    
    Low-latency inference with caching
    '''
    engine = get_scoring_engine()
    
    result = await engine.score(
        model_type=request.model_type,
        input_data=request.input_data,
        cache_key=request.cache_key
    )
    
    return result


@router.post('/batch-score')
async def batch_score(request: BatchScoreRequest):
    '''
    Batch scoring for multiple inputs
    
    Processes predictions concurrently
    '''
    engine = get_scoring_engine()
    
    results = await engine.batch_score(
        model_type=request.model_type,
        inputs=request.inputs
    )
    
    return {'results': results}


@router.get('/performance')
async def get_performance():
    '''Get model performance metrics'''
    engine = get_scoring_engine()
    
    return {
        'latency_metrics': engine.get_performance_metrics(),
        'cache_stats': engine.get_cache_stats()
    }


@router.get('/models/{model_type}/accuracy')
async def get_model_accuracy(model_type: ModelType):
    '''Get model accuracy metrics'''
    monitor = get_model_monitor()
    
    accuracy = await monitor.calculate_accuracy(model_type)
    
    return accuracy


@router.get('/models/{model_type}/drift')
async def detect_model_drift(model_type: ModelType):
    '''
    Detect model drift
    
    Alerts when model performance degrades
    '''
    monitor = get_model_monitor()
    
    drift = await monitor.detect_drift(model_type)
    
    return drift


@router.post('/ground-truth')
async def log_ground_truth(request: GroundTruthRequest):
    '''
    Log actual outcome for accuracy tracking
    
    Essential for model monitoring
    '''
    monitor = get_model_monitor()
    
    await monitor.log_ground_truth(
        prediction_id=request.prediction_id,
        actual_outcome=request.actual_outcome
    )
    
    return {'success': True}


@router.get('/registry/models')
async def list_models():
    '''List all registered models'''
    registry = get_model_registry()
    
    return {'models': list(registry.models.keys())}


@router.get('/registry/models/{model_id}')
async def get_model_versions(model_id: str):
    '''Get all versions of a model'''
    registry = get_model_registry()
    
    metrics = registry.get_model_metrics(model_id)
    
    return {'model_id': model_id, 'versions': metrics}


@router.post('/registry/models/{model_id}/ab-test')
async def start_ab_test(
    model_id: str,
    champion_version: str,
    challenger_version: str,
    challenger_traffic: float = 10.0
):
    '''
    Start A/B test between two model versions
    
    Champion gets majority traffic, challenger gets test traffic
    '''
    registry = get_model_registry()
    
    registry.ab_test(
        model_id=model_id,
        champion_version=champion_version,
        challenger_version=challenger_version,
        challenger_traffic=challenger_traffic
    )
    
    return {
        'ab_test_started': True,
        'champion': f'{champion_version} ({100-challenger_traffic}%)',
        'challenger': f'{challenger_version} ({challenger_traffic}%)'
    }


@router.post('/registry/models/{model_id}/promote')
async def promote_winner(model_id: str, winning_version: str):
    '''Promote A/B test winner to 100% traffic'''
    registry = get_model_registry()
    
    registry.promote_winner(model_id, winning_version)
    
    return {'winner_promoted': True, 'version': winning_version}


@router.post('/registry/models/{model_id}/rollback')
async def rollback_model(model_id: str, target_version: str):
    '''Rollback to previous model version'''
    registry = get_model_registry()
    
    registry.rollback(model_id, target_version)
    
    return {'rollback_complete': True, 'version': target_version}
