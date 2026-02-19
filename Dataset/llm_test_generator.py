"""
LLM Test Generator for Automated Unit Test Creation
======================================================
- Jury generates unit tests for LLM-created code
- Tests validate correctness, edge cases, and data integrity
- Automatic test execution with real metrics data
- Fallback and error handling for failed tests
"""

# Import your existing multi-provider LLM system
from aws_llm_provider import MultiProviderLLM

import os
import json
import subprocess
import sys
import tempfile
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestSuite:
    """Generated test suite for a metric"""
    metric_name: str
    code_under_test: str
    test_code: str
    test_cases: List[Dict]  # [{"name": "test_x", "input": {...}, "expected": ...}]
    dependencies: List[str]


@dataclass
class SingleTestResult:
    """Result of running a single test (renamed to avoid conflict with integrated_jury_system.TestResult)"""
    test_name: str
    status: str  # "passed", "failed", "error"
    output: str
    error_message: Optional[str] = None
    execution_time: float = 0.0


class LLMTestGenerator:
    """
    Intelligent Test Generator for LLM-Generated Metrics Code
    """
    
    def __init__(self, api_key: str = None):
        # Use your existing multi-provider LLM system (AWS + Gemini)
        self.llm_provider = MultiProviderLLM()
        print(f"[INIT] LLM Test Generator using: {self.llm_provider.get_active_provider()}")
        
        # Keep api_key for backward compatibility (not used anymore)
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        
        self.test_generator_config = {
            'temperature': 0.5,
            'top_p': 0.95,
        }
        
        self.test_validators = [
            {'temperature': 0.3, 'top_p': 0.9},   # Conservative test validator
            {'temperature': 0.5, 'top_p': 0.95},  # Balanced validator
            {'temperature': 0.4, 'top_p': 0.85},  # Strict validator
        ]
    
    def generate_unit_tests(
        self,
        metric_name: str,
        metric_code: str,
        metric_description: str,
        base_metrics: Dict
    ) -> TestSuite:
        """
        Generate comprehensive unit tests for the metric
        IMPORTANT: Will be validated by 3 judges, so generate STRONG test cases
        """
        
        prompt = f"""You are an expert test engineer writing comprehensive unit tests for a custom metrics calculation function.

**CRITICAL REQUIREMENT: This test suite will be validated by 3 expert judges. Each judge will verify:
1. Minimum 3 test cases covering different scenarios
2. Each test case must be independent and well-documented
3. Tests must properly import and call the calculate_custom_metric function
4. Tests must include proper assertions for success/failure cases**

**Metric Information:**
Name: {metric_name}
Description: {metric_description}

**Code to Test:**
```python
{metric_code}
```

**Available Base Metrics:**
{json.dumps(base_metrics, indent=2)}

**MANDATORY Task:** Generate AT LEAST 3 distinct test cases in these categories:
1. **Normal Case:** Test with valid base_metrics, use Path("/tmp") or tempfile for repo_path - should pass
2. **Edge Case:** Test with zero values, empty metrics, boundary values
3. **Error Case:** Test with invalid inputs - should raise KeyError or FileNotFoundError

**Additional Cases (Optional):**
4. **Consistency:** Test that same input gives same output
5. **Data Validation:** Test metrics calculation with different metric combinations

**Requirements:**
1. Write tests using Python's unittest framework
2. EXACTLY import: `from code import calculate_custom_metric`
3. Import statement MUST be: `from code import calculate_custom_metric` (not from custom_metrics)
4. For repo_path: Use `str(Path(__file__).parent)` or `tempfile.gettempdir()` for testing (NOT relative test_repo)
5. Create test class inheriting from unittest.TestCase
6. Each test method must start with `def test_` prefix
7. Include clear docstrings for each test
8. All tests must be executable and independent
9. Include proper error handling with assertRaises for exception tests
10. Use `tempfile`, `pathlib.Path`, and `os.path` as needed

**Output Format (JSON):**
{{
    "test_cases": [
        {{
            "name": "test_normal_case",
            "description": "Test with typical inputs",
            "category": "Normal Case",
            "input_data": {{"metric1": 100}},
            "expected_outcome": "Should return dict with metric value"
        }},
        {{
            "name": "test_edge_case",
            "description": "Test with edge values",
            "category": "Edge Case",
            "input_data": {{"metric1": 0}},
            "expected_outcome": "Should handle zero values"
        }},
        {{
            "name": "test_error_case",
            "description": "Test with invalid input",
            "category": "Error Case",
            "input_data": {{}},
            "expected_outcome": "Should raise KeyError for missing metrics"
        }}
    ],
    "test_code": "import unittest\\nfrom code import calculate_custom_metric\\nfrom pathlib import Path\\n\\nclass TestCustomMetric(unittest.TestCase):\\n    def test_normal_case(self):\\n        ...",
    "dependencies": ["unittest", "pathlib"],
    "test_count": 3,
    "coverage_notes": "Covers normal, edge, and error cases"
}}

IMPORTANT: The test_code must be VALID Python that can be executed with: python -m unittest tests.py

Generate the test suite now:"""

        try:
            # Use your multi-provider LLM system (AWS + Gemini fallback)
            response = self.llm_provider.generate_content(prompt)
            response_text = response['text'].strip()
            
            print(f"[DEBUG] LLM Response length: {len(response_text)}")
            print(f"[DEBUG] Response preview: {response_text[:200]}...")
            
            # Extract JSON
            original_text = response_text
            extraction_text = response_text
            
            if '```json' in response_text:
                extraction_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```python' in response_text:
                # If it's only python code, extract it and return as is
                code_match = re.search(r'```python\n(.*?)```', original_text, re.DOTALL)
                if code_match:
                    test_code = code_match.group(1).strip()
                    print(f"[INFO] Extracted test code from markdown (no JSON)")
                    return TestSuite(
                        metric_name=metric_name,
                        code_under_test=metric_code,
                        test_code=test_code,
                        test_cases=[],
                        dependencies=[]
                    )
            elif '```' in response_text:
                extraction_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Sanitize the response: remove non-printable characters and Python literals
            # Remove control characters (but keep newlines and tabs)
            extraction_text = ''.join(char if ord(char) >= 32 or char in '\n\t\r' else '' for char in extraction_text)
            # Convert Path(...) calls to strings
            extraction_text = re.sub(r'Path\(["\']([^"\']*?)["\']\)', r'"\1"', extraction_text)
            
            print(f"[DEBUG] Extracted JSON: {extraction_text[:200]}...")
            
            try:
                result = json.loads(extraction_text)
            except json.JSONDecodeError as json_error:
                print(f"[ERROR] JSON parsing failed: {json_error}")
                
                # Fallback: Try to extract JSON from any {} blocks
                json_match = re.search(r'\{.*\}', extraction_text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        print("[INFO] Recovered JSON using regex fallback")
                    except Exception as e2:
                        print(f"[DEBUG] Regex fallback also failed: {e2}")
                        # Last resort: try to extract test code from markdown
                        code_match = re.search(r'```python\n(.*?)```', original_text, re.DOTALL)
                        if code_match:
                            test_code = code_match.group(1).strip()
                            print(f"[INFO] Extracted test code from markdown, creating result")
                            
                            # Extract test case names from the code
                            test_names = re.findall(r'def (test_\w+)\(', test_code)
                            print(f"[INFO] Found {len(test_names)} test cases: {test_names}")
                            
                            result = {
                                "test_code": test_code,
                                "test_cases": [{"name": name, "description": f"Test: {name}"} for name in test_names],
                                "dependencies": []
                            }
                        else:
                            raise Exception(f"JSON parsing failed even with fallback: {json_error}")
                else:
                    raise Exception(f"No JSON found in response: {json_error}")
            
            return TestSuite(
                metric_name=metric_name,
                code_under_test=metric_code,
                test_code=result.get('test_code', ''),
                test_cases=result.get('test_cases', []),
                dependencies=result.get('dependencies', [])
            )
            
        except Exception as e:
            print(f"Test generation error: {e}")
            return None
    
    def generate_tests_with_jury(
        self,
        metric_name: str,
        metric_code: str,
        metric_description: str,
        base_metrics: Dict,
        num_judges: int = 3
    ) -> TestSuite:
        """
        Have 3 jury members EACH generate test cases independently,
        then merge all tests into one comprehensive test suite
        """
        print(f"\nHaving {num_judges} judges each create test cases...")
        
        all_test_codes = []
        all_test_cases = []
        
        for judge_num in range(num_judges):
            judge_prompt = f"""You are Judge #{judge_num + 1} - an expert QA engineer writing comprehensive unit tests.

**Your Task:** Generate YOUR OWN set of unit tests for this metric function.
Each judge generates DIFFERENT test scenarios to ensure comprehensive coverage.

**Metric Information:**
Name: {metric_name}
Description: {metric_description}

**Code to Test:**
```python
{metric_code}
```

**Available Base Metrics:**
{json.dumps(base_metrics, indent=2)}

**CRITICAL:** Write AT LEAST 3 test cases focusing on:
- Judge 1: Normal cases, happy path, typical inputs
- Judge 2: Edge cases, boundary values, zero values, empty inputs
- Judge 3: Error cases, invalid inputs, exception handling

Your Judge Role: Generate tests for {"normal/happy path scenarios" if judge_num == 0 else "edge cases and boundary conditions" if judge_num == 1 else "error handling and exceptions"}

**Requirements:**
1. Write complete unittest code ready to execute
2. EXACTLY import: `from code import calculate_custom_metric`
3. For repo_path: Use `tempfile.gettempdir()` or `str(Path(__file__).parent)` (NOT relative paths)
4. Focus on YOUR assigned test category
5. At least 3 test cases
6. Each test method must start with `def test_`
7. Include clear docstrings

**Output Format (JSON):**
{{
    "judge_number": {judge_num + 1},
    "test_code": "import unittest\\nfrom code import...[full Python code here]"
}}

OR just provide the test code in a python block:

```python
import unittest
from code import calculate_custom_metric
...your test code...
```

Generate your test suite now (code is more important than JSON):"""
            
            try:
                response = self.llm_provider.generate_content(judge_prompt)
                response_text = response['text'].strip()
                
                print(f"[DEBUG] Judge {judge_num + 1} Response length: {len(response_text)}")
                
                # Extract JSON or code
                extraction_text = response_text
                
                if '```json' in response_text:
                    extraction_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```python' in response_text:
                    code_match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
                    if code_match:
                        test_code = code_match.group(1).strip()
                        all_test_codes.append(test_code)
                        print(f"[INFO] Judge {judge_num + 1}: Extracted test code from markdown")
                        continue
                elif '```' in response_text:
                    extraction_text = response_text.split('```')[1].split('```')[0].strip()
                
                # Sanitize
                extraction_text = ''.join(char if ord(char) >= 32 or char in '\n\t\r' else '' for char in extraction_text)
                extraction_text = re.sub(r'Path\(["\']([^"\']*?)["\']\)', r'"\1"', extraction_text)
                
                # Additional cleanup for control chars in strings
                extraction_text = extraction_text.replace('\x00', '').replace('\x01', '').replace('\x02', '')
                
                try:
                    result = json.loads(extraction_text)
                    test_code = result.get('test_code', '')
                    if test_code:
                        all_test_codes.append(test_code)
                        all_test_cases.extend(result.get('test_cases', []))
                        print(f"Judge {judge_num + 1}: Generated tests")
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Judge {judge_num + 1} JSON parsing: {e}")
                    # Try to extract just the code block
                    code_match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
                    if code_match:
                        test_code = code_match.group(1).strip()
                        all_test_codes.append(test_code)
                        print(f"Judge {judge_num + 1}: Extracted code directly from markdown")
                    else:
                        # Try regex fallback for JSON
                        json_match = re.search(r'\{.*\}', extraction_text, re.DOTALL)
                        if json_match:
                            try:
                                result = json.loads(json_match.group())
                                test_code = result.get('test_code', '')
                                if test_code:
                                    all_test_codes.append(test_code)
                                    all_test_cases.extend(result.get('test_cases', []))
                                    print(f"Judge {judge_num + 1}: Recovered with fallback")
                            except:
                                print(f"[ERROR] Judge {judge_num + 1} fallback also failed")
                        else:
                            print(f"[ERROR] Judge {judge_num + 1} no JSON found")
                            
            except Exception as e:
                print(f"⚠️ Judge {judge_num + 1} error: {e}")
                continue
        
        # Merge all test codes into one test suite
        merged_test_code = self._merge_test_codes(all_test_codes, metric_name, metric_code)
        
        return TestSuite(
            metric_name=metric_name,
            code_under_test=metric_code,
            test_code=merged_test_code,
            test_cases=all_test_cases,
            dependencies=["unittest", "tempfile", "pathlib", "json"]
        )
    
    def _merge_test_codes(self, test_codes: List[str], metric_name: str, metric_code: str) -> str:
        """Merge multiple test codes from different judges into one comprehensive suite"""
        if not test_codes:
            return ""
        
        # Extract test methods from each judge's code
        all_test_methods = []
        
        for test_code in test_codes:
            # Extract all test methods (def test_...)
            test_methods = re.findall(r'(    def test_.*?)(?=    def test_|\Z)', test_code, re.DOTALL)
            all_test_methods.extend(test_methods)
        
        # Create merged test suite
        merged_code = f"""import unittest
import tempfile
from pathlib import Path
from code import calculate_custom_metric


class Test{metric_name.replace('_', '').replace('-', '').title()}(unittest.TestCase):
    \"\"\"Comprehensive test suite with tests from {len(test_codes)} judges\"\"\"
    
"""
        
        # Add all test methods
        for i, method in enumerate(all_test_methods, 1):
            merged_code += method + "\n"
        
        merged_code += """
if __name__ == '__main__':
    unittest.main()
"""
        
        return merged_code
    
    def validate_tests_with_jury(
        self,
        test_suite: TestSuite,
        num_validators: int = 3
    ) -> Tuple[bool, List[str], float]:
        """
        Multiple LLMs validate the test quality
        Returns: (is_good, feedback_list, quality_score)
        """
        
        validation_results = []
        scores = []
        
        validation_prompt = f"""You are an expert QA engineer reviewing a test suite for metrics code.

**Metric:** {test_suite.metric_name}

**Code Being Tested:**
```python
{test_suite.code_under_test}
```

**Test Suite:**
```python
{test_suite.test_code}
```

**Your Task:** Evaluate:
1. **Coverage:** Do tests cover normal, edge, and error cases?
2. **Correctness:** Are assertions checking the right things?
3. **Completeness:** Are there enough test cases (at least 5)?
4. **Practicality:** Can these tests actually run and provide value?
5. **Maintainability:** Are tests clear and well-documented?

**Output Format (JSON):**
{{
    "quality_score": 85,
    "is_good_quality": true,
    "issues": ["list of issues if any"],
    "suggestions": ["list of improvements"],
    "reasoning": "overall assessment"
}}

Provide your evaluation:"""

        for i in range(min(num_validators, len(self.test_validators))):
            try:
                # Use your multi-provider LLM system (AWS + Gemini fallback)
                response = self.llm_provider.generate_content(validation_prompt)
                response_text = response['text'].strip()
                
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as json_error:
                    print(f"[ERROR] Validator {i+1} JSON parsing failed: {json_error}")
                    # Fallback: Try to extract JSON from any {} blocks
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            print(f"[INFO] Validator {i+1} recovered JSON using regex fallback")
                        except:
                            print(f"[ERROR] Validator {i+1} JSON fallback also failed")
                            continue
                    else:
                        print(f"[ERROR] Validator {i+1} no JSON found in response")
                        continue
                
                scores.append(result.get('quality_score', 50))
                if result.get('issues'):
                    validation_results.extend(result['issues'])
                
            except Exception as e:
                print(f"⚠️ Validator {i+1} error: {e}")
                continue
        
        avg_score = sum(scores) / len(scores) if scores else 0
        is_good = avg_score >= 70
        
        return is_good, validation_results, avg_score
    
    def execute_tests_in_sandbox(
        self,
        test_suite: TestSuite,
        sample_data: Dict
    ) -> List[SingleTestResult]:
        """
        Execute tests in isolated sandbox environment
        Returns list of test results
        """
        
        results = []
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_test_file = f.name
            
            # Write combined code: implementation + tests
            combined_code = f"""
import unittest
import json
import sys
from pathlib import Path

# Implementation
{test_suite.code_under_test}

# Sample data for tests
SAMPLE_DATA = {json.dumps(sample_data, indent=4)}

# Tests
{test_suite.test_code}

if __name__ == '__main__':
    # Run tests with verbose output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
"""
            f.write(combined_code)
        
        try:
            # Execute tests
            result = subprocess.run(
                [sys.executable, temp_test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output - improved unittest result parsing
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            
            # Look for unittest summary first (more reliable)
            total_tests = 0
            failures = 0
            errors = 0
            
            for line in output_lines:
                line = line.strip()
                if line.startswith('Ran ') and ' tests in ' in line:
                    try:
                        total_tests = int(line.split('Ran ')[1].split(' ')[0])
                        print(f"[DEBUG] Found {total_tests} total tests")
                    except:
                        pass
                elif 'FAILED (' in line:
                    # Parse "FAILED (failures=3, errors=1)"
                    try:
                        if 'failures=' in line:
                            failures = int(line.split('failures=')[1].split(',')[0].split(')')[0])
                        if 'errors=' in line:
                            errors = int(line.split('errors=')[1].split(',')[0].split(')')[0])
                        print(f"[DEBUG] Found {failures} failures, {errors} errors")
                    except:
                        pass
            
            if total_tests > 0:
                # Create results based on parsed summary
                passed = total_tests - failures - errors
                
                print(f"[DEBUG] Test results: {passed} passed, {failures} failed, {errors} errors")
                
                for i in range(passed):
                    results.append(SingleTestResult(
                        test_name=f'test_{i+1}',
                        status='passed',
                        output=result.stdout,
                        error_message=None
                    ))
                for i in range(failures):
                    results.append(SingleTestResult(
                        test_name=f'failed_test_{i+1}',
                        status='failed',
                        output=result.stdout,
                        error_message=result.stderr if result.stderr else None
                    ))
                for i in range(errors):
                    results.append(SingleTestResult(
                        test_name=f'error_test_{i+1}',
                        status='error',
                        output=result.stdout,
                        error_message=result.stderr if result.stderr else None
                    ))
            else:
                # Fallback: parse individual test lines
                for line in output_lines:
                    line = line.strip()
                    if ' ... ' in line:
                        if ' ... ok' in line:
                            test_name = line.split(' ... ')[0].split(' ')[0]
                            results.append(SingleTestResult(
                                test_name=test_name,
                                status='passed',
                                output=result.stdout,
                                error_message=None
                            ))
                        elif ' ... FAIL' in line:
                            test_name = line.split(' ... ')[0].split(' ')[0]
                            results.append(SingleTestResult(
                                test_name=test_name,
                                status='failed',
                                output=result.stdout,
                                error_message=result.stderr if result.stderr else None
                            ))
                        elif ' ... ERROR' in line:
                            test_name = line.split(' ... ')[0].split(' ')[0]
                            results.append(SingleTestResult(
                                test_name=test_name,
                                status='error',
                                output=result.stdout,
                                error_message=result.stderr if result.stderr else None
                            ))
                
                # If still no results, create summary result
                if not results:
                    overall_status = 'passed' if result.returncode == 0 else 'failed'
                    results.append(SingleTestResult(
                        test_name='all_tests',
                        status=overall_status,
                        output=result.stdout,
                        error_message=result.stderr if result.stderr else None
                    ))
            
        except subprocess.TimeoutExpired:
            results.append(SingleTestResult(
                test_name='execution',
                status='error',
                output='',
                error_message='Test execution timeout (>30s)'
            ))
        except Exception as e:
            results.append(SingleTestResult(
                test_name='execution',
                status='error',
                output='',
                error_message=str(e)
            ))
        finally:
            # Cleanup
            try:
                Path(temp_test_file).unlink()
            except:
                pass
        
        return results
    
    def full_test_process(
        self,
        metric_name: str,
        metric_code: str,
        metric_description: str,
        base_metrics: Dict,
        sample_data: Dict
    ) -> Tuple[bool, TestSuite, List[SingleTestResult], Dict]:
        """
        Complete testing process:
        1. Generate tests
        2. Validate test quality with jury
        3. Execute tests with real data
        4. Report results
        """
        
        print(f"\n{'='*70}")
        print(f"AUTOMATED TEST PROCESS STARTING")
        print(f"{'='*70}")
        print(f"📝 Metric: {metric_name}")
        
        # Step 1: Generate tests
        print(f"\n🤖 Generating unit tests...")
        test_suite = self.generate_unit_tests(
            metric_name, 
            metric_code, 
            metric_description, 
            base_metrics
        )
        
        if not test_suite:
            return False, None, [], {'error': 'Failed to generate tests'}
        
        print(f"Generated {len(test_suite.test_cases)} test cases")
        
        # Step 2: Validate test quality
        print(f"\n⚖️ Validating test quality with jury...")
        is_good_tests, feedback, quality_score = self.validate_tests_with_jury(test_suite)
        
        print(f"📊 Test Quality Score: {quality_score:.1f}/100")
        if feedback:
            print(f"⚠️ Issues found: {feedback}")
        
        # Step 3: Execute tests
        print(f"\n▶️ Executing tests with real data...")
        test_results = self.execute_tests_in_sandbox(test_suite, sample_data)
        
        # Summary
        passed = sum(1 for r in test_results if r.status == 'passed')
        failed = sum(1 for r in test_results if r.status == 'failed')
        errors = sum(1 for r in test_results if r.status == 'error')
        
        print(f"\n{'='*70}")
        print(f"📊 TEST RESULTS SUMMARY")
        print(f"{'='*70}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"📈 Success Rate: {(passed/(passed+failed+errors)*100):.1f}%" if (passed+failed+errors) > 0 else "N/A")
        
        # Print individual results
        for result in test_results:
            status_icon = "✅" if result.status == 'passed' else "❌" if result.status == 'failed' else "⚠️"
            print(f"{status_icon} {result.test_name}: {result.status}")
            if result.error_message:
                print(f"   Error: {result.error_message[:100]}")
        
        all_passed = failed == 0 and errors == 0
        
        summary = {
            'metric_name': metric_name,
            'total_tests': len(test_results),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed/(passed+failed+errors)*100) if (passed+failed+errors) > 0 else 0,
            'quality_score': quality_score,
            'all_passed': all_passed
        }
        
        return all_passed, test_suite, test_results, summary


# Example usage
def test_generator_example():
    """Example usage of test generator"""
    
    generator = LLMTestGenerator()
    
    # Example code to test
    example_code = """
def calculate_custom_metric(repo_path=None, base_metrics=None):
    '''Calculate a custom metric combining multiple base metrics'''
    if base_metrics is None:
        return 0
    
    value1 = base_metrics.get('metric1', 0)
    value2 = base_metrics.get('metric2', 0)
    
    if value2 == 0:
        return 0
    
    return (value1 / value2) * 100
"""
    
    base_metrics = {
        'metric1': 50,
        'metric2': 100,
        'metric3': 25
    }
    
    sample_data = {
        'metric1': 50,
        'metric2': 100,
        'metric3': 25
    }
    
    success, test_suite, results, summary = generator.full_test_process(
        metric_name='custom_metric',
        metric_code=example_code,
        metric_description='Test metric combining two base metrics',
        base_metrics=base_metrics,
        sample_data=sample_data
    )
    
    print(f"\n{'='*70}")
    print(f"TEST PROCESS COMPLETE" if success else "TEST PROCESS FAILED")
    print(f"{'='*70}")
    print(f"Summary: {json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    test_generator_example()
