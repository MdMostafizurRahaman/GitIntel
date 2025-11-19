# Dataset Management System - Complete Summary

## 📋 সিস্টেম ওভারভিউ

সম্পূর্ণ dataset management platform যা **Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, Sourcerer Dataset, PROMISE Repository** প্রভৃতি বিভিন্ন ধরনের ডেটা:
- ✅ এক্সট্রাক্ট করা
- ✅ প্রসেস করা (নরমালাইজ, ক্লিন, ভ্যালিডেট)
- ✅ লেবেল করা (সেভেরিটি, কমপ্লেক্সিটি, টাইপ)
- ✅ Neo4j গ্রাফ ডাটাবেসে সংরক্ষণ
- ✅ এক্সপোর্ট করা (CSV, JSON, Parquet)

## 📁 Complete Folder Structure

```
Dataset/
├── __init__.py                 # Main package
├── requirements.txt            # Dependencies
│
├── config/
│   └── config.py               # All configurations
│
├── extractors/                 # Data Extraction Layer
│   ├── base_extractor.py       # Base class
│   ├── java_extractors.py      # Defects4J, ManySStuBs4J
│   ├── code_extractors.py      # CodeXGLUE, CodeSearchNet, Sourcerer
│   ├── metrics_extractors.py   # Bugs.jar, PROMISE
│   └── factory.py              # Factory pattern
│
├── processors/                 # Data Processing Layer
│   └── base_processor.py       # Normalizer, Cleaner, Validator, Deduplicator, Pipeline
│
├── labelers/                   # Data Labeling Layer
│   └── labeler.py              # BugSeverity, CodeComplexity, FeatureType, MultiLabel
│
├── neo4j/                      # Neo4j Integration
│   ├── manager.py              # Database operations
│   └── schema.py               # Data models & Cypher templates
│
├── cli/                        # Command-Line Interface
│   └── main.py                 # CLI commands (list, extract, process, label, import)
│
├── gui/                        # Desktop GUI (PyQt5)
│   └── app.py                  # Interactive application
│
├── api/                        # REST API (FastAPI)
│   └── server.py               # Web server & endpoints
│
├── utils/                      # Utilities
│   ├── logger.py               # Logging setup
│   └── helpers.py              # Helper functions
│
├── docs/                       # Documentation
│   ├── README.md               # User guide & usage
│   ├── ARCHITECTURE.md         # System architecture
│   ├── SETUP.md                # Installation & setup
│   └── EXAMPLES.md             # Complete examples
│
└── samples/                    # Sample data
```

## 🎯 7টি সাপোর্টেড ডেটাসেট

| # | নাম | ধরন | উপাদান | উৎস |
|---|------|------|--------|-----|
| 1 | **Defects4J** | বাগ ডেটা | Buggy/fixed pairs | Git repositories |
| 2 | **Bugs.jar** | জাভা বাগ | Class info, bugs, tests | JAR files |
| 3 | **ManySStuBs4J** | মাল্টি-ইস্যু | Issues, patches, commits | GitHub |
| 4 | **CodeXGLUE** | কোড মূলক | Code-to-code/text mappings | GitHub |
| 5 | **CodeSearchNet** | কোড সার্চ | Functions, documentation | Python repos |
| 6 | **Sourcerer** | সোর্স মাইনিং | Structure, dependencies, metrics | Projects |
| 7 | **PROMISE** | সফটওয়্যার মেট্রিক্স | Metrics, defect labels | CSV/ARFF/JSON |

## 🔧 Key Components

### 1. Extraction Layer (extractors/)
```python
extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()  # List[Dict]
```

**সাপোর্টেড অপারেশন**: Repository cloning, file parsing, JSON/CSV reading, JAR inspection

### 2. Processing Pipeline (processors/)
```python
pipeline = ProcessingPipeline()
pipeline.add_processor(CodeNormalizer())
pipeline.add_processor(TextCleaner())
pipeline.add_processor(DuplicateRemover())
processed = pipeline.process(records)
```

**প্রসেসরস**: CodeNormalizer, TextCleaner, DataValidator, DuplicateRemover

### 3. Labeling (labelers/)
```python
labeler = BugSeverityLabeler()  # বা অন্যকোনো labeler
labeled = labeler.label(records)
```

**লেবেলার্স**: BugSeverityLabeler, CodeComplexityLabeler, FeatureLabelClassifier, MultiLabelClassifier

