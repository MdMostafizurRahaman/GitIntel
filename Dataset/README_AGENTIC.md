# Dataset Management System - Agentic Enhancement

Welcome to the enhanced Dataset Management System with **Agentic Dataset Maker** - an AI-powered system for intelligent, dynamic dataset creation!

## What's New?

### 🤖 Agentic Dataset Maker
An intelligent agent-based system that:
- **Understands natural language** - Describe what dataset you want in plain English
- **Clarifies ambiguous requests** - Asks clarifying questions when needed
- **Generates execution plans** - Determines which metrics and processors to use
- **Executes automatically** - Extracts, processes, and exports your dataset
- **Provides intelligent feedback** - Guides you through the entire process

## Quick Start

### Interactive Mode (Recommended for beginners)

```bash
cd d:\GitIntel\Dataset

# Run the agent - it will ask questions
python -m cli.main agent create

# Just describe what you want:
# > "I want a defects4j dataset with code normalization"
# Agent will ask for clarification and create your dataset
```

### Direct API Mode (For automation)

```bash
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source "d:\GitIntel\druid" \
    --processors code_normalizer,duplicate_remover \
    --format json \
    --output output/dataset.json
```

### Python Code

```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()

# Interactive - agent asks questions
result = maker.create_dataset(
    "Create a bug dataset with cleaned text",
    interactive=True
)

# Or direct API
result = maker.create_dataset_direct(
    dataset_type="defects4j",
    source="/path/to/repo",
    processing_steps=["code_normalizer"],
    output_format="json"
)

print(f"✓ Created {result['total_records']} records")
```

## System Architecture

```
User Request
    ↓
┌─────────────────────────────────────────┐
│  AgentPlanner                           │
│  - Parse natural language              │
│  - Detect dataset type                 │
│  - Identify processors                 │
│  - Ask for clarification if needed      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  ExecutionPlan                          │
│  - Extract step                         │
│  - Processing pipeline steps            │
│  - Export step                          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  DatasetExecutor                        │
│  - Run extraction                       │
│  - Apply processors                     │
│  - Export to format                     │
└─────────────────────────────────────────┘
    ↓
Dataset Output ✓
```

## Key Features

### 1. **Multiple Dataset Types**
- Defects4J - Real Java bugs
- Bugs.jar - Large Java bug dataset
- CodeXGLUE - Code transformation
- CodeSearchNet - Code-to-doc mapping
- Sourcerer - Source code mining
- PROMISE - Software metrics
- ManySStuBs4J - Large Java issues

### 2. **Intelligent Processing**
- Code normalization
- Text cleaning
- Data validation
- Duplicate removal
- Custom processor support

### 3. **Flexible Output**
- JSON format
- CSV format
- JSONL (JSON Lines)

### 4. **Two Modes**
- **Interactive** - Agent clarifies ambiguous requests
- **Direct API** - Programmatic control

### 5. **Query Understanding**
- Natural language parsing
- Dataset type detection
- Processor recommendation
- Missing info detection

## File Structure

```
Dataset/
├── agentic_dataset_maker.py       # Main agentic system
├── cli/
│   ├── main.py                    # Updated CLI with agent commands
│   └── agentic_cli.py             # Agentic-specific commands
├── config/
│   └── config.py                  # Configuration (updated with AGENTIC_CONFIG)
├── docs/
│   └── AGENTIC_DATASET_MAKER.md   # Full documentation
├── AGENTIC_QUICKSTART.md          # Quick start guide
├── examples_agentic.py            # Comprehensive examples
├── extractors/                    # Dataset extractors
├── processors/                    # Data processors
├── generated_datasets/            # Output location
└── ...
```

## Usage Examples

### Example 1: Simple Interactive

```bash
python -m cli.main agent create
# Answer: "defects4j dataset with normalization"
# Provide source path
# Get dataset ✓
```

### Example 2: Complex Request

```bash
python -m cli.main agent create-direct \
    --dataset-type bugs_jar \
    --source "bugs.json" \
    --processors data_validator,code_normalizer,duplicate_remover,text_cleaner \
    --format csv \
    --output output/bugs_cleaned.csv
```

### Example 3: Query Explanation

```bash
python -m cli.main agent explain --query "I want a defects4j dataset"
# Shows: Dataset Type: defects4j, Is Straightforward: false (missing source)
```

### Example 4: List Available

```bash
python -m cli.main agent list-all
# Shows all dataset types and processors
```

## CLI Commands

```bash
# Interactive creation
python -m cli.main agent create

# Direct API creation
python -m cli.main agent create-direct \
    --dataset-type <type> \
    --source <path> \
    [--processors <proc1,proc2>] \
    [--format <json|csv|jsonl>] \
    [--output <path>]

# List available
python -m cli.main agent list-all

# Explain query
python -m cli.main agent explain --query "<query>"
```

## Configuration

