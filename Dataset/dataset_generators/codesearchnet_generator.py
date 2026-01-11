import os
import json
import re
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False
    print("WARNING: javalang not installed. Install with: pip install javalang")

try:
    from metrics_helper import MetricsHelper
    METRICS_HELPER_AVAILABLE = True
except ImportError:
    METRICS_HELPER_AVAILABLE = False
    print("WARNING: MetricsHelper not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeSearchNetGenerator:
    
    def __init__(self, repo_path: str, output_dir: str = None, file_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.file_limit = file_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MetricsHelper for 64 real metrics
        if METRICS_HELPER_AVAILABLE:
            try:
                self.metrics_helper = MetricsHelper(str(self.repo_path))
                logger.info("MetricsHelper initialized - 64 real metrics available")
            except Exception as e:
                logger.warning(f"MetricsHelper init failed: {e}")
                self.metrics_helper = None
        else:
            self.metrics_helper = None
        
        logger.info(f"Initialized CodeSearchNet generator for {self.repo_path}")
    
    def _get_java_files(self) -> List[Path]:
        """Get all Java files in repository"""
        java_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['target', 'build', 'node_modules', 'generated_datasets', '__pycache__']]
            
            for f in files:
                if f.endswith('.java'):
                    java_files.append(Path(root) / f)
                    
                    if self.file_limit and len(java_files) >= self.file_limit:
                        return java_files
        
        return java_files
    
    def generate(self) -> Dict:
        logger.info("Generating CodeSearchNet dataset from Java files...")
        
        dataset = []
        dataset_dir = self.output_dir / f"codesearchnet_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)
        
        project_name = self.repo_path.name
        
        # Get all Java files
        java_files = self._get_java_files()
        logger.info(f"Found {len(java_files)} Java files")
        
        if not java_files:
            logger.warning("No Java files found")
            return {"error": "No Java files found"}
        
        try:
            for file_path in java_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if not code.strip():
                        continue
                    
                    # Get relative path
                    try:
                        rel_path = file_path.relative_to(self.repo_path)
                    except:
                        rel_path = file_path.name
                    
                    # Extract Javadoc comments
                    javadoc_pattern = r'/\*\*(.*?)\*/'
                    javadocs = re.findall(javadoc_pattern, code, re.DOTALL)
                    
                    # Extract single-line comments
                    single_comments = re.findall(r'//\s*(.+)', code)
                    
                    # Extract methods with their docs
                    method_pattern = r'(/\*\*.*?\*/\s*)?(public|private|protected|static)[\s\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
                    methods = re.findall(method_pattern, code, re.DOTALL)
                    
                    # Tokenize code
                    code_tokens = re.findall(r'\w+|[^\w\s]', code)
                    
                    # Clean Javadoc
                    docstring = ""
                    if javadocs:
                        docstring = javadocs[0].replace('*', '').strip()
                    elif single_comments:
                        docstring = ' '.join(single_comments[:3])  # First 3 comments
                    
                    # Extract package
                    package_pattern = r'package\s+([\w\.]+);'
                    package_match = re.search(package_pattern, code)
                    package = package_match.group(1) if package_match else ""
                    
                    # Extract imports
                    import_pattern = r'import\s+([\w\.]+);'
                    imports = re.findall(import_pattern, code)
                    
                    record = {
                        "project": project_name,
                        "file_path": str(rel_path),
                        "language": "java",
                        "dataset_type": "codesearchnet",
                        "code": code,  # FULL CODE
                        "docstring": docstring,
                        "code_tokens": code_tokens[:500],  # First 500 tokens
                        "docstring_tokens": docstring.split()[:100],  # First 100 words
                        "package": package,
                        "imports": imports,
                        "num_methods": len(methods),
                        "has_javadoc": len(javadocs) > 0,
                        "has_comments": len(single_comments) > 0,
                        "method_names": [m[2] for m in methods if m[2]][:10]  # First 10 method names
                    }
                    
                    dataset.append(record)
                    
                    if len(dataset) % 100 == 0:
                        logger.info(f"Processed {len(dataset)} files...")
                
                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    continue
            
            logger.info(f"Extracted data from {len(dataset)} files")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
        
        # Save to JSON
        output_file = dataset_dir / "codesearchnet_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'CodeSearchNet_Real',
                'description': 'Real code with documentation for search tasks',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_files': len(dataset),
                'data': dataset,
                'extraction_method': 'file_based_code_doc_analysis'
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"SUCCESS: REAL CodeSearchNet dataset generated: {len(dataset)} files -> {dataset_dir}")
        
        return {
            "status": "success",
            "total_files": len(dataset),
            "output_dir": str(dataset_dir),
            "output_file": str(output_file)
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python codesearchnet_generator.py <repo_path> [file_limit]")
        print("Example: python codesearchnet_generator.py d:/GitIntel/repo 500")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    file_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    generator = CodeSearchNetGenerator(repo_path, file_limit=file_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_files']} file entries")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
