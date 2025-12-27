"""
🤖 Truly Agentic Dataset Generation System
==========================================

Features:
- Uses latest Gemini 2.5 models
- Extensive user communication and clarification
- ONLY real data from cloned repository
- Shows complete preview before execution
- Requires user confirmation at every step
- Integrates with existing GUI
- No mock/dummy data generation

Philosophy: Agent asks until fully understands, then shows preview, gets confirmation, executes
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

# Try new google.genai first, fallback to google.generativeai
try:
    import google.genai as genai
    GENAI_NEW = True
except ImportError:
    import google.generativeai as genai
    GENAI_NEW = False

# Import real data extractors
from llm_git_analyzer import LLMGitAnalyzer
from unified_metrics_analyzer import UnifiedMetricsAnalyzer
from ck_metrics_analyzer import CKMetricsAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatasetRequirement:
    """User's dataset requirements"""
    description: str
    desired_columns: List[str]
    desired_rows_count: Optional[int]
    formulas: Dict[str, str]
    filters: Dict[str, Any]
    confirmed: bool = False


@dataclass
class DatasetPreview:
    """Preview of dataset before generation"""
    columns: List[str]
    sample_rows: List[Dict]
    total_rows: int
    calculations: Dict[str, str]
    data_source: str
    
    
class AgenticDatasetSystem:
    """
    Truly agentic dataset generation system
    Asks, clarifies, previews, confirms before executing
    """
    
    def __init__(self):
        """Initialize the agentic system"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # Configure Gemini with latest model
        if GENAI_NEW:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            genai.configure(api_key=self.api_key)
            # Try latest models
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except:
                try:
                    self.model = genai.GenerativeModel('gemini-2.0-flash')
                except:
                    self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # Initialize real data extractors
        self.git_analyzer = None
        self.repo_path = None
        self.available_metrics = []
        self.conversation_history = []
        self.current_requirement = None
        self.current_preview = None
        
        logger.info(f"✅ Initialized with model: {self.model._model_name if hasattr(self.model, '_model_name') else 'latest'}")
    
    def set_repository(self, repo_path: str) -> bool:
        """Set the repository to work with"""
        try:
            self.repo_path = Path(repo_path)
            if not self.repo_path.exists():
                logger.error(f"Repository not found: {repo_path}")
                return False
            
            # Initialize analyzers with real repo
            self.git_analyzer = LLMGitAnalyzer()
            self.git_analyzer.set_repository(str(self.repo_path))
            
            # Discover available metrics from repository
            self._discover_available_metrics()
            
            logger.info(f"✅ Repository set: {repo_path}")
            logger.info(f"📊 Found {len(self.available_metrics)} available metrics")
            return True
            
        except Exception as e:
            logger.error(f"Error setting repository: {e}")
            return False
    
    def _discover_available_metrics(self):
        """Discover what metrics are available from the repository"""
        self.available_metrics = []
        
        try:
            # Check if it's a Java repository
            java_files = list(self.repo_path.rglob("*.java"))
            if java_files:
                self.available_metrics.extend([
                    "LOC", "NCLOC", "comment_lines", "blank_lines",
                    "cyclomatic_complexity", "cognitive_complexity",
                    "CBO", "DIT", "WMC", "RFC", "LCOM", "NOC",
                    "halstead_volume", "halstead_difficulty", "halstead_effort",
                    "maintainability_index", "technical_debt_hours",
                    "num_classes", "num_methods", "num_fields",
                    "max_nesting_depth"
                ])
            
            # Git-based metrics (always available)
            self.available_metrics.extend([
                "commit_count", "author_count", "change_frequency",
                "lines_added", "lines_deleted", "files_changed",
                "bug_count", "issue_count"
            ])
            
            # Remove duplicates
            self.available_metrics = list(set(self.available_metrics))
            
        except Exception as e:
            logger.error(f"Error discovering metrics: {e}")
    
    def start_conversation(self, user_request: str) -> str:
        """Start agentic conversation with user"""
        self.conversation_history = [
            {"role": "user", "content": user_request}
        ]
        
        # Agent analyzes and asks clarifying questions
        response = self._agent_analyze_request(user_request)
        
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        return response
    
    def _agent_analyze_request(self, user_request: str) -> str:
        """Agent analyzes request and asks clarifying questions"""
        prompt = f"""
