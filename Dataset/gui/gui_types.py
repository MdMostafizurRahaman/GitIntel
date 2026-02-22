"""GUI type definitions extracted from main.py to avoid circular imports."""
import queue
from enum import Enum
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    PENDING = "Pending"
    WAITING_APPROVAL = "Waiting Approval"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass
class Task:
    """Represents a single task in the workflow"""
    id: int
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    action: Optional[Callable] = None
    requires_approval: bool = True
    subtasks: List['Task'] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    

class TaskManager:
    """Manages the task workflow"""
    
    def __init__(self, on_update: Callable = None):
        self.tasks: List[Task] = []
        self.current_task_index = 0
        self.on_update = on_update
        self.is_running = False
        self.approval_queue = queue.Queue()
    
    def add_task(self, title: str, description: str, action: Callable = None, 
                 requires_approval: bool = True) -> Task:
        """Add a new task"""
        task = Task(
            id=len(self.tasks) + 1,
            title=title,
            description=description,
            action=action,
            requires_approval=requires_approval
        )
        self.tasks.append(task)
        self._notify_update()
        return task
        
    def clear_tasks(self):
        """Clear all tasks"""
        self.tasks = []
        self.current_task_index = 0
        self._notify_update()
        
    def set_task_status(self, task_id: int, status: TaskStatus, result: str = None, error: str = None):
        """Update task status"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                task.result = result
                task.error = error
                break
        self._notify_update()
        
    def get_current_task(self) -> Optional[Task]:
        """Get the current task"""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None
        
    def approve_current(self):
        """Approve current task"""
        self.approval_queue.put(True)
        
    def reject_current(self):
        """Reject current task"""
        self.approval_queue.put(False)
        
    def skip_current(self):
        """Skip current task"""
        self.approval_queue.put("skip")
        
    def _notify_update(self):
        """Notify UI of updates"""
        if self.on_update:
            self.on_update()


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT MESSAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class MessageType(Enum):
    SYSTEM   = "SYSTEM"
    USER     = "YOU"
    THINKING = "AGENT"
    ACTION   = "AGENT"
    SUCCESS  = "AGENT"
    ERROR    = "AGENT"
    QUESTION = "AGENT"
    INFO     = "AGENT"
    PREVIEW  = "AGENT"


@dataclass
class AgentMessage:
    """Represents a message in the agent panel"""
    type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    actions: List[Dict] = field(default_factory=list)  # For buttons/actions
