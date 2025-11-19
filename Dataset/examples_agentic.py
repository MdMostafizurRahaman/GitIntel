"""
Agentic Dataset Maker - Complete Examples
Demonstrates all features and use cases
"""

import json
import logging
from pathlib import Path
from agentic_dataset_maker import AgenticDatasetMaker, MetricsRegistry, AgentPlanner

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_interactive_simple():
    """
    Example 1: Simple Interactive Mode
    User describes what they want, agent handles the rest
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Interactive Mode (Simple)")
    print("="*70)
    
    maker = AgenticDatasetMaker()
    
    # Simulate user query
    user_query = "Create a defects4j dataset from our Java repository with code normalization"
    print(f"\nUser Query: {user_query}")
    
    # In real scenario, user would type this at prompt
    # Here we'll just parse it to show what happens
    request = maker.planner.parse_user_request(user_query)
    
    print(f"\nAgent Analysis:")
    print(f"  Dataset Type: {request.dataset_type}")
    print(f"  Processing Steps: {request.processing_steps}")
    print(f"  Is Straightforward: {request.is_straightforward}")
    print(f"  Missing Info: {request.missing_info}")
    
    if request.is_straightforward:
        print("\n✓ Agent can proceed without clarification")
    else:
        print("\n⚠ Agent would ask user for: " + ", ".join(request.missing_info))


def example_2_direct_api():
    """
    Example 2: Direct API Mode
    Programmatic creation without interaction
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Direct API Mode")
    print("="*70)
    
    maker = AgenticDatasetMaker()
    
    # Note: In real usage, you would provide actual paths
    print("\nCreating dataset directly with API...")
    print("Parameters:")
    print("  Dataset Type: defects4j")
    print("  Source: /path/to/java/repo")
    print("  Processors: code_normalizer, duplicate_remover")
    print("  Output Format: json")
    print("  Output Path: output/defects4j.json")
    
    # This would execute: (commented out to avoid errors)
    # result = maker.create_dataset_direct(
    #     dataset_type="defects4j",
    #     source="/path/to/java/repo",
    #     processing_steps=["code_normalizer", "duplicate_remover"],
    #     output_format="json",
    #     output_path="output/defects4j.json"
    # )
    
    print("\n✓ API execution would proceed automatically")


def example_3_query_parsing():
    """
    Example 3: Query Parsing and Understanding
    Shows how agent interprets various natural language queries
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Query Parsing & Interpretation")
    print("="*70)
    
    maker = AgenticDatasetMaker()
    planner = maker.planner
    
    queries = [
        "I want a defects4j dataset",
        "Create a bug fix dataset with cleaned code",
        "Generate bugs.jar with metrics and no duplicates",
        "CodeSearchNet data with text cleaning",
        "Extract Sourcerer dataset from /data with CSV format",
        "Promise metrics dataset with validation",
    ]
    
    for query in queries:
        print(f"\n{'─'*70}")
        print(f"Query: {query}")
        request = planner.parse_user_request(query)
        print(f"  Dataset Type: {request.dataset_type or '❌ Not detected'}")
        print(f"  Processors: {request.processing_steps or '(none)'}")
        print(f"  Output Format: {request.output_format}")
        print(f"  Straightforward: {'✓' if request.is_straightforward else '❌'}")
        if request.missing_info:
            print(f"  Missing Info: {', '.join(request.missing_info)}")


def example_4_metrics_registry():
    """
    Example 4: Exploring Available Metrics
    Shows what extractors and processors are available
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Metrics Registry")
    print("="*70)
    
    registry = MetricsRegistry()
    
    # Show all available metrics
    print("\n📊 Available Dataset Types & Extractors:")
    print("{")*-50)
    
    metrics = registry.get_available_metrics()
    for dtype, info in metrics.items():
        print(f"\n  {dtype}:")
        print(f"    Description: {info['description']}")
        print(f"    Extractors: {', '.join(info['extractors'])}")
        print(f"    Formats: {', '.join(info['supported_formats'])}")
    
    # Show all available processors
    print(f"\n\n⚙️  Available Processors:")
    print("{")*-50)
    processors = registry.get_available_processors()
    for proc in processors:
        print(f"  • {proc}")


