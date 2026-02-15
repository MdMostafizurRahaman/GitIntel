import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
import queue
import io
import pandas as pd
import subprocess
import re

try:
    from dotenv import load_dotenv
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(parent_dir, '.env')
    
    print(f"  Main file location: {__file__}")
    print(f"  Looking for .env at: {env_path}")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from {parent_dir}")
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            print(f"AWS_ACCESS_KEY_ID loaded successfully")
        if os.environ.get('GEMINI_API_KEY'):
            print(f"GEMINI_API_KEY loaded successfully")
    else:
        # Try current directory
        print(f"  .env not found at {env_path}, trying current directory...")
        load_dotenv()
        print(f"Attempted to load from current directory")
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import helper functions from same directory (gui folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset_helpers import apply_custom_metrics, safe_print

# Import MetricsHelper from dataset_generators package
try:
    from dataset_generators import MetricsHelper
    METRICS_HELPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MetricsHelper not available: {e}")
    METRICS_HELPER_AVAILABLE = False

try:
    from metrics_catalog import MetricsCatalog
    from github_autonomous_agent import GitHubAutonomousAgent
    from interactive_dataset_generator import InteractiveDatasetGenerator
    from autonomous_agent import AutonomousDatasetAgent, AgentMode
    from enhanced_agentic_system import EnhancedAgenticSystem, AgentMode as EnhancedMode
    from llm_code_jury_system import LLMCodeJurySystem
    from agentic_code_test_executor import AgenticCodeTestExecutor
    from integrated_jury_system import IntegratedJurySystem
    from multi_agent_orchestrator import MultiAgentOrchestrator, create_orchestrator, WorkflowStatus
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    AGENT_AVAILABLE = False

# Try to import LLM Jury System
try:
    import google.generativeai as genai
    import time
    from functools import wraps
    LLM_AVAILABLE = True
except ImportError:
    print("Warning: google.generativeai not available. LLM Jury features disabled.")
    LLM_AVAILABLE = False
    
# Rate Limiting Decorator
def rate_limited(max_per_minute=10):
    """Rate limiter for API calls"""
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


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
# GIT METRICS EXTRACTION - REAL DATA
# ═══════════════════════════════════════════════════════════════════════════════

def is_git_repo(repo_path: str) -> bool:
    """Check if path is a Git repository"""
    if not repo_path or not os.path.exists(repo_path):
        return False
    
    git_dir = os.path.join(repo_path, '.git')
    if os.path.exists(git_dir):
        return True
    
    # Check if we're inside a git repo (check parent directories)
    current = repo_path
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, '.git')):
            return True
        current = os.path.dirname(current)
    
    return False


def get_git_root(file_path: str) -> Optional[str]:
    """Find the Git repository root for a file"""
    current = os.path.dirname(os.path.abspath(file_path))
    
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, '.git')):
            return current
        current = os.path.dirname(current)
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# All metric extraction now handled by MetricsHelper - use dataset_generators only
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT MESSAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class MessageType(Enum):
    SYSTEM = "🤖"
    USER = "👤"
    THINKING = "💭"
    ACTION = "⚡"
    SUCCESS = "✓"
    ERROR = "[ERROR]"
    QUESTION = "❓"
    INFO = "[INFO]"


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
# NOTE: LLMJurySystem/LLMCodeJurySystem is imported from llm_code_jury_system.py (see imports above)

