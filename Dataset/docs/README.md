# Dataset Management System

আপনার ওয়েবসাইটে Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, Sourcerer Dataset, PROMISE Repository-এর মতো বিভিন্ন ধরনের সোর্স কোড ও বাগ ডেটাসেট তৈরি, প্রসেসিং, এবং সরবরাহ করার পূর্ণাঙ্গ সিস্টেম।

## 📁 ফোল্ডার স্ট্রাকচার

```
Dataset/
├── config/                      # কনফিগারেশন ফাইল
│   └── config.py               # সব কিছুর সেটিংস
├── extractors/                 # ডেটা এক্সট্রাকশন
│   ├── base_extractor.py       # বেস ক্লাস
│   ├── java_extractors.py      # Defects4J, ManySStuBs4J
│   ├── code_extractors.py      # CodeXGLUE, CodeSearchNet, Sourcerer
│   ├── metrics_extractors.py   # Bugs.jar, PROMISE
│   └── factory.py              # এক্সট্রাকটর ফ্যাক্টরি
├── processors/                 # ডেটা প্রসেসিং
│   └── base_processor.py       # নরমালাইজ, ভ্যালিডেশন, ক্লিনিং
├── labelers/                   # ডেটা লেবেলিং
│   └── labeler.py              # বাগ সেভেরিটি, কমপ্লেক্সিটি, ফিচার টাইপ
├── neo4j/                      # Neo4j ইন্টিগ্রেশন
│   ├── manager.py              # Neo4j কানেকশন ও অপারেশন
│   └── schema.py               # ডেটা মডেল ও স্কিমা
├── cli/                        # কমান্ড-লাইন ইন্টারফেস
│   └── main.py                 # CLI কমান্ড
├── gui/                        # ডেস্কটপ GUI টুল
│   └── app.py                  # PyQt5 ইউজার ইন্টারফেস
├── api/                        # ওয়েবসাইট API
│   └── server.py               # FastAPI সার্ভার
├── utils/                      # ইউটিলিটি ফাংশন
│   ├── logger.py               # লগিং সেটআপ
│   └── helpers.py              # হেল্পার ফাংশন
├── docs/                       # ডকুমেন্টেশন
│   └── ARCHITECTURE.md         # আর্কিটেকচার গাইড
└── samples/                    # নমুনা ডেটা

```

## 🎯 সাপোর্টেড ডেটাসেট

### 1. **Defects4J**
- **প্রকার**: বাগ ডেটাসেট
- **উপাদান**: Buggy/fixed code pairs, bug descriptions
- **এক্সট্রাকশন**: Git repositories থেকে

### 2. **Bugs.jar**
- **প্রকার**: জাভা বাগ ডেটাসেট
- **উপাদান**: JAR ফাইল, ক্লাস ইনফো, টেস্ট কেস
- **এক্সট্রাকশন**: JAR ফাইল, metadata JSON

### 3. **ManySStuBs4J**
- **প্রকার**: মাল্টি-ইস্যু ডেটাসেট
- **উপাদান**: Issue tracking, patches, commits
- **এক্সট্রাকশন**: GitHub issues, pull requests

### 4. **CodeXGLUE**
- **প্রকার**: কোড-টু-কোড/কোড-টু-টেক্সট
- **উপাদান**: Code snippets, mappings
- **এক্সট্রাকশন**: Source files, JSONL data

### 5. **CodeSearchNet**
- **প্রকার**: কোড-টু-ডকুমেন্টেশন
- **উপাদান**: Functions, docstrings
- **এক্সট্রাকশন**: Python source files

### 6. **Sourcerer Dataset**
- **প্রকার**: সোর্স কোড মাইনিং
- **উপাদান**: Project structure, dependencies, metrics
- **এক্সট্রাকশন**: Maven/Gradle projects

### 7. **PROMISE Repository**
- **প্রকার**: মেট্রিক্স ডেটাসেট
- **উপাদান**: Software metrics, defect labels
- **এক্সট্রাকশন**: CSV, ARFF, JSON files

## 🚀 ব্যবহার করার উপায়

### CLI ব্যবহার করে

```bash
# ডেটাসেট লিস্ট দেখুন
python -m cli.main list-datasets

# ডেটা এক্সট্রাক্ট করুন
python -m cli.main extract \
  --dataset-type defects4j \
  --source /path/to/repo \
  --output extracted_data.json

# ডেটা প্রসেস করুন
python -m cli.main process \
  --input extracted_data.json \
  --output processed_data.json \
  --normalize-code \
  --clean-text \
  --remove-duplicates

# ডেটা লেবেল করুন
python -m cli.main label \
  --input processed_data.json \
  --output labeled_data.json \
  --label-type bug_severity

# Neo4j-এ ইমপোর্ট করুন
python -m cli.main import-to-neo4j \
  --input labeled_data.json \
  --dataset-name "My Dataset" \
  --project-id "proj_001"
```

### Python Code থেকে

```python
from extractors.factory import create_extractor
from processors.base_processor import ProcessingPipeline, CodeNormalizer
from labelers.labeler import BugSeverityLabeler

# এক্সট্রাক্ট
extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()

# প্রসেস
pipeline = ProcessingPipeline().add_processor(CodeNormalizer())
processed = pipeline.process(records)

# লেবেল
labeler = BugSeverityLabeler()
labeled = labeler.label(processed)

# Neo4j-এ সংরক্ষণ করুন
from neo4j.manager import get_neo4j_manager
neo4j = get_neo4j_manager()
for record in labeled:
    neo4j.create_node("Bug", record)
```

