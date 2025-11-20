"""
Agentic Dataset Maker
An intelligent system that creates datasets dynamically based on user requests.
Uses LLM to understand user intent, determines required metrics/functions,
and orchestrates the dataset generation process.
"""

import os
import json
import logging
import random
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

from config.config import DATASET_CONFIGS, PROCESSING_CONFIG, BASE_DIR
from extractors.factory import create_extractor, SUPPORTED_DATASETS, validate_source
from processors.base_processor import (
    ProcessingPipeline, CodeNormalizer, TextCleaner,
    DataValidator, DuplicateRemover, BaseProcessor
)
from extractors.base_extractor import BaseExtractor
from utils.helpers import batch_list
from llm_query_parser import LLMQueryParser
from metrics_catalog import MetricsCatalog


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
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from Bugs.jar
        metrics['bugs_jar'] = {
            'extractors': [
                'class_info', 'bug_location', 'test_cases',
                'fix_info', 'metrics'
            ],
            'description': 'Large-scale Java bug dataset with metrics',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from CodeXGLUE
        metrics['codexglue'] = {
            'extractors': [
                'code_snippet', 'target_code', 'complexity',
                'language', 'description'
            ],
            'description': 'Code-to-code transformation dataset',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from CodeSearchNet
        metrics['codesearchnet'] = {
            'extractors': [
                'code', 'documentation', 'tokens',
                'language', 'docstring'
            ],
            'description': 'Code-to-documentation mapping',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from Sourcerer
        metrics['sourcerer'] = {
            'extractors': [
                'file_structure', 'dependencies', 'metrics',
                'project_info', 'language'
            ],
            'description': 'Large-scale source code mining',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from PROMISE
        metrics['promise'] = {
            'extractors': [
                'software_metrics', 'defect_labels',
                'project_info', 'version_info'
            ],
            'description': 'Software metrics for defect prediction',
            'supported_formats': ['csv', 'json', 'excel', 'xlsx'],
        }

        # Metrics from ManySStuBs4J
        metrics['manystubs4j'] = {
            'extractors': [
                'issue_id', 'commit_hash', 'file_changes',
                'description', 'severity'
            ],
            'description': 'Large-scale Java bug dataset',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
        }

        # Metrics from Source Code Analysis
        metrics['source_code'] = {
            'extractors': [
                'software_metrics', 'code_analysis', 'complexity_metrics',
                'size_metrics', 'quality_metrics'
            ],
            'description': 'Generic source code repository analysis',
            'supported_formats': ['json', 'csv', 'excel', 'xlsx'],
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
        self.llm_parser = LLMQueryParser()

    def parse_user_request(self, user_query: str) -> DatasetRequest:
        """
        Parse user query to extract intent, dataset type, and requirements.
        Uses LLM-based parser to understand the request.
        """
        logger.info(f"Parsing user request: {user_query}")
        
        # Use LLM parser to extract structured information
        parse_result = self.llm_parser.parse_query(user_query)
        
        request = DatasetRequest(user_query=user_query)
        
        # Set dataset type if detected
        if parse_result['dataset_type']:
            request.dataset_type = parse_result['dataset_type']
            logger.info(f"Detected dataset type: {request.dataset_type}")
        else:
            request.missing_info.append('dataset_type')
            logger.warning("Dataset type not detected")
        
        # Set requested metrics
        if parse_result['metrics']:
            request.additional_params['requested_metrics'] = parse_result['metrics']
            logger.info(f"Detected {len(parse_result['metrics'])} metrics")
        
        # Set output format
        if parse_result['output_format']:
            request.output_format = parse_result['output_format']
            logger.info(f"Detected output format: {request.output_format}")
        
        # Mark as straightforward if no clarification needed
        request.is_straightforward = (
            parse_result['confidence'] >= 0.8 and
            not parse_result['needs_clarification'] and
            request.dataset_type is not None
        )
        
        logger.info(f"Parsed request: dataset_type={request.dataset_type}, "
                   f"metrics={len(parse_result['metrics'])}, "
                   f"is_straightforward={request.is_straightforward}, "
                   f"confidence={parse_result['confidence']:.2f}")
        
        return request

    def ask_user_for_clarification(self, request: DatasetRequest) -> DatasetRequest:
        """
        Use LLM parser's clarification mechanism to ask user for missing info
        """
        logger.info("Asking user for clarification...")
        
        # Parse query again with interactive clarification
        parse_result = self.llm_parser.parse_query(request.user_query)
        
        # Ask for clarification if needed
        if parse_result['needs_clarification']:
            parse_result = self.llm_parser.ask_clarification(parse_result)
        
        # Update request with clarified values
        if parse_result['dataset_type']:
            request.dataset_type = parse_result['dataset_type']
            if 'dataset_type' in request.missing_info:
                request.missing_info.remove('dataset_type')
        
        if parse_result['metrics']:
            request.additional_params['requested_metrics'] = parse_result['metrics']
        
        if parse_result['output_format']:
            request.output_format = parse_result['output_format']
        
        # Print summary
        summary = self.llm_parser.format_result_summary(parse_result)
        print(summary)
        
        return request

    def generate_execution_plan(self, request: DatasetRequest) -> ExecutionPlan:
        """
        Generate a detailed execution plan based on the parsed request.
        """
        logger.info("Generating execution plan...")

        # Handle output path - if it's a directory, create a filename inside it
        output_path = request.output_path
        if output_path:
            output_path_obj = Path(output_path)
            if output_path_obj.is_dir() or (not output_path_obj.exists() and not output_path_obj.suffix):
                # It's a directory or looks like a directory (no extension)
                # Create a filename inside the directory
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"dataset_{timestamp}.{request.output_format}"
                output_path = str(output_path_obj / filename)
                logger.info(f"Output path is directory, creating file: {output_path}")
            else:
                # It's already a file path
                logger.info(f"Using provided output path: {output_path}")
        else:
            # No output path provided, use default
            output_path = f"generated_datasets/dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.output_format}"
            logger.info(f"Using default output path: {output_path}")

        plan = ExecutionPlan(
            dataset_type=request.dataset_type,
            source=request.source,
            extraction_config={},
            processing_pipeline=request.processing_steps,
            output_format=request.output_format,
            output_path=output_path,
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
        print(f"\n[*] Extracting data from {plan.dataset_type}...")
        print(f"   Source: {plan.source}")

        try:
            # Special case for synthetic data generation
            if plan.source == "synthetic" and plan.dataset_type == "promise":
                logger.info("Using synthetic data generation mode")
                records = self._generate_synthetic_promise_data()
                self.extraction_results = {
                    'records': records,
                    'metadata': {'synthetic': True, 'generation_method': 'workspace_analysis'},
                    'count': len(records),
                }
                print(f"✓ Generated {len(records)} synthetic PROMISE records")
                return records

            # Handle None source for datasets that can generate synthetic data
            if plan.source is None:
                if plan.dataset_type in ["defects4j", "bugs_jar", "manystubs4j"]:
                    logger.info(f"Using synthetic data generation for {plan.dataset_type}")
                    records = self._generate_synthetic_dataset(plan.dataset_type)
                    self.extraction_results = {
                        'records': records,
                        'metadata': {'synthetic': True, 'generation_method': 'workspace_analysis'},
                        'count': len(records),
                    }
                    print(f"✓ Generated {len(records)} synthetic {plan.dataset_type} records")
                    return records
                else:
                    raise ValueError(f"No source provided for {plan.dataset_type}")

            # Validate source
            if not validate_source(plan.dataset_type, plan.source):
                logger.error(f"Source validation failed: {plan.dataset_type} from {plan.source}")
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

            print(f"[OK] Extracted {len(records)} records")
            print(f"  Metadata: {json.dumps(metadata, indent=2)}")

            return records

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            logger.exception(f"Full traceback for extraction error:")
            print(f"[ERROR] Extraction failed: {e}")
            print(f"   Source was: {plan.source}")
            print(f"   Dataset type: {plan.dataset_type}")
            raise

    def execute_processing(self, records: List[Dict], plan: ExecutionPlan) -> List[Dict]:
        """
        Execute processing pipeline.
        """
        if not plan.processing_pipeline:
            logger.info("No processing steps, skipping pipeline")
            return records

        logger.info(f"Executing processing pipeline: {plan.processing_pipeline}")
        print(f"\n[*] Processing data ({len(plan.processing_pipeline)} steps)...")

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

            print(f"[OK] Processing completed")
            print(f"  Final record count: {len(processed)}")
            for proc_name, proc_stats in stats.items():
                print(f"  {proc_name}: {proc_stats}")

            return processed

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            print(f"[ERROR] Processing failed: {e}")
            raise

    def execute_export(self, records: List[Dict], plan: ExecutionPlan) -> str:
        """
        Execute export to specified format.
        """
        logger.info(f"Exporting {len(records)} records to {plan.output_format}")
        print(f"\n[*] Exporting data ({plan.output_format})...")

        try:
            output_path = Path(plan.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if plan.output_format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(records, f, indent=2, default=str)

            elif plan.output_format == 'csv':
                import csv
                if records:
                    # Collect all unique fieldnames from all records
                    fieldnames = set()
                    for record in records:
                        fieldnames.update([k for k in record.keys() if k is not None])
                    fieldnames = sorted(list(fieldnames), key=str)
                    
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='', extrasaction='ignore')
                        writer.writeheader()
                        writer.writerows(records)

            elif plan.output_format in ['excel', 'xlsx']:
                import pandas as pd
                if records:
                    df = pd.DataFrame(records)
                    df.to_excel(output_path, index=False, engine='openpyxl')
                else:
                    # Create empty Excel file
                    pd.DataFrame().to_excel(output_path, index=False, engine='openpyxl')

            elif plan.output_format == 'jsonl':
                with open(output_path, 'w') as f:
                    for record in records:
                        f.write(json.dumps(record, default=str) + '\n')

            print(f"[OK] Exported to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            print(f"[ERROR] Export failed: {e}")
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
                'files_created': [output_path],  # Include files_created for GUI compatibility
                'total_records': len(processed_records),
                'extraction_info': self.extraction_results,
                'processing_info': self.processing_results,
                'timestamp': datetime.now().isoformat(),
            }

            print("\n" + "="*60)
            print("[SUCCESS] Dataset Generation Completed!")
            print("="*60)
            print(f"\n[SUMMARY]")
            print(f"  Dataset Type: {plan.dataset_type}")
            print(f"  Total Records: {len(processed_records)}")
            print(f"  Output Format: {plan.output_format}")
            print(f"  Output Path: {output_path}")
            print()

            return result

        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            print(f"\n[ERROR] Execution failed: {e}\n")
            return {
                'status': 'failed',
                'error': str(e),
            }

    def _generate_synthetic_dataset(self, dataset_type: str) -> List[Dict]:
        """
        Generate synthetic dataset based on type.
        """
        logger.info(f"Generating synthetic {dataset_type} data from workspace")
        
        if dataset_type == "promise":
            return self._generate_synthetic_promise_data()
        elif dataset_type == "defects4j":
            return self._generate_synthetic_defects4j_data()
        elif dataset_type == "bugs_jar":
            return self._generate_synthetic_bugs_jar_data()
        elif dataset_type == "manystubs4j":
            return self._generate_synthetic_manystubs4j_data()
        else:
            raise ValueError(f"Unsupported dataset type for synthetic generation: {dataset_type}")

    def _generate_synthetic_promise_data(self) -> List[Dict]:
        """
        Generate synthetic PROMISE-style dataset from workspace analysis.
        """
        logger.info("Generating synthetic PROMISE data from workspace")
        dataset = []

        # Analyze Java files in the workspace
        workspace_path = BASE_DIR.parent  # Go up to GitIntel root
        java_files = list(workspace_path.rglob("*.java"))[:50]  # Limit to 50 files

        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                lines = code.split('\n')
                loc = len(lines)

                # Calculate basic metrics
                num_methods = code.count('public ') + code.count('private ') + code.count('protected ')
                num_classes = code.count('class ')
                num_comments = code.count('//') + code.count('/*')
                cyclomatic_complexity = max(1, num_methods + code.count('if ') + code.count('for ') + code.count('while ') + code.count('case '))

                # Generate synthetic CK metrics
                record = {
                    "project": java_file.parent.name,
                    "file": str(java_file.relative_to(workspace_path)),
                    "language": "java",
                    "dataset_type": "promise",
                    "loc": loc,
                    "cyclomatic_complexity": cyclomatic_complexity,
                    "num_methods": num_methods,
                    "num_classes": num_classes,
                    "num_comments": num_comments,
                    "churn": 0,  # Would need git history for real churn
                    "defects": 0,  # Synthetic - no real defects
                    "wmc": cyclomatic_complexity,  # Weighted methods per class
                    "dit": 1,  # Depth of inheritance (simplified)
                    "noc": 0,  # Number of children (simplified)
                    "cbo": num_classes,  # Coupling between objects (simplified)
                    "rfc": num_methods,  # Response for a class
                    "lcom": 0  # Lack of cohesion (simplified)
                }
                dataset.append(record)

            except Exception as e:
                logger.warning(f"Error processing {java_file}: {e}")

        logger.info(f"Generated {len(dataset)} synthetic PROMISE records")
        return dataset

    def _generate_synthetic_defects4j_data(self) -> List[Dict]:
        """
        Generate synthetic Defects4J-style dataset.
        """
        logger.info("Generating synthetic Defects4J data")
        dataset = []

        # Similar to PROMISE but with Defects4J-specific fields
        workspace_path = BASE_DIR.parent
        java_files = list(workspace_path.rglob("*.java"))[:30]  # Limit to 30 files

        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                lines = code.split('\n')
                loc = len(lines)
                cyclomatic_complexity = max(1, code.count('if ') + code.count('for ') + code.count('while ') + code.count('case ') + 1)

                record = {
                    "project": java_file.parent.name,
                    "bug_id": f"bug_{java_file.stem}",
                    "file": str(java_file.relative_to(workspace_path)),
                    "loc": loc,
                    "cyclomatic_complexity": cyclomatic_complexity,
                    "buggy_code": "",  # Would need actual bug data
                    "fixed_code": code[:200],  # Truncated for demo
                    "commit_hash": "synthetic_commit_hash",
                    "defects": random.randint(0, 1),  # Random defect label
                }
                dataset.append(record)

            except Exception as e:
                logger.warning(f"Error processing {java_file}: {e}")

        logger.info(f"Generated {len(dataset)} synthetic Defects4J records")
        return dataset

    def _generate_synthetic_bugs_jar_data(self) -> List[Dict]:
        """
        Generate synthetic Bugs.jar-style dataset.
        """
        logger.info("Generating synthetic Bugs.jar data")
        dataset = []

        workspace_path = BASE_DIR.parent
        java_files = list(workspace_path.rglob("*.java"))[:25]

        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                record = {
                    "class_info": java_file.stem,
                    "bug_location": str(java_file.relative_to(workspace_path)),
                    "test_cases": random.randint(1, 10),
                    "fix_info": "synthetic_fix",
                    "metrics": {
                        "loc": len(code.split('\n')),
                        "complexity": random.randint(1, 20)
                    }
                }
                dataset.append(record)

            except Exception as e:
                logger.warning(f"Error processing {java_file}: {e}")

        logger.info(f"Generated {len(dataset)} synthetic Bugs.jar records")
        return dataset

    def _generate_synthetic_manystubs4j_data(self) -> List[Dict]:
        """
        Generate synthetic ManySStuBs4J-style dataset.
        """
        logger.info("Generating synthetic ManySStuBs4J data")
        dataset = []

        workspace_path = BASE_DIR.parent
        java_files = list(workspace_path.rglob("*.java"))[:20]

        for java_file in java_files:
            try:
                record = {
                    "issue_id": f"issue_{random.randint(1000, 9999)}",
                    "commit_hash": f"commit_{random.randint(10000, 99999)}",
                    "file_changes": str(java_file.relative_to(workspace_path)),
                    "description": "Synthetic bug description",
                    "severity": random.choice(["low", "medium", "high"])
                }
                dataset.append(record)

            except Exception as e:
                logger.warning(f"Error processing {java_file}: {e}")

        logger.info(f"Generated {len(dataset)} synthetic ManySStuBs4J records")
        return dataset


class AgenticDatasetMaker:
    """Main orchestrator for agentic dataset creation"""

    def __init__(self):
        self.metrics_registry = MetricsRegistry()
        self.planner = AgentPlanner(self.metrics_registry)
        self.executor = DatasetExecutor(self.metrics_registry)

    def create_dataset(self, user_query: str, interactive: bool = True, output_path: Optional[str] = None, source_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point: Create dataset from user query with AI analysis.
        """
        logger.info(f"🤖 AI Agent creating dataset from query: {user_query}")

        print("\n" + "="*80)
        print("🤖 AI AGENTIC DATASET MAKER")
        print("="*80)
        print(f"User Query: {user_query}")
        print()

        # Step 1: Parse user request with AI analysis
        print("🧠 Analyzing your request with AI...")
        request = self.planner.parse_user_request(user_query)

        # Set output path if provided
        if output_path:
            request.output_path = output_path

        # Set source path if provided, otherwise set defaults for certain datasets
        valid_source_path = False
        if source_path:
            # Validate the source path exists
            if os.path.exists(source_path):
                request.source = source_path
                valid_source_path = True
                logger.info(f"Using provided source path: {source_path}")
            else:
                logger.warning(f"Source path does not exist: {source_path}, falling back to default logic")

        if not valid_source_path:  # Only set defaults if no valid source_path provided
            if request.dataset_type:
                # Set default sources for datasets that can generate synthetic data
                if request.dataset_type == "promise":
                    # For promise, we can generate synthetic data or look for existing files
                    default_promise_files = [
                        str(BASE_DIR / "data" / "promise_dataset.csv"),
                        str(BASE_DIR / "generated_datasets" / "promise_dataset.csv"),
                        str(BASE_DIR / "exports" / "promise_dataset.csv")
                    ]
                    file_found = False
                    for file_path in default_promise_files:
                        if os.path.exists(file_path):
                            request.source = file_path
                            file_found = True
                            logger.info(f"Using default PROMISE file: {file_path}")
                            break
                    if not file_found:
                        # No existing file found, we'll generate synthetic data
                        request.source = "synthetic"
                        logger.info("No existing PROMISE files found, will generate synthetic data")
                elif request.dataset_type == "source_code":
                    # For source_code, look for elasticsearch directory or use workspace root
                    workspace_path = BASE_DIR.parent
                    elasticsearch_path = workspace_path / "elasticsearch"
                    if elasticsearch_path.exists():
                        request.source = str(elasticsearch_path)
                        logger.info(f"Using Elasticsearch source: {elasticsearch_path}")
                    else:
                        # Fall back to workspace root for generic source code analysis
                        request.source = str(workspace_path)
                        logger.info(f"Using workspace root for source code analysis: {workspace_path}")
                elif request.dataset_type in ["defects4j", "bugs_jar", "manystubs4j"]:
                    # These require actual source data, so leave source as None to trigger clarification
                    pass
                else:
                    # For other datasets, leave as None to trigger clarification
                    pass

        # Step 2: Ask for clarification if needed (AI feedback mechanism)
        if not request.is_straightforward and interactive:
            print("💬 AI needs clarification on your request...")
            request = self.planner.ask_user_for_clarification(request)

        # Step 3: Generate execution plan
        print("📋 Generating execution plan...")
        plan = self.planner.generate_execution_plan(request)

        # Display the AI analysis summary
        summary = self.planner.llm_parser.format_result_summary({
            'dataset_type': plan.dataset_type,
            'output_format': plan.output_format,
            'metrics': request.additional_params.get('requested_metrics', []),
            'intent_analysis': request.additional_params.get('intent_analysis', {'primary_intent': 'dataset_creation'})
        })
        print(summary)

        # Step 4: Execute plan
        print("⚡ Executing dataset generation...")
        result = self.executor.execute_plan(plan)

        # Enhanced result reporting
        if result['status'] == 'success':
            print("\n" + "="*80)
            print("✅ SUCCESS! AI Agent completed dataset generation")
            print("="*80)
            print(f"📁 Dataset saved to: {result['output_path']}")
            print(f"📊 Total records: {result.get('total_records', 'N/A')}")
            print(f"🎯 Dataset type: {plan.dataset_type}")
            print(f"📈 Metrics included: {len(request.additional_params.get('requested_metrics', []))}")
            print()

        return result

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze a user prompt and return AI analysis results.
        Used by GUI for initial analysis before dataset generation.
        """
        logger.info(f"Analyzing prompt: {prompt}")
        
        try:
            # Parse the user request
            request = self.planner.parse_user_request(prompt)
            
            # Get the parse result from the LLM parser
            parse_result = self.planner.llm_parser.parse_query(prompt)
            
            # Build analysis result
            analysis = {
                'dataset_type': request.dataset_type,
                'output_format': request.output_format,
                'requested_metrics': request.additional_params.get('requested_metrics', []),
                'needs_clarification': parse_result.get('needs_clarification', False),
                'clarification_question': parse_result.get('clarification_question', ''),
                'confidence': parse_result.get('confidence', 0.0),
                'intent_analysis': request.additional_params.get('intent_analysis', {}),
                'is_straightforward': request.is_straightforward,
                'missing_info': request.missing_info
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing prompt: {e}")
            return {
                'error': str(e),
                'needs_clarification': True,
                'clarification_question': 'Could you please clarify your dataset requirements?'
            }

    def analyze_prompt_with_clarification(self, prompt: str, clarification: str) -> Dict[str, Any]:
        """
        Analyze a prompt with additional clarification.
        """
        logger.info(f"Analyzing prompt with clarification: {prompt} + {clarification}")
        
        try:
            # Combine prompt and clarification
            combined_query = f"{prompt}\n\nAdditional clarification: {clarification}"
            
            # Parse with clarification
            request = self.planner.parse_user_request(combined_query)
            parse_result = self.planner.llm_parser.parse_query(combined_query)
            
            # Build analysis result
            analysis = {
                'dataset_type': request.dataset_type,
                'output_format': request.output_format,
                'requested_metrics': request.additional_params.get('requested_metrics', []),
                'needs_clarification': False,  # Clarification provided
                'confidence': parse_result.get('confidence', 0.0),
                'intent_analysis': request.additional_params.get('intent_analysis', {}),
                'is_straightforward': request.is_straightforward,
                'missing_info': request.missing_info
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing prompt with clarification: {e}")
            return {
                'error': str(e),
                'needs_clarification': False
            }

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
