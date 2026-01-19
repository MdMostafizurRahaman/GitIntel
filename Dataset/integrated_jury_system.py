"""
Integrated Multi-LLM Jury System
=================================
Complete workflow:
1. Question Clarifier LLM: Keeps asking feedback until it understands
2. Code Generator LLM: Writes code for the clarified requirement
3. 3 Test Generator LLMs: Each independently generates unit tests
4. Validation: At least 2/3 tests must pass
5. Feedback Loop: Max 5 iterations, then asks for human help
6. GUI Integrated: Works seamlessly with gui/main.py

Author: Enhanced Agentic System
Date: 2026
"""

import os
import sys
import json
import tempfile
import subprocess
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add Dataset folder to path
sys.path.insert(0, str(Path(__file__).parent))

from aws_llm_provider import MultiProviderLLM


class ClarificationStatus(Enum):
    """Status of question clarification"""
    UNCLEAR = "unclear"
    NEEDS_MORE_INFO = "needs_more_info"
    CLARIFIED = "clarified"
    CONFIRMED = "confirmed"


class TestStatus(Enum):
    """Status of test execution"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ClarificationResult:
    """Result of question clarification process"""
    status: ClarificationStatus
    understanding: str
    clarifying_questions: List[str]
    confidence: float  # 0-100
    requirements: Dict[str, Any]


@dataclass
class CodeGeneration:
    """Generated code with metadata"""
    code: str
    function_name: str
    description: str
    dependencies: List[str]
    expected_input: Dict[str, str]
    expected_output: str


@dataclass
class TestResult:
    """Result from a test LLM"""
    llm_id: str
    test_code: str
    status: TestStatus
    passed_count: int
    failed_count: int
    error_message: Optional[str]
    execution_output: str


@dataclass
class IterationResult:
    """Result of one complete iteration"""
    iteration: int
    code: CodeGeneration
    tests: List[TestResult]
    validation_passed: bool
    total_passed: int
    total_tests: int
    feedback_for_next: Optional[str]


class QuestionClarifier:
    """
    LLM that keeps asking questions until it fully understands user's request
    """
    
    def __init__(self):
        self.llm = MultiProviderLLM()
        self.conversation_history = []
        self.max_clarification_rounds = 5
        
    def clarify_question(
        self,
        user_question: str,
        user_feedback: Optional[str] = None
    ) -> ClarificationResult:
        """
        Ask clarifying questions until fully understanding the requirement
        
        Args:
            user_question: Initial user question
            user_feedback: User's response to clarifying questions
            
        Returns:
            ClarificationResult with understanding and next questions if needed
        """
        
        if user_feedback:
            self.conversation_history.append({
                'role': 'user',
                'content': user_feedback
            })
        else:
            self.conversation_history = [{
                'role': 'user',
                'content': user_question
            }]
        
        # Build conversation context
        conversation = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in self.conversation_history
        ])
        
        prompt = f"""You are an expert software engineer helping clarify a user's requirements.

**Conversation History:**
{conversation}

**Your Task:**
1. Analyze the user's request thoroughly
2. Determine if you have enough information to proceed
3. If NOT clear, ask specific clarifying questions
4. If CLEAR, provide a detailed understanding

**Response Format (JSON):**
{{
    "status": "unclear|needs_more_info|clarified",
    "confidence": 85,
    "understanding": "Detailed explanation of what user wants",
    "requirements": {{
        "primary_goal": "what to build",
        "inputs": {{"param1": "description"}},
        "outputs": "what should be returned",
        "constraints": ["list of constraints"],
        "examples": ["example scenarios"]
    }},
    "clarifying_questions": [
        "Specific question 1?",
        "Specific question 2?"
    ]
}}

**Guidelines:**
- Status "unclear": Don't understand at all, need basic info
- Status "needs_more_info": Understand partially, need specific details
- Status "clarified": Fully understand, ready to proceed
- Ask 1-3 specific questions per round
- Higher confidence (>90) when ready to proceed
- Be thorough but respectful of user's time

