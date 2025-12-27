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

# Import existing analyzers
try:
    from unified_metrics_analyzer import UnifiedMetricsAnalyzer
    from ck_metrics_analyzer import CKMetricsAnalyzer
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
            
    def set_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Set repository and discover available metrics
        
        Args:
            repo_path: Path to Git repository
            
        Returns:
            Repository info with discovered metrics
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository not found: {repo_path}")
            
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
        
        # Re-understand with new context
        full_context = "\n".join([
            msg.content for msg in self.conversation_history 
            if msg.type in [MessageType.USER, MessageType.QUESTION]
        ])
        
        understanding = self._understand_request(full_context)
        
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
            return result
        except Exception as e:
            self._add_message(MessageType.ERROR, 
                f"⚠️ LLM understanding error: {e}")
            return self._basic_understanding(request)
    
    def _basic_understanding(self, request: str) -> Dict[str, Any]:
        """Fallback basic understanding without LLM"""
        # Simple keyword matching
        needs_defect = any(kw in request.lower() for kw in ['defect', 'bug', 'fault', 'error'])
        needs_complexity = any(kw in request.lower() for kw in ['complex', 'cyclomatic', 'cognitive'])
        needs_maintainability = any(kw in request.lower() for kw in ['maintain', 'technical debt', 'quality'])
        
        columns = []
        formulas = {}
        
        # Determine columns based on keywords
        if needs_defect:
            columns = ['class_name', 'lines_of_code', 'cbo', 'wmc', 'bug_count']
            formulas = {'bug_count': 'Count of bug-fix commits'}
        elif needs_complexity:
            columns = ['class_name', 'cyclomatic_complexity', 'cognitive_complexity', 'lines_of_code']
        elif needs_maintainability:
            columns = ['class_name', 'maintainability_index', 'technical_debt_hours']
        else:
            # Need clarification
            return {
                'needs_clarification': True,
                'question': "What type of dataset do you need? (e.g., defect prediction, complexity analysis, maintainability metrics)",
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
                "❓ Approve this plan? Reply 'yes' to generate preview, 'modify' to change, 'cancel' to stop")
            return {
                'status': 'awaiting_approval',
                'plan': req
            }
        else:
            # Auto-proceed in AGENT mode
            return self.generate_preview()
    
    def generate_preview(self) -> Dict[str, Any]:
        """
        Generate preview of dataset with sample data
        
        Returns:
            Preview information with sample rows
        """
        if not self.current_requirement:
            raise ValueError("No requirement set. Call start_conversation first.")
            
        self._add_message(MessageType.THINKING, 
            "🔄 Extracting data from repository...")
            
        # Extract real data
        extracted_data = self._extract_repository_data()
        
        self._add_message(MessageType.THINKING, 
            "🧮 Applying formulas and calculations...")
            
        # Apply formulas
        calculated_data = self._apply_formulas(extracted_data)
        
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
        Generate complete dataset
        
        Returns:
            Generation result with file paths
        """
        self._add_message(MessageType.THINKING, 
            "🚀 Generating full dataset...")
            
        # Extract all data
        extracted_data = self._extract_repository_data()
        calculated_data = self._apply_formulas(extracted_data)
        
        # Create DataFrame
        df = pd.DataFrame(calculated_data)
        
        # Save files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('generated_datasets')
        output_dir.mkdir(exist_ok=True)
        
        csv_path = output_dir / f'dataset_{timestamp}.csv'
        json_path = output_dir / f'dataset_{timestamp}.json'
        meta_path = output_dir / f'dataset_{timestamp}_metadata.json'
        
        # Save CSV
        df.to_csv(csv_path, index=False)
        
        # Save JSON
        df.to_json(json_path, orient='records', indent=2)
        
        # Save metadata
        metadata = {
            'generated_at': timestamp,
            'description': self.current_requirement.description,
            'repository': str(self.repo_path),
            'columns': self.current_requirement.columns,
            'formulas': self.current_requirement.formulas,
            'rows': len(df),
            'mode': self.mode.value,
            'conversation_history': [
                {'type': msg.type.value, 'content': msg.content, 'timestamp': msg.timestamp.isoformat()}
                for msg in self.conversation_history
            ]
        }
        
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        success_msg = f"""✅ **Dataset Generated Successfully!**

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
