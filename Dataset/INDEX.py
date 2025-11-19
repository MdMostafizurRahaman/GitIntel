"""
Dataset Management System - Quick Reference & Index
সম্পূর্ণ সিস্টেমের দ্রুত রেফারেন্স এবং ইন্ডেক্স
"""

# ==================== QUICK LINKS ====================

DOCUMENTATION = {
    "README": "docs/README.md",  # Main user guide
    "SETUP": "docs/SETUP.md",    # Installation & configuration
    "ARCHITECTURE": "docs/ARCHITECTURE.md",  # System design
    "EXAMPLES": "docs/EXAMPLES.md",  # Complete examples
    "SUMMARY": "SUMMARY.md",  # Quick overview
}

# ==================== SUPPORTED DATASETS ====================

DATASETS = {
    "defects4j": {
        "name": "Defects4J",
        "description": "Real bugs from Java projects (buggy/fixed pairs)",
        "extractor": "extractors.java_extractors.Defects4JExtractor",
        "source_type": "Git repository",
    },
    "bugs_jar": {
        "name": "Bugs.jar",
        "description": "Large-scale Java bug dataset with class info & test cases",
        "extractor": "extractors.metrics_extractors.BugsJarExtractor",
        "source_type": "JAR files or metadata JSON",
    },
    "manystubs4j": {
        "name": "ManySStuBs4J",
        "description": "Java dataset with multiple issues per project",
        "extractor": "extractors.java_extractors.ManySStuBs4JExtractor",
        "source_type": "Git repository with issues",
    },
    "codexglue": {
        "name": "CodeXGLUE",
        "description": "Code-to-code and code-to-text mappings",
        "extractor": "extractors.code_extractors.CodeXGLUEExtractor",
        "source_type": "Git repository with JSONL/JSON data",
    },
    "codesearchnet": {
        "name": "CodeSearchNet",
        "description": "Code-to-documentation mapping dataset",
        "extractor": "extractors.code_extractors.CodeSearchNetExtractor",
        "source_type": "Git repository with Python files",
    },
    "sourcerer": {
        "name": "Sourcerer Dataset",
        "description": "Large-scale source code mining with project structure",
        "extractor": "extractors.code_extractors.SourcererExtractor",
        "source_type": "Maven/Gradle project",
    },
    "promise": {
        "name": "PROMISE Repository",
        "description": "Software metrics and defect prediction data",
        "extractor": "extractors.metrics_extractors.PROMISEExtractor",
        "source_type": "CSV/ARFF/JSON files",
    },
}

# ==================== COMMAND REFERENCE ====================

CLI_COMMANDS = """
LIST DATASETS:
  python -m cli.main list-datasets
  python -m cli.main list-datasets --format json

EXTRACT DATA:
  python -m cli.main extract \\
    --dataset-type defects4j \\
    --source /path/to/repo \\
    --output data.json \\
    --format json

PROCESS DATA:
  python -m cli.main process \\
    --input raw_data.json \\
    --output processed_data.json \\
    --normalize-code \\
    --clean-text \\
    --validate \\
    --remove-duplicates

LABEL DATA:
  python -m cli.main label \\
    --input processed_data.json \\
    --output labeled_data.json \\
    --label-type bug_severity

  # Label types: bug_severity, code_complexity, feature_type, multi_label

IMPORT TO NEO4J:
  python -m cli.main import-to-neo4j \\
    --input labeled_data.json \\
    --dataset-name "My Dataset" \\
    --project-id "proj_001"

CHECK STATUS:
  python -m cli.main status

VIEW HELP:
  python -m cli.main --help
"""

# ==================== API ENDPOINTS ====================

API_ENDPOINTS = """
BASE URL: http://127.0.0.1:8000

GET /api/health
  - Health check & version info

GET /api/datasets
  - List all supported datasets

GET /api/datasets/{dataset_id}
  - Get specific dataset information

POST /api/extract
  - Extract data from source
  - Body: {dataset_type, source, output_format}

POST /api/process
  - Process extracted data
  - Body: {input_file, normalize_code, clean_text, remove_duplicates}

POST /api/label
  - Label dataset records
  - Body: {input_file, label_type}

POST /api/export
  - Export data in specified format
  - Body: {input_file, output_format, output_file}

GET /api/neo4j/stats
  - Get Neo4j database statistics

POST /api/neo4j/import
  - Import data to Neo4j
  - Body: {input_file, dataset_name}

GET /api/data/{file_id}
  - Download processed data file

GET /api/status
  - Get overall system status
"""

# ==================== PYTHON API REFERENCE ====================

