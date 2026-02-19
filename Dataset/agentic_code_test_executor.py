"""
Agentic Code-to-Test Execution System
======================================
Complete autonomous workflow:
1. LLM Jury generates code for custom metrics
2. Test jury generates comprehensive unit tests
3. Agent executes tests with real data
4. Validates results and provides feedback
5. Auto-fixes or re-prompts on failures
"""

import os
import sys
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

# Add Dataset folder to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_jury_system import LLMJurySystem, ValidationResult
from llm_test_generator import LLMTestGenerator, TestSuite, SingleTestResult


class AgenticCodeTestExecutor:
    """
    Autonomous agent that:
    - Uses LLM jury to generate code
    - Uses LLM test generator to create tests
    - Executes tests autonomously
    - Handles failures and re-prompts
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.jury = LLMJurySystem(api_key=self.api_key)
        self.test_generator = LLMTestGenerator(api_key=self.api_key)
        self.execution_log = []
        self.max_retries = 5  # Max 5 auto-fix iterations
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = f'generated_datasets/agentic_run_{self.run_id}'
        # Create run directory
        os.makedirs(self.run_dir, exist_ok=True)
        print(f"[INFO] Run directory: {self.run_dir}")
    
    def _save_iteration(self, iteration: int, code: str, test_code: str, results: Dict):
        """Save iteration artifacts to run directory"""
        iteration_dir = Path(self.run_dir) / f'iteration_{iteration}'
        iteration_dir.mkdir(exist_ok=True)
        
        # Save code
        (iteration_dir / 'code.py').write_text(code)
        # Save tests
        (iteration_dir / 'tests.py').write_text(test_code)
        # Save results
        (iteration_dir / 'results.json').write_text(json.dumps(results, indent=2))
        
        return str(iteration_dir)
    
    def _check_test_quality(self, passed: int, failed: int, errors: int) -> Tuple[bool, str]:
        """Check if tests pass majority voting (2/3 = ok)"""
        total = passed + failed + errors
        if total == 0:
            return False, "No tests executed"
        
        # Majority voting: need at least 2/3 to pass
        required_pass = (total * 2 + 2) // 3  # Ceiling division for 2/3
        
        if passed >= required_pass:
            return True, f"✅ Tests approved: {passed}/{total} passed (need {required_pass})"
        else:
            return False, f"❌ Tests failed: {passed}/{total} passed (need {required_pass})"
    
    def log_action(self, action: str, details: Dict = None):
        """Log execution actions"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details or {}
        }
        self.execution_log.append(log_entry)
        print(f"[{timestamp}] {action}")
        if details:
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def execute_full_workflow(
        self,
        metric_description: str,
        available_metrics: Dict,
        sample_data: Dict,
        base_metrics: Dict = None,
        num_judges: int = 3,
        auto_fix: bool = True
    ) -> Dict:
        """
        Complete agentic workflow: Code → Tests → Execute → Validate
        
        Args:
            metric_description: Description of metric to generate
            available_metrics: Available base metrics
            sample_data: Real data for testing
            base_metrics: Base metrics for test generation
            num_judges: Number of jury judges
            auto_fix: Auto-fix and re-run on failures
        
        Returns:
            Comprehensive execution report
        """
        
        report = {
            'metric_description': metric_description,
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'overall_success': False,
            'execution_log': []
        }
        
        self.log_action("STARTING AGENTIC CODE-TO-TEST WORKFLOW")
        
        # ============================================================
        # STAGE 1: Code Generation with Jury
        # ============================================================
        self.log_action("STAGE 1: Code Generation", {
            'description': metric_description,
            'judges': num_judges
        })
        
        proposal, code_votes, code_summary = self.jury.full_jury_process(
            metric_description=metric_description,
            available_metrics=available_metrics,
            num_judges=num_judges
        )
        
        if not proposal:
            self.log_action("Code generation failed", {'summary': code_summary})
            report['stages']['code_generation'] = {
                'status': 'failed',
                'summary': code_summary
            }
            return report
        
        report['stages']['code_generation'] = {
            'status': 'approved',
            'metric_name': proposal.metric_name,
            'summary': code_summary,
            'votes': len(code_votes)
        }
        
        self.log_action("Code Generation Success", {
            'metric': proposal.metric_name,
            'approval': code_summary
        })
        
        # ============================================================
        # STAGE 2: Test Generation with 3 Jury Validators Each Generating Tests
        # ============================================================
        self.log_action("STAGE 2: Test Generation (3 judges)", {
            'metric': proposal.metric_name
        })
        
        # Have 3 jury members EACH generate test cases
        test_suite = self.test_generator.generate_tests_with_jury(
            metric_name=proposal.metric_name,
            metric_code=proposal.code,
            metric_description=metric_description,
            base_metrics=base_metrics or available_metrics,
            num_judges=3  # Always 3 judges for test generation
        )
        
        if not test_suite or not test_suite.test_code:
            self.log_action("Test generation failed")
            report['stages']['test_generation'] = {'status': 'failed'}
            return report
        
        # Validate test quality
        is_good_tests, feedback, quality_score = self.test_generator.validate_tests_with_jury(test_suite)
        
        report['stages']['test_generation'] = {
            'status': 'generated',
            'test_count': len(test_suite.test_cases) if test_suite.test_cases else 5,
            'quality_score': quality_score,
            'is_approved': is_good_tests
        }
        
        self.log_action("Tests Generated", {
            'test_cases': len(test_suite.test_cases) if test_suite.test_cases else 5,
            'quality_score': quality_score
        })
        
        # ============================================================
        # AUTO-FIX LOOP: Retry up to 5 times
        # ============================================================
        iteration = 0
        current_proposal = proposal
        current_test_suite = test_suite
        validation_passed = False
        
        while iteration <= self.max_retries and not validation_passed:
            iteration += 1
            self.log_action(f"STAGE 3: Test Execution (Iteration {iteration}/{self.max_retries + 1})", {
                'metric': current_proposal.metric_name
            })
            
            # Execute tests
            test_results = self.test_generator.execute_tests_in_sandbox(
                test_suite=current_test_suite,
                sample_data=sample_data
            )
            
            passed = sum(1 for r in test_results if r.status == 'passed')
            failed = sum(1 for r in test_results if r.status == 'failed')
            errors = sum(1 for r in test_results if r.status == 'error')
            total = len(test_results)
            
            # Save iteration to folder
            iter_dir = self._save_iteration(
                iteration=iteration,
                code=current_proposal.code,
                test_code=current_test_suite.test_code,
                results={
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'total': total
                }
            )
            
            self.log_action(f"Test Results - Iteration {iteration}", {
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'total': total,
                'saved_to': iter_dir
            })
            
            # Check quality with majority voting (2/3 = ok)
            is_good, quality_msg = self._check_test_quality(passed, failed, errors)
            self.log_action(quality_msg)
            
            if is_good:
                validation_passed = True
                report['overall_success'] = True
                report['stages']['test_execution'] = {
                    'status': 'executed',
                    'total_tests': total,
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'iteration': iteration
                }
                report['stages']['validation'] = {
                    'status': 'success',
                    'iteration': iteration,
                    'total_tests': total,
                    'passed': passed,
                    'run_directory': self.run_dir
                }
                self.log_action("VALIDATION SUCCESSFUL! Tests passed majority voting (2/3)")
                break
            
            # If validation failed and we can retry
            if iteration <= self.max_retries and auto_fix:
                self.log_action(f"Auto-fix attempt {iteration} - Regenerating code based on failures")
                
                # Collect failure details
                failure_details = []
                for result in test_results:
                    if result.status != 'passed':
                        failure_details.append(f"\\n- {result.test_name}: {result.error_message}")
                
                failure_summary = f"Tests failed in iteration {iteration}:\\n" + "".join(failure_details)
                
                # Create jury votes from failures - tell them what went wrong
                from llm_jury_system import JuryVote
                synthetic_votes = []
                for i in range(num_judges):
                    vote = JuryVote(
                        judge_id=f'AutoFix_Judge_{i+1}',
                        result=ValidationResult.NEEDS_REVISION,
                        reasoning=failure_summary,
                        score=40,
                        suggested_fixes=[
                            f"Only {passed}/{total} tests passed (need at least {(total * 2 + 2) // 3})",
                            "Fix the root causes of test failures",
                            "Ensure code correctly implements the required functionality"
                        ]
                    )
                    synthetic_votes.append(vote)
                
                # Revise code with detailed failure feedback
                revised_proposal = self.jury.revise_code_based_on_feedback(
                    original_proposal=current_proposal,
                    jury_votes=synthetic_votes
                )
                
                if revised_proposal:
                    current_proposal = revised_proposal
                    # Regenerate tests for revised code
                    revised_test_suite = self.test_generator.generate_unit_tests(
                        metric_name=revised_proposal.metric_name,
                        metric_code=revised_proposal.code,
                        metric_description=metric_description,
                        base_metrics=base_metrics or available_metrics
                    )
                    if revised_test_suite:
                        current_test_suite = revised_test_suite
                        self.log_action(f"Code and tests regenerated for iteration {iteration + 1}")
                    else:
                        self.log_action("Failed to regenerate tests")
                        break
                else:
                    self.log_action("Failed to revise code")
                    break
            else:
                # Max retries reached or auto-fix disabled
                if iteration > self.max_retries:
                    self.log_action(f"MAX RETRIES ({self.max_retries}) REACHED - Need human review", {
                        'passed': passed,
                        'failed': failed,
                        'errors': errors,
                        'run_dir': self.run_dir,
                        'last_status': 'iteration_' + str(iteration)
                    })
                    report['overall_success'] = False
                    report['stages']['test_execution'] = {
                        'status': 'executed',
                        'total_tests': total,
                        'passed': passed,
                        'failed': failed,
                        'errors': errors,
                        'iteration': iteration
                    }
                    report['stages']['validation'] = {
                        'status': 'failed_max_retries',
                        'iterations': iteration,
                        'last_passed': passed,
                        'last_failed': failed,
                        'run_directory': self.run_dir,
                        'note': 'Human review required. Check run directory for all iterations.'
                    }
                break
        
        # ============================================================
        # Generate Final Report
        # ============================================================
        report['execution_log'] = self.execution_log
        
        self.log_action(f"WORKFLOW COMPLETE", {
            'overall_success': report['overall_success'],
            'duration': 'N/A (see timestamps)'
        })
        
        return report
    
    def generate_report_file(
        self,
        report: Dict,
        output_dir: str = 'generated_datasets'
    ) -> str:
        """
        Save execution report to file
        Returns path to report file
        """
        
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(output_dir) / f"agentic_execution_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved: {report_file}")
        return str(report_file)