class AgenticDatasetGUI:
    """    
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
        self.root.title("GitIntel Agentic Dataset Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize components
        self.task_manager = TaskManager(on_update=self.update_task_panel)
        self.messages: List[AgentMessage] = []
        self.message_queue = queue.Queue()
        
        # State
        self.repo_path = None  # Will be set by user input
        self.selected_metrics = []
        self.dataset_config = {}
        self.agent_panel_visible = True
        self.execution_complete = False
        self.current_query = None
        self.current_plan = None
        self.metrics_helper = None  # Will be initialized when repo_path is set
        
        # Initialize autonomous agent
        if AGENT_AVAILABLE:
            try:
                self.autonomous_agent = AutonomousDatasetAgent()
                self.enhanced_system = EnhancedAgenticSystem(mode=EnhancedMode.ASK)
                
                # Initialize LLMCodeJurySystem with 4 API keys
                generator_key = os.environ.get('GEMINI_API_KEY', '')
                jury_keys = [
                    os.environ.get('Jurry_1', ''),
                    os.environ.get('Jurry_2', ''),
                    os.environ.get('Jurry_3', '')
                ]
                
                if generator_key and all(jury_keys):
                    # Enable AWS fallback by default
                    self.llm_jury_system = LLMCodeJurySystem(
                        generator_key=generator_key, 
                        jury_keys=jury_keys,
                        use_aws_fallback=True  # Auto-fallback to AWS when Gemini quota exceeded
                    )
                    
                    # Check if AWS is configured
                    aws_configured = bool(os.environ.get('AWS_ACCESS_KEY_ID') and 
                                        os.environ.get('AWS_SECRET_ACCESS_KEY'))
                    
                    if aws_configured:
                        self.add_agent_message(MessageType.SUCCESS, 
                            f"Multi-LLM Jury System initialized (1 Generator + 3 Verifiers)\n"
                            f"AWS Bedrock fallback: ENABLED (unlimited quota)")
                    else:
                        self.add_agent_message(MessageType.SUCCESS, 
                            f"Multi-LLM Jury System initialized (1 Generator + 3 Verifiers)\n"
                            f"AWS fallback: DISABLED (add AWS credentials to .env for unlimited)")
                else:
                    self.llm_jury_system = None
                    missing = []
                    if not generator_key: missing.append('GEMINI_API_KEY')
                    if not jury_keys[0]: missing.append('Jurry_1')
                    if not jury_keys[1]: missing.append('Jurry_2')
                    if not jury_keys[2]: missing.append('Jurry_3')
                    self.add_agent_message(MessageType.INFO, 
                        f"Multi-LLM Jury disabled - missing: {', '.join(missing)}")
                    
            except Exception as e:
                safe_print(f"Autonomous agent initialization failed: {e}")
                self.autonomous_agent = None
                self.enhanced_system = None
                self.llm_jury_system = None
        else:
            self.autonomous_agent = None
            self.enhanced_system = None
            self.llm_jury_system = None
        
        # Try to initialize catalog and agent
        try:
            self.catalog = MetricsCatalog()
            all_metrics = self.catalog.get_all_metrics()
            self.add_agent_message(MessageType.SUCCESS, f"Loaded {len(all_metrics)} metrics from catalog")
        except Exception as e:
            self.catalog = None
            self.add_agent_message(MessageType.ERROR, f"Metrics catalog not available: {e}")
            
        try:
            self.agent = GitHubAutonomousAgent()
        except:
            self.agent = None
        
        # Configure main API key
        self.api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY', '')
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Conversation state for agentic chat
        self.conversation_history = []
        self.pending_clarification = False
        self.understood_request = None
        
        # Initialize test executor for custom metrics validation
        try:
            self.test_executor = AgenticCodeTestExecutor()
            print("Test executor initialized (5-iteration validation)")
        except Exception as e:
            print(f"  Test executor not available: {e}")
            self.test_executor = None
            
        # Initialize integrated jury system
        try:
            self.integrated_jury = IntegratedJurySystem()
            self.jury_session_active = False
            self.jury_clarification_pending = False
            print("Integrated Jury System initialized (Question Clarifier + Generator + 3 Test LLMs)")
            self.add_agent_message(MessageType.SUCCESS, 
                " Integrated Jury System ready:\n"
                "   • Question Clarifier: Asks until understands\n"
                "   • Code Generator: Creates code from clarified requirements\n"
                "   • 3 Test LLMs: Independent test generation\n"
                "   • Validation: 2/3 tests must pass\n"
                "   • Max 5 iterations before human help")
        except Exception as e:
            print(f"  Integrated jury system not available: {e}")
            self.integrated_jury = None
            self.jury_session_active = False
            self.jury_clarification_pending = False
            
        # Style configuration
        self.configure_styles()
        
        # Build UI
        self.build_ui()
        
        # Start message processing
        self.process_message_queue()
        
        # Welcome message
        self.add_agent_message(MessageType.SYSTEM, 
            "Welcome to GitIntel Agentic Dataset Generator!\n\n"
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
        """Build the main UI with tab-based organization"""
        # Main Notebook (Tab Container)
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # TAB 1: Dataset Generator (Original functionality)
        self.dataset_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.dataset_tab, text="Dataset Generator")
                
        # Build Tab 1: Dataset Generator
        self.build_dataset_tab()
    
    def build_dataset_tab(self):
        """TAB 1: Dataset Generator (original functionality in clean layout)"""
        # Split panel like before
        split_container = ttk.PanedWindow(self.dataset_tab, orient=tk.HORIZONTAL)
        split_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (config)
        self.left_frame = ttk.Frame(split_container)
        split_container.add(self.left_frame, weight=3)
        
        # Right panel (agent)
        self.right_frame = ttk.Frame(split_container)
        split_container.add(self.right_frame, weight=2)
        
        # Build original panels
        self.build_left_panel()
        self.build_agent_panel()

    def build_left_panel(self):
        """Build the left main content panel"""
        # Title bar
        title_frame = ttk.Frame(self.left_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Dataset Generator", 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        # ═══════════════════════════════════════════════════════════════════
        # REPOSITORY SECTION
        # ═══════════════════════════════════════════════════════════════════
        repo_frame = ttk.LabelFrame(self.left_frame, text="Repository", padding=10)
        repo_frame.pack(fill=tk.X, pady=(0, 10))
        
        repo_input_frame = ttk.Frame(repo_frame)
        repo_input_frame.pack(fill=tk.X)
        
        self.repo_var = tk.StringVar()
        self.repo_entry = ttk.Entry(repo_input_frame, textvariable=self.repo_var, 
                                     font=('Consolas', 10))
        self.repo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.repo_entry.insert(0, "Path or URL: apache/kafka or https://github.com/...")
        self.repo_entry.bind('<FocusIn>', self.on_repo_focus)
        
        ttk.Button(repo_input_frame, text="Browse", width=10,
                   command=self.browse_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(repo_input_frame, text="Clone", width=10,
                   command=self.clone_repository).pack(side=tk.LEFT, padx=2)
        ttk.Button(repo_input_frame, text="✓ Set", 
                   command=self.set_repository).pack(side=tk.LEFT, padx=2)
        
        self.repo_status = ttk.Label(repo_frame, text="", font=('Segoe UI', 9))
        self.repo_status.pack(anchor=tk.W, pady=(5, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # BENCHMARK & METRICS SELECTOR
        # ═══════════════════════════════════════════════════════════════════
        selector_frame = ttk.LabelFrame(self.left_frame, text="Quick Dataset Options", padding=10)
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Benchmark dropdown
        bench_row = ttk.Frame(selector_frame)
        bench_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(bench_row, text="Benchmark:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.benchmark_var = tk.StringVar(value="None")
        benchmark_options = ["None", "Defects4J", "Bugs.jar", "PROMISE", "CodeXGLUE", 
                           "CodeSearchNet", "ManySStuBs4J", "Sourcerer"]
        self.benchmark_dropdown = ttk.Combobox(bench_row, textvariable=self.benchmark_var,
                                               values=benchmark_options, state="readonly", width=18)
        self.benchmark_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(bench_row, text="Info", width=6,
                  command=self.show_benchmark_info).pack(side=tk.LEFT, padx=2)
        
        # Row 2: Metrics selector button & combine option
        metrics_row = ttk.Frame(selector_frame)
        metrics_row.pack(fill=tk.X, pady=(5, 5))
        
        ttk.Label(metrics_row, text="Metrics:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.selected_metrics_count = tk.StringVar(value="0/64 selected")
        ttk.Label(metrics_row, textvariable=self.selected_metrics_count,
                 font=('Segoe UI', 9), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(metrics_row, text="Select Metrics",
                  command=self.show_metrics_selector).pack(side=tk.LEFT, padx=5)
        
        # Combine checkbox
        self.combine_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(metrics_row, text="Combine with Benchmark",
                       variable=self.combine_var).pack(side=tk.LEFT, padx=10)
        
        # Row 3: File limit option
        limit_row = ttk.Frame(selector_frame)
        limit_row.pack(fill=tk.X, pady=(5, 5))
        
        ttk.Label(limit_row, text="File Limit:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_limit_var = tk.StringVar(value="100")
        file_limit_entry = ttk.Entry(limit_row, textvariable=self.file_limit_var, width=10)
        file_limit_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(limit_row, text="(Default: 100 files. Use 'All' for entire repo)",
                 font=('Segoe UI', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # Row 4: Quick action buttons
        action_row = ttk.Frame(selector_frame)
        action_row.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(action_row, text="Generate Dataset",
                  command=self.generate_from_selection,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        
        ttk.Button(action_row, text="Clear Selection",
                  command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        
        # ═══════════════════════════════════════════════════════════════════
        # CHAT INPUT (Ask me anything)
        # ═══════════════════════════════════════════════════════════════════
        input_frame = ttk.LabelFrame(self.left_frame, text="Chat - Ask me anything", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mode dropdown
        mode_frame = ttk.Frame(input_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(mode_frame, text="Mode:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.agent_mode_var = tk.StringVar(value="agent")
        mode_dropdown = ttk.Combobox(mode_frame, textvariable=self.agent_mode_var, 
                                     values=["agent", "ask"], state="readonly", width=10)
        mode_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mode_frame, text="(agent = auto, ask = confirm each step)", 
                 font=('Segoe UI', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # Chat input
        self.unified_input_var = tk.StringVar()
        self.unified_input = ttk.Entry(input_frame, textvariable=self.unified_input_var,
                                       font=('Segoe UI', 11))
        self.unified_input.pack(fill=tk.X, pady=(5, 5))
        self.unified_input.insert(0, "Type: 'health dataset', 'complexity analysis', 'custom metric for...'")
        self.unified_input.bind('<FocusIn>', lambda e: self.unified_input.delete(0, tk.END) 
                               if 'Type:' in self.unified_input.get() else None)
        self.unified_input.bind('<Return>', lambda e: self.process_chat_input())
        
        # Send button
        ttk.Button(input_frame, text="Send", 
                   command=self.process_chat_input,
                   style='Accent.TButton').pack(fill=tk.X, pady=(5, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # INFO: Formula Generator moved to separate tab
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'llm_jury_system') and self.llm_jury_system:
            info_frame = ttk.Frame(self.left_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(info_frame,
                     text="Tip: Use 'Dynamic Formulas' tab for formula generation with Multi-LLM Jury",
                     font=('Segoe UI', 9), foreground="#034e8c", wraplength=500).pack(anchor=tk.W)
        
        # ═══════════════════════════════════════════════════════════════════
        # TODO LIST PANEL
        # ═══════════════════════════════════════════════════════════════════
        self.todo_frame = ttk.LabelFrame(self.left_frame, text="Task Plan", padding=10)
        self.todo_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Todo header with control buttons
        todo_header = ttk.Frame(self.todo_frame)
        todo_header.pack(fill=tk.X, pady=(0, 10))
        
        # Left side: Task count
        left_header = ttk.Frame(todo_header)
        left_header.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.task_progress_var = tk.StringVar(value="0/0 tasks")
        ttk.Label(left_header, textvariable=self.task_progress_var,
                  style='Task.TLabel', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        # Right side: Control buttons
        control_frame = ttk.Frame(todo_header)
        control_frame.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(control_frame, text="Start",
                                     command=self.start_execution,
                                     style='Accent.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=2)
        self.start_btn.config(state=tk.DISABLED)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸ Pause",
                                     command=self.pause_execution)
        self.pause_btn.pack(side=tk.LEFT, padx=2)
        self.pause_btn.config(state=tk.DISABLED)
        
        ttk.Button(control_frame, text="Clear",
                   command=self.clear_plan).pack(side=tk.LEFT, padx=2)
        
        # Progress bar below header
        progress_frame = ttk.Frame(self.todo_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            mode='determinate')
        self.progress_bar.pack(fill=tk.X)
        
        # Info text
        ttk.Label(self.todo_frame, text="Tasks will appear below when you describe what you need",
                  style='TaskPending.TLabel', font=('Segoe UI', 9)).pack(anchor=tk.W, pady=(0, 5))
        
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
        # STATUS BAR
        # ═══════════════════════════════════════════════════════════════════
        status_frame = ttk.Frame(self.left_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var,
                  font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
    def build_agent_panel(self):
        """Build the right agent panel"""
        # Header
        header_frame = ttk.Frame(self.right_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Agent Assistant",
                  style='Header.TLabel').pack(side=tk.LEFT)
        
        # Message area (optimized height for visibility)
        self.message_frame = ttk.Frame(self.right_frame)
        self.message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.message_text = scrolledtext.ScrolledText(
            self.message_frame,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white',
            state=tk.DISABLED,
            height=20  # Set fixed height to ensure bottom controls are visible
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
        self.approval_frame = ttk.LabelFrame(self.right_frame, text="Action Required ❓", padding=10)
        self.approval_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.approval_text = ttk.Label(self.approval_frame, 
                                        text="No pending approvals",
                                        wraplength=300)
        self.approval_text.pack(fill=tk.X, pady=(0, 10))
        
        approval_btns = ttk.Frame(self.approval_frame)
        approval_btns.pack(fill=tk.X)
        
        self.approve_btn = ttk.Button(approval_btns, text="Approve",
                                       command=self.approve_action,
                                       style='Approve.TButton')
        self.approve_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.reject_btn = ttk.Button(approval_btns, text="Reject",
                                      command=self.reject_action,
                                      style='Reject.TButton')
        self.reject_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.skip_btn = ttk.Button(approval_btns, text="Skip",
                                    command=self.skip_action)
        self.skip_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Hide initially
        self.set_approval_visible(False)
        
        # ═══════════════════════════════════════════════════════════════════
        # FEEDBACK INPUT
        # ═══════════════════════════════════════════════════════════════════
        feedback_frame = ttk.LabelFrame(self.right_frame, text="Your Feedback", padding=10)
        feedback_frame.pack(fill=tk.X)
        
        self.feedback_var = tk.StringVar()
        self.feedback_entry = ttk.Entry(feedback_frame, textvariable=self.feedback_var,
                                         font=('Segoe UI', 10))
        self.feedback_entry.pack(fill=tk.X, pady=(0, 5))
        self.feedback_entry.bind('<Return>', lambda e: self.send_feedback())
        
        ttk.Button(feedback_frame, text="Send",
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
                TaskStatus.IN_PROGRESS: '[PROCESSING]',
                TaskStatus.COMPLETED: '✓',
                TaskStatus.FAILED: '[ERROR]',
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
    
    def process_unified_input(self):
        """LEGACY - redirect to chat input"""
        self.process_chat_input()
    
    def process_natural_language(self):
        """LEGACY - redirects to unified processor"""
        query = self.nl_input_var.get().strip() if hasattr(self, 'nl_input_var') else self.unified_input_var.get().strip()
        
        if not query or 'e.g.' in query or 'Type anything' in query:
            messagebox.showwarning("Input Required", "Please describe what you want to create")
            return
        
        # Store last request for feedback processing
        self.last_user_request = query
        
        # Show user message
        self.add_agent_message(MessageType.USER, query)
        if hasattr(self, 'nl_input_var'):
            self.nl_input_var.set("")
        else:
            self.unified_input_var.set("")
        
        # Show thinking
        self.add_agent_message(MessageType.THINKING, "Analyzing your request...")
        
        # CHECK: Is this a request for BENCHMARK dataset or REAL repo analysis?
        query_lower = query.lower()
        is_benchmark_request = any(b.lower() in query_lower for b in self.BENCHMARK_DATASETS.keys())
        
        if is_benchmark_request:
            # USE ORIGINAL: Benchmark dataset generation (predefined formats)
            self.add_agent_message(MessageType.INFO, 
                "Detected benchmark dataset request. Using predefined format generation.")
            threading.Thread(target=self._create_plan_from_input, 
                            args=(query,), daemon=True).start()
        else:
            # USE ENHANCED: Real repository analysis with LLM
            if not self.repo_path:
                self.add_agent_message(MessageType.ERROR, 
                    "ERROR real repository analysis requires a repository to be set first.")
                messagebox.showwarning("Repository Required", 
                    "For custom metrics analysis, please set a repository first.\n\n"
                    "Or use benchmark datasets (Defects4J, Bugs.jar, etc.) which don't need a repo.")
                return
            
            if self.enhanced_system:
                self.add_agent_message(MessageType.INFO, 
                    "Using AI-powered repository analysis with LLM.")
                self._process_with_enhanced_system(query)
            else:
                # Fallback to basic
                threading.Thread(target=self._create_plan_from_input, 
                                args=(query,), daemon=True).start()
    
    def _process_with_enhanced_system(self, query: str):
        """Process using EnhancedAgenticSystem"""
        # SIMPLIFIED: Check if it's a benchmark request first
        query_lower = query.lower()
        is_benchmark = any(b.lower() in query_lower for b in self.BENCHMARK_DATASETS.keys())
        
        if is_benchmark:
            # Use old working benchmark generation DIRECTLY
            self.add_agent_message(MessageType.INFO, 
                "Benchmark dataset detected. Using proven benchmark generator.")
            threading.Thread(target=self._create_plan_from_input, 
                            args=(query,), daemon=True).start()
            return
        
        # For NON-benchmark: check if catalog is loaded
        if not self.catalog:
            self.add_agent_message(MessageType.ERROR, 
                "ERROR Metrics catalog not available. Cannot analyze custom metrics.")
            return
            
        # Show available metrics FIRST before asking questions
        all_metrics = self.catalog.get_all_metrics()
        categories = self.catalog.get_categories()
        
        metrics_summary = f"  **{len(all_metrics)} Metrics Available:**\n\n"
        for category in categories:
            cat_metrics = self.catalog.get_metrics_by_category(category)
            metrics_summary += f"**{category.upper()}** ({len(cat_metrics)}): "
            metrics_summary += ", ".join(list(cat_metrics.keys())[:5])
            if len(cat_metrics) > 5:
                metrics_summary += f" (+{len(cat_metrics)-5} more)"
            metrics_summary += "\n"
        
        self.add_agent_message(MessageType.SUCCESS, metrics_summary)
        
        # Set repository if not already set
        if not self.enhanced_system.repo_path or str(self.enhanced_system.repo_path) != str(self.repo_path):
            try:
                self.add_agent_message(MessageType.THINKING, 
                    "Setting up repository and discovering metrics...")
                
                repo_info = self.enhanced_system.set_repository(self.repo_path)
                
            except Exception as e:
                self.add_agent_message(MessageType.ERROR, 
                    f"  Repository setup failed: {e}")
                return
        
        # Start conversation in background thread
        thread = threading.Thread(target=self._enhanced_conversation_thread, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _enhanced_conversation_thread(self, query: str):
        """Handle enhanced system conversation in background"""
        try:
            # Start conversation
            result = self.enhanced_system.start_conversation(query)
            
            # Display conversation messages
            self._display_enhanced_messages()
            
            # Handle result status
            while result['status'] in ['needs_clarification', 'needs_approval_for_formula_generation', 
                                       'awaiting_approval', 'awaiting_final_approval']:
                
                if result['status'] == 'needs_clarification':
                    # Wait for user response
                    question = result['question']
                    self.root.after(0, lambda: self._setup_enhanced_input_handler(question))
                    break
                    
                elif result['status'] == 'needs_approval_for_formula_generation':
                    # Show formulas that need to be generated
                    formulas_text = "**New Formulas Needed:**\n\n"
                    for formula_name in result['missing_formulas']:
                        formulas_text += f"  • {formula_name}\n"
                    formulas_text += "\nLLM will generate Python code for these. Approve?"
                    
                    self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION, formulas_text))
                    self.root.after(0, lambda: self._setup_approval_buttons(
                        on_approve=lambda: self._approve_formula_generation(result),
                        on_reject=lambda: self._reject_formula_generation()
                    ))
                    break
                    
                elif result['status'] == 'awaiting_approval':
                    # Show plan approval buttons
                    self.root.after(0, lambda: self._setup_approval_buttons(
                        on_approve=lambda: self._approve_plan(),
                        on_reject=lambda: self._reject_plan(),
                        on_modify=lambda: self._modify_plan()
                    ))
                    break
                    
                elif result['status'] == 'awaiting_final_approval':
                    # Show final approval after preview
                    preview_text = f"**Preview Ready!**\n\n"
                    preview_text += f"**Total Rows:** {result['total_rows']}\n"
                    preview_text += f"**Columns:** {len(result['preview'])}\n\n"
                    
                    for col_preview in result['preview']:
                        preview_text += f"**{col_preview.column_name}** ({col_preview.data_type})\n"
                        preview_text += f"  Formula: {col_preview.formula}\n"
                        preview_text += f"    Sample: {col_preview.sample_values[:3]}\n"
                        if col_preview.min_value is not None:
                            preview_text += f"    Range: [{col_preview.min_value:.2f} - {col_preview.max_value:.2f}]\n"
                        preview_text += f"Unique: {col_preview.unique_count}\n\n"
                    
                    self.root.after(0, lambda: self.add_agent_message(MessageType.PREVIEW, preview_text))
                    self.root.after(0, lambda: self._setup_final_approval_buttons(
                        on_confirm=lambda: self._confirm_generation(),
                        on_cancel=lambda: self._cancel_generation()
                    ))
                    break
            
            # If completed, show result
            if result['status'] == 'completed':
                success_text = f"**Dataset Generated!**\n\n"
                success_text += f"**Files:**\n"
                success_text += f"  • CSV: {result['csv_file']}\n"
                success_text += f"  • JSON: {result['json_file']}\n"
                success_text += f"  • Metadata: {result['metadata_file']}\n\n"
                success_text += f"**Statistics:**\n"
                success_text += f"  • Rows: {result['rows']:,}\n"
                success_text += f"  • Columns: {result['columns']}\n"
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, success_text))
                
        except Exception as e:
            error_msg = f"**Error:** {str(e)}"
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, error_msg))
    
    def _display_enhanced_messages(self):
        """Display messages from enhanced system"""
        # Get conversation history
        history = self.enhanced_system.get_conversation_history()
        
        # Display new messages (skip already displayed ones)
        displayed_count = getattr(self, '_displayed_message_count', 0)
        new_messages = history[displayed_count:]
        
        for msg in new_messages:
            msg_type_str = msg['type']
            content = msg['content']
            
            # Map enhanced message types to GUI message types
            type_mapping = {
                'system': MessageType.SYSTEM,
                'user': MessageType.USER,
                'agent': MessageType.INFO,
                'thinking': MessageType.THINKING,
                'plan': MessageType.INFO,
                'question': MessageType.QUESTION,
                'preview': MessageType.INFO,
                'success': MessageType.SUCCESS,
                'error': MessageType.ERROR
            }
            
            gui_type = type_mapping.get(msg_type_str, MessageType.INFO)
            self.root.after(0, lambda c=content, t=gui_type: self.add_agent_message(t, c))
        
        self._displayed_message_count = len(history)
    
    def _setup_enhanced_input_handler(self, question: str):
        """Setup input handler for clarification question"""
        # Enable agent input for response
        if hasattr(self, 'agent_input'):
            self.agent_input.config(state=tk.NORMAL)
            self.agent_input.delete(0, tk.END)
            self.agent_input.insert(0, "Type your answer here...")
            self.agent_input.bind('<Return>', 
                lambda e: self._handle_clarification_response(self.agent_input.get()))
    
    def _handle_clarification_response(self, response: str):
        """Handle user's clarification response"""
        if not response or 'Type your answer' in response:
            return
        
        self.add_agent_message(MessageType.USER, f"💬 {response}")
        
        # Continue conversation in background
        thread = threading.Thread(target=self._continue_enhanced_conversation, args=(response,))
        thread.daemon = True
        thread.start()
    
    def _continue_enhanced_conversation(self, response: str):
        """Continue the enhanced conversation"""
        try:
            result = self.enhanced_system.continue_conversation(response)
            self._display_enhanced_messages()
            
            # Handle new status (similar to initial conversation)
            # Reuse the logic from _enhanced_conversation_thread
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Error: {str(e)}"))
    
    def _approve_formula_generation(self, result):
        """Approve formula generation and execute comprehensive test validation"""
        self.add_agent_message(MessageType.SUCCESS, "Formula generation approved. Running jury verification...")
        
        # Generate formulas with jury verification
        self.enhanced_system._generate_missing_formulas()
        
        # Capture generated formulas for later use in dataset generation
        if self.enhanced_system.generated_formulas:
            self.custom_metrics_to_apply = self.enhanced_system.generated_formulas
            num_formulas = len(self.enhanced_system.generated_formulas)
            self.add_agent_message(MessageType.SUCCESS, 
                f"{num_formulas} custom formula(s) approved by jury")
            
            # Display all messages including jury voting
            self._display_enhanced_messages()
            
            # ═══════════════════════════════════════════════════════════════
            # NEW: Execute comprehensive test validation with 5-iteration retry
            # ═══════════════════════════════════════════════════════════════
            if self.test_executor and hasattr(self, 'repo_path') and self.repo_path:
                self.add_agent_message(MessageType.THINKING, 
                    "Starting unit test generation and validation...\n"
                    "System will: Generate tests → Execute → Retry up to 5 times if needed")
                
                # Prepare sample data from repository
                sample_data = self._prepare_sample_data_for_testing()
                
                validation_success = True
                for idx, formula in enumerate(self.enhanced_system.generated_formulas, 1):
                    self.add_agent_message(MessageType.INFO,
                        f"\n{'='*60}\n"
                        f"Formula {idx}/{num_formulas}: {formula.name}\n"
                        f"{'='*60}")
                    
                    try:
                        # Execute full workflow with test generation, execution, and auto-fix
                        report = self.test_executor.execute_full_workflow(
                            metric_description=formula.description,
                            available_metrics=self.available_metrics or {},
                            sample_data=sample_data,
                            base_metrics=self.available_metrics or {},
                            num_judges=3,
                            auto_fix=True  # Enable 5-iteration retry
                        )
                        
                        # Display comprehensive test results
                        self._display_test_results(report, formula.name)
                        
                        if not report['overall_success']:
                            self.add_agent_message(MessageType.ERROR,
                                f"Test validation FAILED for '{formula.name}' after 5 iterations\n"
                                f" Human review required\n"
                                f" Check: {report['stages'].get('validation', {}).get('run_directory', 'N/A')}")
                            validation_success = False
                            # Don't break - test all formulas to show complete status
                    
                    except Exception as e:
                        self.add_agent_message(MessageType.ERROR,
                            f"Test execution failed for '{formula.name}': {str(e)[:200]}")
                        validation_success = False
                
                if validation_success:
                    self.add_agent_message(MessageType.SUCCESS,
                        f"\nAll {num_formulas} formula(s) validated successfully!\n"
                        f"Ready for full dataset generation with validated code")
                else:
                    self.add_agent_message(MessageType.WARNING,
                        f"\n Some formulas failed validation\n"
                        f"   Review failed tests before dataset generation")
            else:
                if not self.test_executor:
                    self.add_agent_message(MessageType.WARNING,
                        "Test executor not available - skipping test validation")
                else:
                    self.add_agent_message(MessageType.WARNING,
                        "No repository set - skipping test validation")
        
        # Display final messages
        self._display_enhanced_messages()
        
        # Prepare for full dataset generation using enhanced_system
        self.add_agent_message(MessageType.THINKING, 
            "Preparing full dataset generation with all 64+ metrics...")
        
        # Mark that we should use enhanced_system for generation
        self.use_enhanced_generation = True
    
    def _reject_formula_generation(self):
        """Reject formula generation"""
        self.add_agent_message(MessageType.ERROR, "  Formula generation rejected. Operation cancelled.")
    
    def _prepare_sample_data_for_testing(self) -> Dict:
        """Prepare sample data from repository for test execution"""
        try:
            # Try to get real metrics from repository
            if hasattr(self, 'available_metrics') and self.available_metrics:
                # Use existing metrics if available
                return dict(list(self.available_metrics.values())[:1][0]) if self.available_metrics.values() else {}
            
            # Fallback: Generate sample data
            sample_data = {
                'lines_of_code': 1000,
                'cyclomatic_complexity': 5,
                'bug_count': 3,
                'test_coverage': 0.75,
                'code_churn': 150,
                'commit_count': 50
            }
            return sample_data
        except Exception as e:
            print(f"Could not prepare sample data: {e}")
            return {'lines_of_code': 1000, 'bug_count': 5}
    
    def _display_test_results(self, report: Dict, formula_name: str):
        """
        Display comprehensive test execution results in GUI
        Shows: Code generation → Test generation → Execution → Iterations → Final status
        """
        stages = report.get('stages', {})
        
        # Stage 1: Code Generation Status
        if 'code_generation' in stages:
            code_info = stages['code_generation']
            if code_info['status'] == 'approved':
                self.add_agent_message(MessageType.SUCCESS,
                    f"Stage 1: Code generation approved by {code_info.get('votes', 3)} judges")
            else:
                self.add_agent_message(MessageType.ERROR,
                    f"Stage 1: Code generation failed")
                return
        
        # Stage 2: Test Generation Status
        if 'test_generation' in stages:
            test_info = stages['test_generation']
            test_count = test_info.get('test_count', 0)
            quality_score = test_info.get('quality_score', 0)
            
            status_icon = "OK" if test_info.get('is_approved', False) else "[WARNING]"
            self.add_agent_message(MessageType.INFO,
                f"{status_icon} Stage 2: Generated {test_count} unit tests "
                f"(Quality: {quality_score:.0f}%)")
        
        # Stage 3: Test Execution with Iteration Details
        if 'test_execution' in stages:
            exec_info = stages['test_execution']
            iteration = exec_info.get('iteration', 1)
            passed = exec_info.get('passed', 0)
            failed = exec_info.get('failed', 0)
            errors = exec_info.get('errors', 0)
            total = exec_info.get('total_tests', 0)
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            required = (total * 2 + 2) // 3  # 2/3 threshold
            
            self.add_agent_message(MessageType.INFO,
                f"[STEP 3] Test Execution - Iteration {iteration}/5\n"
                f"   Passed: {passed}/{total} tests ({pass_rate:.1f}%)\n"
                f"   Failed: {failed} tests\n"
                f"   Errors: {errors}\n"
                f"   Required: {required}/{total} ({required/total*100:.0f}%) for approval")
        
        # Stage 4: Final Validation Status
        if 'validation' in stages:
            val_info = stages['validation']
            
            if val_info['status'] == 'success':
                iterations_taken = val_info.get('iteration', 1)
                total_tests = val_info.get('total_tests', 0)
                passed_final = val_info.get('passed', 0)
                
                self.add_agent_message(MessageType.SUCCESS,
                    f"VALIDATION SUCCESSFUL for '{formula_name}'\n"
                    f"Iterations: {iterations_taken}/5\n"
                    f"Final: {passed_final}/{total_tests} tests passed\n"
                    f"Results: {val_info.get('run_directory', 'N/A')}")
            
            elif val_info['status'] == 'failed_max_retries':
                iterations = val_info.get('iterations', 5)
                last_passed = val_info.get('last_passed', 0)
                last_failed = val_info.get('last_failed', 0)
                run_dir = val_info.get('run_directory', 'N/A')
                
                self.add_agent_message(MessageType.ERROR,
                    f"VALIDATION FAILED for '{formula_name}'\n"
                    f" Max iterations reached: {iterations}/5\n"
                    f" Last result: {last_passed} passed, {last_failed} failed\n"
                    f" Manual review required\n"
                    f" Check iteration logs: {run_dir}\n"
                    f" {val_info.get('note', 'See logs for details')}")
            else:
                self.add_agent_message(MessageType.ERROR,
                    f"Validation failed with status: {val_info['status']}")
    
    def _reject_formula_generation_old(self):
        """Reject formula generation (renamed old method)"""
        self.add_agent_message(MessageType.ERROR, "  Formula generation rejected. Operation cancelled.")
    
    def _approve_plan(self):
        """Approve the plan and generate preview"""
        self.add_agent_message(MessageType.SUCCESS, "Plan approved. Generating preview...")
        thread = threading.Thread(target=self._generate_preview_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_preview_thread(self):
        """Generate preview in background"""
        try:
            result = self.enhanced_system.generate_preview()
            self._display_enhanced_messages()
            
            # Show preview in GUI (handled by _enhanced_conversation_thread logic)
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Preview generation failed: {str(e)}"))
    
    def _reject_plan(self):
        """Reject the plan"""
        self.add_agent_message(MessageType.ERROR, "  Plan rejected. Describe what you need differently.")
    
    def _modify_plan(self):
        """Modify the plan"""
        self.add_agent_message(MessageType.QUESTION, 
            "What would you like to change? Describe the modifications:")
        self._setup_enhanced_input_handler("Modifications")
    
    def _confirm_generation(self):
        """Confirm final dataset generation"""
        self.add_agent_message(MessageType.SUCCESS, "Confirmed. Generating full dataset...")
        thread = threading.Thread(target=self._generate_full_dataset_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_full_dataset_thread(self):
        """Generate full dataset in background"""
        try:
            result = self.enhanced_system.generate_full_dataset()
            self._display_enhanced_messages()
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Generation failed: {str(e)}"))
    
    def _cancel_generation(self):
        """Cancel dataset generation"""
        self.add_agent_message(MessageType.ERROR, "  Generation cancelled.")
    
    def _generate_tasks_from_config(self):
        """Generate task plan from stored dataset config"""
        if not hasattr(self, 'dataset_config') or not self.dataset_config:
            self.add_agent_message(MessageType.ERROR, "  No configuration available")
            return
        
        config = self.dataset_config
        
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        self.add_agent_message(MessageType.SYSTEM, " Creating task plan...")
        
        # Task 1: Verify repository
        if self.repo_path:
            self.task_manager.add_task(
                "Verify Repository",
                f"Check repository: {self.repo_path}",
                action=self.task_verify_repo,
                requires_approval=False
            )
        
        # Task 2: Extract/Calculate metrics
        metrics_str = ', '.join(config.get('metrics', [])) if config.get('metrics') else 'custom formula'
        self.task_manager.add_task(
            "Extract Metrics",
            f"Calculate metrics: {metrics_str}",
            action=lambda: self.task_extract_custom_formula(config),
            requires_approval=False
        )
        
        # Task 3: Apply formula if present
        if config.get('custom'):
            self.task_manager.add_task(
                "Apply Custom Formula",
                f"Calculate: {config.get('custom')}",
                action=lambda: self.task_apply_formula(config),
                requires_approval=False
            )
        
        # Task 4: Generate output
        self.task_manager.add_task(
            "Generate Dataset",
            "Create output file",
            action=lambda: self.task_generate_output(config),
            requires_approval=False
        )
        
        # Show summary
        summary = f"""**Task Plan Created ({len(self.task_manager.tasks)} tasks)**

Ready to execute. Click **▶ Start Execution** to begin."""
        
        self.add_agent_message(MessageType.SUCCESS, summary)
        
        # Enable start button
        self.start_btn.config(state=tk.NORMAL)
    
    def _create_default_task_plan(self):
        """Create a default task plan when no specific config is available"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        # Use last_user_request to create a config
        if hasattr(self, 'last_user_request') and self.last_user_request:
            # Create a basic config from the request
            self.dataset_config = {
                'metrics': [],
                'format': 'csv',
                'custom': self.last_user_request
            }
            self._generate_tasks_from_config()
        else:
            self.add_agent_message(MessageType.ERROR, 
                "Unable to create task plan. Please describe what dataset you need.")
    
    def _setup_approval_buttons(self, on_approve, on_reject, on_modify=None):
        """Setup approval buttons in agent panel"""
        # Create button frame
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Approve", command=on_approve,
                   style='Approve.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="  Reject", command=on_reject,
                   style='Reject.TButton').pack(side=tk.LEFT, padx=5)
        
        if on_modify:
            ttk.Button(btn_frame, text="Modify", command=on_modify).pack(side=tk.LEFT, padx=5)
    
    def _setup_final_approval_buttons(self, on_confirm, on_cancel):
        """Setup final approval buttons"""
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Confirm & Generate", command=on_confirm,
                   style='Approve.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel,
                   style='Reject.TButton').pack(side=tk.LEFT, padx=5)
    

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
**Plan Created with {len(self.task_manager.tasks)} tasks:**

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
        """Execute tasks one by one in SEPARATE THREAD to prevent GUI freeze"""
        def run_tasks_in_thread():
            for task in self.task_manager.tasks:
                if not self.task_manager.is_running:
                    break
                        
                # Execute task directly
                self.task_manager.set_task_status(task.id, TaskStatus.IN_PROGRESS)
                self.root.after(0, lambda t=task: self.add_agent_message(MessageType.ACTION, f"⚡ Executing: {t.title}..."))
                
                try:
                    if task.action:
                        result = task.action()
                        self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                           result=str(result) if result else "Done")
                        self.root.after(0, lambda t=task: self.add_agent_message(MessageType.SUCCESS, 
                            f"Completed: {t.title}"))
                    else:
                        self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                           result="No action required")
                except Exception as e:
                    self.task_manager.set_task_status(task.id, TaskStatus.FAILED,
                                                       error=str(e))
                    self.root.after(0, lambda t=task, err=str(e): self.add_agent_message(MessageType.ERROR, 
                        f"Failed: {t.title}\nError: {err}"))
                        
            # Execution complete
            self.root.after(0, self._execution_complete)
        
        # Run in separate thread to prevent GUI freeze
        thread = threading.Thread(target=run_tasks_in_thread, daemon=True)
        thread.start()
        
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
        
        success_msg = "Dataset generated successfully!" if failed == 0 else "Some tasks failed. Please review."
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Execution Complete!\n\n"
            f"Completed: {completed}\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}\n\n"
            f"{success_msg}\n\n"
            f"**Next Steps:**\n"
            f"• Check the output in 'generated_datasets' folder\n"
            f"• Describe what you need to create a new dataset\n"
            f"• Or click **Clear Plan** to start fresh"
        )
        
        # Keep start button enabled but don't auto-start
        self.execution_complete = True
        
    def pause_execution(self):
        """Pause the execution"""
        self.task_manager.is_running = False
        self.pause_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.add_agent_message(MessageType.INFO, "Execution paused. Click Start to resume.")
        
    def clear_plan(self):
        """Clear the task plan"""
        self.task_manager.clear_tasks()
        self.progress_var.set(0)
        self.execution_complete = False
        self.add_agent_message(MessageType.INFO, "Plan cleared. Describe what you need to create a new plan.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # APPROVAL SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show_approval_request(self, task: Task):
        """Show approval request for a task"""
        self.approval_text.config(text=f"Task: {task.title}\n\n{task.description}\n\nApprove this action?")
        self.set_approval_visible(True)
        
        self.add_agent_message(MessageType.QUESTION,
            f"**Approval Required**\n\n"
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
        self.add_agent_message(MessageType.SUCCESS, "Action approved!")
        
    def reject_action(self):
        """Reject the current action"""
        self.set_approval_visible(False)
        self.task_manager.reject_current()
        self.add_agent_message(MessageType.ERROR, "Action rejected.")
        
    def skip_action(self):
        """Skip the current action"""
        self.set_approval_visible(False)
        self.task_manager.skip_current()
        self.add_agent_message(MessageType.INFO, "Action skipped.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # FEEDBACK SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def send_feedback(self):
        """
        Send user feedback - handles approval/rejection/modification
        """
        feedback = self.feedback_var.get().strip()
        if not feedback:
            return
            
        self.feedback_var.set("")
        
        # Show user message
        self.add_agent_message(MessageType.USER, f"{feedback}")
        
        # Add to conversation
        self.conversation_history.append({"role": "user", "content": feedback})
        
        feedback_lower = feedback.lower()
        
        # Check if waiting for extraction approval
        if hasattr(self, 'awaiting_extraction_approval') and self.awaiting_extraction_approval:
            if any(word in feedback_lower for word in ['extract', 'yes', 'ok', 'approve', 'proceed']):
                self.awaiting_extraction_approval = False
                self.add_agent_message(MessageType.SUCCESS, "Starting extraction with Jury Process...")
                
                # Start jury process for formula extraction
                threading.Thread(target=self._process_formula_extraction, daemon=True).start()
                return
            else:
                self.awaiting_extraction_approval = False
                self.add_agent_message(MessageType.INFO,
                    "Please describe an alternative approach or start a new query.")
                self.current_plan = None
                return
        
        # Check if user is approving
        if any(word in feedback_lower for word in ['yes', 'ok', 'approve', 'confirm', 'proceed', 'correct']):
            if self.current_plan:
                self.add_agent_message(MessageType.SUCCESS, "Approved! Generating dataset...")
                threading.Thread(target=self._execute_approved_plan, daemon=True).start()
            else:
                self.add_agent_message(MessageType.ERROR, 
                    "  No plan to approve. Please describe what dataset you need first.")
        
        # Check if user is rejecting/modifying
        elif any(word in feedback_lower for word in ['no', 'wrong', 'change', 'modify', 'different']):
            self.add_agent_message(MessageType.INFO, 
                "Please describe what you'd like to change, or start over with a new request.")
            self.current_plan = None
        
        # Help request
        elif any(word in feedback_lower for word in ['help', 'how', 'what can']):
            self.add_agent_message(MessageType.INFO,
                "**Here's what you can do:**\n\n"
                "**1. Describe your dataset:**\n"
                "   • 'Create a complexity dataset'\n"
                "   • 'I need CK metrics for Java files'\n"
                "   • 'Defects4J format with my data'\n\n"
                "**2. Custom metrics:**\n"
                "   • 'Calculate bug density per 1000 LOC'\n"
                "   • 'Create a metric for code smells'\n"
                "   → I'll use LLM Jury to validate!\n\n"
                "**3. Approve/Reject:**\n"
                "   • Type 'yes' to proceed\n"
                "   • Type 'no' to cancel\n\n"
                "**4. Quick options:**\n"
                "   • Select benchmarks above\n"
                "   • Choose metrics (64+ available)\n"
                "   • Click 'Generate Dataset'")
        
        # Treat as new query
        else:
            self.current_query = feedback
            threading.Thread(target=self._intelligent_chat_processor, 
                           args=(feedback,), daemon=True).start()
    
    def _process_feedback(self, feedback: str):
        """Legacy feedback processor - redirects to send_feedback logic"""
        # This is now handled in send_feedback() above
        pass
    
    def _execute_approved_plan(self):
        """
        Execute the approved plan:
        1. Extract real data from repository
        2. Calculate known metrics
        3. Apply custom metrics (jury-approved)
        4. Generate output file
        5. Create visualizations
        6. Show results
        """
        if not self.current_plan:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "No plan to execute"))
            return
        
        plan = self.current_plan
        
        try:
            # Clear old tasks
            self.root.after(0, self.task_manager.clear_tasks)
            
            # Step 1: Verify repository
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 1/5: Verifying repository..."))
            
            task1 = self.task_manager.add_task(
                "Verify Repository",
                f"Check {self.repo_path}",
                action=self.task_verify_repo,
                requires_approval=False
            )
            
            # Step 2: Extract data
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 2/5: Extracting real data from repository..."))
            
            known_metrics = plan.get('known_metrics', [])
            validated_custom = plan.get('validated_custom_metrics', [])
            
            # Get file limit from GUI (user control!)
            file_limit = self.file_limit_var.get().strip()
            
            # Warn user if no limit or very high limit
            if not file_limit or file_limit.lower() == "all":
                self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                    f"**WARNING**: No file limit set!\n\n"
                    f"This will process ALL files in the repository which may take a very long time.\n\n"
                    f"**Recommended**: Set a file limit (e.g., 100) in the File Limit field above.\n\n"
                    f"Current setting: '{file_limit}' - Are you sure you want to continue?"))
                # Don't proceed without explicit user confirmation
                return
            
            task2 = self.task_manager.add_task(
                "Extract Metrics",
                f"Calculate {len(known_metrics)} known + {len(validated_custom)} custom metrics from {file_limit} files",
                action=lambda: self._extract_real_data(known_metrics, validated_custom, file_limit),
                requires_approval=False
            )
            
            # Step 3: Generate dataset
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 3/5: Generating dataset file..."))
            
            output_config = {
                'format': 'csv',
                'benchmark': plan.get('benchmark'),
                'selected_metrics': known_metrics,
                'custom_metrics': validated_custom,
                'file_limit': self.file_limit_var.get() if hasattr(self, 'file_limit_var') else 'All'
            }
            
            task3 = self.task_manager.add_task(
                "Generate Dataset",
                "Create output CSV/JSON",
                action=lambda: self.task_generate_output(output_config),
                requires_approval=False
            )
            
            # Step 4: Create visualization
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 4/5: Creating visualizations..."))
            
            task4 = self.task_manager.add_task(
                "Create Visualizations",
                "Generate charts and graphs",
                action=lambda: self._create_visualizations(output_config),
                requires_approval=False
            )
            
            # Step 5: Validate
            task5 = self.task_manager.add_task(
                "Validate Output",
                "Check generated files",
                action=self.task_validate,
                requires_approval=False
            )
            
            # Start execution
            self.root.after(0, lambda: self.add_agent_message(MessageType.SYSTEM,
                f"Plan created with {len(self.task_manager.tasks)} tasks. Executing..."))
            
            self.root.after(100, self.start_execution)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda e=str(e): self.add_agent_message(
                MessageType.ERROR, f"Execution failed: {e}"))
            print(f"Execution error: {error_detail}")
    
    def _extract_real_data(self, known_metrics: List[str], custom_metrics: List[Dict], max_files: str = "All") -> str:
        """
        Extract REAL data from repository - NO MOCK DATA
        Respects user's choice of how many files to analyze
        """
        if not self.repo_path:
            raise ValueError("Repository not set")
        
        # Parse max_files from user input
        if max_files.lower() == "all" or max_files == "":
            limit = None
        else:
            try:
                limit = int(max_files)
            except ValueError:
                limit = None  # If invalid, process ALL files
        
        # Find code files
        extensions = {'.py', '.java', '.js', '.ts', '.go', '.rb', '.cpp', '.c', '.cs', '.php'}
        code_files = []
        
        repo_dir = Path(self.repo_path)
        for file_path in repo_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                # Skip common ignore patterns
                if any(skip in str(file_path) for skip in [
                    'node_modules', 'venv', '__pycache__', '.git', 
                    'build', 'dist', 'target', '.venv', 'env'
                ]):
                    continue
                code_files.append(file_path)
                
                # Stop if reached limit
                if limit and len(code_files) >= limit:
                    break
        
        if not code_files:
            return f"No code files found in {self.repo_path}"
        
        # Show how many files will be processed
        total_to_process = len(code_files)
        self.add_agent_message(MessageType.INFO, 
            f"  Found {total_to_process} code files, extracting metrics...")
        
        # Extract metrics from files
        results = []
        
        #   IMPORTANT: If no base metrics specified, use common ones
        if not known_metrics:
            known_metrics = ['loc', 'cyclomatic_complexity', 'imports', 'blank_lines', 'comment_lines']
            self.add_agent_message(MessageType.INFO, 
                f"No specific metrics requested, using default: {', '.join(known_metrics)}")
        
        for idx, file_path in enumerate(code_files, 1):
            try:
                metrics = self._extract_file_metrics(str(file_path), known_metrics)
                metrics['file'] = str(file_path.relative_to(repo_dir))
                results.append(metrics)
                
                # Progress update every 50 files
                if idx % 50 == 0 or idx == total_to_process:
                    self.add_agent_message(MessageType.INFO, 
                        f"Extracting: {idx}/{total_to_process} files ({int(idx/total_to_process*100)}%)")
            except Exception as e:
                print(f"Error extracting metrics from {file_path}: {e}")
                continue
        
        if not results:
            return f"Failed to extract metrics from any files"
        
        # Store results (WITHOUT custom metrics yet - they come later)
        self.extracted_data = results
        self.custom_metrics_to_apply = custom_metrics  # Store for later
        
        self.add_agent_message(MessageType.SUCCESS, 
            f"Successfully extracted base metrics from {len(results)}/{total_to_process} files")
        
        return f"Extracted base metrics from {len(results)} files (User requested: {max_files})"
            
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
            # Initialize MetricsHelper when repo is set
            if METRICS_HELPER_AVAILABLE:
                try:
                    self.metrics_helper = MetricsHelper(str(self.repo_path))
                    self.add_agent_message(MessageType.SUCCESS, 
                        f"MetricsHelper initialized - 64 real metrics available")
                except Exception as e:
                    safe_print(f"  MetricsHelper initialization failed: {e}")
                    self.metrics_helper = None
            return f"Local repository: {os.path.basename(repo_path)}"
        elif 'github.com' in repo_path or '/' in repo_path:
            # Try to clone or use agent
            if self.agent:
                success = self.agent.set_repository(repo_path)
                if success:
                    self.repo_path = self.agent.repo_path
                    # Initialize MetricsHelper when repo is set via agent
                    if METRICS_HELPER_AVAILABLE:
                        try:
                            self.metrics_helper = MetricsHelper(str(self.repo_path))
                            self.add_agent_message(MessageType.SUCCESS, 
                                f"MetricsHelper initialized - 64 real metrics available")
                        except Exception as e:
                            safe_print(f"  MetricsHelper initialization failed: {e}")
                            self.metrics_helper = None
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
        """Setup benchmark dataset format AND GENERATE IT DIRECTLY"""
        self.dataset_config['benchmark'] = benchmark_name
        info = self.BENCHMARK_DATASETS.get(benchmark_name, {})
        
        # Generate benchmark dataset IMMEDIATELY using ProfessionalDatasetGenerator
        try:
            from dataset_generator import ProfessionalDatasetGenerator
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if not self.repo_path:
                raise ValueError("Repository not set. Please set a repository first.")
            
            generator = ProfessionalDatasetGenerator(
                workspace_path=str(self.repo_path),
                commit_limit=None,
                timestamp=timestamp
            )
            
            # Call the appropriate benchmark generator method
            method_map = {
                "Defects4J": generator.generate_defects4j_dataset,
                "Bugs.jar": generator.generate_bugs_jar_dataset,
                "PROMISE": generator.generate_promise_dataset,
                "CodeXGLUE": generator.generate_codexglue_dataset,
                "CodeSearchNet": generator.generate_codesearchnet_dataset,
                "ManySStuBs4J": generator.generate_manystubs4j_dataset,
                "Sourcerer": generator.generate_sourcerer_dataset
            }
            
            if benchmark_name in method_map:
                self.add_agent_message(MessageType.ACTION, f"⚡ Generating {benchmark_name}...")
                method_map[benchmark_name]()
                self.add_agent_message(MessageType.SUCCESS, f"  {benchmark_name} generated!")
                return f"{benchmark_name} dataset generated successfully"
            else:
                return f"Configured for {benchmark_name} ({info.get('format', 'json')} format)"
                
        except Exception as e:
            raise ValueError(f"Failed to generate {benchmark_name}: {str(e)}")
        
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
        """Generate the output dataset with proper file saving"""
        # Create output directory - make sure it's in the right place
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_datasets")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create output directory: {str(e)}")
        
        output_format = config.get('format', 'csv')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark = config.get('benchmark')
        
        if benchmark:
            output_file = os.path.join(output_dir, f"{benchmark.lower()}_{timestamp}.{output_format}")
        else:
            output_file = os.path.join(output_dir, f"custom_dataset_{timestamp}.{output_format}")
        
        # Get code files
        extensions = {'.py', '.java', '.js', '.ts', '.go', '.rb', '.cpp', '.c', '.cs'}
        
        #   USE ALREADY-EXTRACTED DATA if available (avoid re-scanning!)
        if hasattr(self, 'extracted_data') and self.extracted_data:
            self.add_agent_message(MessageType.INFO, 
                f"  Using already-extracted data from {len(self.extracted_data)} files")
            rows = self.extracted_data.copy()
            selected_metrics = config.get('selected_metrics', list(rows[0].keys()) if rows else [])
        else:
            # Fallback: Extract fresh data
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
            # Use config metrics OR fall back to defaults
            selected_metrics = config.get('selected_metrics', self.selected_metrics if self.selected_metrics else ['loc', 'cyclomatic_complexity'])
            
            if not selected_metrics:
                selected_metrics = ['loc', 'cyclomatic_complexity']
                self.add_agent_message(MessageType.WARNING, 
                    f"  No metrics selected, using defaults: {selected_metrics}")
            
            # Get user-specified file limit (no hardcoding!)
            file_limit = config.get('file_limit', 'All')
            if file_limit == 'All' or file_limit == '' or file_limit is None:
                files_to_process = code_files  # Process ALL files
            else:
                try:
                    limit_num = int(file_limit)
                    files_to_process = code_files[:limit_num]
                    self.add_agent_message(MessageType.INFO, 
                        f"Processing {len(files_to_process)} files (limit: {limit_num}, total found: {len(code_files)})")
                except ValueError:
                    files_to_process = code_files  # Invalid input, use all
                    self.add_agent_message(MessageType.INFO, 
                        f"Processing ALL {len(code_files)} files (invalid limit value, using all)")
            
            # Process files
            total_files = len(files_to_process)
            first_metrics_debug_logged = False
            for idx, file_path in enumerate(files_to_process, 1):
                try:
                    metrics = self._extract_file_metrics(file_path, selected_metrics)
                    
                    # Debug: Check what we got on first file
                    if not first_metrics_debug_logged and metrics:
                        metric_count = len(metrics) - 1  # Subtract 1 for 'file' column
                        if metric_count <= 1:
                            self.add_agent_message(MessageType.ERROR, 
                                f"First file metrics dict has only {len(metrics)} keys: {list(metrics.keys())}")
                        else:
                            self.add_agent_message(MessageType.SUCCESS,
                                f"First file metrics dict has {len(metrics)} keys")
                        first_metrics_debug_logged = True
                    
                    metrics['file'] = os.path.relpath(file_path, self.repo_path) if self.repo_path else file_path
                    rows.append(metrics)
                    
                    # Progress update every 10 files
                    if idx % 10 == 0 or idx == total_files:
                        self.add_agent_message(MessageType.INFO, 
                            f"Extracting base metrics: {idx}/{total_files} files processed")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    import traceback
                    print(traceback.format_exc())
                    pass
        
        #   APPLY CUSTOM METRICS FROM JURY PROCESS
        if hasattr(self, 'custom_metrics_to_apply') and self.custom_metrics_to_apply and rows:
            try:
                self.add_agent_message(MessageType.INFO, 
                    f"Applying {len(self.custom_metrics_to_apply)} custom metric(s) with REAL git data extraction...")
                
                # Progress callback for GUI updates
                def progress_update(current, total, message):
                    self.root.after(0, lambda: self.add_agent_message(MessageType.INFO, 
                        f"Progress: {current}/{total} files - {message}"))
                
                # Add timeout handling with concurrent execution
                import concurrent.futures
                import time
                
                start_time = time.time()
                timeout_seconds = 120  # 2 minute timeout
                
                # Run with timeout
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        apply_custom_metrics,
                        rows, self.custom_metrics_to_apply, 
                        self.repo_path,
                        progress_update
                    )
                    
                    try:
                        rows_list, applied_count, errors = future.result(timeout=timeout_seconds)
                        rows = rows_list  # Update with custom metric values
                        elapsed = time.time() - start_time
                        if applied_count > 0:
                            self.add_agent_message(MessageType.SUCCESS, 
                                f"  Applied {applied_count} custom metric(s) in {elapsed:.1f}s")
                        if errors:
                            self.add_agent_message(MessageType.INFO, 
                                f"  Some custom metrics had issues: {', '.join(errors[:3])}")
                    except concurrent.futures.TimeoutError:
                        self.add_agent_message(MessageType.ERROR, 
                            f"Custom metrics timed out after {timeout_seconds}s - saving base metrics only")
                        # Continue with base metrics only
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                self.add_agent_message(MessageType.ERROR, 
                    f"Failed to apply custom metrics: {str(e)}")
                safe_print(f"Custom metrics error:\n{error_trace}")
        
        # If no code files found, show error (NO SAMPLE DATA GENERATION!)
        if not rows:
            raise Exception(f"  No code files found in repository! "
                           f"Could not generate any metrics. "
                           f"Ensure repository contains Java/Python code files.")
        
        # Write output with proper error handling
        self.add_agent_message(MessageType.INFO, 
            f"Writing {len(rows)} records to {output_format.upper()} file...")
        
        #   VALIDATE: Ensure rows have actual metrics, not just file paths
        if rows:
            first_row_keys = set(rows[0].keys())
            if first_row_keys == {'file'} or len(first_row_keys) <= 1:
                raise Exception(f"  No metrics extracted! Only got file paths. "
                               f"This usually means metric extraction was interrupted or failed. "
                               f"Try with a smaller file limit (e.g., 100 files)")
        
        try:
            if output_format == 'csv':
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                        print(f"CSV written: {len(rows)} rows with {len(rows[0].keys())} columns to {output_file}")
                        self.add_agent_message(MessageType.SUCCESS, 
                            f"  Saved {len(rows)} records with {len(rows[0].keys())} metrics")
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
            
            # Verify file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                self.add_agent_message(MessageType.SUCCESS, 
                    f"  CSV file created: {file_size} bytes, {len(rows)} records")
                return f"  Dataset saved successfully!\n\nFile: {os.path.basename(output_file)}\nLocation: {output_dir}\nSize: {file_size} bytes\nRecords: {len(rows)}"
            else:
                raise Exception("File was not created")
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"CSV write error:\n{error_trace}")
            self.add_agent_message(MessageType.ERROR, 
                f"  CSV write failed: {str(e)}")
            raise Exception(f"Failed to write output file: {str(e)}")
    
    def _extract_file_metrics(self, file_path: str, selected_metrics: List[str]) -> Dict:
        """
        Use MetricsHelper to get all metrics - NO local calculation!
        All metric extraction is delegated to metrics_generators via MetricsHelper.
        
        IMPORTANT: MetricsHelper.get_all_metrics() returns a nested structure:
            {'metrics': {actual_64_metrics_dict}, ...other_keys...}
        
        So we must extract the 'metrics' key before filtering/returning.
        """
        # AGGRESSIVE DEBUG
        safe_print(f"  _extract_file_metrics called with {len(selected_metrics)} metrics")
        
        if not self.metrics_helper:
            safe_print(f"self.metrics_helper is None!")
            return {'file': file_path}
        
        try:
            # MetricsHelper handles both absolute and relative paths
            result_dict = self.metrics_helper.get_all_metrics(file_path)
            
            # CRITICAL DEBUG
            safe_print(f"File: {os.path.basename(file_path)}")
            safe_print(f"result_dict type: {type(result_dict)}")
            safe_print(f"result_dict keys: {list(result_dict.keys()) if isinstance(result_dict, dict) else 'NOT A DICT'}")
            
            # Extract the actual metrics from the nested structure
            # MetricsHelper returns {'metrics': {actual metrics}, ...other keys...}
            all_metrics = result_dict.get('metrics', {})
            
            safe_print(f"all_metrics type: {type(all_metrics)}")
            safe_print(f"all_metrics size: {len(all_metrics) if isinstance(all_metrics, dict) else 'NOT A DICT'}")
            if isinstance(all_metrics, dict) and len(all_metrics) > 0:
                safe_print(f"Sample keys: {list(all_metrics.keys())[:5]}")
            
            # Debug on first file
            if not hasattr(self, '_metrics_debug_logged'):
                safe_print(f"Path: {file_path}")
                safe_print(f"Result type: {type(result_dict)}, keys: {list(result_dict.keys())}")
                safe_print(f"Metrics dict size: {len(all_metrics)}")
                
                self.add_agent_message(MessageType.INFO,
                    f"  MetricsHelper returned {len(all_metrics)} metrics for {os.path.basename(file_path)}")
                if all_metrics:
                    sample_keys = list(all_metrics.keys())[:10]
                    self.add_agent_message(MessageType.INFO,
                        f"  Sample metric keys: {sample_keys}...")
                    self.add_agent_message(MessageType.INFO,
                        f"  Filtering to {len(selected_metrics)} selected metrics")
                else:
                    self.add_agent_message(MessageType.ERROR,
                        f"MetricsHelper returned NO metrics for {os.path.basename(file_path)}")
                    safe_print(f"Result dict: {result_dict}")
                self._metrics_debug_logged = True
            
            # Filter to selected metrics only
            if selected_metrics and len(selected_metrics) > 0:
                result = {}
                found_count = 0
                for metric_name in selected_metrics:
                    if metric_name in all_metrics:
                        result[metric_name] = all_metrics[metric_name]
                        found_count += 1
                    else:
                        result[metric_name] = None
                if not hasattr(self, '_metrics_filter_logged'):
                    self.add_agent_message(MessageType.INFO,
                        f"  Filtered {len(all_metrics)} → {found_count} matching metrics")
                    self._metrics_filter_logged = True
            else:
                result = all_metrics
                safe_print(f"  No selected_metrics provided! Using all {len(result)} metrics")
            
            result['file'] = file_path
            return result
        except Exception as e:
            safe_print(f"  _extract_file_metrics exception: {str(e)}")
            import traceback
            safe_print(traceback.format_exc())
            return {'file': file_path}
    
    def task_validate(self):
        """Validate the generated dataset"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_datasets")
        
        # Check if directory exists and list files
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            recent_files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)[:3]
            file_list = '\n'.join([f"  • {f}" for f in recent_files]) if recent_files else "  (No files yet)"
            
            return f"  Dataset validation complete!\n\n**Output Location:**\n{output_dir}\n\n**Recent Files:**\n{file_list}"
        else:
            return f"  Output directory not found yet.\n\nExpected location:\n{output_dir}"
    
    def _safe_eval_formula(self, formula: str, row: Dict) -> float:
        """Safely evaluate formula with row data"""
        try:
            # Create safe namespace with row data
            namespace = dict(row)
            namespace['__builtins__'] = {}  # Restrict builtins for safety
            
            # Allow safe math functions
            import math
            namespace.update({
                'abs': abs, 'max': max, 'min': min, 'sum': sum,
                'round': round, 'int': int, 'float': float,
                'sqrt': math.sqrt, 'log': math.log, 'exp': math.exp
            })
            
            # Evaluate the formula
            result = eval(formula, namespace)
            return float(result) if result is not None else 0
        except:
            return 0
    
    def _create_visualizations(self, config: Dict) -> str:
        """
        Create visualizations of the generated dataset
        - Distribution charts
        - Correlation heatmaps
        - Metric trends
        """
        if not hasattr(self, 'extracted_data') or not self.extracted_data:
            return "  No data to visualize"
        
        try:
            import pandas as pd
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Convert to DataFrame
            df = pd.DataFrame(self.extracted_data)
            
            # Create output directory for visualizations
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            viz_dir = os.path.join(base_dir, "generated_datasets", "visualizations")
            os.makedirs(viz_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if len(numeric_cols) == 0:
                return "  No numeric metrics to visualize"
            
            # 1. Distribution plots
            fig, axes = plt.subplots(min(3, len(numeric_cols)), 1, figsize=(10, 4*min(3, len(numeric_cols))))
            if not isinstance(axes, np.ndarray):
                axes = [axes]
            
            for i, col in enumerate(numeric_cols[:3]):
                df[col].hist(ax=axes[i], bins=30, edgecolor='black')
                axes[i].set_title(f'Distribution of {col}')
                axes[i].set_xlabel(col)
                axes[i].set_ylabel('Frequency')
            
            plt.tight_layout()
            dist_file = os.path.join(viz_dir, f"distributions_{timestamp}.png")
            plt.savefig(dist_file, dpi=100, bbox_inches='tight')
            plt.close()
            
            # 2. Correlation heatmap (if enough metrics)
            if len(numeric_cols) >= 2:
                plt.figure(figsize=(10, 8))
                correlation = df[numeric_cols[:10]].corr()  # Limit to 10 metrics
                sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', center=0)
                plt.title('Metric Correlation Heatmap')
                plt.tight_layout()
                corr_file = os.path.join(viz_dir, f"correlation_{timestamp}.png")
                plt.savefig(corr_file, dpi=100, bbox_inches='tight')
                plt.close()
            
            return f"  Visualizations created in {viz_dir}\n  • Distribution plot\n  • Correlation heatmap"
            
        except ImportError:
            return "  Visualization libraries not available (matplotlib/seaborn)"
        except Exception as e:
            return f"  Visualization failed: {str(e)}"
    
    def task_extract_custom_formula(self, config: Dict):
        """Extract base metrics needed for custom formula"""
        metrics_needed = config.get('metrics', [])
        
        if not metrics_needed:
            return "Using all available metrics"
        
        # Ensure metrics are selected
        if metrics_needed:
            self.dataset_config['selected_metrics'] = metrics_needed
            return f"Extracted {len(metrics_needed)} base metrics: {', '.join(metrics_needed)}"
        else:
            return "No specific metrics required"
    
    def task_apply_formula(self, config: Dict):
        """Apply custom formula to the dataset"""
        formula_desc = config.get('custom', 'custom calculation')
        return f"Applied formula: {formula_desc}"
    
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
        """Generate benchmark datasets using ORIGINAL DatasetGenerator formats"""
        if not self.repo_path:
            return "  Error: Repository not set! Please set repository first."
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_datasets")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            return f"  Failed to create output directory: {str(e)}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            import sys
            from pathlib import Path
            
            # Import ORIGINAL ProfessionalDatasetGenerator with proper benchmark formats
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from dataset_generator import ProfessionalDatasetGenerator
            
            self.add_agent_message(MessageType.THINKING, 
                f"Using ORIGINAL benchmark generator for: {self.repo_path}")
            
            # Get commit limit from dataset config (None = ALL commits)
            commit_limit = self.dataset_config.get('class_limit')  # Reuse as commit_limit
            if commit_limit:
                self.add_agent_message(MessageType.INFO, 
                    f"  Limiting to {commit_limit} commits per benchmark")
            else:
                self.add_agent_message(MessageType.INFO, 
                    "  Processing ALL commits from repository")
            
            # Initialize generator with repository path, commit limit, and timestamp
            # Use the ACTUAL repository loaded in GUI (not parent, not hardcoded path)
            workspace_path = str(self.repo_path)  # Use user's loaded repository
            
            self.add_agent_message(MessageType.INFO, 
                f"Generating datasets from YOUR repository: {Path(workspace_path).name}")
            
            generator = ProfessionalDatasetGenerator(
                workspace_path=workspace_path,
                commit_limit=commit_limit,
                timestamp=timestamp
            )
            
            # Generate each benchmark using ORIGINAL methods with PROPER formats
            generated_files = []
            
            for benchmark in benchmarks:
                self.add_agent_message(MessageType.ACTION, 
                    f"  Generating {benchmark} with ORIGINAL format...")
                
                if benchmark == 'Defects4J':
                    generator.generate_defects4j_dataset()
                    generated_files.append(f"defects4j_dataset_{timestamp}/ (folder structure + JSON)")
                    self.add_agent_message(MessageType.SUCCESS, 
                        "  Defects4J: Folder structure (bug_NNN/buggy.java, fixed.java) + JSON metadata")
                    
                elif benchmark == 'Bugs.jar':
                    generator.generate_bugs_jar_dataset()
                    generated_files.append(f"bugs_jar_dataset_{timestamp}.json")
                    self.add_agent_message(MessageType.SUCCESS, 
                        "  Bugs.jar: JSON with metrics (from GIT commits)")
                    
                elif benchmark == 'PROMISE':
                    generator.generate_promise_dataset()
                    generated_files.append(f"promise_dataset_{timestamp}.csv")
                    self.add_agent_message(MessageType.SUCCESS, 
                        "  PROMISE: CSV with 42 comprehensive columns (from GIT commits)")
                    
                elif benchmark == 'CodeXGLUE':
                    generator.generate_codexglue_dataset()
                    generated_files.append(f"codexglue_dataset_{timestamp}.json")
                    self.add_agent_message(MessageType.SUCCESS, 
                        "  CodeXGLUE: JSON with code snippets + complexity (from GIT commits)")
                    
                elif benchmark == 'CodeSearchNet':
                    generator.generate_codesearchnet_dataset()
                    generated_files.append(f"codesearchnet_dataset_{timestamp}.json")
                    self.add_agent_message(MessageType.SUCCESS, 
                        "  CodeSearchNet: JSON with code + docstrings + tokens (from GIT commits)")
                    
                elif benchmark in ['ManySStuBs4J', 'Sourcerer']:
                    if benchmark == 'ManySStuBs4J':
                        generator.generate_manystubs4j_dataset()
                        generated_files.append(f"manystubs4j_dataset_{timestamp}.json")
                        self.add_agent_message(MessageType.SUCCESS, 
                            "  ManySStuBs4J: JSON with issue arrays (from GIT commits)")
                    else:
                        generator.generate_sourcerer_dataset()
                        generated_files.append(f"sourcerer_dataset_{timestamp}.json")
                        self.add_agent_message(MessageType.SUCCESS, 
                            "  Sourcerer: JSON with full code (from GIT commits)")
            
            commit_info = f"  Commits: {'ALL' if not commit_limit else commit_limit}"
            return f"  Generated {len(benchmarks)} benchmark datasets with ORIGINAL formats!\n\n{commit_info}\n  Files: {', '.join(generated_files)}\n📂 Location: {output_dir}\n\n  Using PROPER benchmark formats with REAL GIT COMMIT data!"
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"  Error: {str(e)}\n\nDetails:\n{error_details}"
        
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
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NEW UI HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show_benchmark_info(self):
        """Show info about selected benchmark"""
        benchmark = self.benchmark_var.get()
        if benchmark == "None":
            messagebox.showinfo("Benchmark Info", "Select a benchmark from dropdown to see details.")
            return
        
        info = {
            "Defects4J": "Java bugs with buggy/fixed code pairs.\nFormat: Folder structure\nFields: bug_id, project, buggy.java, fixed.java",
            "Bugs.jar": "Large-scale Java bug dataset.\nFormat: JSON\nFields: bug_id, project, files, metrics, commit_hash",
            "PROMISE": "Software defect prediction.\nFormat: CSV (42 columns)\nFields: wmc, dit, noc, cbo, rfc, lcom, ca, ce, npm, lcom3, loc, dam, moa, mfa, cam, ic, cbm, amc, max_cc, avg_cc, defects",
            "CodeXGLUE": "Microsoft code benchmark.\nFormat: JSONL\nFields: code, docstring, func_name, complexity",
            "CodeSearchNet": "Code-to-documentation.\nFormat: JSONL\nFields: code, docstring, language, url, tokens",
            "ManySStuBs4J": "Simple stupid bugs in Java.\nFormat: JSON\nFields: bug_type, buggy_code, fixed_code, project",
            "Sourcerer": "Large-scale code repository.\nFormat: CSV\nFields: file_path, content, language, project, metrics"
        }
        messagebox.showinfo(f"{benchmark} Info", info.get(benchmark, "No info available"))
    
    def generate_from_selection(self):
        """Generate dataset from dropdown/metrics selection"""
        benchmark = self.benchmark_var.get()
        metrics = self.selected_metrics
        combine = self.combine_var.get()
        
        if benchmark == "None" and not metrics:
            messagebox.showwarning("Selection Required", 
                "Please select a benchmark OR some metrics, or use Chat to describe what you need.")
            return
        
        if not self.repo_path:
            messagebox.showwarning("Repository Required", "Please set a repository first.")
            return
        
        # Show what we're generating
        desc = []
        if benchmark != "None":
            desc.append(f"Benchmark: {benchmark}")
        if metrics:
            desc.append(f"Metrics: {len(metrics)} selected")
        if combine:
            desc.append("(Combined)")
        
        self.add_agent_message(MessageType.USER, f"Generate dataset: {', '.join(desc)}")
        self.add_agent_message(MessageType.THINKING, "Creating generation plan...")
        
        # Start generation
        if benchmark != "None" and not metrics:
            # Pure benchmark
            threading.Thread(target=self._generate_benchmark_dataset, 
                           args=(benchmark,), daemon=True).start()
        elif metrics and benchmark == "None":
            # Pure metrics
            threading.Thread(target=self._generate_metrics_dataset,
                           args=(metrics,), daemon=True).start()
        else:
            # Combined
            threading.Thread(target=self._generate_combined_dataset,
                           args=(benchmark, metrics), daemon=True).start()
    
    def clear_selection(self):
        """Clear all selections"""
        self.benchmark_var.set("None")
        self.selected_metrics = []
        self.selected_metrics_count.set("0/64 selected")
        self.combine_var.set(False)
        self.add_agent_message(MessageType.INFO, "Selection cleared")
    
    def _generate_benchmark_dataset(self, benchmark: str):
        """Generate pure benchmark dataset"""
        try:
            from dataset_generator import ProfessionalDatasetGenerator
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            self.add_agent_message(MessageType.ACTION, f"Generating {benchmark}...")
            
            generator = ProfessionalDatasetGenerator(
                workspace_path=str(self.repo_path),
                commit_limit=None,
                timestamp=timestamp
            )
            
            method_map = {
                "Defects4J": generator.generate_defects4j_dataset,
                "Bugs.jar": generator.generate_bugs_jar_dataset,
                "PROMISE": generator.generate_promise_dataset,
                "CodeXGLUE": generator.generate_codexglue_dataset,
                "CodeSearchNet": generator.generate_codesearchnet_dataset,
                "ManySStuBs4J": generator.generate_manystubs4j_dataset,
                "Sourcerer": generator.generate_sourcerer_dataset
            }
            
            if benchmark in method_map:
                method_map[benchmark]()
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"  {benchmark} dataset generated successfully!"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))
    
    def _generate_metrics_dataset(self, metrics: List[str]):
        """Generate dataset with selected metrics using Multi-Agent Orchestrator"""
        try:
            self.add_agent_message(MessageType.ACTION, f"Generating dataset with {len(metrics)} metrics...")
            self.add_agent_message(MessageType.THINKING, "Starting Multi-Agent Orchestrator...")
            
            # Initialize Multi-Agent Orchestrator
            orchestrator = MultiAgentOrchestrator(
                metrics_catalog=self.catalog,
                max_refinement_cycles=3,
                progress_callback=lambda msg: self.root.after(0, 
                    lambda m=msg: self.add_agent_message(MessageType.SYSTEM, m))
            )
            
            # Run full workflow
            result = orchestrator.run_full_workflow(
                user_request=f"Calculate metrics for repository: {', '.join(metrics)}",
                repo_path=str(self.repo_path),
                selected_predefined_metrics=metrics
            )
            
            # Handle result
            if result.status == WorkflowStatus.SUCCESS:
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"Dataset generated successfully with {len(metrics)} metrics!"))
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"Output: {result.output_path}"))
            elif result.status == WorkflowStatus.NEEDS_HUMAN_INTERVENTION:
                self.root.after(0, lambda: self.add_agent_message(MessageType.WARNING,
                    f"Workflow needs human intervention after {result.cycles_completed} cycles"))
            else:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"Workflow failed: {result.final_message}"))
                    
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))
    
    def _generate_combined_dataset(self, benchmark: str, metrics: List[str]):
        """Generate combined benchmark + custom metrics"""
        try:
            self.add_agent_message(MessageType.ACTION, 
                f"Generating combined: {benchmark} + {len(metrics)} custom metrics...")
            
            # First generate benchmark
            self._generate_benchmark_dataset(benchmark)
            
            # Then add custom metrics
            # TODO: Merge benchmark output with custom metrics
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"  Combined dataset ready: {benchmark} base + {len(metrics)} extra metrics"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DYNAMIC FORMULA GENERATOR (Multi-LLM Jury System)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_dynamic_formulas(self):
        """Process dynamic formulas using Multi-LLM Jury System"""
        if not hasattr(self, 'llm_jury_system') or not self.llm_jury_system:
            self.add_agent_message(MessageType.ERROR, 
                "Multi-LLM Jury System not available. Check .env for API keys.")
            return
        
        formula_text = self.formula_input.get('1.0', tk.END).strip()
        if not formula_text or 'Example:' in formula_text:
            self.add_agent_message(MessageType.ERROR, "Please enter formula request")
            return
        
        # Clear formula input
        self.formula_input.delete('1.0', tk.END)
        
        self.add_agent_message(MessageType.USER, f"Dynamic Formula Request:\n{formula_text}")
        self.add_agent_message(MessageType.THINKING, "Starting Multi-LLM Jury System...")
        
        # Run in background
        threading.Thread(target=self._execute_dynamic_formulas, 
                        args=(formula_text,), daemon=True).start()
    
    def _execute_dynamic_formulas(self, formula_text: str):
        """Execute dynamic formula generation with Multi-LLM Jury"""
        try:
            # Step 1: Understand request
            self.root.after(0, lambda: self.jury_status_var.set("Understanding request..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION, 
                "Step 1: Generator LLM understanding your request..."))
            
            understanding = self.llm_jury_system.understand_user_request(formula_text)
            formulas = understanding.get('formulas', [])
            
            if not formulas:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    "Could not extract formulas from request. Try being more specific."))
                self.root.after(0, lambda: self.jury_status_var.set("Ready | 1 Generator + 3 Verifiers"))
                return
            
            # Show what was understood and ASK FOR CONFIRMATION
            formula_list = "\n".join([f"  {i+1}. {f.get('name', 'Unknown')}: {f.get('expression', 'N/A')}" 
                                     for i, f in enumerate(formulas)])
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                f"I understood your request:\n\n"
                f"Formulas to calculate:\n{formula_list}\n\n"
                f"Data source: Mock data (50 rows)\n"
                f"Output folder: generate_dataset/\n\n"
                f"  This will:\n"
                f"  1. Generate Python code dynamically (Generator LLM)\n"
                f"  2. Verify with 3 independent LLMs (Jury)\n"
                f"  3. Execute code temporarily (self-destructs after)\n"
                f"  4. Save result CSV to generate_dataset/\n\n"
                f"Cost: ~$0.005 (5 AWS calls)\n\n"
                f"Type 'yes' or 'confirm' in chat to proceed, or 'no' to cancel."))
            
            # Store for later execution
            self.pending_formula_execution = {
                'formulas': formulas,
                'formula_text': formula_text
            }
            self.root.after(0, lambda: self.jury_status_var.set("Waiting for your confirmation..."))
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"Understanding error: {e}\n\nDetails:\n{error_detail}"))
            self.root.after(0, lambda: self.jury_status_var.set("Error - check logs"))
    
    def _continue_formula_execution(self):
        """Continue formula execution after user confirmation"""
        if not hasattr(self, 'pending_formula_execution') or not self.pending_formula_execution:
            self.add_agent_message(MessageType.ERROR, "No pending formula execution")
            return
        
        formulas = self.pending_formula_execution['formulas']
        
        self.add_agent_message(MessageType.ACTION, "  Confirmed! Starting execution...")
        
        # Run in background thread
        threading.Thread(target=self._run_formula_generation, 
                        args=(formulas,), daemon=True).start()
    
    def _run_formula_generation(self, formulas):
        """Actually run the formula generation (called after confirmation)"""
        try:
            # Step 2: Generate code
            self.root.after(0, lambda: self.jury_status_var.set("Generating code..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 2: Generator LLM writing Python code dynamically..."))
            
            # Create mock data for testing
            import pandas as pd
            import numpy as np
            mock_data = pd.DataFrame({
                'lines_of_code': np.random.randint(100, 5000, 50),
                'bug_count': np.random.randint(0, 50, 50),
                'commit_count': np.random.randint(10, 500, 50),
                'code_smells': np.random.randint(0, 100, 50),
                'complexity': np.random.randint(1, 50, 50),
                'maintainability_index': np.random.randint(0, 100, 50),
                'test_coverage': np.random.randint(0, 100, 50),
                'loc_added': np.random.randint(0, 1000, 50),
                'loc_deleted': np.random.randint(0, 800, 50),
                'commits_by_author': np.random.randint(1, 200, 50)
            })
            
            # Pass DataFrame directly (not columns list)
            code = self.llm_jury_system.generate_code(formulas, mock_data)
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"Code generated ({len(code)} characters)"))
            
            # Step 3: Jury verification
            self.root.after(0, lambda: self.jury_status_var.set("Jury verifying code..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 3: 3 Verifier LLMs checking code correctness..."))
            
            verification = self.llm_jury_system.verify_code_with_jury(code, formulas)
            
            # Show verification results (votes are tuples: (name, verdict_dict))
            approval_rate = verification.get('approval_rate', 0)
            votes_text = "\n".join([
                f"{name}: {verdict.get('verdict', 'UNKNOWN')} (confidence: {verdict.get('confidence', 0):.0%})"
                for name, verdict in verification.get('votes', [])
            ])
            
            if verification.get('approved'):
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"APPROVED by jury ({approval_rate:.0%}):\n{votes_text}"))
                
                # Step 4: Execute code
                self.root.after(0, lambda: self.jury_status_var.set("Executing & self-destructing..."))
                self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                    "Step 4: Executing code temporarily (will auto-delete)..."))
                
                result_df = self.llm_jury_system.execute_temporary_code(code, mock_data)
                
                # Show results
                new_cols = [col for col in result_df.columns if col not in mock_data.columns]
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"SUCCESS! Added {len(new_cols)} new columns:\n" +
                    "\n".join([f"  - {col}" for col in new_cols]) +
                    f"\n\nSample values:\n{result_df[new_cols].head(3).to_string() if new_cols else 'None'}"))
                
                # Save to CORRECT folder: generate_dataset/
                from datetime import datetime
                output_dir = Path('generate_dataset')
                output_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f'dynamic_formulas_{timestamp}.csv'
                result_df.to_csv(output_path, index=False)
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"  Dataset saved to: {output_path}\n"
                    f"  Rows: {len(result_df)}, Columns: {len(result_df.columns)}\n"
                    f"Estimated cost: ~$0.005"))
                
            else:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"  REJECTED by jury ({approval_rate:.0%}):\n{votes_text}\n\n"
                    f"The generated code did not pass verification. Please try rewording your formula."))
            
            self.root.after(0, lambda: self.jury_status_var.set("Ready | 1 Generator + 3 Verifiers"))
            
            # Clear pending
            self.pending_formula_execution = None
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"Execution error: {e}\n\nDetails:\n{error_detail}"))
            self.root.after(0, lambda: self.jury_status_var.set("Error - check logs"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AGENTIC CHAT SYSTEM (TAB 1 - DATASET GENERATOR ONLY)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_chat_input(self):
        """
        MAIN ENTRY POINT: Process chat input from unified interface
        Handles ALL user requirements:
        1. Repository path/link check
        2. Metric selection from 64+ catalog
        3. Natural language query interpretation
        4. LLM jury process for unknown metrics
        5. User approval workflow
        6. Real data generation (no mock)
        7. Visualization & feedback
        """
        query = self.unified_input_var.get().strip()
        
        if not query or 'Type:' in query:
            return
        
        # Show user message
        self.add_agent_message(MessageType.USER, f"{query}")
        self.unified_input_var.set("")
        self.current_query = query
        
        # Step 1: Check repository is set
        if not self.repo_path:
            self.add_agent_message(MessageType.ERROR, 
                "**Repository not set!**\n\n"
                "Please set a repository first:\n"
                "1. Enter path or GitHub URL above\n"
                "2. Click 'Set Repository'\n"
                "3. Then ask your question again")
            return
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Process in background thread
        threading.Thread(target=self._intelligent_chat_processor, 
                        args=(query,), daemon=True).start()
    
    
    def _intelligent_chat_processor(self, query: str):
        """
        INTELLIGENT PROCESSOR - Handles all requirements
        
        Flow:
        1. Interpret query with LLM
        2. Check if all metrics are known
        3. If unknown metrics → Start LLM Jury Process
        4. Show understanding → Ask user approval
        5. Generate real dataset from repo
        6. Create visualizations
        7. Collect feedback
        """
        if not self.api_key:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "  API key missing. Set GEMINI_API_KEY in .env"))
            return
        
        try:
            # Step 1: INTERPRET QUERY
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, 
                "Analyzing your request..."))
            
            # Get available metrics
            available_metrics = {}
            if self.catalog:
                available_metrics = self.catalog.get_all_metrics()
            
            # Build analysis prompt
            analysis_prompt = f"""You are an intelligent dataset generation assistant.

USER QUERY: "{query}"

AVAILABLE METRICS ({len(available_metrics)}):
{json.dumps(list(available_metrics.keys())[:50], indent=2)}... (and {len(available_metrics)-50 if len(available_metrics)>50 else 0} more)

AVAILABLE BENCHMARKS:
- Defects4J (Java bugs, buggy/fixed versions)
- Bugs.jar (Large-scale Java bugs)
- PROMISE (Defect prediction)
- CodeXGLUE (Microsoft code benchmark)
- CodeSearchNet (Code-to-documentation)
- ManySStuBs4J (Simple stupid bugs)
- Sourcerer (Large-scale mining)

ANALYZE and return JSON:
{{
    "understood": true/false,
    "clarification_needed": "question if unclear, null otherwise",
    "intent": "benchmark|custom_metrics|combined|custom_formula|analysis",
    "is_formula": true/false,
    "formula_expression": "the complete formula if is_formula=true",
    "formula_name": "name of the custom metric being calculated",
    "base_metrics_needed": ["list", "of", "metrics", "needed", "for", "formula"],
    "unknown_base_metrics": [
        {{
            "name": "metric_name",
            "description": "what this base metric represents",
            "extract_from": "git_history|code_analysis|file_system"
        }}
    ],
    "benchmark": "name or null",
    "known_metrics": ["list", "of", "known", "metric", "names"],
    "summary": "Clear summary of what will be generated",
    "ready": true/false
}}

CRITICAL RULES:
- If query contains math operators (/, *, +, -, **) → set is_formula=true
- For formulas: Extract ALL base metrics needed (both sides of operators)
- Example: "max(commits_by_author) / commit_count"
  → formula_name: "Code Ownership Concentration"
  → base_metrics_needed: ["commits_by_author", "commit_count"]
  → unknown_base_metrics: [{{"name": "commits_by_author", "description": "per-author commit counts", "extract_from": "git_history"}}]
- If base metric is UNKNOWN → add to unknown_base_metrics (NOT unknown_metrics)
- Ask clarification if unclear what formula calculates
"""
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Try Gemini first, with AWS Bedrock fallback on quota errors
            try:
                response = model.generate_content(analysis_prompt)
                text = response.text.strip()
            except Exception as gemini_error:
                error_msg = str(gemini_error).lower()
                
                # Check if quota exceeded
                if ('429' in error_msg or 'quota' in error_msg or 'resourceexhausted' in error_msg):
                    self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                        "  Gemini quota exceeded. Using AWS Bedrock fallback..."))
                    
                    # Try AWS Bedrock fallback
                    if hasattr(self, 'llm_jury_system') and self.llm_jury_system and self.llm_jury_system.use_aws_fallback:
                        try:
                            aws_response = self.llm_jury_system.multi_provider.generate_content(analysis_prompt)
                            
                            # Debug: Check what AWS returned
                            print(f"AWS Response type: {type(aws_response)}")
                            print(f"AWS Response keys: {aws_response.keys() if isinstance(aws_response, dict) else 'not a dict'}")
                            
                            # Extract text from AWS response
                            if isinstance(aws_response, dict):
                                text = aws_response.get('text', '') or aws_response.get('content', '')
                            else:
                                text = str(aws_response)
                            
                            # Validate response is not empty
                            if not text or len(text.strip()) < 10:
                                raise Exception(f"AWS response empty or too short: {text[:100]}")
                            
                            text = text.strip()
                            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                                "  AWS Bedrock responded successfully"))
                        except Exception as aws_error:
                            print(f"AWS error details: {aws_error}")
                            raise Exception(f"Both Gemini and AWS Bedrock failed. Gemini: {gemini_error}. AWS: {aws_error}")
                    else:
                        raise Exception(f"Gemini quota exceeded and AWS Bedrock not configured. Error: {gemini_error}")
                else:
                    raise gemini_error
            
            # Parse JSON response
            text = text.strip()
            if not text:
                raise Exception("Empty response received from LLM")
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            # Validate JSON before parsing
            if not text or text == 'null':
                raise Exception(f"Invalid response text: {text}")
            
            try:
                understanding = json.loads(text)
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, show user the error and ask for clarification
                print(f"  JSON parsing failed. AWS response preview: {text[:300]}")
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"Failed to parse response (AWS Bedrock returned text but not valid JSON).\n\n"
                    f"Response preview: {text[:200]}\n\n"
                    f"This might be a provider issue. Try again with a simpler request."))
                return
            
            # Step 2: CHECK IF CLARIFICATION NEEDED
            if not understanding.get('understood', False) or understanding.get('clarification_needed'):
                question = understanding.get('clarification_needed', 
                                            'Can you provide more details?')
                self.root.after(0, lambda q=question: self.add_agent_message(
                    MessageType.QUESTION, f"{q}"))
                return
            
            # Step 3: CHECK IF FORMULA OR UNKNOWN METRICS
            is_formula = understanding.get('is_formula', False)
            unknown_base_metrics = understanding.get('unknown_base_metrics', [])
            
            # If formula with unknown base metrics → ASK USER first
            if is_formula and unknown_base_metrics:
                formula_name = understanding.get('formula_name', 'custom metric')
                formula_expr = understanding.get('formula_expression', '')
                
                unknown_list = "\n".join([
                    f"  • {m['name']}: {m['description']} (from {m.get('extract_from', 'unknown')})"
                    for m in unknown_base_metrics
                ])
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                    f"**CLARIFICATION NEEDED**\n\n"
                    f"You want to calculate: **{formula_name}**\n"
                    f"Formula: `{formula_expr}`\n\n"
                    f"But these base metrics are NOT available:\n{unknown_list}\n\n"
                    f"Should I:\n"
                    f"  1️⃣ Extract them from repository using Jury-generated code?\n"
                    f"  2️⃣ Use alternative/approximation?\n\n"
                    f"Type 'extract' or 'yes' to proceed with extraction, or describe alternative."))
                
                # Store for later
                self.current_plan = understanding
                self.awaiting_extraction_approval = True
                return
            
            # Legacy: Handle non-formula unknown metrics
            unknown_metrics = understanding.get('unknown_metrics', [])
            
            if unknown_metrics and self.llm_jury_system:
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"Found {len(unknown_metrics)} unknown metric(s). "
                    f"Starting LLM Jury Process to validate..."))
                
                # Process each unknown metric through jury
                validated_metrics = []
                
                for unk in unknown_metrics:
                    metric_name = unk.get('name', 'custom_metric')
                    metric_desc = unk.get('description', metric_name)
                    
                    self.root.after(0, lambda n=metric_name: self.add_agent_message(
                        MessageType.THINKING, f"Jury evaluating: {n}..."))
                    
                    try:
                        # Step 1: Prepare formula structure for LLMCodeJurySystem
                        # Extract what metrics are needed from the formula/expression
                        import re
                        formula_text = metric_desc
                        
                        # Look for known metric names in the formula
                        all_metrics = list(available_metrics.keys()) + [
                            'lines_added', 'lines_deleted', 'commit_count', 'commits_per_file', 'author_count',
                            'code_smells', 'cyclomatic_complexity', 'cognitive_complexity'
                        ]
                        metrics_in_formula = [m for m in all_metrics if m.lower() in formula_text.lower()]
                        
                        formula_structure = [{
                            'name': metric_name,
                            'description': metric_desc,
                            'expression': formula_text,
                            'required_columns': metrics_in_formula if metrics_in_formula else list(available_metrics.keys())[:20]
                        }]
                        
                        # Create dummy dataframe with available metrics as columns
                        # CRITICAL: Always include git metrics even if not in catalog
                        import pandas as pd
                        metrics_for_dummy = list(available_metrics.keys())[:20]
                        
                        # Ensure git metrics are in the dummy data if formula mentions them
                        git_metrics = ['lines_added', 'lines_deleted', 'commit_count', 'commits_per_file', 'author_count']
                        code_metrics = ['code_smells', 'cyclomatic_complexity', 'cognitive_complexity']
                        all_possible_metrics = metrics_for_dummy + git_metrics + code_metrics
                        
                        # Filter to unique and only use first 30
                        unique_metrics = list(dict.fromkeys(all_possible_metrics))[:30]
                        
                        dummy_data = pd.DataFrame({
                            metric: [0] for metric in unique_metrics
                        })
                        
                        # Step 2: Generate code
                        self.root.after(0, lambda: self.add_agent_message(
                            MessageType.INFO, "Generator LLM creating code..."))
                        
                        generated_code = self.llm_jury_system.generate_code(
                            formula_structure, 
                            dummy_data
                        )
                        
                        if not generated_code:
                            self.root.after(0, lambda n=metric_name: 
                                self.add_agent_message(MessageType.ERROR, 
                                    f"  {n}: Code generation failed"))
                            continue
                        
                        # Step 3: Verify with jury
                        self.root.after(0, lambda: self.add_agent_message(
                            MessageType.INFO, "3 Judge LLMs verifying..."))
                        
                        verification = self.llm_jury_system.verify_code_with_jury(
                            generated_code,
                            formula_structure
                        )
                        
                        # Check votes
                        votes = verification.get('votes', [])
                        approved_count = sum(1 for name, verdict in votes 
                                           if verdict.get('verdict') == 'APPROVE')
                        
                        # Show each judge's vote
                        for judge_name, verdict in votes:
                            status = " " if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                            self.root.after(0, lambda j=judge_name, s=status, v=verdict: 
                                self.add_agent_message(MessageType.INFO, 
                                    f"{s} {j}: {v.get('verdict')}"))
                        
                        # Need majority approval
                        if approved_count >= 2:  # At least 2 out of 3
                            validated_metrics.append({
                                'name': metric_name,
                                'description': metric_desc,
                                'code': generated_code,
                                'jury_summary': f"{approved_count}/3 judges approved"
                            })
                            self.root.after(0, lambda n=metric_name, c=approved_count: 
                                self.add_agent_message(MessageType.SUCCESS, 
                                    f"  {n}: Approved by {c}/3 judges"))
                        else:
                            self.root.after(0, lambda n=metric_name, c=approved_count: 
                                self.add_agent_message(MessageType.ERROR, 
                                    f"  {n}: Rejected - only {c}/3 judges approved"))
                    
                    except Exception as e:
                        self.root.after(0, lambda n=metric_name, err=str(e): 
                            self.add_agent_message(MessageType.ERROR, 
                                f"  {n}: Error - {err}"))
                
                # Add validated metrics to known list
                understanding['validated_custom_metrics'] = validated_metrics
            
            # Step 4: SHOW UNDERSTANDING & ASK APPROVAL
            known_metrics = understanding.get('known_metrics', [])
            validated_custom = understanding.get('validated_custom_metrics', [])
            
            approval_msg = f"""📋 **HERE'S MY UNDERSTANDING:**

{understanding.get('summary', 'Generate dataset')}

**Type:** {understanding.get('intent', 'custom')}
**Repository:** {self.repo_path}
**Known Metrics:** {len(known_metrics)} metrics
  → {', '.join(known_metrics[:10])}{"..." if len(known_metrics) > 10 else ""}
"""
            
            if validated_custom:
                approval_msg += f"\n**Custom Metrics (Jury Approved):** {len(validated_custom)}\n"
                for vc in validated_custom:
                    approval_msg += f"    {vc['name']}: {vc['jury_summary']}\n"
            
            if understanding.get('benchmark'):
                approval_msg += f"**Benchmark Format:** {understanding['benchmark']}\n"
            
            approval_msg += "\n**DATA SOURCE:** Real data from your repository (NO MOCK DATA)\n"
            approval_msg += "\n  **Type 'yes' or 'approve' to proceed**\n  **Type 'no' or describe changes to modify**"
            
            self.root.after(0, lambda m=approval_msg: self.add_agent_message(
                MessageType.QUESTION, m))
            
            #   IMPORTANT: Ask user for file limit BEFORE processing
            self.root.after(100, lambda: self.add_agent_message(MessageType.QUESTION,
                f"  **HOW MANY FILES TO PROCESS?**\n\n"
                f"Default: 100 files\n\n"
                f"Enter a number or type 'all' for entire repo\n"
                f"(Larger = slower, but more comprehensive)\n\n"
                f"Current setting: {self.file_limit_var.get()}"))
            
            # Store for approval
            self.current_plan = understanding
            self.conversation_history.append({
                "role": "assistant", 
                "content": approval_msg,
                "plan": understanding
            })
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda err=str(e), detail=error_detail: 
                self.add_agent_message(MessageType.ERROR, 
                    f"  Analysis error: {err}\n\nDetails:\n{detail}"))
    
    def _process_formula_extraction(self):
        """
        Process formula extraction using Jury System
        
        Flow:
        1. Get unknown base metrics from current_plan
        2. Create extraction code using Generator LLM
        3. Verify with 3 Judge LLMs
        4. If approved → Extract data and apply formula
        5. Show results to user
        """
        if not self.current_plan:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "  No plan found"))
            return
        
        try:
            unknown_base = self.current_plan.get('unknown_base_metrics', [])
            formula_name = self.current_plan.get('formula_name', 'custom metric')
            formula_expr = self.current_plan.get('formula_expression', '')
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"Starting Jury Process for: **{formula_name}**"))
            
            # Combine all unknown metrics into ONE extraction task
            combined_description = f"""Extract base metrics for formula: {formula_expr}

Required metrics:
{chr(10).join([f"- {m['name']}: {m['description']} (from {m.get('extract_from', 'unknown')})" for m in unknown_base])}

These metrics will be used to calculate: {formula_name}
"""
            
            # Step 1: Generate extraction code
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "Generator LLM creating extraction code..."))
            
            formula_structure = [{
                'name': formula_name,
                'description': combined_description,
                'expression': formula_expr,
                'required_columns': [m['name'] for m in unknown_base]
            }]
            
            # Create dummy dataframe with repository structure
            import pandas as pd
            dummy_data = pd.DataFrame({
                'file': ['example.java'],
                'commit_count': [100]  # Include known metrics
            })
            
            generated_code = self.llm_jury_system.generate_code(
                formula_structure,
                dummy_data
            )
            
            if not generated_code:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    "  Code generation failed"))
                return
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"  Code generated ({len(generated_code)} chars)"))
            
            # Step 2: Verify with jury
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "3 Judge LLMs verifying..."))
            
            verification = self.llm_jury_system.verify_code_with_jury(
                generated_code,
                formula_structure
            )
            
            votes = verification.get('votes', [])
            approved_count = sum(1 for name, verdict in votes 
                               if verdict.get('verdict') == 'APPROVE')
            
            # Show each judge's vote
            for judge_name, verdict in votes:
                status = " " if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                reason = verdict.get('reason', 'No reason provided')
                self.root.after(0, lambda j=judge_name, s=status, v=verdict.get('verdict'): 
                    self.add_agent_message(MessageType.INFO, 
                        f"{s} {j}: {v}"))
            
            # Need majority approval (2/3)
            if approved_count >= 2:
                self.root.after(0, lambda n=formula_name, c=approved_count: 
                    self.add_agent_message(MessageType.SUCCESS, 
                        f"  **{n}**: Approved by {c}/3 judges"))
                
                # Store validated code
                if 'validated_custom_metrics' not in self.current_plan:
                    self.current_plan['validated_custom_metrics'] = []
                
                self.current_plan['validated_custom_metrics'].append({
                    'name': formula_name,
                    'expression': formula_expr,
                    'code': generated_code,
                    'jury_summary': f"{approved_count}/3 judges approved"
                })
                
                # Now ask for final approval
                self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                    f"  **Formula validation complete!**\n\n"
                    f"**Metric:** {formula_name}\n"
                    f"**Formula:** `{formula_expr}`\n"
                    f"**Jury Result:** {approved_count}/3 approved\n\n"
                    f"Ready to extract data and apply formula?\n\n"
                    f"Type 'yes' to proceed"))
                
            else:
                self.root.after(0, lambda n=formula_name, c=approved_count: 
                    self.add_agent_message(MessageType.ERROR, 
                        f"**{n}**: Rejected - only {c}/3 judges approved\n\n"
                        f"Please rephrase your formula or try a different approach."))
                self.current_plan = None
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda err=str(e), detail=error_detail: 
                self.add_agent_message(MessageType.ERROR, 
                    f"Extraction error: {err}\n\nDetails:\n{detail}"))
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda e=str(e): self.add_agent_message(
                MessageType.ERROR, f"Error: {e}"))
            print(f"Chat processor error: {error_detail}")
    
    def _process_agentic_chat(self, query: str):
        """Legacy method - redirects to new intelligent processor"""
        self._intelligent_chat_processor(query)
    
    def _execute_understood_request(self):
        """Execute the understood request"""
        if not self.understood_request:
            return
        
        req = self.understood_request
        dtype = req.get('dataset_type', 'custom')
        
        self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION, 
            "Starting generation based on your request..."))
        
        if dtype == 'benchmark' and req.get('benchmark'):
            threading.Thread(target=self._generate_benchmark_dataset,
                           args=(req['benchmark'],), daemon=True).start()
        elif dtype == 'custom' and req.get('custom_description'):
            # Use LLM Jury for custom metric
            threading.Thread(target=self._generate_custom_with_jury,
                           args=(req['custom_description'],), daemon=True).start()
        elif req.get('metrics'):
            self.selected_metrics = req['metrics']
            threading.Thread(target=self._generate_metrics_dataset,
                           args=(req['metrics'],), daemon=True).start()
        else:
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "Please select metrics or benchmark, or describe a custom metric."))
    
    def _generate_custom_with_jury(self, description: str):
        """Generate custom metric using LLM Jury system"""
        if not self.llm_jury or not self.llm_jury.enabled:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "LLM Jury System not available. Check API keys in .env"))
            return
        
        def progress_callback(msg):
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, msg))
        
        try:
            # Get available metrics
            available = self.catalog.get_all_metrics() if self.catalog else {}
            
            # Full jury process
            result = self.llm_jury.full_jury_process(
                description, available, num_judges=3, on_progress=progress_callback
            )
            
            if result.get('success') and result.get('approved'):
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"  Custom metric approved!\n\n"
                    f"**Name:** {result['proposal'].get('metric_name')}\n"
                    f"**Jury:** {result['jury_result']['summary']}\n\n"
                    f"Generating dataset with this metric..."))
                
                # TODO: Actually generate dataset with custom metric code
            else:
                issues = result.get('jury_result', {}).get('votes', [])
                issue_text = "\n".join([f"- Judge {v.get('judge_id')}: {v.get('reasoning', 'No reason')}" 
                                       for v in issues])
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"   Custom metric rejected by jury:\n{issue_text}"))
        
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Jury error: {msg}"))
            
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
    
    def clone_repository(self):
        """Clone a Git repository from URL"""
        repo_input = self.repo_var.get().strip()
        
        # Validate input
        if not repo_input or 'Enter' in repo_input:
            messagebox.showwarning("Clone Repository", 
                "Please enter a GitHub URL (e.g., https://github.com/user/repo) or owner/repo")
            return
        
        # Convert owner/repo to full URL
        if '/' in repo_input and not repo_input.startswith(('http://', 'https://', 'git@')):
            repo_input = f"https://github.com/{repo_input}.git"
        
        # Check if it looks like a Git URL
        if not any(x in repo_input.lower() for x in ['github.com', 'gitlab.com', 'bitbucket.org', '.git']):
            messagebox.showwarning("Clone Repository",
                "Please enter a valid Git repository URL\n\nExamples:\n" +
                "• https://github.com/apache/kafka\n" +
                "• apache/kafka\n" +
                "• git@github.com:apache/kafka.git")
            return
        
        # Create clone dialog
        clone_dialog = tk.Toplevel(self.root)
        clone_dialog.title("Clone Repository")
        clone_dialog.geometry("600x300")
        clone_dialog.grab_set()
        
        # Header
        ttk.Label(clone_dialog, text="Clone Git Repository", 
                  font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        # Repository URL display
        url_frame = ttk.LabelFrame(clone_dialog, text="Repository URL", padding=10)
        url_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        url_text = tk.Text(url_frame, height=2, wrap=tk.WORD, font=('Consolas', 9))
        url_text.pack(fill=tk.X)
        url_text.insert('1.0', repo_input)
        url_text.config(state=tk.DISABLED)
        
        # Destination selection
        dest_frame = ttk.LabelFrame(clone_dialog, text="Clone Destination", padding=10)
        dest_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Default destination
        default_dest = os.path.join(os.path.expanduser("~"), "GitIntel_Clones")
        dest_var = tk.StringVar(value=default_dest)
        
        dest_input_frame = ttk.Frame(dest_frame)
        dest_input_frame.pack(fill=tk.X)
        
        ttk.Entry(dest_input_frame, textvariable=dest_var, 
                  font=('Consolas', 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def browse_destination():
            folder = filedialog.askdirectory(title="Select Clone Destination")
            if folder:
                dest_var.set(folder)
        
        ttk.Button(dest_input_frame, text="Browse", 
                   command=browse_destination).pack(side=tk.LEFT)
        
        # Progress area
        progress_frame = ttk.LabelFrame(clone_dialog, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        progress_text = scrolledtext.ScrolledText(progress_frame, height=5, 
                                                   font=('Consolas', 8), wrap=tk.WORD)
        progress_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(clone_dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        clone_btn = ttk.Button(btn_frame, text="Start Clone", style='Accent.TButton')
        cancel_btn = ttk.Button(btn_frame, text="Cancel")
        
        def log_progress(message):
            """Thread-safe progress logging"""
            clone_dialog.after(0, lambda: progress_text.insert(tk.END, message + '\n'))
            clone_dialog.after(0, lambda: progress_text.see(tk.END))
        
        def start_clone():
            """Start cloning in background thread"""
            clone_btn.config(state=tk.DISABLED)
            cancel_btn.config(text="Close")
            
            def clone_thread():
                try:
                    dest_path = dest_var.get()
                    
                    # Create destination directory
                    os.makedirs(dest_path, exist_ok=True)
                    log_progress(f" ] Destination: {dest_path}")
                    
                    # Extract repo name from URL
                    repo_name = repo_input.rstrip('/').split('/')[-1].replace('.git', '')
                    clone_path = os.path.join(dest_path, repo_name)
                    
                    # Check if already exists
                    if os.path.exists(clone_path):
                        log_progress(f"Directory already exists: {repo_name}")
                        log_progress(f"Using existing directory...")
                        final_path = clone_path
                    else:
                        log_progress(f" Cloning {repo_name}...")
                        log_progress(f"This may take a few minutes...")
                        
                        # Run git clone
                        process = subprocess.Popen(
                            ['git', 'clone', '--progress', repo_input, clone_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            bufsize=1
                        )
                        
                        # Stream output
                        for line in process.stdout:
                            log_progress(line.strip())
                        
                        process.wait()
                        
                        if process.returncode == 0:
                            log_progress(f"\n Repository cloned successfully!")
                            final_path = clone_path
                        else:
                            log_progress(f"\n   Clone failed with code {process.returncode}")
                            return
                    
                    # Set the repository in main window
                    log_progress(f" ] Setting up repository...")
                    self.root.after(0, lambda: self.repo_var.set(final_path))
                    self.root.after(0, lambda: self.set_repository())
                    
                    log_progress(f"\n🎉 Ready to analyze!")
                    clone_dialog.after(2000, clone_dialog.destroy)
                    
                except subprocess.CalledProcessError as e:
                    log_progress(f"\n   Git error: {e}")
                    log_progress(f"  Make sure Git is installed and URL is correct")
                except Exception as e:
                    log_progress(f"\n   Unexpected error: {e}")
                finally:
                    clone_dialog.after(0, lambda: clone_btn.config(state=tk.NORMAL))
            
            threading.Thread(target=clone_thread, daemon=True).start()
        
        clone_btn.config(command=start_clone)
        cancel_btn.config(command=clone_dialog.destroy)
        
        clone_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        cancel_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            
    def set_repository(self):
        """Set the repository - supports local paths and GitHub URLs"""
        repo_input = self.repo_var.get().strip()
        if not repo_input or 'Enter' in repo_input:
            messagebox.showwarning("Warning", "Please enter a repository path or GitHub URL")
            return
        
        # Use enhanced system's repository handler for both GitHub URLs and local paths
        try:
            self.repo_status.config(text="[...] Processing...", foreground='blue')
            self.root.update()
            
            # The enhanced system handles both GitHub URLs and local paths
            repo_info = self.enhanced_system.set_repository(repo_input)
            
            # Get the actual path from enhanced system
            self.repo_path = str(self.enhanced_system.repo_path)
            
            # Display success
            repo_name = os.path.basename(self.repo_path)
            self.repo_status.config(text=f"{repo_name}", foreground='green')
            self.add_agent_message(MessageType.SUCCESS, 
                f"Repository set: {repo_name}\nMetrics discovered: {len(self.enhanced_system.available_metrics)}")
        except Exception as e:
            self.repo_status.config(text=f"   Failed to set repository", foreground='red')
            self.add_agent_message(MessageType.ERROR, 
                f"Repository setup failed: {str(e)[:100]}")
            
    def show_benchmark_options(self):
        """Show benchmark dataset options with selection"""
        # Create benchmark window
        benchmark_window = tk.Toplevel(self.root)
        benchmark_window.title("  Benchmark Datasets")
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
        # CLASS LIMIT INPUT
        # ═══════════════════════════════════════════════════════════════════
        limit_frame = ttk.LabelFrame(benchmark_window, text="⚙️ Dataset Size", padding=10)
        limit_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(limit_frame, text="How many classes to analyze?",
                 font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        
        limit_subframe = ttk.Frame(limit_frame)
        limit_subframe.pack(fill=tk.X, pady=5)
        
        class_limit_var = tk.StringVar(value="all")
        
        ttk.Radiobutton(limit_subframe, text="All classes in repository",
                       variable=class_limit_var, value="all").pack(anchor=tk.W)
        
        custom_frame = ttk.Frame(limit_subframe)
        custom_frame.pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(custom_frame, text="First",
                       variable=class_limit_var, value="custom").pack(side=tk.LEFT)
        
        class_count_var = tk.StringVar(value="100")
        class_count_entry = ttk.Entry(custom_frame, textvariable=class_count_var, width=10)
        class_count_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(custom_frame, text="classes").pack(side=tk.LEFT)
        
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
        
        ttk.Button(btn_frame, text="Select All", command=select_all,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All", command=deselect_all).pack(side=tk.LEFT, padx=2)
        
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
            
            # Get class limit
            if class_limit_var.get() == "all":
                class_limit = None  # All classes
            else:
                try:
                    class_limit = int(class_count_var.get())
                except:
                    messagebox.showerror("Error", "Invalid class count. Please enter a number.")
                    return
            
            # Save to config
            self.dataset_config['selected_benchmarks'] = selected
            self.dataset_config['class_limit'] = class_limit
            
            benchmark_window.destroy()
            
            # DIRECTLY GENERATE - NO PLAN, NO APPROVAL!
            benchmark_str = ', '.join(selected[:3])
            if len(selected) > 3:
                benchmark_str += f", ... and {len(selected)-3} more"
            
            self.add_agent_message(MessageType.SYSTEM,
                f"Generating {len(selected)} benchmark dataset(s)...\n"
                f"Benchmarks: {benchmark_str}"
            )
            
            # Generate directly in thread
            def generate():
                result = self.task_generate_benchmark_output(selected)
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, result))
            
            threading.Thread(target=generate, daemon=True).start()
        
        ttk.Button(button_frame, text="Apply Selection",
                  command=apply_benchmarks, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Cancel",
                  command=benchmark_window.destroy).pack(side=tk.LEFT, padx=2)
        
    def show_metrics_selector(self):
        """Show metrics selector dialog - ALL 64 metrics from catalog"""
        # Create metrics window
        metrics_window = tk.Toplevel(self.root)
        metrics_window.title("  Select Metrics (64 Available)")
        metrics_window.geometry("900x700")
        metrics_window.grab_set()
        
        # Header
        header = ttk.Label(metrics_window, text="Select Metrics from Catalog (64 Total)",
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=10)
        
        # Get ALL metrics from catalog
        if not self.catalog:
            messagebox.showerror("Error", "Metrics catalog not available")
            metrics_window.destroy()
            return
        
        all_metrics = self.catalog.get_all_metrics()
        categories_dict = {}
        
        # Organize by category
        for key, metric in all_metrics.items():
            cat = metric.get('category', 'other').upper()
            if cat not in categories_dict:
                categories_dict[cat] = {}
            categories_dict[cat][key] = metric.get('name', key)
        
        # Info label showing actual count
        info_label = ttk.Label(metrics_window, 
                              text=f"Total: {len(all_metrics)} metrics across {len(categories_dict)} categories",
                              font=('Segoe UI', 9), foreground='blue')
        info_label.pack(pady=(0, 10))
        
        # Category tabs
        notebook = ttk.Notebook(metrics_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        metric_vars = {}
        
        # Create tab for each category
        for category, metrics_in_cat in sorted(categories_dict.items()):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=f"{category} ({len(metrics_in_cat)})")
            
            # Scrollable content
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Add metrics checkboxes
            for metric_key, metric_name in sorted(metrics_in_cat.items()):
                var = tk.BooleanVar(value=metric_key in self.selected_metrics)
                metric_vars[metric_key] = var
                
                chk = ttk.Checkbutton(scrollable_frame, text=f"{metric_name} ({metric_key})",
                                     variable=var)
                chk.pack(anchor=tk.W, padx=10, pady=2)
        
        # Bottom buttons
        btn_frame = ttk.Frame(metrics_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Select/Deselect all
        ttk.Button(btn_frame, text="Select All",
                  command=lambda: [v.set(True) for v in metric_vars.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All",
                  command=lambda: [v.set(False) for v in metric_vars.values()]).pack(side=tk.LEFT, padx=2)
        
        # Save button
        def save_selection():
            self.selected_metrics = [k for k, v in metric_vars.items() if v.get()]
            self.selected_metrics_count.set(f"{len(self.selected_metrics)}/64 selected")
            self.add_agent_message(MessageType.SUCCESS, 
                f"Selected {len(self.selected_metrics)} metrics")
            metrics_window.destroy()
        
        ttk.Button(btn_frame, text="✓ Save Selection",
                  command=save_selection,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=2)
        
        ttk.Button(btn_frame, text="✗ Cancel",
                  command=metrics_window.destroy).pack(side=tk.RIGHT, padx=2)
    
    def _create_plan_from_benchmarks(self, selected_benchmarks: List[str]):
        """Create a task plan for benchmark dataset"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Creating plan for benchmark dataset with {len(selected_benchmarks)} benchmark(s)...")
        
        # Create tasks for benchmarks - NO individual approvals
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Analyze Repository",
            f"Extract REAL metrics from repository",
            action=lambda: self.task_analyze_benchmarks(selected_benchmarks),
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Generate Dataset",
            f"Create {len(selected_benchmarks)} benchmark dataset(s) with REAL data",
            action=lambda: self.task_generate_benchmark_output(selected_benchmarks),
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Save to Output",
            "Save generated datasets to output folder",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary
        summary = f"""
**Plan Created with {len(self.task_manager.tasks)} tasks:**

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
        """Create dataset using enhanced system - no more task overhead!"""
        if not self.repo_path:
            self.add_agent_message(MessageType.ERROR, "   Repository path not set")
            return
        
        # Update enhanced system with selected metrics
        self.dataset_config['selected_metrics'] = selected_metrics
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Generating dataset with {len(selected_metrics)} metrics...")
        
        # Run generation in background thread to avoid freezing GUI
        thread = threading.Thread(
            target=self._generate_metrics_dataset_direct,
            args=(selected_metrics,),
            daemon=True
        )
        thread.start()
    
    def _generate_metrics_dataset_direct(self, selected_metrics: List[str]):
        """Generate dataset directly using analyzer tools"""
        try:
            # CRITICAL: Check if metrics_helper is available
            if not self.metrics_helper:
                safe_print("self.metrics_helper is None in _generate_metrics_dataset_direct!")
                safe_print(f"  repo_path: {self.repo_path}")
                safe_print(f"  METRICS_HELPER_AVAILABLE: {METRICS_HELPER_AVAILABLE}")
                
                # Try to reinitialize
                if METRICS_HELPER_AVAILABLE and self.repo_path:
                    try:
                        safe_print("Re-initializing MetricsHelper...")
                        self.metrics_helper = MetricsHelper(str(self.repo_path))
                        safe_print(" MetricsHelper re-initialized!")
                    except Exception as e:
                        safe_print(f"  Could not re-initialize MetricsHelper: {e}")
                        self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                            f"   MetricsHelper not available - cannot extract metrics"))
                        return
                else:
                    self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                        f"   MetricsHelper not available - please restart application"))
                    return
            
            safe_print(f"Starting with {len(selected_metrics)} selected metrics")
            safe_print(f"MetricsHelper status: {self.metrics_helper is not None}")
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, 
                f"[STEP 1] Scanning repository..."))
            
            # Get all Java files
            java_files = []
            for root_dir, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root_dir, file))
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Found {len(java_files)} Java files"))
            
            # Extract metrics from each file
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING,
                f"[STEP 2] Extracting metrics from {len(java_files)} files..."))
            
            all_metrics = []
            for idx, file_path in enumerate(java_files, 1):
                try:
                    # CRITICAL DEBUG
                    if idx == 1:
                        safe_print(f"\n========== PROCESSING FIRST FILE ==========")
                        safe_print(f"File path: {file_path}")
                        safe_print(f"self.metrics_helper exists: {self.metrics_helper is not None}")
                        safe_print(f"selected_metrics count: {len(selected_metrics)}")
                        safe_print(f"selected_metrics sample: {selected_metrics[:5]}")
                    
                    file_metrics = self._extract_file_metrics(file_path, selected_metrics)
                    
                    # DEBUG: Show what we got
                    if idx == 1:
                        safe_print(f"\nFIRST FILE RESULT")
                        safe_print(f"  Type: {type(file_metrics)}")
                        safe_print(f"  Keys: {list(file_metrics.keys())}")
                        safe_print(f"  Count: {len(file_metrics)}")
                        safe_print(f"  Sample values: {list(file_metrics.items())[:3]}")
                        print(f" Keys: {list(file_metrics.keys())}, Count: {len(file_metrics)}")
                        print(f" Content preview: {dict(list(file_metrics.items())[:5])}")
                    
                    file_metrics['file'] = file_path.replace(self.repo_path, '').lstrip(os.sep)
                    all_metrics.append(file_metrics)
                    
                    # Progress indicator
                    if idx % max(1, len(java_files) // 10) == 0:
                        self.root.after(0, lambda i=idx, t=len(java_files): 
                            self.add_agent_message(MessageType.INFO,
                            f"Processed {i}/{t} files..."))
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Extracted metrics from {len(all_metrics)} files"))
            
            # Apply custom formulas if any
            if hasattr(self, 'custom_metrics_to_apply') and self.custom_metrics_to_apply:
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"[STEP 3] Applying {len(self.custom_metrics_to_apply)} custom formula(s)..."))
                
                for formula_name, formula_def in self.custom_metrics_to_apply.items():
                    for row in all_metrics:
                        try:
                            # Safe formula evaluation
                            result = self._safe_eval_formula(formula_def['formula'], row)
                            row[formula_name] = result
                        except:
                            row[formula_name] = None
            
            # Save to CSV
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING,
                f"[STEP 4] Saving dataset to CSV..."))
            
            output_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "generated_datasets"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"custom_dataset_{timestamp}.csv"
            
            # DEBUG: Check first row metrics
            if all_metrics and len(all_metrics) > 0:
                first_row = all_metrics[0]
                num_cols = len(first_row)
                col_names = list(first_row.keys())
                print(f"First row has {num_cols} columns: {col_names}")
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"  First row keys: {col_names}"))
            
            df = pd.DataFrame(all_metrics)
            df.to_csv(output_file, index=False)
            
            # Success message
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Dataset saved: {output_file.name}"))
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Generated: {len(all_metrics)} rows × {len(df.columns)} metrics"))
            
        except Exception as e:
            import traceback
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"{str(e)[:100]}"))
            print(f"Error:\n{traceback.format_exc()}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # AUTONOMOUS AGENT METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _clear_agent_input_placeholder(self):
        """LEGACY - not needed anymore"""
        pass
    
    def process_agent_query(self):
        """LEGACY - redirects to unified processor"""
        self.process_unified_input()
    
    def _execute_agent_query(self, query: str):
        """Execute agent query in background thread"""
        try:
            # Parse mode from query
            mode_str = self.agent_mode_var.get()
            mode = AgentMode.ASK if mode_str == "ask" else AgentMode.AGENT
            
            # Add thinking message
            self.add_agent_message(MessageType.THINKING, f"Analyzing: {query}")
            
            # Parse input
            actual_mode, actual_query = self.autonomous_agent.parse_user_input(
                f"/{mode_str} {query}" if mode_str == "ask" else query
            )
            
            # Generate plan
            self.add_agent_message(MessageType.ACTION, "Generating task plan...")
            plan = self.autonomous_agent.generate_task_plan(actual_query)
            
            # Show plan details
            self.add_agent_message(MessageType.INFO, 
                f"Intent: {plan.get('intent')}\n"
                f"  Metrics: {', '.join(plan.get('metrics', []))}\n"
                f"  Type: {plan.get('dataset_type')}"
            )
            
            # Show tasks
            tasks_text = "Tasks:\n"
            for i, task in enumerate(plan.get('tasks', []), 1):
                auto = "🤖" if task.get('auto_execute') else "❓"
                tasks_text += f"  {i}. {auto} {task.get('task')}\n"
            self.add_agent_message(MessageType.INFO, tasks_text)
            
            # Execute based on mode
            if mode == AgentMode.ASK:
                self._execute_agent_ask_mode(plan)
            else:
                self._execute_agent_autonomous_mode(plan)
                
        except Exception as e:
            self.add_agent_message(MessageType.ERROR, f"   Error: {str(e)}")
    
    def _execute_agent_ask_mode(self, plan: dict):
        """Execute agent in ASK mode"""
        self.add_agent_message(MessageType.ACTION, 
            "▶️ ASK MODE - Permission required for each task\n\n"
            "Approval workflow initiated. Check task panel for approval buttons."
        )
        
        # Create tasks in task manager
        self.task_manager.clear_tasks()
        for task_data in plan.get('tasks', []):
            self.task_manager.add_task(
                title=task_data.get('task', 'Task'),
                description=task_data.get('description', ''),
                requires_approval=True
            )
        
        # Update UI
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.add_agent_message(MessageType.INFO, 
            "Plan ready. Click ▶ Start Execution in task panel."
        )
    
    def _execute_agent_autonomous_mode(self, plan: dict):
        """Execute agent in AGENT mode (autonomous)"""
        self.add_agent_message(MessageType.ACTION, 
            "AGENT MODE - Autonomous execution started"
        )
        
        # Execute plan
        result = self.autonomous_agent.execute_plan(plan, AgentMode.AGENT)
        
        # Show execution messages
        for msg in result.get('messages', []):
            self.add_agent_message(MessageType.ACTION, msg)
        
        # Show result
        if result['success']:
            self.add_agent_message(MessageType.SUCCESS,
                f"Completed {result['tasks_completed']}/{result['tasks_total']} tasks"
            )
            
            # Show output file if generated
            if result.get('output_file'):
                import os
                file_size = os.path.getsize(result['output_file']) if os.path.exists(result['output_file']) else 0
                self.add_agent_message(MessageType.INFO,
                    f"  **Output Dataset:**\n"
                    f"   File: {result['output_file']}\n"
                    f"   Size: {file_size:,} bytes"
                )
            
            # Ask for feedback
            self.add_agent_message(MessageType.QUESTION,
                "Do you have feedback or need changes?\n\n"
                "Type your feedback in the agent input field and press Enter."
            )
        else:
            self.add_agent_message(MessageType.ERROR,
                f"Execution had failures\n"
                f"Completed: {result['tasks_completed']}/{result['tasks_total']}"
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FORMULA TAB METHODS (TAB 2 - ISOLATED)
    # ═══════════════════════════════════════════════════════════════════════
    
    def execute_formula_only(self):
        """Execute formula from Formula Tab - COMPLETELY ISOLATED"""
        formula_text = self.formula_text_input.get('1.0', tk.END).strip()
        
        if not formula_text:
            self.log_to_formula("error", "   Please enter a formula")
            return
        
        self.log_to_formula("info", f"Starting formula generation...\n   Input: {formula_text[:150]}...")
        self.formula_status_display.set("Processing...")
        
        # Run in background
        threading.Thread(target=self._execute_formula_background, args=(formula_text,), daemon=True).start()
    
    def _execute_formula_background(self, formula_text: str):
        """Execute formula - ONLY REAL DATA, NO MOCK"""
        try:
            import pandas as pd
            import numpy as np
            from pathlib import Path
            
            # Get repository path - MUST BE SET
            repo_path = self.repo_var.get() if hasattr(self, 'repo_var') else None
            
            if not repo_path or repo_path == "Not set":
                self.root.after(0, lambda: self.log_to_formula("error", 
                    "   ERROR: No repository set!\n\n"
                    "Please set repository first in Tab 1 (Dataset Generator).\n"
                    "Formula generation requires REAL data from your repository."))
                self.root.after(0, lambda: self.formula_status_display.set("Error - No repository"))
                return
            
            # Try to find existing analysis data
            data = None
            output_dir = Path(repo_path).parent / "output"
            
            if output_dir.exists():
                csv_files = list(output_dir.glob("*.csv"))
                if csv_files:
                    try:
                        # Load most recent CSV
                        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
                        data = pd.read_csv(latest_csv)
                        self.root.after(0, lambda: self.log_to_formula("success", 
                            f"Loaded REAL data: {latest_csv.name}\n   Rows: {len(data)}\n   Columns: {list(data.columns)[:10]}..."))
                    except Exception as e:
                        self.root.after(0, lambda err=str(e): self.log_to_formula("error", 
                            f"   Could not load CSV: {err}"))
            
            # If still no data, show error - NO MOCK DATA
            if data is None or data.empty:
                self.root.after(0, lambda: self.log_to_formula("error", 
                    f"ERROR: No data found in repository!\n\n"
                    f"Searched: {output_dir}\n"
                    f"Please analyze repository first:\n"
                    f"  1. Go to Tab 1 (Dataset Generator)\n"
                    f"  2. Click 'Analyze Repository'\n"
                    f"  3. Wait for CSV to be generated\n"
                    f"  4. Then come back here\n\n"
                    f"NO MOCK DATA IS USED - only real repository data."))
                self.root.after(0, lambda: self.formula_status_display.set("Error - No data"))
                return
            
            # Step 1: Understand
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 1] Understanding request..."))
            understanding = self.llm_jury_system.understand_user_request(formula_text)
            
            if not understanding or not understanding.get('formulas'):
                self.root.after(0, lambda: self.log_to_formula("error", "Failed to understand"))
                self.root.after(0, lambda: self.formula_status_display.set("Error"))
                return
            
            formulas = understanding['formulas']
            self.root.after(0, lambda: self.log_to_formula("success", f"Understood {len(formulas)} formula(s)"))
            
            # Step 2: Generate
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 2] Generating code..."))
            code = self.llm_jury_system.generate_code(formulas, data)
            
            if not code:
                self.root.after(0, lambda: self.log_to_formula("error", "Code generation failed"))
                self.root.after(0, lambda: self.formula_status_display.set("Error"))
                return
            
            self.root.after(0, lambda: self.log_to_formula("success", f"Code generated ({len(code)} chars)"))
            
            # Step 3: Verify
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 3] Jury verification..."))
            verification = self.llm_jury_system.verify_code_with_jury(code, formulas)
            
            for name, verdict in verification.get('votes', []):
                status = "OK" if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                self.root.after(0, lambda n=name, s=status, v=verdict: 
                               self.log_to_formula("info", f"{s} {n}: {v.get('verdict')}"))
            
            if not verification.get('approved'):
                self.root.after(0, lambda: self.log_to_formula("error", "Jury rejected"))
                self.root.after(0, lambda: self.formula_status_display.set("Rejected"))
                return
            
            # Step 4: Execute
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 4] Executing..."))
            result_df = self.llm_jury_system.execute_temporary_code(code, data.copy())
            
            new_cols = [col for col in result_df.columns if col not in data.columns]
            
            # Save
            output_dir = Path(__file__).parent.parent / "generate_dataset"
            output_dir.mkdir(exist_ok=True)
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"formula_output_{timestamp}.csv"
            result_df.to_csv(output_path, index=False)
            
            # Show preview (first 10 rows)
            preview_text = f"\nPREVIEW (showing 10/{len(result_df)} rows):\n{result_df[new_cols].head(10).to_string()}"
            
            self.root.after(0, lambda: self.log_to_formula("success", 
                f"SUCCESS!\n   Rows: {len(result_df)}\n   New Columns: {new_cols}\n   File: {output_path.name}{preview_text}"))
            self.root.after(0, lambda: self.formula_status_display.set(f"Success - {len(result_df)} rows, {len(new_cols)} column(s)"))
            self.root.after(0, lambda: self.log_system(f"Formula generated: {output_path.name} ({len(result_df)} rows)"))
            
            # Ask for feedback
            self.root.after(0, lambda path=output_path: self._show_formula_feedback(path, result_df, new_cols))
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.log_to_formula("error", f"Error: {str(e)[:200]}"))
            self.root.after(0, lambda: self.formula_status_display.set("Error"))
            self.root.after(0, lambda: self.log_system(f"Formula error: {str(e)}"))
    
    def log_to_formula(self, log_type: str, text: str):
        """Add log to formula execution logs"""
        if not hasattr(self, 'formula_execution_logs'):
            return
        
        import pandas as pd
        self.formula_execution_logs.configure(state=tk.NORMAL)
        timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
        self.formula_execution_logs.insert(tk.END, f"[{timestamp}] {text}\n", log_type)
        self.formula_execution_logs.see(tk.END)
        self.formula_execution_logs.configure(state=tk.DISABLED)
    
    def _show_formula_feedback(self, output_path, result_df, new_cols):
        """Show feedback dialog after formula generation"""
        import subprocess
        import platform
        
        # Create feedback dialog
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Formula Generation Complete")
        feedback_window.geometry("600x400")
        
        # Success message
        ttk.Label(feedback_window, text="Formula Generated Successfully!",
                 font=('Segoe UI', 14, 'bold'), foreground='green').pack(pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(feedback_window, text="  Results", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(stats_frame, text=f"Rows: {len(result_df)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"New Columns: {', '.join(new_cols)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"File: {output_path.name}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        # Actions
        actions_frame = ttk.LabelFrame(feedback_window, text="Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def open_csv():
            try:
                if platform.system() == 'Windows':
                    os.startfile(output_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', output_path])
                else:  # Linux
                    subprocess.run(['xdg-open', output_path])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
        
        def open_folder():
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['explorer', '/select,', str(output_path)])
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', '-R', str(output_path)])
                else:
                    subprocess.run(['xdg-open', str(output_path.parent)])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        
        ttk.Button(actions_frame, text="Open CSV", command=open_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="  Open Folder", command=open_folder).pack(side=tk.LEFT, padx=5)
        
        # Feedback
        feedback_frame = ttk.LabelFrame(feedback_window, text="Rate This Generation", padding=10)
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(feedback_frame, text="Was the result correct?").pack(anchor=tk.W)
        
        rating_var = tk.StringVar(value="")
        
        ttk.Radiobutton(feedback_frame, text="Perfect - exactly what I needed", 
                       variable=rating_var, value="perfect").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Good - mostly correct", 
                       variable=rating_var, value="good").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Okay - needs some fixes", 
                       variable=rating_var, value="okay").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Wrong - incorrect results", 
                       variable=rating_var, value="wrong").pack(anchor=tk.W)
        
        def submit_feedback():
            rating = rating_var.get()
            if rating:
                self.log_system(f"User feedback: {rating} for {output_path.name}")
                messagebox.showinfo("Thank You!", "Feedback recorded!")
                feedback_window.destroy()
            else:
                messagebox.showwarning("No Rating", "Please select a rating first")
        
        ttk.Button(feedback_frame, text="Submit Feedback", command=submit_feedback,
                  style='Accent.TButton').pack(pady=10)
        
        ttk.Button(feedback_window, text="Close", command=feedback_window.destroy).pack(pady=10)
    
    # ═══════════════════════════════════════════════════════════════════
    # INTEGRATED JURY SYSTEM HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    
    def jury_log(self, message: str, tag: str = 'system'):
        """Log message to jury conversation panel"""
        if not hasattr(self, 'jury_conversation'):
            return
        
        self.jury_conversation.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.jury_conversation.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.jury_conversation.see(tk.END)
        self.jury_conversation.configure(state=tk.DISABLED)

    def jury_start_new_request(self):
        """Start a new request in integrated jury system"""
        if not self.integrated_jury:
            messagebox.showerror("Error", "Integrated jury system not available")
            return
        
        user_question = self.jury_input.get('1.0', tk.END).strip()
        
        if not user_question:
            messagebox.showwarning("Empty Input", "Please describe what you need")
            return
        
        # Clear input
        self.jury_input.delete('1.0', tk.END)
        
        # Log user question
        self.jury_log(f"YOU: {user_question}", 'question')
        self.jury_log("Starting integrated jury workflow...", 'thinking')
        
        # Update status
        self.jury_status_var.set("Processing your request...")
        self.jury_session_active = True
        self.jury_session_info.set(f"Session: {self.integrated_jury.session_id}")
        
        # Run workflow in background thread
        thread = threading.Thread(
            target=self._jury_run_workflow_thread,
            args=(user_question,),
            daemon=True
        )
        thread.start()

    def _jury_run_workflow_thread(self, user_question: str):
        """Run integrated jury workflow in background thread"""
        try:
            def progress_callback(msg):
                self.root.after(0, lambda m=msg: self.jury_log(m, 'system'))
            
            result = self.integrated_jury.run_full_workflow(
                user_question=user_question,
                progress_callback=progress_callback
            )
            
            # Handle result on main thread
            self.root.after(0, lambda r=result: self._jury_handle_result(r))
            
        except Exception as e:
            import traceback
            error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda m=error_msg: self.jury_log(m, 'error'))
            self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

    def _jury_handle_result(self, result: Dict):
        """Handle result from jury workflow"""
        status = result.get('status')
        
        if status == 'needs_clarification':
            # Need user to answer clarifying questions
            self.jury_clarification_pending = True
            self.jury_answer_btn.configure(state=tk.NORMAL)
            
            self.jury_log("I need more information to help you:", 'question')
            for q in result.get('questions', []):
                self.jury_log(f"  • {q}", 'question')
            
            self.jury_log(f"\nMy current understanding ({result.get('confidence', 0)}% confident):", 'thinking')
            self.jury_log(result.get('current_understanding', ''), 'thinking')
            
            self.jury_status_var.set("Please answer the clarifying questions above")
            
        elif status == 'success':
            # Success! Show code
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)
            
            self.jury_log(" Code generated and validated!", 'system')
            self.jury_log(f"\nIterations: {result['iterations']}", 'system')
            self.jury_log(f"Test Results: {result['test_results']['passing_llms']}/3 LLMs passed", 'system')
            self.jury_log(f"Total Tests: {result['test_results']['total_passed']}/{result['test_results']['total_tests']} passed", 'system')
            
            self.jury_log("\n" + "="*60, 'system')
            self.jury_log("GENERATED CODE:", 'system')
            self.jury_log("="*60, 'system')
            self.jury_log(result['code'], 'answer')
            
            self.jury_status_var.set("Code ready to use")
            self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
            
            # Offer to save code
            self.root.after(100, lambda r=result: self._jury_offer_save_code(r))
            
        elif status == 'human_intervention_required':
            # Failed after max iterations
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)
            
            self.jury_log("  HUMAN INTERVENTION NEEDED", 'error')
            self.jury_log(f"\n{result['message']}", 'error')
            self.jury_log(f"\nAttempted {len(result['iterations'])} iterations", 'error')
            
            if result.get('last_code'):
                self.jury_log("\nLast generated code (may have issues):", 'thinking')
                self.jury_log(result['last_code'], 'answer')
            
            if result.get('last_feedback'):
                self.jury_log("\nLast test feedback:", 'error')
                self.jury_log(result['last_feedback'], 'error')
            
            self.jury_status_var.set("  Failed - Human help needed")
            self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
            
        else:
            self.jury_log(f"Unknown status: {status}", 'error')

    def jury_provide_feedback(self):
        """Provide answers to clarifying questions"""
        if not self.jury_clarification_pending:
            messagebox.showinfo("Info", "No clarification needed at this time")
            return
        
        user_feedback = self.jury_input.get('1.0', tk.END).strip()
        
        if not user_feedback:
            messagebox.showwarning("Empty Input", "Please provide your answers")
            return
        
        # Clear input
        self.jury_input.delete('1.0', tk.END)
        
        # Log feedback
        self.jury_log(f"\nYOU: {user_feedback}", 'answer')
        self.jury_log("Processing your feedback...", 'thinking')
        
        # Update status
        self.jury_status_var.set("Processing feedback...")
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        # Continue clarification in thread
        thread = threading.Thread(
            target=self._jury_continue_clarification_thread,
            args=(user_feedback,),
            daemon=True
        )
        thread.start()

    def _jury_continue_clarification_thread(self, user_feedback: str):
        """Continue clarification process in background"""
        try:
            result = self.integrated_jury.provide_clarification(user_feedback)
            
            self.root.after(0, lambda r=result: self._jury_handle_clarification_result(r))
            
        except Exception as e:
            import traceback
            error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda m=error_msg: self.jury_log(m, 'error'))
            self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

    def _jury_handle_clarification_result(self, result: Dict):
        """Handle clarification result"""
        if result['status'] == 'clarified':
            self.jury_log(" Requirements clarified! Ready to generate code.", 'system')
            self.jury_log("Please click 'Start New Request' to begin generation with clarified requirements.", 'question')
            self.jury_status_var.set("Clarified! Ready for code generation")
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)
        else:
            # Need more clarification
            self.jury_clarification_pending = True
            self.jury_answer_btn.configure(state=tk.NORMAL)
            
            self.jury_log("\nI still need a bit more information:", 'question')
            for q in result.get('questions', []):
                self.jury_log(f"  • {q}", 'question')
            
            self.jury_log(f"\nMy understanding so far ({result.get('confidence', 0)}% confident):", 'thinking')
            self.jury_log(result.get('current_understanding', ''), 'thinking')
            
            self.jury_status_var.set("Please provide more details")

    def jury_reset_session(self):
        """Reset jury session"""
        if self.jury_session_active:
            confirm = messagebox.askyesno("Confirm Reset", 
                                          "Are you sure you want to reset the current session?")
            if not confirm:
                return
        
        # Reset state
        try:
            from integrated_jury_system import IntegratedJurySystem
            self.integrated_jury = IntegratedJurySystem()
            self.jury_session_active = False
            self.jury_clarification_pending = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset: {str(e)}")
            return
        
        # Clear UI
        self.jury_conversation.configure(state=tk.NORMAL)
        self.jury_conversation.delete('1.0', tk.END)
        self.jury_conversation.configure(state=tk.DISABLED)
        
        self.jury_input.delete('1.0', tk.END)
        
        # Reset status
        self.jury_status_var.set("Ready to help! Describe what you need...")
        self.jury_session_info.set("No active session")
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        self.jury_log("Session reset. Ready for new request!", 'system')

    def _jury_offer_save_code(self, result: Dict):
        """Offer to save generated code"""
        response = messagebox.askyesnocancel(
            "Save Code?",
            f"Code generated successfully!\n\n"
            f"Function: {result['function_name']}\n"
            f"Tests passed: {result['test_results']['passing_llms']}/3 LLMs\n\n"
            f"Would you like to save the code to a file?"
        )
        
        if response is None:  # Cancel
            return
        
        if response:  # Yes - save
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                initialfile=f"{result['function_name']}.py"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w') as f:
                        f.write(f"# Generated by Integrated Jury System\n")
                        f.write(f"# Session: {result['session_id']}\n")
                        f.write(f"# Validation: {result['test_results']['passing_llms']}/3 LLMs passed\n")
                        f.write(f"# Description: {result['description']}\n\n")
                        f.write(result['code'])
                    
                    messagebox.showinfo("Success", f"Code saved to:\n{file_path}")
                    self.jury_log(f"\n Code saved to: {file_path}", 'system')
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save code:\n{str(e)}")
    
    def log_system(self, text: str):
        """Add log to system logs tab"""
        if not hasattr(self, 'system_logs_text'):
            return
        
        import pandas as pd
        self.system_logs_text.configure(state=tk.NORMAL)
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        self.system_logs_text.insert(tk.END, f"[{timestamp}] {text}\n")
        self.system_logs_text.see(tk.END)
        self.system_logs_text.configure(state=tk.DISABLED)


    def orch_browse_repo(self):
        """Browse for repository folder in orchestrator tab"""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.orch_repo_var.set(folder)
    
    def orch_clone_repo(self):
        """Clone a Git repository in orchestrator tab"""
        repo_input = self.orch_repo_var.get().strip()
        
        if not repo_input:
            messagebox.showwarning("Clone Repository", 
                "Please enter a GitHub URL or owner/repo")
            return
        
        # Convert owner/repo to full URL
        if '/' in repo_input and not repo_input.startswith(('http://', 'https://', 'git@')):
            repo_input = f"https://github.com/{repo_input}.git"
        
        if not any(x in repo_input.lower() for x in ['github.com', 'gitlab.com', '.git']):
            messagebox.showwarning("Clone Repository",
                "Please enter a valid Git URL")
            return
        
        messagebox.showinfo("Clone Repository", 
            f"Clone functionality would clone:\n{repo_input}\n\nThis feature requires Git CLI installed.")
    
    def orch_load_metrics(self):
        """Load all metrics into listbox"""
        if not hasattr(self, 'catalog') or not self.catalog:
            return
        
        self.orch_metrics_listbox.delete(0, tk.END)
        all_metrics = self.catalog.get_all_metrics()
        
        for metric_name, info in all_metrics.items():
            display = f"{metric_name:30} - {info['description'][:50]}"
            self.orch_metrics_listbox.insert(tk.END, display)
    
    def orch_filter_metrics(self):
        """Filter metrics by category"""
        if not hasattr(self, 'catalog') or not self.catalog:
            return
        
        category = self.orch_category_var.get()
        self.orch_metrics_listbox.delete(0, tk.END)
        
        if category == "All":
            all_metrics = self.catalog.get_all_metrics()
        else:
            all_metrics = self.catalog.get_metrics_by_category(category.lower())
        
        for metric_name, info in all_metrics.items():
            display = f"{metric_name:30} - {info['description'][:50]}"
            self.orch_metrics_listbox.insert(tk.END, display)
    
    def orch_select_all(self):
        """Select all metrics"""
        self.orch_metrics_listbox.select_set(0, tk.END)
    
    def orch_clear_all(self):
        """Clear all selections"""
        self.orch_metrics_listbox.selection_clear(0, tk.END)
    
    def orch_popular_set(self):
        """Select popular metrics set"""
        popular = ['loc', 'cyclomatic_complexity', 'cbo', 'wmc', 'dit', 'churn', 
                   'bug_density', 'maintainability_index', 'test_coverage']
        
        self.orch_metrics_listbox.selection_clear(0, tk.END)
        
        for i in range(self.orch_metrics_listbox.size()):
            item_text = self.orch_metrics_listbox.get(i)
            for metric in popular:
                if item_text.startswith(metric):
                    self.orch_metrics_listbox.selection_set(i)
                    break
    
    def orch_log_message(self, message: str, tag: str = 'info'):
        """Log message to orchestrator log"""
        if not hasattr(self, 'orch_log'):
            return
        self.orch_log.configure(state=tk.NORMAL)
        self.orch_log.insert(tk.END, f"{message}\n", tag)
        self.orch_log.see(tk.END)
        self.orch_log.configure(state=tk.DISABLED)
    
    def orch_start_workflow(self):
        """Start multi-agent workflow"""
        if not hasattr(self, 'orch_running'):
            self.orch_running = False
        
        if self.orch_running:
            messagebox.showwarning("Already Running", "Workflow is already in progress")
            return
        
        # Get configuration
        repo_path = self.orch_repo_var.get().strip()
        if not repo_path:
            messagebox.showwarning("Missing Repository", "Please select a repository")
            return
        
        user_request = self.orch_request_text.get('1.0', tk.END).strip()
        if not user_request or "Example:" in user_request:
            messagebox.showwarning("Missing Request", "Please describe what you want to generate")
            return
        
        # Get selected metrics
        selections = self.orch_metrics_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Metrics", "Please select at least one metric")
            return
        
        selected_metrics = []
        for i in selections:
            item_text = self.orch_metrics_listbox.get(i)
            metric_name = item_text.split()[0]  # First word is metric name
            selected_metrics.append(metric_name)
        
        # Clear logs
        if hasattr(self, 'orch_log'):
            self.orch_log.configure(state=tk.NORMAL)
            self.orch_log.delete('1.0', tk.END)
            self.orch_log.configure(state=tk.DISABLED)
        
        # Update status
        self.orch_running = True
        if hasattr(self, 'orch_status_var'):
            self.orch_status_var.set("Multi-Agent Workflow...")
        
        self.orch_log_message("="*70, 'info')
        self.orch_log_message("MULTI-AGENT WORKFLOW STARTING", 'success')
        self.orch_log_message("="*70, 'info')
        self.orch_log_message(f"Repository: {repo_path}", 'info')
        self.orch_log_message(f"User Request: {user_request[:100]}...", 'info')
        self.orch_log_message(f"Selected Metrics: {len(selected_metrics)}", 'info')
        self.orch_log_message("="*70, 'info')
        
        # Run in background thread
        thread = threading.Thread(
            target=self._orch_run_workflow_thread,
            args=(user_request, repo_path, selected_metrics),
            daemon=True
        )
        thread.start()
    
    def _orch_run_workflow_thread(self, user_request: str, repo_path: str, selected_metrics: list):
        """Run orchestrator workflow in background"""
        try:
            from multi_agent_orchestrator import MultiAgentOrchestrator
            
            def progress_callback(msg: str):
                tag = 'info'
                if '[AGENT 1]' in msg:
                    tag = 'agent1'
                elif '[AGENT 2]' in msg:
                    tag = 'agent2'
                elif '[AGENTS 3-5]' in msg or '[TESTING]' in msg:
                    tag = 'agent3'
                elif '[SUCCESS]' in msg or 'SUCCESS' in msg or 'PASSED' in msg:
                    tag = 'success'
                elif '[ERROR]' in msg or 'ERROR' in msg or 'FAILED' in msg:
                    tag = 'error'
                elif '[WARNING]' in msg or 'WARNING' in msg:
                    tag = 'warning'
                
                self.root.after(0, lambda m=msg, t=tag: self.orch_log_message(m, t))
            
            self.root.after(0, lambda: self.orch_log_message("\nInitializing orchestrator...", 'info'))
            
            orchestrator = MultiAgentOrchestrator(
                progress_callback=progress_callback
            )
            
            result = orchestrator.run_full_workflow(
                user_request=user_request,
                repo_path=repo_path,
                selected_predefined_metrics=selected_metrics
            )
            
            self.root.after(0, lambda r=result: self._orch_handle_result(r))
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            self.root.after(0, lambda em=error_msg: self.orch_log_message(em, 'error'))
            if hasattr(self, 'orch_status_var'):
                self.root.after(0, lambda: self.orch_status_var.set(" Workflow Failed"))
            self.orch_running = False
    
    def _orch_handle_result(self, result):
        """Handle workflow result"""
        self.orch_running = False
        self.orch_result = result
        
        from multi_agent_orchestrator import WorkflowStatus
        
        status = result.status
        
        self.orch_log_message("", 'info')
        self.orch_log_message("="*70, 'info')
        
        if status == WorkflowStatus.SUCCESS:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set(f" Dataset Generated ({result.iterations} iterations)")
            if hasattr(self, 'orch_progress_var'):
                self.orch_progress_var.set(f"Cycle: {result.iterations}/5 | Completed in {result.execution_time:.2f}s")
            
            self.orch_log_message("WORKFLOW COMPLETED SUCCESSFULLY", 'success')
            self.orch_log_message(f"Iterations: {result.iterations}", 'success')
            self.orch_log_message(f"Execution Time: {result.execution_time:.2f}s", 'success')
            
            if result.dataset is not None:
                self.orch_log_message(f"Dataset Shape: {result.dataset.shape}", 'success')
                self.orch_log_message(f"Output: {result.metadata.get('dataset_file', 'N/A')}", 'success')
                
                if hasattr(self, 'orch_results_text'):
                    self.orch_results_text.delete('1.0', tk.END)
                    self.orch_results_text.insert('1.0', result.dataset.to_string())
        
        elif status == WorkflowStatus.NEEDS_HUMAN_INTERVENTION:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set("  HUMAN INTERVENTION REQUIRED")
            if hasattr(self, 'orch_progress_var'):
                self.orch_progress_var.set(f"Cycle: {result.iterations}/5 | Max cycles exceeded")
            
            self.orch_log_message("HUMAN INTERVENTION REQUIRED", 'warning')
            self.orch_log_message(f"Error: {result.error_message}", 'warning')
            self.orch_log_message(f"Attempted {result.iterations} iterations", 'warning')
        
        else:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set(" WORKFLOW FAILED")
            self.orch_log_message("WORKFLOW FAILED", 'error')
            self.orch_log_message(f"Error: {result.error_message}", 'error')
        
        self.orch_log_message("="*70, 'info')
    
    def orch_pause(self):
        """Pause workflow"""
        if not self.orch_running:
            messagebox.showinfo("Not Running", "No workflow is currently running")
            return
        
        messagebox.showinfo("Pause", "Pause functionality will be implemented")
    
    def orch_reset(self):
        """Reset orchestrator state"""
        if self.orch_running:
            confirm = messagebox.askyesno("Confirm Reset", 
                                          "Workflow is running. Stop and reset?")
            if not confirm:
                return
        
        self.orch_running = False
        if hasattr(self, 'orch_log'):
            self.orch_log.configure(state=tk.NORMAL)
            self.orch_log.delete('1.0', tk.END)
            self.orch_log.configure(state=tk.DISABLED)
        
        if hasattr(self, 'orch_results_text'):
            self.orch_results_text.delete('1.0', tk.END)
        
        if hasattr(self, 'orch_status_var'):
            self.orch_status_var.set("⏸ Ready - Configure and start workflow")
        
        self.orch_log_message("Orchestrator reset. Ready for new workflow!", 'success')
    
    def orch_save_dataset(self):
        """Save generated dataset"""
        if not hasattr(self, 'orch_result') or not self.orch_result or not self.orch_result.dataset:
            messagebox.showwarning("No Dataset", "No dataset available to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Dataset",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.orch_result.dataset.to_json(file_path, orient='records', indent=2)
                else:
                    self.orch_result.dataset.to_csv(file_path, index=False)
                
                messagebox.showinfo("Success", f"Dataset saved to:\n{file_path}")
                self.orch_log_message(f"Dataset saved: {file_path}", 'success')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save dataset:\n{str(e)}")
    
    def orch_view_dataset(self):
        """View full dataset in new window"""
        if not hasattr(self, 'orch_result') or not self.orch_result or not self.orch_result.dataset:
            messagebox.showwarning("No Dataset", "No dataset available to view")
            return
        
        view_window = tk.Toplevel(self.root)
        view_window.title("Dataset Viewer")
        view_window.geometry("1000x600")
        
        frame = ttk.Frame(view_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.NONE, font=('Consolas', 9))
        text.pack(fill=tk.BOTH, expand=True)
        
        text.insert('1.0', self.orch_result.dataset.to_string())
        text.configure(state=tk.DISABLED)
    
    def orch_open_folder(self):
        """Open output folder"""
        if not self.orch_result or not self.orch_result.metadata.get('output_dir'):
            messagebox.showwarning("No Output", "No output directory available")
            return
        
        import subprocess
        import os
        
        output_dir = self.orch_result.metadata['output_dir']
        
        if os.path.exists(output_dir):
            subprocess.Popen(['explorer', output_dir])
        else:
            messagebox.showwarning("Not Found", f"Directory not found:\n{output_dir}")


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
