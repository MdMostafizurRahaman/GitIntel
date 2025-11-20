# Agentic Dataset Maker - Quick Index

## 📍 Start Here

**New to Agentic Dataset Maker?**
1. Read this file first (you are here)
2. Read **AGENTIC_QUICKSTART.md** (5 min read)
3. Try the interactive mode: `python -m cli.main agent create`

---

## 📚 Documentation

### Quick References
- **AGENTIC_QUICKSTART.md** - Get started in 5 minutes
- **README_AGENTIC.md** - System overview and features
- **AGENTIC_STATUS_REPORT.md** - What was implemented

### Complete References
- **docs/AGENTIC_DATASET_MAKER.md** - Full API documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details

---

## 💻 Command Quick Reference

### List Available Datasets
```bash
python -m cli.main agent list-all
```

### Understand Query Parsing
```bash
python -m cli.main agent explain --query "your query here"
```

### Create Dataset (Interactive)
```bash
python -m cli.main agent create
```

### Create Dataset (Direct)
```bash
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source /path/to/repo \
    --processors code_normalizer,duplicate_remover \
    --format json
```

---

## 🐍 Python API Quick Reference

### Interactive Mode
```python
from agentic_dataset_maker import AgenticDatasetMaker

maker = AgenticDatasetMaker()
result = maker.create_dataset(
    "Create defects4j with code normalization",
    interactive=True
)
```

### Direct API
```python
result = maker.create_dataset_direct(
    dataset_type="defects4j",
    source="/path/to/repo",
    processing_steps=["code_normalizer"],
    output_format="json"
)

print(f"✓ {result['total_records']} records created")
```

### Check Query Interpretation
```python
request = maker.planner.parse_user_request(
    "I want a bugs_jar dataset"
)
print(f"Dataset type: {request.dataset_type}")
print(f"Processing: {request.processing_steps}")
```

---

## 📁 File Structure

```
Dataset/
├── agentic_dataset_maker.py           ← Main implementation
├── cli/main.py                        ← Updated with agent commands
├── config/config.py                   ← Updated with AGENTIC_CONFIG
├── examples_agentic.py                ← 10 runnable examples
├── test_agentic_validation.py         ← Validation tests (14/14 pass)
├── AGENTIC_QUICKSTART.md              ← This is what you should read first
├── AGENTIC_STATUS_REPORT.md           ← What was implemented
├── README_AGENTIC.md                  ← System overview
├── IMPLEMENTATION_SUMMARY.md          ← Technical details
├── AGENTIC_INDEX.md                   ← This file
└── docs/
    └── AGENTIC_DATASET_MAKER.md       ← Complete reference
```

---

## 🎯 Common Tasks

### Task: Create a defects4j dataset
```bash
# Interactive
python -m cli.main agent create
# Answer: "defects4j with code normalization"

# Or direct
python -m cli.main agent create-direct \
    --dataset-type defects4j \
    --source d:\GitIntel\druid \
    --processors code_normalizer,duplicate_remover
```

### Task: Export to CSV
```bash
python -m cli.main agent create-direct \
    --dataset-type bugs_jar \
    --source bugs.json \
    --format csv
```

### Task: Apply multiple processors
```bash
python -m cli.main agent create-direct \
    --dataset-type promise \
    --source metrics.csv \
    --processors data_validator,text_cleaner,duplicate_remover \
    --format json
```

### Task: Understand how agent interprets my query
```bash
python -m cli.main agent explain --query "I want a bug dataset"
```

---

## 📊 Supported Datasets

1. **defects4j** - Real Java bugs (buggy/fixed code pairs)
2. **bugs_jar** - Large Java bug dataset (with metrics)
3. **codexglue** - Code-to-code transformation
4. **codesearchnet** - Code-to-documentation mapping
5. **sourcerer** - Source code mining
6. **promise** - Software metrics for defect prediction
7. **manystubs4j** - Large Java issues dataset

---

## ⚙️ Available Processors

