"""
Code Search and Knowledge Base Dataset Extractors
For CodeXGLUE, CodeSearchNet, Sourcerer Dataset
"""

from typing import Dict, List, Optional
import logging
from pathlib import Path
import ast
import re
from extractors.base_extractor import RepositoryExtractor, FileExtractor
from utils.helpers import generate_hash

logger = logging.getLogger(__name__)

class CodeXGLUEExtractor(RepositoryExtractor):
    """Extractor for CodeXGLUE dataset"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize CodeXGLUE extractor"""
        super().__init__(repo_path, config)
        self.dataset_type = "codexglue"
    
    def extract(self) -> List[Dict]:
        """
        Extract CodeXGLUE format data
        Code-to-code and code-to-text mappings
        """
        logger.info(f"Extracting CodeXGLUE data from {self.repo_path}")
        
        extracted = []
        
        # Look for data files
        data_files = list(self.repo_path.glob("**/*.jsonl")) + list(self.repo_path.glob("**/*.json"))
        
        for data_file in data_files:
            extracted.extend(self._extract_from_file(data_file))
        
        # Extract from source files
        source_files = list(self.repo_path.glob("**/*.java")) + list(self.repo_path.glob("**/*.py"))
        for source_file in source_files:
            extracted.extend(self._extract_from_source(source_file))
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "codexglue_structure")
        
        logger.info(f"Extracted {len(extracted)} CodeXGLUE records")
        return extracted
    
    def _extract_from_file(self, file_path: Path) -> List[Dict]:
        """Extract from JSONL or JSON file"""
        records = []
        
        try:
            if file_path.suffix == ".jsonl":
                import json
                with open(file_path) as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            record["type"] = "codexglue_pair"
                            records.append(record)
            
            elif file_path.suffix == ".json":
                import json
                with open(file_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            item["type"] = "codexglue_pair"
                            records.append(item)
        
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
        
        return records
    
    def _extract_from_source(self, source_file: Path) -> List[Dict]:
        """Extract code snippets from source files"""
        records = []
        
        try:
            content = source_file.read_text()
            
            # Extract functions/methods
            if source_file.suffix == ".py":
                functions = self._extract_python_functions(content)
                for func in functions:
                    records.append({
                        "type": "codexglue_code_snippet",
                        "language": "python",
                        "file": str(source_file),
                        "content": func,
                        "hash": generate_hash(func),
                    })
            
            elif source_file.suffix == ".java":
                functions = self._extract_java_methods(content)
                for func in functions:
                    records.append({
                        "type": "codexglue_code_snippet",
                        "language": "java",
                        "file": str(source_file),
                        "content": func,
                        "hash": generate_hash(func),
                    })
        
        except Exception as e:
            logger.warning(f"Error extracting from {source_file}: {e}")
        
        return records
    
    @staticmethod
    def _extract_python_functions(code: str) -> List[str]:
        """Extract Python functions"""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get source lines for this function
                    functions.append(ast.unparse(node))
        except:
            pass
        return functions
    
    @staticmethod
    def _extract_java_methods(code: str) -> List[str]:
        """Extract Java methods using regex"""
        # Simple regex to extract method signatures and body
        pattern = r'(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.findall(pattern, code, re.DOTALL)
        return matches

class CodeSearchNetExtractor(RepositoryExtractor):
    """Extractor for CodeSearchNet dataset"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize CodeSearchNet extractor"""
        super().__init__(repo_path, config)
        self.dataset_type = "codesearchnet"
    
    def extract(self) -> List[Dict]:
        """
        Extract CodeSearchNet format data
        Code-to-documentation mappings
        """
        logger.info(f"Extracting CodeSearchNet data from {self.repo_path}")
        
        extracted = []
        
        # Look for training/test data
        for split in ["train", "test", "valid"]:
            split_dir = self.repo_path / split
            if split_dir.exists():
                extracted.extend(self._extract_from_split(split_dir, split))
        
        # Extract from source files with docstrings
        source_files = list(self.repo_path.glob("**/*.py"))
        for source_file in source_files:
            extracted.extend(self._extract_documented_functions(source_file))
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "codesearchnet_structure")
        
        logger.info(f"Extracted {len(extracted)} CodeSearchNet records")
        return extracted
    
    def _extract_from_split(self, split_dir: Path, split_name: str) -> List[Dict]:
        """Extract from split directory"""
        records = []
        
        for json_file in split_dir.glob("*.jsonl"):
            import json
            with open(json_file) as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        record["split"] = split_name
                        record["type"] = "codesearchnet_pair"
                        records.append(record)
                    except:
                        pass
        
        return records
    
    def _extract_documented_functions(self, source_file: Path) -> List[Dict]:
        """Extract functions with documentation"""
        records = []
        
        try:
            code = source_file.read_text()
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        records.append({
                            "type": "codesearchnet_documented_function",
                            "name": node.name,
                            "language": "python",
                            "file": str(source_file),
                            "documentation": docstring,
                            "code_hash": generate_hash(ast.unparse(node)),
                        })
        except Exception as e:
            logger.warning(f"Error extracting from {source_file}: {e}")
        
        return records

