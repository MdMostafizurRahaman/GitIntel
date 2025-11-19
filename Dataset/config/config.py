"""
Configuration module for Dataset Management System
"""

import os
from pathlib import Path
from typing import Dict

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"
EXPORT_DIR = BASE_DIR / "exports"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# Neo4j Configuration
NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "neo4j+s://a8427b75.databases.neo4j.io"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "31BGUwfd2E16WS1YIvFC2r_4bl7AZGw-KbxGLCWdHK8"),
    "database": os.getenv("NEO4J_DATABASE", "neo4j"),
}

# Database Configuration
DB_CONFIG = {
    "sqlite": str(DATA_DIR / "datasets.db"),
    "mongodb_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
}

# Dataset Configurations
DATASET_CONFIGS = {
    "defects4j": {
        "name": "Defects4J",
        "description": "Real bugs from Java projects",
        "type": "bug_dataset",
        "source_type": "github_repo",
        "features": ["buggy_code", "fixed_code", "bug_description", "commit_hash"]
    },
    "bugs_jar": {
        "name": "Bugs.jar",
        "description": "Large-scale Java bug dataset",
        "type": "bug_dataset",
        "source_type": "jar_files",
        "features": ["class_info", "bug_location", "test_cases", "fix_info"]
    },
    "manystubs4j": {
        "name": "ManySStuBs4J",
        "description": "Large-scale Java bug dataset with multiple issues per project",
        "type": "bug_dataset",
        "source_type": "github_repo",
        "features": ["issue_id", "commit_hash", "file_changes", "description"]
    },
    "codexglue": {
        "name": "CodeXGLUE",
        "description": "Code-to-code and code-to-text benchmark",
        "type": "code_dataset",
        "source_type": "github_repo",
        "features": ["source_code", "target_code", "description", "language"]
    },
    "codesearchnet": {
        "name": "CodeSearchNet",
        "description": "Code to natural language mapping dataset",
        "type": "code_search_dataset",
        "source_type": "github_repo",
        "features": ["code_snippet", "documentation", "query", "language"]
    },
    "sourcerer": {
        "name": "Sourcerer Dataset",
        "description": "Large-scale source code mining dataset",
        "type": "code_mining_dataset",
        "source_type": "github_repo",
        "features": ["project_info", "file_structure", "dependencies", "metrics"]
    },
    "promise": {
        "name": "PROMISE Repository",
        "description": "Software engineering datasets for empirical studies",
        "type": "metrics_dataset",
        "source_type": "csv_files",
        "features": ["metrics", "defect_labels", "project_info", "version_info"]
    }
}

# Processing Configuration
PROCESSING_CONFIG = {
    "chunk_size": 1000,
    "batch_size": 100,
    "max_workers": 4,
    "timeout": 300,  # seconds
    "retry_attempts": 3,
}

# Neo4j Node Types
NEO4J_NODES = {
    "Project": {"properties": ["name", "url", "language", "stars", "forks"]},
    "Commit": {"properties": ["hash", "message", "timestamp", "author"]},
    "Bug": {"properties": ["id", "title", "description", "severity", "status"]},
    "File": {"properties": ["path", "language", "size", "complexity"]},
    "Function": {"properties": ["name", "signature", "lines", "cyclomatic_complexity"]},
    "Issue": {"properties": ["id", "title", "body", "state", "created_at"]},
    "CodeSnippet": {"properties": ["hash", "content", "language", "tokens"]},
    "Metric": {"properties": ["name", "value", "category", "timestamp"]},
}

# Neo4j Relationships
NEO4J_RELATIONSHIPS = {
    "HAS_BUG": {"properties": ["found_at", "severity"]},
    "FIXED_BY": {"properties": ["fixed_at"]},
    "CONTAINS_FILE": {"properties": []},
    "CONTAINS_FUNCTION": {"properties": []},
    "CALLS": {"properties": ["line_number"]},
    "RELATED_TO": {"properties": ["similarity_score"]},
    "REPORTED_IN": {"properties": ["reported_at"]},
    "CHANGED_IN": {"properties": ["type"]},
}

# Export Formats
EXPORT_FORMATS = {
    "csv": {"extension": ".csv", "handler": "csv"},
    "json": {"extension": ".json", "handler": "json"},
    "jsonl": {"extension": ".jsonl", "handler": "jsonl"},
    "parquet": {"extension": ".parquet", "handler": "parquet"},
    "graphml": {"extension": ".graphml", "handler": "graphml"},
    "cypher": {"extension": ".cypher", "handler": "cypher"},
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": str(BASE_DIR / "logs" / "dataset.log"),
}

# API Configuration
API_CONFIG = {
    "host": os.getenv("API_HOST", "127.0.0.1"),
    "port": int(os.getenv("API_PORT", 8000)),
    "debug": os.getenv("API_DEBUG", False),
    "workers": int(os.getenv("API_WORKERS", 4)),
}

# GUI Configuration
GUI_CONFIG = {
    "theme": "dark",
    "window_size": (1200, 800),
    "default_dataset_type": "defects4j",
}

# Agentic Dataset Maker Configuration
AGENTIC_CONFIG = {
    "enable_interactive_mode": True,
    "enable_direct_api": True,
    "auto_clarify_ambiguous_requests": True,
    "default_output_format": "json",
    "default_processing_pipeline": ["duplicate_remover"],  # Applied by default
    "max_records_for_processing": 1000000,
    "enable_caching": True,
    "cache_dir": str(CACHE_DIR / "agentic"),
}