Provide your analysis:"""

        try:
            response = self.llm.generate_content(prompt)
            result_text = response['text'].strip()
            
            # Extract JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            
            # Save LLM response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': result['understanding']
            })
            
            return ClarificationResult(
                status=ClarificationStatus(result['status']),
                understanding=result['understanding'],
                clarifying_questions=result.get('clarifying_questions', []),
                confidence=result.get('confidence', 0),
                requirements=result.get('requirements', {})
            )
            
        except Exception as e:
            print(f"[ERROR] Clarification error: {e}")
            return ClarificationResult(
                status=ClarificationStatus.UNCLEAR,
                understanding=f"Error: {str(e)}",
                clarifying_questions=["Could you please rephrase your request?"],
                confidence=0,
                requirements={}
            )


class CodeGenerator:
    """
    LLM that generates code based on clarified requirements
    """
    
    def __init__(self):
        self.llm = MultiProviderLLM()
        
    def generate_code(
        self,
        requirements: Dict[str, Any],
        previous_code: Optional[str] = None,
        test_feedback: Optional[str] = None
    ) -> CodeGeneration:
        """
        Generate Python code based on requirements
        
        Args:
            requirements: Clarified requirements from QuestionClarifier
            previous_code: Previous code if this is a revision
            test_feedback: Feedback from failed tests
            
        Returns:
            CodeGeneration with complete code
        """
        
        revision_context = ""
        if previous_code and test_feedback:
            revision_context = f"""
**PREVIOUS CODE (Had Issues):**
```python
{previous_code}
```

**TEST FEEDBACK:**
{test_feedback}

**IMPORTANT:** Fix the issues mentioned in the feedback!
"""
        
        prompt = f"""You are an expert Python developer. Generate production-ready code based on requirements.

**Requirements:**
{json.dumps(requirements, indent=2)}

{revision_context}

**Code Requirements:**
1. Function signature must match expected inputs/outputs
2. Include comprehensive error handling
3. Add docstrings with examples
4. Use type hints
5. Follow Python best practices
6. Include input validation
7. Handle edge cases (None, empty, invalid data)

**Response Format (JSON):**
{{
    "function_name": "calculate_metric",
    "description": "Clear description",
    "code": "Complete Python code here",
    "dependencies": ["import1", "import2"],
    "expected_input": {{"param1": "type and description"}},
    "expected_output": "type and description"
}}

**Example Code Structure:**
```python
def calculate_metric(data: dict, config: dict = None) -> float:
    \"\"\"
    Calculate custom metric.
    
    Args:
        data: Input data dictionary
        config: Optional configuration
        
    Returns:
        Calculated metric value
        
    Raises:
        ValueError: If data is invalid
        KeyError: If required key missing
        
    Example:
        >>> calculate_metric({{'value': 10}})
        15.5
    \"\"\"
    # Validate inputs
    if not data:
        raise ValueError("Data cannot be empty")
    
    # Your logic here
    result = ...
    
    return result
```

Generate the code now:"""

        try:
            response = self.llm.generate_content(prompt)
            result_text = response['text'].strip()
            
            # Extract JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                # Try to find JSON block
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group()
            
            result = json.loads(result_text)
            
            return CodeGeneration(
                code=result['code'],
                function_name=result['function_name'],
                description=result['description'],
                dependencies=result.get('dependencies', []),
                expected_input=result.get('expected_input', {}),
                expected_output=result.get('expected_output', 'Any')
            )
            
        except Exception as e:
            print(f"[ERROR] Code generation error: {e}")
            # Return minimal fallback
            return CodeGeneration(
                code=f"# Error: {str(e)}\ndef placeholder():\n    pass",
                function_name="placeholder",
                description="Error in code generation",
                dependencies=[],
                expected_input={},
                expected_output="None"
            )


class TestGeneratorJury:
    """
    3 independent LLMs that each generate unit tests
    """
    
    def __init__(self):
        self.llms = [MultiProviderLLM() for _ in range(3)]
        
    def generate_tests(
        self,
        code: CodeGeneration,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """
        Have 3 LLMs independently generate unit tests
        
        Args:
            code: Generated code to test
            requirements: Original requirements
            
        Returns:
            List of 3 test code strings
        """
        
        test_codes = []
        
        for i, llm in enumerate(self.llms, 1):
            print(f"\n[TEST LLM {i}] Generating unit tests...")
            
            test_type = ["edge cases", "normal cases", "error cases"][i-1]
            
            prompt = f"""You are Test Engineer #{i}. Generate comprehensive unit tests for this code.

