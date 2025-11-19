"""
Factory for creating dataset extractors
Provides unified interface for all extractor types
"""

from typing import Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_extractor(dataset_type: str, source: str, config: Optional[Dict] = None):
    """
    Factory function to create appropriate extractor
    
    Args:
        dataset_type: Type of dataset (defects4j, bugs_jar, etc.)
        source: Source path/URL
        config: Optional configuration
    
    Returns:
        Configured extractor instance
    """
    
    dataset_type = dataset_type.lower()
    
    if dataset_type == "defects4j":
        from extractors.java_extractors import Defects4JExtractor
        return Defects4JExtractor(source, config)
    
    elif dataset_type == "bugs_jar":
        from extractors.metrics_extractors import BugsJarExtractor
        return BugsJarExtractor(source, config)
    
    elif dataset_type == "manystubs4j":
        from extractors.java_extractors import ManySStuBs4JExtractor
        return ManySStuBs4JExtractor(source, config)
    
    elif dataset_type == "codexglue":
        from extractors.code_extractors import CodeXGLUEExtractor
        return CodeXGLUEExtractor(source, config)
    
    elif dataset_type == "codesearchnet":
        from extractors.code_extractors import CodeSearchNetExtractor
        return CodeSearchNetExtractor(source, config)
    
    elif dataset_type == "sourcerer":
        from extractors.code_extractors import SourcererExtractor
        return SourcererExtractor(source, config)
    
    elif dataset_type == "promise":
        from extractors.metrics_extractors import PROMISEExtractor
        return PROMISEExtractor(source, config)
    
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")

SUPPORTED_DATASETS = {
    "defects4j": {
        "name": "Defects4J",
        "description": "Real bugs from Java projects",
        "type": "repository",
    },
    "bugs_jar": {
        "name": "Bugs.jar",
        "description": "Large-scale Java bug dataset",
        "type": "file",
    },
    "manystubs4j": {
        "name": "ManySStuBs4J",
        "description": "Java bug dataset with multiple issues",
        "type": "repository",
    },
    "codexglue": {
        "name": "CodeXGLUE",
        "description": "Code-to-code and code-to-text benchmark",
        "type": "repository",
    },
    "codesearchnet": {
        "name": "CodeSearchNet",
        "description": "Code to documentation mapping",
        "type": "repository",
    },
    "sourcerer": {
        "name": "Sourcerer Dataset",
        "description": "Large-scale source code mining",
        "type": "repository",
    },
    "promise": {
        "name": "PROMISE Repository",
        "description": "Software metrics and defect prediction",
        "type": "file",
    },
}

def get_supported_datasets() -> Dict:
    """Get list of supported datasets"""
    return SUPPORTED_DATASETS

def validate_source(dataset_type: str, source: str) -> bool:
    """
    Validate if source is appropriate for dataset type
    
    Args:
        dataset_type: Type of dataset
        source: Source path/URL
    
    Returns:
        True if valid, False otherwise
    """
    dataset_type = dataset_type.lower()
    
    if dataset_type not in SUPPORTED_DATASETS:
        return False
    
    # Check if it's a URL
    if source.startswith(('http://', 'https://', 'git://', 'ssh://')) or 'github.com' in source or 'gitlab.com' in source:
        return True
    
    # Local path validation
    source_path = Path(source)
    
    # Repository-based datasets
    if SUPPORTED_DATASETS[dataset_type]["type"] == "repository":
        # Special case for defects4j - can be any directory with bug data
        if dataset_type == "defects4j":
            return source_path.exists() and source_path.is_dir()
        return source_path.exists() and (source_path / ".git").exists()
    
    # File-based datasets
    elif SUPPORTED_DATASETS[dataset_type]["type"] == "file":
        return source_path.exists() and source_path.is_file()
    
    return False
