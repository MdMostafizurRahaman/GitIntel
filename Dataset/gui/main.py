import tkinter as tk
import os
import sys
import queue
from typing import List, Optional

try:
    from dotenv import load_dotenv

    # When frozen (PyInstaller exe), look for .env next to the executable
    # When running as script, go two levels up: gui/ -> Dataset/
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        env_path = os.path.join(base_dir, '.env')
        # Also try one level up from exe (in case exe is in dist/ subfolder)
        if not os.path.exists(env_path):
            env_path = os.path.join(os.path.dirname(base_dir), '.env')
    else:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(parent_dir, '.env')

    print(f"  Main file location: {__file__}")
    print(f"  Looking for .env at: {env_path}")

    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from {os.path.dirname(env_path)}")
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            print(f"AWS_ACCESS_KEY_ID loaded successfully")
    else:
        # Try current directory
        print(f"  .env not found at {env_path}, trying current directory...")
        load_dotenv()
        print(f"Attempted to load from current directory")
except ImportError:
    pass

# Add parent directory to path
# When frozen by PyInstaller, sys._MEIPASS is the temp extraction dir (auto in sys.path)
# For script mode, add Dataset/ and gui/ directories manually
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
else:
    # Frozen: ensure _MEIPASS is in path (usually auto-set, but be explicit)
    if hasattr(sys, '_MEIPASS'):
        sys.path.insert(0, sys._MEIPASS)
from dataset_helpers import safe_print

# Import MetricsHelper from dataset_generators package
try:
    from dataset_generators import MetricsHelper
    METRICS_HELPER_AVAILABLE = True
except Exception as e:
    print(f"Warning: MetricsHelper not available: {e}")
    MetricsHelper = None
    METRICS_HELPER_AVAILABLE = False

try:
    from metrics_catalog import MetricsCatalog
    from github_autonomous_agent import GitHubAutonomousAgent
    from autonomous_agent import AutonomousDatasetAgent, AgentMode
    from enhanced_agentic_system import EnhancedAgenticSystem, AgentMode as EnhancedMode
    from llm_code_jury_system import LLMCodeJurySystem
    from agentic_code_test_executor import AgenticCodeTestExecutor
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some agent imports failed: {e}")
    AGENT_AVAILABLE = False

# IntegratedJurySystem is imported independently so it works even if other agents fail
try:
    from integrated_jury_system import IntegratedJurySystem
    JURY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: IntegratedJurySystem not available: {e}")
    JURY_AVAILABLE = False

# All LLM operations use IntegratedJurySystem with AWS Bedrock
import time
from functools import wraps
try:
    from .gui_types import TaskStatus, Task, TaskManager, MessageType, AgentMessage
    from .gui_styles import StylesMixin
    from .gui_layout import LayoutMixin
    from .gui_messages import MessagesMixin
    from .gui_repo import RepoMixin
    from .gui_plan import PlanMixin
    from .gui_tasks import TasksMixin
    from .gui_dataset import DatasetMixin
    from .gui_jury_tab import JuryTabMixin
    from .gui_formula_tab import FormulaTabMixin
    from .gui_chat import ChatMixin
    from .gui_orchestrator_tab import OrchestratorMixin
except ImportError:
    from gui_types import TaskStatus, Task, TaskManager, MessageType, AgentMessage
    from gui_styles import StylesMixin
    from gui_layout import LayoutMixin
    from gui_messages import MessagesMixin
    from gui_repo import RepoMixin
    from gui_plan import PlanMixin
    from gui_tasks import TasksMixin
    from gui_dataset import DatasetMixin
    from gui_jury_tab import JuryTabMixin
    from gui_formula_tab import FormulaTabMixin
    from gui_chat import ChatMixin
    from gui_orchestrator_tab import OrchestratorMixin
    
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
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
# NOTE: LLMJurySystem/LLMCodeJurySystem is imported from llm_code_jury_system.py (see imports above)

class AgenticDatasetGUI(
    StylesMixin, LayoutMixin, MessagesMixin,
    RepoMixin, PlanMixin, TasksMixin, DatasetMixin,
    JuryTabMixin, FormulaTabMixin, ChatMixin, OrchestratorMixin
):
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
                # Note: Legacy LLMCodeJurySystem removed — using IntegratedJurySystem instead
                # which uses AWS Bedrock Claude for all operations
                    
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
        
        # API key configuration handled by IntegratedJurySystem using AWS Bedrock
        # No Gemini/Google API keys needed
        
        # Conversation state for agentic chat
        self.conversation_history = []
        self.pending_clarification = False
        self.understood_request = None

        # IntegratedJurySystem chat state (main chat panel)
        self._chat_jury_in_session = False
        self._chat_jury_requirements = None
        
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
            "Powered by IntegratedJurySystem (Jury 1 → Jury 2 → Jury 1/2/3):\n"
            "  1. Jury 1 understands your requirement (asks if unclear)\n"
            "  2. Jury 2 checks the 65-metric catalog + 7 benchmarks;\n"
            "     calls existing functions or synthesises new code\n"
            "  3. All 3 Jury LLMs write unit tests independently;\n"
            "     ≥2/3 must pass — up to 5 retries before human review\n\n"
            "Tell me what you need:\n"
            "  • 'Create a PROMISE dataset from my repo'\n"
            "  • 'Calculate cyclomatic + cognitive complexity for Java files'\n"
            "  • 'Build a custom metric: bugs per changed line'\n\n"
            "Set a repository first, then type your request."
        )
        
    # ── Confirmation gate helpers ──────────────────────────────────────────

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
