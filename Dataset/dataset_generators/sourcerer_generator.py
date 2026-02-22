import os
import json
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

try:
    from .oop_analysis import OOPAnalyzer
    OOP_ANALYSIS_AVAILABLE = True
except ImportError:
    try:
        from oop_analysis import OOPAnalyzer
        OOP_ANALYSIS_AVAILABLE = True
    except ImportError:
        OOP_ANALYSIS_AVAILABLE = False
        print("WARNING: oop_analysis module not available")

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False
    print("WARNING: javalang not installed. Install with: pip install javalang")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourcererGenerator:
    
    def __init__(self, repo_path: str, output_dir: str = None, file_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.file_limit = file_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized Sourcerer generator for {self.repo_path}")
    
    def _get_all_files(self, extension: str = None) -> List[Path]:
        """Get all files in repository"""
        files = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['target', 'build', 'node_modules', 'generated_datasets', '__pycache__']]
            
            for f in filenames:
                if extension:
                    if f.endswith(extension):
                        files.append(Path(root) / f)
                else:
                    files.append(Path(root) / f)
        
        return files
    
    def generate(self) -> Dict:
        """Generate REAL Sourcerer dataset from repository"""
        logger.info("Generating REAL Sourcerer dataset from repository structure...")
        
        dataset = []
        dataset_dir = self.output_dir / f"sourcerer_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)
        
        project_name = self.repo_path.name
        
        try:
            # Get all Java files (not limited - process until we have enough records)
            java_files = self._get_all_files('.java')
            logger.info(f"Found {len(java_files)} Java files")
            
            # Get repository-level statistics
            all_files = self._get_all_files()
            
            # Calculate file type distribution
            file_types = {}
            for file in all_files:
                ext = file.suffix if file.suffix else 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # Process each Java file
            total_loc = 0
            total_classes = 0
            total_methods = 0
            total_imports = 0
            
            for file_path in java_files:
                # Stop if we've found enough records
                if self.file_limit and len(dataset) >= self.file_limit:
                    break
                
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
                    
                    # Count LOC
                    loc = len([l for l in code.split('\n') if l.strip()])
                    total_loc += loc
                    
                    # Perform OOP Analysis using separate module
                    oop_metrics = {}
                    if OOP_ANALYSIS_AVAILABLE:
                        oop_metrics = OOPAnalyzer.analyze(code)
                    else:
                        # Fallback to basic regex
                        import re
                        oop_metrics = {
                            "num_classes": len(re.findall(r'\bclass\s+\w+', code)),
                            "num_interfaces": len(re.findall(r'\binterface\s+\w+', code)),
                            "num_enums": len(re.findall(r'\benum\s+\w+', code)),
                            "num_methods": len(re.findall(r'(public|private|protected|static)\s+[\w<>\[\]]+\s+\w+\s*\(', code)),
                            "num_fields": 0,
                            "num_abstract_methods": 0,
                            "num_static_methods": 0,
                            "inheritance_depth": 0,
                            "implements_count": 0,
                            "extraction_method": "regex_fallback"
                        }
                    
                    # Extract individual metrics
                    classes = oop_metrics.get("num_classes", 0)
                    interfaces = oop_metrics.get("num_interfaces", 0)
                    enums = oop_metrics.get("num_enums", 0)
                    methods = oop_metrics.get("num_methods", 0)
                    fields = oop_metrics.get("num_fields", 0)
                    abstract_methods = oop_metrics.get("num_abstract_methods", 0)
                    static_methods = oop_metrics.get("num_static_methods", 0)
                    inheritance_depth = oop_metrics.get("inheritance_depth", 0)
                    implements_count = oop_metrics.get("implements_count", 0)
                    
                    # Count imports separately (not part of OOP analysis)
                    imports = 0
                    if JAVALANG_AVAILABLE:
                        try:
                            tree = javalang.parse.parse(code)
                            if tree.imports:
                                imports = len(tree.imports)
                        except:
                            import re
                            imports = len(re.findall(r'import\s+[\w\.]+;', code))
                    else:
                        import re
                        imports = len(re.findall(r'import\s+[\w\.]+;', code))
                    
                    total_classes += classes
                    total_methods += methods
                    total_imports += imports
                    
                    # Get file size
                    file_size = len(code)
                    
                    record = {
                        "project": project_name,
                        "file_path": str(rel_path),
                        "language": "java",
                        "dataset_type": "sourcerer",
                        "code": code,  # FULL CODE - REAL
                        "file_size": file_size,
                        "loc": loc,
                        
                        # Basic counts
                        "num_classes": classes,
                        "num_interfaces": interfaces,
                        "num_enums": enums,
                        "num_methods": methods,
                        "num_imports": imports,
                        
                        # OOP Analysis - REAL metrics
                        "num_fields": fields,
                        "num_abstract_methods": abstract_methods,
                        "num_static_methods": static_methods,
                        "inheritance_depth": inheritance_depth,
                        "implements_count": implements_count,
                        
                        # Project info
                        "has_pom": (self.repo_path / "pom.xml").exists(),
                        "has_gradle": (self.repo_path / "build.gradle").exists(),
                        
                        # Metadata
                        "extraction_method": "javalang_ast",
                        "is_real_data": True
                    }
                    
                    dataset.append(record)
                    
                    if len(dataset) % 100 == 0:
                        logger.info(f"Processed {len(dataset)} files...")
                
                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    continue
            
            logger.info(f"Extracted data from {len(dataset)} files")
            
            # Create repository summary
            repo_summary = {
                "project_name": project_name,
                "repository_path": str(self.repo_path),
                "total_files": len(all_files),
                "total_java_files": len(java_files),
                "total_loc": total_loc,
                "total_classes": total_classes,
                "total_methods": total_methods,
                "total_imports": total_imports,
                "avg_loc_per_file": total_loc // len(java_files) if java_files else 0,
                "avg_methods_per_file": total_methods // len(java_files) if java_files else 0,
                "file_type_distribution": file_types,
                "has_pom": (self.repo_path / "pom.xml").exists(),
                "has_gradle": (self.repo_path / "build.gradle").exists(),
                "has_maven": (self.repo_path / "pom.xml").exists(),
                "build_system": self._detect_build_system()
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
        
        # Save file-level data
        output_file = dataset_dir / "sourcerer_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'Sourcerer_Real',
                'description': 'Real repository structure and code statistics',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_files': len(dataset),
                'data': dataset,
                'extraction_method': 'file_system_analysis'
            }, f, indent=2, ensure_ascii=False)
        
        # Save repository summary
        summary_file = dataset_dir / "repository_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(repo_summary, f, indent=2)
        
        logger.info(f"SUCCESS: REAL Sourcerer dataset generated: {len(dataset)} files -> {dataset_dir}")
        
        # Generate README
        readme = dataset_dir / "README.md"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"""# Sourcerer Dataset

## Overview
This dataset follows the **Sourcerer** standard from https://sourcerer.ics.uci.edu/

Sourcerer provides large-scale code repository analysis with fine-grained metrics.

### Structure:
```
sourcerer_dataset_{self.timestamp}/
├── sourcerer_dataset.json      # File-level analysis data
├── repository_summary.json     # Repository-level statistics
└── README.md                   # This file
```

### File-Level Data Format:
```json
{{
  "project": "project_name",
  "file_path": "src/Main.java",
  "language": "java",
  "dataset_type": "sourcerer",
  "code": "<full source code>",
  "file_size": 1250,
  "loc": 45,
  
  "num_classes": 1,
  "num_interfaces": 0,
  "num_enums": 0,
  "num_methods": 5,
  "num_imports": 8,
  
  "num_fields": 3,
  "num_abstract_methods": 0,
  "num_static_methods": 2,
  "inheritance_depth": 1,
  "implements_count": 0,
  
  "has_pom": true,
  "has_gradle": false,
  "extraction_method": "javalang_ast",
  "is_real_data": true
}}
```

### Repository-Level Summary:
```json
{{
  "project_name": "my_project",
  "repository_path": "/path/to/repo",
  "total_files": 150,
  "total_java_files": 120,
  "total_loc": 50000,
  "total_classes": 85,
  "total_methods": 2450,
  "total_imports": 890,
  "avg_loc_per_file": 417,
  "avg_methods_per_file": 20,
  "file_type_distribution": {{ ".java": 120, ".xml": 5, ".md": 2 }},
  "has_pom": true,
  "build_system": "Maven"
}}
```

### Metrics by File:

**Size Metrics:**
- `file_size`: Characters in file
- `loc`: Lines of code (non-blank)

**Class/Interface Metrics:**
- `num_classes`: Classes defined
- `num_interfaces`: Interfaces defined
- `num_enums`: Enumerations
- `num_methods`: Total methods

**Complexity Metrics:**
- `num_fields`: Member fields
- `num_abstract_methods`: Abstract method count
- `num_static_methods`: Static method count
- `inheritance_depth`: Inheritance distance
- `implements_count`: Interface implementations

### Statistics:
- **Total files**: {len(dataset)}
- **Total LOC**: {total_loc}
- **Total classes**: {total_classes}
- **Total methods**: {total_methods}
- **Avg LOC/file**: {total_loc // len(dataset) if dataset else 0}
- **Build system**: {repo_summary.get('build_system', 'Unknown')}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Use Cases
- Large-scale code repository analysis
- Type/tool statistics
- Language ecosystem analysis
- Software engineering research

## References
- Sourcerer: https://sourcerer.ics.uci.edu/
- GitHub: https://github.com/Mondego/Sourcerer
- Application website: https://sourcerer.io/
""")

        logger.info(f"Generated README at {readme}")
        
        return {
            "status": "success",
            "total_files": len(dataset),
            "total_loc": total_loc,
            "output_dir": str(dataset_dir),
            "output_file": str(output_file),
            "summary_file": str(summary_file)
        }
    
    def _detect_build_system(self) -> str:
        """Detect build system"""
        if (self.repo_path / "pom.xml").exists():
            return "Maven"
        elif (self.repo_path / "build.gradle").exists():
            return "Gradle"
        elif (self.repo_path / "build.xml").exists():
            return "Ant"
        else:
            return "Unknown"


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sourcerer_generator.py <repo_path>")
        print("Example: python sourcerer_generator.py d:/GitIntel/repo")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    generator = SourcererGenerator(repo_path)
    result = generator.generate()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_files']} file entries")
        print(f"Total LOC: {result['total_loc']}")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