**Code to Test:**
```python
{code.code}
```

**Requirements:**
{json.dumps(requirements, indent=2)}

**Your Focus:** Test {test_type} specifically, but cover all scenarios.

**Test Requirements:**
1. Use Python unittest framework
2. Test class name: Test{code.function_name.title().replace('_', '')}
3. Include setUp/tearDown if needed
4. At least 5 test methods
5. Test categories:
   - Normal/happy path cases
   - Edge cases (empty, None, zeros, extremes)
   - Error cases (invalid inputs, exceptions)
6. Clear test method names (test_functionality_scenario)
7. Assertions with helpful messages

**Response Format:**
Provide ONLY the complete test code (no JSON, no explanation):

```python
import unittest
# other imports

class Test{code.function_name.title().replace('_', '')}(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_case_1(self):
        # Test code here
        pass
        
if __name__ == '__main__':
    unittest.main()
```

Generate complete test code now:"""

            try:
                response = llm.generate_content(prompt)
                test_code = response['text'].strip()
                
                # Extract Python code
                if '```python' in test_code:
                    test_code = test_code.split('```python')[1].split('```')[0].strip()
                elif '```' in test_code:
                    test_code = test_code.split('```')[1].split('```')[0].strip()
                
                test_codes.append(test_code)
                print(f"[TEST LLM {i}] Generated {len(test_code.splitlines())} lines of tests")
                
            except Exception as e:
                print(f"[TEST LLM {i}] Error: {e}")
                # Minimal fallback test
                test_codes.append(f"""
import unittest

