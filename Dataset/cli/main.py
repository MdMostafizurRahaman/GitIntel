"""
Dataset Management CLI Tool
Command-line interface for dataset creation, processing, and export
"""

import click
import logging
from pathlib import Path
from typing import Optional
import json
from tabulate import tabulate
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config.config import DATASET_CONFIGS
from extractors.factory import create_extractor, SUPPORTED_DATASETS, validate_source
from processors.base_processor import (
    ProcessingPipeline, CodeNormalizer, TextCleaner, 
    DataValidator, DuplicateRemover
)
from labelers.labeler import (
    BugSeverityLabeler, CodeComplexityLabeler, 
    FeatureLabelClassifier, MultiLabelClassifier
)
# Import neo4j manager only when needed
from utils.helpers import batch_list

@click.group()
def cli():
    """Dataset Management System CLI"""
    pass

@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def list_datasets(format):
    """List supported datasets"""
    
    if format == 'json':
        click.echo(json.dumps(SUPPORTED_DATASETS, indent=2))
    else:
        data = [
            [name, info['name'], info['description']]
            for name, info in SUPPORTED_DATASETS.items()
        ]
        click.echo(tabulate(data, headers=['ID', 'Name', 'Description']))

@cli.command()
@click.option('--dataset-type', required=True, type=click.Choice(list(SUPPORTED_DATASETS.keys())))
@click.option('--source', required=True, help='Source path or URL')
@click.option('--output', required=True, help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv', 'jsonl']), default='json')
def extract(dataset_type, source, output, format):
    """Extract data from source"""
    
    logger.info(f"Extracting {dataset_type} from {source}")
    
    # Validate source
    if not validate_source(dataset_type, source):
        click.echo(f"Error: Invalid source for {dataset_type}", err=True)
        return
    
    try:
        # Create extractor
        extractor = create_extractor(dataset_type, source)
        
        # Extract data
        click.echo("Extracting data...")
        records = extractor.extract()
        
        # Save data
        click.echo(f"Saving {len(records)} records to {output}")
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(records, f, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            if records:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
        
        elif format == 'jsonl':
            with open(output_path, 'w') as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + '\n')
        
        click.echo(f"✓ Extracted {len(records)} records")
        click.echo(f"✓ Metadata: {json.dumps(extractor.get_metadata(), indent=2)}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--input', required=True, help='Input data file')
@click.option('--output', required=True, help='Output file path')
@click.option('--normalize-code', is_flag=True, help='Normalize code')
@click.option('--clean-text', is_flag=True, help='Clean text fields')
@click.option('--validate', is_flag=True, help='Validate records')
@click.option('--remove-duplicates', is_flag=True, help='Remove duplicates')
def process(input, output, normalize_code, clean_text, validate, remove_duplicates):
    """Process extracted data"""
    
    logger.info(f"Processing data from {input}")
    
    try:
        # Load data
        input_path = Path(input)
        with open(input_path) as f:
            records = json.load(f)
        
        click.echo(f"Loaded {len(records)} records")
        
        # Create processing pipeline
        pipeline = ProcessingPipeline()
        
        if normalize_code:
            pipeline.add_processor(CodeNormalizer())
        
        if clean_text:
            pipeline.add_processor(TextCleaner())
        
        if validate:
            pipeline.add_processor(DataValidator())
        
        if remove_duplicates:
            pipeline.add_processor(DuplicateRemover())
        
        # Process
        click.echo("Processing...")
        processed = pipeline.process(records)
        
        # Save results
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(processed, f, indent=2, default=str)
        
        # Display stats
        stats = pipeline.get_stats()
        click.echo(f"\n✓ Processed {len(processed)} records")
        click.echo("\nProcessing Statistics:")
        click.echo(json.dumps(stats, indent=2))
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--input', required=True, help='Input data file')
@click.option('--output', required=True, help='Output file path')
@click.option('--label-type', required=True, type=click.Choice([
    'bug_severity', 'code_complexity', 'feature_type', 'multi_label'
]))
def label(input, output, label_type):
    """Label dataset records"""
    
    logger.info(f"Labeling data with {label_type}")
    
    try:
        # Load data
        input_path = Path(input)
        with open(input_path) as f:
            records = json.load(f)
        
        click.echo(f"Loaded {len(records)} records")
        
        # Create labeler
        if label_type == 'bug_severity':
            labeler = BugSeverityLabeler()
        elif label_type == 'code_complexity':
            labeler = CodeComplexityLabeler()
        elif label_type == 'feature_type':
            labeler = FeatureLabelClassifier()
        else:  # multi_label
            labeler = MultiLabelClassifier()
        
        # Label
        click.echo("Labeling...")
        labeled = labeler.label(records)
        
        # Save results
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(labeled, f, indent=2, default=str)
        
        # Display stats
        stats = labeler.get_stats()
        click.echo(f"\n✓ Labeled {len(labeled)} records")
        click.echo("\nLabeling Distribution:")
        for label, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {label}: {count}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--input', required=True, help='Input data file')
@click.option('--dataset-name', required=True, help='Dataset name')
@click.option('--project-id', required=True, help='Project ID in Neo4j')
def import_to_neo4j(input, dataset_name, project_id):
    """Import processed data to Neo4j"""
    
    logger.info(f"Importing data to Neo4j")
    
    try:
        # Load data
        input_path = Path(input)
        with open(input_path) as f:
            records = json.load(f)
        
        click.echo(f"Loaded {len(records)} records")
        
        # Connect to Neo4j
        from neo4j.manager import get_neo4j_manager
        neo4j = get_neo4j_manager()
        click.echo("Connected to Neo4j")
        
        # Create project node
        project_node = {
            "id": project_id,
            "name": dataset_name,
            "import_date": datetime.now().isoformat(),
        }
        neo4j.create_node("Dataset", project_node)
        click.echo(f"Created dataset node: {dataset_name}")
        
        # Import records in batches
        batch_size = 100
        batches = batch_list(records, batch_size)
        
        with click.progressbar(length=len(batches), label='Importing batches') as bar:
            for batch in batches:
                for record in batch:
                    node_type = record.get("type", "Record").replace("_", "").title()
                    try:
                        neo4j.create_node(node_type, record)
                    except Exception as e:
                        logger.warning(f"Error importing record: {e}")
                
                bar.update(1)
        
        # Display stats
        stats = neo4j.get_statistics()
        click.echo(f"\n✓ Imported records to Neo4j")
        click.echo("\nNeo4j Statistics:")
        for node_type, count in sorted(stats.items()):
            click.echo(f"  {node_type}: {count}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
def status():
    """Check system status"""
    
    try:
        # Check Neo4j connection
        from neo4j.manager import get_neo4j_manager
        neo4j = get_neo4j_manager()
        stats = neo4j.get_statistics()
        
        click.echo("✓ Neo4j connected")
        click.echo(f"  Database has {sum(stats.values())} items")
        
        click.echo("\n✓ System status: OK")
    
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)

# Add agentic commands
@cli.group()
def agent():
    """Agentic Dataset Creation (AI-powered)"""
    pass

@agent.command()
@click.option('--query', prompt='Describe the dataset you want to create', help='Natural language dataset request')
@click.option('--interactive/--no-interactive', default=True, help='Enable interactive mode for clarifications')
@click.option('--output-dir', default='generated_datasets', help='Output directory for dataset')
def create(query, interactive, output_dir):
    """Create dataset from natural language query (interactive)"""
    
    from agentic_dataset_maker import AgenticDatasetMaker
    
    click.echo("\n" + "="*60)
    click.echo("🤖 Agentic Dataset Creation")
    click.echo("="*60)
    
    maker = AgenticDatasetMaker()
    
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        result = maker.create_dataset(query, interactive=interactive)
        
        if result['status'] == 'success':
            click.echo(f"\n✓ Success!")
            click.echo(f"  Output: {result['output_path']}")
            click.echo(f"  Records: {result['total_records']}")
        else:
            click.echo(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        click.echo(f"\n✗ Error: {e}")

@agent.command()
@click.option('--dataset-type', required=True, type=click.Choice([
    'defects4j', 'bugs_jar', 'codexglue', 'codesearchnet', 'sourcerer', 'promise', 'manystubs4j'
]), help='Type of dataset')
@click.option('--source', required=True, help='Data source (path or URL)')
@click.option('--processors', help='Processors (code_normalizer,text_cleaner,etc.)')
@click.option('--format', type=click.Choice(['json', 'csv', 'jsonl']), default='json', help='Output format')
@click.option('--output', help='Output file path')
def create_direct(dataset_type, source, processors, format, output):
    """Create dataset directly (non-interactive)"""
    
    from agentic_dataset_maker import AgenticDatasetMaker
    
    click.echo("\n" + "="*60)
    click.echo("🤖 Direct Dataset Creation")
    click.echo("="*60)
    
    maker = AgenticDatasetMaker()
    processing_steps = [p.strip() for p in processors.split(',')] if processors else []
    
    try:
        result = maker.create_dataset_direct(
            dataset_type=dataset_type,
            source=source,
            processing_steps=processing_steps,
            output_format=format,
            output_path=output
        )
        
        if result['status'] == 'success':
            click.echo(f"\n✓ Success!")
            click.echo(f"  Output: {result['output_path']}")
            click.echo(f"  Records: {result['total_records']}")
        else:
            click.echo(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        click.echo(f"\n✗ Error: {e}")

@agent.command()
def list_all():
    """List available datasets and processors"""
    
    from agentic_dataset_maker import AgenticDatasetMaker
    
    maker = AgenticDatasetMaker()
    
    click.echo("\n" + "="*60)
    click.echo("📊 Available Datasets & Processors")
    click.echo("="*60)
    
    click.echo("\n📦 Datasets:")
    metrics = maker.metrics_registry.get_available_metrics()
    for dtype, info in metrics.items():
        click.echo(f"  {dtype}: {info.get('description', 'N/A')}")
    
    click.echo("\n⚙️  Processors:")
    for proc in maker.metrics_registry.get_available_processors():
        click.echo(f"  - {proc}")

@agent.command()
@click.option('--query', help='Query to analyze')
def explain(query):
    """Explain query interpretation"""
    
    from agentic_dataset_maker import AgenticDatasetMaker
    
    if not query:
        query = click.prompt("Enter your query")
    
    maker = AgenticDatasetMaker()
    request = maker.planner.parse_user_request(query)
    
    click.echo("\n" + "="*60)
    click.echo("🔍 Query Analysis")
    click.echo("="*60)
    click.echo(f"\nQuery: {query}")
    click.echo(f"Dataset Type: {request.dataset_type or 'Not detected'}")
    click.echo(f"Processing Steps: {request.processing_steps or 'None'}")
    click.echo(f"Output Format: {request.output_format}")
    click.echo(f"Straightforward: {request.is_straightforward}")
    click.echo(f"Missing Info: {request.missing_info or 'None'}")

if __name__ == '__main__':
    cli()