def example_5_complex_processing():
    """
    Example 5: Complex Processing Pipeline
    Shows how to build multi-step processing workflows
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Complex Processing Pipeline")
    print("="*70)
    
    maker = AgenticDatasetMaker()
    
    # Scenario: User wants fully processed dataset
    query = "I need a bugs_jar dataset with validated, normalized, and deduplicated records in CSV"
    
    print(f"\nUser Request: {query}")
    
    request = maker.planner.parse_user_request(query)
    plan = maker.planner.generate_execution_plan(request)
    
    print(f"\nGenerated Execution Plan:")
    print(f"  Step 1: Extract {request.dataset_type} data")
    print(f"  Step 2: Process with pipeline:")
    for i, proc in enumerate(request.processing_steps, 1):
        print(f"    {i}. {proc}")
    print(f"  Step 3: Export to {request.output_format}")
    print(f"\nTotal Steps: {plan.step_count}")


def example_6_use_case_research():
    """
    Example 6: Use Case - Research/Benchmarking
    Create datasets for ML model training and benchmarking
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Use Case - Research/Benchmarking")
    print("="*70)
    
    print("\nScenario: Preparing datasets for ML research on bug detection\n")
    
    print("Step 1: Create training data")
    print("  python -m cli.main agent create-direct \\")
    print("    --dataset-type defects4j \\")
    print("    --source ~/projects/defects4j \\")
    print("    --processors code_normalizer,duplicate_remover \\")
    print("    --format json \\")
    print("    --output datasets/training.json")
    
    print("\nStep 2: Create validation data")
    print("  python -m cli.main agent create-direct \\")
    print("    --dataset-type bugs_jar \\")
    print("    --source ~/data/bugs.jar \\")
    print("    --processors data_validator \\")
    print("    --format json \\")
    print("    --output datasets/validation.json")
    
    print("\nStep 3: Create test data")
    print("  python -m cli.main agent create-direct \\")
    print("    --dataset-type manystubs4j \\")
    print("    --source ~/projects/many-java-repos \\")
    print("    --format json \\")
    print("    --output datasets/test.json")


def example_7_use_case_automation():
    """
    Example 7: Use Case - Pipeline Automation
    Integrate dataset creation into CI/CD pipelines
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Use Case - Pipeline Automation")
    print("="*70)
    
    print("\nScenario: Automated weekly dataset generation for analysis\n")
    
    print("Python code for automated pipeline:")
    print("""
from agentic_dataset_maker import AgenticDatasetMaker
from datetime import datetime

maker = AgenticDatasetMaker()

# Generate weekly datasets
datasets = [
    ("defects4j", "s3://datasets/java-repo"),
    ("promise", "s3://datasets/metrics.csv"),
    ("bugs_jar", "s3://datasets/bugs.jar"),
]

for dtype, source in datasets:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = maker.create_dataset_direct(
        dataset_type=dtype,
        source=source,
        processing_steps=["duplicate_remover", "data_validator"],
        output_format="json",
        output_path=f"s3://outputs/{dtype}_{timestamp}.json"
    )
    print(f"✓ Generated {dtype}: {result['total_records']} records")
    """)


def example_8_use_case_interactive():
    """
    Example 8: Use Case - Interactive Data Exploration
    Explore and understand available datasets interactively
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: Use Case - Interactive Exploration")
    print("="*70)
    
    print("\nScenario: Exploring available datasets and creating one interactively\n")
    
    print("Steps:")
    print("1. List all available datasets")
    print("   python -m cli.main agent list-all")
    
    print("\n2. Understand how agent interprets a query")
    print("   python -m cli.main agent explain --query 'defects4j with normalization'")
    
    print("\n3. Create dataset interactively")
    print("   python -m cli.main agent create")
    print("   > Enter query: Extract bug dataset with cleaned code")
    print("   > Agent asks: Select dataset type (1-7)")
    print("   > You answer: 1 (defects4j)")
    print("   > Agent asks: Enter source")
    print("   > You answer: d:\\\\GitIntel\\\\druid")
    print("   > Agent creates dataset...")