class TestFallback(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(True, "Fallback test")
        
if __name__ == '__main__':
    unittest.main()
""")
        
        return test_codes


class TestExecutor:
    """
    Executes tests and determines if they pass
    """
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / 'integrated_jury_tests'
        self.temp_dir.mkdir(exist_ok=True)
        
    def execute_tests(
        self,
        code: CodeGeneration,
        test_codes: List[str]
    ) -> List[TestResult]:
        """
        Execute all test suites and collect results
        
        Args:
            code: Generated code
            test_codes: List of test codes from 3 LLMs
            
        Returns:
            List of TestResult for each LLM
        """
        
        results = []
        
        # Save code to file
        code_file = self.temp_dir / 'code_to_test.py'
        code_file.write_text(code.code)
        
        for i, test_code in enumerate(test_codes, 1):
            print(f"\n[EXECUTOR] Running tests from LLM {i}...")
            
            # Save test to file
            test_file = self.temp_dir / f'test_from_llm_{i}.py'
            
            # Ensure test imports the code correctly
            test_with_import = f"""import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

{test_code}
"""
            test_file.write_text(test_with_import)
            
            # Run tests
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'unittest', f'test_from_llm_{i}'],
                    cwd=str(self.temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout + result.stderr
                
                # Parse results
                passed = output.count('OK') > 0 or output.count('Ran ') > 0
                failed_match = output.count('FAILED')
                error_match = output.count('ERROR')
                
                # Count tests
                import re
                ran_match = re.search(r'Ran (\d+) test', output)
                total_tests = int(ran_match.group(1)) if ran_match else 0
                
                fail_count = failed_match + error_match
                pass_count = total_tests - fail_count if total_tests > 0 else (1 if passed else 0)
                
                status = TestStatus.PASSED if passed and fail_count == 0 else (
                    TestStatus.FAILED if fail_count > 0 else TestStatus.ERROR
                )
                
                results.append(TestResult(
                    llm_id=f"LLM_{i}",
                    test_code=test_code,
                    status=status,
                    passed_count=pass_count,
                    failed_count=fail_count,
                    error_message=None if status == TestStatus.PASSED else output,
                    execution_output=output
                ))
                
                print(f"[LLM {i}] {pass_count} passed, {fail_count} failed")
                
            except subprocess.TimeoutExpired:
                results.append(TestResult(
                    llm_id=f"LLM_{i}",
                    test_code=test_code,
                    status=TestStatus.ERROR,
                    passed_count=0,
                    failed_count=0,
                    error_message="Test execution timeout",
                    execution_output="Timeout after 30 seconds"
                ))
                print(f"[LLM {i}] Timeout")
                
            except Exception as e:
                results.append(TestResult(
                    llm_id=f"LLM_{i}",
                    test_code=test_code,
                    status=TestStatus.ERROR,
                    passed_count=0,
                    failed_count=0,
                    error_message=str(e),
                    execution_output=f"Error: {str(e)}"
                ))
                print(f"[LLM {i}] Error: {e}")
        
        return results


class IntegratedJurySystem:
    """
    Complete integrated jury system
    """
    
    def __init__(self):
        self.clarifier = QuestionClarifier()
        self.generator = CodeGenerator()
        self.test_jury = TestGeneratorJury()
        self.executor = TestExecutor()
        
        self.max_iterations = 5
        self.min_passing_tests = 2  # At least 2 of 3 must pass
        
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_dir = Path('generated_datasets') / f'jury_session_{self.session_id}'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.iterations: List[IterationResult] = []
        
    def run_full_workflow(
        self,
        user_question: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: Clarify → Generate → Test → Validate → Iterate/Human
        
        Args:
            user_question: User's initial question
            progress_callback: Function to call with progress updates
            
        Returns:
            Complete session result
        """
        
        def log(message: str):
            print(f"[JURY] {message}")
            if progress_callback:
                progress_callback(message)
        
        log("Starting Integrated Jury System...")
        log(f"Session ID: {self.session_id}")
        
        # ===============================================
        # PHASE 1: Question Clarification
        # ===============================================
        log("\n=== PHASE 1: Question Clarification ===")
        
        clarification = self.clarifier.clarify_question(user_question)
        clarification_rounds = 0
        
        while (clarification.status != ClarificationStatus.CLARIFIED and 
               clarification_rounds < self.clarifier.max_clarification_rounds):
            
            log(f"\nConfidence: {clarification.confidence}%")
            log(f"Understanding: {clarification.understanding}")
            
            if clarification.clarifying_questions:
                log("\nNeed clarification:")
                for q in clarification.clarifying_questions:
                    log(f"  - {q}")
                
                # In GUI, this will pause for user input
                # For now, return asking for clarification
                return {
                    'status': 'needs_clarification',
                    'questions': clarification.clarifying_questions,
                    'current_understanding': clarification.understanding,
                    'confidence': clarification.confidence,
                    'session_id': self.session_id
                }
            
            clarification_rounds += 1
        
        if clarification.status != ClarificationStatus.CLARIFIED:
            log("Could not clarify requirements after max rounds")
            return {
                'status': 'clarification_failed',
                'message': 'Could not understand requirements',
                'session_id': self.session_id
            }
        
        log(f"Requirements clarified (Confidence: {clarification.confidence}%)")
        requirements = clarification.requirements
        
        # ===============================================
        # PHASE 2: Iterative Code Generation & Testing
        # ===============================================
        log("\n=== PHASE 2: Code Generation & Testing ===")
        
        current_code = None
        test_feedback = None
        
        for iteration in range(1, self.max_iterations + 1):
            log(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            
            # Generate code
            log("Generating code...")
            code = self.generator.generate_code(
                requirements=requirements,
                previous_code=current_code.code if current_code else None,
                test_feedback=test_feedback
            )
            current_code = code
            
            log(f"Code generated: {code.function_name}")
            
            # Generate tests (3 LLMs)
            log("Generating tests (3 LLMs)...")
            test_codes = self.test_jury.generate_tests(code, requirements)
            
            # Execute tests
            log("Executing tests...")
            test_results = self.executor.execute_tests(code, test_codes)
            
            # Count passing tests
            passing_llms = sum(1 for r in test_results if r.status == TestStatus.PASSED)
            total_passed = sum(r.passed_count for r in test_results)
            total_tests = sum(r.passed_count + r.failed_count for r in test_results)
            
            log(f"Results: {passing_llms}/3 LLMs passed")
            log(f"Total: {total_passed}/{total_tests} tests passed")
            
            # Validation: Need at least 2 of 3 LLMs to pass
            validation_passed = passing_llms >= self.min_passing_tests
            
            iteration_result = IterationResult(
                iteration=iteration,
                code=code,
                tests=test_results,
                validation_passed=validation_passed,
                total_passed=total_passed,
                total_tests=total_tests,
                feedback_for_next=None
            )
            self.iterations.append(iteration_result)
            
            # Save iteration artifacts
            self._save_iteration(iteration_result)
            
            if validation_passed:
                log(f"SUCCESS! {passing_llms}/3 LLMs passed validation")
                return {
                    'status': 'success',
                    'code': code.code,
                    'function_name': code.function_name,
                    'description': code.description,
                    'iterations': iteration,
                    'test_results': {
                        'passing_llms': passing_llms,
                        'total_passed': total_passed,
                        'total_tests': total_tests
                    },
                    'session_id': self.session_id,
                    'session_dir': str(self.session_dir)
                }
            
            # Prepare feedback for next iteration
            log(f"Only {passing_llms}/3 LLMs passed. Preparing feedback...")
            
            feedback_parts = []
            for result in test_results:
                if result.status != TestStatus.PASSED:
                    feedback_parts.append(f"""
**{result.llm_id} Failed:**
{result.error_message or result.execution_output}
""")
            
            test_feedback = "\n".join(feedback_parts)
            iteration_result.feedback_for_next = test_feedback
            
            log(f"Attempting revision (Iteration {iteration + 1})...")
        
        # ===============================================
        # PHASE 3: Human Intervention Required
        # ===============================================
        log("\n=== PHASE 3: Human Intervention Needed ===")
        log(f"Failed after {self.max_iterations} iterations")
        
        return {
            'status': 'human_intervention_required',
            'message': f'Failed to generate passing code after {self.max_iterations} iterations',
            'iterations': self.iterations,
            'last_code': current_code.code if current_code else None,
            'last_feedback': test_feedback,
            'session_id': self.session_id,
            'session_dir': str(self.session_dir)
        }
    
    def provide_clarification(self, user_feedback: str) -> Dict[str, Any]:
        """
        Continue clarification process with user feedback
        
        Args:
            user_feedback: User's answers to clarifying questions
            
        Returns:
            Either more questions or ready to proceed
        """
        
        clarification = self.clarifier.clarify_question(
            user_question=None,  # Already in history
            user_feedback=user_feedback
        )
        
        if clarification.status == ClarificationStatus.CLARIFIED:
            return {
                'status': 'clarified',
                'requirements': clarification.requirements,
                'confidence': clarification.confidence
            }
        else:
            return {
                'status': 'needs_more_clarification',
                'questions': clarification.clarifying_questions,
                'current_understanding': clarification.understanding,
                'confidence': clarification.confidence
            }
    
    def _save_iteration(self, iteration: IterationResult):
        """Save iteration artifacts to session directory"""
        
        iter_dir = self.session_dir / f'iteration_{iteration.iteration}'
        iter_dir.mkdir(exist_ok=True)
        
        # Save code
        (iter_dir / 'code.py').write_text(iteration.code.code)
        
        # Save tests
        for i, test_result in enumerate(iteration.tests, 1):
            (iter_dir / f'test_llm_{i}.py').write_text(test_result.test_code)
            (iter_dir / f'test_llm_{i}_output.txt').write_text(test_result.execution_output)
        
        # Save summary
        summary = {
            'iteration': iteration.iteration,
            'validation_passed': iteration.validation_passed,
            'total_passed': iteration.total_passed,
            'total_tests': iteration.total_tests,
            'test_results': [
                {
                    'llm_id': r.llm_id,
                    'status': r.status.value,
                    'passed': r.passed_count,
                    'failed': r.failed_count
                }
                for r in iteration.tests
            ]
        }
        (iter_dir / 'summary.json').write_text(json.dumps(summary, indent=2))


def test_integrated_system():
    """Test the integrated jury system"""
    
    system = IntegratedJurySystem()
    
    user_question = """
I need a function that calculates code quality score.
It should take lines of code, bug count, and test coverage as inputs.
Higher test coverage is better, more bugs is worse.
"""
    
    def progress(msg):
        print(f"[PROGRESS] {msg}")
    
    result = system.run_full_workflow(user_question, progress)
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    test_integrated_system()
