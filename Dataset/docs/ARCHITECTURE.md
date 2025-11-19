# Dataset Management System - Architecture Guide

## System Overview

একটি সম্পূর্ণ dataset management platform যা Defects4J, Bugs.jar, ManySStuBs4J, CodeXGLUE, CodeSearchNet, Sourcerer Dataset, PROMISE Repository-এর মতো বিভিন্ন ধরনের ডেটা তৈরি, প্রসেস, লেবেল করে Neo4j-এ সংরক্ষণ এবং export করতে সাহায্য করে।

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│               User Interface Layer                       │
│  ┌──────────────────┐   ┌──────────────────┐            │
│  │   Desktop GUI    │   │    Web API       │            │
│  │    (PyQt5)       │   │   (FastAPI)      │            │
│  └──────────────────┘   └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│          Business Logic Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Extract  │→ │ Process  │→ │  Label   │             │
│  │  (7 DS)  │  │ (Pipeline)│  │ (Classify)│             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            Database & Storage Layer                     │
│  ┌──────────────┐   ┌──────────────┐                  │
│  │   Neo4j      │   │  File Storage│                  │
│  │ (Graph DB)   │   │  (JSON/CSV)  │                  │
│  └──────────────┘   └──────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Extraction Layer (extractors/)

**Purpose**: বিভিন্ন ডেটা সোর্স থেকে ডেটা নিষ্কাশন

**Components**:
- `BaseExtractor`: সকল extractors এর parent class
- `Defects4JExtractor`: Java bug pairs নিষ্কাশন
- `ManySStuBs4JExtractor`: GitHub issues ও patches নিষ্কাশন
- `BugsJarExtractor`: JAR ফাইল থেকে class information নিষ্কাশন
- `CodeXGLUEExtractor`: Code-to-code/code-to-text mappings নিষ্কাশন
- `CodeSearchNetExtractor`: Documented functions নিষ্কাশন
- `SourcererExtractor`: Project structure ও dependencies নিষ্কাশন
- `PROMISEExtractor`: Software metrics (CSV/ARFF/JSON) নিষ্কাশন
- `Factory`: সঠিক extractor তৈরি করে

**Flow**:
```
Source (Repo/File/URL)
    ↓
Extractor.extract()
    ↓
Data Validation
    ↓
List[Dict] (Raw Records)
```

### 2. Processing Layer (processors/)

**Purpose**: নিষ্কৃত ডেটা পরিষ্কার, স্বাভাবিক ও যাচাই করা

**Components**:
- `CodeNormalizer`: কোড স্বাভাবিকীকরণ (comment/whitespace removal)
- `TextCleaner`: টেক্সট ফিল্ড পরিষ্কার ও truncation
- `DataValidator`: বাধ্যতামূলক ফিল্ড ও ডেটা গুণমান যাচাই
- `DuplicateRemover`: ডুপ্লিকেট রেকর্ড সরানো
- `ProcessingPipeline`: একাধিক processor chain করা

**Flow**:
```
Raw Records
    ↓
CodeNormalizer → TextCleaner → DataValidator → DuplicateRemover
    ↓
Processed Records
```

**Example**:
```python
pipeline = ProcessingPipeline()
pipeline.add_processor(CodeNormalizer())
pipeline.add_processor(TextCleaner())
pipeline.add_processor(DuplicateRemover())
processed = pipeline.process(raw_records)
```

### 3. Labeling Layer (labelers/)

**Purpose**: রেকর্ডকে সেভেরিটি, কমপ্লেক্সিটি, ফিচার টাইপ ইত্যাদি অনুযায়ী শ্রেণীভুক্ত করা

**Components**:
- `BugSeverityLabeler`: বাগ severity নির্ধারণ (critical/high/medium/low)
- `CodeComplexityLabeler`: কোড complexity লেবেল (simple/moderate/complex/very_complex)
- `FeatureLabelClassifier`: feature type শ্রেণীভুক্ত (bug_fix/feature/refactoring/etc)
- `MultiLabelClassifier`: একাধিক labels নির্ধারণ