class SourcererExtractor(RepositoryExtractor):
    """Extractor for Sourcerer Dataset"""
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """Initialize Sourcerer extractor"""
        super().__init__(repo_path, config)
        self.dataset_type = "sourcerer"
    
    def extract(self) -> List[Dict]:
        """
        Extract Sourcerer format data
        Large-scale source code mining dataset
        """
        logger.info(f"Extracting Sourcerer data from {self.repo_path}")
        
        extracted = []
        
        # Extract project structure
        project_info = self._extract_project_info()
        if project_info:
            extracted.append(project_info)
        
        # Extract file structure
        extracted.extend(self._extract_file_structure())
        
        # Extract dependencies
        extracted.extend(self._extract_dependencies())
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "sourcerer_structure")
        
        logger.info(f"Extracted {len(extracted)} Sourcerer records")
        return extracted
    
    def _extract_project_info(self) -> Optional[Dict]:
        """Extract project information"""
        record = {
            "type": "sourcerer_project",
            "path": str(self.repo_path),
            "name": self.repo_path.name,
        }
        
        # Look for pom.xml or build.gradle
        pom_file = self.repo_path / "pom.xml"
        gradle_file = self.repo_path / "build.gradle"
        
        if pom_file.exists():
            record["build_system"] = "maven"
            import xml.etree.ElementTree as ET
            try:
                tree = ET.parse(pom_file)
                root = tree.getroot()
                record["build_config"] = ET.tostring(root, encoding='unicode')[:500]
            except:
                pass
        
        elif gradle_file.exists():
            record["build_system"] = "gradle"
            record["build_config"] = gradle_file.read_text()[:500]
        
        return record
    
    def _extract_file_structure(self) -> List[Dict]:
        """Extract file structure"""
        records = []
        
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and self._is_source_file(file_path):
                record = {
                    "type": "sourcerer_file",
                    "path": str(file_path.relative_to(self.repo_path)),
                    "language": self._get_language(file_path),
                    "size": file_path.stat().st_size,
                }
                records.append(record)
        
        return records
    
    def _extract_dependencies(self) -> List[Dict]:
        """Extract project dependencies"""
        records = []
        
        # Maven dependencies
        pom_file = self.repo_path / "pom.xml"
        if pom_file.exists():
            import xml.etree.ElementTree as ET
            try:
                tree = ET.parse(pom_file)
                for dep in tree.findall(".//{http://maven.apache.org/POM/4.0.0}dependency"):
                    group = dep.find("{http://maven.apache.org/POM/4.0.0}groupId")
                    artifact = dep.find("{http://maven.apache.org/POM/4.0.0}artifactId")
                    version = dep.find("{http://maven.apache.org/POM/4.0.0}version")
                    
                    if group is not None and artifact is not None:
                        records.append({
                            "type": "sourcerer_dependency",
                            "group": group.text,
                            "artifact": artifact.text,
                            "version": version.text if version is not None else "unknown",
                        })
            except:
                pass
        
        return records
    
    @staticmethod
    def _is_source_file(file_path: Path) -> bool:
        """Check if file is a source file"""
        source_extensions = {'.java', '.py', '.js', '.ts', '.go', '.rb', '.php', '.cpp', '.c', '.h'}
        return file_path.suffix in source_extensions
    
    @staticmethod
    def _get_language(file_path: Path) -> str:
        """Get programming language from file extension"""
        ext_to_lang = {
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
        }
        return ext_to_lang.get(file_path.suffix, 'unknown')
