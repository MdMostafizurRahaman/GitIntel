# 📊 Dataset Management System

**A Comprehensive, Production-Ready System for Managing Multiple Dataset Types**

Bengali: **বহুমুখী ডেটাসেট ম্যানেজমেন্ট সিস্টেম - Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, Sourcerer, PROMISE সমর্থন করে**

---

## 🎯 Overview

This system provides a **complete, modular, and extensible solution** for managing datasets like:
- **Defects4J** - Real bugs from Java projects
- **Bugs.jar** - Large-scale Java bug dataset
- **ManySStuBs4J** - Java dataset with multiple issues
- **CodeXGLUE** - Code-to-code/code-to-text mappings
- **CodeSearchNet** - Code-to-documentation mappings
- **Sourcerer Dataset** - Large-scale source code mining
- **PROMISE Repository** - Software metrics and defect prediction

### এই সিস্টেম সম্পূর্ণ করে:

✅ **Data Extraction** - সকল 7 টি ডেটাসেট টাইপ থেকে ডেটা নিষ্কাশন  
✅ **Data Processing** - নর্মালাইজেশন, ক্লিনিং, ভ্যালিডেশন, ডি-ডুপ্লিকেশন  
✅ **Data Labeling** - স্বয়ংক্রিয় শ্রেণীবিভাগ (সেভারিটি, জটিলতা, ফিচার টাইপ)  
✅ **Neo4j Storage** - গ্রাফ ডেটাবেস ইন্টিগ্রেশন  
✅ **3 User Interfaces** - CLI, Desktop GUI (PyQt5), REST API (FastAPI)  
✅ **Complete Documentation** - সেটআপ, আর্কিটেকচার, উদাহরণ সহ  

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Clone or create Dataset folder
cd d:\GitIntel\Dataset

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Neo4j (See docs/SETUP.md for details)
```

### 2️⃣ Configure

```bash
# Create .env file with Neo4j credentials
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3️⃣ Test Connection

```bash
python -m cli.main status
```

### 4️⃣ Extract Data

```bash
python -m cli.main extract \
  --dataset-type defects4j \
  --source /path/to/repo \
  --output data.json
```

### 5️⃣ Process & Label

```bash
# Process
python -m cli.main process \
  --input data.json \
  --output processed.json \
  --normalize-code --clean-text

# Label
python -m cli.main label \
  --input processed.json \
  --output labeled.json \
  --label-type bug_severity
```

### 6️⃣ Import to Neo4j

```bash
python -m cli.main import-to-neo4j \
  --input labeled.json \
  --dataset-name "My Dataset" \
  --project-id "proj_001"
```

---

## 📚 Documentation

| Document | Purpose | Link |
|----------|---------|------|
| **SETUP.md** | Installation & configuration guide | `docs/SETUP.md` |
| **ARCHITECTURE.md** | System design & components | `docs/ARCHITECTURE.md` |
| **EXAMPLES.md** | 8+ complete usage examples | `docs/EXAMPLES.md` |
| **SUMMARY.md** | Quick reference & overview | `SUMMARY.md` |
| **INDEX.py** | Quick reference guide | `INDEX.py` |

---

## 🎮 User Interfaces

### Command-Line Interface (CLI)

```bash
# List all supported datasets
python -m cli.main list-datasets

# Extract data
python -m cli.main extract --dataset-type defects4j --source /path --output data.json

# Process data
python -m cli.main process --input data.json --output processed.json --normalize-code

# Label data
python -m cli.main label --input data.json --output labeled.json --label-type bug_severity

# Import to Neo4j
python -m cli.main import-to-neo4j --input data.json --dataset-name "My Data"

# Check status
python -m cli.main status
```

### Desktop GUI (PyQt5 or tkinter)

```bash
# Option 1: PyQt5 GUI (requires installation)
python -m gui.app

# Option 2: tkinter GUI (built-in, no installation needed)
python -m gui.app_tkinter
```

**GUI Features:**
- Interactive dataset selection
- Source path browsing
- Real-time processing logs
- Progress tracking
- Data preview and statistics
- Multi-format export

**Choose tkinter if you don't want to install PyQt5**

### REST API (FastAPI)

```bash
python -m api.server
# Server starts at http://127.0.0.1:8000
```

API Endpoints:
- `POST /api/extract` - Extract data
- `POST /api/process` - Process data
- `POST /api/label` - Label data
- `POST /api/export` - Export to format
- `POST /api/neo4j/import` - Import to Neo4j
- `GET /api/datasets` - List datasets
- `GET /api/status` - System status
- [And 5 more endpoints...]

---

## 📁 Folder Structure