**Heuristics**:
- **Severity**: Keywords analysis, description length
- **Complexity**: LOC, cyclomatic complexity, parameters
- **Type**: Keyword matching in title/description/message

### 4. Neo4j Layer (neo4j/)

**Purpose**: ডেটা graph database-এ সংরক্ষণ ও query

**Components**:
- `Neo4jManager`: Connection, CRUD operations, querying
- `Schema`: Node/Relationship definitions, Data models, Cypher templates

**Node Types**:
```
Project ──HAS_BUG──→ Bug
  │
  ├─CONTAINS_FILE──→ File
  │                    │
  │                    └─CONTAINS_FUNCTION──→ Function
  │                                              │
  │                                              └─CALLS──→ Function
  │
  └─CHANGED_IN──→ Commit
                     │
                     └─FIXED_BY──← Bug

CodeSnippet ──HAS_METRIC──→ Metric
Issue ──REPORTED_IN──→ Project
```

### 5. CLI Interface (cli/)

**Purpose**: কমান্ড-লাইন থেকে পুরো workflow চালানো

**Commands**:
```bash
list-datasets          # সব dataset লিস্ট
extract                # নতুন ডেটা extract করা
process                # ডেটা process করা
label                  # ডেটা label করা
import-to-neo4j        # Neo4j-এ import করা
status                 # সিস্টেম স্ট্যাটাস চেক
```

### 6. GUI Interface (gui/)

**Purpose**: ডেস্কটপ GUI থেকে ইন্টারঅ্যাক্টিভ কাজ

**Features**:
- Dataset selection with description
- Source/output path selection
- Processing options checkbox
- Real-time progress & logging
- Data preview & statistics
- Export in multiple formats

### 7. API Server (api/)

**Purpose**: ওয়েবসাইট থেকে REST API দ্বারা এক্সেস

**Endpoints**:
```
GET  /api/health              Health check
GET  /api/datasets            All datasets
GET  /api/datasets/{id}       Specific dataset
POST /api/extract             Extract data
POST /api/process             Process data
POST /api/label               Label data
POST /api/export              Export data
GET  /api/neo4j/stats         Neo4j statistics
POST /api/neo4j/import        Import to Neo4j
GET  /api/data/{file_id}      Download file
GET  /api/status              System status
```

## Data Flow Diagram

### Complete Workflow

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: EXTRACTION                                          │
│  Select dataset type → Choose source → Extract data         │
│  Output: raw_data.json (with metadata)                       │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: PROCESSING                                          │
│  Load raw data → Apply processing pipeline → Clean output    │
│  - Normalize code (remove comments, whitespace)             │
│  - Clean text (truncate, remove extra spaces)              │
│  - Validate records (required fields, data quality)        │
│  - Remove duplicates (by ID or hash)                       │
│  Output: processed_data.json                                │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: LABELING                                            │
│  Select labeling type → Apply appropriate labeler           │
│  - Bug severity (critical/high/medium/low)                 │
│  - Code complexity (simple/moderate/complex)               │
│  - Feature type (bug/feature/refactoring/etc)             │
│  - Multi-label classification                             │
│  Output: labeled_data.json (with labels)                   │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: STORAGE & ACCESS                                   │
│  ┌─────────────────┐   ┌──────────────────┐                 │
│  │  Neo4j Storage  │   │  File Export     │                 │
│  │  (Graph queries)│   │  (CSV/JSON/etc)  │                 │
│  └─────────────────┘   └──────────────────┘                 │
│  Create nodes & relationships for graph queries             │
│  Export in multiple formats for distribution               │
└──────────────────────────────────────────────────────────────┘
```

## Configuration Management

```
config/config.py
├── NEO4J_CONFIG (URI, credentials, database)
├── DATASET_CONFIGS (7 datasets, their properties)
├── PROCESSING_CONFIG (chunk size, batch size, timeouts)
├── NEO4J_NODES (node types & properties)
├── NEO4J_RELATIONSHIPS (relationship types)
├── EXPORT_FORMATS (CSV, JSON, Parquet, etc.)
├── LOGGING_CONFIG (level, format, file)
└── API_CONFIG (host, port, workers)
```

## Database Schema (Neo4j)

### Nodes

```
Project
├── id: String
├── name: String
├── url: String
├── language: String
├── stars: Integer
├── forks: Integer
└── description: String

