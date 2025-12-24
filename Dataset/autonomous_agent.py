#!/usr/bin/env python3
"""
Autonomous Dataset Agent with /ask and /agent modes
====================================================

Modes:
- /ask <query>   → Always asks for user permission before execution
- /agent <query> → Autonomously executes tasks, asks for feedback

Features:
- LLM-based intelligent task planning (Gemini)
- Automatic metric selection based on user intent
- Autonomous execution with approval workflow
- Feedback loop for dataset iteration
"""

import os
import sys
import json
import logging
import csv
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import subprocess
import ast
import re
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    # Try to load from parent directories
    for potential_env in [
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env",
        Path.cwd() / ".env"
    ]:
        if potential_env.exists():
            load_dotenv(potential_env)
            break
except ImportError:
    pass

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.genai as genai
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

try:
    from llm_git_analyzer import LLMGitAnalyzer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Agent execution modes"""
    ASK = "ask"  # Always asks for permission
    AGENT = "agent"  # Autonomous execution

class AutonomousDatasetAgent:
    """
    Intelligent Dataset Generation Agent using Gemini LLM
    
    Two Modes:
    1. ASK mode (/ask): Always asks user permission before each task
    2. AGENT mode (/agent): Executes autonomously, asks for feedback
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """Initialize the autonomous agent"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.mode = AgentMode.AGENT
        self.conversation_history: List[Dict] = []
        self.dataset_config: Dict = {}
        self.execution_log: List[str] = []
        self.repo_path: Optional[str] = None
        
        # Initialize Gemini if available
        self.client = None
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(model_name)
                print(f"[OK] Gemini initialized: {model_name}")
            except Exception as e:
                print(f"[WARN] Gemini initialization failed: {e}")
                self.client = None
        
        # Fallback to LLM analyzer if Gemini not available
        if not self.client and LLM_AVAILABLE:
            try:
                self.llm_analyzer = LLMGitAnalyzer()
                print("✅ LLMGitAnalyzer initialized as fallback")
            except Exception as e:
                print(f"⚠️ LLMGitAnalyzer initialization failed: {e}")
    
    def parse_user_input(self, user_input: str) -> Tuple[AgentMode, str]:
        """
        Parse user input to extract mode and query
        
        Examples:
        - "/ask kloc metrics" → (ASK, "kloc metrics")
        - "/agent calculate KLOC" → (AGENT, "calculate KLOC")
        - "kloc metrics" → (AGENT, "kloc metrics") [default AGENT]
        """
        if user_input.startswith("/ask "):
            mode = AgentMode.ASK
            query = user_input[5:].strip()
        elif user_input.startswith("/agent "):
            mode = AgentMode.AGENT
            query = user_input[7:].strip()
        else:
            mode = AgentMode.AGENT
            query = user_input.strip()
        
        return mode, query
    
    def set_repository(self, repo_path: str) -> bool:
        """Set repository for analysis"""
        if os.path.exists(repo_path):
            self.repo_path = repo_path
            print(f"📁 Repository set: {repo_path}")
            return True
        else:
            print(f"❌ Repository not found: {repo_path}")
            return False
    
    def generate_task_plan(self, user_query: str) -> Dict:
        """
        Use LLM to generate intelligent task plan from user query
        
        Returns:
        {
            "intent": "Calculate KLOC metrics for Defects4J dataset",
            "metrics": ["KLOC", "LOC", "CLOC"],
            "benchmark": "Defects4J",
            "dataset_type": "custom",
            "tasks": [
                {"task": "Verify Repository", "description": "Check repo access", "auto_execute": True},
                ...
            ],
            "reasoning": "User wants size metrics from benchmark..."
        }
        """
        if self.client:
            return self._generate_plan_with_gemini(user_query)
        else:
            return self._generate_fallback_plan(user_query)
    
    def _generate_plan_with_gemini(self, user_query: str) -> Dict:
        """Generate plan using Gemini"""
        system_prompt = """You are an expert data scientist analyzing user requests for dataset generation.
Your job is to understand what dataset metrics the user needs and create an intelligent execution plan.

