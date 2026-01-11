"""
Integration Bridge: Connect Agentic Testing to Autonomous Agent
================================================================
Integrates automated testing into the autonomous dataset agent workflow
Provides methods to:
- Use in /agent mode for autonomous test execution
- Use in /ask mode with user approval
- Store results in Neo4j if available
- Export test reports to generated_datasets
"""

import os
import sys
import json
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

# Add Dataset folder to path
sys.path.insert(0, str(Path(__file__).parent))

from agentic_code_test_executor import AgenticCodeTestExecutor


class TestingIntegrationBridge:
    """
    Bridge between autonomous agent and testing system
    Provides integration points for /ask and /agent modes
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.executor = AgenticCodeTestExecutor(api_key=self.api_key)
        self.test_history = []
        self.neo4j_handler = None  # Optional Neo4j integration
    
    def set_neo4j_handler(self, handler):
        """Set Neo4j handler for optional storage"""
        self.neo4j_handler = handler
    
    def ask_mode_workflow(
        self,
        metric_description: str,
        available_metrics: Dict,
        sample_data: Dict,
        num_judges: int = 3
    ) -> Dict:
        """
        /ask mode: Generate code and tests, wait for user approval
        User can approve/reject each stage
        """
        
        print("\n" + "="*70)
        print("📋 ASK MODE - CODE & TEST GENERATION")
        print("="*70)
        print(f"Metric: {metric_description}\n")
        
        # Generate code with jury
        print("Step 1: Generating code with jury...\n")
        proposal, code_votes, code_summary = self.executor.jury.full_jury_process(
            metric_description=metric_description,
            available_metrics=available_metrics,
            num_judges=num_judges
        )
        
        if not proposal:
            return {'status': 'failed', 'stage': 'code_generation'}
        
        print(f"\n{code_summary}")
        print(f"\nGenerated Code:\n{proposal.code}\n")
        
        # Ask for approval
        approval = input("👤 Approve this code? (yes/no): ").lower().strip()
        if approval != 'yes':
            return {'status': 'rejected', 'stage': 'code_generation'}
        
        # Generate tests
        print("\nStep 2: Generating unit tests...\n")
        test_suite = self.executor.test_generator.generate_unit_tests(
            metric_name=proposal.metric_name,
            metric_code=proposal.code,
            metric_description=metric_description,
            base_metrics=available_metrics
        )
        
        if not test_suite:
            return {'status': 'failed', 'stage': 'test_generation'}
        
        print(f"Generated {len(test_suite.test_cases)} test cases:")
        for i, test_case in enumerate(test_suite.test_cases, 1):
            print(f"  {i}. {test_case.get('name', 'test_' + str(i))}: {test_case.get('description', '')}")
        
        print(f"\nTest Code:\n{test_suite.test_code}\n")
        
        # Ask for approval
        approval = input("👤 Approve these tests? (yes/no): ").lower().strip()
        if approval != 'yes':
            return {'status': 'rejected', 'stage': 'test_generation'}
        
        # Execute tests
        print("\nStep 3: Executing tests...\n")
        test_results = self.executor.test_generator.execute_tests_in_sandbox(
            test_suite=test_suite,
            sample_data=sample_data
        )
        
        passed = sum(1 for r in test_results if r.status == 'passed')
        failed = sum(1 for r in test_results if r.status == 'failed')
        
        print(f"\nTest Results: {passed} passed, {failed} failed")
        
        # Store and return
        execution_record = {
            'mode': 'ask',
            'timestamp': datetime.now().isoformat(),
            'metric_name': proposal.metric_name,
            'code': proposal.code,
            'test_count': len(test_suite.test_cases),
            'test_results': {
                'passed': passed,
                'failed': failed,
                'success_rate': (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
            },
            'status': 'approved' if failed == 0 else 'needs_revision'
        }
        
        self.test_history.append(execution_record)
        
        # Store in Neo4j if available
        if self.neo4j_handler:
            self.neo4j_handler.store_custom_metric(
                metric_name=proposal.metric_name,
                metric_code=proposal.code,
                test_results=execution_record
            )
        
        return execution_record
    
    def agent_mode_workflow(
        self,
        metric_description: str,
        available_metrics: Dict,
        sample_data: Dict,
        auto_fix: bool = True,
        num_judges: int = 3
    ) -> Dict:
        """
        /agent mode: Autonomously execute full workflow
        Code → Tests → Execution → Auto-fix if needed
        No user approval required
        """
        
        print("\n" + "="*70)
        print("🤖 AGENT MODE - AUTONOMOUS EXECUTION")
        print("="*70)
        
        # Execute full workflow
        report = self.executor.execute_full_workflow(
            metric_description=metric_description,
            available_metrics=available_metrics,
            sample_data=sample_data,
            base_metrics=available_metrics,
            num_judges=num_judges,
            auto_fix=auto_fix
        )
        
        # Store execution record
        execution_record = {
            'mode': 'agent',
            'timestamp': report['timestamp'],
            'overall_success': report['overall_success'],
            'stages': report['stages'],
            'metric_description': metric_description
        }
        
        self.test_history.append(execution_record)
        
        # Store in Neo4j if available
        if self.neo4j_handler and report['overall_success']:
            code_stage = report['stages'].get('code_generation', {})
            test_stage = report['stages'].get('test_execution', {})
            
            if code_stage.get('metric_name'):
                self.neo4j_handler.store_custom_metric(
                    metric_name=code_stage['metric_name'],
                    metric_description=metric_description,
                    test_results=test_stage
                )
        
        # Generate and save report
        report_file = self.executor.generate_report_file(report)
        execution_record['report_file'] = report_file
        
        return execution_record
    
    def process_custom_formula_request(
        self,
        formula_description: str,
        mode: str = 'agent',
        auto_approve: bool = False
    ) -> Dict:
        """
        Process a custom formula/metric request from user
        Handles both /ask and /agent modes
        """
        
        # Placeholder metrics (would come from repo analysis)
        available_metrics = {
            'cyclomatic_complexity': 5.2,
            'test_coverage': 0.75,
            'bugs_per_kloc': 2.3,
            'code_churn_ratio': 0.15,
            'duplicate_lines_percent': 5.0,
            'comment_ratio': 0.25
        }
        
        sample_data = available_metrics.copy()
        
        if mode == 'ask':
            return self.ask_mode_workflow(
                metric_description=formula_description,
                available_metrics=available_metrics,
                sample_data=sample_data,
                num_judges=3
            )
        
        elif mode == 'agent':
            return self.agent_mode_workflow(
                metric_description=formula_description,
                available_metrics=available_metrics,
                sample_data=sample_data,
                auto_fix=True,
                num_judges=3
            )
        
        else:
            return {'status': 'error', 'message': f'Unknown mode: {mode}'}
    
    def get_test_history(self, limit: int = 10) -> List[Dict]:
        """Get recent test execution history"""
        return self.test_history[-limit:]
    
    def export_test_reports(self, output_dir: str = 'generated_datasets') -> str:
        """Export all test history to file"""
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        
        report_file = Path(output_dir) / f"test_execution_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_executions': len(self.test_history),
                'executions': self.test_history
            }, f, indent=2)
        
        print(f"📄 Test history exported: {report_file}")
        return str(report_file)


# ============================================================
# INTEGRATION WITH AUTONOMOUS AGENT
# ============================================================

def integrate_with_autonomous_agent():
    """
    Example: Integrate with existing autonomous_agent.py
    Call this from autonomous agent when user requests custom formula
    """
    
    print("""
    Integration with Autonomous Agent:
    ==================================
    
    In autonomous_agent.py, add this to handle /agent commands:
    
    ```python
    from agentic_testing_integration import TestingIntegrationBridge
    
    class AutonomousDatasetAgent:
        def __init__(self, ...):
            # ... existing code ...
            self.testing_bridge = TestingIntegrationBridge()
        
        def handle_custom_formula(self, formula_description):
            '''Handle /agent custom formula requests'''
            result = self.testing_bridge.process_custom_formula_request(
                formula_description=formula_description,
                mode='agent',
                auto_approve=True
            )
            return result
        
        def handle_ask_custom_formula(self, formula_description):
            '''Handle /ask custom formula requests'''
            result = self.testing_bridge.process_custom_formula_request(
                formula_description=formula_description,
                mode='ask',
                auto_approve=False
            )
            return result
    ```
    """)


# ============================================================
# EXAMPLE USAGE
# ============================================================

def example_usage():
    """Demonstrate the integration"""
    
    print("\n" + "="*70)
    print("🔗 TESTING INTEGRATION BRIDGE - EXAMPLE")
    print("="*70)
    
    bridge = TestingIntegrationBridge()
    
    # Example 1: /agent mode (autonomous)
    print("\n\n--- Example 1: /agent mode (Autonomous) ---\n")
    
    result = bridge.process_custom_formula_request(
        formula_description="""
        Create a 'Performance Health Score' metric that:
        - Rewards low cyclomatic complexity
        - Rewards high test coverage
        - Penalizes high bug density
        - Combines into 0-100 scale
        """,
        mode='agent'
    )
    
    print(f"\nAgent Mode Result:")
    print(json.dumps({
        'overall_success': result.get('overall_success'),
        'timestamp': result.get('timestamp')
    }, indent=2))
    
    # Example 2: Export test history
    print("\n\n--- Example 2: Export Test History ---\n")
    history_file = bridge.export_test_reports()
    print(f"Exported to: {history_file}")


if __name__ == "__main__":
    example_usage()
