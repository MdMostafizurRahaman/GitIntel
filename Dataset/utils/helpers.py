"""
Helper utilities for dataset management
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def generate_hash(content: str, algorithm: str = "sha256") -> str:
    """Generate hash of content"""
    if algorithm == "sha256":
        return hashlib.sha256(content.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(content.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string for database storage"""
    text = text.strip()
    if max_length:
        text = text[:max_length]
    return text

def normalize_code(code: str) -> str:
    """Normalize code for comparison"""
    # Remove comments, extra whitespace
    lines = code.split('\n')
    normalized = []
    for line in lines:
        # Remove single-line comments
        if '#' in line:
            line = line[:line.index('#')]
        line = line.strip()
        if line:
            normalized.append(line)
    return '\n'.join(normalized)

def extract_metadata(data: Dict) -> Dict[str, Any]:
    """Extract and standardize metadata"""
    metadata = {
        "extracted_at": datetime.now().isoformat(),
        "version": "1.0",
    }
    
    # Common fields
    if "id" in data:
        metadata["id"] = data["id"]
    if "name" in data:
        metadata["name"] = data["name"]
    if "description" in data:
        metadata["description"] = data["description"][:500]  # Truncate
    if "url" in data:
        metadata["url"] = data["url"]
    
    return metadata

def batch_list(items: List, batch_size: int) -> List[List]:
    """Split list into batches"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches

def dict_to_json(data: Dict, indent: int = 2) -> str:
    """Convert dict to JSON string"""
    return json.dumps(data, indent=indent, default=str)

def json_to_dict(json_str: str) -> Dict:
    """Convert JSON string to dict"""
    return json.loads(json_str)

def validate_dataset_type(dataset_type: str, valid_types: List[str]) -> bool:
    """Validate dataset type"""
    return dataset_type.lower() in [t.lower() for t in valid_types]

def retry_operation(func, max_attempts: int = 3, delay: float = 1.0):
    """Retry operation with exponential backoff"""
    import time
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
            time.sleep(wait_time)

def estimate_processing_time(data_size: int, rate: float = 100) -> str:
    """Estimate processing time"""
    seconds = data_size / rate
    minutes = seconds / 60
    hours = minutes / 60
    
    if hours > 1:
        return f"{hours:.1f} hours"
    elif minutes > 1:
        return f"{minutes:.1f} minutes"
    else:
        return f"{seconds:.0f} seconds"
