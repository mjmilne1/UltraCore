"""
Real-Time Scoring Engine
Low-latency ML model inference for production
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import asyncio
import time

from ultracore.ml_models.registry.model_registry import get_model_registry
from ultracore.ml_models.enhanced_pipeline import enhanced_ml
from ultracore.ml_models.additional_models import (
    AMLTransactionMonitor,
    CustomerLifetimeValue,
    ProductRecommendation,
    MarketMovementPrediction,
    MerchantRiskScoring,
    RealEstateValuation,
    CybersecurityThreatDetection,
    DocumentClassification,
    SentimentAnalysis,
    CashFlowForecasting
)


class ModelType(str, Enum):
    FRAUD_DETECTION = 'FRAUD_DETECTION'
    CREDIT_RISK = 'CREDIT_RISK'
    CHURN_PREDICTION = 'CHURN_PREDICTION'
    DEFAULT_PREDICTION = 'DEFAULT_PREDICTION'
    PORTFOLIO_OPTIMIZATION = 'PORTFOLIO_OPTIMIZATION'
    INSURANCE_FRAUD = 'INSURANCE_FRAUD'
    TRANSACTION_ANOMALY = 'TRANSACTION_ANOMALY'
    CUSTOMER_SEGMENTATION = 'CUSTOMER_SEGMENTATION'
    LOAN_APPROVAL = 'LOAN_APPROVAL'
    CARD_RISK = 'CARD_RISK'
    # New models
    AML_MONITORING = 'AML_MONITORING'
    CUSTOMER_LIFETIME_VALUE = 'CUSTOMER_LIFETIME_VALUE'
    PRODUCT_RECOMMENDATION = 'PRODUCT_RECOMMENDATION'
    MARKET_PREDICTION = 'MARKET_PREDICTION'
    MERCHANT_RISK = 'MERCHANT_RISK'
    PROPERTY_VALUATION = 'PROPERTY_VALUATION'
    CYBERSECURITY_THREAT = 'CYBERSECURITY_THREAT'
    DOCUMENT_CLASSIFICATION = 'DOCUMENT_CLASSIFICATION'
    SENTIMENT_ANALYSIS = 'SENTIMENT_ANALYSIS'
    CASHFLOW_FORECAST = 'CASHFLOW_FORECAST'


class FeatureStore:
    """
    Feature store for real-time feature retrieval
    
    Caches commonly used features for low-latency inference
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl: int = 300  # 5 minutes
    
    def get_customer_features(self, customer_id: str) -> Dict:
        """Get customer features for ML inference"""
        
        # Check cache
        cache_key = f'customer:{customer_id}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # In production: fetch from database/data warehouse
        features = {
            'customer_id': customer_id,
            'account_age_days': 365,
            'total_balance': 15000,
            'monthly_transactions': 45,
            'product_count': 3,
            'credit_score': 720,
            'average_transaction': 150,
            'last_transaction_days': 2,
            'has_loan': True,
            'has_investment': False,
            'has_insurance': False
        }
        
        # Cache features
        self.cache[cache_key] = features
        
        return features
    
    def get_transaction_features(self, transaction_data: Dict) -> Dict:
        """Extract features from transaction data"""
        
        return {
            'amount': transaction_data.get('amount', 0),
            'merchant_category': transaction_data.get('merchant_category', 'RETAIL'),
            'location': transaction_data.get('location', 'DOMESTIC'),
            'time_of_day': transaction_data.get('hour', 12),
            'day_of_week': transaction_data.get('day_of_week', 3),
            'is_international': 'international' in transaction_data.get('location', '').lower(),
            'unusual_time': transaction_data.get('hour', 12) < 6 or transaction_data.get('hour', 12) > 23
        }
    
    def get_loan_features(self, loan_data: Dict) -> Dict:
        """Extract features for loan scoring"""
        
        return {
            'loan_amount': loan_data.get('amount', 0),
            'annual_income': loan_data.get('annual_income', 50000),
            'employment_years': loan_data.get('employment_years', 3),
            'existing_debt': loan_data.get('existing_debt', 0),
            'dti_ratio': loan_data.get('existing_debt', 0) / max(loan_data.get('annual_income', 1), 1),
            'loan_to_income': loan_data.get('amount', 0) / max(loan_data.get('annual_income', 1), 1)
        }


