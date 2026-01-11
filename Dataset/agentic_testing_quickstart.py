#!/usr/bin/env python3
"""
Quick Start Example: Agentic Code-to-Test System
=================================================
Complete working example showing all components in action

Run this script to see the system in action:
  python agentic_testing_quickstart.py
"""

import os
import sys
import json
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded from .env")
except ImportError:
    print("[INFO] python-dotenv not installed, using system environment variables")

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from agentic_code_test_executor import AgenticCodeTestExecutor
from agentic_testing_integration import TestingIntegrationBridge


def example_1_full_workflow():
    """Example 1: Complete autonomous workflow"""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: FULL AGENTIC WORKFLOW (Code → Tests → Execution)")
    print("="*80)
    
    executor = AgenticCodeTestExecutor()
    
    # Define a custom metric to generate
    metric_description = """
    Calculate a 'Developer Productivity Score' that combines:
    - Commits per week (higher is better, shows activity)
    - Code review speed (lower is better, measured in days)
    - Bug fix rate (higher is better, percentage fixed/introduced)
    
    Weight: 40% activity + 30% review speed + 30% bug fixes
    Output range: 0-100 where 100 is excellent productivity
    """
    
    # Available metrics in the repo
    available_metrics = {
        'total_commits': 150,
        'weeks_active': 26,
        'avg_review_days': 2.5,
        'bugs_introduced': 12,
        'bugs_fixed': 10,
        'total_lines_changed': 15000
    }
    
    # Real sample data for testing
    sample_data = {
        'total_commits': 150,
        'weeks_active': 26,
        'avg_review_days': 2.5,
        'bugs_introduced': 12,
        'bugs_fixed': 10
    }
    
    # Execute full workflow
    print("\n📋 Metric Description:")
    print(metric_description)
    
    print("\n📊 Available Metrics:")
    for key, value in available_metrics.items():
        print(f"  - {key}: {value}")
    
    # Run the workflow
    report = executor.execute_full_workflow(
        metric_description=metric_description,
        available_metrics=available_metrics,
        sample_data=sample_data,
        num_judges=3,
        auto_fix=True
    )
    
    # Display summary
    print("\n" + "="*80)
    print("WORKFLOW RESULT SUMMARY")
    print("="*80)
    print(f"Overall Success: {'✅ YES' if report['overall_success'] else '❌ NO'}")
    print(f"Timestamp: {report['timestamp']}")
    print("\nStage Results:")
    
    for stage_name, stage_result in report['stages'].items():
        status = stage_result.get('status', 'unknown')
        status_icon = "✅" if status == 'success' or status == 'approved' or status == 'generated' else "❌"
        print(f"\n{status_icon} {stage_name.upper()}:")
        
        # Print relevant details
        if stage_name == 'code_generation':
            print(f"    Metric: {stage_result.get('metric_name', 'N/A')}")
            print(f"    Judges: {stage_result.get('votes', 'N/A')}")
            print(f"    Summary: {stage_result.get('summary', '')[:60]}...")
        
        elif stage_name == 'test_generation':
            print(f"    Test Count: {stage_result.get('test_count', 0)}")
            print(f"    Quality Score: {stage_result.get('quality_score', 0):.1f}/100")
            print(f"    Approved: {'Yes' if stage_result.get('is_approved') else 'No'}")
        
        elif stage_name == 'test_execution':
            print(f"    Total Tests: {stage_result.get('total_tests', 0)}")
            print(f"    Passed: {stage_result.get('passed', 0)}")
            print(f"    Failed: {stage_result.get('failed', 0)}")
            print(f"    Errors: {stage_result.get('errors', 0)}")
            print(f"    Success Rate: {stage_result.get('success_rate', 0):.1f}%")
    
    # Save and show report location
    if report['overall_success']:
        print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️ WORKFLOW COMPLETED WITH ISSUES (see stage results)")
    
    return report


def example_2_ask_mode():
    """Example 2: Interactive /ask mode with user approval"""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: ASK MODE (Interactive with User Approval)")
    print("="*80)
    
    bridge = TestingIntegrationBridge()
    
    # Simulate user input for demonstration
    print("\n📋 Simulating user request:")
    formula_description = """
    Create a 'Code Maintainability Index' that scores how easy code is to maintain:
    - Lower complexity = higher score
    - Higher test coverage = higher score
    - Lower duplication = higher score
    - Output: 0-100, where 80+ is highly maintainable
    """
    print(f"Formula: {formula_description}")
    
    # In real usage, this would prompt for user input
    # For now, we'll do agent mode to avoid interactive input
    print("\n(In real usage, this would ask for approval at each stage)")
    print("Running in agent mode instead for demonstration...\n")
    
    # Use agent mode instead
    result = bridge.process_custom_formula_request(
        formula_description=formula_description,
        mode='agent'
    )
    
    print("\n" + "="*80)
    print("ASK MODE RESULT")
    print("="*80)
    print(f"Status: {result.get('overall_success')}")
    print(f"Stages: {result.get('stages')}")
    
    return result


def example_3_error_recovery():
    """Example 3: Auto-fix when tests fail"""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: AUTO-FIX WITH FAILING TESTS")
    print("="*80)
    
    executor = AgenticCodeTestExecutor()
    
    # Request a metric that might have edge cases (to trigger potential failures)
    metric_description = """
    Calculate 'Division-based Risk Score' using division operations:
    - bugs_found / lines_of_code * 100
    - complexity_score / team_size
    This demonstrates edge cases like division by zero
    """
    
    available_metrics = {
        'bugs_found': 5,
        'lines_of_code': 10000,
        'complexity_score': 45,
        'team_size': 5
    }
    
    sample_data = available_metrics.copy()
    
    print("\n📋 Requesting metric that might have edge cases...")
    print(f"Metric: {metric_description}")
    
    print("\n⚙️ Running with auto-fix enabled (max 2 retries)...")
    
    report = executor.execute_full_workflow(
        metric_description=metric_description,
        available_metrics=available_metrics,
        sample_data=sample_data,
        num_judges=3,
        auto_fix=True  # Enable auto-fix
    )
    
    print("\n" + "="*80)
    print("AUTO-FIX RESULT")
    print("="*80)
    
    if report['overall_success']:
        print("✅ Auto-fix successfully resolved test failures!")
    else:
        print("⚠️ Could not resolve all issues even with auto-fix")
    
    stages_with_auto_fix = [s for s in report['stages'].keys() if 'auto_fix' in s]
    if stages_with_auto_fix:
        print(f"Auto-fix attempts: {stages_with_auto_fix}")
    
    return report


def example_4_metrics_comparison():
    """Example 4: Compare multiple metrics side-by-side"""
    
    print("\n" + "="*80)
    print("EXAMPLE 4: MULTIPLE METRICS COMPARISON")
    print("="*80)
    
    bridge = TestingIntegrationBridge()
    
    metrics_to_generate = [
        {
            'name': 'Bug Density',
            'description': 'Bugs per 1000 lines of code'
        },
        {
            'name': 'Code Churn',
            'description': 'Percentage of files changed per sprint'
        },
        {
            'name': 'Test Coverage Quality',
            'description': 'Combination of coverage percentage and assertion density'
        }
    ]
    
    print("\n📊 Generating 3 different metrics...\n")
    
    results = []
    for metric in metrics_to_generate:
        print(f"\n▶️ Generating: {metric['name']}")
        print(f"   Description: {metric['description']}")
        
        result = bridge.process_custom_formula_request(
            formula_description=metric['description'],
            mode='agent'
        )
        
        results.append({
            'name': metric['name'],
            'success': result.get('overall_success', False),
            'timestamp': result.get('timestamp', 'N/A')
        })
    
    # Summary table
    print("\n" + "="*80)
    print("METRICS GENERATION SUMMARY")
    print("="*80)
    print(f"{'Metric Name':<25} {'Status':<15} {'Timestamp':<20}")
    print("-" * 60)
    
    for result in results:
        status = "✅ Success" if result['success'] else "❌ Failed"
        print(f"{result['name']:<25} {status:<15} {result['timestamp']:<20}")
    
    print(f"\nTotal: {len([r for r in results if r['success']])}/{len(results)} successful")
    
    return results


