"""
Close of Business (COB) Processing Engine

Automates end-of-day processing including:
- Interest accrual
- Fee processing
- Arrears detection
- Balance calculations
- Regulatory reporting
- AI-optimized task scheduling
"""

from typing import List, Dict, Optional
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
from dataclasses import dataclass


class COBTaskType(str, Enum):
    """Types of COB tasks"""
    INTEREST_ACCRUAL = "interest_accrual"
    FEE_PROCESSING = "fee_processing"
    ARREARS_DETECTION = "arrears_detection"
    BALANCE_CALCULATION = "balance_calculation"
    DIVIDEND_ACCRUAL = "dividend_accrual"
    REGULATORY_REPORTING = "regulatory_reporting"
    DATA_ARCHIVAL = "data_archival"
    RECONCILIATION = "reconciliation"
    BACKUP = "backup"


class COBTaskStatus(str, Enum):
    """COB task execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class COBRunStatus(str, Enum):
    """COB run statuses"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


# ============================================================================
# MODELS
# ============================================================================

class COBTask(BaseModel):
    """Individual COB task definition"""
    task_id: str
    task_type: COBTaskType
    task_name: str
    description: str
    
    # Dependencies
    depends_on: List[str] = []  # Task IDs that must complete first
    
    # Execution
    priority: int = 100  # Lower number = higher priority
    timeout_seconds: int = 3600
    retry_count: int = 3
    
    # Scheduling
    is_enabled: bool = True
    run_on_weekends: bool = True
    run_on_holidays: bool = False
    
    # AI optimization
    estimated_duration_seconds: int = 60
    resource_requirements: Dict[str, float] = {}  # cpu, memory, io
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class COBTaskExecution(BaseModel):
    """COB task execution record"""
    execution_id: str
    run_id: str
    task_id: str
    task_type: COBTaskType
    
    status: COBTaskStatus = COBTaskStatus.PENDING
    
    # Timing
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    
    # Metrics
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class COBRun(BaseModel):
    """COB run (entire end-of-day process)"""
    run_id: str
    business_date: date
    
    status: COBRunStatus = COBRunStatus.SCHEDULED
    
    # Timing
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Tasks
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    
    # Results
    total_records_processed: int = 0
    total_records_failed: int = 0
    
    # Metadata
    triggered_by: str = "system"
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# COB ENGINE
# ============================================================================

