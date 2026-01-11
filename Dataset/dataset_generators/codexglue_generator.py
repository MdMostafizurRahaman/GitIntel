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


class CodeXGLUEGenerator:
    
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
        
        logger.info(f"Initialized CodeXGLUE generator for {self.repo_path}")
    
    def _get_java_files(self) -> List[Path]:
        """Get all Java files in repository"""
        java_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden, build, and generated directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['target', 'build', 'node_modules', 'generated_datasets', '__pycache__']]
            
            for f in files:
                if f.endswith('.java'):
                    java_files.append(Path(root) / f)
                    
                    if self.file_limit and len(java_files) >= self.file_limit:
                        return java_files
        
        return java_files
    
    def generate(self) -> Dict:
        """Generate REAL CodeXGLUE dataset from Java files"""
        logger.info("Generating REAL CodeXGLUE dataset from Java files...")
        
        dataset = []
        dataset_dir = self.output_dir / f"codexglue_dataset_{self.timestamp}"
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
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if not code.strip():
                        continue
                    
                    # Get relative path
                    try:
                        rel_path = file_path.relative_to(self.repo_path)
                    except:
                        rel_path = file_path.name
                    
                    # Use Javalang for ACCURATE parsing
                    methods = []
                    classes = []
                    complexity = 0
                    imports = []
                    
                    # Count LOC first
                    loc = len([l for l in code.split('\n') if l.strip()])
                    
                    if JAVALANG_AVAILABLE:
                        try:
                            tree = javalang.parse.parse(code)
                            
                            # Extract classes accurately
                            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                                classes.append(('class', node.name))
                            for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                                classes.append(('interface', node.name))
                            for path, node in tree.filter(javalang.tree.EnumDeclaration):
                                classes.append(('enum', node.name))
                            
                            # Extract methods accurately
                            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                                methods.append(('method', node.name))
                            for path, node in tree.filter(javalang.tree.ConstructorDeclaration):
                                methods.append(('constructor', node.name))
                            
                            # Calculate complexity (count control flow statements)
                            for _, node in tree.filter(javalang.tree.IfStatement):
                                complexity += 1
                            for _, node in tree.filter(javalang.tree.ForStatement):
                                complexity += 1
                            for _, node in tree.filter(javalang.tree.WhileStatement):
                                complexity += 1
                            for _, node in tree.filter(javalang.tree.SwitchStatement):
                                complexity += 1
                            for _, node in tree.filter(javalang.tree.TryStatement):
                                complexity += 1
                            
                            # Extract imports
                            if tree.imports:
                                imports = [imp.path for imp in tree.imports]
                        except Exception as e:
                            # Fallback to regex if parsing fails
                            method_pattern = r'(public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
                            methods = re.findall(method_pattern, code)
                            class_pattern = r'(public|private|protected)?\s*class\s+(\w+)'
                            classes = re.findall(class_pattern, code)
                            complexity = (code.count('if ') + code.count('for ') + 
                                        code.count('while ') + code.count('switch '))
                            import_pattern = r'import\s+([\w\.]+);'
                            imports = re.findall(import_pattern, code)
                    else:
                        # Fallback to regex
                        method_pattern = r'(public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
                        methods = re.findall(method_pattern, code)
                        class_pattern = r'(public|private|protected)?\s*class\s+(\w+)'
                        classes = re.findall(class_pattern, code)
                        complexity = (code.count('if ') + code.count('for ') + 
                                    code.count('while ') + code.count('switch '))
                        import_pattern = r'import\s+([\w\.]+);'
                        imports = re.findall(import_pattern, code)
                    
                    if not methods and not classes:
                        # If no methods/classes, include whole file
                        record = {
                            "project": project_name,
                            "file_path": str(rel_path),
                            "language": "java",
                            "dataset_type": "codexglue",
                            "signature": f"file {file_path.stem}",
                            "code": code,  # FULL CODE
                            "complexity": complexity,
                            "loc": loc,
                            "imports": imports,
                            "num_methods": 0,
                            "num_classes": 0
                        }
                        dataset.append(record)
                    else:
                        # Create entry with file-level info
                        record = {
                            "project": project_name,
                            "file_path": str(rel_path),
                            "language": "java",
                            "dataset_type": "codexglue",
                            "signature": f"{len(classes)} class(es), {len(methods)} method(s)",
                            "code": code,  # FULL CODE
                            "complexity": complexity,
                            "loc": loc,
                            "imports": imports,
                            "num_methods": len(methods),
                            "num_classes": len(classes),
                            "method_names": [m[1] for m in methods[:10]],  # First 10
                            "class_names": [c[1] for c in classes]
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
        output_file = dataset_dir / "codexglue_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'CodeXGLUE_Real',
                'description': 'Real code dataset for ML tasks',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_files': len(dataset),
                'data': dataset,
                'extraction_method': 'file_based_analysis'
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"SUCCESS: REAL CodeXGLUE dataset generated: {len(dataset)} files -> {dataset_dir}")
        
        return {
            "status": "success",
            "total_files": len(dataset),
            "output_dir": str(dataset_dir),
            "output_file": str(output_file)
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python codexglue_generator.py <repo_path> [file_limit]")
        print("Example: python codexglue_generator.py d:/GitIntel/repo 500")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    file_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    generator = CodeXGLUEGenerator(repo_path, file_limit=file_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_files']} file entries")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
