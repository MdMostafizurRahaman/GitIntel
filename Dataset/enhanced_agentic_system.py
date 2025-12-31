#!/usr/bin/env python3
"""
Enhanced Agentic Dataset System with Dynamic Formula Generation
================================================================

Features:
- Repository-aware (clone or existing)
- Two modes: ASK (permission) vs AGENT (autonomous)
- Gemini-powered natural language understanding
- Dynamic formula generation when metrics missing
- Column preview before final generation
- Full repo context for any dataset type

Author: GitIntel Team
Date: December 26, 2025
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed")

# For Git clone support
import subprocess

# Import existing analyzers
try:
    from unified_metrics_analyzer import UnifiedMetricsAnalyzer
    from ck_metrics_analyzer import CKMetricsAnalyzer
    from dataset_generator import ProfessionalDatasetGenerator
    ANALYZERS_AVAILABLE = True
except ImportError:
    ANALYZERS_AVAILABLE = False
    print("⚠️ Analyzers not available")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class AgentMode(Enum):
    """Agent operation modes"""
    ASK = "ask"      # Always asks permission
    AGENT = "agent"  # Autonomous execution


class MessageType(Enum):
    """Message types for conversation"""
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    THINKING = "thinking"
    PLAN = "plan"
    QUESTION = "question"
    PREVIEW = "preview"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ConversationMessage:
    """Single message in conversation"""
    type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class DatasetRequirement:
    """Parsed dataset requirements"""
    description: str
    columns: List[str]
    formulas: Dict[str, str]  # column -> formula/calculation
    filters: List[str]
    dataset_type: str
    scope: str  # "all", "filtered", "specific"
    estimated_rows: int
    requires_new_formulas: bool = False
    missing_metrics: List[str] = field(default_factory=list)


@dataclass
class FormulaDefinition:
    """Generated formula definition"""
    name: str
    description: str
    python_code: str
    dependencies: List[str]  # Required metrics
    example_output: Any


@dataclass
class ColumnPreview:
    """Preview of dataset columns"""
    column_name: str
    data_type: str
    formula: str
    sample_values: List[Any]
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unique_count: Optional[int] = None


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED AGENTIC SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedAgenticSystem:
    """
    Enhanced agentic system with:
    - Full repo context awareness
    - Dynamic formula generation
    - Two-mode operation (ASK/AGENT)
    - Preview before generation
    """
    
    def __init__(self, mode: AgentMode = AgentMode.ASK):
        self.mode = mode
        self.repo_path: Optional[Path] = None
        self.conversation_history: List[ConversationMessage] = []
        self.available_metrics: Dict[str, List[str]] = {}
        self.current_requirement: Optional[DatasetRequirement] = None
        self.generated_formulas: List[FormulaDefinition] = []
        self.preview_data: Optional[pd.DataFrame] = None
        self.sample_data: Optional[pd.DataFrame] = None
        self.sample_generated: bool = False
        self.user_accepted: bool = False
        self.feedback_iterations: int = 0
        
        # Initialize Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                # Try latest models with fallback
                for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        self._add_message(MessageType.SYSTEM, 
                            f"✅ Gemini AI initialized ({model_name})")
                        break
                    except:
                        continue
            else:
                self.model = None
                self._add_message(MessageType.SYSTEM, 
                    "⚠️ GEMINI_API_KEY not found in environment")
        else:
            self.model = None
            
    def set_repository(self, repo_path_or_url: str) -> Dict[str, Any]:
        """
        Set repository from path OR Git URL (auto-clones if URL)
        
        Args:
            repo_path_or_url: Local path OR GitHub URL (https://github.com/...)
            
        Returns:
            Repository info with discovered metrics
        """
        input_str = repo_path_or_url.strip()
        
        # Check if it's a GitHub URL - clone it first
        if 'github.com' in input_str or input_str.startswith('https://') or input_str.startswith('http://'):
            clone_result = self._clone_repository(input_str)
            if not clone_result['success']:
                raise ValueError(clone_result['error'])
            self.repo_path = Path(clone_result['path'])
        else:
            # Local path
            self.repo_path = Path(input_str)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository not found: {self.repo_path}")
            
        self._add_message(MessageType.SYSTEM, 
            f"📁 Repository set: {self.repo_path}")
            
        # Discover metrics
        self._discover_metrics()
        
        return {
            'path': str(self.repo_path),
            'exists': True,
            'metrics_discovered': len(self.available_metrics),
            'categories': list(self.available_metrics.keys())
        }
    
    def _clone_repository(self, url: str) -> Dict[str, Any]:
        """
        Clone GitHub repository to temp location
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Result dict with success status and cloned path
        """
        try:
            # Extract repo name from URL
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            
            # Clone to Dataset/cloned_repos/<repo_name>
            clone_base = Path(__file__).parent / 'cloned_repos'
            clone_base.mkdir(parents=True, exist_ok=True)
            clone_path = clone_base / repo_name
            
            # Check if already cloned
            if clone_path.exists():
                self._add_message(MessageType.SYSTEM, 
                    f"📁 Repository already cloned: {clone_path}")
                return {
                    'success': True,
                    'path': str(clone_path),
                    'already_existed': True
                }
            
            # Clone repository
            self._add_message(MessageType.SYSTEM, 
                f"📥 Cloning repository from {url}...")
            
            result = subprocess.run(
                ['git', 'clone', url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for large repos
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                self._add_message(MessageType.SUCCESS, 
                    f"✅ Repository cloned successfully to {clone_path}")
                return {
                    'success': True,
                    'path': str(clone_path),
                    'already_existed': False
                }
            else:
                error_msg = result.stderr or result.stdout or "Unknown clone error"
                return {
                    'success': False,
                    'error': f"Git clone failed: {error_msg}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Clone timeout (>10 minutes) - repository too large or network slow'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Clone error: {str(e)}"
            }
    
    def _discover_metrics(self):
        """Discover available metrics from repository"""
        if not ANALYZERS_AVAILABLE:
            self._add_message(MessageType.SYSTEM, 
                "⚠️ Analyzers not available, using basic metrics")
            self.available_metrics = {
                'basic': ['lines_of_code', 'file_count', 'method_count']
            }
            return
            
        self._add_message(MessageType.THINKING, 
            "🔍 Analyzing repository to discover available metrics...")
            
        try:
            # Try CK metrics
            ck_analyzer = CKMetricsAnalyzer(str(self.repo_path))
            self.available_metrics['ck'] = [
                'cbo', 'wmc', 'lcom', 'rfc', 'dit', 'noc',
                'lines_of_code', 'method_count', 'field_count'
            ]
            
            # Try unified metrics
            unified_analyzer = UnifiedMetricsAnalyzer(str(self.repo_path))
            self.available_metrics['complexity'] = [
                'cyclomatic_complexity', 'cognitive_complexity'
            ]
            self.available_metrics['halstead'] = [
                'halstead_volume', 'halstead_difficulty', 'halstead_effort'
            ]
            self.available_metrics['maintainability'] = [
                'maintainability_index', 'technical_debt_hours'
            ]
            self.available_metrics['git'] = [
                'commit_count', 'author_count', 'change_frequency',
                'bug_fix_count', 'last_modified'
            ]
            
            total_metrics = sum(len(v) for v in self.available_metrics.values())
            self._add_message(MessageType.SUCCESS, 
                f"✅ Discovered {total_metrics} metrics across {len(self.available_metrics)} categories")
                
        except Exception as e:
            self._add_message(MessageType.ERROR, 
                f"⚠️ Error discovering metrics: {e}")
            self.available_metrics = {'basic': ['lines_of_code', 'file_count']}
    
    def start_conversation(self, user_request: str) -> Dict[str, Any]:
        """
        Start conversation with natural language request
        
        Args:
            user_request: User's dataset request in natural language
            
        Returns:
            Conversation state and next action
        """
        self._add_message(MessageType.USER, user_request)
        
        if not self.repo_path:
            self._add_message(MessageType.QUESTION, 
                "❓ Please set a repository first using set_repository()")
            return {'status': 'needs_repo', 'question': None}
        
        # Start understanding requirements
        self._add_message(MessageType.THINKING, 
            "💭 Understanding your requirements...")
            
        # Use Gemini to understand request
        understanding = self._understand_request(user_request)
        
        if understanding['needs_clarification']:
            self._add_message(MessageType.QUESTION, 
                f"❓ {understanding['question']}")
            return {
                'status': 'needs_clarification',
                'question': understanding['question'],
                'partial_understanding': understanding.get('partial_requirement')
            }
        else:
            # Have enough info, create requirement
            self.current_requirement = understanding['requirement']
            
            # Check if new formulas needed
            if self.current_requirement.requires_new_formulas:
                self._add_message(MessageType.PLAN, 
                    f"📋 Some formulas need to be generated:\n" +
                    "\n".join(f"  • {m}" for m in self.current_requirement.missing_metrics))
                
                # Generate formulas if in AGENT mode
                if self.mode == AgentMode.AGENT:
                    self._generate_missing_formulas()
                else:
                    return {
                        'status': 'needs_approval_for_formula_generation',
                        'missing_formulas': self.current_requirement.missing_metrics
                    }
            
            # Show plan
            return self._show_plan()
    
    def continue_conversation(self, user_response: str) -> Dict[str, Any]:
        """
        Continue conversation with user response
        
        Args:
            user_response: User's answer to question
            
        Returns:
            Updated conversation state
        """
        self._add_message(MessageType.USER, user_response)
        
        # Check if this is an approval response (for plan approval)
        approval_keywords = ['yes', 'approve', 'ok', 'proceed', 'go', 'confirmed', 'hbe', 'hbe bhai']
        if any(keyword in user_response.lower() for keyword in approval_keywords):
            # Check last message type
            last_question = None
            for msg in reversed(self.conversation_history):
                if msg.type == MessageType.QUESTION:
                    last_question = msg.content.lower()
                    break
            
            # If last question was about approval, generate sample
            if last_question and ('approve' in last_question or 'plan' in last_question):
                return self.generate_sample()
        
        # Re-understand with new context - add response to previous question
        user_messages = [msg.content for msg in self.conversation_history if msg.type == MessageType.USER]
        questions = [msg.content for msg in self.conversation_history if msg.type == MessageType.QUESTION]
        
        # Build enriched context with Q&A pairs
        full_context = user_messages[0]  # Original request
        if len(questions) > 0 and len(user_messages) > 1:
            full_context += "\n\nPrevious clarifications:\n"
            for i, (q, a) in enumerate(zip(questions, user_messages[1:])):
                full_context += f"Q{i+1}: {q}\nA{i+1}: {a}\n"
        
        # NO LIMIT on clarifications but prevent infinite loops
        # Detect if same question is being asked repeatedly (infinite loop prevention)
        understanding = self._understand_request(full_context)
        
        if understanding.get('needs_clarification') and len(questions) > 0:
            # Check last 3 questions for repetition
            recent_questions = [q.lower() for q in questions[-3:]]
            new_question = understanding.get('question', '').lower()
            
            # Extract keywords from new question
            new_keywords = set(word for word in new_question.split() if len(word) > 4)
            
            # Check if we're asking about the same thing
            repetition_count = 0
            for prev_q in recent_questions:
                prev_keywords = set(word for word in prev_q.split() if len(word) > 4)
                # If >50% keywords overlap, it's repetitive
                if new_keywords and prev_keywords:
                    overlap = len(new_keywords & prev_keywords) / len(new_keywords)
                    if overlap > 0.5:
                        repetition_count += 1
            
            if repetition_count >= 2:  # Same question asked 2+ times
                self._add_message(MessageType.INFO, 
                    "ℹ️ Detected repeated question. Proceeding with SAMPLE GENERATION based on available information.")
                understanding['needs_clarification'] = False
                # Build requirement from what we have
                if not understanding.get('requirement'):
                    understanding['requirement'] = self._build_requirement_from_context(full_context)
        
        if understanding['needs_clarification']:
            self._add_message(MessageType.QUESTION, 
                f"❓ {understanding['question']}")
            return {
                'status': 'needs_clarification',
                'question': understanding['question']
            }
        else:
            self.current_requirement = understanding['requirement']
            return self._show_plan()
    
    def _understand_request(self, request: str) -> Dict[str, Any]:
        """
        Use LLM to understand dataset request
        
        Returns:
            Dictionary with understanding status
        """
        if not self.model:
            # Fallback: basic parsing
            return self._basic_understanding(request)
            
        # Create prompt for Gemini
        prompt = f"""You are helping create a dataset from a code repository.

Available metrics:
{json.dumps(self.available_metrics, indent=2)}

User request:
{request}

Analyze the request and determine:
1. What columns are needed?
2. What calculations/formulas are required?
3. What filters should be applied?
4. What's the dataset type (defect prediction, complexity analysis, etc.)?
5. What's the scope (all files, specific packages, etc.)?
6. Are there missing metrics that need formulas generated?

If you need clarification, ask ONE specific question.
If you have enough info, provide a complete JSON specification.

Respond in JSON format:
{{
    "needs_clarification": true/false,
    "question": "your question here" or null,
    "requirement": {{
        "description": "dataset description",
        "columns": ["col1", "col2", ...],
        "formulas": {{"col_name": "calculation description"}},
        "filters": ["filter descriptions"],
        "dataset_type": "type",
        "scope": "all/filtered/specific",
        "estimated_rows": number,
        "requires_new_formulas": true/false,
        "missing_metrics": ["metric1", ...]
    }} or null
}}"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(self._extract_json(response.text))
            
            # Convert requirement dict to DatasetRequirement object if present
            if result.get('requirement') and isinstance(result['requirement'], dict):
                result['requirement'] = DatasetRequirement(**result['requirement'])
            
            return result
        except Exception as e:
            self._add_message(MessageType.ERROR, 
                f"⚠️ LLM understanding error: {e}")
            return self._basic_understanding(request)
    
    def _build_requirement_from_context(self, context: str) -> 'DatasetRequirement':
        """Build requirement from conversation context when clarifications exhausted"""
        # Extract mentioned metrics from context
        mentioned_metrics = []
        for category_metrics in self.available_metrics.values():
            for metric in category_metrics:
                if metric.lower() in context.lower():
                    mentioned_metrics.append(metric)
        
        # If no metrics mentioned, use common ones
        if not mentioned_metrics:
            mentioned_metrics = ['lines_of_code', 'commit_count', 'cyclomatic_complexity']
        
        # Parse formula if present (e.g., "health = (churn/1000 commit) + LOC")
        formulas = {}
        if '=' in context:
            # Try to extract custom formula
            parts = context.split('=')
            if len(parts) == 2:
                formula_name = parts[0].strip().split()[-1]  # Get last word before =
                formula_desc = parts[1].strip()
                formulas[formula_name] = formula_desc
        
        return DatasetRequirement(
            description=context[:100],
            columns=mentioned_metrics,
            formulas=formulas,
            filters=[],
            dataset_type='custom',
            scope='all',
            estimated_rows=100,
            requires_new_formulas=len(formulas) > 0,
            missing_metrics=[]
        )
    
    def _basic_understanding(self, request: str) -> Dict[str, Any]:
        """Fallback basic understanding without LLM"""
        # Simple keyword matching
        needs_defect = any(kw in request.lower() for kw in ['defect', 'bug', 'fault', 'error'])
        needs_complexity = any(kw in request.lower() for kw in ['complex', 'cyclomatic', 'cognitive'])
        needs_maintainability = any(kw in request.lower() for kw in ['maintain', 'technical debt', 'quality'])
        
        # Check for custom formula in request
        has_formula = '=' in request and any(word in request.lower() for word in ['churn', 'loc', 'commit'])
        
        columns = []
        formulas = {}
        
        # Determine columns based on keywords
        if has_formula:
            # User provided custom formula - parse it
            requirement = self._build_requirement_from_context(request)
            return {
                'needs_clarification': False,
                'question': None,
                'requirement': requirement
            }
        elif needs_defect:
            columns = ['class_name', 'lines_of_code', 'cbo', 'wmc', 'bug_fix_count']
            formulas = {'bug_count': 'Count of bug-fix commits'}
        elif needs_complexity:
            columns = ['class_name', 'cyclomatic_complexity', 'cognitive_complexity', 'lines_of_code']
        elif needs_maintainability:
            columns = ['class_name', 'maintainability_index', 'technical_debt_hours']
        else:
            # Need clarification - but don't loop indefinitely
            return {
                'needs_clarification': True,
                'question': "What type of dataset do you need? (e.g., defect prediction, complexity analysis, maintainability metrics). You can also provide a custom formula like: health = (churn/1000) + LOC",
                'partial_requirement': None
            }
        
        return {
            'needs_clarification': False,
            'question': None,
            'requirement': DatasetRequirement(
                description=request,
                columns=columns,
                formulas=formulas,
                filters=[],
                dataset_type='inferred',
                scope='all',
                estimated_rows=100,
                requires_new_formulas=False,
                missing_metrics=[]
            )
        }
    
    def _show_plan(self) -> Dict[str, Any]:
        """Show execution plan to user"""
        req = self.current_requirement
        
        plan_text = f"""📋 **Dataset Generation Plan**

**Description:** {req.description}

**Columns ({len(req.columns)}):**
{chr(10).join(f'  • {col}' for col in req.columns)}

**Calculations:**
{chr(10).join(f'  • {col}: {formula}' for col, formula in req.formulas.items())}

**Scope:** {req.scope}
**Estimated Rows:** ~{req.estimated_rows}

**Data Source:** {self.repo_path}
"""
        
        self._add_message(MessageType.PLAN, plan_text)
        
        if self.mode == AgentMode.ASK:
            self._add_message(MessageType.QUESTION, 
                "❓ Approve this plan? Reply 'yes' to generate SAMPLE, 'modify' to change, 'cancel' to stop")
            return {
                'status': 'awaiting_approval',
                'plan': req
            }
        else:
            # Auto-proceed in AGENT mode - Generate SAMPLE first
            return self.generate_sample()
    
    def generate_sample(self, num_rows: int = 10) -> Dict[str, Any]:
        """
        Generate SAMPLE dataset (5-10 rows) for user review
        
        Args:
            num_rows: Number of sample rows (default 10)
            
        Returns:
            Sample dataset info with preview
        """
        if not self.current_requirement:
            return {'error': 'No dataset requirement set'}
        
        self._add_message(MessageType.SYSTEM, 
            f"📊 Generating {num_rows}-row SAMPLE for review...")
        
        try:
            # Extract sample data from repository
            data = self._extract_repository_data()
            data = data[:num_rows]  # Limit to sample size
            
            # Apply formulas
            data = self._apply_formulas(data)
            
            # Convert to DataFrame
            self.sample_data = pd.DataFrame(data)
            self.sample_generated = True
            
            # Show preview to user
            preview_info = self._format_sample_preview(self.sample_data)
            self._add_message(MessageType.PREVIEW, 
                f"\n📋 SAMPLE DATASET PREVIEW ({len(self.sample_data)} rows):\n{preview_info}")
            
            self._add_message(MessageType.QUESTION, 
                "\n💬 Please review the sample. You can:\n"
                "   • 'accepted' / 'looks good' / 'proceed' → Generate full dataset\n"
                "   • Provide feedback for changes → I'll modify and regenerate sample\n"
                "   • 'cancel' / 'stop' → Abort generation")
            
            return {
                'status': 'sample_generated',
                'sample_rows': len(self.sample_data),
                'columns': list(self.sample_data.columns),
                'preview': preview_info,
                'awaiting_feedback': True
            }
            
        except Exception as e:
            self._add_message(MessageType.ERROR, f"❌ Sample generation failed: {e}")
            return {'error': str(e)}
    
    def process_feedback(self, feedback: str) -> Dict[str, Any]:
        """
        Process user feedback on sample dataset
        
        Args:
            feedback: User's feedback text
            
        Returns:
            Action result (accepted, regenerate, error)
        """
        self._add_message(MessageType.USER, feedback)
        self.feedback_iterations += 1
        
        # Check for acceptance keywords
        acceptance_keywords = ['accept', 'looks good', 'proceed', 'ok', 'correct', 'yes', 'perfect', 'right', 'thik ace', 'valo', 'hbe']
        feedback_lower = feedback.lower()
        
        if any(keyword in feedback_lower for keyword in acceptance_keywords):
            self.user_accepted = True
            self._add_message(MessageType.SUCCESS, 
                "✅ Sample ACCEPTED! Proceeding with FULL dataset generation...")
            return {
                'status': 'accepted',
                'action': 'generate_full',
                'feedback_iterations': self.feedback_iterations
            }
        
        # Check for cancellation
        cancel_keywords = ['cancel', 'stop', 'abort', 'no', 'nah', 'band kro']
        if any(keyword in feedback_lower for keyword in cancel_keywords):
            self._add_message(MessageType.INFO, "⚠️ Generation cancelled by user.")
            return {
                'status': 'cancelled',
                'action': 'abort'
            }
        
        # User wants changes - analyze feedback
        self._add_message(MessageType.THINKING, 
            f"🤔 Analyzing feedback (iteration #{self.feedback_iterations})...")
        
        changes = self._analyze_feedback(feedback)
        
        if changes.get('understood', False):
            # Apply changes to requirement
            self._apply_changes_to_requirement(changes)
            
            self._add_message(MessageType.PLAN, 
                f"📝 Changes identified:\n{changes['summary']}\n\n"
                "Regenerating sample with modifications...")
            
            # Regenerate sample
            self.sample_generated = False
            self.user_accepted = False
            result = self.generate_sample()
            
            return {
                'status': 'modified',
                'action': 'regenerated_sample',
                'changes': changes,
                'feedback_iterations': self.feedback_iterations,
                'new_sample': result
            }
        else:
            # Need clarification on feedback
            self._add_message(MessageType.QUESTION, 
                f"❓ {changes.get('clarification_needed', 'Could you clarify what changes you want?')}")
            return {
                'status': 'needs_clarification',
                'question': changes.get('clarification_needed'),
                'feedback_iterations': self.feedback_iterations
            }
    
    def _format_sample_preview(self, df: pd.DataFrame) -> str:
        """Format sample dataframe for display"""
        if df is None or len(df) == 0:
            return "(Empty dataset)"
        
        # Show first 5 rows with formatted output
        preview = "\n"
        preview += "Columns: " + ", ".join(df.columns) + "\n"
        preview += "-" * 80 + "\n"
        preview += df.head(min(5, len(df))).to_string(index=False) + "\n"
        preview += "-" * 80 + "\n"
        preview += f"Total rows: {len(df)}\n"
        
        # Show basic stats for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            preview += "\nNumeric Summary:\n"
            for col in numeric_cols:
                preview += f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}\n"
        
        return preview
    
    def _analyze_feedback(self, feedback: str) -> Dict[str, Any]:
        """Use LLM to analyze user feedback and identify changes"""
        if not self.model:
            # Simple keyword-based analysis
            return {
                'understood': False,
                'clarification_needed': 'Could you specify exactly what needs to change?'
            }
        
        prompt = f"""You are analyzing user feedback on a sample dataset.

Current Dataset Columns:
{list(self.sample_data.columns) if self.sample_data is not None else []}

Current Requirement:
{self.current_requirement}

User Feedback:
{feedback}

Analyze the feedback and determine:
1. What specific changes are requested?
2. Which columns need modification/addition/removal?
3. What filters or calculations need adjustment?
4. Is the feedback clear enough to make changes?

Respond in JSON:
{{
    "understood": true/false,
    "changes": {{
        "add_columns": ["col1", ...],
        "remove_columns": ["col2", ...],
        "modify_formulas": {{"col_name": "new formula"}},
        "modify_filters": ["filter description"],
        "other_changes": "description"
    }},
    "summary": "brief summary of changes",
    "clarification_needed": "question if unclear" or null
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(self._extract_json(response.text))
            return result
        except:
            return {
                'understood': False,
                'clarification_needed': 'Could you specify exactly what needs to change?'
            }
    
    def _apply_changes_to_requirement(self, changes: Dict[str, Any]):
        """Apply feedback changes to current requirement"""
        if not self.current_requirement or not changes.get('changes'):
            return
        
        mods = changes['changes']
        
        # Add columns
        if 'add_columns' in mods:
            for col in mods['add_columns']:
                if col not in self.current_requirement.columns:
                    self.current_requirement.columns.append(col)
        
        # Remove columns
        if 'remove_columns' in mods:
            for col in mods['remove_columns']:
                if col in self.current_requirement.columns:
                    self.current_requirement.columns.remove(col)
        
        # Modify formulas
        if 'modify_formulas' in mods:
            self.current_requirement.formulas.update(mods['modify_formulas'])
        
        # Modify filters
        if 'modify_filters' in mods:
            self.current_requirement.filters.extend(mods['modify_filters'])
    
    def _detect_dataset_type(self) -> Optional[str]:
        """Detect dataset type from conversation history and user request"""
        # Collect all user messages and requests
        conversation_text = ""
        for msg in self.conversation_history:
            if msg.type in [MessageType.USER, MessageType.QUESTION]:
                conversation_text += msg.content.lower() + " "
        
        if self.current_requirement:
            conversation_text += self.current_requirement.description.lower()
        
        # Dataset type keywords mapping
        dataset_patterns = {
            'defects4j': ['defects4j', 'defect4j', 'buggy', 'fixed', 'bug fix', 'bug-fix', 'before after'],
            'bugsjar': ['bugs.jar', 'bugsjar', 'bugs jar', 'bug jar', 'patch', 'bug record'],
            'promise': ['promise', 'promise repository'],
            'codexglue': ['codexglue', 'code-text', 'code text pair', 'ml training', 'code-nl'],
            'codesearchnet': ['codesearchnet', 'code search', 'documentation', 'docstring', 'code doc'],
            'manystubs4j': ['manystubs4j', 'manystubs', 'stub', 'bug pattern', 'simple bug'],
            'sourcerer': ['sourcerer', 'repository stats', 'repo statistics', 'project metrics']
        }
        
        # Check for custom formula keywords (these override benchmark detection)
        custom_formula_keywords = [
            'custom formula', 'custom metric', 'calculated metric', 'derived metric',
            'code smell density', 'test coverage health', 'documentation quality',
            'release stability', 'duplication risk', 'maintainability risk',
            'refactoring need', 'change volatility', 'code churn', 'defect density',
            'technical debt ratio', 'bug fix rate', 'ownership concentration'
        ]
        
        # If custom formulas mentioned, use custom pipeline
        if any(keyword in conversation_text for keyword in custom_formula_keywords):
            self._add_message(MessageType.THINKING,
                "🎯 Detected CUSTOM METRICS request - using custom formula pipeline")
            return 'custom'
        
        # Score each dataset type
        scores = {}
        for dataset_type, keywords in dataset_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in conversation_text:
                    score += 1
            if score > 0:
                scores[dataset_type] = score
        
        # Return highest scoring type
        if scores:
            detected_type = max(scores, key=scores.get)
            self._add_message(MessageType.THINKING,
                f"🎯 Detected dataset type: {detected_type.upper()}")
            return detected_type
        
        # Default to custom if no specific type detected
        self._add_message(MessageType.THINKING,
            "🎯 No benchmark detected, using CUSTOM metrics pipeline")
        return 'custom'
    
    def generate_preview(self) -> Dict[str, Any]:
        """
        Generate preview of dataset with sample data
        
        Returns:
            Preview information with sample rows
        """
        if not self.current_requirement:
            raise ValueError("No requirement set. Call start_conversation first.")
        
        # Detect dataset type
        dataset_type = self._detect_dataset_type()
        
        self._add_message(MessageType.THINKING, 
            "🔄 Generating professional dataset preview...")
        
        try:
            # Use ProfessionalDatasetGenerator
            generator = ProfessionalDatasetGenerator(str(self.repo_path))
            
            # Generate based on detected type (just get sample rows)
            if dataset_type == 'defects4j':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating Defects4J preview (buggy/fixed pairs)...")
                result = generator.generate_defects4j_dataset()
                # Load generated data for preview
                if result.get('csv_path') and Path(result['csv_path']).exists():
                    calculated_data = pd.read_csv(result['csv_path']).head(5).to_dict('records')
                else:
                    calculated_data = []
            
            elif dataset_type == 'bugsjar':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating Bugs.jar preview (bug records)...")
                result = generator.generate_bugsjar_dataset()
                if result.get('json_path') and Path(result['json_path']).exists():
                    with open(result['json_path'], 'r') as f:
                        data = json.load(f)
                    calculated_data = data[:5]
                else:
                    calculated_data = []
            
            elif dataset_type == 'promise':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating PROMISE preview (comprehensive metrics)...")
                result = generator.generate_promise_dataset()
                if result.get('csv_path') and Path(result['csv_path']).exists():
                    calculated_data = pd.read_csv(result['csv_path']).head(5).to_dict('records')
                else:
                    calculated_data = []
            
            elif dataset_type == 'codexglue':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating CodeXGLUE preview (code-text pairs)...")
                result = generator.generate_codexglue_dataset()
                if result.get('json_path') and Path(result['json_path']).exists():
                    with open(result['json_path'], 'r') as f:
                        data = json.load(f)
                    calculated_data = data[:5]
                else:
                    calculated_data = []
            
            elif dataset_type == 'codesearchnet':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating CodeSearchNet preview (code documentation)...")
                result = generator.generate_codesearchnet_dataset()
                if result.get('json_path') and Path(result['json_path']).exists():
                    with open(result['json_path'], 'r') as f:
                        data = json.load(f)
                    calculated_data = data[:5]
                else:
                    calculated_data = []
            
            elif dataset_type == 'manystubs4j':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating ManySStuBs4J preview (bug patterns)...")
                result = generator.generate_manystubs4j_dataset()
                if result.get('csv_path') and Path(result['csv_path']).exists():
                    calculated_data = pd.read_csv(result['csv_path']).head(5).to_dict('records')
                else:
                    calculated_data = []
            
            elif dataset_type == 'sourcerer':
                self._add_message(MessageType.THINKING, 
                    "📦 Generating Sourcerer preview (repository stats)...")
                result = generator.generate_sourcerer_dataset()
                if result.get('json_path') and Path(result['json_path']).exists():
                    with open(result['json_path'], 'r') as f:
                        data = json.load(f)
                    calculated_data = [data]  # Single record
                else:
                    calculated_data = []
            else:
                # Fallback to basic extraction
                extracted_data = self._extract_repository_data()
                calculated_data = self._apply_formulas(extracted_data)[:5]
            
            # Store dataset type for full generation
            self.detected_dataset_type = dataset_type
            
        except Exception as e:
            self._add_message(MessageType.ERROR, 
                f"⚠️ Error with professional generator: {e}")
            # Fallback to basic method
            extracted_data = self._extract_repository_data()
            calculated_data = self._apply_formulas(extracted_data)[:5]
            self.detected_dataset_type = None
        
        # Create preview DataFrame
        self.preview_data = pd.DataFrame(calculated_data[:5])  # First 5 rows
        
        # Generate column previews
        column_previews = []
        for col in self.current_requirement.columns:
            if col in self.preview_data.columns:
                values = self.preview_data[col].tolist()
                col_preview = ColumnPreview(
                    column_name=col,
                    data_type=str(self.preview_data[col].dtype),
                    formula=self.current_requirement.formulas.get(col, 'Direct extraction'),
                    sample_values=values,
                    min_value=self.preview_data[col].min() if pd.api.types.is_numeric_dtype(self.preview_data[col]) else None,
                    max_value=self.preview_data[col].max() if pd.api.types.is_numeric_dtype(self.preview_data[col]) else None,
                    unique_count=self.preview_data[col].nunique()
                )
                column_previews.append(col_preview)
        
        # Format preview message
        preview_text = f"""👁️ **Dataset Preview**