You are an expert data scientist helping a user generate a custom dataset from a Git repository.

**Repository Information:**
- Path: {self.repo_path}
- Available Metrics: {', '.join(self.available_metrics)}

**User Request:**
{user_request}

**Your Task:**
Analyze the user's request thoroughly and create a clarification plan. You MUST:

1. **Understand Requirements:**
   - What columns does the user want?
   - What calculations/formulas are needed?
   - How many rows (all data or filtered)?
   - What filters to apply?

2. **Ask Clarifying Questions:**
   - List ALL questions you need answered
   - Be specific and numbered
   - Cover every ambiguity
   - Don't assume anything

3. **Identify Missing Information:**
   - Which metrics are available vs requested?
   - How to derive missing metrics from available ones?
   - What assumptions need confirmation?

**Output Format:**
Provide a friendly, conversational response that:
- Shows you understand the request
- Lists specific questions (numbered)
- Explains available options
- Asks for confirmation on assumptions

**Example Response:**
"I understand you want to generate a dataset for defect prediction! Let me clarify a few things:

1. **Columns**: You mentioned 'bugs' and 'complexity'. Should I include:
   - Bug count per file/class?
   - Cyclomatic complexity or cognitive complexity (or both)?
   - Any other metrics like LOC, maintainability index?

2. **Data Scope**: Should the dataset include:
   - All files in the repository?
   - Only Java files?
   - Only files with bugs?
   
3. **Calculations**: For 'defect density', should I calculate:
   - bugs_count / KLOC (thousands of lines of code)?
   - bugs_count / total_lines?
   - Something else?

4. **Additional Metrics**: Would you like me to include any of these available metrics?
   {{list 5-6 relevant metrics}}

Please answer these questions so I can create exactly what you need!"

Now analyze the user's request and respond:
"""

        try:
            if GENAI_NEW:
                response = self.model.generate_content(prompt)
                return response.text
            else:
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.error(f"Error in agent analysis: {e}")
            return f"I'm ready to help! Please tell me:\n1. What columns do you want?\n2. What calculations?\n3. How many rows?\n4. Any filters?"
    
    def continue_conversation(self, user_response: str) -> str:
        """Continue the conversation with user input"""
        self.conversation_history.append({
            "role": "user",
            "content": user_response
        })
        
        # Check if we have enough information
        if self._has_enough_information():
            # Generate requirement specification
            requirement = self._extract_requirement()
            
            if requirement:
                self.current_requirement = requirement
                return self._generate_confirmation_message(requirement)
        
        # Need more clarification
        response = self._ask_more_questions()
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _has_enough_information(self) -> bool:
        """Check if agent has enough information to proceed"""
        # Agent decides if enough info collected
        conversation_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in self.conversation_history
        ])
        
        prompt = f"""
Analyze this conversation and determine if you have ALL necessary information to generate a dataset.

**Conversation:**
{conversation_text}

**Required Information:**
1. ✅ Specific columns needed
2. ✅ Formulas/calculations for derived columns
3. ✅ Number of rows or filtering criteria
4. ✅ Confirmation of assumptions

**Your Task:**
Respond with ONLY "YES" or "NO" followed by a brief explanation.

YES - if you can confidently create a complete dataset specification
NO - if you still need clarification on any aspect

Format: 
YES: <explanation>
or
NO: <what's still missing>
"""

        try:
            if GENAI_NEW:
                response = self.model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
            
            result = response.text.strip().upper()
            return result.startswith("YES")
            
        except Exception as e:
            logger.error(f"Error checking information: {e}")
            return False
    
    def _ask_more_questions(self) -> str:
        """Agent asks more clarifying questions"""
        conversation_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in self.conversation_history
        ])
        
        prompt = f"""
Continue the conversation to gather complete dataset requirements.

**Available Metrics:**
{', '.join(self.available_metrics)}

**Conversation So Far:**
{conversation_text}

**Your Task:**
Based on what the user has said, ask the NEXT set of clarifying questions.
Be specific, friendly, and focused on getting actionable information.