### 4. Neo4j Integration (neo4j/)
```python
neo4j = get_neo4j_manager()
neo4j.create_node("Bug", {"id": "bug_001", "severity": "high"})
neo4j.find_nodes("Bug", {"severity": "critical"})
results = neo4j.query("MATCH (b:Bug) RETURN b LIMIT 10")
```

**নোড টাইপস**: Project, Bug, Commit, File, Function, Issue, CodeSnippet, Metric
**সম্পর্ক**: HAS_BUG, FIXED_BY, CONTAINS, CALLS, RELATED_TO, REPORTED_IN, etc.

### 5. CLI Tool (cli/)
```bash
python -m cli.main list-datasets
python -m cli.main extract --dataset-type defects4j --source /path --output data.json
python -m cli.main process --input raw.json --output processed.json --normalize-code
python -m cli.main label --input data.json --output labeled.json --label-type bug_severity
python -m cli.main import-to-neo4j --input data.json --dataset-name "My Dataset"
python -m cli.main status
```

### 6. GUI Application (gui/)
```bash
python -m gui.app
```

**ফিচার**:
- Dataset type selection
- Source/output path chooser
- Processing options
- Labeling options
- Real-time progress
- Data visualization
- Export functionality

### 7. REST API (api/)
```bash
python -m api.server  # http://127.0.0.1:8000
```

**Endpoints**:
- `GET /api/health` - Health check
- `GET /api/datasets` - All datasets
- `POST /api/extract` - Extract data
- `POST /api/process` - Process data
- `POST /api/label` - Label data
- `POST /api/export` - Export data
- `GET /api/neo4j/stats` - Database stats
- `POST /api/neo4j/import` - Import to Neo4j

## 🚀 ব্যবহার করার ৩টি উপায়

### 1️⃣ Command-Line Interface (CLI)
```bash
python -m cli.main extract --dataset-type defects4j --source /path --output data.json
```
**সেরা জন্য**: Automation, scripting, server environments

### 2️⃣ Desktop GUI
```bash
python -m gui.app
```
**সেরা জন্য**: Interactive use, visual feedback, testing

### 3️⃣ REST API
```bash
# Server চালু করুন
python -m api.server

# Python/JavaScript থেকে API call করুন
curl -X POST http://127.0.0.1:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"dataset_type": "defects4j", "source": "/path", "output_format": "json"}'
```
**সেরা জন্য**: Website integration, remote access, web applications

## 🔄 Complete Data Flow

```
1. SOURCE DATA
   ├─ Repository (Git)
   ├─ Files (JAR, CSV, JSON, ARFF)
   └─ Remote (URLs, APIs)
        ↓
2. EXTRACTION (extractors/)
   └─ Dataset-specific extraction logic
        ↓
3. RAW RECORDS
   └─ List of Dict with all data
        ↓
4. PROCESSING (processors/)
   ├─ CodeNormalizer (remove comments, whitespace)
   ├─ TextCleaner (truncate, remove extra spaces)
   ├─ DataValidator (check required fields)
   └─ DuplicateRemover (remove duplicates)
        ↓
5. PROCESSED RECORDS
   └─ Clean, validated data
        ↓
6. LABELING (labelers/)
   ├─ BugSeverityLabeler (critical/high/medium/low)
   ├─ CodeComplexityLabeler (simple/moderate/complex)
   ├─ FeatureLabelClassifier (bug/feature/refactoring)
   └─ MultiLabelClassifier (multiple tags)
        ↓
7. LABELED RECORDS
   └─ Enriched with labels/classifications
        ↓
8. STORAGE & ACCESS
   ├─ Neo4j (Graph queries)
   └─ File Export (CSV, JSON, Parquet)
        ↓
9. OUTPUT
   ├─ Graph Database (Neo4j)
   ├─ CSV Files
   ├─ JSON Files
   └─ Other formats
```

## 📊 Database Schema (Neo4j)

### উদাহরণ: একটি বাগ এবং এর সম্পর্কিত ডেটা

