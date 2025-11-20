# Agentic Dataset Maker - Quick Start Guide

## Installation

The agentic dataset maker is already integrated into your Dataset folder. No additional installation needed!

## Quick Examples

### Example 1: Simple Interactive Mode

```bash
cd d:\GitIntel\Dataset

# Run the interactive CLI
python -m cli.main agent create

# Follow the prompts:
# 1. Describe what dataset you want
# 2. Agent asks clarifying questions
# 3. Get your dataset
```

### Example 2: Create Defects4J Dataset

```bash
# Interactive
python -m cli.main agent create
# Answer: "I want a defects4j dataset with code normalization"
# Provide Java repository path

# Or direct (if you know exactly what you want)
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source "d:\GitIntel\druid" \
    --processors code_normalizer,duplicate_remover \
    --format json \
    --output output/defects4j_clean.json
```

### Example 3: Bugs.jar Dataset with Metrics

```bash
python -m cli.main agent create-direct \
    --dataset-type bugs_jar \
    --source "d:\GitIntel\Dataset\generated_datasets\bugs_jar_dataset.json" \
    --processors data_validator,duplicate_remover \
    --format csv \
    --output output/bugs_jar_clean.csv
```

### Example 4: CodeSearchNet with Documentation

```bash
python -m cli.main agent create
# Answer: "I need CodeSearchNet data with cleaned text and CSV format"
# Provide source repository
```

## In Python Code

### Simple Usage

```python
from agentic_dataset_maker import AgenticDatasetMaker

# Create maker
maker = AgenticDatasetMaker()

# Interactive mode (agent asks questions)
result = maker.create_dataset(
    "Create a defects4j dataset with code normalization"
)

if result['status'] == 'success':
    print(f"✓ Dataset created: {result['output_path']}")
    print(f"  Records: {result['total_records']}")
```

### Direct API Mode

```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()

# Create dataset without interaction
result = maker.create_dataset_direct(
    dataset_type="defects4j",
    source="d:\\GitIntel\\druid",
    processing_steps=["code_normalizer", "duplicate_remover"],
    output_format="json",
    output_path="output/dataset.json"
)

print(f"✓ Created {result['total_records']} records")
print(f"  Location: {result['output_path']}")
```

### Understanding Query Interpretation

```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()

# See how agent interprets your query
request = maker.planner.parse_user_request(
    "I want a bugs_jar dataset with cleaned text and no duplicates"
)

print(f"Dataset Type: {request.dataset_type}")
print(f"Processing: {request.processing_steps}")
print(f"Output Format: {request.output_format}")
print(f"Straightforward: {request.is_straightforward}")
```

## Dataset Types

### 1. Defects4J
Real Java bugs with buggy/fixed code pairs
```bash
python -m cli.main agent create
# Query: "defects4j from /path/to/java/repo"
```

### 2. Bugs.jar
Large Java bug dataset with metrics
```bash
python -m cli.main agent create-direct \
    --dataset-type bugs_jar \
    --source "path/to/bugs_jar.json"
```

### 3. CodeXGLUE
Code-to-code transformation
```bash
python -m cli.main agent create
# Query: "CodeXGLUE code transformation dataset"
```

### 4. CodeSearchNet
Code-to-documentation mapping
```bash
python -m cli.main agent create-direct \
    --dataset-type codesearchnet \
    --source "/path/to/code"
```

### 5. Sourcerer
Source code mining
```bash
python -m cli.main agent create-direct \
    --dataset-type sourcerer \
    --source "/path/to/code"
```

### 6. PROMISE
Software metrics for defect prediction
```bash
python -m cli.main agent create-direct \
    --dataset-type promise \
    --source "path/to/metrics.csv"
```

### 7. ManySStuBs4J
Large Java issue dataset
```bash
python -m cli.main agent create-direct \
    --dataset-type manystubs4j \
    --source "/path/to/code"
```

## Processing Options

Apply processing to clean your data:

- **code_normalizer** - Clean and normalize code
- **text_cleaner** - Standardize text fields
- **data_validator** - Validate and filter records
- **duplicate_remover** - Remove duplicate records

### Example: Multiple Processors

```bash
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source "d:\GitIntel\druid" \
    --processors code_normalizer,text_cleaner,duplicate_remover,data_validator \
    --format json
```

## Output Formats

- **json** - JSON format (default), one object per file
- **csv** - CSV format, one row per record
- **jsonl** - JSON Lines, one JSON object per line

## Use Cases

### Research/ML Training
```python
# Get clean dataset for ML model training
result = maker.create_dataset_direct(
    dataset_type="defects4j",
    source="bug_repo",
    processing_steps=["code_normalizer", "data_validator", "duplicate_remover"],
    output_format="json"
)
```

### Data Pipeline
```python
# Automated dataset generation
result = maker.create_dataset_direct(
    dataset_type="promise",
    source="metrics.csv",
    processing_steps=["duplicate_remover"],
    output_format="csv"
)
```

### Interactive Exploration
```python
# Explore data interactively
result = maker.create_dataset(
    "Create a bugs_jar dataset and show me the records",
    interactive=True
)
```

## Useful CLI Commands

```bash
# List all available datasets and processors
python -m cli.main agent list-all

# Understand how agent interprets a query
python -m cli.main agent explain --query "I want a bug dataset"

# Create with custom output
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source "/path/to/repo" \
    --output "my_dataset.json"
```

## Troubleshooting

### Issue: "Source not found"
```
Ensure:
- Path exists and is accessible
- Repository has .git folder (for repo-based datasets)
- File is readable (for file-based datasets)
```

### Issue: "Dataset type not recognized"
```
Solution:
- Use exact dataset names from list-all
- Be more specific in query
- Use agent explain to debug
```

### Issue: "Processing is slow"
```
Tips:
- Use smaller source files first
- Run with fewer processors
- Use CSV format instead of JSON
- Check disk space availability
```

## Next Steps

1. **Read Full Documentation** - See `AGENTIC_DATASET_MAKER.md`
2. **Explore Existing Datasets** - Check `generated_datasets/`
3. **Create Your First Dataset** - Use examples above
4. **Integrate with Your Pipeline** - Use direct API mode
5. **Customize Processors** - Create your own processors

## Contact & Support

For issues or feature requests:
- Check existing documentation
- Review examples in this guide
- Check dataset generation logs
- Inspect config/config.py for customization

---

**Happy Dataset Making!** 🚀