PYTHON_API = """
from extractors.factory import create_extractor
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner
from labelers.labeler import BugSeverityLabeler
from neo4j.manager import get_neo4j_manager

# EXTRACTION
extractor = create_extractor("defects4j", "/path/to/repo")
records = extractor.extract()
metadata = extractor.get_metadata()

# PROCESSING
pipeline = ProcessingPipeline()
pipeline.add_processor(CodeNormalizer())
pipeline.add_processor(TextCleaner())
processed = pipeline.process(records)
stats = pipeline.get_stats()

# LABELING
labeler = BugSeverityLabeler()
labeled = labeler.label(processed)
distribution = labeler.get_stats()

# NEO4J
neo4j = get_neo4j_manager()
neo4j.create_node("Bug", {id: "bug_001", severity: "high"})
bugs = neo4j.find_nodes("Bug", {severity: "critical"})
results = neo4j.query("MATCH (b:Bug) RETURN b LIMIT 10")
stats = neo4j.get_statistics()
neo4j.close()
"""

# ==================== FOLDER STRUCTURE ====================

FOLDER_STRUCTURE = """
Dataset/
├── __init__.py                      # Package initialization
├── requirements.txt                 # Dependencies
├── SUMMARY.md                       # Quick overview
│
├── config/                          # Configuration
│   └── config.py                    # All settings
│
├── extractors/                      # Data Extraction (7 dataset types)
│   ├── base_extractor.py            # Base classes
│   ├── java_extractors.py           # Defects4J, ManySStuBs4J
│   ├── code_extractors.py           # CodeXGLUE, CodeSearchNet, Sourcerer
│   ├── metrics_extractors.py        # Bugs.jar, PROMISE
│   └── factory.py                   # Factory pattern
│
├── processors/                      # Data Processing Pipeline
│   └── base_processor.py            # CodeNormalizer, TextCleaner, DataValidator, etc.
│
├── labelers/                        # Data Labeling & Classification
│   └── labeler.py                   # BugSeverity, CodeComplexity, FeatureType, MultiLabel
│
├── neo4j/                           # Neo4j Integration
│   ├── manager.py                   # Database operations & connection
│   └── schema.py                    # Node/Relationship models, Cypher templates
│
├── cli/                             # Command-Line Interface
│   └── main.py                      # All CLI commands
│
├── gui/                             # Desktop GUI Application
│   └── app.py                       # PyQt5 interface
│
├── api/                             # REST API Server
│   └── server.py                    # FastAPI application & endpoints
│
├── utils/                           # Utility Functions
│   ├── logger.py                    # Logging setup
│   └── helpers.py                   # Helper functions
│
└── docs/                            # Documentation
    ├── README.md                    # User guide
    ├── SETUP.md                     # Installation guide
    ├── ARCHITECTURE.md              # System design
    └── EXAMPLES.md                  # Complete examples
"""

# ==================== COMMON WORKFLOWS ====================

WORKFLOWS = {
    "Simple Extraction": """
    python -m cli.main extract \\
      --dataset-type defects4j \\
      --source /path/to/repo \\
      --output data.json
    """,
    
    "Full Pipeline": """
    # 1. Extract
    python -m cli.main extract --dataset-type defects4j --source /path --output raw.json
    
    # 2. Process
    python -m cli.main process --input raw.json --output processed.json --normalize-code --clean-text
    
    # 3. Label
    python -m cli.main label --input processed.json --output labeled.json --label-type bug_severity
    
    # 4. Import
    python -m cli.main import-to-neo4j --input labeled.json --dataset-name "My Dataset" --project-id "proj_001"
    
    # 5. Check Status
    python -m cli.main status
    """,
    
    "Python Script": """
    from extractors.factory import create_extractor
    from processors.base_processor import ProcessingPipeline, CodeNormalizer
    from labelers.labeler import BugSeverityLabeler
    from neo4j.manager import get_neo4j_manager
    
    # Extract
    extractor = create_extractor("defects4j", "/path/to/repo")
    records = extractor.extract()
    
    # Process
    pipeline = ProcessingPipeline().add_processor(CodeNormalizer())
    processed = pipeline.process(records)
    
    # Label
    labeler = BugSeverityLabeler()
    labeled = labeler.label(processed)
    
    # Store
    neo4j = get_neo4j_manager()
    for record in labeled:
        neo4j.create_node("Bug", record)
    """,
    
    "GUI Application": """
    # Option 1: PyQt5 GUI (Advanced, requires installation)
    python -m gui.app
    
    # Option 2: tkinter GUI (Built-in, no installation needed)
    python -m gui.app_tkinter
    
    Then use the GUI to:
    1. Select dataset type
    2. Choose source directory
    3. Select processing options
    4. Apply labeling
    5. Export data
    
    Choose tkinter if you don't want to install PyQt5!
    """,
    
    "REST API": """
    # Start API server
    python -m api.server
    
    # Make requests from any client:
    curl -X POST http://127.0.0.1:8000/api/extract \\
      -H "Content-Type: application/json" \\
      -d '{
        "dataset_type": "defects4j",
        "source": "/path/to/repo",
        "output_format": "json"
      }'
    """,
}

# ==================== CONFIGURATION TEMPLATE ====================