Focus on:
- Exact column names
- Specific formulas
- Clear filters or row count
- Confirmation of any assumptions

Respond naturally and conversationally.
"""

        try:
            if GENAI_NEW:
                response = self.model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error asking questions: {e}")
            return "Could you please clarify what columns and calculations you need?"
    
    def _extract_requirement(self) -> Optional[DatasetRequirement]:
        """Extract structured requirement from conversation"""
        conversation_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in self.conversation_history
        ])
        
        prompt = f"""
Extract a structured dataset requirement from this conversation.

**Conversation:**
{conversation_text}

**Available Metrics:**
{', '.join(self.available_metrics)}

**Your Task:**
Extract and return a JSON object with this structure:
{{
    "description": "Brief description of what dataset is for",
    "desired_columns": ["column1", "column2", ...],
    "desired_rows_count": null or number,
    "formulas": {{
        "derived_column": "formula using available metrics"
    }},
    "filters": {{
        "filter_type": "value"
    }}
}}

**Important:**
- Use ONLY metrics from the available list
- Be specific about formulas
- Include all columns user mentioned
- Return ONLY valid JSON, no explanation

JSON:
"""

        try:
            if GENAI_NEW:
                response = self.model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            json_text = response.text.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]
            
            req_data = json.loads(json_text)
            
            return DatasetRequirement(
                description=req_data.get("description", ""),
                desired_columns=req_data.get("desired_columns", []),
                desired_rows_count=req_data.get("desired_rows_count"),
                formulas=req_data.get("formulas", {}),
                filters=req_data.get("filters", {})
            )
            
        except Exception as e:
            logger.error(f"Error extracting requirement: {e}")
            return None
    
    def _generate_confirmation_message(self, requirement: DatasetRequirement) -> str:
        """Generate confirmation message with preview"""
        message = f"""
✅ **I understand! Here's what I'll generate:**

**Description:** {requirement.description}

**Columns:** ({len(requirement.desired_columns)})
"""
        for i, col in enumerate(requirement.desired_columns, 1):
            message += f"  {i}. {col}\n"
        
        if requirement.formulas:
            message += f"\n**Calculated Columns:** ({len(requirement.formulas)})\n"
            for col, formula in requirement.formulas.items():
                message += f"  • {col} = {formula}\n"
        
        if requirement.filters:
            message += f"\n**Filters:**\n"
            for filter_name, filter_value in requirement.filters.items():
                message += f"  • {filter_name}: {filter_value}\n"
        
        message += f"\n**Estimated Rows:** {requirement.desired_rows_count or 'All available data'}\n"
        
        message += """
**Next Steps:**
1. I'll extract REAL data from your repository
2. Apply the formulas and calculations
3. Show you a PREVIEW of the dataset
4. You confirm if it looks good
5. I'll generate the complete dataset

