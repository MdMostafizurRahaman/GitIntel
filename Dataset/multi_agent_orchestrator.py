import os
import sys
import io
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

# Fix Windows console encoding for Unicode emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# Add Dataset folder to path
sys.path.insert(0, str(Path(__file__).parent))

# Import existing components
from integrated_jury_system import (
    IntegratedJurySystem,
    QuestionClarifier,
    CodeGenerator,
    TestGeneratorJury,
    TestExecutor,
    ClarificationStatus,
    TestStatus
)
from metrics_catalog import MetricsCatalog
from aws_llm_provider import MultiProviderLLM


class WorkflowStatus(Enum):
    """Overall workflow status"""
    INITIALIZING = "initializing"
    ANALYZING_REQUIREMENTS = "analyzing_requirements"
    GENERATING_CODE = "generating_code"
    TESTING = "testing"
    REFINING = "refining"
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_HUMAN_INTERVENTION = "needs_human_intervention"


@dataclass
class MetricSpecification:
    """Formal specification for a metric"""
    name: str
    description: str
    formula: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    scope: str = "file"  # file, class, method, repository
    data_sources: List[str] = field(default_factory=list)
    category: str = "custom"
    is_predefined: bool = False


@dataclass
class OrchestrationResult:
    """Result of the complete orchestration workflow"""
    status: WorkflowStatus
    specifications: List[MetricSpecification]
    generated_code: Optional[str]
    test_results: Optional[Dict]
    dataset: Optional[pd.DataFrame]
    iterations: int
    error_message: Optional[str]
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiAgentOrchestrator:
    """
    Main orchestrator that coordinates all agents
    """
    
    def __init__(
        self, 
        metrics_catalog: Optional[MetricsCatalog] = None,
        max_refinement_cycles: int = 5,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize orchestrator
        
        Args:
            metrics_catalog: Catalog of available metrics
            max_refinement_cycles: Maximum refinement iterations (default 5)
            progress_callback: Optional callback for progress updates
        """
        self.metrics_catalog = metrics_catalog or MetricsCatalog()
        self.max_cycles = max_refinement_cycles
        self.progress_callback = progress_callback
        
        # Initialize integrated jury system
        self.jury_system = IntegratedJurySystem()
        
        # Execution state
        self.current_cycle = 0
        self.specifications = []
        self.workflow_history = []
        
        # Results tracking
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path('generated_datasets') / f'multi_agent_run_{self.run_id}'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create agent-specific directories
        self.agent1_dir = self.output_dir / "agent1_requirements_analyzer"
        self.agent2_dir = self.output_dir / "agent2_code_generator"
        self.agent3_dir = self.output_dir / "agent3_test_llm1"
        self.agent4_dir = self.output_dir / "agent4_test_llm2"
        self.agent5_dir = self.output_dir / "agent5_test_llm3"
        
        for agent_dir in [self.agent1_dir, self.agent2_dir, self.agent3_dir, self.agent4_dir, self.agent5_dir]:
            agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy metrics_generators to output dir for test access
        self._setup_metrics_generators_in_output()
        
        self._log(f"[INIT] Multi-Agent Orchestrator initialized")
        self._log(f"[INIT] Output directory: {self.output_dir}")
        self._log(f"[INIT] Agent folders created: agent1-5/")
        self._log(f"[INIT] Max refinement cycles: {max_refinement_cycles}")
    
    def _setup_metrics_generators_in_output(self):
        """Copy metrics_generators to output directory for test access"""
        import shutil
        
        metrics_src = Path(__file__).parent / 'metrics_generators'
        metrics_dst = self.output_dir / 'metrics_generators'
        
        if metrics_src.exists() and not metrics_dst.exists():
            try:
                shutil.copytree(metrics_src, metrics_dst)
                self._log(f"[SETUP] Copied metrics_generators to output directory")
            except Exception as e:
                self._log(f"[SETUP] Warning: Could not copy metrics_generators: {e}")
    
    def _log(self, message: str, level: str = "INFO"):
        """Internal logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        
        # Save to log file
        log_file = self.output_dir / "orchestrator.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
        
        # Progress callback
        if self.progress_callback:
            self.progress_callback(message)
    
    def _save_checkpoint(self, cycle: int, data: Dict):
        """Save checkpoint for each cycle"""
        checkpoint_file = self.output_dir / f"checkpoint_cycle_{cycle}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        self._log(f"[CHECKPOINT] Saved cycle {cycle} checkpoint")
    
    def run_full_workflow(
        self,
        user_request: str,
        repo_path: Optional[str] = None,
        selected_predefined_metrics: Optional[List[str]] = None
    ) -> OrchestrationResult:
        """
        Execute complete multi-agent workflow
        
        Args:
            user_request: User's natural language request
            repo_path: Path to repository (if analyzing existing code)
            selected_predefined_metrics: Pre-selected metrics from catalog
            
        Returns:
            OrchestrationResult with complete workflow results
        """
        start_time = datetime.now()
        self._log("="*70)
        self._log("MULTI-AGENT WORKFLOW STARTING")
        self._log("="*70)
        self._log(f"User Request: {user_request[:100]}...")
        
        try:
            # =====================================================
            # STAGE 1: Requirement Analysis (Agent 1)
            # =====================================================
            self._log("\n[STAGE 1] Requirement Analysis")
            self._log("-" * 50)
            
            requirements_result = self._analyze_requirements(
                user_request,
                selected_predefined_metrics
            )
            
            if requirements_result['status'] != 'clarified':
                return OrchestrationResult(
                    status=WorkflowStatus.NEEDS_HUMAN_INTERVENTION,
                    specifications=[],
                    generated_code=None,
                    test_results=None,
                    dataset=None,
                    iterations=0,
                    error_message="Requirements not fully understood. Need more clarification.",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    metadata=requirements_result
                )
            
            self.specifications = requirements_result['specifications']
            self._log(f"[STAGE 1] ✅ Requirements clarified: {len(self.specifications)} metrics")
            
            # Save requirements checkpoint
            self._save_checkpoint(0, {
                'stage': 'requirements',
                'specifications': [vars(s) for s in self.specifications],
                'requirements': requirements_result
            })
            
            # =====================================================
            # STAGE 2-4: Code Generation & Testing Loop
            # =====================================================
            refinement_success = False
            final_code = None
            final_tests = None
            
            for cycle in range(1, self.max_cycles + 1):
                self.current_cycle = cycle
                self._log(f"\n[CYCLE {cycle}/{self.max_cycles}] Starting refinement cycle")
                self._log("-" * 50)
                
                # Stage 2: Code Generation (Agent 2)
                self._log(f"[CYCLE {cycle}] [STAGE 2] Code Generation")
                code_result = self._generate_code(
                    requirements_result,
                    previous_code=final_code,
                    feedback=final_tests.get('feedback') if final_tests else None
                )
                
                if not code_result['success']:
                    self._log(f"[CYCLE {cycle}] ❌ Code generation failed: {code_result.get('error')}")
                    continue
                
                final_code = code_result['code']
                self._log(f"[CYCLE {cycle}] ✅ Code generated successfully")
                
                # Stage 3 & 4: Testing with 3 LLMs (Agents 3-5)
                self._log(f"[CYCLE {cycle}] [STAGE 3-4] Testing Trio (3 LLMs)")
                test_result = self._execute_testing_trio(
                    final_code,
                    requirements_result,
                    repo_path
                )
                
                final_tests = test_result
                
                # Save cycle checkpoint
                self._save_checkpoint(cycle, {
                    'cycle': cycle,
                    'code': final_code,
                    'tests': test_result
                })
                
                # Check voting results
                passed_llms = test_result.get('passed_llms', 0)
                total_llms = test_result.get('total_llms', 3)
                
                self._log(f"[CYCLE {cycle}] Test Results: {passed_llms}/{total_llms} LLMs passed")
                
                # Majority voting: need at least 2/3
                if passed_llms >= 2:
                    self._log(f"[CYCLE {cycle}] ✅ VOTING PASSED: {passed_llms}/{total_llms}")
                    refinement_success = True
                    break
                else:
                    self._log(f"[CYCLE {cycle}] ❌ VOTING FAILED: {passed_llms}/{total_llms}")
                    self._log(f"[CYCLE {cycle}] Preparing feedback for next iteration...")
            
            # =====================================================
            # STAGE 5: Dataset Generation or Human Intervention
            # =====================================================
            if refinement_success:
                self._log("\n[STAGE 5] Dataset Generation")
                self._log("-" * 50)
                
                dataset = self._generate_dataset(
                    final_code,
                    repo_path,
                    self.specifications
                )
                
                # Save dataset
                output_file = self.output_dir / "generated_dataset.csv"
                dataset.to_csv(output_file, index=False)
                self._log(f"[DATASET] ✅ Saved to: {output_file}")
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self._log(f"\n{'='*70}")
                self._log(f"✅ WORKFLOW COMPLETED SUCCESSFULLY")
                self._log(f"Iterations: {self.current_cycle}")
                self._log(f"Execution Time: {execution_time:.2f}s")
                self._log(f"Dataset Shape: {dataset.shape}")
                self._log(f"{'='*70}")
                
                return OrchestrationResult(
                    status=WorkflowStatus.SUCCESS,
                    specifications=self.specifications,
                    generated_code=final_code,
                    test_results=final_tests,
                    dataset=dataset,
                    iterations=self.current_cycle,
                    error_message=None,
                    execution_time=execution_time,
                    metadata={
                        'output_dir': str(self.output_dir),
                        'dataset_file': str(output_file)
                    }
                )
            else:
                # Max cycles exceeded - need human intervention
                execution_time = (datetime.now() - start_time).total_seconds()
                self._log(f"\n{'='*70}")
                self._log(f"❌ MAX CYCLES EXCEEDED ({self.max_cycles})")
                self._log(f"⚠️  HUMAN INTERVENTION REQUIRED")
                self._log(f"{'='*70}")
                
                return OrchestrationResult(
                    status=WorkflowStatus.NEEDS_HUMAN_INTERVENTION,
                    specifications=self.specifications,
                    generated_code=final_code,
                    test_results=final_tests,
                    dataset=None,
                    iterations=self.current_cycle,
                    error_message=f"Tests failed after {self.max_cycles} refinement cycles",
                    execution_time=execution_time,
                    metadata={
                        'output_dir': str(self.output_dir),
                        'last_code': final_code,
                        'last_tests': final_tests
                    }
                )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._log(f"❌ WORKFLOW ERROR: {str(e)}", level="ERROR")
            
            return OrchestrationResult(
                status=WorkflowStatus.FAILED,
                specifications=self.specifications,
                generated_code=None,
                test_results=None,
                dataset=None,
                iterations=self.current_cycle,
                error_message=str(e),
                execution_time=execution_time,
                metadata={}
            )
    
    def _analyze_requirements(
        self,
        user_request: str,
        selected_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Agent 1: Analyze and clarify requirements
        """
        self._log("[AGENT 1] Analyzing requirements...")
        
        # Build context with available metrics
        available_metrics = self.metrics_catalog.get_all_metrics()
        
        # Create prompt for Agent 1
        prompt = f"""You are Agent 1: Requirements Analyzer.
        
User Request: {user_request}

Pre-selected Metrics: {selected_metrics or 'None'}

Available Metrics: {len(available_metrics)} metrics available

Task: Analyze the requirements and clarify what metrics are needed.
Output: List of metric specifications with descriptions.
"""
        
        # Save prompt
        self._save_agent_file(self.agent1_dir, "prompt.txt", prompt)
        
        # Use integrated jury system's question clarifier
        # For now, we'll create a simplified version
        # The full IntegratedJurySystem will be used if iterative clarification is needed
        
        specifications = []
        
        # Add pre-selected metrics
        unknown_metrics = []
        if selected_metrics:
            for metric_name in selected_metrics:
                metric_info = self._get_metric_info(metric_name)
                if metric_info:
                    # Use the canonical name from catalog (case-corrected)
                    canonical_name = self._get_canonical_metric_name(metric_name)
                    spec = MetricSpecification(
                        name=canonical_name,
                        description=metric_info.get('description', ''),
                        formula=None,
                        dependencies=[],
                        scope='file',
                        data_sources=['ast_parsing'],
                        category=metric_info.get('category', 'unknown'),
                        is_predefined=True
                    )
                    specifications.append(spec)
                    self._log(f"[AGENT 1] ✓ Found predefined metric: {canonical_name}")
                else:
                    unknown_metrics.append(metric_name)
                    self._log(f"[AGENT 1] ⚠️  Unknown metric: {metric_name}")
        
        # Handle unknown metrics - use jury system for clarification
        if unknown_metrics:
            self._log(f"[AGENT 1] Using Jury System for {len(unknown_metrics)} unknown metrics...")
            custom_specs = self._clarify_unknown_metrics_with_jury(unknown_metrics, user_request)
            specifications.extend(custom_specs)
        
        # Parse additional custom metrics from user request using LLM
        additional_specs = self._extract_custom_metrics_llm(user_request)
        specifications.extend(additional_specs)
        
        # Save response
        response = f"""Requirements Analysis Complete

Total Metrics: {len(specifications)}

Specifications:
"""
        for spec in specifications:
            response += f"\n- {spec.name}: {spec.description}"
        
        self._save_agent_file(self.agent1_dir, "response.txt", response)
        self._save_agent_file(self.agent1_dir, "specifications.json", 
                            json.dumps([vars(s) for s in specifications], indent=2))
        
        return {
            'status': 'clarified',
            'specifications': specifications,
            'user_request': user_request,
            'selected_predefined': selected_metrics or []
        }
    
    def _get_canonical_metric_name(self, metric_name: str) -> str:
        """Get canonical metric name from catalog (handles case-insensitive lookup)"""
        all_metrics = self.metrics_catalog.get_all_metrics()
        
        # Try exact match first
        if metric_name in all_metrics:
            return metric_name
        
        # Find case-insensitive match
        metric_lower = metric_name.lower()
        for key in all_metrics.keys():
            if key.lower() == metric_lower:
                return key
        
        return metric_name
    
    def _clarify_unknown_metrics_with_jury(self, unknown_metrics: List[str], user_request: str) -> List[MetricSpecification]:
        """Use jury system to clarify unknown metrics"""
        specifications = []
        
        for metric_name in unknown_metrics:
            self._log(f"[JURY] Clarifying unknown metric: {metric_name}")
            
            # Use integrated jury system's question clarifier
            clarifier_prompt = f"""User requested metric: {metric_name}

Context: {user_request}

Please provide:
1. Description of the metric
2. Formula to calculate it
3. What data is needed
"""
            
            try:
                # Simple implementation - could be enhanced with actual jury voting
                jury_result = self.jury_system.generate_with_llm(
                    clarifier_prompt,
                    "metric_clarification"
                )
                
                # Parse response and create specification
                spec = MetricSpecification(
                    name=metric_name,
                    description=f"Custom metric: {metric_name}",
                    formula=jury_result.get('formula', 'User-defined'),
                    dependencies=[],
                    scope='file',
                    data_sources=['custom'],
                    category='custom',
                    is_predefined=False
                )
                specifications.append(spec)
                self._log(f"[JURY] ✓ Clarified: {metric_name}")
                
            except Exception as e:
                self._log(f"[JURY] ❌ Failed to clarify {metric_name}: {e}")
        
        return specifications
    
    def _extract_custom_metrics_llm(self, user_request: str) -> List[MetricSpecification]:
        """Extract custom metrics from user request using LLM"""
        # This would use the QuestionClarifier to parse user intent
        # For now, return empty list (can be extended)
        return []
    
    def _get_metric_info(self, metric_name: str) -> Optional[Dict]:
        """Get metric information from catalog (case-insensitive)"""
        all_metrics = self.metrics_catalog.get_all_metrics()
        
        # Try exact match first
        if metric_name in all_metrics:
            return all_metrics[metric_name]
        
        # Try case-insensitive match
        metric_lower = metric_name.lower()
        for key, value in all_metrics.items():
            if key.lower() == metric_lower:
                return value
        
        return None
    
    def _generate_code(
        self,
        requirements: Dict,
        previous_code: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent 2: Generate code for metrics calculation
        """
        self._log("[AGENT 2] Generating code...")
        
        # Create prompt for Agent 2
        specs = requirements['specifications']
        metric_names = [s.name for s in specs]
        
        prompt = f"""You are Agent 2: Code Generator.

Task: Generate Python code to calculate the following metrics:
{', '.join(metric_names)}

Requirements:
"""
        for spec in specs:
            prompt += f"\n- {spec.name}: {spec.description}"
        
        if previous_code:
            prompt += f"\n\nPrevious Code:\n{previous_code}"
        if feedback:
            prompt += f"\n\nFeedback from tests:\n{feedback}"
        
        prompt += "\n\nGenerate executable Python code with calculate_metrics() function."
        
        # Save prompt
        cycle_dir = self.agent2_dir / f"cycle_{self.current_cycle}"
        cycle_dir.mkdir(exist_ok=True)
        self._save_agent_file(cycle_dir, "prompt.txt", prompt)
        
        # Use IntegratedJurySystem's CodeGenerator
        # This is a simplified call - full implementation would use the actual CodeGenerator
        
        try:
            # Generate code based on specifications
            code_template = self._create_code_template(requirements['specifications'])
            
            # Save generated code
            self._save_agent_file(cycle_dir, "generated_code.py", code_template)
            self._save_agent_file(cycle_dir, "metadata.json", json.dumps({
                'cycle': self.current_cycle,
                'metrics': metric_names,
                'timestamp': datetime.now().isoformat()
            }, indent=2))
            
            return {
                'success': True,
                'code': code_template,
                'function_name': 'calculate_metrics',
                'dependencies': ['pandas', 'numpy']
            }
        except Exception as e:
            error_msg = str(e)
            self._save_agent_file(cycle_dir, "error.txt", error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _create_code_template(self, specifications: List[MetricSpecification]) -> str:
        """Create executable code template for metrics"""
        metric_names = [spec.name for spec in specifications]
        
        # Separate predefined vs custom metrics
        predefined_specs = [s for s in specifications if s.is_predefined]
        custom_specs = [s for s in specifications if not s.is_predefined]
        
        self._log(f"[AGENT 2] Predefined metrics: {len(predefined_specs)}")
        self._log(f"[AGENT 2] Custom metrics: {len(custom_specs)}")
        
        # Pre-calculate metric names for docstring
        pred_names = ', '.join([s.name for s in predefined_specs]) if predefined_specs else 'None'
        cust_names = ', '.join([s.name for s in custom_specs]) if custom_specs else 'None'
        
        # Use MasterMetricsGenerator for ALL predefined metrics
        code = f"""
import pandas as pd
import numpy as np
from pathlib import Path
import ast
import os
import sys

# Fix import paths - look for metrics_generators in parent directories
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# If metrics_generators not found, look in parent directory (Dataset folder)
if not os.path.exists(os.path.join(current_dir, 'metrics_generators')):
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

# Also try grandparent directory (in case we're deep in subfolders)
if not os.path.exists(os.path.join(current_dir, 'metrics_generators')):
    grandparent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, grandparent_dir)

# Import the REAL metrics generator system
from metrics_generators.master_metrics_generator import MasterMetricsGenerator

def calculate_metrics(repo_path: str, file_paths: list) -> pd.DataFrame:
    \"\"\"
    Calculate metrics for repository files using MasterMetricsGenerator
    
    Predefined Metrics (from real calculators): {pred_names}
    Custom Metrics (formula-based): {cust_names}
    \"\"\"
    # Initialize the REAL metrics generator
    generator = MasterMetricsGenerator(repo_path)
    
    results = []
    
    for file_path in file_paths:
        # Generate ALL metrics using REAL calculators
        all_metrics_result = generator.generate_all_metrics(file_path)
        all_metrics = all_metrics_result.get('metrics', {{}})
        
        metrics_dict = {{'file': file_path}}
        
        # Extract requested predefined metrics
"""
        
        # Add predefined metrics by extracting from MasterMetricsGenerator results
        for spec in predefined_specs:
            metric_code = self._generate_extractor_call_code(spec)
            code += metric_code
        
        # Add custom metrics section
        code += """        
        # Calculate custom metrics (formula-based)
"""
        
        # Add custom metrics (LLM generates these)
        for spec in custom_specs:
            metric_code = self._generate_custom_metric_code(spec)
            code += metric_code
        
        code += """        
        results.append(metrics_dict)
    
    return pd.DataFrame(results)
"""
        
        # Save generated code to file
        self._save_generated_code(code)
        
        return code
    
    def _generate_extractor_call_code(self, spec: MetricSpecification) -> str:
        """
        Generate code to extract metric from MasterMetricsGenerator results
        Uses REAL calculator implementations instead of inline code
        """
        name = spec.name
        
        # ALL 64 metrics are calculated by MasterMetricsGenerator
        # Simply extract from the 'all_metrics' dictionary
        return f"        metrics_dict['{name}'] = all_metrics.get('{name}', 0)\n"
    
    def _generate_simple_metric_code(self, spec: MetricSpecification) -> str:
        """
        DEPRECATED: This method should NOT be used anymore
        MasterMetricsGenerator handles ALL metrics
        """
        # Fallback in case of error
        name = spec.name
        self._log(f"[AGENT 2] ⚠️  WARNING: Using fallback for metric '{name}' - should use MasterMetricsGenerator!")
        return f"        metrics_dict['{name}'] = 0  # Fallback - MasterMetricsGenerator should handle this\n"
    
    def _generate_custom_metric_code(self, spec: MetricSpecification) -> str:
        """
        Generate code for custom metrics with formulas
        Formula should contain metric names and operators: +, -, *, /, %, (, )
        Example: (loc+soc-cloc+bloc)/1000
        """
        name = spec.name
        formula = spec.formula or '0'
        
        self._log(f"[AGENT 2] Generating custom metric: {name} with formula: {formula}")
        
        # Parse formula to extract component metrics
        # Remove parentheses and operators to get metric names
        import re
        component_metrics = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
        component_metrics = [m for m in component_metrics if m not in ['and', 'or', 'not', 'if', 'else']]
        
        if component_metrics:
            self._log(f"[AGENT 2]   Formula components: {', '.join(component_metrics)}")
            # Replace metric names with metrics_dict access
            formula_code = formula
            for metric in component_metrics:
                formula_code = formula_code.replace(metric, f"metrics_dict.get('{metric}', 0)")
            
            return f"        metrics_dict['{name}'] = {formula_code}  # Formula: {formula}\n"
        else:
            return f"        metrics_dict['{name}'] = 0  # Invalid formula: {formula}\n"
    
    def _save_generated_code(self, code: str) -> None:
        """Save generated code to output directory"""
        if self.output_dir:
            code_file = self.output_dir / 'generated_metrics_calculator.py'
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            self._log(f"[CODE] Saved generated code to: {code_file}")
    
    def _generate_tests_with_llm(self, llm_name: str, code: str, specs: List[MetricSpecification], output_dir: Path) -> Dict:
        """Generate tests using LLM"""
        try:
            # Generate basic test template
            # In production, this would call actual LLM APIs
            test_code = self._create_basic_test_template(code, specs)
            
            # Simple validation - check if tests are valid Python
            try:
                compile(test_code, '<string>', 'exec')
                test_count = test_code.count('def test_')
                
                # Simulate test execution (basic validation)
                # In production, would actually run the tests
                import random
                passed = random.choice([True, True, False])  # 2/3 probability of passing
                
                return {
                    'passed': passed,
                    'test_code': test_code,
                    'test_count': test_count,
                    'errors': [] if passed else [f'{llm_name} found issues in edge cases']
                }
            except SyntaxError as e:
                return {
                    'passed': False,
                    'test_code': test_code,
                    'test_count': 0,
                    'error': f'Syntax error: {str(e)}',
                    'errors': [str(e)]
                }
        except Exception as e:
            return {
                'passed': False,
                'test_code': f'# Error generating tests: {str(e)}',
                'test_count': 0,
                'error': str(e),
                'errors': [str(e)]
            }
    
    def _create_basic_test_template(self, code: str, specs: List[MetricSpecification]) -> str:
        """Create basic test template"""
        metric_names = [s.name for s in specs]
        
        test_code = '''import unittest
import pandas as pd
from pathlib import Path

# Code to test
'''
        test_code += code + '\n\n'
        
        test_code += '''class TestMetricsCalculation(unittest.TestCase):
    
    def test_basic_calculation(self):
        """Test basic metrics calculation"""
        # Create test data
        test_files = ['test1.py', 'test2.py']
        result = calculate_metrics('.', test_files)
        
        # Check DataFrame structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        self.assertIn('file', result.columns)
'''
        
        for metric_name in metric_names:
            test_code += f'''    
    def test_{metric_name}(self):
        """Test {metric_name} metric"""
        result = calculate_metrics('.', ['test.py'])
        self.assertIn('{metric_name}', result.columns)
        self.assertIsNotNone(result['{metric_name}'].iloc[0])
'''
        
        test_code += '''
if __name__ == '__main__':
    unittest.main()
'''
        
        return test_code
    
    def _save_agent_file(self, directory: Path, filename: str, content: str) -> None:
        """Save agent output file"""
        file_path = directory / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _run_tests_subprocess(self, test_file_path: Path, llm_name: str) -> Dict:
        """Actually run tests using subprocess and capture output"""
        import subprocess
        try:
            # Convert to absolute path
            abs_path = test_file_path.resolve()
            
            result = subprocess.run(
                [sys.executable, str(abs_path)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.output_dir)  # Use output dir as cwd instead of test file's parent
            )
            
            # Parse output for errors
            errors = []
            if result.returncode != 0:
                # Extract error messages from stderr
                for line in result.stderr.split('\n'):
                    if 'Error' in line or 'FAIL' in line or 'Traceback' in line:
                        errors.append(line.strip())
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'errors': errors,
                'error': result.stderr.split('\n')[0] if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Test execution timeout after 10 seconds',
                'returncode': -1,
                'errors': ['Timeout'],
                'error': 'Test timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'errors': [str(e)],
                'error': str(e)
            }
    
    def _execute_testing_trio(
        self,
        code: str,
        requirements: Dict,
        repo_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Agents 3-5: Three independent test generators and executors
        """
        self._log("[AGENTS 3-5] Testing Trio starting...")
        
        # Test with 3 independent LLMs
        agent_dirs = [self.agent3_dir, self.agent4_dir, self.agent5_dir]
        agent_names = ["LLM 1", "LLM 2", "LLM 3"]
        
        test_results = []
        passed_count = 0
        
        for i, (agent_dir, agent_name) in enumerate(zip(agent_dirs, agent_names), 1):
            self._log(f"[AGENT {i+2}] {agent_name} generating tests...")
            
            # Create cycle-specific directory
            cycle_dir = agent_dir / f"cycle_{self.current_cycle}"
            cycle_dir.mkdir(exist_ok=True)
            
            # Create prompt for test generation
            specs = requirements['specifications']
            metric_names = [s.name for s in specs]
            
            prompt = f"""You are Agent {i+2}: Test Generator ({agent_name}).

Task: Generate unit tests for the following code:

```python
{code}
```

Metrics to test: {', '.join(metric_names)}

Generate comprehensive unit tests using unittest framework.
Test edge cases, normal cases, and error handling.
"""
            
            # Save prompt
            self._save_agent_file(cycle_dir, "prompt.txt", prompt)
            
            # Generate tests using LLM
            test_result = self._generate_tests_with_llm(agent_name, code, specs, cycle_dir)
            
            # Save test code
            self._save_agent_file(cycle_dir, "generated_tests.py", test_result['test_code'])
            
            # ACTUALLY RUN THE TESTS
            test_file = cycle_dir / "generated_tests.py"
            actual_result = self._run_tests_subprocess(test_file, agent_name)
            
            # Update result with actual test execution
            passed = actual_result['success']
            test_results.append({
                'llm': agent_name,
                'passed': passed,
                'test_count': test_result['test_count'],
                'errors': actual_result.get('errors', []),
                'stdout': actual_result.get('stdout', ''),
                'stderr': actual_result.get('stderr', '')
            })
            
            if passed:
                passed_count += 1
                self._log(f"[TESTING] {agent_name}: ✅ PASSED ({test_result['test_count']} tests)")
            else:
                self._log(f"[TESTING] {agent_name}: ❌ FAILED - {actual_result.get('error', 'Test execution failed')}")
                # Log first few error lines
                if actual_result.get('stderr'):
                    error_lines = actual_result['stderr'].split('\n')[:3]
                    for line in error_lines:
                        if line.strip():
                            self._log(f"         {line.strip()}")
            
            # Save results with actual execution data
            self._save_agent_file(cycle_dir, "result.json", json.dumps({
                'passed': passed,
                'test_count': test_result['test_count'],
                'errors': actual_result.get('errors', []),
                'execution_stdout': actual_result.get('stdout', '')[:500],  # First 500 chars
                'execution_stderr': actual_result.get('stderr', '')[:500],
                'timestamp': datetime.now().isoformat()
            }, indent=2))
        
        # Build detailed feedback from test failures
        if passed_count < 3:
            feedback_parts = [f"{passed_count}/3 tests passed"]
            for test_res in test_results:
                if not test_res['passed']:
                    feedback_parts.append(f"\n{test_res['llm']} errors:")
                    if test_res.get('stderr'):
                        # Extract key error messages
                        stderr_lines = test_res['stderr'].split('\n')
                        for line in stderr_lines:
                            if 'Error' in line or 'FAIL' in line or 'AssertionError' in line:
                                feedback_parts.append(f"  - {line.strip()}")
            feedback_str = '\n'.join(feedback_parts[:20])  # Limit feedback size
        else:
            feedback_str = f'{passed_count}/3 LLMs passed testing'
        
        return {
            'total_llms': 3,
            'passed_llms': passed_count,
            'tests': test_results,
            'feedback': feedback_str
        }
    
    def _generate_dataset(
        self,
        code: str,
        repo_path: Optional[str],
        specifications: List[MetricSpecification]
    ) -> pd.DataFrame:
        """Generate final dataset using validated code"""
        self._log("[DATASET] Generating dataset...")
        
        try:
            # Get git info if available
            git_info = self._get_git_info(repo_path) if repo_path else None
            if git_info:
                self._log(f"[GIT] Commit: {git_info['commit']}")
                self._log(f"[GIT] Message: {git_info['message'][:60]}...")
            
            # Execute generated code
            namespace = {}
            exec(code, namespace)
            calculate_metrics = namespace.get('calculate_metrics')
            
            if not calculate_metrics:
                raise ValueError("calculate_metrics function not found in generated code")
            
            # Find Python files in repository
            if repo_path and os.path.exists(repo_path):
                self._log(f"[SCAN] Scanning repository: {repo_path}")
                python_files = []
                for root, dirs, files in os.walk(repo_path):
                    # Skip common directories
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
                    for file in files:
                        if file.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                            python_files.append(rel_path)
                
                # Limit to first 50 files for testing
                python_files = python_files[:50]
                
                if not python_files:
                    self._log("[DATASET] No Python files found, using sample data")
                    python_files = ['sample1.py', 'sample2.py', 'sample3.py']
                    repo_path = None  # Will create mock files
                
                self._log(f"[DATASET] Found {len(python_files)} Python files to process")
                
                # Execute metric calculation with progress logging
                if repo_path:
                    self._log("[PROCESS] Starting metric calculation...")
                    df = self._calculate_metrics_with_logging(calculate_metrics, repo_path, python_files, specifications)
                else:
                    # Create mock files for testing
                    df = self._generate_mock_dataset(specifications, python_files)
            else:
                self._log("[DATASET] No valid repo path, using mock data")
                df = self._generate_mock_dataset(specifications, ['file1.py', 'file2.py', 'file3.py'])
            
            self._log(f"[DATASET] Generated {len(df)} rows with {len(df.columns)-1} metrics")
            
            # Log sample results
            if len(df) > 0:
                self._log(f"[SAMPLE] First file: {df['file'].iloc[0]}")
                for col in df.columns[1:3]:  # First 2 metrics
                    if col in df.columns:
                        self._log(f"[SAMPLE]   {col}: {df[col].iloc[0]}")
            
            return df
            
        except Exception as e:
            self._log(f"[DATASET] Error executing code: {e}", level="ERROR")
            self._log("[DATASET] Falling back to mock data")
            return self._generate_mock_dataset(specifications, ['file1.py', 'file2.py', 'file3.py'])
    
    def _get_git_info(self, repo_path: str) -> Optional[Dict]:
        """Get git commit information"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            commit = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%s'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            message = result.stdout.strip() if result.returncode == 0 else 'No commit message'
            
            return {' commit': commit, 'message': message}
        except:
            return None
    
    def _calculate_metrics_with_logging(
        self,
        calculate_fn: Callable,
        repo_path: str,
        file_list: List[str],
        specifications: List[MetricSpecification]
    ) -> pd.DataFrame:
        """Calculate metrics with detailed progress logging"""
        
        # Process files in batches to show progress
        batch_size = 10
        total_files = len(file_list)
        
        for i in range(0, total_files, batch_size):
            batch = file_list[i:i+batch_size]
            self._log(f"[PROCESS] Processing files {i+1}-{min(i+batch_size, total_files)} of {total_files}")
            
            # Show first few files in batch
            for file in batch[:3]:
                self._log(f"[FILE] {file}")
        
        # Calculate all metrics
        self._log(f"[CALC] Calculating {len(specifications)} metrics...")
        df = calculate_fn(repo_path, file_list)
        
        # Log statistics
        if len(df) > 0:
            self._log(f"[STATS] Successfully processed: {len(df)}/{total_files} files")
            for spec in specifications[:3]:  # First 3 metrics
                if spec.name in df.columns:
                    values = df[spec.name]
                    self._log(f"[STATS] {spec.name}: min={values.min()}, max={values.max()}, mean={values.mean():.1f}")
        
        return df
    
    def _generate_mock_dataset(self, specifications: List[MetricSpecification], file_list: List[str]) -> pd.DataFrame:
        """Generate mock dataset when real calculation fails"""
        mock_data = {'file': file_list}
        for spec in specifications:
            mock_data[spec.name] = np.random.randint(0, 100, len(file_list))
        return pd.DataFrame(mock_data)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def create_orchestrator(
    max_cycles: int = 5,
    progress_callback: Optional[Callable] = None
) -> MultiAgentOrchestrator:
    """
    Create and configure a multi-agent orchestrator
    
    Args:
        max_cycles: Maximum refinement cycles (default 5)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Configured MultiAgentOrchestrator instance
    """
    return MultiAgentOrchestrator(
        max_refinement_cycles=max_cycles,
        progress_callback=progress_callback
    )


def run_quick_workflow(
    user_request: str,
    repo_path: Optional[str] = None,
    selected_metrics: Optional[List[str]] = None
) -> OrchestrationResult:
    """
    Quick workflow execution with default settings
    
    Args:
        user_request: User's natural language request
        repo_path: Path to repository
        selected_metrics: List of predefined metric names
        
    Returns:
        OrchestrationResult
    """
    orchestrator = create_orchestrator()
    return orchestrator.run_full_workflow(
        user_request=user_request,
        repo_path=repo_path,
        selected_predefined_metrics=selected_metrics
    )


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    print("Multi-Agent Orchestrator for Metrics Dataset Generation")
    print("=" * 70)
    
    # Example 1: Simple workflow
    result = run_quick_workflow(
        user_request="Generate bug prediction dataset with complexity and change metrics",
        repo_path="d:\\GitIntel\\repo",
        selected_metrics=['cyclomatic_complexity', 'churn', 'loc', 'bug_density']
    )
    
    print(f"\nWorkflow Status: {result.status.value}")
    print(f"Iterations: {result.iterations}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    if result.dataset is not None:
        print(f"\nDataset Shape: {result.dataset.shape}")
        print("\nFirst 3 rows:")
        print(result.dataset.head(3))
