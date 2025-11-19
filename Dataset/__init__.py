"""
Dataset Management System
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "Dataset Management Team"
__description__ = "Comprehensive dataset management for Defects4J, Bugs.jar, CodeXGLUE, and more"

from .config.config import (
    DATASET_CONFIGS,
    NEO4J_CONFIG,
    PROCESSING_CONFIG,
    EXPORT_FORMATS
)

from .extractors.factory import create_extractor, SUPPORTED_DATASETS

from .processors.base_processor import (
    ProcessingPipeline,
    CodeNormalizer,
    TextCleaner,
    DataValidator,
    DuplicateRemover
)

from .labelers.labeler import (
    BugSeverityLabeler,
    CodeComplexityLabeler,
    FeatureLabelClassifier,
    MultiLabelClassifier
)

from .neo4j.manager import get_neo4j_manager

__all__ = [
    'create_extractor',
    'SUPPORTED_DATASETS',
    'ProcessingPipeline',
    'CodeNormalizer',
    'TextCleaner',
    'DataValidator',
    'DuplicateRemover',
    'BugSeverityLabeler',
    'CodeComplexityLabeler',
    'FeatureLabelClassifier',
    'MultiLabelClassifier',
    'get_neo4j_manager',
    'DATASET_CONFIGS',
    'NEO4J_CONFIG',
    'PROCESSING_CONFIG',
    'EXPORT_FORMATS',
]
