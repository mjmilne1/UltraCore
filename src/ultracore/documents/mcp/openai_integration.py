"""
UltraCore Document Management - OpenAI Integration

OpenAI function calling integration for document management:
- Document search and retrieval
- Workflow execution
- Agent management
- Natural language document operations
- GPT-4 powered assistance
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date
from decimal import Decimal
import openai

from ultracore.documents.document_core import (
    Document, DocumentStore, get_document_store,
    DocumentType, DocumentStatus, DocumentMetadata, ClassificationLevel
)
from ultracore.documents.mesh.data_mesh import (
    get_document_data_mesh, DocumentDomain, DataProductQuality
)
from ultracore.documents.ml.ml_pipeline import get_ml_pipeline
from ultracore.documents.ai.agentic_core import (
    get_agent_registry, Task, TaskPriority, AgentType
)
from ultracore.documents.ai.workflow_orchestrator import get_workflow_orchestrator
from ultracore.events.kafka_store import get_production_kafka_store


# ============================================================================
# OpenAI Function Definitions
# ============================================================================

DOCUMENT_FUNCTIONS = [
    {
        'name': 'search_documents',
        'description': 'Search for documents using filters like type, classification, tags, or free-text query',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Free-text search query'
                },
                'document_type': {
                    'type': 'string',
                    'enum': [dt.value for dt in DocumentType],
                    'description': 'Filter by document type'
                },
                'classification': {
                    'type': 'string',
                    'enum': [cl.value for cl in ClassificationLevel],
                    'description': 'Filter by security classification'
                },
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Filter by tags'
                },
                'domain': {
                    'type': 'string',
                    'enum': [d.value for d in DocumentDomain],
                    'description': 'Filter by business domain'
                }
            }
        }
    },
    {
        'name': 'get_document',
        'description': 'Retrieve detailed information about a specific document by ID',
        'parameters': {
            'type': 'object',
            'properties': {
                'document_id': {
                    'type': 'string',
                    'description': 'The unique document identifier'
                }
            },
            'required': ['document_id']
        }
    },
    {
        'name': 'create_document',
        'description': 'Create a new document in the system',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'Document title'
                },
                'document_type': {
                    'type': 'string',
                    'enum': [dt.value for dt in DocumentType],
                    'description': 'Type of document'
                },
                'classification': {
                    'type': 'string',
                    'enum': [cl.value for cl in ClassificationLevel],
                    'description': 'Security classification'
                },
                'owner': {
                    'type': 'string',
                    'description': 'Document owner user ID'
                },
                'department': {
                    'type': 'string',
                    'description': 'Owning department'
                },
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Document tags'
                },
                'content': {
                    'type': 'string',
                    'description': 'Document content (text)'
                }
            },
            'required': ['title', 'document_type', 'owner', 'department']
        }
    },
    {
        'name': 'process_document',
        'description': 'Run ML pipeline to classify, extract entities, and enrich a document',
        'parameters': {
            'type': 'object',
            'properties': {
                'document_id': {
                    'type': 'string',
                    'description': 'Document ID to process'
                }
            },
            'required': ['document_id']
        }
    },
    {
        'name': 'execute_workflow',
        'description': 'Execute a document processing workflow',
        'parameters': {
            'type': 'object',
            'properties': {
                'workflow_id': {
                    'type': 'string',
                    'enum': ['standard_processing', 'compliance_review', 'kyc_verification', 'financial_processing'],
                    'description': 'Workflow to execute'
                },
                'document_id': {
                    'type': 'string',
                    'description': 'Document to process'
                },
                'priority': {
                    'type': 'string',
                    'enum': ['CRITICAL', 'HIGH', 'NORMAL', 'LOW'],
                    'description': 'Task priority'
                }
            },
            'required': ['workflow_id', 'document_id']
        }
    },
    {
        'name': 'get_document_statistics',
        'description': 'Get comprehensive statistics about the document system',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    {
        'name': 'get_data_mesh_overview',
        'description': 'Get overview of data mesh architecture and data products',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    {
        'name': 'discover_data_products',
        'description': 'Search for data products in the data mesh',
        'parameters': {
            'type': 'object',
            'properties': {
                'search_query': {
                    'type': 'string',
                    'description': 'Search query for data products'
                },
                'domain': {
                    'type': 'string',
                    'enum': [d.value for d in DocumentDomain],
                    'description': 'Filter by domain'
                },
                'quality_level': {
                    'type': 'string',
                    'enum': [q.value for q in DataProductQuality],
                    'description': 'Filter by quality level'
                }
            }
        }
    },
    {
        'name': 'get_agent_status',
        'description': 'Get status and metrics for all autonomous agents',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    {
        'name': 'get_workflow_status',
        'description': 'Get status of a specific workflow execution',
        'parameters': {
            'type': 'object',
            'properties': {
                'execution_id': {
                    'type': 'string',
                    'description': 'Workflow execution ID'
                }
            },
            'required': ['execution_id']
        }
    },
    {
        'name': 'list_workflows',
        'description': 'List all available document processing workflows',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    }
]


# ============================================================================
# OpenAI Integration Service
# ============================================================================

class OpenAIDocumentService:
    """
    OpenAI integration service for document management
    Provides GPT-4 powered natural language interface
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.document_store = get_document_store()
        self.data_mesh = get_document_data_mesh()
        self.ml_pipeline = get_ml_pipeline()
        self.agent_registry = get_agent_registry()
        self.workflow_orchestrator = get_workflow_orchestrator()
        
        # Set OpenAI API key
        if api_key:
            openai.api_key = api_key
        
        # Function registry
        self.functions: Dict[str, Callable] = {
            'search_documents': self.search_documents,
            'get_document': self.get_document,
            'create_document': self.create_document,
            'process_document': self.process_document,
            'execute_workflow': self.execute_workflow,
            'get_document_statistics': self.get_document_statistics,
            'get_data_mesh_overview': self.get_data_mesh_overview,
            'discover_data_products': self.discover_data_products,
            'get_agent_status': self.get_agent_status,
            'get_workflow_status': self.get_workflow_status,
            'list_workflows': self.list_workflows
        }
        
        # Initialize agents
        asyncio.create_task(self._initialize_agents())
    
    async def _initialize_agents(self):
        """Initialize all autonomous agents"""
        from ultracore.documents.ai.agentic_core import (
            ClassifierAgent, ValidatorAgent, EnricherAgent,
            RouterAgent, ComplianceAgent
        )
        
        agents = [
            ClassifierAgent(),
            ValidatorAgent(),
            EnricherAgent(),
            RouterAgent(),
            ComplianceAgent()
        ]
        
        for agent in agents:
            await self.agent_registry.register_agent(agent)
    
    # ========================================================================
    # Function Implementations
    # ========================================================================
    
    async def search_documents(
        self,
        query: Optional[str] = None,
        document_type: Optional[str] = None,
        classification: Optional[str] = None,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for documents"""
        
        # Convert string enums to actual enums
        doc_type_enum = DocumentType(document_type) if document_type else None
        class_enum = ClassificationLevel(classification) if classification else None
        
        documents = await self.document_store.search_documents(
            query=query,
            document_type=doc_type_enum,
            classification=class_enum,
            tags=tags,
            domain=domain
        )
        
        return {
            'count': len(documents),
            'documents': [
                {
                    'document_id': doc.document_id,
                    'title': doc.metadata.title,
                    'type': doc.metadata.document_type,
                    'classification': doc.metadata.classification,
                    'owner': doc.metadata.owner,
                    'department': doc.metadata.department,
                    'status': doc.status,
                    'created_at': doc.created_at.isoformat(),
                    'tags': doc.metadata.tags,
                    'domain': doc.domain
                }
                for doc in documents
            ]
        }
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get detailed document information"""
        
        document = await self.document_store.get_document(document_id)
        if not document:
            return {'error': f'Document {document_id} not found'}
        
        return {
            'document_id': document.document_id,
            'metadata': {
                'title': document.metadata.title,
                'type': document.metadata.document_type,
                'classification': document.metadata.classification,
                'owner': document.metadata.owner,
                'department': document.metadata.department,
                'tags': document.metadata.tags
            },
            'current_version': document.current_version,
            'status': document.status,
            'processing_status': document.processing_status,
            'extracted_text': document.extracted_text[:500] + '...' if document.extracted_text and len(document.extracted_text) > 500 else document.extracted_text,
            'extracted_entities': document.extracted_entities,
            'classification_confidence': document.classification_confidence,
            'sentiment_score': document.sentiment_score,
            'key_phrases': document.key_phrases,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
            'domain': document.domain,
            'data_product_id': document.data_product_id
        }
    
    async def create_document(
        self,
        title: str,
        document_type: str,
        classification: str,
        owner: str,
        department: str,
        tags: Optional[List[str]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new document"""
        
        metadata = DocumentMetadata(
            title=title,
            document_type=DocumentType(document_type),
            classification=ClassificationLevel(classification),
            owner=owner,
            department=department,
            tags=tags or []
        )
        
        # Create document with simulated content
        content_bytes = (content or f"Document: {title}").encode('utf-8')
        storage_path = f"/storage/docs/{datetime.now(timezone.utc).strftime('%Y%m%d')}/{title.replace(' ', '_')}.txt"
        
        document = await self.document_store.create_document(
            content=content_bytes,
            metadata=metadata,
            created_by=owner,
            storage_path=storage_path
        )
        
        return {
            'document_id': document.document_id,
            'title': document.metadata.title,
            'status': document.status,
            'created_at': document.created_at.isoformat(),
            'message': 'Document created successfully'
        }
    
    async def process_document(self, document_id: str) -> Dict[str, Any]:
        """Process document through ML pipeline"""
        
        document = await self.ml_pipeline.process_document(document_id)
        
        return {
            'document_id': document_id,
            'processing_status': document.processing_status,
            'classification_confidence': document.classification_confidence,
            'entities_extracted': len(document.extracted_entities),
            'sentiment_score': document.sentiment_score,
            'key_phrases_count': len(document.key_phrases),
            'message': 'Document processed successfully'
        }
    
    async def execute_workflow(
        self,
        workflow_id: str,
        document_id: str,
        priority: str = 'NORMAL'
    ) -> Dict[str, Any]:
        """Execute a document workflow"""
        
        priority_enum = TaskPriority(priority)
        
        execution = await self.workflow_orchestrator.execute_workflow(
            workflow_id=workflow_id,
            document_id=document_id,
            priority=priority_enum
        )
        
        return {
            'execution_id': execution.execution_id,
            'workflow_id': execution.workflow_id,
            'document_id': execution.document_id,
            'status': execution.status,
            'current_step': execution.current_step,
            'started_at': execution.started_at.isoformat(),
            'message': 'Workflow execution started'
        }
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get comprehensive document statistics"""
        
        stats = await self.document_store.get_statistics()
        mesh_overview = await self.data_mesh.get_mesh_overview()
        agent_metrics = await self.agent_registry.get_all_metrics()
        workflow_stats = await self.workflow_orchestrator.get_workflow_stats()
        
        return {
            'documents': stats,
            'data_mesh': mesh_overview,
            'agents': agent_metrics,
            'workflows': workflow_stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def get_data_mesh_overview(self) -> Dict[str, Any]:
        """Get data mesh overview"""
        return await self.data_mesh.get_mesh_overview()
    
    async def discover_data_products(
        self,
        search_query: Optional[str] = None,
        domain: Optional[str] = None,
        quality_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Discover data products"""
        
        domain_enum = DocumentDomain(domain) if domain else None
        quality_enum = DataProductQuality(quality_level) if quality_level else None
        
        products = await self.data_mesh.discover_data_products(
            search_query=search_query,
            domain=domain_enum,
            quality_level=quality_enum
        )
        
        return {
            'count': len(products),
            'data_products': [
                {
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'description': p.description,
                    'domain': p.domain.value,
                    'quality_level': p.quality_level.value,
                    'owner': p.owner,
                    'total_documents': p.total_documents,
                    'total_size_mb': round(p.total_size_bytes / (1024 * 1024), 2)
                }
                for p in products
            ]
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get all agent metrics"""
        return await self.agent_registry.get_all_metrics()
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        
        execution = await self.workflow_orchestrator.get_execution(execution_id)
        if not execution:
            return {'error': f'Execution {execution_id} not found'}
        
        return {
            'execution_id': execution.execution_id,
            'workflow_id': execution.workflow_id,
            'document_id': execution.document_id,
            'status': execution.status,
            'current_step': execution.current_step,
            'step_results': execution.step_results,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message
        }
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List all available workflows"""
        
        workflows = await self.workflow_orchestrator.list_workflows()
        
        return {
            'count': len(workflows),
            'workflows': [
                {
                    'workflow_id': w.workflow_id,
                    'name': w.name,
                    'description': w.description,
                    'trigger': w.trigger,
                    'steps': len(w.steps),
                    'active': w.active
                }
                for w in workflows
            ]
        }
    
    # ========================================================================
    # OpenAI Chat Completion with Function Calling
    # ========================================================================
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4-turbo-preview"
    ) -> Dict[str, Any]:
        """
        Chat with OpenAI using function calling for document operations
        """
        
        try:
            # Call OpenAI with function definitions
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=model,
                messages=messages,
                functions=DOCUMENT_FUNCTIONS,
                function_call="auto"
            )
            
            message = response.choices[0].message
            
            # Check if function was called
            if message.get('function_call'):
                function_name = message['function_call']['name']
                function_args = json.loads(message['function_call']['arguments'])
                
                # Execute the function
                if function_name in self.functions:
                    function_result = await self.functions[function_name](**function_args)
                    
                    # Add function result to messages and get final response
                    messages.append({
                        'role': 'assistant',
                        'content': None,
                        'function_call': message['function_call']
                    })
                    messages.append({
                        'role': 'function',
                        'name': function_name,
                        'content': json.dumps(function_result)
                    })
                    
                    # Get final response
                    final_response = await asyncio.to_thread(
                        openai.ChatCompletion.create,
                        model=model,
                        messages=messages
                    )
                    
                    return {
                        'response': final_response.choices[0].message['content'],
                        'function_called': function_name,
                        'function_result': function_result
                    }
            
            # No function call, return direct response
            return {
                'response': message['content'],
                'function_called': None
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Error processing chat request'
            }
    
    async def ask(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Simple question-answering interface
        """
        
        system_message = {
            'role': 'system',
            'content': '''You are an AI assistant for UltraCore Document Management System.
            
You have access to a comprehensive document management system with:
- Document storage and versioning
- Data mesh architecture with domain-driven data products
- ML pipeline for classification, NER, OCR, sentiment analysis
- Autonomous agents for document processing
- Workflow orchestration

You can search documents, create documents, process them through ML pipelines,
execute workflows, and provide insights about the document system.

Always be helpful, precise, and provide actionable information.'''
        }
        
        messages = [system_message]
        
        # Add context if provided
        if context:
            messages.append({
                'role': 'system',
                'content': f'Additional context: {json.dumps(context)}'
            })
        
        # Add user question
        messages.append({
            'role': 'user',
            'content': question
        })
        
        result = await self.chat(messages)
        
        return result.get('response', 'Error: No response generated')


# ============================================================================
# Global Service Instance
# ============================================================================

_openai_service: Optional[OpenAIDocumentService] = None

def get_openai_service(api_key: Optional[str] = None) -> OpenAIDocumentService:
    """Get the singleton OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIDocumentService(api_key=api_key)
    return _openai_service


# ============================================================================
# Usage Examples
# ============================================================================

async def example_usage():
    \"\"\"
    Example usage of OpenAI integration
    \"\"\"
    
    service = get_openai_service(api_key='your-openai-api-key')
    
    # Example 1: Natural language document search
    response = await service.ask(
        "Find all compliance reports from the last quarter"
    )
    print(response)
    
    # Example 2: Create and process document
    response = await service.ask(
        "Create a new invoice document for ABC Corp and process it through the ML pipeline"
    )
    print(response)
    
    # Example 3: Get system overview
    response = await service.ask(
        "Give me an overview of the document system - how many documents, agents, and workflows?"
    )
    print(response)
    
    # Example 4: Execute workflow
    response = await service.ask(
        "Run the compliance review workflow on document DOC-20250111120000"
    )
    print(response)