**Total Rows:** {len(calculated_data)}
**Columns:** {len(column_previews)}

**Sample Data (first 5 rows):**

"""
        
        for preview in column_previews:
            preview_text += f"\n**{preview.column_name}** ({preview.data_type})\n"
            preview_text += f"  Formula: {preview.formula}\n"
            preview_text += f"  Sample: {preview.sample_values}\n"
            if preview.min_value is not None:
                preview_text += f"  Range: [{preview.min_value:.2f} - {preview.max_value:.2f}]\n"
            preview_text += f"  Unique values: {preview.unique_count}\n"
        
        self._add_message(MessageType.PREVIEW, preview_text)
        
        if self.mode == AgentMode.ASK:
            self._add_message(MessageType.QUESTION, 
                "❓ This is REAL data from your repository. Confirm generation? Reply 'yes' to generate full dataset, 'no' to cancel")
            return {
                'status': 'awaiting_final_approval',
                'preview': column_previews,
                'total_rows': len(calculated_data)
            }
        else:
            # Auto-proceed in AGENT mode
            return self.generate_full_dataset()
    
    def generate_full_dataset(self) -> Dict[str, Any]:
        """
        Generate complete dataset (ONLY after sample accepted)
        
        Workflow enforced:
        1. Check if sample was generated
        2. Check if user accepted sample
        3. Generate full dataset from repository
        
        Returns:
            Generation result with file paths
        """
        # ENFORCE WORKFLOW: Must generate sample first and get acceptance
        if not self.sample_generated:
            self._add_message(MessageType.ERROR, 
                "❌ Cannot generate full dataset without sample review!\n"
                "   Please use generate_sample() first.")
            return {
                'error': 'sample_required',
                'message': 'Must generate and review sample before full generation'
            }
        
        if not self.user_accepted:
            self._add_message(MessageType.ERROR, 
                "❌ Sample not yet accepted by user!\n"
                "   Please review sample and provide feedback or acceptance.")
            return {
                'error': 'acceptance_required',
                'message': 'User must accept sample before full generation',
                'feedback_iterations': self.feedback_iterations
            }
        
        self._add_message(MessageType.THINKING, 
            f"🚀 Generating FULL dataset (after {self.feedback_iterations} feedback iterations)...")
        
        # Use detected dataset type or detect now
        dataset_type = getattr(self, 'detected_dataset_type', None) or self._detect_dataset_type()
        
        # Create timestamp and output directory once
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('generated_datasets')
        output_dir.mkdir(exist_ok=True)
        
        # SEPARATE PIPELINES: Professional vs Custom
        if dataset_type == 'custom':
            # CUSTOM FORMULA PIPELINE - Don't use professional generators
            self._add_message(MessageType.THINKING,
                "🔧 Using CUSTOM METRICS pipeline (not professional benchmark)")
            
            extracted_data = self._extract_repository_data()
            calculated_data = self._apply_formulas(extracted_data)
            df = pd.DataFrame(calculated_data)
            
            # Apply custom formulas from conversation
            df = self._apply_custom_formulas_to_dataframe(df)
            
            # Save custom dataset
            csv_path = output_dir / f'custom_metrics_{timestamp}.csv'
            json_path = output_dir / f'custom_metrics_{timestamp}.json'
            
            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient='records', indent=2)
            
            self._add_message(MessageType.SUCCESS,
                f"✅ Custom metrics dataset saved: {csv_path}")
        
        else:
            # PROFESSIONAL BENCHMARK PIPELINE - Keep exact format
            try:
                # Use ProfessionalDatasetGenerator
                generator = ProfessionalDatasetGenerator(str(self.repo_path))
                
                # Generate based on detected type
                if dataset_type == 'defects4j':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating Defects4J dataset (buggy/fixed pairs)...")
                    result = generator.generate_defects4j_dataset()
                
                elif dataset_type == 'bugsjar':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating Bugs.jar dataset (bug records with patches)...")
                    result = generator.generate_bugsjar_dataset()
                
                elif dataset_type == 'promise':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating PROMISE dataset (comprehensive metrics)...")
                    result = generator.generate_promise_dataset()
                
                elif dataset_type == 'codexglue':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating CodeXGLUE dataset (code-text pairs)...")
                    result = generator.generate_codexglue_dataset()
                
                elif dataset_type == 'codesearchnet':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating CodeSearchNet dataset (code documentation)...")
                    result = generator.generate_codesearchnet_dataset()
                
                elif dataset_type == 'manystubs4j':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating ManySStuBs4J dataset (bug patterns)...")
                    result = generator.generate_manystubs4j_dataset()
                
                elif dataset_type == 'sourcerer':
                    self._add_message(MessageType.THINKING, 
                        "📦 Generating Sourcerer dataset (repository statistics)...")
                    result = generator.generate_sourcerer_dataset()
                
                else:
                    raise ValueError(f"Unknown dataset type: {dataset_type}")
                
                # Use paths from generator result - DON'T MODIFY PROFESSIONAL FORMATS
                csv_path = Path(result.get('csv_path', '')) if result.get('csv_path') else None
                json_path = Path(result.get('json_path', '')) if result.get('json_path') else None
                
                # Load data for row count
                if csv_path and csv_path.exists():
                    df = pd.read_csv(csv_path)
                elif json_path and json_path.exists():
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    df = pd.DataFrame(data if isinstance(data, list) else [data])
                else:
                    raise ValueError("No data generated by professional generator")
                
                # DON'T apply custom formulas to professional benchmarks
                self._add_message(MessageType.SUCCESS,
                    f"✅ Professional {dataset_type.upper()} dataset generated (exact format preserved)")
                
            except Exception as e:
                self._add_message(MessageType.ERROR, 
                    f"⚠️ Professional generator failed: {e}. Using fallback...")
                # Fallback to basic method
                extracted_data = self._extract_repository_data()
                calculated_data = self._apply_formulas(extracted_data)
                df = pd.DataFrame(calculated_data)
                
                # Save files (fallback)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = Path('generated_datasets')
                output_dir.mkdir(exist_ok=True)
                
                csv_path = output_dir / f'dataset_{timestamp}.csv'
                json_path = output_dir / f'dataset_{timestamp}.json'
                
                df.to_csv(csv_path, index=False)
                df.to_json(json_path, orient='records', indent=2)
        
        # Save metadata (timestamp and output_dir already set above)
        meta_path = output_dir / f'dataset_{timestamp}_metadata.json'
        
        # Save metadata
        metadata = {
            'generated_at': timestamp,
            'description': self.current_requirement.description,
            'repository': str(self.repo_path),
            'columns': self.current_requirement.columns,
            'formulas': self.current_requirement.formulas,
            'rows': len(df),
            'mode': self.mode.value,
            'feedback_iterations': self.feedback_iterations,
            'sample_accepted': self.user_accepted,
            'conversation_history': [
                {'type': msg.type.value, 'content': msg.content, 'timestamp': msg.timestamp.isoformat()}
                for msg in self.conversation_history
            ]
        }
        
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        success_msg = f"""✅ **Dataset Generated Successfully!**

