# Agentic Dataset Maker Documentation

## Overview

The **Agentic Dataset Maker** is an intelligent system that creates datasets dynamically based on user requests using an AI-powered agent approach. It uses natural language understanding to:

1. **Parse user queries** - Understand what type of dataset you want
2. **Clarify ambiguous requests** - Ask for missing information interactively
3. **Generate execution plans** - Determine which metrics/functions to use
4. **Execute dataset creation** - Extract, process, and export data automatically
5. **Provide intelligent feedback** - Guide users through the process

## How It Works

### Architecture

```
User Query
    ↓
[AgentPlanner] → Parse Intent + Detect Dataset Type
    ↓
    ├─ If Straightforward → Generate Plan
    │
    └─ If Ambiguous → Ask User for Clarification
    ↓
[ExecutionPlan] → List all extraction, processing, export steps
    ↓
[DatasetExecutor] → Execute plan step by step
    ├─ Extract (using appropriate extractor)
    ├─ Process (applying selected processors)
    └─ Export (in desired format)
    ↓
Dataset Output ✓
```

### Key Components

#### 1. **AgentPlanner**
- Parses natural language queries
- Detects dataset type from keywords
- Identifies processing requirements
- Asks for clarification when needed

#### 2. **MetricsRegistry**
- Maintains a catalog of all available metrics
- Lists available extractors for each dataset type
- Manages available processors
- Provides factory methods to create processors

#### 3. **DatasetExecutor**
- Executes the extraction step
- Manages the processing pipeline
- Exports results in desired format
- Tracks execution progress

#### 4. **AgenticDatasetMaker**
- Main orchestrator that coordinates all components
- Provides two modes: interactive and direct API
- Handles end-to-end dataset creation

## Usage

### Mode 1: Interactive (Conversational)

Best when you're not sure about exact requirements:

```bash
# Using CLI
python -m cli.main agent create

# Or programmatic
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()
result = maker.create_dataset(
    "I want a defects4j dataset with normalized code",
    interactive=True  # Enables interactive clarifications
)
```

**Process:**
1. You describe what you want in natural language
2. Agent parses your request
3. If something is missing → Agent asks you
4. Agent generates and executes the plan
5. You get your dataset

**Example Session:**
```
🤖 Agentic Dataset Maker

Your Query: "I need a bug dataset with cleaned text and no duplicates"

Agent Analysis:
  - Dataset Type: Not detected (ambiguous)
  
Asking for Clarification...

[Agent asks: "Which dataset type do you prefer?"]
  1. defects4j
  2. bugs_jar
  3. manystubs4j
  ...

Your Choice: 1

[Agent asks: "Enter data source (path or URL)"]
Your Input: /path/to/java/repo

Processing: Extract → Normalize Code → Remove Duplicates
✓ Dataset created: output.json (150 records)
```

### Mode 2: Direct API (Programmatic)

Best for automation and known requirements:

```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()

# Direct creation without interaction
result = maker.create_dataset_direct(
    dataset_type="defects4j",
    source="/path/to/repo",
    processing_steps=["code_normalizer", "duplicate_remover"],
    output_format="json",
    output_path="output/dataset.json"
)

print(f"✓ Created {result['total_records']} records")
```

### Mode 3: CLI Commands

```bash
# Interactive mode (agent asks questions)
python -m cli.main agent create

# Direct mode (specify everything)
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source /path/to/repo \
    --processors code_normalizer,duplicate_remover \
    --format json \
    --output output.json

# List available datasets and processors
python -m cli.main agent list-all

# Explain how agent interprets a query
python -m cli.main agent explain --query "I want bug fixes"
```

## Supported Datasets

Each dataset type has different extractors and metrics:

### 1. **Defects4J** - Real Java bugs
```
Extractors: buggy_code, fixed_code, bug_description, commit_hash, bug_id, project
Description: Real bugs from Java projects
Formats: json, csv
```

### 2. **Bugs.jar** - Large Java bug dataset
```
Extractors: class_info, bug_location, test_cases, fix_info, metrics
Description: Large-scale Java bug dataset with metrics
Formats: json, csv
```

### 3. **CodeXGLUE** - Code transformation
```
Extractors: code_snippet, target_code, complexity, language, description
Description: Code-to-code transformation dataset
Formats: json, csv
```

### 4. **CodeSearchNet** - Code-to-doc mapping
```
Extractors: code, documentation, tokens, language, docstring
Description: Code-to-documentation mapping
Formats: json, csv
```

### 5. **Sourcerer** - Source code mining
```
Extractors: file_structure, dependencies, metrics, project_info, language
Description: Large-scale source code mining
Formats: json, csv
```

### 6. **PROMISE** - Software metrics
```
Extractors: software_metrics, defect_labels, project_info, version_info
Description: Software metrics for defect prediction
Formats: csv, json
```

### 7. **ManySStuBs4J** - Large Java issues
```
Extractors: issue_id, commit_hash, file_changes, description, severity
Description: Large-scale Java bug dataset with multiple issues
Formats: json, csv
```

## Available Processors

Processors transform and clean your data:

### 1. **code_normalizer**
- Removes comments
- Normalizes whitespace
- Standardizes formatting
- Ideal for: Code comparison, deduplication

### 2. **text_cleaner**
- Removes extra whitespace
- Truncates long texts
- Normalizes formatting
- Ideal for: Text fields, descriptions

### 3. **data_validator**
- Checks required fields
- Validates data types
- Removes invalid records
- Ideal for: Quality assurance

### 4. **duplicate_remover**
- Identifies duplicate records
- Keeps unique entries
- Based on configurable key field
- Ideal for: Data deduplication

