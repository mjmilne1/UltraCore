"""
UltraCore Document Management - Workflow Orchestrator

Orchestrates multi-agent workflows for document processing:
- Workflow definition and execution
- Agent coordination
- Parallel and sequential execution
- Error handling and recovery
- Progress tracking
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import asyncio

from ultracore.documents.ai.agentic_core import (
    Agent, AgentType, Task, TaskPriority, TaskStatus,
    Workflow, WorkflowStep, get_agent_registry
)
from ultracore.documents.document_core import get_document_store
from ultracore.events.kafka_store import get_production_kafka_store


# ============================================================================
# Workflow Enums
# ============================================================================

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class WorkflowExecution:
    """Tracks execution of a workflow instance"""
    execution_id: str
    workflow_id: str
    document_id: str
    status: WorkflowStatus
    current_step: int = 0
    step_results: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ============================================================================
# Workflow Orchestrator
# ============================================================================

class WorkflowOrchestrator:
    """
    Orchestrates complex multi-agent workflows
    Coordinates multiple agents to process documents end-to-end
    """
    
    def __init__(self):
        self.agent_registry = get_agent_registry()
        self.document_store = get_document_store()
        self._workflows: Dict[str, Workflow] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        
        # Initialize default workflows
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """Initialize default document processing workflows"""
        
        # Standard Document Processing Workflow
        standard_workflow = Workflow(
            workflow_id="standard_processing",
            name="Standard Document Processing",
            description="Standard workflow for all documents",
            trigger="document_uploaded",
            steps=[
                WorkflowStep(
                    step_id="classify",
                    agent_type=AgentType.CLASSIFIER,
                    parallel=False
                ),
                WorkflowStep(
                    step_id="enrich",
                    agent_type=AgentType.ENRICHER,
                    input_from="classify",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="validate",
                    agent_type=AgentType.VALIDATOR,
                    input_from="enrich",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="route",
                    agent_type=AgentType.ROUTER,
                    input_from="validate",
                    parallel=False
                )
            ]
        )
        self._workflows[standard_workflow.workflow_id] = standard_workflow
        
        # Compliance Review Workflow
        compliance_workflow = Workflow(
            workflow_id="compliance_review",
            name="Compliance Review Workflow",
            description="Comprehensive compliance checking for regulatory documents",
            trigger="regulatory_document",
            steps=[
                WorkflowStep(
                    step_id="classify",
                    agent_type=AgentType.CLASSIFIER,
                    parallel=False
                ),
                WorkflowStep(
                    step_id="enrich",
                    agent_type=AgentType.ENRICHER,
                    input_from="classify",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="compliance",
                    agent_type=AgentType.COMPLIANCE,
                    input_from="enrich",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="validate",
                    agent_type=AgentType.VALIDATOR,
                    input_from="compliance",
                    parallel=False
                )
            ]
        )
        self._workflows[compliance_workflow.workflow_id] = compliance_workflow
        
        # KYC Verification Workflow
        kyc_workflow = Workflow(
            workflow_id="kyc_verification",
            name="KYC Verification Workflow",
            description="Identity verification for customer onboarding",
            trigger="identity_document",
            steps=[
                WorkflowStep(
                    step_id="classify",
                    agent_type=AgentType.CLASSIFIER,
                    parallel=False
                ),
                WorkflowStep(
                    step_id="enrich",
                    agent_type=AgentType.ENRICHER,
                    input_from="classify",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="validate",
                    agent_type=AgentType.VALIDATOR,
                    input_from="enrich",
                    parallel=False
                ),
                WorkflowStep(
                    step_id="compliance",
                    agent_type=AgentType.COMPLIANCE,
                    input_from="validate",
                    parallel=False
                )
            ]
        )
        self._workflows[kyc_workflow.workflow_id] = kyc_workflow
        
        # Financial Processing Workflow
        financial_workflow = Workflow(
            workflow_id="financial_processing",
            name="Financial Document Processing",
            description="Processing for invoices, receipts, statements",
            trigger="financial_document",
            steps=[
                WorkflowStep(
                    step_id="classify",
                    agent_type=AgentType.CLASSIFIER,
                    parallel=False
                ),
                WorkflowStep(
                    step_id="enrich",
                    agent_type=AgentType.ENRICHER,
                    input_from="classify",
                    parallel=True
                ),
                WorkflowStep(
                    step_id="validate",
                    agent_type=AgentType.VALIDATOR,
                    input_from="enrich",
                    parallel=True
                ),
                WorkflowStep(
                    step_id="route",
                    agent_type=AgentType.ROUTER,
                    input_from="validate",
                    parallel=False
                )
            ]
        )
        self._workflows[financial_workflow.workflow_id] = financial_workflow
    
    async def execute_workflow(
        self,
        workflow_id: str,
        document_id: str,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> WorkflowExecution:
        """Execute a workflow for a document"""
        
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow.active:
            raise ValueError(f"Workflow {workflow_id} is not active")
        
        # Create execution instance
        execution_id = f"EXEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{document_id}"
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            document_id=document_id,
            status=WorkflowStatus.RUNNING
        )
        
        self._executions[execution_id] = execution
        
        # Publish workflow started event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='workflows',
            event_type='workflow_started',
            event_data={
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'document_id': document_id,
                'steps': len(workflow.steps)
            },
            aggregate_id=execution_id
        )
        
        try:
            # Execute workflow steps
            await self._execute_steps(workflow, execution, priority)
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            # Publish completion event
            await kafka_store.append_event(
                entity='workflows',
                event_type='workflow_completed',
                event_data={
                    'execution_id': execution_id,
                    'workflow_id': workflow_id,
                    'document_id': document_id,
                    'duration_seconds': (execution.completed_at - execution.started_at).total_seconds()
                },
                aggregate_id=execution_id
            )
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            
            # Publish failure event
            await kafka_store.append_event(
                entity='workflows',
                event_type='workflow_failed',
                event_data={
                    'execution_id': execution_id,
                    'workflow_id': workflow_id,
                    'document_id': document_id,
                    'error': str(e)
                },
                aggregate_id=execution_id
            )
            
            raise
        
        return execution
    
    async def _execute_steps(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        priority: TaskPriority
    ):
        """Execute workflow steps sequentially or in parallel"""
        
        for i, step in enumerate(workflow.steps):
            execution.current_step = i
            
            # Check condition if specified
            if step.condition and not self._evaluate_condition(step.condition, execution):
                continue
            
            # Create task for this step
            task = Task(
                task_id=f"{execution.execution_id}-{step.step_id}",
                task_type=step.agent_type.value.lower(),
                priority=priority,
                input_data={
                    'document_id': execution.document_id,
                    'previous_results': execution.step_results.get(step.input_from) if step.input_from else None
                }
            )
            
            # Assign to agent
            success = await self.agent_registry.assign_task_to_best_agent(
                task,
                step.agent_type
            )
            
            if not success:
                raise RuntimeError(f"No agent available for step {step.step_id}")
            
            # Wait for task completion
            await self._wait_for_task(task)
            
            if task.status == TaskStatus.COMPLETED:
                execution.step_results[step.step_id] = task.output_data
            elif task.status == TaskStatus.FAILED:
                raise RuntimeError(f"Step {step.step_id} failed: {task.error_message}")
            elif task.status == TaskStatus.REQUIRES_HUMAN:
                execution.status = WorkflowStatus.PAUSED
                raise RuntimeError(f"Step {step.step_id} requires human intervention")
    
    async def _wait_for_task(self, task: Task, timeout: int = 30):
        """Wait for a task to complete"""
        start_time = datetime.utcnow()
        
        while task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            await asyncio.sleep(0.5)
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Task {task.task_id} timed out after {timeout}s")
    
    def _evaluate_condition(
        self,
        condition: str,
        execution: WorkflowExecution
    ) -> bool:
        """Evaluate a workflow step condition"""
        # Simple condition evaluation (would be more sophisticated in production)
        # Example: "compliance.compliant == true"
        
        try:
            # Parse condition
            parts = condition.split('.')
            if len(parts) == 2:
                step_id, field = parts
                result = execution.step_results.get(step_id, {})
                return result.get(field, False)
        except:
            pass
        
        return True
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution status"""
        return self._executions.get(execution_id)
    
    async def list_workflows(self) -> List[Workflow]:
        """List all available workflows"""
        return list(self._workflows.values())
    
    async def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        
        total_executions = len(self._executions)
        completed = len([e for e in self._executions.values() if e.status == WorkflowStatus.COMPLETED])
        failed = len([e for e in self._executions.values() if e.status == WorkflowStatus.FAILED])
        running = len([e for e in self._executions.values() if e.status == WorkflowStatus.RUNNING])
        
        by_workflow = {}
        for workflow_id in self._workflows.keys():
            executions = [e for e in self._executions.values() if e.workflow_id == workflow_id]
            by_workflow[workflow_id] = {
                'total': len(executions),
                'completed': len([e for e in executions if e.status == WorkflowStatus.COMPLETED]),
                'failed': len([e for e in executions if e.status == WorkflowStatus.FAILED])
            }
        
        return {
            'total_workflows': len(self._workflows),
            'total_executions': total_executions,
            'completed': completed,
            'failed': failed,
            'running': running,
            'success_rate': (completed / total_executions * 100) if total_executions > 0 else 0,
            'by_workflow': by_workflow
        }


# Global orchestrator
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None

def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get the singleton workflow orchestrator"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator()
    return _workflow_orchestrator