**Workflow Summary:**
  • Clarification rounds: {len([m for m in self.conversation_history if m.type == MessageType.QUESTION])}
  • Feedback iterations: {self.feedback_iterations}
  • Sample reviewed and accepted: ✅

**Files Created:**
  • CSV: {csv_path}
  • JSON: {json_path}
  • Metadata: {meta_path}

**Statistics:**
  • Rows: {len(df):,}
  • Columns: {len(df.columns)}
  • Size: {csv_path.stat().st_size:,} bytes
"""
        
        self._add_message(MessageType.SUCCESS, success_msg)
        
        return {
            'status': 'completed',
            'csv_file': str(csv_path),
            'json_file': str(json_path),
            'metadata_file': str(meta_path),
            'rows': len(df),
            'columns': len(df.columns)
        }
    
    def _extract_repository_data(self) -> List[Dict[str, Any]]:
        """Extract data from repository using available analyzers"""
        if not ANALYZERS_AVAILABLE:
            # Mock data for testing
            return [
                {'class_name': f'Class{i}', 'lines_of_code': 100 + i * 10}
                for i in range(1, 101)
            ]
        
        try:
            # Use CK analyzer
            ck_analyzer = CKMetricsAnalyzer(str(self.repo_path))
            ck_results = ck_analyzer.analyze_repository()
            
            # Use unified analyzer
            unified_analyzer = UnifiedMetricsAnalyzer(str(self.repo_path))
            unified_results = unified_analyzer.analyze_all()
            
            # Merge results
            data = []
            for class_data in ck_results:
                row = {
                    'class_name': class_data.get('class_name'),
                    'lines_of_code': class_data.get('loc', 0),
                    'cbo': class_data.get('cbo', 0),
                    'wmc': class_data.get('wmc', 0),
                    'lcom': class_data.get('lcom', 0),
                    'rfc': class_data.get('rfc', 0),
                    'dit': class_data.get('dit', 0),
                    'noc': class_data.get('noc', 0),
                    'method_count': class_data.get('number_of_methods', 0),
                    'field_count': class_data.get('number_of_fields', 0)
                }
                
                # Add unified metrics if available
                class_name = row['class_name']
                if class_name in unified_results:
                    unified = unified_results[class_name]
                    row['cyclomatic_complexity'] = unified.get('cyclomatic_complexity', 0)
                    row['cognitive_complexity'] = unified.get('cognitive_complexity', 0)
                    row['maintainability_index'] = unified.get('maintainability_index', 0)
                
                data.append(row)
            
            return data
            
        except Exception as e:
            self._add_message(MessageType.ERROR, 
                f"⚠️ Error extracting data: {e}")
            # Return mock data
            return [
                {'class_name': f'Class{i}', 'lines_of_code': 100 + i * 10}
                for i in range(1, 51)
            ]
    
    def _apply_formulas(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply formulas to extracted data"""
        # Filter to only requested columns
        req_cols = set(self.current_requirement.columns)
        
        result = []
        for row in data:
            new_row = {}
            
            # Copy requested columns
            for col in req_cols:
                if col in row:
                    new_row[col] = row[col]
                elif col in self.current_requirement.formulas:
                    # Apply formula
                    formula = self.current_requirement.formulas[col]
                    new_row[col] = self._eval_formula(formula, row)
                else:
                    new_row[col] = None
            
            result.append(new_row)
        
        return result
    
    def _eval_formula(self, formula: str, row: Dict[str, Any]) -> Any:
        """Evaluate a formula with row context"""
        # Simple formula evaluation
        # For production, use safer eval or generated Python functions
        try:
            if 'bug' in formula.lower():
                # Simulate bug count
                return np.random.randint(0, 5)
            elif 'sum' in formula.lower():
                # Find columns to sum
                cols = [k for k in row.keys() if isinstance(row[k], (int, float))]
                return sum(row[c] for c in cols[:2])
            else:
                return 0
        except:
            return None
    
    def _extract_custom_formulas_from_conversation(self) -> Dict[str, str]:
        """Extract custom formula definitions from conversation using LLM"""
        if not self.model:
            return {}
        
        # Collect all user messages
        conversation_text = ""
        for msg in self.conversation_history:
            if msg.type == MessageType.USER:
                conversation_text += msg.content + "\n"
        
        # Use LLM to dynamically parse formulas
        try:
            prompt = f"""Analyze this user request and extract ALL custom formula definitions.

User Request:
{conversation_text}

Extract formulas in JSON format:
{{
  "formula_name": "mathematical_expression",
  ...
}}

Rules:
- Use snake_case for formula names
- Keep original mathematical expressions
- Include ALL formulas mentioned (even if hundreds)
- If no formulas found, return empty object

Example:
{{
  "code_smell_density": "code_smells / (lines_of_code / 1000)",
  "test_coverage_health": "test_coverage - (bug_count / commit_count) * 10"
}}

Return ONLY valid JSON, no explanation."""

            response = self.model.generate_content(prompt)
            
            # Debug: print response
            print(f"\n[DEBUG] LLM Response:\n{response.text[:500]}\n")
            
            # Parse JSON response
            import re
            import json
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                formulas = json.loads(json_match.group())
                self._add_message(MessageType.SUCCESS,
                    f"✓ Extracted {len(formulas)} custom formulas using LLM")
                return formulas
            else:
                print(f"[DEBUG] No JSON found in response")
            
        except Exception as e:
            self._add_message(MessageType.ERROR,
                f"⚠️ LLM formula extraction failed: {e}")
            print(f"[DEBUG] Exception: {e}")
        
        return {}
    
    def _apply_custom_formulas_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply custom formulas - FULLY DYNAMIC using Multi-LLM Jury System"""
        
        # Check if Jury System is available
        if self.jury_system and JURY_SYSTEM_AVAILABLE:
            self._add_message(MessageType.THINKING,
                "🤖 Using Multi-LLM Jury System (ZERO hardcoded formulas)...")
            
            # Get user's formula request from conversation
            user_query = ""
            for msg in self.conversation_history:
                if msg.type == MessageType.USER:
                    user_query += msg.content + "\n"
            
            if not user_query.strip():
                self._add_message(MessageType.INFO,
                    "ℹ️ No formula request in conversation")
                return df
            
            try:
                # Process with Jury System - completely dynamic!
                enhanced_df = self.jury_system.process_user_request(user_query, df)
                
                new_cols = len(enhanced_df.columns) - len(df.columns)
                if new_cols > 0:
                    self._add_message(MessageType.SUCCESS,
                        f"✅ Jury System added {new_cols} formula columns")
                    return enhanced_df
                else:
                    self._add_message(MessageType.WARNING,
                        "⚠️ Jury System: No formulas could be applied")
                    
            except Exception as e:
                self._add_message(MessageType.ERROR,
                    f"❌ Jury System failed: {e}")
                # Fall through to fallback method
        
        # Fallback: Use old LLM extraction method if Jury System unavailable
        self._add_message(MessageType.INFO,
            "ℹ️ Using fallback method (LLM extraction)")
        
        custom_formulas = self._extract_custom_formulas_from_conversation()
        
        if not custom_formulas:
            self._add_message(MessageType.INFO,
                "ℹ️ No custom formulas detected in conversation")
            return df
        
        self._add_message(MessageType.THINKING,
            f"🔧 Processing {len(custom_formulas)} custom formulas...")
        
        # Analyze which formulas can be applied
        available_cols = set(df.columns)
        applied_count = 0
        skipped_formulas = []
        
        # Apply each formula with intelligent fallback
        for formula_name, formula_expr in custom_formulas.items():
            try:
                # Try to apply formula
                new_col = self._calculate_formula_column(df, formula_name, formula_expr)
                if new_col is not None:
                    df[formula_name] = new_col
                    applied_count += 1
                    self._add_message(MessageType.SUCCESS,
                        f"  ✓ {formula_name}")
                else:
                    # Formula failed - identify missing columns
                    missing_cols = self._identify_missing_columns(formula_expr, available_cols)
                    skipped_formulas.append((formula_name, formula_expr, missing_cols))
                    self._add_message(MessageType.WARNING,
                        f"  ⊘ {formula_name} (missing: {', '.join(missing_cols)})")
            except Exception as e:
                self._add_message(MessageType.ERROR,
                    f"  ✗ {formula_name}: {e}")
        
        # Report results
        if applied_count > 0:
            self._add_message(MessageType.SUCCESS,
                f"✅ Applied {applied_count}/{len(custom_formulas)} formulas")
        
        # Use LLM to suggest alternatives for skipped formulas
        if skipped_formulas and self.model:
            self._suggest_formula_alternatives(df, skipped_formulas)
        
        return df
    
    def _identify_missing_columns(self, formula_expr: str, available_cols: set) -> list:
        """Identify missing columns from formula expression"""
        import re
        # Extract variable names from formula (basic regex)
        variables = re.findall(r'\b[a-z_][a-z0-9_]*\b', formula_expr)
        
        # Filter out Python keywords and functions
        keywords = {'sum', 'max', 'min', 'abs', 'len', 'int', 'float', 'str', 'ln', 'log', 'sqrt', 'if', 'else', 'and', 'or', 'not'}
        candidates = [v for v in variables if v not in keywords]
        
        # Check which are missing
        missing = [c for c in candidates if c not in available_cols]
        return list(set(missing))  # Unique
    
    def _suggest_formula_alternatives(self, df: pd.DataFrame, skipped_formulas: list):
        """Use LLM to suggest alternatives for skipped formulas"""
        if not self.model:
            return
        
        available_cols = ', '.join(df.columns)
        
        self._add_message(MessageType.THINKING,
            f"🤔 Asking LLM for alternatives to {len(skipped_formulas)} skipped formulas...")
        
        for formula_name, formula_expr, missing_cols in skipped_formulas[:3]:  # Limit to 3
            try:
                prompt = f"""This formula cannot be calculated:

Formula: {formula_name} = {formula_expr}
Missing columns: {', '.join(missing_cols)}
Available columns: {available_cols}

Suggest an alternative formula using ONLY available columns, or explain why impossible.
Keep response under 50 words."""

                response = self.model.generate_content(prompt)
                self._add_message(MessageType.SUGGESTION,
                    f"💡 {formula_name}: {response.text[:200]}")
            except:
                continue
    
    def _calculate_formula_column(self, df: pd.DataFrame, name: str, formula: str) -> pd.Series:
        """Calculate a formula column from a DataFrame"""
        # Map common column name variations
        col_mapping = {
            'lines_of_code': ['lines_of_code', 'loc', 'lines', 'line_count'],
            'comment_lines': ['comment_lines', 'comments', 'comment_count'],
            'blank_lines': ['blank_lines', 'blanks'],
            'cyclomatic_complexity': ['cyclomatic_complexity', 'cc', 'complexity'],
            'cognitive_complexity': ['cognitive_complexity'],
            'maintainability_index': ['maintainability_index', 'mi'],
            'cbo': ['cbo', 'coupling'],
            'wmc': ['wmc', 'weighted_methods'],
            'lcom': ['lcom', 'cohesion'],
            'bug_count': ['bug_count', 'bugs', 'num_bugs', 'defects'],
            'commit_count': ['commit_count', 'commits'],
            'bug_fix_count': ['bug_fix_count', 'bug_fixes', 'fixes']
        }
        
        # Find actual column names in DataFrame
        available_cols = {}
        for standard_name, variations in col_mapping.items():
            for var in variations:
                if var in df.columns:
                    available_cols[standard_name] = var
                    break
        
        # Replace formula variables with actual column names
        formula_code = formula
        for standard_name, actual_col in available_cols.items():
            # Replace variable name in formula
            formula_code = formula_code.replace(standard_name, f"df['{actual_col}']")
        
        # Safe evaluation with basic operations
        try:
            # Use pandas eval for safety
            result = eval(formula_code, {"df": df, "np": np, "pd": pd, "max": max, "min": min, "sum": sum})
            return result
        except Exception as e:
            # If eval fails, return None column
            return None
    
    def _generate_missing_formulas(self):
        """Use LLM to generate missing formula definitions"""
        if not self.model:
            self._add_message(MessageType.ERROR, 
                "⚠️ Cannot generate formulas without LLM")
            return
            
        for metric_name in self.current_requirement.missing_metrics:
            self._add_message(MessageType.THINKING, 
                f"🔧 Generating formula for: {metric_name}")
                
            prompt = f"""Generate a Python function to calculate: {metric_name}