## Query Examples

The agent understands various natural language queries:

### Example 1: Simple request
```
"I want a defects4j dataset"
→ Agent asks: source location
→ Creates dataset with default settings
```

### Example 2: Specific processing
```
"Create a bug dataset with cleaned text and no duplicates"
→ Agent detects: cleaning, deduplication
→ Applies: TextCleaner + DuplicateRemover
```

### Example 3: Complex request
```
"Generate a CodeSearchNet dataset from GitHub with normalized code, 
validated records, and CSV output format"
→ Agent detects: codesearchnet, normalization, validation, CSV format
→ Applies: CodeNormalizer + DataValidator + CSV export
```

### Example 4: With source
```
"Extract Bugs.jar data from ~/projects/java_repo with deduplication"
→ Agent detects: bugs_jar, source location, deduplication
→ Creates dataset from specified source
```

## API Reference

### AgenticDatasetMaker

```python
maker = AgenticDatasetMaker()

# Interactive mode
result = maker.create_dataset(
    user_query: str,        # Natural language request
    interactive: bool = True # Enable clarifications
) -> Dict

# Direct API
result = maker.create_dataset_direct(
    dataset_type: str,              # "defects4j", "bugs_jar", etc.
    source: str,                    # Path or URL
    processing_steps: List[str] = None,  # ["code_normalizer", ...]
    output_format: str = 'json',    # "json", "csv", "jsonl"
    output_path: str = None         # Custom output path
) -> Dict
```

### Result Structure

```python
result = {
    'status': 'success' or 'failed',
    'output_path': 'path/to/dataset.json',
    'total_records': 150,
    'extraction_info': {
        'records': [...],
        'metadata': {...},
        'count': 150
    },
    'processing_info': {
        'records': [...],
        'stats': {
            'CodeNormalizer': {'total': 150, 'normalized': 150},
            ...
        }
    },
    'timestamp': '2024-11-19T10:30:00'
}
```

## Configuration

Edit `config/config.py` to customize behavior:

```python
AGENTIC_CONFIG = {
    "enable_interactive_mode": True,
    "enable_direct_api": True,
    "auto_clarify_ambiguous_requests": True,
    "default_output_format": "json",
    "default_processing_pipeline": ["duplicate_remover"],
    "max_records_for_processing": 1000000,
    "enable_caching": True,
    "cache_dir": "cache/agentic",
}
```

## Use Cases

### 1. **Research & Benchmarking**
```python
# Quickly create datasets for ML research
maker.create_dataset("Generate defects4j with code normalization")
```

### 2. **Data Pipeline Automation**
```python
# Automated dataset creation in CI/CD
result = maker.create_dataset_direct(
    dataset_type="promise",
    source="metrics_source.csv",
    processing_steps=["data_validator", "duplicate_remover"],
    output_format="json"
)
```

### 3. **Interactive Data Exploration**
```python
# Explore what datasets are available
maker.create_dataset(
    "Show me available datasets",
    interactive=True
)
```

### 4. **Custom Processing Pipelines**
```python
# Build complex processing workflows
result = maker.create_dataset_direct(
    dataset_type="bugs_jar",
    source="jar_files/",
    processing_steps=[
        "data_validator",
        "code_normalizer", 
        "duplicate_remover",
        "text_cleaner"
    ],
    output_format="csv"
)
```

## Troubleshooting

### Issue: "Source is invalid"
```
Solution: 
- For repositories: Ensure .git folder exists
- For files: Ensure file path is correct
- For URLs: Ensure URL is accessible
```

### Issue: "Dataset type not detected"
```
Solution:
- Be more specific: "I want a defects4j dataset"
- Use exact dataset names from --help
- Use agent explain: python -m cli.main agent explain --query "your query"
```

### Issue: "Too many records, processing is slow"
```
Solution:
- Use CSV export instead of JSON
- Reduce source data size
- Run on smaller subset first
- Adjust PROCESSING_CONFIG chunk_size in config.py
```

## Advanced Features

### Custom Processor Pipeline
```python
from processors.base_processor import ProcessingPipeline, CodeNormalizer

pipeline = ProcessingPipeline()
pipeline.add_processor(CodeNormalizer())
pipeline.add_processor(TextCleaner({"max_length": 500}))

result = pipeline.process(records)
stats = pipeline.get_stats()
```

### Direct Extractor Usage
```python
from extractors.factory import create_extractor

extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()
metadata = extractor.get_metadata()
```

### Metrics Inspection
```python
registry = MetricsRegistry()
metrics = registry.get_available_metrics("defects4j")
processors = registry.get_available_processors()
```

## Integration with Existing System

The agentic maker integrates seamlessly with:

1. **Existing Extractors** - Uses all registered extractors
2. **Existing Processors** - Applies all available processors
3. **CLI System** - Adds `agent` command group
4. **Neo4j Integration** - Can export to Neo4j (future)
5. **Export Formats** - Supports json, csv, jsonl

## Performance Notes

- Small datasets (< 10,000 records): ~5-10 seconds
- Medium datasets (10k-100k): ~30-60 seconds
- Large datasets (> 100k): Depends on processors used
- Processing speed: ~1000-2000 records/sec

## Future Enhancements

- [ ] LLM integration for better query understanding
- [ ] Caching of extraction results
- [ ] Parallel processing for large datasets
- [ ] Custom metric creation
- [ ] Dataset versioning and tracking
- [ ] Neo4j export integration
- [ ] Advanced filtering capabilities
- [ ] Dataset diffing and comparison

---

**Happy Dataset Creation!** 🚀