```cypher
// Create nodes
CREATE (p:Project {id: "proj_001", name: "MyProject"})
CREATE (b:Bug {id: "bug_001", title: "Login fails", severity: "high"})
CREATE (c:Commit {hash: "abc123", message: "Fix login bug"})
CREATE (f:File {path: "src/auth.java", language: "java"})
CREATE (fn:Function {name: "authenticate", lines: 45})

// Create relationships
CREATE (p)-[HAS_BUG]->(b)
CREATE (b)-[FIXED_BY]->(c)
CREATE (p)-[CONTAINS_FILE]->(f)
CREATE (f)-[CONTAINS_FUNCTION]->(fn)

// Query
MATCH (p:Project)-[HAS_BUG]->(b:Bug)-[FIXED_BY]->(c:Commit)
WHERE b.severity = "high"
RETURN p.name, b.title, c.message
```

## 🎓 Quick Start Example

```python
# Complete workflow in Python
from extractors.factory import create_extractor
from processors.base_processor import ProcessingPipeline, CodeNormalizer
from labelers.labeler import BugSeverityLabeler
from neo4j.manager import get_neo4j_manager

# 1. Extract
extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()

# 2. Process
pipeline = ProcessingPipeline().add_processor(CodeNormalizer())
processed = pipeline.process(records)

# 3. Label
labeler = BugSeverityLabeler()
labeled = labeler.label(processed)

# 4. Store in Neo4j
neo4j = get_neo4j_manager()
for record in labeled:
    neo4j.create_node("Bug", record)

# 5. Query
critical_bugs = neo4j.find_nodes("Bug", {"severity": "critical"})
```

## 🔐 Configuration

**.env** ফাইল:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
```

অথবা Python এ `config/config.py` এডিট করুন।

## 📦 Dependencies

```
neo4j>=5.0.0          # Neo4j driver
click>=8.0.0          # CLI framework
PyQt5>=5.15.0         # GUI framework
FastAPI>=0.68.0       # Web API
pandas>=1.3.0         # Data processing
requests>=2.25.0      # HTTP client
```

## 🧪 Testing & Validation

```bash
# সংযোগ পরীক্ষা করুন
python -c "from neo4j.manager import get_neo4j_manager; print('Connected!')"

# সব ডেটাসেট দেখুন
python -m cli.main list-datasets

# সিস্টেম স্ট্যাটাস চেক করুন
python -m cli.main status
```

## 📈 Scalability Features

- **Batch Processing**: Large datasets processed in batches
- **Parallel Processing**: Multi-worker support
- **Streaming**: Handle large files line-by-line
- **Pagination**: API supports pagination
- **Caching**: Results cached for reuse
- **Neo4j Indexing**: Automatic indexing for performance

## 🛠️ Extension Points

### নতুন Extractor যোগ করুন
```python
class MyExtractor(RepositoryExtractor):
    def extract(self):
        # Your extraction logic
        pass
```

### নতুন Processor যোগ করুন
```python
class MyProcessor(BaseProcessor):
    def process(self, records):
        # Your processing logic
        pass
```

### নতুন Labeler যোগ করুন
```python
class MyLabeler(BaseLabeler):
    def label(self, records):
        # Your labeling logic
        pass
```

## 📚 Documentation Files

| ফাইল | বিষয় |
|------|--------|
| `docs/README.md` | ব্যবহার গাইড ও ওভারভিউ |
| `docs/ARCHITECTURE.md` | সিস্টেম আর্কিটেকচার |
| `docs/SETUP.md` | ইনস্টলেশন ও সেটআপ |
| `docs/EXAMPLES.md` | কম্পিট উদাহরণ |

## 🎉 সাফল্য!

আপনার সম্পূর্ণ Dataset Management System প্রস্তুত! এখন:

1. ✅ **Installation করুন**: `docs/SETUP.md` পড়ুন
2. ✅ **Try examples**: `docs/EXAMPLES.md` দেখুন
3. ✅ **Use CLI/GUI/API**: আপনার পছন্দের ইন্টারফেস ব্যবহার করুন
4. ✅ **Extend**: নতুন extractors/processors/labelers যোগ করুন
5. ✅ **Deploy**: আপনার ওয়েবসাইটে integrate করুন

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Support**: See docs/ folder for detailed guides

## ⭐ Key Highlights

- ✨ 7টি different dataset types সাপোর্ট করে
- ✨ Modular & extensible architecture
- ✨ 3টি ভিন্ন ইন্টারফেস (CLI, GUI, API)
- ✨ Neo4j graph database integration
- ✨ Complete data pipeline (extract → process → label → store)
- ✨ Multi-format export (CSV, JSON, Parquet, etc.)
- ✨ Production-ready with error handling & logging
- ✨ Comprehensive documentation & examples

---

**Ready to manage your datasets? Let's go! 🚀**