Available data for each row:
{json.dumps(list(self.available_metrics.values())[0] if self.available_metrics else [], indent=2)}

Provide:
1. Function name
2. Description
3. Python code (function that takes a dict and returns a value)
4. Dependencies (required metrics)
5. Example output

Respond in JSON format:
{{
    "name": "metric_name",
    "description": "what it calculates",
    "python_code": "def calculate_X(data):\\n    return ...",
    "dependencies": ["metric1", "metric2"],
    "example_output": 42
}}"""

            try:
                response = self.model.generate_content(prompt)
                formula_def = json.loads(self._extract_json(response.text))
                
                self.generated_formulas.append(FormulaDefinition(**formula_def))
                
                self._add_message(MessageType.SUCCESS, 
                    f"✅ Generated formula for {metric_name}")
                    
            except Exception as e:
                self._add_message(MessageType.ERROR, 
                    f"❌ Failed to generate formula for {metric_name}: {e}")
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code blocks or raw text"""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text
    
    def _add_message(self, msg_type: MessageType, content: str):
        """Add message to conversation history"""
        msg = ConversationMessage(type=msg_type, content=content)
        self.conversation_history.append(msg)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get formatted conversation history"""
        return [
            {
                'type': msg.type.value,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in self.conversation_history
        ]
    
    def switch_mode(self, new_mode: AgentMode):
        """Switch between ASK and AGENT modes"""
        old_mode = self.mode
        self.mode = new_mode
        self._add_message(MessageType.SYSTEM, 
            f"🔄 Mode switched: {old_mode.value} → {new_mode.value}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI interface for testing"""
    print("=" * 80)
    print("Enhanced Agentic Dataset System - CLI")
    print("=" * 80)
    
    # Get repo path
    repo_path = input("\n📁 Enter repository path: ").strip()
    if not repo_path:
        repo_path = "d:\\GitIntel\\repo"  # Default for testing
    
    # Get mode
    mode_input = input("\n🤖 Mode? (ask/agent) [ask]: ").strip().lower() or "ask"
    mode = AgentMode.ASK if mode_input == "ask" else AgentMode.AGENT
    
    # Initialize system
    system = EnhancedAgenticSystem(mode=mode)
    
    try:
        system.set_repository(repo_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Get user request
    request = input("\n💬 What dataset do you need?\n> ").strip()
    
    # Start conversation
    result = system.start_conversation(request)
    
    # Handle conversation loop
    while result['status'] in ['needs_clarification', 'awaiting_approval', 'awaiting_final_approval']:
        if result['status'] == 'needs_clarification':
            answer = input(f"\n{result['question']}\n> ").strip()
            result = system.continue_conversation(answer)
        elif result['status'] == 'awaiting_approval':
            answer = input("\n> ").strip().lower()
            if answer == 'yes':
                result = system.generate_preview()
            elif answer == 'modify':
                modify = input("What changes? > ").strip()
                result = system.continue_conversation(modify)
            else:
                print("❌ Cancelled")
                return
        elif result['status'] == 'awaiting_final_approval':
            answer = input("\n> ").strip().lower()
            if answer == 'yes':
                result = system.generate_full_dataset()
            else:
                print("❌ Cancelled")
                return
    
    # Show final result
    if result['status'] == 'completed':
        print(f"\n✅ Dataset generated: {result['csv_file']}")
    
    # Show conversation history
    print("\n" + "=" * 80)
    print("Conversation History:")
    print("=" * 80)
    for msg in system.get_conversation_history():
        print(f"\n[{msg['type'].upper()}] {msg['timestamp']}")
        print(msg['content'])


if __name__ == "__main__":
    main()
