"""
Defects4J Dataset Extractor
Extracts buggy/fixed code pairs from Java projects
"""

from typing import Dict, List, Optional
import logging
from pathlib import Path
from extractors.base_extractor import RepositoryExtractor
from utils.helpers import generate_hash

logger = logging.getLogger(__name__)

class Defects4JExtractor(RepositoryExtractor):
    """Extractor for Defects4J dataset"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize Defects4J extractor"""
        super().__init__(repo_path, config)
        self.dataset_type = "defects4j"
    
    def extract(self) -> List[Dict]:
        """
        Extract Defects4J format data
        
        Expected structure:
        - bugs.csv or bugs.json with bug information
        - per-bug directories with buggy/fixed files
        """
        logger.info(f"Extracting Defects4J data from {self.repo_path}")
        
        extracted = []
        
        # Look for bugs data file
        bugs_file = self.repo_path / "bugs.json"
        if not bugs_file.exists():
            bugs_file = self.repo_path / "bugs.csv"
        
        if bugs_file.exists():
            extracted.extend(self._extract_from_file(bugs_file))
        
        # Look for bug directories
        bug_dirs = self._find_bug_directories()
        for bug_dir in bug_dirs:
            extracted.extend(self._extract_bug_pair(bug_dir))
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "defects4j_structure")
        
        logger.info(f"Extracted {len(extracted)} Defects4J records")
        return extracted
    
    def _find_bug_directories(self) -> List[Path]:
        """Find bug directories"""
        bug_dirs = []
        for item in self.repo_path.iterdir():
            if item.is_dir() and item.name.startswith("bug_"):
                bug_dirs.append(item)
        return bug_dirs
    
    def _extract_bug_pair(self, bug_dir: Path) -> List[Dict]:
        """Extract buggy/fixed code pair from directory"""
        records = []
        
        bug_id = bug_dir.name
        buggy_file = bug_dir / "buggy.java"
        fixed_file = bug_dir / "fixed.java"
        
        if buggy_file.exists() and fixed_file.exists():
            buggy_code = buggy_file.read_text()
            fixed_code = fixed_file.read_text()
            
            record = {
                "bug_id": bug_id,
                "buggy_code": buggy_code,
                "fixed_code": fixed_code,
                "buggy_hash": generate_hash(buggy_code),
                "fixed_hash": generate_hash(fixed_code),
                "language": "java",
                "type": "defects4j_bug_pair",
            }
            
            # Add metadata if available
            metadata_file = bug_dir / "metadata.json"
            if metadata_file.exists():
                import json
                metadata = json.load(open(metadata_file))
                record.update(metadata)
            
            records.append(record)
        
        return records
    
    def _extract_from_file(self, file_path: Path) -> List[Dict]:
        """Extract data from bugs.json or bugs.csv"""
        records = []
        
        if file_path.suffix == ".json":
            import json
            data = json.load(open(file_path))
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "bugs" in data:
                records = data["bugs"]
        
        elif file_path.suffix == ".csv":
            import csv
            with open(file_path) as f:
                reader = csv.DictReader(f)
                records = list(reader)
        
        return records

class ManySStuBs4JExtractor(RepositoryExtractor):
    """Extractor for ManySStuBs4J dataset"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize ManySStuBs4J extractor"""
        super().__init__(repo_path, config)
        self.dataset_type = "manystubs4j"
    
    def extract(self) -> List[Dict]:
        """
        Extract ManySStuBs4J format data
        Uses git history to find bug-fix commits
        """
        logger.info(f"Extracting ManySStuBs4J data from {self.repo_path}")
        
        extracted = []
        
        # Look for issues/bugs directory
        bugs_dir = self.repo_path / "issues"
        if bugs_dir.exists():
            for issue_dir in bugs_dir.iterdir():
                if issue_dir.is_dir():
                    extracted.extend(self._extract_issue(issue_dir))
        
        # Alternative: look for bug files
        bug_files = list(self.repo_path.glob("**/bug_*.json"))
        for bug_file in bug_files:
            extracted.extend(self._extract_from_json(bug_file))
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "manystubs4j_structure")
        
        logger.info(f"Extracted {len(extracted)} ManySStuBs4J records")
        return extracted
    
    def _extract_issue(self, issue_dir: Path) -> List[Dict]:
        """Extract issue/bug information"""
        records = []
        issue_id = issue_dir.name
        
        # Look for issue metadata
        metadata_file = issue_dir / "metadata.json"
        if metadata_file.exists():
            import json
            metadata = json.load(open(metadata_file))
            metadata["issue_id"] = issue_id
            metadata["type"] = "manystubs4j_issue"
            records.append(metadata)
        
        # Look for patch files
        patch_files = list(issue_dir.glob("*.patch"))
        for patch_file in patch_files:
            record = {
                "issue_id": issue_id,
                "patch_file": str(patch_file),
                "patch_content": patch_file.read_text(),
                "type": "manystubs4j_patch",
            }
            records.append(record)
        
        return records
    
    def _extract_from_json(self, file_path: Path) -> List[Dict]:
        """Extract from JSON file"""
        import json
        try:
            data = json.load(open(file_path))
            data["type"] = "manystubs4j_bug"
            return [data]
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []
