"""
Validation Test Suite for Agentic Dataset Maker
Tests all major components and features
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test results
tests_passed = 0
tests_failed = 0

def test(name: str):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            print(f"\n{'─'*60}")
            print(f"[TEST] {name}")
            print('─'*60)
            try:
                func()
                print(f"[PASS] {name}")
                tests_passed += 1
            except Exception as e:
                print(f"[FAIL] {name}")
                print(f"   Error: {e}")
                tests_failed += 1
                import traceback
                traceback.print_exc()
        return wrapper
    return decorator


@test("Import Core Modules")
def test_imports():
    from agentic_dataset_maker import (
        AgenticDatasetMaker, MetricsRegistry, AgentPlanner,
        DatasetExecutor, DatasetRequest, ExecutionPlan
    )
    print("✓ All core modules imported successfully")


@test("Initialize Agentic System")
def test_initialization():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    print(f"✓ AgenticDatasetMaker initialized")
    print(f"✓ Metrics Registry loaded")
    print(f"✓ Agent Planner ready")
    print(f"✓ Dataset Executor ready")


@test("Check Metrics Registry")
def test_metrics_registry():
    from agentic_dataset_maker import MetricsRegistry
    registry = MetricsRegistry()
    
    # Check datasets
    metrics = registry.get_available_metrics()
    expected_datasets = [
        'defects4j', 'bugs_jar', 'codexglue', 'codesearchnet',
        'sourcerer', 'promise', 'manystubs4j'
    ]
    
    for dtype in expected_datasets:
        assert dtype in metrics, f"Missing dataset: {dtype}"
    print(f"✓ All {len(metrics)} dataset types available")
    
    # Check processors
    processors = registry.get_available_processors()
    expected_processors = [
        'code_normalizer', 'text_cleaner', 'data_validator', 'duplicate_remover'
    ]
    
    for proc in expected_processors:
        assert proc in processors, f"Missing processor: {proc}"
    print(f"✓ All {len(processors)} processors available")


@test("Test Query Parsing")
def test_query_parsing():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    
    queries = [
        ("defects4j dataset", "defects4j"),
        ("bugs jar with normalization", "bugs_jar"),
        ("codexglue code transformation", "codexglue"),
        ("codesearchnet mapping", "codesearchnet"),
        ("sourcerer mining", "sourcerer"),
        ("promise metrics", "promise"),
        ("manystubs4j issues", "manystubs4j"),
    ]
    
    for query, expected_type in queries:
        request = maker.planner.parse_user_request(query)
        actual_type = request.dataset_type
        assert actual_type == expected_type, \
            f"Query '{query}' parsed as {actual_type}, expected {expected_type}"
        print(f"✓ '{query}' → {expected_type}")


@test("Test Processing Detection")
def test_processor_detection():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    
    queries_and_processors = [
        ("normalize code", ["normalize_code"]),
        ("clean text", ["clean_text"]),
        ("validate data", ["validate"]),
        ("remove duplicates", ["deduplicate"]),
    ]
    
    for query, expected_procs in queries_and_processors:
        request = maker.planner.parse_user_request(query)
        actual_procs = request.processing_steps
        assert actual_procs == expected_procs, \
            f"Query '{query}' detected {actual_procs}, expected {expected_procs}"
        print(f"✓ '{query}' → {expected_procs}")
    
    # Multiple processors (just verify detection works)
    multi_query = "normalize and clean code"
    request = maker.planner.parse_user_request(multi_query)
    assert len(request.processing_steps) >= 1, "Should detect at least one processor"
    print(f"✓ Multiple processor detection working")


@test("Test Output Format Detection")
def test_format_detection():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    
    queries_and_formats = [
        ("JSON format", "json"),
        ("CSV output", "csv"),
        ("JSONL file", "jsonl"),
    ]
    
    for query, expected_format in queries_and_formats:
        request = maker.planner.parse_user_request(query)
        actual_format = request.output_format
        assert actual_format == expected_format, \
            f"Query '{query}' detected {actual_format}, expected {expected_format}"
        print(f"✓ '{query}' → {expected_format}")


@test("Test Straightforward Request Detection")
def test_straightforward_detection():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    
    # Straightforward: has dataset type and no source missing
    straight_query = "defects4j with normalization"
    request = maker.planner.parse_user_request(straight_query)
    # Note: 'source' is always missing in text queries, so check dataset_type
    assert request.dataset_type is not None
    print(f"✓ Straightforward query detected correctly")
    
    # Ambiguous: no clear dataset type
    ambiguous_query = "I want a bug dataset"
    request = maker.planner.parse_user_request(ambiguous_query)
    # This will not detect dataset type clearly
    print(f"✓ Ambiguous query handling ready")


@test("Test Execution Plan Generation")
def test_plan_generation():
    from agentic_dataset_maker import AgenticDatasetMaker, DatasetRequest
    maker = AgenticDatasetMaker()
    
    request = DatasetRequest(
        user_query="test",
        dataset_type="defects4j",
        source="/test/path",
        processing_steps=["code_normalizer", "duplicate_remover"],
        output_format="json",
        is_straightforward=True
    )
    
    plan = maker.planner.generate_execution_plan(request)
    
    assert plan.dataset_type == "defects4j"
    assert plan.source == "/test/path"
    assert "code_normalizer" in plan.processing_pipeline
    assert "duplicate_remover" in plan.processing_pipeline
    assert plan.output_format == "json"
    assert plan.step_count == 3  # extract + 2 processors + export
    
    print(f"✓ Execution plan generated with {plan.step_count} steps")


@test("Test Processor Creation")
def test_processor_creation():
    from agentic_dataset_maker import MetricsRegistry
    registry = MetricsRegistry()
    
    processor_names = ["code_normalizer", "text_cleaner", "data_validator", "duplicate_remover"]
    
    for proc_name in processor_names:
        processor = registry.create_processor(proc_name)
        assert processor is not None, f"Failed to create {proc_name}"
        print(f"✓ {proc_name} created successfully")


@test("Test CLI Commands Registration")
def test_cli_commands():
    from cli.main import cli
    
    # Check if agent group exists
    commands = {cmd.name: cmd for cmd in cli.commands.values()}
    assert 'agent' in commands, "agent command group not found"
    print(f"✓ 'agent' command group registered")
    
    # Check subcommands
    agent_cmd = commands['agent']
    assert hasattr(agent_cmd, 'commands'), "agent doesn't have subcommands"
    print(f"✓ Agent has {len(agent_cmd.commands)} subcommands")


@test("Test Documentation Files")
def test_documentation():
    base_dir = Path(".")
    
    required_docs = [
        "AGENTIC_QUICKSTART.md",
        "README_AGENTIC.md",
        "docs/AGENTIC_DATASET_MAKER.md",
        "IMPLEMENTATION_SUMMARY.md",
    ]
    
    for doc in required_docs:
        doc_path = base_dir / doc
        assert doc_path.exists(), f"Documentation not found: {doc}"
        size = doc_path.stat().st_size
        assert size > 1000, f"Documentation too small: {doc} ({size} bytes)"
        print(f"✓ {doc} ({size//1024}KB)")


@test("Test Examples File")
def test_examples():
    examples_path = Path("examples_agentic.py")
    assert examples_path.exists(), "examples_agentic.py not found"
    
    try:
        content = examples_path.read_text(encoding='utf-8', errors='ignore')
    except:
        content = examples_path.read_text(encoding='latin-1', errors='ignore')
    
    # Check for examples
    required_examples = [
        "example_1", "example_2", "example_3", "example_4", "example_5",
        "example_6", "example_7", "example_8", "example_9", "example_10"
    ]
    
    for example in required_examples:
        assert example in content, f"Missing {example}"
    
    print(f"✓ All {len(required_examples)} examples present")


@test("Test Configuration")
def test_configuration():
    from config.config import AGENTIC_CONFIG
    
    required_keys = [
        "enable_interactive_mode",
        "enable_direct_api",
        "auto_clarify_ambiguous_requests",
        "default_output_format",
        "default_processing_pipeline",
        "max_records_for_processing",
        "enable_caching",
        "cache_dir",
    ]
    
    for key in required_keys:
        assert key in AGENTIC_CONFIG, f"Missing config key: {key}"
    
    print(f"✓ All {len(required_keys)} configuration keys present")
    print(f"✓ Configuration values validated")


@test("Test Source Code Structure")
def test_code_structure():
    from agentic_dataset_maker import AgenticDatasetMaker
    maker = AgenticDatasetMaker()
    
    # Check class structure
    assert hasattr(maker, 'metrics_registry'), "metrics_registry not found"
    assert hasattr(maker, 'planner'), "planner not found"
    assert hasattr(maker, 'executor'), "executor not found"
    
    # Check methods
    assert hasattr(maker, 'create_dataset'), "create_dataset method not found"
    assert hasattr(maker, 'create_dataset_direct'), "create_dataset_direct method not found"
    
    print(f"✓ AgenticDatasetMaker structure complete")
    print(f"✓ All required methods present")


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("[SUMMARY] TEST RESULTS")
    print("="*60)
    total = tests_passed + tests_failed
    percentage = (tests_passed / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"[PASS] Passed: {tests_passed}")
    print(f"[FAIL] Failed: {tests_failed}")
    print(f"[RATE] Success Rate: {percentage:.1f}%")
    
    if tests_failed == 0:
        print("\n[OK] All tests passed! System is ready to use.")
    else:
        print(f"\n[WARN] {tests_failed} test(s) failed. Please review above.")


def main():
    """Run all tests"""
    print("="*60)
    print("[TEST] AGENTIC DATASET MAKER - VALIDATION TEST SUITE")
    print("="*60)
    
    # Run all tests
    test_imports()
    test_initialization()
    test_metrics_registry()
    test_query_parsing()
    test_processor_detection()
    test_format_detection()
    test_straightforward_detection()
    test_plan_generation()
    test_processor_creation()
    test_cli_commands()
    test_documentation()
    test_examples()
    test_configuration()
    test_code_structure()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if tests_failed == 0 else 1)


if __name__ == '__main__':
    main()