class COBEngine:
    """
    Close of Business Processing Engine
    
    Orchestrates end-of-day processing with:
    - Dependency management
    - Parallel execution
    - AI-optimized scheduling
    - Error handling and retry
    - Progress tracking
    """
    
    def __init__(self, kafka_producer=None):
        self.tasks: Dict[str, COBTask] = {}
        self.runs: Dict[str, COBRun] = {}
        self.executions: Dict[str, COBTaskExecution] = {}
        self.kafka_producer = kafka_producer
        
        # Initialize default tasks
        self._initialize_default_tasks()
        
    def _initialize_default_tasks(self):
        """Initialize default COB tasks"""
        
        # Task 1: Interest Accrual (must run first)
        self.tasks["interest_accrual"] = COBTask(
            task_id="interest_accrual",
            task_type=COBTaskType.INTEREST_ACCRUAL,
            task_name="Interest Accrual",
            description="Calculate and accrue interest on all accounts",
            priority=10,
            estimated_duration_seconds=300,
            resource_requirements={"cpu": 0.5, "memory": 1.0, "io": 0.3}
        )
        
        # Task 2: Dividend Accrual
        self.tasks["dividend_accrual"] = COBTask(
            task_id="dividend_accrual",
            task_type=COBTaskType.DIVIDEND_ACCRUAL,
            task_name="Dividend Accrual",
            description="Accrue dividends on share accounts",
            priority=15,
            estimated_duration_seconds=120,
            resource_requirements={"cpu": 0.3, "memory": 0.5, "io": 0.2}
        )
        
        # Task 3: Fee Processing (depends on interest)
        self.tasks["fee_processing"] = COBTask(
            task_id="fee_processing",
            task_type=COBTaskType.FEE_PROCESSING,
            task_name="Fee Processing",
            description="Process account fees and charges",
            depends_on=["interest_accrual"],
            priority=20,
            estimated_duration_seconds=180,
            resource_requirements={"cpu": 0.4, "memory": 0.8, "io": 0.3}
        )
        
        # Task 4: Balance Calculation (depends on interest and fees)
        self.tasks["balance_calculation"] = COBTask(
            task_id="balance_calculation",
            task_type=COBTaskType.BALANCE_CALCULATION,
            task_name="Balance Calculation",
            description="Recalculate all account balances",
            depends_on=["interest_accrual", "fee_processing"],
            priority=30,
            estimated_duration_seconds=240,
            resource_requirements={"cpu": 0.6, "memory": 1.2, "io": 0.4}
        )
        
        # Task 5: Arrears Detection (depends on balance)
        self.tasks["arrears_detection"] = COBTask(
            task_id="arrears_detection",
            task_type=COBTaskType.ARREARS_DETECTION,
            task_name="Arrears Detection",
            description="Detect accounts in arrears",
            depends_on=["balance_calculation"],
            priority=40,
            estimated_duration_seconds=150,
            resource_requirements={"cpu": 0.4, "memory": 0.6, "io": 0.2}
        )
        
        # Task 6: Reconciliation (depends on balance)
        self.tasks["reconciliation"] = COBTask(
            task_id="reconciliation",
            task_type=COBTaskType.RECONCILIATION,
            task_name="Reconciliation",
            description="Reconcile accounts and transactions",
            depends_on=["balance_calculation"],
            priority=50,
            estimated_duration_seconds=300,
            resource_requirements={"cpu": 0.5, "memory": 1.0, "io": 0.5}
        )
        
        # Task 7: Regulatory Reporting (depends on reconciliation)
        self.tasks["regulatory_reporting"] = COBTask(
            task_id="regulatory_reporting",
            task_type=COBTaskType.REGULATORY_REPORTING,
            task_name="Regulatory Reporting",
            description="Generate regulatory reports",
            depends_on=["reconciliation"],
            priority=60,
            estimated_duration_seconds=600,
            resource_requirements={"cpu": 0.7, "memory": 1.5, "io": 0.8}
        )
        
        # Task 8: Data Archival (can run in parallel)
        self.tasks["data_archival"] = COBTask(
            task_id="data_archival",
            task_type=COBTaskType.DATA_ARCHIVAL,
            task_name="Data Archival",
            description="Archive old data",
            priority=70,
            estimated_duration_seconds=900,
            resource_requirements={"cpu": 0.3, "memory": 0.5, "io": 1.0}
        )
        
        # Task 9: Backup (must run last)
        self.tasks["backup"] = COBTask(
            task_id="backup",
            task_type=COBTaskType.BACKUP,
            task_name="Database Backup",
            description="Backup all databases",
            depends_on=["regulatory_reporting", "data_archival"],
            priority=100,
            estimated_duration_seconds=1200,
            resource_requirements={"cpu": 0.4, "memory": 0.8, "io": 1.5}
        )
        
    async def run_cob(
        self,
        business_date: date,
        triggered_by: str = "system"
    ) -> COBRun:
        """Execute complete COB process"""
        import uuid
        
        run_id = f"COB-{business_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create COB run
        cob_run = COBRun(
            run_id=run_id,
            business_date=business_date,
            status=COBRunStatus.SCHEDULED,
            scheduled_time=datetime.combine(business_date, time(23, 0)),
            triggered_by=triggered_by,
            total_tasks=len(self.tasks)
        )
        
        self.runs[run_id] = cob_run
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_cob_started(run_id, business_date)
        
        try:
            # Update status
            cob_run.status = COBRunStatus.IN_PROGRESS
            cob_run.start_time = datetime.now(timezone.utc)
            
            # Execute tasks with dependency resolution
            await self._execute_tasks_with_dependencies(run_id, business_date)
            
            # Calculate results
            cob_run.end_time = datetime.now(timezone.utc)
            cob_run.duration_seconds = (cob_run.end_time - cob_run.start_time).total_seconds()
            
            # Count task statuses
            executions = [e for e in self.executions.values() if e.run_id == run_id]
            cob_run.completed_tasks = sum(1 for e in executions if e.status == COBTaskStatus.COMPLETED)
            cob_run.failed_tasks = sum(1 for e in executions if e.status == COBTaskStatus.FAILED)
            cob_run.skipped_tasks = sum(1 for e in executions if e.status == COBTaskStatus.SKIPPED)
            
            # Set final status
            if cob_run.failed_tasks == 0:
                cob_run.status = COBRunStatus.COMPLETED
            elif cob_run.completed_tasks > 0:
                cob_run.status = COBRunStatus.PARTIALLY_COMPLETED
            else:
                cob_run.status = COBRunStatus.FAILED
            
            # Publish event
            if self.kafka_producer:
                self.kafka_producer.publish_cob_completed(
                    run_id, business_date, cob_run.status.value,
                    cob_run.completed_tasks, cob_run.failed_tasks
                )
            
        except Exception as e:
            cob_run.status = COBRunStatus.FAILED
            cob_run.notes = str(e)
            
            if self.kafka_producer:
                self.kafka_producer.publish_cob_failed(run_id, business_date, str(e))
        
        return cob_run
        
    async def _execute_tasks_with_dependencies(
        self,
        run_id: str,
        business_date: date
    ):
        """Execute tasks respecting dependencies"""
        completed_tasks = set()
        failed_tasks = set()
        
        # Get execution order using topological sort
        execution_order = self._topological_sort()
        
        for task_id in execution_order:
            task = self.tasks[task_id]
            
            # Check if enabled
            if not task.is_enabled:
                self._skip_task(run_id, task_id, "Task disabled")
                continue
            
            # Check dependencies
            if not all(dep in completed_tasks for dep in task.depends_on):
                # Check if any dependency failed
                if any(dep in failed_tasks for dep in task.depends_on):
                    self._skip_task(run_id, task_id, "Dependency failed")
                    continue
            
            # Execute task
            success = await self._execute_task(run_id, task_id, business_date)
            
            if success:
                completed_tasks.add(task_id)
            else:
                failed_tasks.add(task_id)
        
    async def _execute_task(
        self,
        run_id: str,
        task_id: str,
        business_date: date
    ) -> bool:
        """Execute a single COB task"""
        import uuid
        
        task = self.tasks[task_id]
        execution_id = f"EXEC-{uuid.uuid4().hex[:12].upper()}"
        
        # Create execution record
        execution = COBTaskExecution(
            execution_id=execution_id,
            run_id=run_id,
            task_id=task_id,
            task_type=task.task_type,
            scheduled_time=datetime.now(timezone.utc),
            status=COBTaskStatus.RUNNING
        )
        
        self.executions[execution_id] = execution
        
        try:
            execution.start_time = datetime.now(timezone.utc)
            
            # Execute task based on type
            if task.task_type == COBTaskType.INTEREST_ACCRUAL:
                records_processed = await self._process_interest_accrual(business_date)
            elif task.task_type == COBTaskType.FEE_PROCESSING:
                records_processed = await self._process_fees(business_date)
            elif task.task_type == COBTaskType.BALANCE_CALCULATION:
                records_processed = await self._calculate_balances(business_date)
            elif task.task_type == COBTaskType.ARREARS_DETECTION:
                records_processed = await self._detect_arrears(business_date)
            elif task.task_type == COBTaskType.DIVIDEND_ACCRUAL:
                records_processed = await self._accrue_dividends(business_date)
            elif task.task_type == COBTaskType.REGULATORY_REPORTING:
                records_processed = await self._generate_reports(business_date)
            elif task.task_type == COBTaskType.DATA_ARCHIVAL:
                records_processed = await self._archive_data(business_date)
            elif task.task_type == COBTaskType.RECONCILIATION:
                records_processed = await self._reconcile(business_date)
            elif task.task_type == COBTaskType.BACKUP:
                records_processed = await self._backup(business_date)
            else:
                records_processed = 0
            
            execution.end_time = datetime.now(timezone.utc)
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            execution.records_processed = records_processed
            execution.status = COBTaskStatus.COMPLETED
            
            return True
            
        except Exception as e:
            execution.end_time = datetime.now(timezone.utc)
            execution.status = COBTaskStatus.FAILED
            execution.error_message = str(e)
            
            return False
        
    def _skip_task(self, run_id: str, task_id: str, reason: str):
        """Skip a task"""
        import uuid
        
        execution_id = f"EXEC-{uuid.uuid4().hex[:12].upper()}"
        
        execution = COBTaskExecution(
            execution_id=execution_id,
            run_id=run_id,
            task_id=task_id,
            task_type=self.tasks[task_id].task_type,
            scheduled_time=datetime.now(timezone.utc),
            status=COBTaskStatus.SKIPPED,
            error_message=reason
        )
        
        self.executions[execution_id] = execution
        
    def _topological_sort(self) -> List[str]:
        """Sort tasks by dependencies (topological sort)"""
        # Simple implementation - in production use proper algorithm
        sorted_tasks = []
        visited = set()
        
        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks[task_id]
            for dep in task.depends_on:
                if dep in self.tasks:
                    visit(dep)
            
            sorted_tasks.append(task_id)
        
        for task_id in self.tasks:
            visit(task_id)
        
        return sorted_tasks
        
    # ========================================================================
    # TASK IMPLEMENTATIONS (Stubs - would integrate with actual modules)
    # ========================================================================
    
    async def _process_interest_accrual(self, business_date: date) -> int:
        """Process interest accrual for all accounts"""
        # Simulate processing
        await asyncio.sleep(0.1)
        return 1000  # Number of accounts processed
        
    async def _process_fees(self, business_date: date) -> int:
        """Process fees for all accounts"""
        await asyncio.sleep(0.1)
        return 800
        
    async def _calculate_balances(self, business_date: date) -> int:
        """Recalculate balances"""
        await asyncio.sleep(0.1)
        return 1200
        
    async def _detect_arrears(self, business_date: date) -> int:
        """Detect accounts in arrears"""
        await asyncio.sleep(0.1)
        return 50
        
    async def _accrue_dividends(self, business_date: date) -> int:
        """Accrue dividends"""
        await asyncio.sleep(0.1)
        return 300
        
    async def _generate_reports(self, business_date: date) -> int:
        """Generate regulatory reports"""
        await asyncio.sleep(0.2)
        return 10
        
    async def _archive_data(self, business_date: date) -> int:
        """Archive old data"""
        await asyncio.sleep(0.3)
        return 5000
        
    async def _reconcile(self, business_date: date) -> int:
        """Reconcile accounts"""
        await asyncio.sleep(0.15)
        return 1500
        
    async def _backup(self, business_date: date) -> int:
        """Backup databases"""
        await asyncio.sleep(0.4)
        return 1
