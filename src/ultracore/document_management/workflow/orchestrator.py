"""
Agentic Document Processing Workflow
Autonomous agents orchestrate document processing

MCP-based: Each agent is a microservice with specific responsibility
"""
from typing import Dict, Optional
from enum import Enum

from ultracore.document_management.storage.document_storage import (
    Document, DocumentStatus, get_storage_service
)
from ultracore.document_management.ocr.ocr_service import OCRService
from ultracore.document_management.classification.classifier import DocumentClassificationService
from ultracore.document_management.extraction.data_extractor import DataExtractionService
from ultracore.document_management.fraud_detection.fraud_detector import FraudDetectionService
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class AgentType(str, Enum):
    OCR_AGENT = 'OCR_AGENT'
    CLASSIFICATION_AGENT = 'CLASSIFICATION_AGENT'
    EXTRACTION_AGENT = 'EXTRACTION_AGENT'
    FRAUD_DETECTION_AGENT = 'FRAUD_DETECTION_AGENT'
    VERIFICATION_AGENT = 'VERIFICATION_AGENT'
    APPROVAL_AGENT = 'APPROVAL_AGENT'


class DocumentProcessingAgent:
    """
    Base class for document processing agents
    
    MCP Pattern: Each agent is autonomous and event-driven
    """
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.is_active = True
    
    async def process(self, document_id: str, context: Dict) -> Dict:
        """Process document (override in subclass)"""
        raise NotImplementedError


class OCRAgent(DocumentProcessingAgent):
    """Agent responsible for OCR processing"""
    
    def __init__(self):
        super().__init__(AgentType.OCR_AGENT)
    
    async def process(self, document_id: str, context: Dict) -> Dict:
        """Run OCR on document"""
        storage = get_storage_service()
        document = storage.get_document(document_id)
        
        # Update status
        await storage.update_document_status(document_id, DocumentStatus.PROCESSING)
        
        # Run OCR
        ocr_result = await OCRService.process_document(document)
        
        return {
            'agent': self.agent_type.value,
            'status': 'completed',
            'ocr_text': ocr_result['text'],
            'confidence': ocr_result['confidence']
        }


class ClassificationAgent(DocumentProcessingAgent):
    """Agent responsible for document classification"""
    
    def __init__(self):
        super().__init__(AgentType.CLASSIFICATION_AGENT)
    
    async def process(self, document_id: str, context: Dict) -> Dict:
        """Classify document type"""
        storage = get_storage_service()
        document = storage.get_document(document_id)
        ocr_text = context.get('ocr_text', '')
        
        # Run classification
        classification_result = await DocumentClassificationService.classify_document(
            document, ocr_text
        )
        
        await storage.update_document_status(document_id, DocumentStatus.CLASSIFIED)
        
        return {
            'agent': self.agent_type.value,
            'status': 'completed',
            'predicted_type': classification_result['predicted_type'],
            'confidence': classification_result['confidence']
        }


class ExtractionAgent(DocumentProcessingAgent):
    """Agent responsible for data extraction"""
    
    def __init__(self):
        super().__init__(AgentType.EXTRACTION_AGENT)
    
    async def process(self, document_id: str, context: Dict) -> Dict:
        """Extract structured data"""
        storage = get_storage_service()
        document = storage.get_document(document_id)
        ocr_text = context.get('ocr_text', '')
        document_type = context.get('predicted_type', document.document_type.value)
        
        # Run extraction
        extracted_data = await DataExtractionService.extract_data(
            document, ocr_text, document_type
        )
        
        await storage.update_document_status(
            document_id, DocumentStatus.EXTRACTED, extracted_data
        )
        
        return {
            'agent': self.agent_type.value,
            'status': 'completed',
            'extracted_data': extracted_data
        }


class FraudDetectionAgent(DocumentProcessingAgent):
    """Agent responsible for fraud detection"""
    
    def __init__(self):
        super().__init__(AgentType.FRAUD_DETECTION_AGENT)
    
    async def process(self, document_id: str, context: Dict) -> Dict:
        """Detect fraud"""
        storage = get_storage_service()
        document = storage.get_document(document_id)
        extracted_data = context.get('extracted_data', {})
        
        # Run fraud detection
        fraud_result = await FraudDetectionService.detect_fraud(document, extracted_data)
        
        # Update document with fraud score
        document.fraud_score = fraud_result['fraud_score']
        
        return {
            'agent': self.agent_type.value,
            'status': 'completed',
            'fraud_score': fraud_result['fraud_score'],
            'risk_level': fraud_result['risk_level'],
            'action': fraud_result['recommended_action']
        }


class WorkflowOrchestrator:
    """
    Orchestrate document processing workflow
    
    Agentic: Agents work autonomously, coordinated by events
    """
    
    def __init__(self):
        self.agents = {
            AgentType.OCR_AGENT: OCRAgent(),
            AgentType.CLASSIFICATION_AGENT: ClassificationAgent(),
            AgentType.EXTRACTION_AGENT: ExtractionAgent(),
            AgentType.FRAUD_DETECTION_AGENT: FraudDetectionAgent()
        }
    
    async def process_document(self, document_id: str) -> Dict:
        """
        Process document through complete pipeline
        
        Pipeline: Upload → OCR → Classification → Extraction → Fraud Detection → Verification
        """
        context = {}
        results = []
        
        # Stage 1: OCR
        ocr_result = await self.agents[AgentType.OCR_AGENT].process(document_id, context)
        results.append(ocr_result)
        context.update(ocr_result)
        
        # Stage 2: Classification
        classification_result = await self.agents[AgentType.CLASSIFICATION_AGENT].process(
            document_id, context
        )
        results.append(classification_result)
        context.update(classification_result)
        
        # Stage 3: Extraction
        extraction_result = await self.agents[AgentType.EXTRACTION_AGENT].process(
            document_id, context
        )
        results.append(extraction_result)
        context.update(extraction_result)
        
        # Stage 4: Fraud Detection
        fraud_result = await self.agents[AgentType.FRAUD_DETECTION_AGENT].process(
            document_id, context
        )
        results.append(fraud_result)
        context.update(fraud_result)
        
        # Publish workflow completion
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='document_management',
            event_type='workflow_completed',
            event_data={
                'document_id': document_id,
                'pipeline_stages': len(results),
                'final_status': fraud_result['action'],
                'completed_at': datetime.utcnow().isoformat()
            },
            aggregate_id=document_id
        )
        
        return {
            'document_id': document_id,
            'status': 'completed',
            'stages': results,
            'final_action': fraud_result['action']
        }
    
    async def handle_event(self, event_type: str, event_data: Dict):
        """
        Event-driven processing
        
        Listens to Kafka events and triggers appropriate agents
        """
        if event_type == 'trigger_ocr':
            document_id = event_data['document_id']
            await self.agents[AgentType.OCR_AGENT].process(document_id, {})
        
        elif event_type == 'trigger_classification':
            document_id = event_data['document_id']
            context = {'ocr_text': event_data.get('ocr_text', '')}
            await self.agents[AgentType.CLASSIFICATION_AGENT].process(document_id, context)
        
        # ... handle other event types


# Global orchestrator
_orchestrator: Optional[WorkflowOrchestrator] = None


def get_orchestrator() -> WorkflowOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator
