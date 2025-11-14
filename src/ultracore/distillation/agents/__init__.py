"""Distillation Agents"""
from .data_curator import DataCuratorAgent
from .model_trainer import ModelTrainerAgent
from .evaluator import EvaluationAgent

__all__ = [
    'DataCuratorAgent',
    'ModelTrainerAgent',
    'EvaluationAgent',
]