class ModelInferenceCache:
    """
    Cache ML model predictions
    
    For features that don't change frequently (e.g., credit score)
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.ttl: Dict[ModelType, int] = {
            ModelType.CREDIT_RISK: 86400,  # 24 hours
            ModelType.CUSTOMER_LIFETIME_VALUE: 3600,  # 1 hour
            ModelType.CUSTOMER_SEGMENTATION: 3600,
            ModelType.FRAUD_DETECTION: 60,  # 1 minute (real-time)
        }
    
    def get(self, model_type: ModelType, key: str) -> Optional[Dict]:
        """Get cached prediction"""
        cache_key = f'{model_type.value}:{key}'
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            
            # Check if expired
            age = time.time() - cached['timestamp']
            ttl = self.ttl.get(model_type, 300)
            
            if age < ttl:
                return cached['prediction']
        
        return None
    
    def set(self, model_type: ModelType, key: str, prediction: Dict):
        """Cache prediction"""
        cache_key = f'{model_type.value}:{key}'
        
        self.cache[cache_key] = {
            'prediction': prediction,
            'timestamp': time.time()
        }


class ScoringEngine:
    """
    Real-Time ML Scoring Engine
    
    Low-latency model inference with caching and monitoring
    """
    
    def __init__(self):
        self.feature_store = FeatureStore()
        self.inference_cache = ModelInferenceCache()
        self.model_registry = get_model_registry()
        
        # Initialize model instances
        self.aml_monitor = AMLTransactionMonitor()
        self.clv_predictor = CustomerLifetimeValue()
        self.product_recommender = ProductRecommendation()
        self.market_predictor = MarketMovementPrediction()
        self.merchant_scorer = MerchantRiskScoring()
        self.property_valuator = RealEstateValuation()
        self.threat_detector = CybersecurityThreatDetection()
        self.doc_classifier = DocumentClassification()
        self.sentiment_analyzer = SentimentAnalysis()
        self.cashflow_forecaster = CashFlowForecasting()
        
        # Performance metrics
        self.inference_times: Dict[ModelType, List[float]] = {}
    
    async def score(
        self,
        model_type: ModelType,
        input_data: Dict,
        cache_key: Optional[str] = None
    ) -> Dict:
        """
        Score using specified model
        
        Returns prediction with metadata
        """
        
        start_time = time.time()
        
        # Check cache
        if cache_key:
            cached = self.inference_cache.get(model_type, cache_key)
            if cached:
                return {
                    **cached,
                    'cached': True,
                    'inference_time_ms': 0
                }
        
        # Route to appropriate model
        prediction = await self._route_inference(model_type, input_data)
        
        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000  # ms
        
        # Record metrics
        if model_type not in self.inference_times:
            self.inference_times[model_type] = []
        self.inference_times[model_type].append(inference_time)
        
        # Cache result
        if cache_key:
            self.inference_cache.set(model_type, cache_key, prediction)
        
        # Add metadata
        result = {
            **prediction,
            'model_type': model_type.value,
            'cached': False,
            'inference_time_ms': round(inference_time, 2),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return result
    
    async def _route_inference(self, model_type: ModelType, input_data: Dict) -> Dict:
        """Route to appropriate model"""
        
        if model_type == ModelType.FRAUD_DETECTION:
            return await enhanced_ml.detect_fraud(input_data)
        
        elif model_type == ModelType.CREDIT_RISK:
            return await enhanced_ml.assess_credit_risk(input_data)
        
        elif model_type == ModelType.CHURN_PREDICTION:
            return await enhanced_ml.predict_customer_churn(input_data)
        
        elif model_type == ModelType.DEFAULT_PREDICTION:
            return await enhanced_ml.predict_payment_default(input_data)
        
        elif model_type == ModelType.PORTFOLIO_OPTIMIZATION:
            return await enhanced_ml.optimize_investment_portfolio(input_data)
        
        elif model_type == ModelType.INSURANCE_FRAUD:
            return await enhanced_ml.detect_insurance_claim_fraud(input_data)
        
        elif model_type == ModelType.AML_MONITORING:
            return await self.aml_monitor.detect_suspicious_patterns(input_data.get('transactions', []))
        
        elif model_type == ModelType.CUSTOMER_LIFETIME_VALUE:
            return await self.clv_predictor.predict_clv(input_data)
        
        elif model_type == ModelType.PRODUCT_RECOMMENDATION:
            return {
                'recommendations': await self.product_recommender.recommend_products(
                    input_data.get('customer_id'),
                    input_data.get('customer_profile', {})
                )
            }
        
        elif model_type == ModelType.MARKET_PREDICTION:
            return await self.market_predictor.predict_market_trend(
                input_data.get('symbol'),
                input_data.get('timeframe', '1D')
            )
        
        elif model_type == ModelType.MERCHANT_RISK:
            return await self.merchant_scorer.score_merchant_risk(input_data)
        
        elif model_type == ModelType.PROPERTY_VALUATION:
            return await self.property_valuator.estimate_property_value(input_data)
        
        elif model_type == ModelType.CYBERSECURITY_THREAT:
            return await self.threat_detector.detect_threat(input_data.get('activity_log', []))
        
        elif model_type == ModelType.DOCUMENT_CLASSIFICATION:
            return await self.doc_classifier.classify_document(input_data.get('document_image', b''))
        
        elif model_type == ModelType.SENTIMENT_ANALYSIS:
            return await self.sentiment_analyzer.analyze_sentiment(input_data.get('feedback_text', ''))
        
        elif model_type == ModelType.CASHFLOW_FORECAST:
            return await self.cashflow_forecaster.forecast_cashflow(input_data.get('historical_data', []))
        
        else:
            raise ValueError(f'Unknown model type: {model_type}')
    
    async def batch_score(
        self,
        model_type: ModelType,
        inputs: List[Dict]
    ) -> List[Dict]:
        """
        Batch scoring for multiple inputs
        
        Processes multiple predictions concurrently
        """
        
        tasks = [
            self.score(model_type, input_data)
            for input_data in inputs
        ]
        
        results = await asyncio.gather(*tasks)
        
        return results
    
    def get_performance_metrics(self) -> Dict:
        """Get model performance metrics"""
        
        metrics = {}
        
        for model_type, times in self.inference_times.items():
            if times:
                metrics[model_type.value] = {
                    'count': len(times),
                    'avg_latency_ms': round(sum(times) / len(times), 2),
                    'p50_latency_ms': round(sorted(times)[len(times)//2], 2),
                    'p95_latency_ms': round(sorted(times)[int(len(times)*0.95)], 2),
                    'p99_latency_ms': round(sorted(times)[int(len(times)*0.99)], 2)
                }
        
        return metrics
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        
        return {
            'cached_predictions': len(self.inference_cache.cache),
            'cached_features': len(self.feature_store.cache)
        }


class ModelMonitor:
    """
    Monitor ML model performance in production
    
    Track accuracy, drift, latency
    """
    
    def __init__(self):
        self.predictions: Dict[ModelType, List[Dict]] = {}
        self.ground_truth: Dict[str, Any] = {}
    
    async def log_prediction(
        self,
        model_type: ModelType,
        prediction_id: str,
        prediction: Dict,
        input_data: Dict
    ):
        """Log prediction for monitoring"""
        
        if model_type not in self.predictions:
            self.predictions[model_type] = []
        
        self.predictions[model_type].append({
            'prediction_id': prediction_id,
            'prediction': prediction,
            'input_data': input_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    async def log_ground_truth(
        self,
        prediction_id: str,
        actual_outcome: Any
    ):
        """Log actual outcome for accuracy tracking"""
        
        self.ground_truth[prediction_id] = {
            'outcome': actual_outcome,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def calculate_accuracy(self, model_type: ModelType) -> Dict:
        """Calculate model accuracy"""
        
        predictions = self.predictions.get(model_type, [])
        
        correct = 0
        total = 0
        
        for pred in predictions:
            pred_id = pred['prediction_id']
            
            if pred_id in self.ground_truth:
                predicted = pred['prediction'].get('prediction')
                actual = self.ground_truth[pred_id]['outcome']
                
                if predicted == actual:
                    correct += 1
                
                total += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            'model_type': model_type.value,
            'accuracy': round(accuracy, 4),
            'total_predictions': len(predictions),
            'validated_predictions': total
        }
    
    async def detect_drift(self, model_type: ModelType) -> Dict:
        """
        Detect model drift
        
        Compare recent predictions to historical baseline
        """
        
        predictions = self.predictions.get(model_type, [])
        
        if len(predictions) < 100:
            return {
                'drift_detected': False,
                'message': 'Insufficient data for drift detection'
            }
        
        # Compare last 20% to first 80%
        split = int(len(predictions) * 0.8)
        baseline = predictions[:split]
        recent = predictions[split:]
        
        # Simple drift check: compare prediction distributions
        baseline_avg = sum(p['prediction'].get('score', 0) for p in baseline) / len(baseline)
        recent_avg = sum(p['prediction'].get('score', 0) for p in recent) / len(recent)
        
        drift_magnitude = abs(recent_avg - baseline_avg) / baseline_avg if baseline_avg > 0 else 0
        
        drift_detected = drift_magnitude > 0.2  # 20% change
        
        return {
            'model_type': model_type.value,
            'drift_detected': drift_detected,
            'drift_magnitude': round(drift_magnitude, 4),
            'baseline_avg': round(baseline_avg, 4),
            'recent_avg': round(recent_avg, 4),
            'action': 'RETRAIN_MODEL' if drift_detected else 'MONITOR'
        }


# Global instances
_scoring_engine: Optional[ScoringEngine] = None
_model_monitor: Optional[ModelMonitor] = None


def get_scoring_engine() -> ScoringEngine:
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ScoringEngine()
    return _scoring_engine


def get_model_monitor() -> ModelMonitor:
    global _model_monitor
    if _model_monitor is None:
        _model_monitor = ModelMonitor()
    return _model_monitor