# ============================================================
# EXAMPLE USAGE
# ============================================================

def main_example():
    """Example execution"""
    
    print("\n" + "="*70)
    print("🤖 AGENTIC CODE-TO-TEST EXECUTOR - EXAMPLE")
    print("="*70)
    
    executor = AgenticCodeTestExecutor()
    
    # Define metric to generate
    metric_description = """
    Calculate 'Code Quality Index' combining:
    - Cyclomatic Complexity (lower is better)
    - Test Coverage Ratio (higher is better)
    - Bug Density per 1000 LOC (lower is better)
    
    Formula: 100 - (0.4 * normalized_complexity + 0.3 * (1 - test_coverage) + 0.3 * normalized_bug_density)
    """
    
    # Available base metrics
    available_metrics = {
        'cyclomatic_complexity': 5.2,
        'test_coverage': 0.75,
        'bugs_found': 3,
        'lines_of_code': 5000,
        'total_commits': 150,
        'code_churn': 15.5
    }
    
    # Real sample data for testing
    sample_data = {
        'cyclomatic_complexity': 5.2,
        'test_coverage': 0.75,
        'bugs_found': 3,
        'lines_of_code': 5000
    }
    
    # Execute full workflow
    report = executor.execute_full_workflow(
        metric_description=metric_description,
        available_metrics=available_metrics,
        sample_data=sample_data,
        base_metrics=available_metrics,
        num_judges=3,
        auto_fix=True
    )
    
    # Save report
    report_file = executor.generate_report_file(report)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 EXECUTION SUMMARY")
    print("="*70)
    print(json.dumps({
        'overall_success': report['overall_success'],
        'stages': report['stages'],
        'report_file': report_file
    }, indent=2))


if __name__ == "__main__":
    main_example()