## 🗄️ Neo4j Schema

### Node Types
- `Project`: প্রকল্প তথ্য
- `Bug`: বাগ রিপোর্ট
- `Commit`: কমিট তথ্য
- `File`: সোর্স ফাইল
- `Function`: ফাংশন/মেথড
- `Issue`: ইস্যু টিকেট
- `CodeSnippet`: কোড স্নিপেট
- `Metric`: মেট্রিক তথ্য

### Relationships
- `HAS_BUG`: প্রকল্পের বাগ আছে
- `FIXED_BY`: বাগ ফিক্স হয়েছে
- `CONTAINS_FILE`: ফাইল আছে
- `CONTAINS_FUNCTION`: ফাংশন আছে
- `CALLS`: ফাংশন কল করে
- `RELATED_TO`: সম্পর্কিত
- `REPORTED_IN`: রিপোর্ট করা হয়েছে

## 📊 Processing Pipeline

```
Raw Data (Extracted)
        ↓
    Normalizer (Code normalization, whitespace handling)
        ↓
    TextCleaner (Text field cleanup, truncation)
        ↓
    Validator (Required fields, data quality)
        ↓
    DuplicateRemover (Remove duplicates by key)
        ↓
    Labeler (Add labels/classifications)
        ↓
Processed & Labeled Data
        ↓
    Neo4j Storage
        ↓
    Export (CSV, JSON, etc.)
```

## 🔧 কনফিগারেশন

`config/config.py` ফাইল এ এডিট করুন:

```python
# Neo4j সংযোগ
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password",
    "database": "neo4j",
}

# প্রসেসিং সেটিংস
PROCESSING_CONFIG = {
    "chunk_size": 1000,
    "batch_size": 100,
    "max_workers": 4,
}
```

## 📦 এক্সপোর্ট ফরম্যাট

- CSV
- JSON
- JSONL (Line-delimited JSON)
- Parquet
- GraphML (Neo4j compatible)
- Cypher (Neo4j queries)

## 🎨 ডেস্কটপ GUI (PyQt5)

```bash
python -m gui.app
```

Features:
- Dataset type selection
- Source path chooser
- Processing options
- Real-time progress
- Export options
- Visualization

## 🌐 API সার্ভার

```bash
python -m api.server
```

Endpoints:
- `GET /api/datasets` - ডেটাসেট লিস্ট
- `POST /api/extract` - এক্সট্রাক্ট নতুন ডেটা
- `POST /api/process` - প্রসেস ডেটা
- `POST /api/label` - লেবেল ডেটা
- `GET /api/neo4j/stats` - Neo4j স্ট্যাটিস্টিক্স
- `POST /api/export` - এক্সপোর্ট ডেটা

## 📝 Example Workflow

```bash
# 1. একটি Java প্রজেক্ট থেকে Defects4J ডেটা এক্সট্রাক্ট করুন
python -m cli.main extract \
  --dataset-type defects4j \
  --source ~/projects/my_java_repo \
  --output /tmp/defects4j_raw.json

# 2. কোড নরমালাইজ করুন এবং ডুপ্লিকেট সরান
python -m cli.main process \
  --input /tmp/defects4j_raw.json \
  --output /tmp/defects4j_processed.json \
  --normalize-code \
  --remove-duplicates

# 3. বাগ সেভেরিটি অনুযায়ী লেবেল করুন
python -m cli.main label \
  --input /tmp/defects4j_processed.json \
  --output /tmp/defects4j_labeled.json \
  --label-type bug_severity

# 4. Neo4j-এ ইমপোর্ট করুন
python -m cli.main import-to-neo4j \
  --input /tmp/defects4j_labeled.json \
  --dataset-name "Defects4J Dataset" \
  --project-id "defects4j_001"

# 5. স্ট্যাটাস চেক করুন
python -m cli.main status
```

## 🔌 Environment Variables

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
```

## 📚 Extensibility

### নতুন ডেটাসেট যোগ করা

1. `extractors/` ফোল্ডারে নতুন extractor বানান
2. `BaseExtractor` extend করুন
3. `extract()` method implement করুন
4. `factory.py` এ এন্ট্রি যোগ করুন

### নতুন Processor যোগ করা

1. `processors/` ফোল্ডারে নতুন ফাইল বানান
2. `BaseProcessor` extend করুন
3. `process()` method implement করুন
4. Pipeline-এ যোগ করুন

## ⚙️ সিস্টেম রিকোয়ারমেন্ট

- Python 3.8+
- Neo4j 4.0+
- 4GB RAM (কম পক্ষে)
- 10GB ডিস্ক স্পেস (ডেটা সেটের উপর নির্ভর করে)

## 📞 সাপোর্ট ও অবদান

Issues এবং pull requests স্বাগত জানাই।

## 📄 লাইসেন্স

MIT License

---

**তৈরি**: Dataset Management System v1.0  
**আপডেট**: `datetime.now()`  
**লক্ষ্য**: Comprehensive dataset management for AI/ML research