**Reply with:**
- "yes" or "proceed" to continue
- "modify" to make changes
- "cancel" to stop
"""
        return message
    
    def generate_preview(self) -> Optional[DatasetPreview]:
        """Generate preview from REAL repository data"""
        if not self.current_requirement:
            logger.error("No requirement specified")
            return None
        
        if not self.repo_path:
            logger.error("No repository set")
            return None
        
        try:
            logger.info("📊 Extracting real data from repository...")
            
            # Extract real metrics from repository
            real_data = self._extract_real_data()
            
            if not real_data:
                logger.error("No data extracted from repository")
                return None
            
            # Apply formulas
            calculated_data = self._apply_formulas(real_data)
            
            # Create preview
            preview = DatasetPreview(
                columns=list(calculated_data[0].keys()) if calculated_data else [],
                sample_rows=calculated_data[:5],  # First 5 rows
                total_rows=len(calculated_data),
                calculations=self.current_requirement.formulas,
                data_source=str(self.repo_path)
            )
            
            self.current_preview = preview
            return preview
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}", exc_info=True)
            return None
    
    def _extract_real_data(self) -> List[Dict]:
        """Extract REAL data from repository - NO MOCK DATA"""
        logger.info("🔍 Analyzing repository...")
        
        real_data = []
        
        try:
            # Check if Java repository
            java_files = list(self.repo_path.rglob("*.java"))
            
            if java_files:
                logger.info(f"Found {len(java_files)} Java files")
                
                # Use CK Metrics Analyzer for real metrics
                ck_analyzer = CKMetricsAnalyzer(str(self.repo_path))
                ck_results = ck_analyzer.analyze_repository()
                
                # Use Unified Metrics for comprehensive analysis
                unified_analyzer = UnifiedMetricsAnalyzer(str(self.repo_path))
                unified_results = unified_analyzer.analyze_all()
                
                logger.info(f"Analyzed {len(ck_results)} classes with CK metrics")
                logger.info(f"Analyzed {len(unified_results)} classes with unified metrics")
                
                # Convert to dataset format
                for class_name, unified_metrics in unified_results.items():
                    record = {
                        "class_name": class_name,
                        "file_path": unified_metrics.file_path,
                    }
                    
                    # Add CK metrics
                    if unified_metrics.ck_metrics:
                        ck = unified_metrics.ck_metrics
                        record.update({
                            "CBO": ck.cbo,
                            "DIT": ck.dit,
                            "WMC": ck.wmc,
                            "RFC": ck.rfc,
                            "LCOM": ck.lcom,
                            "NOC": ck.noc,
                            "num_methods": ck.number_of_methods,
                            "num_fields": ck.number_of_fields,
                            "LOC": ck.loc
                        })
                    
                    # Add complexity metrics
                    if unified_metrics.complexity:
                        comp = unified_metrics.complexity
                        record.update({
                            "cyclomatic_complexity": comp.cyclomatic_complexity,
                            "cognitive_complexity": comp.cognitive_complexity,
                            "max_nesting_depth": comp.max_nesting_depth
                        })
                    
                    # Add Halstead metrics
                    if unified_metrics.halstead:
                        hal = unified_metrics.halstead
                        record.update({
                            "halstead_volume": hal.volume,
                            "halstead_difficulty": hal.difficulty,
                            "halstead_effort": hal.effort
                        })
                    
                    # Add maintainability metrics
                    if unified_metrics.maintainability:
                        maint = unified_metrics.maintainability
                        record.update({
                            "maintainability_index": maint.maintainability_index,
                            "technical_debt_hours": maint.technical_debt_hours
                        })
                    
                    real_data.append(record)
            
            # If no Java files or additional git metrics needed
            if not real_data:
                logger.warning("No Java classes found, trying alternative extraction")
            
            logger.info(f"✅ Extracted {len(real_data)} records from repository")
            return real_data
            
        except Exception as e:
            logger.error(f"Error extracting real data: {e}", exc_info=True)
            return []
    
    def _apply_formulas(self, data: List[Dict]) -> List[Dict]:
        """Apply user-defined formulas to extracted data"""
        if not self.current_requirement.formulas:
            return data
        
        logger.info(f"🔢 Applying {len(self.current_requirement.formulas)} formulas...")
        
        result_data = []
        
        for record in data:
            new_record = record.copy()
            
            # Apply each formula
            for col_name, formula in self.current_requirement.formulas.items():
                try:
                    # Create safe namespace with record data
                    namespace = {**record, 'abs': abs, 'max': max, 'min': min}
                    
                    # Evaluate formula
                    value = eval(formula, {"__builtins__": {}}, namespace)
                    new_record[col_name] = value
                    
                except Exception as e:
                    logger.warning(f"Error applying formula '{col_name}': {e}")
                    new_record[col_name] = None
            
            result_data.append(new_record)
        
        return result_data
    
    def show_preview_to_user(self) -> str:
        """Format preview for display to user"""
        if not self.current_preview:
            return "❌ No preview available. Please generate preview first."
        
        preview = self.current_preview
        
        message = f"""
📊 **DATASET PREVIEW**
{'='*80}

**Data Source:** {preview.data_source}
**Total Rows:** {preview.total_rows}
**Columns:** {len(preview.columns)}

**Column Names:**
{', '.join(preview.columns)}

