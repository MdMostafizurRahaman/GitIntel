"""
Base Extractor Class - Abstract base for all dataset extractors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import tempfile
import shutil
import urllib.parse
import subprocess

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Abstract base class for dataset extractors"""
    
    def __init__(self, source: str, config: Optional[Dict] = None):
        """
        Initialize extractor
        
        Args:
            source: Source path/URL/identifier
            config: Optional configuration dictionary
        """
        self.source = source
        self.config = config or {}
        self.extracted_data = []
        self.metadata = {}
        self.temp_dir = None
    
    @abstractmethod
    def extract(self) -> List[Dict]:
        """
        Extract data from source
        
        Returns:
            List of extracted records
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate source and configuration
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def get_extracted_data(self) -> List[Dict]:
        """Get extracted data"""
        return self.extracted_data
    
    def get_metadata(self) -> Dict:
        """Get extraction metadata"""
        return self.metadata
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata"""
        self.metadata[key] = value
    
    def get_record_count(self) -> int:
        """Get number of extracted records"""
        return len(self.extracted_data)
    
    def filter_records(self, predicate) -> List[Dict]:
        """Filter extracted records"""
        return [r for r in self.extracted_data if predicate(r)]
    
    def get_fields(self) -> List[str]:
        """Get all fields in extracted data"""
        if not self.extracted_data:
            return []
        return list(self.extracted_data[0].keys())
    
    def is_url(self, source: str) -> bool:
        """Check if source is a URL"""
        try:
            result = urllib.parse.urlparse(source)
            return result.scheme in ('http', 'https', 'git', 'ssh')
        except:
            return False
    
    def download_url(self, url: str) -> str:
        """Download or clone URL to temporary directory"""
        self.temp_dir = tempfile.mkdtemp(prefix="dataset_extract_")
        
        try:
            if url.endswith('.git') or 'github.com' in url or 'gitlab.com' in url:
                # Git repository
                logger.info(f"Cloning repository: {url}")
                subprocess.run(['git', 'clone', '--depth', '1', url, self.temp_dir], 
                             check=True, capture_output=True)
                return self.temp_dir
            else:
                # Regular URL - download file
                import requests
                logger.info(f"Downloading file: {url}")
                response = requests.get(url)
                response.raise_for_status()
                
                # Determine filename
                filename = url.split('/')[-1]
                if not filename:
                    filename = 'downloaded_file'
                
                file_path = Path(self.temp_dir) / filename
                file_path.write_bytes(response.content)
                return str(file_path)
                
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Error cleaning up {self.temp_dir}: {e}")

class RepositoryExtractor(BaseExtractor):
    """Base extractor for Git repositories"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize repository extractor"""
        super().__init__(repo_path, config)
        
        if self.is_url(self.source):
            self.repo_path = Path(self.download_url(self.source))
        else:
            self.repo_path = Path(repo_path)
        
        self.validate()
    
    def validate(self) -> bool:
        """Validate repository exists"""
        if not self.repo_path.exists():
            logger.error(f"Repository not found: {self.repo_path}")
            return False
        if not (self.repo_path / ".git").exists():
            logger.error(f"Not a git repository: {self.repo_path}")
            return False
        return True
    
    def get_commits(self) -> List[Dict]:
        """Get commits from repository"""
        # Placeholder - implement in subclass
        raise NotImplementedError
    
    def get_issues(self) -> List[Dict]:
        """Get issues from repository"""
        # Placeholder - implement in subclass
        raise NotImplementedError

class FileExtractor(BaseExtractor):
    """Base extractor for file-based data"""
    
    def __init__(self, file_path: str, config: Optional[Dict] = None):
        """Initialize file extractor"""
        super().__init__(file_path, config)
        
        if self.is_url(self.source):
            self.file_path = Path(self.download_url(self.source))
        else:
            self.file_path = Path(file_path)
        
        self.validate()
    
    def validate(self) -> bool:
        """Validate file exists"""
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            return False
        if not self.file_path.is_file():
            logger.error(f"Not a file: {self.file_path}")
            return False
        return True
    
    def read_file(self) -> str:
        """Read file content"""
        try:
            return self.file_path.read_text()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return ""