Edit `config/config.py` for customization:

```python
AGENTIC_CONFIG = {
    "enable_interactive_mode": True,
    "enable_direct_api": True,
    "auto_clarify_ambiguous_requests": True,
    "default_output_format": "json",
    "default_processing_pipeline": ["duplicate_remover"],
    "max_records_for_processing": 1000000,
    "enable_caching": True,
}
```

## Documentation

### Full Documentation
- **AGENTIC_DATASET_MAKER.md** - Complete reference guide
  - Architecture details
  - All dataset types
  - Processor descriptions
  - API reference
  - Use cases

### Quick Start
- **AGENTIC_QUICKSTART.md** - Get started quickly
  - Installation
  - Quick examples
  - Common use cases
  - Troubleshooting

### Examples
- **examples_agentic.py** - Comprehensive code examples
  - 10 different usage scenarios
  - Use cases
  - Advanced customization

## Use Cases

### 1. Research & Benchmarking
Create datasets for ML research and model benchmarking
```python
maker.create_dataset("defects4j with normalization and validation")
```

### 2. Data Pipeline Automation
Integrate into CI/CD for automated dataset generation
```python
result = maker.create_dataset_direct(
    dataset_type="promise",
    source="metrics.csv",
    processing_steps=["duplicate_remover"]
)
```

### 3. Interactive Exploration
Explore data and understand available datasets
```python
result = maker.create_dataset(
    "Show me available bug datasets",
    interactive=True
)
```

### 4. Custom Processing
Build complex processing workflows
```python
maker.create_dataset_direct(
    dataset_type="bugs_jar",
    processing_steps=[
        "data_validator",
        "code_normalizer",
        "duplicate_remover",
        "text_cleaner"
    ]
)
```

## Performance

- Small datasets (< 10k): ~5-10 seconds
- Medium datasets (10k-100k): ~30-60 seconds
- Large datasets (> 100k): Depends on processors
- Processing: ~1000-2000 records/second

## Supported Processors

| Processor | Purpose |
|-----------|---------|
| code_normalizer | Clean and normalize code |
| text_cleaner | Standardize text fields |
| data_validator | Validate records |
| duplicate_remover | Remove duplicates |

## Supported Formats

| Format | Use Case |
|--------|----------|
| JSON | Default, most flexible |
| CSV | Tabular data, Excel compatible |
| JSONL | Streaming, large datasets |

## Integration with Existing System

Seamlessly integrates with:
- ✓ All existing extractors
- ✓ All existing processors
- ✓ CLI system (new `agent` command group)
- ✓ Configuration system
- ✓ Logging system
- ✓ Export formats
- ✓ (Future) Neo4j integration

## Next Steps

1. **Try Interactive Mode**
   ```bash
   python -m cli.main agent create
   ```

2. **Read Full Documentation**
   - See `AGENTIC_DATASET_MAKER.md`

3. **Explore Examples**
   ```bash
   python examples_agentic.py
   ```

4. **Integrate into Your Pipeline**
   - Use direct API mode
   - Automate dataset creation

5. **Customize**
   - Create custom processors
   - Extend extractors
   - Modify configuration

## API Reference

### Main Class
```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()

# Interactive mode
result = maker.create_dataset(query, interactive=True)

# Direct API
result = maker.create_dataset_direct(
    dataset_type, source, processing_steps, output_format, output_path
)
```

### Result Structure
```python
{
    'status': 'success' or 'failed',
    'output_path': 'path/to/dataset.json',
    'total_records': 150,
    'extraction_info': {...},
    'processing_info': {...},
    'timestamp': '2024-11-19T10:30:00'
}
```

## Troubleshooting

### Source Not Found
- Ensure path exists and is accessible
- For repos: check .git folder exists
- For files: verify file is readable

### Dataset Type Not Recognized
- Use exact names from `list-all`
- Be more specific in query
- Use `explain` command to debug

### Slow Processing
- Try smaller source first
- Use fewer processors
- Use CSV format instead of JSON

## Future Enhancements

- [ ] Advanced LLM integration
- [ ] Result caching
- [ ] Parallel processing
- [ ] Custom metrics
- [ ] Dataset versioning
- [ ] Neo4j export
- [ ] Dataset diffing
- [ ] Advanced filtering

## Contributing

To extend the system:

1. **Add Custom Processor**
   - Extend `BaseProcessor`
   - Register in `MetricsRegistry`

2. **Add Custom Extractor**
   - Extend `BaseExtractor`
   - Register in factory

3. **Add New Dataset Type**
   - Create extractor
   - Add to metrics registry
   - Update documentation

## Support

For help:
- Check `AGENTIC_DATASET_MAKER.md`
- Run examples: `python examples_agentic.py`
- Use `agent explain` command
- Review logs for errors

---

**Enjoy creating datasets with intelligence!** 🚀

*Last Updated: November 2024*
