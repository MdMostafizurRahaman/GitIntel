"""
Agentic Dataset Maker
An intelligent system that creates datasets dynamically based on user requests.
Uses LLM to understand user intent, determines required metrics/functions,
and orchestrates the dataset generation process.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import inspect

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.config import DATASET_CONFIGS, PROCESSING_CONFIG
from extractors.factory import create_extractor, SUPPORTED_DATASETS, validate_source
from processors.base_processor import (
    ProcessingPipeline, CodeNormalizer, TextCleaner,
    DataValidator, DuplicateRemover, BaseProcessor
)
from extractors.base_extractor import BaseExtractor
from utils.helpers import batch_list


@dataclass
class DatasetRequest:
    """Represents a user's dataset request"""
    user_query: str
    dataset_type: Optional[str] = None
    source: Optional[str] = None
    processing_steps: List[str] = None
    output_format: str = "json"
    output_path: Optional[str] = None
    additional_params: Dict = None
    is_straightforward: bool = False
    missing_info: List[str] = None

    def __post_init__(self):
        if self.processing_steps is None:
            self.processing_steps = []
        if self.additional_params is None:
            self.additional_params = {}
        if self.missing_info is None:
            self.missing_info = []


@dataclass
class ExecutionPlan:
    """Represents the execution plan for dataset generation"""
    dataset_type: str
    source: str
    extraction_config: Dict
    processing_pipeline: List[str]
    output_format: str
    output_path: str
    parameters: Dict
    step_count: int
    estimated_records: int = 0


class MetricsRegistry:
    """Registry of available metrics and extraction functions"""

    def __init__(self):
        self.metrics = self._load_metrics()
        self.processors = self._load_processors()

    def _load_metrics(self) -> Dict[str, Dict]:
        """Load all available metrics from extractors"""
        metrics = {}

        # Metrics from Defects4J
        metrics['defects4j'] = {
            'extractors': [
                'buggy_code', 'fixed_code', 'bug_description',
                'commit_hash', 'bug_id', 'project'
            ],
            'description': 'Real bugs from Java projects',
            'supported_formats': ['json', 'csv'],
        }

        # Metrics from Bugs.jar
        metrics['bugs_jar'] = {
            'extractors': [
                'class_info', 'bug_location', 'test_cases',
                'fix_info', 'metrics'
            ],
            'description': 'Large-scale Java bug dataset with metrics',
            'supported_formats': ['json', 'csv'],
        }

        # Metrics from CodeXGLUE
        metrics['codexglue'] = {
            'extractors': [
                'code_snippet', 'target_code', 'complexity',
                'language', 'description'
            ],
            'description': 'Code-to-code transformation dataset',
            'supported_formats': ['json', 'csv'],
        }

        # Metrics from CodeSearchNet
        metrics['codesearchnet'] = {
            'extractors': [
                'code', 'documentation', 'tokens',
                'language', 'docstring'
            ],
            'description': 'Code-to-documentation mapping',
            'supported_formats': ['json', 'csv'],
        }

        # Metrics from Sourcerer
        metrics['sourcerer'] = {
            'extractors': [
                'file_structure', 'dependencies', 'metrics',
                'project_info', 'language'
            ],
            'description': 'Large-scale source code mining',
            'supported_formats': ['json', 'csv'],
        }

        # Metrics from PROMISE
        metrics['promise'] = {
            'extractors': [
                'software_metrics', 'defect_labels',
                'project_info', 'version_info'
            ],
            'description': 'Software metrics for defect prediction',
            'supported_formats': ['csv', 'json'],
        }

        # Metrics from ManySStuBs4J
        metrics['manystubs4j'] = {
            'extractors': [
                'issue_id', 'commit_hash', 'file_changes',
                'description', 'severity'
            ],
            'description': 'Large-scale Java bug dataset',
            'supported_formats': ['json', 'csv'],
        }

        return metrics

    def _load_processors(self) -> Dict[str, type]:
        """Load all available processors"""
        return {
            'code_normalizer': CodeNormalizer,
            'text_cleaner': TextCleaner,
            'data_validator': DataValidator,
            'duplicate_remover': DuplicateRemover,
        }

    def get_available_metrics(self, dataset_type: Optional[str] = None) -> Dict:
        """Get available metrics for a dataset type or all"""
        if dataset_type:
            return self.metrics.get(dataset_type, {})
        return self.metrics

    def get_available_processors(self) -> List[str]:
        """Get list of available processors"""
        return list(self.processors.keys())

    def create_processor(self, processor_name: str, config: Optional[Dict] = None) -> Optional[BaseProcessor]:
        """Create a processor instance by name"""
        processor_class = self.processors.get(processor_name.lower())
        if processor_class:
            return processor_class(config)
        return None