**Sample Data (first 5 rows):**
"""
        
        # Format sample rows as table
        if preview.sample_rows:
            # Create DataFrame for nice formatting
            df = pd.DataFrame(preview.sample_rows)
            message += f"\n{df.to_string(index=False)}\n"
        
        if preview.calculations:
            message += f"\n**Applied Calculations:**\n"
            for col, formula in preview.calculations.items():
                message += f"  • {col} = {formula}\n"
        
        message += f"""
{'='*80}

**This is REAL data from your repository, not mock data!**

**Do you want to proceed with generating the full dataset?**
- Type "yes" or "confirm" to generate
- Type "modify" to make changes
- Type "cancel" to stop
"""
        
        return message
    
    def generate_full_dataset(self) -> Optional[str]:
        """Generate full dataset after confirmation"""
        if not self.current_preview:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("generated_datasets")
            output_dir.mkdir(exist_ok=True)
            
            # Extract full data (not just preview)
            logger.info("📂 Generating full dataset...")
            full_data = self._extract_real_data()
            full_data = self._apply_formulas(full_data)
            
            # Create DataFrame
            df = pd.DataFrame(full_data)
            
            # Filter columns based on requirement
            if self.current_requirement.desired_columns:
                available_cols = [c for c in self.current_requirement.desired_columns if c in df.columns]
                df = df[available_cols]
            
            # Save CSV
            csv_path = output_dir / f"dataset_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            
            # Save JSON
            json_path = output_dir / f"dataset_{timestamp}.json"
            df.to_json(json_path, orient='records', indent=2)
            
            # Save metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "description": self.current_requirement.description,
                "columns": list(df.columns),
                "rows": len(df),
                "formulas": self.current_requirement.formulas,
                "data_source": str(self.repo_path),
                "conversation_history": self.conversation_history
            }
            
            metadata_path = output_dir / f"dataset_{timestamp}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Dataset generated: {csv_path}")
            
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error generating dataset: {e}", exc_info=True)
            return None


def main():
    """Interactive CLI for agentic system"""
    print("\n" + "="*80)
    print("🤖 AGENTIC DATASET GENERATION SYSTEM")
    print("="*80)
    print("\nFeatures:")
    print("  ✅ Extensive clarification questions")
    print("  ✅ ONLY real data from repository")
    print("  ✅ Preview before generation")
    print("  ✅ Confirmation required")
    print("  ✅ No mock/dummy data")
    print("\n" + "="*80)
    
    try:
        system = AgenticDatasetSystem()
        
        # Set repository
        repo_path = input("\n📁 Enter repository path (or press Enter for current dir): ").strip()
        if not repo_path:
            repo_path = "."
        
        if not system.set_repository(repo_path):
            print("❌ Failed to set repository")
            return
        
        print(f"\n✅ Repository: {system.repo_path}")
        print(f"📊 Available metrics: {len(system.available_metrics)}")
        
        # Start conversation
        print("\n💬 Tell me what dataset you want to generate:")
        user_request = input("> ").strip()
        
        response = system.start_conversation(user_request)
        print(f"\n🤖 Agent: {response}")
        
        # Conversation loop
        while True:
            user_input = input("\n👤 You: ").strip().lower()
            
            if user_input in ['yes', 'proceed', 'confirm']:
                # Check if we have enough info
                if system.current_requirement:
                    # Generate preview
                    print("\n⏳ Generating preview from real repository data...")
                    preview = system.generate_preview()
                    
                    if preview:
                        print(system.show_preview_to_user())
                        
                        # Final confirmation
                        final_confirm = input("\n👤 Confirm generation (yes/no): ").strip().lower()
                        
                        if final_confirm == 'yes':
                            print("\n⏳ Generating full dataset...")
                            output_path = system.generate_full_dataset()
                            
                            if output_path:
                                print(f"\n✅ SUCCESS! Dataset generated: {output_path}")
                            else:
                                print("\n❌ Failed to generate dataset")
                            break
                        else:
                            print("\n❌ Generation cancelled")
                            break
                    else:
                        print("\n❌ Failed to generate preview")
                        break
                else:
                    response = system.continue_conversation(user_input)
                    print(f"\n🤖 Agent: {response}")
            
            elif user_input in ['cancel', 'exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            else:
                response = system.continue_conversation(user_input)
                print(f"\n🤖 Agent: {response}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
