"""
CLI Command for Agentic Dataset Maker
Adds the agent-based dataset creation to the existing CLI system
"""

import click
import json
import logging
from pathlib import Path
from datetime import datetime
from agentic_dataset_maker import AgenticDatasetMaker
from interactive_dataset_generator import InteractiveDatasetGenerator

logger = logging.getLogger(__name__)

@click.group()
def agentic_cli():
    """Agentic Dataset Creation Commands"""
    pass

@agentic_cli.command()
@click.option('--query', prompt='Describe the dataset you want to create', help='Natural language dataset request')
@click.option('--interactive/--no-interactive', default=True, help='Enable interactive mode for clarifications')
@click.option('--output-dir', default='generated_datasets', help='Output directory for dataset')
def create_interactive(query, interactive, output_dir):
    """Create dataset from natural language query (interactive mode)"""
    
    click.echo("\n" + "="*60)
    click.echo("🤖 Agentic Dataset Creation")
    click.echo("="*60)
    
    maker = AgenticDatasetMaker()
    
    try:
        # Set output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        result = maker.create_dataset(query, interactive=interactive)
        
        if result['status'] == 'success':
            click.echo(f"\n✓ Success!")
            click.echo(f"  Output: {result['output_path']}")
            click.echo(f"  Records: {result['total_records']}")
            
            # Save execution summary
            summary_path = Path(output_dir) / f"execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            click.echo(f"  Summary: {summary_path}")
        else:
            click.echo(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"\n✗ Error: {e}")


@agentic_cli.command()
@click.option('--query', prompt='Describe the dataset you want to create', help='Natural language dataset request')
@click.option('--repo-path', help='Repository path (auto-detected if not provided)')
@click.option('--output-dir', default='generated_datasets', help='Output directory for dataset')
def interactive_workflow(query, repo_path, output_dir):
    """Create dataset using interactive feedback workflow"""
    
    click.echo("\n" + "="*60)
    click.echo("🤖 Interactive Dataset Workflow")
    click.echo("="*60)
    
    try:
        # Initialize interactive generator
        generator = InteractiveDatasetGenerator()
        
        # Parse user input
        click.echo(f"\n🔍 Analyzing your request: '{query}'")
        parsed = generator.parse_user_input(query)
        
        # Show understanding
        click.echo(f"\n🧠 My Understanding:")
        generator.print_summary(parsed)
        
        # Ask for confirmation
        if click.confirm("\n🤔 Is this understanding correct?", default=True):
            click.echo("\n✅ Proceeding with dataset generation...")
            
            # Generate dataset
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            dataset_name = parsed.get('dataset_name', 'interactive_dataset')
            output_file = Path(output_dir) / f"{dataset_name}.csv"
            
            # For now, create a simple dataset based on parsed request
            # In a full implementation, this would call the actual generation logic
            with open(output_file, 'w') as f:
                f.write("file,content\n")
                f.write("sample.java,// Generated from interactive workflow\n")
            
            click.echo(f"\n✓ Success!")
            click.echo(f"  Output: {output_file}")
            click.echo(f"  Type: {parsed.get('dataset_type', 'unknown')}")
            
        else:
            click.echo("\n❌ Generation cancelled. Please try rephrasing your request.")
    
    except Exception as e:
        click.echo(f"\n✗ Error: {e}")


@agentic_cli.command()
@click.option('--dataset-type', required=True, type=click.Choice([
    'defects4j', 'bugs_jar', 'codexglue', 'codesearchnet', 'sourcerer', 'promise', 'manystubs4j'
]), help='Type of dataset to create')
@click.option('--source', required=True, help='Data source (path or URL)')
@click.option('--processors', help='Comma-separated list of processors (code_normalizer,text_cleaner,etc.)')
@click.option('--output-format', type=click.Choice(['json', 'csv', 'jsonl']), default='json', help='Output format')
@click.option('--output-path', help='Output file path (auto-generated if not provided)')
def create_direct(dataset_type, source, processors, output_format, output_path):
    """Create dataset using direct API (non-interactive)"""
    
    click.echo("\n" + "="*60)
    click.echo("🤖 Direct Dataset Creation")
    click.echo("="*60)
    
    maker = AgenticDatasetMaker()
    
    # Parse processors
    processing_steps = []
    if processors:
        processing_steps = [p.strip() for p in processors.split(',')]
    
    try:
        result = maker.create_dataset_direct(
            dataset_type=dataset_type,
            source=source,
            processing_steps=processing_steps,
            output_format=output_format,
            output_path=output_path
        )
        
        if result['status'] == 'success':
            click.echo(f"\n✓ Success!")
            click.echo(f"  Output: {result['output_path']}")
            click.echo(f"  Records: {result['total_records']}")
        else:
            click.echo(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"\n✗ Error: {e}")


@agentic_cli.command()
def list_available():
    """List all available datasets and processors"""
    
    maker = AgenticDatasetMaker()
    
    click.echo("\n" + "="*60)
    click.echo("📊 Available Datasets & Processors")
    click.echo("="*60)
    
    # List datasets
    click.echo("\n📦 Supported Datasets:")
    metrics = maker.metrics_registry.get_available_metrics()
    for dtype, info in metrics.items():
        click.echo(f"\n  {dtype}:")
        click.echo(f"    Description: {info.get('description', 'N/A')}")
        click.echo(f"    Extractors: {', '.join(info.get('extractors', []))}")
    
    # List processors
    click.echo("\n\n⚙️  Available Processors:")
    for proc in maker.metrics_registry.get_available_processors():
        click.echo(f"  - {proc}")


@agentic_cli.command()
@click.option('--query', help='Natural language query to analyze (optional)')
def explain_query(query):
    """Explain how the agent would interpret a query"""
    
    maker = AgenticDatasetMaker()
    
    if not query:
        query = click.prompt("Enter your query")
    
    click.echo("\n" + "="*60)
    click.echo("🔍 Query Analysis")
    click.echo("="*60)
    
    request = maker.planner.parse_user_request(query)
    
    click.echo(f"\nQuery: {query}")
    click.echo(f"\nInterpretation:")
    click.echo(f"  Dataset Type: {request.dataset_type or 'Not detected'}")
    click.echo(f"  Processing Steps: {request.processing_steps or 'None'}")
    click.echo(f"  Output Format: {request.output_format}")
    click.echo(f"  Is Straightforward: {request.is_straightforward}")
    click.echo(f"  Missing Info: {request.missing_info or 'None'}")


def add_agentic_commands_to_cli(main_cli):
    """
    Add agentic commands to the main CLI.
    Call this from the main CLI file.
    """
    
    @main_cli.group()
    def agent():
        """Agentic Dataset Creation"""
        pass
    
    agent.add_command(create_interactive, name='create')
    agent.add_command(interactive_workflow, name='interactive')
    agent.add_command(create_direct, name='create-direct')
    agent.add_command(list_available, name='list')
    agent.add_command(explain_query, name='explain')


if __name__ == '__main__':
    agentic_cli()