class AgentPlanner:
    """LLM-based agent that understands user intent and creates execution plans"""

    def __init__(self, metrics_registry: MetricsRegistry):
        self.registry = metrics_registry
        self.supported_datasets = list(SUPPORTED_DATASETS.keys())

    def parse_user_request(self, user_query: str) -> DatasetRequest:
        """
        Parse user query to extract intent, dataset type, and requirements.
        Uses keyword matching and simple NLP to understand the request.
        """
        logger.info(f"Parsing user request: {user_query}")

        request = DatasetRequest(user_query=user_query)
        query_lower = user_query.lower()

        # Detect dataset type from keywords
        dataset_keywords = {
            'defects4j': ['defects4j', 'bug fix', 'buggy', 'fixed'],
            'bugs_jar': ['bugs.jar', 'bugs jar', 'java bug'],
            'codexglue': ['codexglue', 'code transformation', 'source target'],
            'codesearchnet': ['codesearchnet', 'code search', 'documentation'],
            'sourcerer': ['sourcerer', 'code mining', 'source code'],
            'promise': ['promise', 'metrics', 'defect prediction'],
            'manystubs4j': ['manystubs', 'java issue'],
        }

        for dataset_type, keywords in dataset_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                request.dataset_type = dataset_type
                break

        # Detect source from common patterns
        if 'github' in query_lower or 'repository' in query_lower:
            request.missing_info.append('source')
        elif 'file' in query_lower or 'path' in query_lower:
            request.missing_info.append('source')

        # Detect processing requirements
        processing_keywords = {
            'normalize_code': ['normalize', 'clean code', 'code normalization'],
            'clean_text': ['clean text', 'normalize text', 'text cleaning'],
            'validate': ['validate', 'validation', 'check validity'],
            'deduplicate': ['deduplicate', 'remove duplicate', 'unique'],
        }

        for processor_name, keywords in processing_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                request.processing_steps.append(processor_name)

        # Detect output format
        if 'csv' in query_lower:
            request.output_format = 'csv'
        elif 'jsonl' in query_lower:
            request.output_format = 'jsonl'
        elif 'json' in query_lower:
            request.output_format = 'json'

        # Determine if straightforward
        request.is_straightforward = (
            request.dataset_type is not None and
            len(request.missing_info) == 0
        )

        logger.info(f"Parsed request: dataset_type={request.dataset_type}, "
                   f"is_straightforward={request.is_straightforward}, "
                   f"missing_info={request.missing_info}")

        return request

    def ask_user_for_clarification(self, request: DatasetRequest) -> DatasetRequest:
        """
        Interactively ask user for missing information.
        """
        logger.info("Asking user for clarification...")

        print("\n" + "="*60)
        print("Dataset Creation Request Analysis")
        print("="*60)

        # If dataset type not detected
        if not request.dataset_type:
            print("\nAvailable dataset types:")
            for i, dtype in enumerate(self.supported_datasets, 1):
                config = self.registry.get_available_metrics(dtype)
                print(f"  {i}. {dtype}: {config.get('description', 'N/A')}")

            while True:
                try:
                    choice = int(input("\nSelect dataset type (number): ")) - 1
                    if 0 <= choice < len(self.supported_datasets):
                        request.dataset_type = self.supported_datasets[choice]
                        break
                except ValueError:
                    pass
                print("Invalid choice. Please try again.")

        # If source not provided
        if 'source' in request.missing_info:
            print(f"\nFor {request.dataset_type} dataset:")
            dataset_info = self.registry.get_available_metrics(request.dataset_type)
            print(f"Description: {dataset_info.get('description', 'N/A')}")

            source = input("Enter data source (path or URL): ").strip()
            if source:
                request.source = source
                request.missing_info.remove('source')
            else:
                print("Source is required!")
                return self.ask_user_for_clarification(request)

        # Ask about processing
        if not request.processing_steps:
            print("\nAvailable processors:")
            processors = self.registry.get_available_processors()
            for i, proc in enumerate(processors, 1):
                print(f"  {i}. {proc}")

            choice = input("\nSelect processors (comma-separated numbers, or press Enter for none): ").strip()
            if choice:
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    request.processing_steps = [processors[i] for i in indices if 0 <= i < len(processors)]
                except ValueError:
                    pass

        # Ask about output path
        if not request.output_path:
            default_path = f"generated_datasets/dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.output_format}"
            user_path = input(f"\nOutput path (default: {default_path}): ").strip()
            request.output_path = user_path if user_path else default_path

        print("\n✓ Request clarified\n")
        return request

    def generate_execution_plan(self, request: DatasetRequest) -> ExecutionPlan:
        """
        Generate a detailed execution plan based on the parsed request.
        """
        logger.info("Generating execution plan...")

        plan = ExecutionPlan(
            dataset_type=request.dataset_type,
            source=request.source,
            extraction_config={},
            processing_pipeline=request.processing_steps,
            output_format=request.output_format,
            output_path=request.output_path or f"generated_datasets/dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.output_format}",
            parameters=request.additional_params,
            step_count=1 + len(request.processing_steps),
        )

        logger.info(f"Execution plan generated: {plan.step_count} steps")
        return plan


