"""
Base Processor Class - Abstract base for all data processors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for data processors"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize processor
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.processed_data = []
        self.processing_stats = {}
    
    @abstractmethod
    def process(self, records: List[Dict]) -> List[Dict]:
        """
        Process records
        
        Args:
            records: List of records to process
        
        Returns:
            List of processed records
        """
        pass
    
    def get_processed_data(self) -> List[Dict]:
        """Get processed data"""
        return self.processed_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats
    
    def set_stat(self, key: str, value: Any):
        """Set processing statistic"""
        self.processing_stats[key] = value
    
    def add_error(self, record_id: str, error: str):
        """Add processing error"""
        if "errors" not in self.processing_stats:
            self.processing_stats["errors"] = []
        self.processing_stats["errors"].append({"id": record_id, "error": error})

class CodeNormalizer(BaseProcessor):
    """Normalizes code snippets for comparison"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize code normalizer"""
        super().__init__(config)
    
    def process(self, records: List[Dict]) -> List[Dict]:
        """Normalize code in records"""
        logger.info(f"Normalizing {len(records)} code records")
        
        normalized = []
        errors = 0
        
        for record in records:
            try:
                normalized_record = record.copy()
                
                # Normalize code fields
                for field in ["code", "buggy_code", "fixed_code", "content"]:
                    if field in normalized_record and isinstance(normalized_record[field], str):
                        normalized_record[field] = self._normalize_code(
                            normalized_record[field],
                            record.get("language", "unknown")
                        )
                
                normalized.append(normalized_record)
            
            except Exception as e:
                errors += 1
                self.add_error(record.get("id", "unknown"), str(e))
                logger.warning(f"Error normalizing record: {e}")
        
        self.processed_data = normalized
        self.set_stat("total_records", len(records))
        self.set_stat("normalized_records", len(normalized))
        self.set_stat("errors", errors)
        
        logger.info(f"Normalized {len(normalized)}/{len(records)} records")
        return normalized
    
    @staticmethod
    def _normalize_code(code: str, language: str) -> str:
        """Normalize code for comparison"""
        
        # Remove comments based on language
        if language == "python":
            code = CodeNormalizer._remove_python_comments(code)
        elif language in ["java", "cpp", "c", "javascript", "typescript"]:
            code = CodeNormalizer._remove_c_style_comments(code)
        
        # Remove extra whitespace
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    @staticmethod
    def _remove_python_comments(code: str) -> str:
        """Remove Python comments"""
        import re
        # Remove single-line comments
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
        return code
    
    @staticmethod
    def _remove_c_style_comments(code: str) -> str:
        """Remove C-style comments"""
        import re
        # Remove single-line comments //
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments /* */
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

class TextCleaner(BaseProcessor):
    """Cleans and normalizes text fields"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize text cleaner"""
        super().__init__(config)
        self.max_length = config.get("max_length", 1000) if config else 1000
    
    def process(self, records: List[Dict]) -> List[Dict]:
        """Clean text in records"""
        logger.info(f"Cleaning {len(records)} text records")
        
        cleaned = []
        
        for record in records:
            cleaned_record = record.copy()
            
            # Clean text fields
            for field in ["title", "description", "body", "message", "documentation"]:
                if field in cleaned_record and isinstance(cleaned_record[field], str):
                    cleaned_record[field] = self._clean_text(cleaned_record[field])
            
            cleaned.append(cleaned_record)
        
        self.processed_data = cleaned
        self.set_stat("total_records", len(records))
        self.set_stat("cleaned_records", len(cleaned))
        
        logger.info(f"Cleaned {len(cleaned)} records")
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean single text field"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."
        
        return text

class DataValidator(BaseProcessor):
    """Validates data records"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize data validator"""
        super().__init__(config)
        self.required_fields = config.get("required_fields", []) if config else []
    
    def process(self, records: List[Dict]) -> List[Dict]:
        """Validate records"""
        logger.info(f"Validating {len(records)} records")
        
        validated = []
        invalid_count = 0
        
        for record in records:
            if self._validate_record(record):
                validated.append(record)
            else:
                invalid_count += 1
                self.add_error(record.get("id", "unknown"), "Invalid record")
        
        self.processed_data = validated
        self.set_stat("total_records", len(records))
        self.set_stat("valid_records", len(validated))
        self.set_stat("invalid_records", invalid_count)
        
        logger.info(f"Valid {len(validated)}/{len(records)} records")
        return validated
    
    def _validate_record(self, record: Dict) -> bool:
        """Validate single record"""
        
        # Check required fields
        for field in self.required_fields:
            if field not in record or record[field] is None:
                return False
        
        # Check for empty strings
        for key, value in record.items():
            if isinstance(value, str) and not value.strip():
                return False
        
        return True

class DuplicateRemover(BaseProcessor):
    """Removes duplicate records"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize duplicate remover"""
        super().__init__(config)
        self.key_field = config.get("key_field", "id") if config else "id"
    
    def process(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records"""
        logger.info(f"Removing duplicates from {len(records)} records")
        
        seen = set()
        unique = []
        duplicates = 0
        
        for record in records:
            key = record.get(self.key_field)
            if key and key not in seen:
                seen.add(key)
                unique.append(record)
            else:
                duplicates += 1
        
        self.processed_data = unique
        self.set_stat("total_records", len(records))
        self.set_stat("unique_records", len(unique))
        self.set_stat("duplicate_records", duplicates)
        
        logger.info(f"Found {duplicates} duplicates, kept {len(unique)} unique records")
        return unique

class ProcessingPipeline:
    """Chains multiple processors together"""
    
    def __init__(self):
        """Initialize processing pipeline"""
        self.processors = []
        self.stats = {}
    
    def add_processor(self, processor: BaseProcessor) -> 'ProcessingPipeline':
        """Add processor to pipeline"""
        self.processors.append(processor)
        return self  # For method chaining
    
    def process(self, records: List[Dict]) -> List[Dict]:
        """Execute all processors in sequence"""
        logger.info(f"Starting processing pipeline with {len(self.processors)} processors")
        
        data = records
        
        for i, processor in enumerate(self.processors):
            logger.info(f"Running processor {i + 1}/{len(self.processors)}: {processor.__class__.__name__}")
            data = processor.process(data)
            self.stats[processor.__class__.__name__] = processor.get_stats()
        
        logger.info(f"Pipeline completed with {len(data)} records")
        return data
    
    def get_stats(self) -> Dict:
        """Get statistics from all processors"""
        return self.stats
