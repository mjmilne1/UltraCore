"""
UltraCore Document Management - REST API Server

FastAPI server exposing document management capabilities via REST API
Integrates with OpenAI for natural language operations
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ultracore.documents.mcp.openai_integration import get_openai_service


# ============================================================================
# Pydantic Models
# ============================================================================

class DocumentSearchRequest(BaseModel):
    query: Optional[str] = None
    document_type: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None
    domain: Optional[str] = None


class DocumentCreateRequest(BaseModel):
    title: str
    document_type: str
    classification: str
    owner: str
    department: str
    tags: Optional[List[str]] = None
    content: Optional[str] = None


class WorkflowExecuteRequest(BaseModel):
    workflow_id: str
    document_id: str
    priority: str = 'NORMAL'


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4-turbo-preview"


class AskRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="UltraCore Document Management API",
    description="AI-powered document management with data mesh, ML pipeline, and autonomous agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI service
openai_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global openai_service
    # Initialize with API key from environment or config
    openai_service = get_openai_service(api_key=None)  # Set API key as needed


# ============================================================================
# Document Endpoints
# ============================================================================

@app.post("/api/documents/search")
async def search_documents(request: DocumentSearchRequest):
    """Search for documents"""
    result = await openai_service.search_documents(
        query=request.query,
        document_type=request.document_type,
        classification=request.classification,
        tags=request.tags,
        domain=request.domain
    )
    return result


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get document by ID"""
    result = await openai_service.get_document(document_id)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result


@app.post("/api/documents/create")
async def create_document(request: DocumentCreateRequest):
    """Create a new document"""
    result = await openai_service.create_document(
        title=request.title,
        document_type=request.document_type,
        classification=request.classification,
        owner=request.owner,
        department=request.department,
        tags=request.tags,
        content=request.content
    )
    return result


@app.post("/api/documents/{document_id}/process")
async def process_document(document_id: str):
    """Process document through ML pipeline"""
    result = await openai_service.process_document(document_id)
    return result


@app.get("/api/documents/statistics")
async def get_statistics():
    """Get comprehensive system statistics"""
    result = await openai_service.get_document_statistics()
    return result


# ============================================================================
# Data Mesh Endpoints
# ============================================================================

@app.get("/api/data-mesh/overview")
async def get_data_mesh_overview():
    """Get data mesh overview"""
    result = await openai_service.get_data_mesh_overview()
    return result


@app.post("/api/data-mesh/discover")
async def discover_data_products(
    search_query: Optional[str] = None,
    domain: Optional[str] = None,
    quality_level: Optional[str] = None
):
    """Discover data products"""
    result = await openai_service.discover_data_products(
        search_query=search_query,
        domain=domain,
        quality_level=quality_level
    )
    return result


# ============================================================================
# Workflow Endpoints
# ============================================================================

@app.get("/api/workflows")
async def list_workflows():
    """List all available workflows"""
    result = await openai_service.list_workflows()
    return result


@app.post("/api/workflows/execute")
async def execute_workflow(request: WorkflowExecuteRequest):
    """Execute a workflow"""
    result = await openai_service.execute_workflow(
        workflow_id=request.workflow_id,
        document_id=request.document_id,
        priority=request.priority
    )
    return result


@app.get("/api/workflows/executions/{execution_id}")
async def get_workflow_status(execution_id: str):
    """Get workflow execution status"""
    result = await openai_service.get_workflow_status(execution_id)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return result


@app.get("/api/workflows/statistics")
async def get_workflow_statistics():
    """Get workflow statistics"""
    stats = await openai_service.get_document_statistics()
    return stats.get('workflows', {})


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    result = await openai_service.get_agent_status()
    return result


# ============================================================================
# AI/OpenAI Endpoints
# ============================================================================

@app.post("/api/ai/chat")
async def chat(request: ChatRequest):
    """Chat with OpenAI using function calling"""
    result = await openai_service.chat(
        messages=request.messages,
        model=request.model
    )
    return result


@app.post("/api/ai/ask")
async def ask(request: AskRequest):
    """Simple question-answering interface"""
    result = await openai_service.ask(
        question=request.question,
        context=request.context
    )
    return {'response': result}


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'UltraCore Document Management',
        'version': '1.0.0'
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'UltraCore Document Management API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health'
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