def example_9_output_inspection():
    """
    Example 9: Inspecting Output and Results
    Shows how to work with generated datasets
    """
    print("\n" + "="*70)
    print("EXAMPLE 9: Output Inspection & Analysis")
    print("="*70)
    
    print("\nAfter dataset generation, inspect results:\n")
    
    print("Load and analyze JSON dataset:")
    print("""
import json

with open('output/dataset.json') as f:
    dataset = json.load(f)

print(f"Total records: {len(dataset)}")
print(f"Fields: {list(dataset[0].keys())}")
print(f"First record: {dataset[0]}")
    """)
    
    print("\nLoad and analyze CSV dataset:")
    print("""
import pandas as pd

df = pd.read_csv('output/dataset.csv')
print(df.info())
print(df.head())
print(df.describe())
    """)


def example_10_advanced_customization():
    """
    Example 10: Advanced Customization
    Create custom processors and extend functionality
    """
    print("\n" + "="*70)
    print("EXAMPLE 10: Advanced Customization")
    print("="*70)
    
    print("\nScenario: Create custom processor for domain-specific cleaning\n")
    
    print("Python code example:")
    print("""
from processors.base_processor import BaseProcessor

class CustomBugProcessor(BaseProcessor):
    '''Custom processor for bug dataset specifics'''
    
    def process(self, records):
        processed = []
        for record in records:
            # Custom logic
            if self._is_valid_bug_record(record):
                record['severity'] = self._classify_severity(record)
                processed.append(record)
        
        self.processed_data = processed
        return processed
    
    def _is_valid_bug_record(self, record):
        return 'bug_id' in record and 'description' in record
    
    def _classify_severity(self, record):
        # Classify based on description
        desc = record.get('description', '').lower()
        if 'critical' in desc:
            return 'critical'
        elif 'major' in desc:
            return 'major'
        return 'minor'

# Use in pipeline
from processors.base_processor import ProcessingPipeline

pipeline = ProcessingPipeline()
pipeline.add_processor(CustomBugProcessor())
pipeline.add_processor(DataValidator())

result = pipeline.process(records)
    """)


def main():
    """Run all examples"""
    
    print("\n" + "="*70)
    print("🤖 AGENTIC DATASET MAKER - COMPLETE EXAMPLES")
    print("="*70)
    print("This script demonstrates all features of the agentic dataset maker")
    
    examples = [
        ("1", "Interactive Mode (Simple)", example_1_interactive_simple),
        ("2", "Direct API Mode", example_2_direct_api),
        ("3", "Query Parsing & Interpretation", example_3_query_parsing),
        ("4", "Metrics Registry", example_4_metrics_registry),
        ("5", "Complex Processing Pipeline", example_5_complex_processing),
        ("6", "Use Case: Research/Benchmarking", example_6_use_case_research),
        ("7", "Use Case: Pipeline Automation", example_7_use_case_automation),
        ("8", "Use Case: Interactive Exploration", example_8_use_case_interactive),
        ("9", "Output Inspection & Analysis", example_9_output_inspection),
        ("10", "Advanced Customization", example_10_advanced_customization),
    ]
    
    while True:
        print("\n" + "="*70)
        print("Examples:")
        for num, name, _ in examples:
            print(f"  {num}. {name}")
        print("  0. Run all examples")
        print("  q. Quit")
        
        choice = input("\nSelect example (0-10, q): ").strip().lower()
        
        if choice == 'q':
            print("\nGoodbye!")
            break
        elif choice == '0':
            for _, _, func in examples:
                func()
                input("\nPress Enter to continue...")
        else:
            for num, _, func in examples:
                if choice == num:
                    func()
                    break


if __name__ == '__main__':
    main()
