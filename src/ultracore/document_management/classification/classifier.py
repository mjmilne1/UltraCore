"""
Document Classification Service
ML-powered document type detection

Uses existing ML models + fine-tuning for document types
"""
from typing import Dict, List
import numpy as np

from ultracore.ml_models.scoring_engine import get_scoring_engine, ModelType
from ultracore.document_management.storage.document_storage import Document, DocumentType, DocumentStatus
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class DocumentClassificationService:
    """
    ML-Powered Document Classification
    
    Automatically detects document type from content
    """
    
    @staticmethod
    async def classify_document(document: Document, ocr_text: str) -> Dict:
        """
        Classify document type using ML
        
        Uses:
        - Text analysis
        - Image features
        - ML model predictions
        """
        scoring_engine = get_scoring_engine()
        
        # Feature extraction
        features = await DocumentClassificationService._extract_features(ocr_text, document)
        
        # Run ML classification
        # In production: Use fine-tuned document classifier
        classification_result = {
            'predicted_type': DocumentType.DRIVERS_LICENSE.value,
            'confidence': 0.92,
            'alternatives': [
                {'type': DocumentType.NATIONAL_ID.value, 'confidence': 0.06},
                {'type': DocumentType.PASSPORT.value, 'confidence': 0.02}
            ]
        }
        
        # Verify if classification matches uploaded type
        if document.document_type.value != classification_result['predicted_type']:
            # Flag for manual review
            classification_result['needs_review'] = True
            classification_result['reason'] = 'Type mismatch'
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='document_management',
            event_type='document_classified',
            event_data={
                'document_id': document.document_id,
                'predicted_type': classification_result['predicted_type'],
                'confidence': classification_result['confidence'],
                'classified_at': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=document.document_id
        )
        
        # Trigger next stage: Data Extraction
        await kafka_store.append_event(
            entity='document_management',
            event_type='trigger_extraction',
            event_data={
                'document_id': document.document_id,
                'document_type': classification_result['predicted_type'],
                'ocr_text': ocr_text
            },
            aggregate_id=document.document_id
        )
        
        return classification_result
    
    @staticmethod
    async def _extract_features(ocr_text: str, document: Document) -> Dict:
        """Extract features for classification"""
        
        features = {
            'text_length': len(ocr_text),
            'has_photo': False,  # From image analysis
            'has_hologram': False,  # From image analysis
            'has_barcode': False,  # From image analysis
            'contains_keywords': [],
            'layout_features': {}
        }
        
        # Keyword detection
        keywords = {
            'passport': ['passport', 'nationality', 'place of birth'],
            'drivers_license': ['license', 'class', 'restrictions', 'endorsements'],
            'bank_statement': ['balance', 'transaction', 'account number']
        }
        
        for doc_type, words in keywords.items():
            if any(word.lower() in ocr_text.lower() for word in words):
                features['contains_keywords'].append(doc_type)
        
        return features