Bug
├── id: String
├── title: String
├── description: String
├── severity: String (critical/high/medium/low)
├── status: String (open/closed/fixed)
└── reported_date: String

Commit
├── hash: String
├── message: String
├── author: String
├── timestamp: String
├── files_changed: Integer
├── additions: Integer
└── deletions: Integer

File
├── path: String
├── language: String
├── size: Integer
├── complexity: Integer
└── lines_of_code: Integer

Function
├── name: String
├── signature: String
├── lines: Integer
├── cyclomatic_complexity: Integer
└── parameters: Integer

Issue
├── id: String
├── title: String
├── body: String
├── state: String
├── created_at: String
└── priority: String

CodeSnippet
├── hash: String
├── content: String
├── language: String
├── tokens: Integer
└── complexity: Integer

Metric
├── name: String
├── value: Float
├── category: String
├── timestamp: String
└── unit: String
```

### Relationships

```
Project -[HAS_BUG]-> Bug
Project -[CHANGED_IN]-> Commit
Project -[CONTAINS_FILE]-> File
Project -[HAS_METRIC]-> Metric

File -[CONTAINS_FUNCTION]-> Function
Function -[CALLS]-> Function

Bug -[FIXED_BY]-> Commit
Bug -[RELATED_TO]-> Bug
Bug -[LOCATED_IN]-> File

Issue -[REPORTED_IN]-> Project
CodeSnippet -[HAS_METRIC]-> Metric
Commit -[CREATED_FROM]-> CodeSnippet
```

## Extensibility Points

### Adding New Dataset Type

1. Create extractor in `extractors/new_extractor.py`
2. Extend `BaseExtractor` or `RepositoryExtractor`/`FileExtractor`
3. Implement `extract()` and `validate()` methods
4. Register in `extractors/factory.py`

```python
class MyDatasetExtractor(RepositoryExtractor):
    def extract(self) -> List[Dict]:
        # Implementation
        pass
    
    def validate(self) -> bool:
        # Validation logic
        pass
```

### Adding New Processor

1. Create in `processors/new_processor.py`
2. Extend `BaseProcessor`
3. Implement `process()` method
4. Add to pipeline

```python
class MyProcessor(BaseProcessor):
    def process(self, records: List[Dict]) -> List[Dict]:
        # Processing logic
        pass
```

### Adding New Labeler

1. Create in `labelers/new_labeler.py`
2. Extend `BaseLabeler`
3. Implement `label()` method

```python
class MyLabeler(BaseLabeler):
    def label(self, records: List[Dict]) -> List[Dict]:
        # Labeling logic
        pass
```

## Performance Considerations

- **Batch Processing**: Large datasets processed in configurable batch sizes
- **Parallel Processing**: Multi-worker support for extraction/processing
- **Caching**: Results cached to avoid re-processing
- **Indexing**: Neo4j automatically indexes node properties
- **Pagination**: API endpoints support pagination for large result sets

## Security

- Input validation on all extraction sources
- SQL injection prevention (using Neo4j prepared statements)
- API authentication ready (can add JWT)
- Sensitive data handling (password encryption in config)
- Audit logging for all operations

## Deployment

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "api.server"]
```

### Docker Compose
```yaml
version: '3'
services:
  neo4j:
    image: neo4j:latest
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7687:7687"
  api:
    build: .
    environment:
      NEO4J_URI: bolt://neo4j:7687
    ports:
      - "8000:8000"
```

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