def example_5_export_and_report():
    """Example 5: Export test history and generate reports"""
    
    print("\n" + "="*80)
    print("EXAMPLE 5: EXPORT TEST HISTORY")
    print("="*80)
    
    bridge = TestingIntegrationBridge()
    
    # Generate a couple of metrics first
    print("\n📈 Generating sample metrics for export...\n")
    
    bridge.process_custom_formula_request(
        formula_description="Basic quality metric",
        mode='agent'
    )
    
    bridge.process_custom_formula_request(
        formula_description="Performance-based score",
        mode='agent'
    )
    
    # Show test history
    print("\n📊 Test Execution History:")
    history = bridge.get_test_history(limit=10)
    
    for i, entry in enumerate(history, 1):
        mode = entry.get('mode', 'unknown')
        status = entry.get('overall_success', entry.get('status', 'unknown'))
        timestamp = entry.get('timestamp', 'N/A')
        
        print(f"\n{i}. Mode: {mode.upper()}")
        print(f"   Status: {'✅ Success' if status else '❌ Failed'}")
        print(f"   Timestamp: {timestamp}")
    
    # Export to file
    print("\n\n💾 Exporting test history to file...")
    export_file = bridge.export_test_reports()
    print(f"✅ Exported to: {export_file}")
    
    return history


def main():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("🚀 AGENTIC CODE-TO-TEST SYSTEM - QUICK START EXAMPLES")
    print("="*80)
    
    print("""
This script demonstrates the automated testing system with:

1. Full Workflow: Code generation → Tests → Execution
2. Ask Mode: Interactive with user approvals
3. Error Recovery: Auto-fix when tests fail
4. Comparison: Generate multiple metrics
5. Export: Save history and reports

Select which example(s) to run:
  a) Run example 1 (Full Workflow) - RECOMMENDED
  b) Run example 2 (Ask Mode)
  c) Run example 3 (Auto-fix)
  d) Run example 4 (Multiple Metrics)
  e) Run example 5 (Export Reports)
  f) Run all examples
  q) Quit

Note: Examples use LLM API, which requires:
  - Google API Key set (GOOGLE_API_KEY environment variable)
  - Internet connection
  - API quota available
    """)
    
    choice = input("\nSelect option (a/b/c/d/e/f/q): ").strip().lower()
    
    examples = {
        'a': ('Example 1 - Full Workflow', example_1_full_workflow),
        'b': ('Example 2 - Ask Mode', example_2_ask_mode),
        'c': ('Example 3 - Error Recovery', example_3_error_recovery),
        'd': ('Example 4 - Multiple Metrics', example_4_metrics_comparison),
        'e': ('Example 5 - Export Reports', example_5_export_and_report),
    }
    
    if choice == 'f':
        # Run all
        for name, example_func in examples.values():
            try:
                example_func()
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
                import traceback
                traceback.print_exc()
    
    elif choice in examples:
        name, example_func = examples[choice]
        try:
            print(f"\n🎯 Running: {name}\n")
            example_func()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice != 'q':
        print("❌ Invalid option")
    
    print("\n" + "="*80)
    print("✅ Examples completed!")
    print("="*80)
    print("""
Next Steps:
1. Review AGENTIC_TESTING_GUIDE.md for detailed documentation
2. Integrate into autonomous_agent.py (see guide for examples)
3. Check generated_datasets/ for execution reports
4. Monitor test history with bridge.get_test_history()

Documentation: AGENTIC_TESTING_GUIDE.md
Integration Guide: agentic_testing_integration.py
    """)


if __name__ == "__main__":
    main()