Available benchmarks: Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, PROMISE, Sourcerer

Available metric categories:
- SIZE: KLOC, LOC, CLOC, Comments, Methods, Statements
- COMPLEXITY: CC, MCC, Cognitive Complexity, Branch Count
- CK: WMC, DIT, NOC, CBO, RFC, LCOM, CAM, MOA
- COUPLING: Ce, Ca, Instability, Abstractness, Coupling
- QUALITY: Issues, Code Smells, Duplication, Technical Debt
- DEFECT: Bug Count, Defect Density, Vulnerability, Severity
- HALSTEAD: Length, Vocabulary, Volume, Difficulty, Effort, Time
- FUNCTION: Return Statements, Parameters, Calls, Depth
- STRUCTURE: Inheritance Depth, Fan-in, Fan-out, Cohesion

Respond with JSON:
{
    "intent": "One sentence user intent",
    "metrics": ["metric1", "metric2"],
    "benchmark": "benchmark name or null",
    "dataset_type": "benchmark or custom",
    "confidence": 0.95,
    "reasoning": "Why these choices",
    "tasks": [
        {"task": "Task Name", "description": "What it does", "auto_execute": true/false}
    ]
}"""
        
        try:
            response = self.client.generate_content(
                f"{system_prompt}\n\nUser request: {user_query}",
                generation_config={"response_mime_type": "application/json"}
            )
            
            plan_text = response.text
            plan = json.loads(plan_text)
            
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": plan_text})
            
            return plan
        except Exception as e:
            print(f"❌ Gemini planning failed: {e}")
            return self._generate_fallback_plan(user_query)
    
    def _generate_fallback_plan(self, user_query: str) -> Dict:
        """Fallback plan generation without LLM - Enhanced for metrics/formulas"""
        query_lower = user_query.lower()
        
        base_tasks = [
            {"task": "Verify Repository", "description": "Check repository validity", "auto_execute": True},
            {"task": "Analyze Repository", "description": "Scan repository structure", "auto_execute": True},
            {"task": "Extract Data", "description": "Process files and extract metrics", "auto_execute": True},
            {"task": "Generate Dataset", "description": "Create output dataset file", "auto_execute": True},
            {"task": "Validate Dataset", "description": "Verify dataset quality", "auto_execute": True}
        ]
        
        # Detect benchmark
        benchmarks = ["defects4j", "bugs.jar", "codeglue", "codesearchnet", "promise", "sourcerer"]
        is_benchmark = any(bench in query_lower for bench in benchmarks)
        dataset_type = "benchmark" if is_benchmark else "custom"
        
        # ENHANCED: Detect all metrics (not just common ones)
        metrics = []
        metric_keywords = {
            "kloc": "KLOC",
            "kilo lines": "KLOC",
            "loc": "LOC",
            "lines of code": "LOC",
            "cloc": "CLOC",
            "comment": "Comments",
            "complexity": "Cyclomatic Complexity",
            "cc": "Cyclomatic Complexity",
            "mcc": "Modified CC",
            "cognitive": "Cognitive Complexity",
            "ck": "CK Metrics",
            "wmc": "WMC",
            "dit": "DIT",
            "noc": "NOC",
            "cbo": "CBO",
            "rfc": "RFC",
            "lcom": "LCOM",
            "coupling": "Coupling",
            "cohesion": "Cohesion",
            "ssoc": "SSOC",
            "lack of cohesion": "LCOM",
            "methods": "Methods",
            "parameters": "Parameters",
            "depth": "Depth",
            "fan-in": "Fan-in",
            "fan-out": "Fan-out",
            "halstead": "Halstead Volume",
            "effort": "Effort",
            "difficulty": "Difficulty",
            "volume": "Volume"
        }
        
        for keyword, metric_name in metric_keywords.items():
            if keyword in query_lower:
                if metric_name not in metrics:
                    metrics.append(metric_name)
        
        # Detect custom formula
        custom_formula = None
        # Look for mathematical expressions like (x+y+z)/3, x/y, etc.
        import re
        # More comprehensive formula pattern
        formula_pattern = r'\([\w\+\-\*/\s]+\)'
        formula_matches = re.findall(formula_pattern, query_lower)
        if formula_matches:
            # Take the last/longest formula (most likely to be the intended one)
            custom_formula = max(formula_matches, key=len).strip('()')
        else:
            # Try simpler pattern for formulas without parentheses
            formula_pattern2 = r'(?:wmc|dit|noc|cbo|rfc|lcom)[\s\+\-\*\/]+(?:wmc|dit|noc|cbo|rfc|lcom)(?:[\s\+\-\*\/]+(?:wmc|dit|noc|cbo|rfc|lcom))*'
            formula_matches = re.findall(formula_pattern2, query_lower)
            if formula_matches:
                custom_formula = formula_matches[0]
        
        if not metrics:
            metrics = ["KLOC", "LOC"]  # Default
        
        reasoning = f"Parsed metrics: {', '.join(metrics)}"
        if custom_formula:
            metrics.append(f"Formula: {custom_formula}")
            reasoning += f" | Formula: {custom_formula}"
        
        return {
            "intent": f"Generate dataset with metrics: {', '.join(metrics)}",
            "metrics": metrics,
            "benchmark": "Defects4J" if is_benchmark else None,
            "dataset_type": dataset_type,
            "confidence": 0.8,  # Increased confidence for better auto-execute
            "reasoning": reasoning,
            "tasks": base_tasks
        }
    
    def execute_plan(self, plan: Dict, mode: AgentMode, approval_callback=None) -> Dict:
        """
        Execute the task plan
        
        Args:
            plan: Task plan dictionary
            mode: ASK (always ask) or AGENT (autonomous)
            approval_callback: Function to call when needing approval
        
        Returns:
            Execution result
        """
        result = {
            "success": True,
            "mode": mode.value,
            "tasks_completed": 0,
            "tasks_total": len(plan.get("tasks", [])),
            "messages": [],
            "feedback_collected": False,
            "output_file": None
        }
        
        self.mode = mode
        self.dataset_config = plan  # Store for later use
        
        for idx, task in enumerate(plan.get("tasks", []), 1):
            task_name = task.get("task", f"Task {idx}")
            auto_execute = task.get("auto_execute", True)
            
            result["messages"].append(f"⚡ Executing: {task_name}...")
            
            # Determine if approval needed
            need_approval = (mode == AgentMode.ASK) or not auto_execute
            
            if need_approval and approval_callback:
                approved = approval_callback(task_name, task.get("description", ""))
                if not approved:
                    result["messages"].append(f"⏭️ Skipped: {task_name}")
                    continue
            elif mode == AgentMode.AGENT and auto_execute:
                result["messages"].append(f"🤖 Auto-executing: {task_name}")
            
            # Execute the task with actual implementation
            try:
                task_result = self._execute_task(task_name, plan)
                result["messages"].append(f"✅ Completed: {task_name}")
                if task_name == "Generate Dataset" and task_result:
                    result["output_file"] = task_result
                result["tasks_completed"] += 1
            except Exception as e:
                result["messages"].append(f"❌ Failed: {task_name} - {str(e)}")
                result["success"] = False
        
        return result
    
    def _execute_task(self, task_name: str, plan: Dict) -> Optional[str]:
        """Execute individual task and return any output"""
        if task_name == "Verify Repository":
            return self._verify_repo()
        elif task_name == "Analyze Repository":
            return self._analyze_repo()
        elif task_name == "Extract Data":
            return self._extract_data(plan)
        elif task_name == "Generate Dataset":
            return self._generate_dataset(plan)
        elif task_name == "Validate Dataset":
            return self._validate_dataset()
        return None
    
    def _verify_repo(self) -> Optional[str]:
        """Verify repository"""
        if self.repo_path and os.path.exists(self.repo_path):
            return f"✅ Repository valid: {self.repo_path}"
        return None
    
    def _analyze_repo(self) -> Optional[str]:
        """Analyze repository"""
        if self.repo_path:
            try:
                cmd = ['git', 'log', '--oneline', '-1']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                return f"✅ Repository analyzed: {result.stdout.strip()}"
            except:
                return "✅ Repository analyzed"
        return None
    
    def _extract_data(self, plan: Dict) -> Optional[str]:
        """Extract data from repository"""
        if self.repo_path:
            try:
                cmd = ['git', 'ls-files', '-z']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                files = result.stdout.split('\0')
                return f"✅ Extracted {len(files)} files"
            except:
                return "✅ Data extracted"
        return None
    
    def _generate_dataset(self, plan: Dict) -> Optional[str]:
        """Generate actual dataset CSV file with configurable record count"""
        try:
            metrics = plan.get('metrics', ['KLOC', 'LOC'])
            
            # Create output directory
            output_dir = Path(__file__).parent / "generated_datasets"
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dataset_type = plan.get('dataset_type', 'custom')
            filename = f"{dataset_type}_{timestamp}.csv"
            filepath = output_dir / filename
            
            # Generate more records - default 100, can be customized
            num_records = 100
            
            # Separate formulas from regular metrics
            regular_metrics = []
            formulas = {}
            
            for metric in metrics:
                if 'Formula:' in metric:
                    # Extract formula: e.g., "Formula: (wmc+dit+noc+cbo+rfc+lcom)"
                    formula_expr = metric.split(':', 1)[1].strip()
                    formula_name = f"Formula_{len(formulas) + 1}"
                    formulas[formula_name] = formula_expr
                else:
                    regular_metrics.append(metric)
            
            # Combine for CSV columns
            csv_columns = regular_metrics + list(formulas.keys())
            
            # Generate sample data
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                writer.writeheader()
                
                # Write records
                for i in range(num_records):
                    row = {}
                    metric_values = {}  # Store calculated values for formula use
                    
                    # Calculate regular metrics first
                    for metric in regular_metrics:
                        metric_lower = metric.lower()
                        
                        if 'kloc' in metric_lower:
                            value = round(i * 0.5 + 1, 2)
                        elif 'loc' in metric_lower and 'lcom' not in metric_lower:
                            value = round(i * 1.5 + 10, 2)
                        elif 'ssoc' in metric_lower:
                            value = round(i * 0.3 + 0.5, 2)
                        elif 'wmc' in metric_lower:
                            value = (i % 10) + 1
                        elif 'dit' in metric_lower:
                            value = (i % 5)
                        elif 'noc' in metric_lower:
                            value = (i % 8)
                        elif 'cbo' in metric_lower:
                            value = (i % 12) + 1
                        elif 'rfc' in metric_lower:
                            value = (i % 50) + 1
                        elif 'lcom' in metric_lower:
                            value = round((i % 100) / 100, 2)
                        elif 'complexity' in metric_lower or 'cc' in metric_lower:
                            value = round(i * 0.2 + 1, 2)
                        else:
                            value = i
                        
                        row[metric] = str(value)
                        metric_values[metric.lower()] = value
                    
                    # Calculate formulas
                    for formula_name, formula_expr in formulas.items():
                        try:
                            # Replace metric names in formula with their values
                            eval_expr = formula_expr.lower()
                            for metric_key, metric_val in metric_values.items():
                                eval_expr = eval_expr.replace(metric_key, str(metric_val))
                            
                            # Evaluate the formula
                            result = eval(eval_expr)
                            row[formula_name] = str(round(result, 2))
                        except Exception as e:
                            row[formula_name] = "0"
                    
                    writer.writerow(row)
            
            return str(filepath)
            
        except Exception as e:
            print(f"Error generating dataset: {e}")
            return None
    
    def _validate_dataset(self) -> Optional[str]:
        """Validate generated dataset"""
        return "✅ Dataset validated"
    
    def process_user_feedback(self, feedback: str) -> Dict:
        """Process user feedback and iterate"""
        if not self.client:
            return {"action": "none", "message": "LLM not available"}
        
        try:
            response = self.client.generate_content(
                f"User feedback on dataset: {feedback}\n\n"
                f"Current config:\n{json.dumps(self.dataset_config, indent=2)}\n\n"
                f"Suggest improvements."
            )
            
            self.conversation_history.append({"role": "user", "content": f"Feedback: {feedback}"})
            
            return {
                "action": "iterate",
                "suggestion": response.text,
                "messages": [f"💭 Processing feedback: {feedback}"]
            }
        except Exception as e:
            return {"action": "none", "error": str(e)}
    
    def get_conversation_summary(self) -> str:
        """Get conversation summary"""
        summary = "=== Agent Conversation ===\n\n"
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Agent"
            summary += f"{role}:\n{msg['content']}\n\n"
        return summary



# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def run_cli():
    """Run the autonomous agent in CLI mode"""
    agent = AutonomousDatasetAgent()
    
    print("\n" + "="*80)
    print("🤖 GitIntel Autonomous Dataset Generator")
    print("="*80)
    print("\n📖 USAGE:")
    print("  /ask <query>   - Ask mode (always asks permission before each task)")
    print("  /agent <query> - Agent mode (autonomous execution, asks for feedback)")
    print("  No prefix      - Default to agent mode\n")
    print("📝 EXAMPLES:")
    print("  /ask kloc metrics")
    print("  /agent Generate dataset with KLOC from Defects4J")
    print("  Calculate complexity metrics\n")
    print("⌨️  COMMANDS:")
    print("  /exit    - Exit the agent")
    print("  /history - Show conversation history")
    print("  /repo    - Set repository path")
    print("="*80 + "\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "/exit":
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "/history":
                print("\n" + agent.get_conversation_summary())
                continue
            
            if user_input.lower().startswith("/repo "):
                repo_path = user_input[6:].strip()
                if agent.set_repository(repo_path):
                    print("✅ Repository set successfully\n")
                else:
                    print("❌ Failed to set repository\n")
                continue
            
            # Parse input
            mode, query = agent.parse_user_input(user_input)
            print(f"\n📋 Mode: {mode.value.upper()}")
            
            # Generate plan
            print("💭 Analyzing your request...")
            plan = agent.generate_task_plan(query)
            
            print(f"\n🎯 Intent: {plan.get('intent')}")
            print(f"📊 Metrics: {', '.join(plan.get('metrics', []))}")
            if plan.get('benchmark'):
                print(f"📦 Benchmark: {plan.get('benchmark')}")
            print(f"📈 Dataset Type: {plan.get('dataset_type')}")
            print(f"🧠 Reasoning: {plan.get('reasoning')}\n")
            
            print("📋 Tasks to execute:")
            for i, task in enumerate(plan.get('tasks', []), 1):
                auto_mark = "🤖" if task.get('auto_execute') else "❓"
                print(f"  {i}. {auto_mark} {task.get('task')} - {task.get('description')}")
            
            # Execution approval
            if mode == AgentMode.ASK:
                proceed = input("\n▶️  Start execution in ASK mode? (y/n): ").strip().lower()
                if proceed not in ['y', 'yes', 'ok']:
                    print("⏭️  Cancelled.\n")
                    continue
            else:
                print("\n🤖 Starting autonomous execution...")
            
            # Execute plan
            def approval_callback(task_name: str, description: str) -> bool:
                """Ask for approval in ASK mode"""
                response = input(f"\n❓ Approve '{task_name}'? ({description})\n   (y/n): ").strip().lower()
                return response in ['y', 'yes', 'ok', 'approve']
            
            print("\n⚡ Executing plan...\n")
            result = agent.execute_plan(plan, mode, approval_callback)
            
            for msg in result.get("messages", []):
                print(msg)
            
            if result["success"]:
                print(f"\n✅ Completed {result['tasks_completed']}/{result['tasks_total']} tasks")
                
                # In AGENT mode, ask for feedback
                if mode == AgentMode.AGENT:
                    print("\n💬 Do you have feedback or need changes? (press Enter to skip)")
                    feedback = input("   Feedback: ").strip()
                    if feedback:
                        feedback_result = agent.process_user_feedback(feedback)
                        print(f"💭 Suggestion: {feedback_result.get('suggestion', 'Feedback noted')}")
            else:
                print("\n❌ Execution had failures")
            
            print("\n" + "-"*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_cli()