CONFIG_TEMPLATE = """
# .env file template

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Logging
LOG_LEVEL=INFO

# API Server
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=4

# Processing
PROCESSING_CHUNK_SIZE=1000
PROCESSING_BATCH_SIZE=100
PROCESSING_MAX_WORKERS=4
"""

# ==================== SYSTEM REQUIREMENTS ====================

REQUIREMENTS = """
Software:
  - Python 3.8+
  - Neo4j 4.0+
  - Git

Python Packages:
  - neo4j>=5.0.0         (Database driver)
  - click>=8.0.0         (CLI framework)
  - PyQt5>=5.15.0        (GUI framework - optional)
  - tkinter              (Built-in GUI - no installation needed)
  - FastAPI>=0.68.0      (Web API)
  - uvicorn>=0.15.0      (ASGI server)
  - pandas>=1.3.0        (Data processing)
  - requests>=2.25.0     (HTTP client)

Hardware (Recommended):
  - 4GB+ RAM
  - 10GB+ Disk space
  - Dual-core processor

Installation:
  pip install -r requirements.txt
"""

# ==================== TROUBLESHOOTING ====================

TROUBLESHOOTING = """
1. Neo4j Connection Failed
   - Check if Neo4j is running: systemctl status neo4j
   - Verify URI: bolt://localhost:7687
   - Check credentials in .env

2. Module Not Found
   - Activate virtual environment
   - Run: pip install -r requirements.txt

3. Permission Denied
   - On Linux/Mac: chmod +x script_name.py
   - Check folder permissions

4. GUI Won't Start
   - For PyQt5: pip install PyQt5 --force-reinstall
   - For tkinter: python -m gui.app_tkinter (built-in, no install needed)
   - Check: python -c "import tkinter"

5. API Port Already in Use
   - Change API_PORT in .env
   - Or kill process: lsof -i :8000

See docs/SETUP.md for detailed troubleshooting
"""

# ==================== QUICK START ====================

def quick_start_guide():
    """দ্রুত শুরু করার গাইড"""
    return """
╔════════════════════════════════════════════════════════════╗
║     Dataset Management System - Quick Start Guide         ║
╚════════════════════════════════════════════════════════════╝

1. SETUP (সেটআপ)
   └─ docs/SETUP.md পড়ুন এবং ফলো করুন
   
2. CHOOSE INTERFACE (ইন্টারফেস বেছে নিন)
   ├─ CLI:  python -m cli.main --help
   ├─ GUI:  python -m gui.app (PyQt5) or python -m gui.app_tkinter (built-in)
   └─ API:  python -m api.server

3. EXTRACT DATA (ডেটা এক্সট্রাক্ট করুন)
   python -m cli.main extract \\
     --dataset-type defects4j \\
     --source /path/to/repo \\
     --output data.json

4. PROCESS DATA (ডেটা প্রসেস করুন)
   python -m cli.main process \\
     --input data.json \\
     --output processed.json \\
     --normalize-code

5. LABEL DATA (ডেটা লেবেল করুন)
   python -m cli.main label \\
     --input processed.json \\
     --output labeled.json \\
     --label-type bug_severity

6. IMPORT TO NEO4J (Neo4j-এ ইমপোর্ট করুন)
   python -m cli.main import-to-neo4j \\
     --input labeled.json \\
     --dataset-name "My Dataset" \\
     --project-id "proj_001"

7. CHECK STATUS (স্ট্যাটাস চেক করুন)
   python -m cli.main status

📚 See docs/EXAMPLES.md for more examples
📖 See docs/ARCHITECTURE.md for system design
"""

# ==================== SUPPORTED OPERATIONS ====================

OPERATIONS = {
    "Extraction": {
        "description": "Extract data from various sources",
        "module": "extractors",
        "types": ["Defects4J", "Bugs.jar", "ManySStuBs4J", "CodeXGLUE", "CodeSearchNet", "Sourcerer", "PROMISE"],
    },
    "Processing": {
        "description": "Clean, normalize, and validate data",
        "module": "processors",
        "types": ["CodeNormalizer", "TextCleaner", "DataValidator", "DuplicateRemover"],
    },
    "Labeling": {
        "description": "Classify and label records",
        "module": "labelers",
        "types": ["BugSeverityLabeler", "CodeComplexityLabeler", "FeatureLabelClassifier", "MultiLabelClassifier"],
    },
    "Storage": {
        "description": "Store data in Neo4j",
        "module": "neo4j",
        "operations": ["Create nodes", "Create relationships", "Query", "Export"],
    },
    "Export": {
        "description": "Export data in various formats",
        "formats": ["CSV", "JSON", "JSONL", "Parquet", "GraphML"],
    },
}

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    print(quick_start_guide())
    print("\n📚 Documentation Files:")
    for doc_name, doc_path in DOCUMENTATION.items():
        print(f"   - {doc_name}: {doc_path}")
    print("\n🚀 Ready to get started? Follow the Quick Start Guide above!")
