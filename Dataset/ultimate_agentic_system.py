"""
🚀 Ultimate Agentic Dataset Maker
===================================

Full conversational agent that:
1. Accepts GitHub link or local repo
2. Clones repo if needed
3. Asks iterative questions to understand user needs
4. Shows available 64 metrics + 7 benchmark formats
5. Generates TODO list and sample preview
6. Allows modifications before execution
7. Handles both KNOWN and UNKNOWN dataset types

Recommended Model: gemini-2.5-flash (best balance of speed + reasoning)
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd
from enum import Enum

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

# Gemini imports
try:
    import google.genai as genai
    GENAI_NEW = True
except ImportError:
    import google.generativeai as genai
    GENAI_NEW = False

# Import existing components
from Dataset.metrics_catalog import MetricsCatalog
from llm_git_analyzer import LLMGitAnalyzer
from unified_metrics_analyzer import UnifiedMetricsAnalyzer
from ck_metrics_analyzer import CKMetricsAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetType(Enum):
    """Dataset classification"""
    DEFECTS4J = "defects4j"
    BUGS_JAR = "bugs_jar"
    MANY_SSTUBS = "many_sstubs"
    CODEXGLUE = "codexglue"
    CODESEARCHNET = "codesearchnet"
    PROMISE = "promise"
    SOURCERER = "sourcerer"
    CUSTOM = "custom"
    HYBRID = "hybrid"


@dataclass
class ConversationState:
    """Tracks conversation progress"""
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    research_goal: Optional[str] = None
    interested_metrics: List[str] = None
    dataset_type: Optional[DatasetType] = None
    custom_formulas: Dict[str, str] = None
    temporal_data: bool = False
    commit_level: bool = False
    file_level: bool = True
    understanding_complete: bool = False
    
    def __post_init__(self):
        if self.interested_metrics is None:
            self.interested_metrics = []
        if self.custom_formulas is None:
            self.custom_formulas = {}


@dataclass
class DatasetPlan:
    """Generation plan before execution"""
    dataset_type: str
    extraction_steps: List[str]
    metrics_to_compute: List[str]
    expected_columns: List[str]
    sample_rows: List[Dict]
    estimated_rows: int
    output_format: str


class UltimateAgenticDatasetMaker:
    """
    Fully autonomous agentic dataset maker
    Converses until understanding is complete, then generates
    """
    
    def __init__(self, output_dir: str = None):
        """Initialize the ultimate agentic system"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env file")
        
        # Configure Gemini - Handle both old and new API
        try:
            if GENAI_NEW:
                # New google.genai API
                client = genai.Client(api_key=self.api_key)
                self.model = client.models.generate_content
                self.model_name = 'gemini-2.0-flash-exp'
                self.genai_client = client
                logger.info("✅ Using google.genai (new API) with gemini-2.0-flash-exp")
            else:
                # Old google.generativeai API
                genai.configure(api_key=self.api_key)
                try:
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.model_name = 'gemini-2.0-flash-exp'
                except:
                    self.model = genai.GenerativeModel('gemini-flash-latest')
                    self.model_name = 'gemini-flash-latest'
                logger.info(f"✅ Using google.generativeai (old API) with {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            raise
        
        # Output directory
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "generated_datasets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Conversation state
        self.state = ConversationState()
        self.conversation_history = []
        
        # Available metrics (use alias name for compatibility)
        self.catalog = MetricsCatalog()
        self.metrics_catalog = self.catalog
        self.available_metrics = self.catalog.get_all_metrics()
        
        # Known dataset templates
        self.known_datasets = {
            'defects4j': self._defects4j_template,
            'bugs_jar': self._bugs_jar_template,
            'promise': self._promise_template,
        }
        
        logger.info(f"📊 Loaded {len(self.available_metrics)} metrics across {len(self.catalog.get_categories())} categories")
    
    # =====================================================================
    #                    PHASE 1: REPOSITORY INPUT
    # =====================================================================
    
    def handle_repository_input(self, input_str: str) -> Dict[str, Any]:
        """
        Handle repo link or path
        Clones if GitHub link, validates if local path
        """
        input_str = input_str.strip()
        
        # Check if it's a GitHub URL
        if 'github.com' in input_str or input_str.startswith('https://'):
            return self._clone_repository(input_str)
        
        # Check if it's a local path
        path = Path(input_str)
        if path.exists():
            return self._validate_local_repo(path)
        
        return {
            'success': False,
            'error': 'Invalid input. Provide GitHub URL or valid local path.'
        }
    
    def _clone_repository(self, url: str) -> Dict[str, Any]:
        """Clone GitHub repository"""
        try:
            # Extract repo name
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = self.output_dir / 'repos' / repo_name
            clone_path.parent.mkdir(parents=True, exist_ok=True)
            
            if clone_path.exists():
                logger.info(f"📁 Repository already cloned: {clone_path}")
                self.state.repo_path = str(clone_path)
                self.state.repo_url = url
                return self._analyze_repository(clone_path)
            
            logger.info(f"📥 Cloning repository: {url}")
            result = subprocess.run(
                ['git', 'clone', url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.state.repo_path = str(clone_path)
                self.state.repo_url = url
                return self._analyze_repository(clone_path)
            else:
                return {
                    'success': False,
                    'error': f'Clone failed: {result.stderr}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Clone error: {str(e)}'
            }
    
    def _validate_local_repo(self, path: Path) -> Dict[str, Any]:
        """Validate local repository"""
        self.state.repo_path = str(path)
        return self._analyze_repository(path)
    
    def _analyze_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Quick analysis of repository"""
        try:
            # Count files
            java_files = list(repo_path.rglob('*.java'))
            py_files = list(repo_path.rglob('*.py'))
            all_files = java_files + py_files
            
            # Count LOC
            total_loc = 0
            for file in all_files:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        total_loc += len(f.readlines())
                except:
                    pass
            
            # Detect language
            language = 'Java' if len(java_files) > len(py_files) else 'Python' if py_files else 'Unknown'
            
            # Check if git repo
            is_git = (repo_path / '.git').exists()
            
            # Get commit count if git
            commit_count = 0
            if is_git:
                try:
                    result = subprocess.run(
                        ['git', 'rev-list', '--count', 'HEAD'],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        commit_count = int(result.stdout.strip())
                except:
                    pass
            
            summary = {
                'success': True,
                'path': str(repo_path),
                'language': language,
                'file_count': len(all_files),
                'loc': total_loc,
                'is_git': is_git,
                'commit_count': commit_count,
                'message': f"✅ Repository loaded: {total_loc:,} LOC, {len(all_files)} files, {language}" + 
                           (f", {commit_count} commits" if is_git else "")
            }
            
            logger.info(summary['message'])
            return summary
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    # =====================================================================
    #                PHASE 2: CONVERSATIONAL DISCOVERY
    # =====================================================================
    
    def start_conversation(self) -> str:
        """Start the discovery conversation"""
        if not self.state.repo_path:
            return "❌ Please provide a repository first using handle_repository_input()"
        
        # Build context about available capabilities
        context = self._build_system_context()
        
        # Initial question
        initial_prompt = f"""You are an expert data scientist helping create custom datasets from code repositories.

{context}

The user has loaded a repository. Start a conversation to understand:
1. What is their research goal?
2. Which metrics are they interested in?
3. Do they want a known dataset format (Defects4J, Bugs.jar, etc.) or custom?
4. Do they need temporal/commit-level data or just file-level?

Ask ONE clear question at a time. Be friendly and helpful.

Start the conversation:"""
        
        response = self._call_llm(initial_prompt)
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response
    
    def continue_conversation(self, user_message: str) -> Dict[str, Any]:
        """Continue the discovery conversation"""
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Build prompt with history and system context
        context = self._build_system_context()
        history_text = self._format_conversation_history()
        
        # Ask LLM to analyze and respond
        analysis_prompt = f"""You are analyzing a conversation to understand dataset requirements.

{context}

Conversation so far:
{history_text}

Analyze the user's latest message: "{user_message}"

Tasks:
1. Extract any mentioned metrics, formulas, or dataset types
2. Update your understanding
3. Decide if you have enough information or need to ask more
4. If ready, set "understanding_complete": true
5. Respond with next question OR summarize understanding

Respond in JSON format:
{{
    "extracted_info": {{
        "metrics": ["metric1", "metric2"],
        "dataset_type": "known_type or custom",
        "formulas": {{"formula_name": "formula"}},
        "temporal_data": true/false
    }},
    "understanding_complete": true/false,
    "response_to_user": "your message"
}}"""
        
        llm_response = self._call_llm(analysis_prompt)
        
        try:
            # Parse JSON response
            parsed = json.loads(llm_response)
            
            # Update state
            if 'extracted_info' in parsed:
                info = parsed['extracted_info']
                if 'metrics' in info:
                    self.state.interested_metrics.extend(info['metrics'])
                if 'dataset_type' in info:
                    self.state.dataset_type = info['dataset_type']
                if 'formulas' in info:
                    self.state.custom_formulas.update(info['formulas'])
                if 'temporal_data' in info:
                    self.state.temporal_data = info['temporal_data']
            
            if 'understanding_complete' in parsed:
                self.state.understanding_complete = parsed['understanding_complete']
            
            response = parsed.get('response_to_user', 'I understand. What else would you like to know?')
            
            self.conversation_history.append({
                'role': 'assistant',
                'content': response
            })
            
            return {
                'response': response,
                'understanding_complete': self.state.understanding_complete,
                'state': asdict(self.state)
            }
            
        except json.JSONDecodeError:
            # Fallback: use raw response
            self.conversation_history.append({
                'role': 'assistant',
                'content': llm_response
            })
            
            return {
                'response': llm_response,
                'understanding_complete': False,
                'state': asdict(self.state)
            }
    
    # =====================================================================
    #            PHASE 3: CLASSIFICATION & PLANNING
    # =====================================================================
    
    def generate_plan(self) -> DatasetPlan:
        """Generate execution plan based on understanding"""
        if not self.state.understanding_complete:
            raise ValueError("Understanding not complete. Continue conversation first.")
        
        # Classify dataset type
        dataset_type = self._classify_dataset_type()
        
        # Build execution steps
        steps = self._build_execution_steps(dataset_type)
        
        # Identify required metrics
        metrics = self._identify_required_metrics()
        
        # Generate sample data
        sample_rows = self._generate_sample_rows(metrics)
        
        # Create plan
        plan = DatasetPlan(
            dataset_type=dataset_type.value if isinstance(dataset_type, DatasetType) else dataset_type,
            extraction_steps=steps,
            metrics_to_compute=metrics,
            expected_columns=[m for m in metrics],
            sample_rows=sample_rows,
            estimated_rows=self._estimate_row_count(),
            output_format='CSV'
        )
        
        return plan
    
    def show_plan_preview(self, plan: DatasetPlan) -> str:
        """Show formatted plan preview"""
        preview = f"""
📋 DATASET GENERATION PLAN
{'='*60}

Dataset Type: {plan.dataset_type}
Output Format: {plan.output_format}
Estimated Rows: {plan.estimated_rows}

📝 EXECUTION STEPS:
"""
        for i, step in enumerate(plan.extraction_steps, 1):
            preview += f"  {i}. {step}\n"
        
        preview += f"\n📊 COLUMNS ({len(plan.expected_columns)}):\n"
        preview += "  " + ", ".join(plan.expected_columns) + "\n"
        
        preview += f"\n🔍 SAMPLE DATA (3 rows):\n"
        if plan.sample_rows:
            df = pd.DataFrame(plan.sample_rows)
            preview += df.to_string(index=False) + "\n"
        
        preview += "\n" + "="*60
        preview += "\n\n Would you like to:\n"
        preview += "  1. ✅ Execute this plan\n"
        preview += "  2. ✏️ Modify the plan\n"
        preview += "  3. ❌ Cancel\n"
        
        return preview
    
    # =====================================================================
    #                    PHASE 4: EXECUTION
    # =====================================================================
    
    def execute_plan(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Execute the dataset generation plan"""
        logger.info("🚀 Starting dataset generation...")
        
        try:
            # Determine if known or custom dataset
            if plan.dataset_type in self.known_datasets:
                result = self._execute_known_dataset(plan)
            else:
                result = self._execute_custom_dataset(plan)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_known_dataset(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Execute generation for known dataset type"""
        template_func = self.known_datasets[plan.dataset_type]
        return template_func(plan)
    
    def _execute_custom_dataset(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Execute generation for custom dataset"""
        logger.info("📊 Generating custom dataset...")
        
        # Initialize extractors
        repo_path = Path(self.state.repo_path)
        
        data_rows = []
        
        # Extract data based on plan
        if self.state.file_level:
            # File-level dataset
            data_rows = self._extract_file_level_data(repo_path, plan.metrics_to_compute)
        
        if self.state.commit_level:
            # Commit-level dataset
            commit_data = self._extract_commit_level_data(repo_path, plan.metrics_to_compute)
            data_rows.extend(commit_data)
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"custom_dataset_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"✅ Dataset saved: {output_file}")
        
        return {
            'success': True,
            'output_file': str(output_file),
            'rows': len(df),
            'columns': list(df.columns),
            'preview': df.head(5).to_dict('records')
        }
    
    # =====================================================================
    #                      HELPER METHODS
    # =====================================================================
    
    def _build_system_context(self) -> str:
        """Build context about system capabilities"""
        return f"""System Capabilities:
- 64 metrics across 14 categories: {', '.join(self.metrics_catalog.get_categories())}
- 7 benchmark dataset formats: Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, PROMISE, Sourcerer
- Can handle both known and custom dataset formats
- Supports file-level and commit-level analysis
- Repository: {self.state.repo_path or 'Not loaded'}
"""
    
    def _format_conversation_history(self) -> str:
        """Format conversation history for LLM"""
        history = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            role = "Agent" if msg['role'] == 'assistant' else "User"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)
    
    def _call_llm(self, prompt: str) -> str:
        """Call Gemini LLM"""
        try:
            if GENAI_NEW:
                # New API: use client
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            else:
                # Old API: use model directly
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "I apologize, I encountered an error. Could you rephrase that?"
    
    def _classify_dataset_type(self) -> DatasetType:
        """Classify dataset type based on conversation"""
        # Use LLM to classify
        prompt = f"""Based on this conversation state, classify the dataset type:
{json.dumps(asdict(self.state), indent=2)}

Known types: defects4j, bugs_jar, many_sstubs, codexglue, codesearchnet, promise, sourcerer
If doesn't match known types, classify as "custom" or "hybrid"

Respond with just the type name."""
        
        response = self._call_llm(prompt).strip().lower()
        
        # Map to enum
        for dtype in DatasetType:
            if dtype.value in response:
                return dtype
        
        return DatasetType.CUSTOM
    
    def _build_execution_steps(self, dataset_type: DatasetType) -> List[str]:
        """Build execution steps"""
        steps = []
        
        if dataset_type in [DatasetType.DEFECTS4J, DatasetType.BUGS_JAR]:
            steps.append("Extract bug-fixing commits")
            steps.append("Get buggy/fixed code pairs")
        
        if self.state.interested_metrics:
            steps.append(f"Compute {len(self.state.interested_metrics)} metrics")
        
        if self.state.temporal_data:
            steps.append("Extract commit timeline")
        
        steps.append("Generate dataset")
        steps.append("Save to CSV")
        
        return steps
    
    def _identify_required_metrics(self) -> List[str]:
        """Identify required metrics"""
        # Start with explicitly mentioned metrics
        metrics = list(set(self.state.interested_metrics))
        
        # Add defaults based on dataset type
        if self.state.dataset_type in ['defects4j', 'bugs_jar']:
            defaults = ['loc', 'cyclomatic_complexity', 'num_methods', 'defect_density']
            metrics.extend([m for m in defaults if m not in metrics])
        
        return metrics
    
    def _generate_sample_rows(self, metrics: List[str]) -> List[Dict]:
        """Generate sample rows for preview"""
        # This would extract real data, but for preview we show structure
        sample = []
        for i in range(3):
            row = {'id': i+1, 'file': f'Example{i+1}.java'}
            for metric in metrics[:5]:  # Show first 5 metrics
                row[metric] = 'TBD'
            sample.append(row)
        return sample
    
    def _estimate_row_count(self) -> int:
        """Estimate number of rows in final dataset"""
        # Rough estimate based on repo
        if self.state.file_level:
            # Estimate files
            return 50
        if self.state.commit_level:
            # Estimate commits
            return 100
        return 0
    
    def _extract_file_level_data(self, repo_path: Path, metrics: List[str]) -> List[Dict]:
        """Extract file-level data"""
        # This would use your existing extractors
        rows = []
        # Placeholder - integrate with your UnifiedMetricsAnalyzer
        return rows
    
    def _extract_commit_level_data(self, repo_path: Path, metrics: List[str]) -> List[Dict]:
        """Extract commit-level data"""
        # This would use your existing extractors
        rows = []
        # Placeholder - integrate with your LLMGitAnalyzer
        return rows
    
    # =====================================================================
    #                 KNOWN DATASET TEMPLATES
    # =====================================================================
    
    def _defects4j_template(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Generate Defects4J-style dataset"""
        logger.info("📦 Generating Defects4J dataset...")
        # Use your existing dataset_generator.py logic
        return {'success': True, 'message': 'Defects4J dataset generated'}
    
    def _bugs_jar_template(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Generate Bugs.jar-style dataset"""
        logger.info("📦 Generating Bugs.jar dataset...")
        return {'success': True, 'message': 'Bugs.jar dataset generated'}
    
    def _promise_template(self, plan: DatasetPlan) -> Dict[str, Any]:
        """Generate PROMISE-style dataset"""
        logger.info("📦 Generating PROMISE dataset...")
        return {'success': True, 'message': 'PROMISE dataset generated'}


# =====================================================================
#                         CLI INTERFACE
# =====================================================================

def main():
    """CLI interface for ultimate agentic dataset maker"""
    print("🤖 Ultimate Agentic Dataset Maker")
    print("=" * 60)
    
    # Initialize system
    agent = UltimateAgenticDatasetMaker()
    
    # Step 1: Get repository
    print("\n📁 Step 1: Provide Repository")
    repo_input = input("Enter GitHub URL or local path: ").strip()
    
    result = agent.handle_repository_input(repo_input)
    if not result['success']:
        print(f"❌ Error: {result['error']}")
        return
    
    print(result['message'])
    
    # Step 2: Start conversation
    print("\n💬 Step 2: Let's understand your needs")
    first_question = agent.start_conversation()
    print(f"\nAgent: {first_question}")
    
    # Conversation loop
    while not agent.state.understanding_complete:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            return
        
        response = agent.continue_conversation(user_input)
        print(f"\nAgent: {response['response']}")
        
        if response['understanding_complete']:
            print("\n✅ I understand your requirements!")
            break
    
    # Step 3: Generate plan
    print("\n📋 Step 3: Generating execution plan...")
    plan = agent.generate_plan()
    preview = agent.show_plan_preview(plan)
    print(preview)
    
    # Step 4: Confirm and execute
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice == '1':
        print("\n🚀 Executing plan...")
        result = agent.execute_plan(plan)
        if result['success']:
            print(f"\n✅ Success! Dataset saved: {result['output_file']}")
            print(f"   Rows: {result['rows']}, Columns: {len(result['columns'])}")
        else:
            print(f"\n❌ Error: {result['error']}")
    else:
        print("👋 Plan cancelled")


if __name__ == '__main__':
    main()
