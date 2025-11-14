"""Tool Calling Distillation System"""
from .events import (
    AgentDecisionEvent,
    AgentDecisionLogger,
    DecisionLoggerMixin,
    DecisionEventPublisher
)
from .data_products import (
    AgentDecisionHistoryProduct,
    DistillationTrainingDataProduct,
    DistilledModelMetricsProduct
)
from .optimization import (
    SemDeDup,
    OpenAISemDeDup,
    CaR,
    AdaptiveCaR,
    DSPyOptimizer,
    GEPAOptimizer,
    CombinedOptimizer
)
from .agents import (
    DataCuratorAgent,
    ModelTrainerAgent,
    EvaluationAgent
)

__all__ = [
    # Events
    'AgentDecisionEvent',
    'AgentDecisionLogger',
    'DecisionLoggerMixin',
    'DecisionEventPublisher',
    # Data Products
    'AgentDecisionHistoryProduct',
    'DistillationTrainingDataProduct',
    'DistilledModelMetricsProduct',
    # Optimization
    'SemDeDup',
    'OpenAISemDeDup',
    'CaR',
    'AdaptiveCaR',
    'DSPyOptimizer',
    'GEPAOptimizer',
    'CombinedOptimizer',
    # Agents
    'DataCuratorAgent',
    'ModelTrainerAgent',
    'EvaluationAgent',
]