class DatasetExecutor:
    """Executes the dataset generation plan"""

    def __init__(self, metrics_registry: MetricsRegistry):
        self.registry = metrics_registry
        self.extraction_results = None
        self.processing_results = None

    def execute_extraction(self, plan: ExecutionPlan) -> List[Dict]:
        """
        Execute data extraction step.
        """
        logger.info(f"Executing extraction: {plan.dataset_type} from {plan.source}")
        print(f"\n📊 Extracting data from {plan.dataset_type}...")

        try:
            # Validate source
            if not validate_source(plan.dataset_type, plan.source):
                raise ValueError(f"Invalid source for {plan.dataset_type}: {plan.source}")

            # Create extractor
            extractor = create_extractor(plan.dataset_type, plan.source, plan.extraction_config)

            # Extract
            records = extractor.extract()
            metadata = extractor.get_metadata()

            self.extraction_results = {
                'records': records,
                'metadata': metadata,
                'count': len(records),
            }

            print(f"✓ Extracted {len(records)} records")
            print(f"  Metadata: {json.dumps(metadata, indent=2)}")

            return records

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            print(f"✗ Extraction failed: {e}")
            raise

    def execute_processing(self, records: List[Dict], plan: ExecutionPlan) -> List[Dict]:
        """
        Execute processing pipeline.
        """
        if not plan.processing_pipeline:
            logger.info("No processing steps, skipping pipeline")
            return records

        logger.info(f"Executing processing pipeline: {plan.processing_pipeline}")
        print(f"\n⚙️  Processing data ({len(plan.processing_pipeline)} steps)...")

        try:
            pipeline = ProcessingPipeline()

            for step in plan.processing_pipeline:
                processor = self.registry.create_processor(step)
                if processor:
                    pipeline.add_processor(processor)
                    logger.info(f"Added processor: {step}")

            # Execute pipeline
            processed = pipeline.process(records)
            stats = pipeline.get_stats()

            self.processing_results = {
                'records': processed,
                'stats': stats,
            }

            print(f"✓ Processing completed")
            print(f"  Final record count: {len(processed)}")
            for proc_name, proc_stats in stats.items():
                print(f"  {proc_name}: {proc_stats}")

            return processed

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            print(f"✗ Processing failed: {e}")
            raise

    def execute_export(self, records: List[Dict], plan: ExecutionPlan) -> str:
        """
        Execute export to specified format.
        """
        logger.info(f"Exporting {len(records)} records to {plan.output_format}")
        print(f"\n💾 Exporting data ({plan.output_format})...")

        try:
            output_path = Path(plan.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if plan.output_format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(records, f, indent=2, default=str)

            elif plan.output_format == 'csv':
                import csv
                if records:
                    with open(output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=records[0].keys())
                        writer.writeheader()
                        writer.writerows(records)

            elif plan.output_format == 'jsonl':
                with open(output_path, 'w') as f:
                    for record in records:
                        f.write(json.dumps(record, default=str) + '\n')

            print(f"✓ Exported to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            print(f"✗ Export failed: {e}")
            raise

    def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute the complete dataset generation plan.
        """
        logger.info("Starting plan execution...")

        print("\n" + "="*60)
        print("Dataset Generation Execution")
        print("="*60)

        try:
            # Step 1: Extract
            records = self.execute_extraction(plan)

            # Step 2: Process
            processed_records = self.execute_processing(records, plan)

            # Step 3: Export
            output_path = self.execute_export(processed_records, plan)

            # Success
            result = {
                'status': 'success',
                'output_path': output_path,
                'total_records': len(processed_records),
                'extraction_info': self.extraction_results,
                'processing_info': self.processing_results,
                'timestamp': datetime.now().isoformat(),
            }

            print("\n" + "="*60)
            print("✓ Dataset Generation Completed Successfully!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"  Dataset Type: {plan.dataset_type}")
            print(f"  Total Records: {len(processed_records)}")
            print(f"  Output Format: {plan.output_format}")
            print(f"  Output Path: {output_path}")
            print()

            return result

        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            print(f"\n✗ Execution failed: {e}\n")
            return {
                'status': 'failed',
                'error': str(e),
            }


class AgenticDatasetMaker:
    """Main orchestrator for agentic dataset creation"""

    def __init__(self):
        self.metrics_registry = MetricsRegistry()
        self.planner = AgentPlanner(self.metrics_registry)
        self.executor = DatasetExecutor(self.metrics_registry)

    def create_dataset(self, user_query: str, interactive: bool = True) -> Dict[str, Any]:
        """
        Main entry point: Create dataset from user query.
        """
        logger.info(f"Creating dataset from query: {user_query}")

        # Step 1: Parse user request
        request = self.planner.parse_user_request(user_query)

        # Step 2: Ask for clarification if needed
        if not request.is_straightforward and interactive:
            request = self.planner.ask_user_for_clarification(request)

        # Step 3: Generate execution plan
        plan = self.planner.generate_execution_plan(request)

        # Step 4: Execute plan
        result = self.executor.execute_plan(plan)

        return result

    def create_dataset_direct(self, dataset_type: str, source: str,
                             processing_steps: Optional[List[str]] = None,
                             output_format: str = 'json',
                             output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Direct API for dataset creation without interactive mode.
        """
        request = DatasetRequest(
            user_query=f"Create {dataset_type} dataset from {source}",
            dataset_type=dataset_type,
            source=source,
            processing_steps=processing_steps or [],
            output_format=output_format,
            output_path=output_path,
            is_straightforward=True,
        )

        plan = self.planner.generate_execution_plan(request)
        return self.executor.execute_plan(plan)


def main():
    """Interactive CLI for agentic dataset maker"""
    print("\n" + "="*60)
    print("🤖 Agentic Dataset Maker")
    print("="*60)
    print("An intelligent system for creating datasets dynamically")
    print()

    maker = AgenticDatasetMaker()

    while True:
        print("\nOptions:")
        print("  1. Create dataset from query (interactive)")
        print("  2. Create dataset directly (API mode)")
        print("  3. View available datasets")
        print("  4. View available processors")
        print("  5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

        if choice == '1':
            query = input("\nDescribe the dataset you want to create:\n> ").strip()
            if query:
                result = maker.create_dataset(query, interactive=True)
                if result['status'] == 'success':
                    print(f"\n✓ Dataset created at: {result['output_path']}")

        elif choice == '2':
            print("\nAvailable datasets:")
            for i, dtype in enumerate(list(SUPPORTED_DATASETS.keys()), 1):
                print(f"  {i}. {dtype}")

            try:
                choice = int(input("\nSelect dataset type (number): ")) - 1
                dataset_type = list(SUPPORTED_DATASETS.keys())[choice]
                source = input("Enter source (path or URL): ").strip()

                if source:
                    result = maker.create_dataset_direct(dataset_type, source)
                    if result['status'] == 'success':
                        print(f"\n✓ Dataset created at: {result['output_path']}")
            except (ValueError, IndexError):
                print("Invalid selection")

        elif choice == '3':
            print("\nSupported Datasets:")
            for dtype, info in SUPPORTED_DATASETS.items():
                metrics = maker.metrics_registry.get_available_metrics(dtype)
                print(f"\n  {dtype}:")
                print(f"    Description: {metrics.get('description', 'N/A')}")
                print(f"    Extractors: {', '.join(metrics.get('extractors', []))}")

        elif choice == '4':
            print("\nAvailable Processors:")
            for proc in maker.metrics_registry.get_available_processors():
                print(f"  - {proc}")

        elif choice == '5':
            print("\nGoodbye!")
            break

        else:
            print("Invalid option")


if __name__ == '__main__':
    main()