```
Dataset/
├── config/                 # Configuration files
│   └── config.py          # All settings & constants
├── extractors/            # Data extraction (7 types)
│   ├── base_extractor.py
│   ├── java_extractors.py
│   ├── code_extractors.py
│   ├── metrics_extractors.py
│   └── factory.py
├── processors/            # Data processing pipeline
│   └── base_processor.py
├── labelers/              # Data labeling & classification
│   └── labeler.py
├── neo4j/                 # Neo4j database integration
│   ├── manager.py
│   └── schema.py
├── cli/                   # Command-line interface
│   └── main.py
├── gui/                   # Desktop GUI
│   └── app.py
├── api/                   # REST API
│   └── server.py
├── utils/                 # Utility functions
│   ├── logger.py
│   └── helpers.py
├── docs/                  # Documentation
│   ├── README.md
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   └── EXAMPLES.md
├── requirements.txt       # Dependencies
├── SUMMARY.md            # Quick reference
└── INDEX.py              # Quick reference guide
```

---

## 🛠️ Supported Operations

### Data Extraction

Supports 7 dataset types with format-specific parsers:

| Dataset | Source | Parser |
|---------|--------|--------|
| Defects4J | Git repo | buggy.java/fixed.java pairs |
| Bugs.jar | JAR files | zipfile + metadata |
| ManySStuBs4J | Git repo | issue directories |
| CodeXGLUE | JSON/JSONL | code-to-text mappings |
| CodeSearchNet | Git repo | docstrings extraction |
| Sourcerer | Maven/Gradle | project structure |
| PROMISE | CSV/ARFF/JSON | metrics data |

### Data Processing

- **CodeNormalizer** - Remove comments, normalize whitespace
- **TextCleaner** - Truncate long fields, clean text
- **DataValidator** - Validate required fields & integrity
- **DuplicateRemover** - Remove duplicate records
- **ProcessingPipeline** - Chain processors together

### Data Labeling

- **BugSeverityLabeler** - Critical/High/Medium/Low
- **CodeComplexityLabeler** - Simple/Moderate/Complex/VeryComplex
- **FeatureLabelClassifier** - Feature type classification (7 types)
- **MultiLabelClassifier** - Assign multiple labels

### Storage & Querying

**Neo4j Graph Database:**
- 8 Node Types: Project, Bug, Commit, File, Function, Issue, CodeSnippet, Metric
- 11 Relationship Types: HAS_BUG, FIXED_BY, CONTAINS_FILE, etc.
- Pre-built Cypher templates for common queries
- CRUD operations, batch imports, statistics

---

## 💾 Configuration

All settings in `config/config.py`:

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password",
    "database": "neo4j"
}

DATASET_CONFIGS = {
    "defects4j": {...},
    "bugs_jar": {...},
    # ... all 7 datasets
}

PROCESSING_CONFIG = {
    "chunk_size": 1000,
    "batch_size": 100,
    "max_workers": 4,
    "timeout": 300,
}
```

Or use environment variables:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
LOG_LEVEL=INFO
```

---

## 🔧 Python API

Use the system programmatically:

```python
from extractors.factory import create_extractor
from processors.base_processor import ProcessingPipeline, CodeNormalizer
from labelers.labeler import BugSeverityLabeler
from neo4j.manager import get_neo4j_manager

# Extract
extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()

# Process
pipeline = ProcessingPipeline()
pipeline.add_processor(CodeNormalizer())
processed = pipeline.process(records)

# Label
labeler = BugSeverityLabeler()
labeled = labeler.label(processed)

# Store
neo4j = get_neo4j_manager()
for record in labeled:
    neo4j.create_node("Bug", record)
neo4j.close()
```

---

## 🎓 Complete Workflows

### Workflow 1: CLI Pipeline

```bash
# Extract → Process → Label → Import
python -m cli.main extract --dataset-type defects4j --source /repo --output raw.json
python -m cli.main process --input raw.json --output processed.json --normalize-code
python -m cli.main label --input processed.json --output labeled.json --label-type bug_severity
python -m cli.main import-to-neo4j --input labeled.json --dataset-name "My Data"
```

### Workflow 2: Python Script

```python
from Dataset.extractors.factory import create_extractor
# ... (see example above)
```

### Workflow 3: GUI Application

```bash
python -m gui.app
# Use interactive tabs to extract, process, label, view, export
```

### Workflow 4: REST API

```bash
python -m api.server  # Starts at http://127.0.0.1:8000
# Use HTTP requests to all endpoints
```

---

## ✨ Key Features

### 🔄 Modular Architecture
- Separate, independent modules for each component
- Factory pattern for easy extensibility
- Clear interfaces (base classes) for all plugins

### 📊 7 Dataset Types
- Pre-built extractors for all major dataset types
- Format-specific parsing (JSONL, CSV, ARFF, JAR, Git repos)
- Flexible source support (files, directories, URLs)

### 🔗 Neo4j Integration
- Graph database for complex relationship queries
- Pre-defined schema (8 nodes, 11 relationships)
- Batch import operations with progress tracking
- Pre-built Cypher query templates