- **code_normalizer** - Clean and normalize code
- **text_cleaner** - Standardize text fields
- **data_validator** - Validate record integrity
- **duplicate_remover** - Remove duplicate records

---

## 📤 Output Formats

- **json** - Single JSON object per file (flexible, default)
- **csv** - Tabular format (Excel-compatible)
- **jsonl** - JSON Lines (streaming, large datasets)

---

## ✅ Testing

Run validation tests:
```bash
python test_agentic_validation.py
# Expected: All 14 tests pass
```

---

## 🧪 Examples

Run interactive examples:
```bash
python examples_agentic.py
# Choose which examples to run
```

Examples included:
1. Interactive Mode (Simple)
2. Direct API Mode
3. Query Parsing & Interpretation
4. Metrics Registry
5. Complex Processing Pipeline
6. Use Case: Research/Benchmarking
7. Use Case: Pipeline Automation
8. Use Case: Interactive Exploration
9. Output Inspection & Analysis
10. Advanced Customization

---

## 🔍 Troubleshooting

### Issue: "Dataset type not detected"
**Solution**: Be more specific. Use exact dataset names or use `list-all` command.

### Issue: "Source not found"
**Solution**: Verify path exists and is accessible. For repos, check .git folder.

### Issue: "Processing is slow"
**Solution**: Use smaller source first, or use CSV format instead of JSON.

---

## 🚀 Next Steps

1. ✅ **Start**: Read AGENTIC_QUICKSTART.md (5 minutes)
2. ✅ **Try**: Run `python -m cli.main agent create` (2 minutes)
3. ✅ **Explore**: Run `python examples_agentic.py` (5 minutes)
4. ✅ **Learn**: Read docs/AGENTIC_DATASET_MAKER.md (20 minutes)
5. ✅ **Integrate**: Use in your projects

---

## 📞 Help

**Quick Help**: `python -m cli.main agent --help`  
**List Options**: `python -m cli.main agent list-all`  
**Explain Query**: `python -m cli.main agent explain --query "..."`  
**View Examples**: `python examples_agentic.py`  
**Run Tests**: `python test_agentic_validation.py`  

---

## 📋 Implementation Status

- ✅ Core system implemented
- ✅ 7 dataset types supported
- ✅ 4 processors available
- ✅ 2 interaction modes (interactive + direct API)
- ✅ CLI commands integrated
- ✅ Documentation complete (37KB)
- ✅ 10 examples provided
- ✅ 14 validation tests (100% pass rate)
- ✅ Production ready

---

## 🎓 Learning Path

### Beginner
1. AGENTIC_QUICKSTART.md (quick overview)
2. Try: `python -m cli.main agent create` (hands-on)
3. Run: `python examples_agentic.py` (see examples)

### Intermediate
1. README_AGENTIC.md (system overview)
2. Try: Create a few datasets manually
3. Learn: Try all 4 subcommands

### Advanced
1. docs/AGENTIC_DATASET_MAKER.md (complete reference)
2. IMPLEMENTATION_SUMMARY.md (technical details)
3. Review: agentic_dataset_maker.py (source code)
4. Extend: Create custom processors

---

## 💡 Pro Tips

1. **Use interactive mode first** to understand what's available
2. **Use explain command** to debug query interpretation
3. **List available options** to see all datasets and processors
4. **Check examples** for your specific use case
5. **Read documentation** for advanced features

---

## 🎯 Use Cases

- 🔬 **Research** - Create clean datasets for ML experiments
- 🏭 **Automation** - Integrate into CI/CD pipelines
- 📊 **Analysis** - Explore and analyze available data
- 🛠️ **Development** - Build custom data processing workflows

---

**Version**: 1.0 (November 2024)  
**Status**: ✅ Production Ready  
**Quality**: 100% Test Pass Rate  
**Documentation**: Complete  

---

**Ready to get started?** 👇

```bash
# Option 1: Interactive
python -m cli.main agent create

# Option 2: Learn by example
python examples_agentic.py

# Option 3: Read documentation
cat AGENTIC_QUICKSTART.md
```

Enjoy creating datasets! 🚀
