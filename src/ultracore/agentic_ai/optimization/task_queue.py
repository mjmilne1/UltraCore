"""Priority-based Task Queue"""
from queue import PriorityQueue
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TaskPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

@dataclass(order=True)
class AgentTask:
    priority: TaskPriority = field(compare=True)
    task_id: str = field(compare=False)
    agent_id: str = field(compare=False)
    context: Dict[str, Any] = field(compare=False)

class AgentTaskQueue:
    """Priority-based task queue for agents."""
    
    def __init__(self):
        self.queue = PriorityQueue()
        self.in_progress = {}
        self.completed = {}
        logger.info("AgentTaskQueue initialized")
    
    def enqueue(self, task: AgentTask):
        """Add task to queue."""
        self.queue.put(task)
        logger.debug(f"Enqueued task {task.task_id} with priority {task.priority.name}")
    
    def get_next(self) -> AgentTask:
        """Get next task from queue."""
        task = self.queue.get()
        self.in_progress[task.task_id] = task
        return task
    
    def mark_complete(self, task_id: str, result: Any):
        """Mark task as complete."""
        if task_id in self.in_progress:
            task = self.in_progress.pop(task_id)
            self.completed[task_id] = {"task": task, "result": result}
    
    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "queued": self.queue.qsize(),
            "in_progress": len(self.in_progress),
            "completed": len(self.completed)
        }