### 💻 3 User Interfaces
- **CLI**: Automated scripts & pipelines
- **GUI**: Interactive desktop application
- **API**: Web service integration

### 📚 Complete Documentation
- Installation & setup guide
- Architecture documentation
- 8+ complete examples
- Troubleshooting guide
- API reference

### 🚀 Production-Ready
- Error handling & retry logic
- Progress tracking & logging
- Configuration management
- Type hints throughout
- Comprehensive docstrings

---

## 📋 System Requirements

### Software
- Python 3.8+
- Neo4j 4.0+
- Git (for some dataset types)

### Python Packages
```
neo4j>=5.0.0          Database driver
click>=8.0.0          CLI framework
PyQt5>=5.15.0         GUI framework
FastAPI>=0.68.0       Web API
uvicorn>=0.15.0       ASGI server
pandas>=1.3.0         Data processing
requests>=2.25.0      HTTP client
```

### Hardware (Recommended)
- 4GB+ RAM
- 10GB+ disk space
- Dual-core processor

---

## 🔍 Quick Reference

### Commands

```bash
# Extract from Defects4J
python -m cli.main extract --dataset-type defects4j --source /path --output data.json

# Process with all options
python -m cli.main process --input data.json --output processed.json \
  --normalize-code --clean-text --validate --remove-duplicates

# Label with specific type
python -m cli.main label --input data.json --output labeled.json \
  --label-type bug_severity

# Import to Neo4j
python -m cli.main import-to-neo4j --input data.json --dataset-name "My Data" --project-id "proj_001"

# Check system status
python -m cli.main status

# List all datasets
python -m cli.main list-datasets
```

### Python Imports

```python
# Extraction
from extractors.factory import create_extractor
from extractors.java_extractors import Defects4JExtractor

# Processing
from processors.base_processor import ProcessingPipeline, CodeNormalizer

# Labeling
from labelers.labeler import BugSeverityLabeler

# Database
from neo4j.manager import get_neo4j_manager

# Utilities
from utils.logger import setup_logger
from utils.helpers import generate_hash
```

---

## 🤝 Extensibility

### Add Custom Extractor

```python
from extractors.base_extractor import BaseExtractor

class MyExtractor(BaseExtractor):
    def validate(self):
        # Validate source
        pass
    
    def extract(self):
        # Extract and return records
        return records
```

Then register in `factory.py`:
```python
elif dataset_type == "my_dataset":
    return MyExtractor(source, config)
```

### Add Custom Processor

```python
from processors.base_processor import BaseProcessor

class MyProcessor(BaseProcessor):
    def process(self, records):
        # Process records
        return processed_records
```

### Add Custom Labeler

```python
from labelers.labeler import BaseLabeler

class MyLabeler(BaseLabeler):
    def label(self, records):
        # Label records
        return labeled_records
```

---

## 🐛 Troubleshooting

### Neo4j Connection Failed
```bash
# Check if Neo4j is running
sudo systemctl status neo4j

# Verify connection
python -m cli.main status
```

### Module Not Found
```bash
# Activate environment and install
pip install -r requirements.txt
```

### GUI Won't Start
```bash
# Reinstall PyQt5
pip install PyQt5 --force-reinstall
```

See `docs/SETUP.md` for more troubleshooting.

---

## 📖 Learn More

1. **Get Started**: Read `docs/SETUP.md`
2. **Understand Design**: Read `docs/ARCHITECTURE.md`
3. **See Examples**: Read `docs/EXAMPLES.md`
4. **Quick Reference**: Read `SUMMARY.md` or `INDEX.py`

---

## 📞 Support

For issues, questions, or improvements:

1. Check `docs/SETUP.md` for common issues
2. Review `docs/EXAMPLES.md` for usage patterns
3. Check `docs/ARCHITECTURE.md` for design details
4. Run `python -m cli.main --help` for command help

---

## ✅ Status

**System Status**: ✅ **COMPLETE & PRODUCTION-READY**

- ✅ 26 complete source files
- ✅ 7 dataset extractors
- ✅ Full processing pipeline
- ✅ 4 labeling types
- ✅ Neo4j integration
- ✅ CLI interface (6 commands)
- ✅ GUI application (PyQt5)
- ✅ REST API (12 endpoints)
- ✅ Complete documentation
- ✅ Error handling & logging
- ✅ Configuration management

**Ready to use!** Start with `docs/SETUP.md` → then choose your interface (CLI/GUI/API).

---

**Happy Dataset Management! 🚀**

*Sistema diseñado con modular architecture, extensibility in mind, production-ready code.*  
*সিস্টেমটি মডুলার আর্কিটেকচার, সম্প্রসারণযোগ্যতা এবং প্রোডাকশন-রেডি কোডের সাথে ডিজাইন করা হয়েছে।*
