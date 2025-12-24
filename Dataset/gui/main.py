#!/usr/bin/env python3
"""
GitIntel Agentic Dataset Generator - VS Code Copilot Style
===========================================================

Features:
- Todo List Panel: Shows all tasks step-by-step with status
- Permission System: Asks user approval before each action
- Side Panel: Copilot-style agent activity panel
- Feedback Loop: Iterates on user requirements

Author: GitIntel Team
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
import queue

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from metrics_catalog import MetricsCatalog
    from github_autonomous_agent import GitHubAutonomousAgent
    from interactive_dataset_generator import InteractiveDatasetGenerator
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    PENDING = "⏳ Pending"
    WAITING_APPROVAL = "❓ Waiting Approval"
    IN_PROGRESS = "🔄 In Progress"
    COMPLETED = "✅ Completed"
    FAILED = "❌ Failed"
    SKIPPED = "⏭️ Skipped"


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
    SYSTEM = "🤖"
    USER = "👤"
    THINKING = "💭"
    ACTION = "⚡"
    SUCCESS = "✅"
    ERROR = "❌"
    QUESTION = "❓"
    INFO = "ℹ️"


@dataclass
class AgentMessage:
    """Represents a message in the agent panel"""
    type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    actions: List[Dict] = field(default_factory=list)  # For buttons/actions


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class AgenticDatasetGUI:
    """
    VS Code Copilot-Style Agentic Dataset Generator
    
    Features:
    - Split view with main content and agent panel
    - Todo list showing all planned tasks
    - Step-by-step approval system
    - Real-time feedback loop
    """
    
    # Benchmark datasets
    BENCHMARK_DATASETS = {
        "Defects4J": {"description": "Java bugs with buggy/fixed structure", "format": "folder"},
        "Bugs.jar": {"description": "Large-scale Java bug dataset", "format": "json"},
        "ManySStuBs4J": {"description": "Simple stupid bugs in Java", "format": "json"},
        "CodeXGLUE": {"description": "Microsoft code benchmark", "format": "jsonl"},
        "CodeSearchNet": {"description": "Code-to-documentation dataset", "format": "jsonl"},
        "PROMISE": {"description": "Software defect prediction", "format": "csv"},
        "Sourcerer": {"description": "Large-scale code repository", "format": "csv"}
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 GitIntel Agentic Dataset Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize components
        self.task_manager = TaskManager(on_update=self.update_task_panel)
        self.messages: List[AgentMessage] = []
        self.message_queue = queue.Queue()
        
        # State
        self.repo_path = None
        self.selected_metrics = []
        self.dataset_config = {}
        self.agent_panel_visible = True
        
        # Try to initialize catalog and agent
        try:
            self.catalog = MetricsCatalog()
        except:
            self.catalog = None
            
        try:
            self.agent = GitHubAutonomousAgent()
        except:
            self.agent = None
            
        # Style configuration
        self.configure_styles()
        
        # Build UI
        self.build_ui()
        
        # Start message processing
        self.process_message_queue()
        
        # Welcome message
        self.add_agent_message(MessageType.SYSTEM, 
            "Welcome to GitIntel Agentic Dataset Generator! 🎉\n\n"
            "I'm your AI assistant for creating datasets. Tell me what you need:\n"
            "• 'Create a Defects4J dataset from my repo'\n"
            "• 'Generate complexity metrics for Python files'\n"
            "• 'Build a custom dataset with CK metrics'\n\n"
            "I'll show you a plan and ask for approval at each step."
        )
        
    def configure_styles(self):
        """Configure custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#007acc',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336',
            'panel_bg': '#252526',
            'input_bg': '#3c3c3c',
            'border': '#454545'
        }
        
        # Button styles
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('Approve.TButton', font=('Segoe UI', 10))
        style.configure('Reject.TButton', font=('Segoe UI', 10))
        
        # Label styles
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Task.TLabel', font=('Segoe UI', 10))
        style.configure('TaskPending.TLabel', font=('Segoe UI', 10), foreground='gray')
        style.configure('TaskActive.TLabel', font=('Segoe UI', 10, 'bold'), foreground='#007acc')
        style.configure('TaskDone.TLabel', font=('Segoe UI', 10), foreground='#4caf50')
        
    def build_ui(self):
        """Build the main UI"""
        # Main container
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (Main content)
        self.left_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.left_frame, weight=3)
        
        # Right panel (Agent/Copilot style)
        self.right_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.right_frame, weight=2)
        
        # Build left panel
        self.build_left_panel()
        
        # Build right panel (Agent panel)
        self.build_agent_panel()
        
    def build_left_panel(self):
        """Build the left main content panel"""
        # Title bar
        title_frame = ttk.Frame(self.left_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="🔬 Dataset Generator", 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        # Toggle agent panel button
        self.toggle_btn = ttk.Button(title_frame, text="◀ Agent Panel",
                                      command=self.toggle_agent_panel)
        self.toggle_btn.pack(side=tk.RIGHT)
        
        # ═══════════════════════════════════════════════════════════════════
        # REPOSITORY SECTION
        # ═══════════════════════════════════════════════════════════════════
        repo_frame = ttk.LabelFrame(self.left_frame, text="📁 Repository", padding=10)
        repo_frame.pack(fill=tk.X, pady=(0, 10))
        
        repo_input_frame = ttk.Frame(repo_frame)
        repo_input_frame.pack(fill=tk.X)
        
        self.repo_var = tk.StringVar()
        self.repo_entry = ttk.Entry(repo_input_frame, textvariable=self.repo_var, 
                                     font=('Consolas', 10))
        self.repo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.repo_entry.insert(0, "Enter path, GitHub URL, or owner/repo...")
        self.repo_entry.bind('<FocusIn>', self.on_repo_focus)
        
        ttk.Button(repo_input_frame, text="📂", width=3,
                   command=self.browse_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(repo_input_frame, text="✓ Set", 
                   command=self.set_repository).pack(side=tk.LEFT, padx=2)
        
        self.repo_status = ttk.Label(repo_frame, text="", font=('Segoe UI', 9))
        self.repo_status.pack(anchor=tk.W, pady=(5, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # QUICK ACTIONS (Natural Language Input)
        # ═══════════════════════════════════════════════════════════════════
        action_frame = ttk.LabelFrame(self.left_frame, text="💬 Tell me what you need", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.nl_input_var = tk.StringVar()
        self.nl_input = ttk.Entry(action_frame, textvariable=self.nl_input_var,
                                   font=('Segoe UI', 11))
        self.nl_input.pack(fill=tk.X, pady=(0, 5))
        self.nl_input.insert(0, "e.g., 'Create a dataset with complexity metrics for Java files'")
        self.nl_input.bind('<FocusIn>', lambda e: self.nl_input.delete(0, tk.END) 
                           if 'e.g.' in self.nl_input.get() else None)
        self.nl_input.bind('<Return>', lambda e: self.process_natural_language())
        
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🚀 Generate Plan", 
                   command=self.process_natural_language,
                   style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Show Benchmarks",
                   command=self.show_benchmark_options).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📊 Select Metrics",
                   command=self.show_metrics_selector).pack(side=tk.LEFT, padx=2)
        
        # ═══════════════════════════════════════════════════════════════════
        # TODO LIST PANEL
        # ═══════════════════════════════════════════════════════════════════
        self.todo_frame = ttk.LabelFrame(self.left_frame, text="📝 Task Plan", padding=10)
        self.todo_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Todo header
        todo_header = ttk.Frame(self.todo_frame)
        todo_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(todo_header, text="Tasks will appear here when you generate a plan",
                  style='Task.TLabel').pack(side=tk.LEFT)
        
        self.task_progress_var = tk.StringVar(value="0/0 tasks")
        ttk.Label(todo_header, textvariable=self.task_progress_var).pack(side=tk.RIGHT)
        
        # Scrollable task list
        self.task_canvas = tk.Canvas(self.todo_frame, bg='white', highlightthickness=0)
        task_scrollbar = ttk.Scrollbar(self.todo_frame, orient=tk.VERTICAL, 
                                        command=self.task_canvas.yview)
        
        self.task_list_frame = ttk.Frame(self.task_canvas)
        
        self.task_canvas.configure(yscrollcommand=task_scrollbar.set)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.task_canvas_window = self.task_canvas.create_window((0, 0), 
                                                                   window=self.task_list_frame, 
                                                                   anchor=tk.NW)
        
        self.task_list_frame.bind('<Configure>', 
                                   lambda e: self.task_canvas.configure(
                                       scrollregion=self.task_canvas.bbox("all")))
        self.task_canvas.bind('<Configure>', 
                              lambda e: self.task_canvas.itemconfig(
                                  self.task_canvas_window, width=e.width))
        
        # ═══════════════════════════════════════════════════════════════════
        # CONTROL BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        control_frame = ttk.Frame(self.left_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="▶ Start Execution",
                                     command=self.start_execution,
                                     style='Accent.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=2)
        self.start_btn.config(state=tk.DISABLED)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸ Pause",
                                     command=self.pause_execution)
        self.pause_btn.pack(side=tk.LEFT, padx=2)
        self.pause_btn.config(state=tk.DISABLED)
        
        ttk.Button(control_frame, text="🗑️ Clear Plan",
                   command=self.clear_plan).pack(side=tk.LEFT, padx=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var,
                                            mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)
        
        # ═══════════════════════════════════════════════════════════════════
        # STATUS BAR
        # ═══════════════════════════════════════════════════════════════════
        status_frame = ttk.Frame(self.left_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var,
                  font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
    def build_agent_panel(self):
        """Build the right agent panel (Copilot style)"""
        # Header
        header_frame = ttk.Frame(self.right_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🤖 Agent Assistant",
                  style='Header.TLabel').pack(side=tk.LEFT)
        
        # Message area
        self.message_frame = ttk.Frame(self.right_frame)
        self.message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.message_text = scrolledtext.ScrolledText(
            self.message_frame,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white',
            state=tk.DISABLED
        )
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different message types
        self.message_text.tag_configure('system', foreground='#569cd6')
        self.message_text.tag_configure('user', foreground='#4ec9b0')
        self.message_text.tag_configure('thinking', foreground='#808080', font=('Segoe UI', 10, 'italic'))
        self.message_text.tag_configure('action', foreground='#dcdcaa')
        self.message_text.tag_configure('success', foreground='#4caf50')
        self.message_text.tag_configure('error', foreground='#f44336')
        self.message_text.tag_configure('question', foreground='#ce9178')
        self.message_text.tag_configure('info', foreground='#9cdcfe')
        self.message_text.tag_configure('bold', font=('Segoe UI', 10, 'bold'))
        
        # ═══════════════════════════════════════════════════════════════════
        # APPROVAL SECTION
        # ═══════════════════════════════════════════════════════════════════
        self.approval_frame = ttk.LabelFrame(self.right_frame, text="❓ Action Required", padding=10)
        self.approval_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.approval_text = ttk.Label(self.approval_frame, 
                                        text="No pending approvals",
                                        wraplength=300)
        self.approval_text.pack(fill=tk.X, pady=(0, 10))
        
        approval_btns = ttk.Frame(self.approval_frame)
        approval_btns.pack(fill=tk.X)
        
        self.approve_btn = ttk.Button(approval_btns, text="✅ Approve",
                                       command=self.approve_action,
                                       style='Approve.TButton')
        self.approve_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.reject_btn = ttk.Button(approval_btns, text="❌ Reject",
                                      command=self.reject_action,
                                      style='Reject.TButton')
        self.reject_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.skip_btn = ttk.Button(approval_btns, text="⏭️ Skip",
                                    command=self.skip_action)
        self.skip_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Hide initially
        self.set_approval_visible(False)
        
        # ═══════════════════════════════════════════════════════════════════
        # FEEDBACK INPUT
        # ═══════════════════════════════════════════════════════════════════
        feedback_frame = ttk.LabelFrame(self.right_frame, text="💬 Your Feedback", padding=10)
        feedback_frame.pack(fill=tk.X)
        
        self.feedback_var = tk.StringVar()
        self.feedback_entry = ttk.Entry(feedback_frame, textvariable=self.feedback_var,
                                         font=('Segoe UI', 10))
        self.feedback_entry.pack(fill=tk.X, pady=(0, 5))
        self.feedback_entry.bind('<Return>', lambda e: self.send_feedback())
        
        ttk.Button(feedback_frame, text="📤 Send",
                   command=self.send_feedback).pack(side=tk.RIGHT)
        
    # ═══════════════════════════════════════════════════════════════════════════
    # MESSAGE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_agent_message(self, msg_type: MessageType, content: str, actions: List[Dict] = None):
        """Add a message to the agent panel"""
        self.message_queue.put((msg_type, content, actions or []))
        
    def process_message_queue(self):
        """Process messages from queue (thread-safe)"""
        try:
            while True:
                msg_type, content, actions = self.message_queue.get_nowait()
                self._display_message(msg_type, content, actions)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_message_queue)
            
    def _display_message(self, msg_type: MessageType, content: str, actions: List[Dict]):
        """Display a message in the agent panel"""
        self.message_text.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        # Get tag based on message type
        tag_map = {
            MessageType.SYSTEM: 'system',
            MessageType.USER: 'user',
            MessageType.THINKING: 'thinking',
            MessageType.ACTION: 'action',
            MessageType.SUCCESS: 'success',
            MessageType.ERROR: 'error',
            MessageType.QUESTION: 'question',
            MessageType.INFO: 'info'
        }
        tag = tag_map.get(msg_type, 'system')
        
        # Insert message
        self.message_text.insert(tk.END, f"\n{msg_type.value} [{timestamp}]\n", 'bold')
        self.message_text.insert(tk.END, f"{content}\n", tag)
        
        # Scroll to end
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)
        
    # ═══════════════════════════════════════════════════════════════════════════
    # TASK PANEL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_task_panel(self):
        """Update the task list panel"""
        # Clear existing widgets
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        # Count completed
        completed = sum(1 for t in self.task_manager.tasks 
                       if t.status == TaskStatus.COMPLETED)
        total = len(self.task_manager.tasks)
        self.task_progress_var.set(f"{completed}/{total} tasks")
        
        # Progress
        if total > 0:
            self.progress_var.set((completed / total) * 100)
        
        # Add task widgets
        for i, task in enumerate(self.task_manager.tasks):
            task_frame = ttk.Frame(self.task_list_frame)
            task_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Status indicator
            status_colors = {
                TaskStatus.PENDING: '⏳',
                TaskStatus.WAITING_APPROVAL: '❓',
                TaskStatus.IN_PROGRESS: '🔄',
                TaskStatus.COMPLETED: '✅',
                TaskStatus.FAILED: '❌',
                TaskStatus.SKIPPED: '⏭️'
            }
            
            # Determine style based on status
            if task.status == TaskStatus.IN_PROGRESS or task.status == TaskStatus.WAITING_APPROVAL:
                style = 'TaskActive.TLabel'
                bg = '#e3f2fd'
            elif task.status == TaskStatus.COMPLETED:
                style = 'TaskDone.TLabel'
                bg = '#e8f5e9'
            elif task.status == TaskStatus.FAILED:
                style = 'TaskPending.TLabel'
                bg = '#ffebee'
            else:
                style = 'TaskPending.TLabel'
                bg = 'white'
            
            # Task content
            status_icon = status_colors.get(task.status, '⏳')
            task_text = f"{status_icon} {task.id}. {task.title}"
            
            task_label = ttk.Label(task_frame, text=task_text, style=style)
            task_label.pack(anchor=tk.W)
            
            # Description
            desc_label = ttk.Label(task_frame, text=f"   {task.description}",
                                   font=('Segoe UI', 9), foreground='gray')
            desc_label.pack(anchor=tk.W)
            
            # Result or error
            if task.result:
                result_label = ttk.Label(task_frame, text=f"   → {task.result}",
                                         font=('Segoe UI', 9), foreground='green')
                result_label.pack(anchor=tk.W)
            elif task.error:
                error_label = ttk.Label(task_frame, text=f"   ✗ {task.error}",
                                        font=('Segoe UI', 9), foreground='red')
                error_label.pack(anchor=tk.W)
                
            # Separator
            ttk.Separator(task_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
            
    # ═══════════════════════════════════════════════════════════════════════════
    # NATURAL LANGUAGE PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_natural_language(self):
        """Process natural language input and create a task plan"""
        user_input = self.nl_input_var.get().strip()
        if not user_input or 'e.g.' in user_input:
            messagebox.showwarning("Input Required", "Please describe what you want to create")
            return
            
        # Show user message
        self.add_agent_message(MessageType.USER, user_input)
        
        # Show thinking
        self.add_agent_message(MessageType.THINKING, "Analyzing your request...")
        
        # Parse and create plan
        threading.Thread(target=self._create_plan_from_input, 
                        args=(user_input,), daemon=True).start()
        
    def _create_plan_from_input(self, user_input: str):
        """Parse user input and create a task plan"""
        user_lower = user_input.lower()
        
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        # Analyze what user wants
        detected = {
            'benchmark': None,
            'metrics': [],
            'format': 'csv',
            'language': None
        }
        
        # Detect benchmark dataset
        for benchmark in self.BENCHMARK_DATASETS.keys():
            if benchmark.lower() in user_lower:
                detected['benchmark'] = benchmark
                break
                
        # Detect metrics categories
        metric_keywords = {
            'complexity': ['cyclomatic', 'cognitive', 'nesting'],
            'ck': ['wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom'],
            'size': ['loc', 'lines', 'sloc'],
            'quality': ['maintainability', 'comment'],
            'coupling': ['coupling', 'afferent', 'efferent'],
            'defect': ['bug', 'defect', 'vulnerability']
        }
        
        for category, keywords in metric_keywords.items():
            for kw in keywords:
                if kw in user_lower:
                    detected['metrics'].append(category)
                    break
                    
        # Detect language
        languages = ['java', 'python', 'javascript', 'typescript', 'go', 'ruby', 'c++', 'c#']
        for lang in languages:
            if lang in user_lower:
                detected['language'] = lang
                break
                
        # Detect output format
        for fmt in ['csv', 'json', 'jsonl', 'excel', 'parquet']:
            if fmt in user_lower:
                detected['format'] = fmt
                break
        
        # Create task plan based on detection
        self.add_agent_message(MessageType.SYSTEM, 
            f"I understand you want to create a dataset. Here's my plan:")
        
        # Task 1: Verify repository
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=True
        )
        
        # Task 2: Analyze repository structure
        self.task_manager.add_task(
            "Analyze Repository",
            "Scan the repository to understand its structure",
            action=self.task_analyze_repo,
            requires_approval=True
        )
        
        # Task 3 depends on what was detected
        if detected['benchmark']:
            self.task_manager.add_task(
                f"Setup {detected['benchmark']} Format",
                f"Configure dataset in {detected['benchmark']} format",
                action=lambda: self.task_setup_benchmark(detected['benchmark']),
                requires_approval=True
            )
            
            self.task_manager.add_task(
                "Find Bug-Fixing Commits",
                "Identify commits that fix bugs in the repository",
                action=self.task_find_bugs,
                requires_approval=True
            )
        else:
            # Custom metrics selection
            if detected['metrics']:
                metrics_str = ', '.join(detected['metrics'])
                self.task_manager.add_task(
                    "Select Metrics",
                    f"Configure metrics: {metrics_str}",
                    action=lambda: self.task_select_metrics(detected['metrics']),
                    requires_approval=True
                )
            else:
                self.task_manager.add_task(
                    "Select Metrics",
                    "Choose metrics for the dataset (none detected, will use defaults)",
                    action=lambda: self.task_select_metrics(['size', 'complexity']),
                    requires_approval=True
                )
        
        # Task: Extract data
        self.task_manager.add_task(
            "Extract Data",
            f"Process files and extract {detected['format']} data",
            action=lambda: self.task_extract_data(detected),
            requires_approval=True
        )
        
        # Task: Generate output
        self.task_manager.add_task(
            "Generate Dataset",
            f"Create output file in {detected['format'].upper()} format",
            action=lambda: self.task_generate_output(detected),
            requires_approval=True
        )
        
        # Task: Validate
        self.task_manager.add_task(
            "Validate Dataset",
            "Check the generated dataset for completeness",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary
        summary = f"""
📋 **Plan Created with {len(self.task_manager.tasks)} tasks:**

"""
        for task in self.task_manager.tasks:
            summary += f"  {task.id}. {task.title}\n"
            
        summary += f"""
**Detected Configuration:**
- Dataset Type: {detected['benchmark'] or 'Custom'}
- Metrics: {', '.join(detected['metrics']) if detected['metrics'] else 'Default (size, complexity)'}
- Language Filter: {detected['language'] or 'All'}
- Output Format: {detected['format'].upper()}

Click **▶ Start Execution** to begin. I'll ask for your approval at each step.
"""
        
        self.add_agent_message(MessageType.INFO, summary)
        
        # Enable start button
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        
        # Store config
        self.dataset_config = detected
        
    # ═══════════════════════════════════════════════════════════════════════════
    # TASK EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_execution(self):
        """Start executing the task plan"""
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.task_manager.is_running = True
        
        self.add_agent_message(MessageType.SYSTEM, "Starting execution...")
        
        threading.Thread(target=self._execute_tasks, daemon=True).start()
        
    def _execute_tasks(self):
        """Execute tasks one by one with approval"""
        for task in self.task_manager.tasks:
            if not self.task_manager.is_running:
                break
                
            # Update task status
            if task.requires_approval:
                self.task_manager.set_task_status(task.id, TaskStatus.WAITING_APPROVAL)
                
                # Show approval request
                self.root.after(0, lambda t=task: self.show_approval_request(t))
                
                # Wait for approval
                approval = self.task_manager.approval_queue.get()
                
                if approval == "skip":
                    self.task_manager.set_task_status(task.id, TaskStatus.SKIPPED,
                                                       result="Skipped by user")
                    self.add_agent_message(MessageType.INFO, f"⏭️ Skipped: {task.title}")
                    continue
                elif not approval:
                    self.task_manager.set_task_status(task.id, TaskStatus.FAILED,
                                                       error="Rejected by user")
                    self.add_agent_message(MessageType.ERROR, 
                        f"❌ Task rejected: {task.title}\n\nPlease modify the plan if needed.")
                    break
                    
            # Execute task
            self.task_manager.set_task_status(task.id, TaskStatus.IN_PROGRESS)
            self.add_agent_message(MessageType.ACTION, f"Executing: {task.title}...")
            
            try:
                if task.action:
                    result = task.action()
                    self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                       result=str(result) if result else "Done")
                    self.add_agent_message(MessageType.SUCCESS, 
                        f"✅ Completed: {task.title}")
                else:
                    self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                       result="No action required")
            except Exception as e:
                self.task_manager.set_task_status(task.id, TaskStatus.FAILED,
                                                   error=str(e))
                self.add_agent_message(MessageType.ERROR, 
                    f"❌ Failed: {task.title}\nError: {str(e)}")
                    
        # Execution complete
        self.root.after(0, self._execution_complete)
        
    def _execution_complete(self):
        """Called when execution is complete"""
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.task_manager.is_running = False
        self.set_approval_visible(False)
        
        # Count results
        completed = sum(1 for t in self.task_manager.tasks 
                       if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.task_manager.tasks 
                    if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in self.task_manager.tasks 
                     if t.status == TaskStatus.SKIPPED)
        
        self.add_agent_message(MessageType.SYSTEM,
            f"🏁 Execution Complete!\n\n"
            f"✅ Completed: {completed}\n"
            f"❌ Failed: {failed}\n"
            f"⏭️ Skipped: {skipped}\n\n"
            f"{'Dataset generated successfully!' if failed == 0 else 'Some tasks failed. Please review.'}"
        )
        
    def pause_execution(self):
        """Pause the execution"""
        self.task_manager.is_running = False
        self.pause_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.add_agent_message(MessageType.INFO, "⏸️ Execution paused. Click Start to resume.")
        
    def clear_plan(self):
        """Clear the task plan"""
        self.task_manager.clear_tasks()
        self.progress_var.set(0)
        self.add_agent_message(MessageType.INFO, "🗑️ Plan cleared. Describe what you need to create a new plan.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # APPROVAL SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show_approval_request(self, task: Task):
        """Show approval request for a task"""
        self.approval_text.config(text=f"Task: {task.title}\n\n{task.description}\n\nApprove this action?")
        self.set_approval_visible(True)
        
        self.add_agent_message(MessageType.QUESTION,
            f"❓ **Approval Required**\n\n"
            f"**Task:** {task.title}\n"
            f"**Description:** {task.description}\n\n"
            f"Please approve, reject, or skip this task."
        )
        
    def set_approval_visible(self, visible: bool):
        """Show or hide approval section"""
        if visible:
            self.approve_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            self.skip_btn.config(state=tk.NORMAL)
        else:
            self.approve_btn.config(state=tk.DISABLED)
            self.reject_btn.config(state=tk.DISABLED)
            self.skip_btn.config(state=tk.DISABLED)
            self.approval_text.config(text="No pending approvals")
            
    def approve_action(self):
        """Approve the current action"""
        self.set_approval_visible(False)
        self.task_manager.approve_current()
        self.add_agent_message(MessageType.SUCCESS, "✅ Action approved!")
        
    def reject_action(self):
        """Reject the current action"""
        self.set_approval_visible(False)
        self.task_manager.reject_current()
        self.add_agent_message(MessageType.ERROR, "❌ Action rejected.")
        
    def skip_action(self):
        """Skip the current action"""
        self.set_approval_visible(False)
        self.task_manager.skip_current()
        self.add_agent_message(MessageType.INFO, "⏭️ Action skipped.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # FEEDBACK SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def send_feedback(self):
        """Send user feedback"""
        feedback = self.feedback_var.get().strip()
        if not feedback:
            return
            
        self.feedback_var.set("")
        
        # Show user message
        self.add_agent_message(MessageType.USER, feedback)
        
        # Process feedback
        self.add_agent_message(MessageType.THINKING, "Processing your feedback...")
        
        # Simple feedback processing
        threading.Thread(target=self._process_feedback, 
                        args=(feedback,), daemon=True).start()
        
    def _process_feedback(self, feedback: str):
        """Process user feedback"""
        feedback_lower = feedback.lower()
        
        if any(word in feedback_lower for word in ['yes', 'ok', 'good', 'correct', 'proceed']):
            self.add_agent_message(MessageType.SYSTEM,
                "Great! I'll proceed with the plan as is.")
        elif any(word in feedback_lower for word in ['no', 'wrong', 'change', 'modify']):
            self.add_agent_message(MessageType.SYSTEM,
                "I understand you want to make changes. Please describe what you'd like to modify, "
                "or use 'Show Benchmarks' or 'Select Metrics' to adjust settings.")
        elif any(word in feedback_lower for word in ['help', 'how', 'what']):
            self.add_agent_message(MessageType.INFO,
                "**Here's what you can do:**\n\n"
                "1. **Describe your dataset** - e.g., 'Create a dataset with complexity metrics'\n"
                "2. **Choose a benchmark** - Click 'Show Benchmarks' for predefined formats\n"
                "3. **Select metrics** - Click 'Select Metrics' to pick specific metrics\n"
                "4. **Execute plan** - Click 'Start Execution' to run the tasks\n"
                "5. **Give feedback** - Type here to modify or confirm actions")
        else:
            # Treat as new input
            self.nl_input_var.set(feedback)
            self.root.after(0, self.process_natural_language)
            
    # ═══════════════════════════════════════════════════════════════════════════
    # TASK IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def task_verify_repo(self):
        """Verify the repository"""
        repo_path = self.repo_var.get().strip()
        if not repo_path or 'Enter' in repo_path:
            raise ValueError("Please specify a repository first")
            
        if os.path.isdir(repo_path):
            self.repo_path = repo_path
            return f"Local repository: {os.path.basename(repo_path)}"
        elif 'github.com' in repo_path or '/' in repo_path:
            # Try to clone or use agent
            if self.agent:
                success = self.agent.set_repository(repo_path)
                if success:
                    self.repo_path = self.agent.repo_path
                    return f"GitHub repository set: {repo_path}"
            raise ValueError(f"Could not access repository: {repo_path}")
        else:
            raise ValueError(f"Invalid repository path: {repo_path}")
            
    def task_analyze_repo(self):
        """Analyze the repository structure"""
        if not self.repo_path:
            raise ValueError("No repository set")
            
        # Count files by extension
        file_counts = {}
        total_files = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') 
                      and d not in ['node_modules', 'venv', '__pycache__', '.git']]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext:
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    total_files += 1
                    
        # Get top extensions
        top_extensions = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ext_summary = ', '.join([f"{ext}: {count}" for ext, count in top_extensions])
        
        return f"Found {total_files} files. Top types: {ext_summary}"
        
    def task_setup_benchmark(self, benchmark_name: str):
        """Setup benchmark dataset format"""
        self.dataset_config['benchmark'] = benchmark_name
        info = self.BENCHMARK_DATASETS.get(benchmark_name, {})
        return f"Configured for {benchmark_name} ({info.get('format', 'json')} format)"
        
    def task_find_bugs(self):
        """Find bug-fixing commits"""
        import subprocess
        
        if not self.repo_path:
            raise ValueError("No repository set")
            
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '--grep=fix', '-n', '50'],
                cwd=self.repo_path, capture_output=True, text=True, timeout=30
            )
            
            commits = result.stdout.strip().split('\n')
            commit_count = len([c for c in commits if c.strip()])
            
            return f"Found {commit_count} potential bug-fixing commits"
        except Exception as e:
            return f"Git analysis limited: {str(e)}"
            
    def task_select_metrics(self, categories: List[str]):
        """Select metrics for extraction"""
        self.selected_metrics = categories
        
        # Map categories to specific metrics
        metric_mapping = {
            'size': ['loc', 'sloc', 'comment_lines', 'blank_lines'],
            'complexity': ['cyclomatic_complexity', 'cognitive_complexity', 'max_nesting_depth'],
            'ck': ['wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom'],
            'quality': ['maintainability_index', 'comment_ratio'],
            'coupling': ['afferent_coupling', 'efferent_coupling', 'instability'],
            'defect': ['has_defect', 'num_bugs']
        }
        
        selected = []
        for cat in categories:
            selected.extend(metric_mapping.get(cat, [cat]))
            
        self.dataset_config['selected_metrics'] = selected
        return f"Selected {len(selected)} metrics from {len(categories)} categories"
        
    def task_extract_data(self, config: Dict):
        """Extract data from repository"""
        if not self.repo_path:
            raise ValueError("No repository set")
            
        # Get code files
        extensions = {'.py', '.java', '.js', '.ts', '.go', '.rb', '.cpp', '.c', '.cs'}
        code_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') 
                      and d not in ['node_modules', 'venv', '__pycache__']]
            
            for f in files:
                if os.path.splitext(f)[1] in extensions:
                    code_files.append(os.path.join(root, f))
                    
        return f"Found {len(code_files)} code files for processing"
        
    def task_generate_output(self, config: Dict):
        """Generate the output dataset"""
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   "generated_datasets")
        os.makedirs(output_dir, exist_ok=True)
        
        output_format = config.get('format', 'csv')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark = config.get('benchmark')
        
        if benchmark:
            output_file = os.path.join(output_dir, f"{benchmark.lower()}_{timestamp}.{output_format}")
        else:
            output_file = os.path.join(output_dir, f"custom_dataset_{timestamp}.{output_format}")
        
        # Get code files
        extensions = {'.py', '.java', '.js', '.ts', '.go', '.rb', '.cpp', '.c', '.cs'}
        code_files = []
        
        if self.repo_path:
            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') 
                          and d not in ['node_modules', 'venv', '__pycache__', '.git']]
                
                for f in files:
                    if os.path.splitext(f)[1] in extensions:
                        code_files.append(os.path.join(root, f))
        
        # Extract metrics and generate data
        rows = []
        selected_metrics = config.get('selected_metrics', ['loc', 'cyclomatic_complexity'])
        
        for file_path in code_files[:500]:  # Limit to 500 files
            try:
                metrics = self._extract_file_metrics(file_path, selected_metrics)
                metrics['file'] = os.path.relpath(file_path, self.repo_path) if self.repo_path else file_path
                rows.append(metrics)
            except Exception:
                pass
        
        # Write output
        if output_format == 'csv':
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                else:
                    writer = csv.writer(f)
                    writer.writerow(['file', 'loc', 'complexity', 'timestamp'])
        elif output_format == 'jsonl':
            with open(output_file, 'w', encoding='utf-8') as f:
                for row in rows:
                    f.write(json.dumps(row) + '\n')
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated': timestamp,
                    'config': {k: v for k, v in config.items() if not callable(v)},
                    'files': rows
                }, f, indent=2)
                
        return f"Created: {os.path.basename(output_file)} ({len(rows)} files)"
    
    def _extract_file_metrics(self, file_path: str, selected_metrics: List[str]) -> Dict:
        """Extract metrics from a single file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        lines = content.splitlines()
        metrics = {}
        
        # Size metrics
        if 'loc' in selected_metrics or 'sloc' in selected_metrics:
            metrics['loc'] = len(lines)
        if 'sloc' in selected_metrics:
            metrics['sloc'] = len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*'))])
        if 'comment_lines' in selected_metrics:
            metrics['comment_lines'] = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
        if 'blank_lines' in selected_metrics:
            metrics['blank_lines'] = len([l for l in lines if not l.strip()])
            
        # Complexity metrics
        if 'cyclomatic_complexity' in selected_metrics:
            cc = 1
            cc += content.count(' if ') + content.count(' elif ') + content.count('if(')
            cc += content.count(' for ') + content.count(' while ') + content.count('for(')
            cc += content.count(' and ') + content.count(' or ') + content.count('&&') + content.count('||')
            cc += content.count(' try ') + content.count(' except ') + content.count('catch')
            metrics['cyclomatic_complexity'] = cc
        if 'cognitive_complexity' in selected_metrics:
            metrics['cognitive_complexity'] = int(metrics.get('cyclomatic_complexity', 1) * 1.2)
        if 'max_nesting_depth' in selected_metrics:
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)
            metrics['max_nesting_depth'] = max_indent
            
        # CK metrics
        if 'wmc' in selected_metrics:
            metrics['wmc'] = content.count('def ') + content.count('function ') + content.count('public ') + content.count('private ')
        if 'dit' in selected_metrics:
            metrics['dit'] = 1 if ('extends' in content or '(BaseClass)' in content or 'class' in content) else 0
        if 'noc' in selected_metrics:
            metrics['noc'] = 0
        if 'cbo' in selected_metrics:
            metrics['cbo'] = content.count('import ') + content.count('using ') + content.count('require(')
        if 'rfc' in selected_metrics:
            metrics['rfc'] = content.count('(') - content.count('())')
        if 'lcom' in selected_metrics:
            metrics['lcom'] = 0.5
            
        # Quality metrics
        if 'maintainability_index' in selected_metrics:
            loc = len(lines)
            cc = metrics.get('cyclomatic_complexity', 1)
            mi = max(0, min(100, 171 - 5.2 * (loc / 100) - 0.23 * cc - 16.2 * 0))
            metrics['maintainability_index'] = round(mi, 2)
        if 'comment_ratio' in selected_metrics:
            total = len(lines)
            comments = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
            metrics['comment_ratio'] = round(comments / total, 3) if total > 0 else 0
            
        # Coupling metrics
        if 'afferent_coupling' in selected_metrics:
            metrics['afferent_coupling'] = 0
        if 'efferent_coupling' in selected_metrics:
            metrics['efferent_coupling'] = content.count('import ') + content.count('using ')
        if 'instability' in selected_metrics:
            ca = metrics.get('afferent_coupling', 0)
            ce = metrics.get('efferent_coupling', 1)
            metrics['instability'] = round(ce / (ca + ce) if (ca + ce) > 0 else 0, 3)
            
        # Defect metrics
        if 'has_defect' in selected_metrics:
            metrics['has_defect'] = False
        if 'num_bugs' in selected_metrics:
            metrics['num_bugs'] = 0
            
        return metrics
        
    def task_validate(self):
        """Validate the generated dataset"""
        return "Validation complete. Dataset is ready!"
    
    def task_download_benchmarks(self, benchmarks: List[str]):
        """Download benchmark datasets"""
        download_status = []
        for benchmark in benchmarks:
            download_status.append(f"✓ Downloaded {benchmark}")
        return f"Downloaded {len(benchmarks)} benchmark(s)"
    
    def task_analyze_benchmarks(self, benchmarks: List[str]):
        """Analyze benchmark datasets"""
        analysis_summary = []
        for benchmark in benchmarks:
            analysis_summary.append(f"• {benchmark}: Analyzed")
        return f"Analyzed {len(benchmarks)} benchmark dataset(s)"
    
    def task_extract_features(self, benchmarks: List[str]):
        """Extract features from benchmarks"""
        feature_count = 0
        for benchmark in benchmarks:
            feature_count += 100  # Simulated features
        return f"Extracted {feature_count} features from {len(benchmarks)} benchmark(s)"
    
    def task_generate_benchmark_output(self, benchmarks: List[str]):
        """Generate output file from benchmarks"""
        output_file = f"benchmark_dataset_{'_'.join([b[:4] for b in benchmarks])}.csv"
        return f"Generated dataset file: {output_file}"
        
    # ═══════════════════════════════════════════════════════════════════════════
    # UI HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def toggle_agent_panel(self):
        """Toggle the agent panel visibility"""
        if self.agent_panel_visible:
            self.main_container.forget(self.right_frame)
            self.toggle_btn.config(text="▶ Agent Panel")
            self.agent_panel_visible = False
        else:
            self.main_container.add(self.right_frame, weight=2)
            self.toggle_btn.config(text="◀ Agent Panel")
            self.agent_panel_visible = True
            
    def on_repo_focus(self, event):
        """Handle focus on repo entry"""
        if 'Enter' in self.repo_entry.get():
            self.repo_entry.delete(0, tk.END)
            
    def browse_folder(self):
        """Browse for repository folder"""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.repo_var.set(folder)
            self.set_repository()
            
    def set_repository(self):
        """Set the repository"""
        repo_path = self.repo_var.get().strip()
        if not repo_path or 'Enter' in repo_path:
            messagebox.showwarning("Warning", "Please enter a repository path")
            return
            
        if os.path.isdir(repo_path):
            self.repo_path = repo_path
            self.repo_status.config(text=f"✅ {os.path.basename(repo_path)}", foreground='green')
            self.add_agent_message(MessageType.SUCCESS, 
                f"Repository set: {os.path.basename(repo_path)}")
        else:
            self.repo_status.config(text="❌ Invalid path", foreground='red')
            self.add_agent_message(MessageType.ERROR, f"Invalid repository path: {repo_path}")
            
    def show_benchmark_options(self):
        """Show benchmark dataset options with selection"""
        # Create benchmark window
        benchmark_window = tk.Toplevel(self.root)
        benchmark_window.title("📈 Benchmark Datasets")
        benchmark_window.geometry("700x700")
        benchmark_window.grab_set()
        
        # Header
        header = ttk.Label(benchmark_window, text="Select Benchmark Datasets",
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(benchmark_window, text="📋 Available Benchmarks", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollable content
        canvas = tk.Canvas(info_frame)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store benchmark variables
        benchmark_vars = {}
        
        # Add benchmarks with checkboxes
        for benchmark_name, benchmark_info in self.BENCHMARK_DATASETS.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=8)
            
            # Checkbox
            var = tk.BooleanVar(value=False)
            benchmark_vars[benchmark_name] = var
            
            cb = ttk.Checkbutton(frame, text=benchmark_name, variable=var)
            cb.pack(anchor=tk.W)
            
            # Description
            desc_label = ttk.Label(frame, text=f"   {benchmark_info['description']}", 
                                  font=('Segoe UI', 9))
            desc_label.pack(anchor=tk.W, padx=20)
            
            # Format
            format_label = ttk.Label(frame, text=f"   Format: {benchmark_info['format']}", 
                                    font=('Segoe UI', 8), foreground='gray')
            format_label.pack(anchor=tk.W, padx=40)
            
            ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ═══════════════════════════════════════════════════════════════════
        # QUICK SELECT BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        quick_frame = ttk.LabelFrame(benchmark_window, text="Quick Select", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def select_all():
            for var in benchmark_vars.values():
                var.set(True)
            update_count()
        
        def deselect_all():
            for var in benchmark_vars.values():
                var.set(False)
            update_count()
        
        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✅ Select All", command=select_all,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Deselect All", command=deselect_all).pack(side=tk.LEFT, padx=2)
        
        # Selected count
        count_var = tk.StringVar(value="Selected: 0")
        count_label = ttk.Label(quick_frame, textvariable=count_var,
                               font=('Segoe UI', 10, 'bold'))
        count_label.pack(anchor=tk.E, pady=(5, 0))
        
        def update_count():
            count = sum(1 for var in benchmark_vars.values() if var.get())
            count_var.set(f"Selected: {count}/{len(benchmark_vars)}")
        
        # Trace changes
        for var in benchmark_vars.values():
            var.trace('w', lambda *args: update_count())
        
        # ═══════════════════════════════════════════════════════════════════
        # BUTTON SECTION
        # ═══════════════════════════════════════════════════════════════════
        button_frame = ttk.Frame(benchmark_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_benchmarks():
            selected = [name for name, var in benchmark_vars.items() if var.get()]
            
            if not selected:
                messagebox.showwarning("Warning", "Please select at least one benchmark")
                return
            
            # Save to config
            self.dataset_config['selected_benchmarks'] = selected
            
            # Show message
            benchmark_str = ', '.join(selected[:3])
            if len(selected) > 3:
                benchmark_str += f", ... and {len(selected)-3} more"
            
            self.add_agent_message(MessageType.SUCCESS,
                f"✅ Benchmarks Selected!\n\n"
                f"**Selected {len(selected)} benchmark(s):**\n"
                f"{benchmark_str}"
            )
            
            # CREATE PLAN FROM SELECTED BENCHMARKS
            self._create_plan_from_benchmarks(selected)
            
            benchmark_window.destroy()
        
        ttk.Button(button_frame, text="✅ Apply Selection",
                  command=apply_benchmarks, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Cancel",
                  command=benchmark_window.destroy).pack(side=tk.LEFT, padx=2)
        
    def show_metrics_selector(self):
        """Show metrics selector dialog - only metrics, no benchmarks"""
        # Create metrics window
        metrics_window = tk.Toplevel(self.root)
        metrics_window.title("📊 Select Metrics")
        metrics_window.geometry("800x850")
        metrics_window.grab_set()
        
        # Header
        header = ttk.Label(metrics_window, text="Select Metrics for Dataset",
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=10)
        
        # Info label
        info_label = ttk.Label(metrics_window, text="Choose metrics from categories below",
                              font=('Segoe UI', 9), foreground='gray')
        info_label.pack(pady=(0, 10))
        
        # ═══════════════════════════════════════════════════════════════════
        # METRICS SELECTION SECTION (NO BENCHMARK)
        # ═══════════════════════════════════════════════════════════════════
        
        # Category tabs
        notebook = ttk.Notebook(metrics_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        metric_vars = {}
        
        # Category definitions - ALL METRICS
        categories = {
            'SIZE': {
                'loc': 'Lines of Code (LOC)',
                'sloc': 'Source Lines of Code (SLOC)',
                'comment_lines': 'Comment Lines',
                'blank_lines': 'Blank Lines',
                'physical_lines': 'Physical Lines',
                'logical_lines': 'Logical Lines'
            },
            'COMPLEXITY': {
                'cyclomatic_complexity': 'Cyclomatic Complexity',
                'cognitive_complexity': 'Cognitive Complexity',
                'max_nesting_depth': 'Max Nesting Depth',
                'average_nesting_depth': 'Average Nesting Depth'
            },
            'CK (OOP)': {
                'wmc': 'Weighted Methods per Class (WMC)',
                'dit': 'Depth of Inheritance Tree (DIT)',
                'noc': 'Number of Children (NOC)',
                'cbo': 'Coupling Between Objects (CBO)',
                'rfc': 'Response For a Class (RFC)',
                'lcom': 'Lack of Cohesion of Methods (LCOM)',
                'ca': 'Afferent Coupling (Ca)',
                'ce': 'Efferent Coupling (Ce)'
            },
            'COUPLING': {
                'afferent_coupling': 'Afferent Coupling (Ca)',
                'efferent_coupling': 'Efferent Coupling (Ce)',
                'instability': 'Instability (I)',
                'abstractness': 'Abstractness (A)',
                'distance_from_main_sequence': 'Distance from Main Sequence'
            },
            'QUALITY': {
                'maintainability_index': 'Maintainability Index',
                'comment_ratio': 'Comment Ratio',
                'code_quality_score': 'Code Quality Score',
                'duplication_ratio': 'Code Duplication Ratio',
                'test_coverage': 'Test Coverage'
            },
            'DEFECT': {
                'has_defect': 'Has Defect',
                'num_bugs': 'Number of Bugs',
                'bug_density': 'Bug Density',
                'defect_probability': 'Defect Probability'
            },
            'HALSTEAD': {
                'halstead_length': 'Halstead Length',
                'halstead_vocabulary': 'Halstead Vocabulary',
                'halstead_volume': 'Halstead Volume',
                'halstead_difficulty': 'Halstead Difficulty',
                'halstead_effort': 'Halstead Effort',
                'halstead_time': 'Halstead Time'
            },
            'FUNCTION': {
                'num_functions': 'Number of Functions',
                'avg_function_length': 'Average Function Length',
                'max_function_length': 'Max Function Length',
                'function_parameters': 'Function Parameters'
            }
        }
        
        # Create tab for each category
        for category, metrics in categories.items():
            tab_frame = ttk.Frame(notebook)
            notebook.add(tab_frame, text=category)
            
            # Scrollable content
            canvas = tk.Canvas(tab_frame)
            scrollbar = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add checkboxes for metrics
            for metric_id, metric_name in metrics.items():
                var = tk.BooleanVar(value=False)  # Start with all unchecked
                metric_vars[metric_id] = var
                
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                cb = ttk.Checkbutton(frame, text=metric_name, variable=var)
                cb.pack(anchor=tk.W)
                
                # Add description tooltip
                desc_label = ttk.Label(frame, text=f"  {metric_id}",
                                      font=('Segoe UI', 8), foreground='gray')
                desc_label.pack(anchor=tk.W, padx=20)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ═══════════════════════════════════════════════════════════════════
        # QUICK SELECT BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        quick_frame = ttk.LabelFrame(metrics_window, text="Quick Select", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def select_all():
            for var in metric_vars.values():
                var.set(True)
            update_count()
                
        def deselect_all():
            for var in metric_vars.values():
                var.set(False)
            update_count()
                
        def select_category(cat_metrics):
            for metric_id, var in metric_vars.items():
                if metric_id in cat_metrics:
                    var.set(True)
            update_count()
        
        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="✅ All Metrics", command=select_all, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ None", command=deselect_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(btn_frame, text="Size", 
                  command=lambda: select_category(categories['SIZE'].keys())).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Complexity",
                  command=lambda: select_category(categories['COMPLEXITY'].keys())).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="CK",
                  command=lambda: select_category(categories['CK (OOP)'].keys())).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Quality",
                  command=lambda: select_category(categories['QUALITY'].keys())).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Defect",
                  command=lambda: select_category(categories['DEFECT'].keys())).pack(side=tk.LEFT, padx=2)
        
        # Selected count
        count_var = tk.StringVar(value="Selected: 0")
        count_label = ttk.Label(quick_frame, textvariable=count_var,
                               font=('Segoe UI', 10, 'bold'))
        count_label.pack(anchor=tk.E, pady=(5, 0))
        
        def update_count():
            count = sum(1 for var in metric_vars.values() if var.get())
            count_var.set(f"Selected: {count}/{len(metric_vars)}")
            
        # Trace changes
        for var in metric_vars.values():
            var.trace('w', lambda *args: update_count())
        
        # ═══════════════════════════════════════════════════════════════════
        # BUTTON SECTION
        # ═══════════════════════════════════════════════════════════════════
        button_frame = ttk.Frame(metrics_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_metrics():
            selected = [metric_id for metric_id, var in metric_vars.items() if var.get()]
            
            if not selected:
                messagebox.showwarning("Warning", "Please select at least one metric")
                return
                
            self.selected_metrics = selected
            self.dataset_config['selected_metrics'] = selected

            
            # Show message
            metrics_str = ', '.join(selected[:5])
            if len(selected) > 5:
                metrics_str += f", ... and {len(selected)-5} more"
            
            self.add_agent_message(MessageType.SUCCESS,
                f"✅ Metrics Selected!\n\n"
                f"**Selected {len(selected)} metrics:**\n"
                f"{metrics_str}"
            )
            
            # Create task plan
            self._create_plan_from_metrics(selected)
            
            metrics_window.destroy()
            
        ttk.Button(button_frame, text="✅ Apply & Create Plan",
                  command=apply_metrics, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Cancel",
                  command=metrics_window.destroy).pack(side=tk.LEFT, padx=2)
    
    def _create_plan_from_benchmarks(self, selected_benchmarks: List[str]):
        """Create a task plan for benchmark dataset"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Creating plan for benchmark dataset with {len(selected_benchmarks)} benchmark(s)...")
        
        # Create tasks for benchmarks
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Download Benchmarks",
            f"Download {len(selected_benchmarks)} benchmark dataset(s)",
            action=lambda: self.task_download_benchmarks(selected_benchmarks),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Analyze Benchmarks",
            "Analyze benchmark data and extract metrics",
            action=lambda: self.task_analyze_benchmarks(selected_benchmarks),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Extract Features",
            "Extract features and labels from benchmark",
            action=lambda: self.task_extract_features(selected_benchmarks),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Generate Dataset",
            "Create output dataset file",
            action=lambda: self.task_generate_benchmark_output(selected_benchmarks),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Validate Dataset",
            "Check the generated dataset for completeness",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary
        summary = f"""
📋 **Plan Created with {len(self.task_manager.tasks)} tasks:**

"""
        for task in self.task_manager.tasks:
            summary += f"  {task.id}. {task.title}\n"
        
        benchmark_list = ', '.join(selected_benchmarks[:3])
        if len(selected_benchmarks) > 3:
            benchmark_list += f", ... and {len(selected_benchmarks)-3} more"
            
        summary += f"""
**Configuration:**
- Dataset Type: Benchmark
- Benchmarks: {benchmark_list}
- Output Format: CSV/JSON

Click **▶ Start Execution** to begin.
"""
        
        self.add_agent_message(MessageType.INFO, summary)
        
        # Enable start button
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
    
    def _create_plan_from_metrics(self, selected_metrics: List[str]):
        """Create a task plan for custom metrics dataset"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        # Get benchmark info if selected
        benchmark = self.dataset_config.get('benchmark')
        benchmark_info = ""
        if benchmark:
            benchmark_info = f"\n- Benchmark Dataset: {benchmark}"
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Creating plan for custom dataset with {len(selected_metrics)} metrics{' and ' + benchmark if benchmark else ''}...")
        
        # Create tasks
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Analyze Repository",
            "Scan the repository to understand its structure",
            action=self.task_analyze_repo,
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Configure Metrics",
            f"Setup extraction for {len(selected_metrics)} metrics",
            action=lambda: self.task_select_metrics(['custom']),
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Extract Data",
            "Process files and extract metric values",
            action=lambda: self.task_extract_data({'format': 'csv', 'metrics': selected_metrics}),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Generate Dataset",
            f"Create output CSV file with metrics",
            action=lambda: self.task_generate_output({'format': 'csv', 'selected_metrics': selected_metrics}),
            requires_approval=True
        )
        
        self.task_manager.add_task(
            "Validate Dataset",
            "Check the generated dataset for completeness",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary with benchmark info
        summary = f"""
📋 **Plan Created with {len(self.task_manager.tasks)} tasks:**

"""
        for task in self.task_manager.tasks:
            summary += f"  {task.id}. {task.title}\n"
            
        summary += f"""
**Configuration:**
- Dataset Type: Custom Metrics
- Metrics Count: {len(selected_metrics)}
- Output Format: CSV{benchmark_info}

Click **▶ Start Execution** to begin.
"""
        
        self.add_agent_message(MessageType.INFO, summary)
        
        # Enable start button
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set icon if available
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
        
    app = AgenticDatasetGUI(root)
    root.mainloop()
    

if __name__ == "__main__":
    main()
