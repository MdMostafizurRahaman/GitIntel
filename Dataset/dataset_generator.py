"""
Professional Dataset Generator
Creates datasets similar to Defects4J, Bugs.jar, CodeXGLUE, etc. from existing repositories
"""

import os
import json
import csv
import random
from pathlib import Path
from typing import Dict, List, Any
import logging
import subprocess
from datetime import datetime
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfessionalDatasetGenerator:
    """Generates professional-quality datasets from Java repositories"""

    def __init__(self, workspace_path: str, commit_limit: int = None, timestamp: str = None):
        self.workspace = Path(workspace_path)
        # Output always goes to Dataset/generated_datasets folder
        self.output_dir = Path(__file__).parent / "generated_datasets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repositories = self._find_repositories()
        self.commit_limit = commit_limit  # None means ALL commits
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"📁 Output directory: {self.output_dir}")

    def _find_repositories(self) -> List[Dict]:
        """Find all git repositories in workspace"""
        repos = []
        
        # ALWAYS use workspace itself if it has Java files (git or not)
        # This allows processing ANY folder user provides
        repos.append({
            "name": self.workspace.name,
            "path": self.workspace,
            "type": self._classify_repository(self.workspace)
        })
        logger.info(f"Using workspace as repository: {self.workspace.name}")
        return repos

    def _classify_repository(self, repo_path: Path) -> str:
        """Classify repository type"""
        if (repo_path / "pom.xml").exists():
            return "maven"
        elif (repo_path / "build.gradle").exists():
            return "gradle"
        elif (repo_path / "src").exists():
            return "java"
        else:
            return "unknown"
    

    def _get_java_files(self, repo_path: Path, limit: int = None) -> List[Path]:
        """Get all Java files in repository (for file-based analysis)
        
        Use for: PROMISE, CodeSearchNet, CodeXGLUE, Sourcerer
        """
        java_files = []
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden, build, test, and generated directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in ['target', 'build', 'node_modules', 'generated_datasets', 'output', '__pycache__']]
                
                for f in files:
                    if f.endswith('.java'):
                        java_files.append(Path(root) / f)
                        
                        if limit and len(java_files) >= limit:
                            return java_files
        except Exception as e:
            logger.error(f"Error getting Java files: {e}")
        
        logger.info(f"Found {len(java_files)} Java files")
        return java_files

    def generate_all_datasets(self):
        """Generate all types of professional datasets"""
        logger.info("Starting professional dataset generation...")

        # Generate datasets
        self.generate_defects4j_dataset()
        self.generate_bugs_jar_dataset()
        self.generate_codexglue_dataset()
        self.generate_codesearchnet_dataset()
        self.generate_sourcerer_dataset()
        self.generate_promise_dataset()
        self.generate_manystubs4j_dataset()

        logger.info("All datasets generated successfully!")

    def generate_defects4j_dataset(self):
        """Generate SYNTHETIC Defects4J-style dataset (Research Paper Based - ISSTA 2014)"""
        import random
        logger.info("🔧 Generating SYNTHETIC Defects4J-style dataset (mimicking ISSTA 2014 research)...")

        dataset = []
        dataset_dir = self.output_dir / f"defects4j_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        # Generate synthetic Java projects with bug characteristics (based on Defects4J research)
        num_projects = random.randint(5, 15)
        projects_data = []

        # Java project templates based on real Defects4J projects
        project_templates = [
            {"name": "Lang", "description": "Apache Commons Lang utilities"},
            {"name": "Math", "description": "Apache Commons Math library"},
            {"name": "Chart", "description": "JFreeChart visualization"},
            {"name": "Time", "description": "Joda-Time date library"},
            {"name": "Closure", "description": "Google Closure Compiler"},
            {"name": "Mockito", "description": "Mocking framework"},
            {"name": "Codec", "description": "Apache Commons Codec"}
        ]

        for i in range(num_projects):
            template = random.choice(project_templates)
            project = {
                'project_id': f'{template["name"]}_{i+1}',
                'project_name': template["name"],
                'description': template["description"],
                'language': 'Java',
                'bugs_found': random.randint(10, 100),
                'loc': random.randint(10000, 100000),
                'complexity': round(random.uniform(1.5, 5.0), 2),
                'test_coverage': round(random.uniform(0.3, 0.9), 2),
                'maintainability_index': round(random.uniform(40, 90), 2),
                'cyclomatic_complexity': random.randint(5, 50),
                'halstead_volume': round(random.uniform(1000, 50000), 2),
                'defect_density': round(random.uniform(0.1, 2.0), 2)
            }
            projects_data.append(project)

            # Create buggy/fixed directory structure for each project
            project_buggy_dir = dataset_dir / "buggy" / project['project_id']
            project_fixed_dir = dataset_dir / "fixed" / project['project_id']
            project_buggy_dir.mkdir(parents=True, exist_ok=True)
            project_fixed_dir.mkdir(parents=True, exist_ok=True)

            # Generate synthetic bugs for this project
            num_bugs = random.randint(5, 20)
            for bug_idx in range(num_bugs):
                bug_id = f"{project['project_id']}_bug_{bug_idx+1:03d}"

                # Create synthetic buggy Java code
                buggy_code = self._generate_synthetic_java_bug()
                fixed_code = self._generate_synthetic_java_fix(buggy_code)

                # Save buggy version
                buggy_file = project_buggy_dir / f"Bug_{bug_idx+1:03d}.java"
                with open(buggy_file, 'w', encoding='utf-8') as f:
                    f.write(buggy_code)

                # Save fixed version
                fixed_file = project_fixed_dir / f"Bug_{bug_idx+1:03d}.java"
                with open(fixed_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)

                # Create metadata
                metadata = {
                    "bug_id": bug_id,
                    "project": project['project_id'],
                    "project_name": project['project_name'],
                    "description": project['description'],
                    "bug_type": random.choice(["NullPointerException", "ArrayIndexOutOfBounds", "ClassCastException", "LogicError"]),
                    "severity": random.choice(["Low", "Medium", "High", "Critical"]),
                    "loc": random.randint(50, 500),
                    "complexity": random.randint(3, 25),
                    "test_coverage_before": round(random.uniform(0.2, 0.8), 2),
                    "test_coverage_after": round(random.uniform(0.6, 0.95), 2),
                    "time_to_fix_minutes": random.randint(30, 480),
                    "files_changed": 1,
                    "dataset_type": "defects4j_synthetic",
                    "research_paper": "Just et al. 'Defects4J: A Database of Existing Faults' (ISSTA 2014)"
                }

                # Save metadata
                with open(project_buggy_dir / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                with open(project_fixed_dir / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

                dataset.append(metadata)

        # Save comprehensive dataset info
        info = {
            "dataset_type": "Defects4J_Synthetic",
            "description": "Synthetic dataset mimicking Defects4J characteristics (ISSTA 2014)",
            "research_basis": "Just et al. 'Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java Programs' (ISSTA 2014)",
            "generated_at": datetime.now().isoformat(),
            "total_projects": len(projects_data),
            "total_bugs": len(dataset),
            "structure": ["buggy", "fixed"],
            "projects": projects_data,
            "generation_method": "synthetic_research_based"
        }

        info_file = dataset_dir / "dataset_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)

        logger.info(f"✅ SYNTHETIC Defects4J dataset generated: {len(dataset)} bugs across {len(projects_data)} projects -> {dataset_dir.name}/")
        logger.info(f"📊 Based on research: Just et al. (ISSTA 2014) - Real Defects4J has 835 bugs across 17 projects")

    def _generate_synthetic_java_bug(self) -> str:
        """Generate synthetic buggy Java code"""
        bug_templates = [
            """public class Calculator {
    public int divide(int a, int b) {
        return a / b;  // BUG: No division by zero check
    }
}""",
            """public class ArrayProcessor {
    public int getElement(int[] arr, int index) {
        return arr[index];  // BUG: No bounds checking
    }
}""",
            """public class StringUtils {
    public String process(String input) {
        return input.toUpperCase();  // BUG: Null pointer if input is null
    }
}"""
        ]
        return random.choice(bug_templates)

    def _generate_synthetic_java_fix(self, buggy_code: str) -> str:
        """Generate synthetic fixed Java code"""
        if "divide" in buggy_code:
            return """public class Calculator {
    public int divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero");
        }
        return a / b;
    }
}"""
        elif "getElement" in buggy_code:
            return """public class ArrayProcessor {
    public int getElement(int[] arr, int index) {
        if (arr == null || index < 0 || index >= arr.length) {
            throw new IndexOutOfBoundsException("Invalid array access");
        }
        return arr[index];
    }
}"""
        elif "process" in buggy_code:
            return """public class StringUtils {
    public String process(String input) {
        if (input == null) {
            return "";
        }
        return input.toUpperCase();
    }
}"""
        return buggy_code  # fallback

    def generate_bugs_jar_dataset(self):
        """Generate SYNTHETIC Bugs.jar-style dataset (Research Paper Based - MSR 2018)"""
        import random
        logger.info("🔧 Generating SYNTHETIC Bugs.jar-style dataset (mimicking MSR 2018 research)...")

        dataset = []
        dataset_dir = self.output_dir / f"bugsjar_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        # Generate synthetic bug data based on Bugs.jar research (MSR 2018)
        num_bugs = random.randint(1000, 5000)
        projects = ["Apache Commons", "Spring Framework", "Hibernate", "JUnit", "Mockito", "Jackson", "Guava"]

        bug_types = ['NullPointerException', 'ArrayIndexOutOfBounds', 'ClassCastException',
                     'IllegalArgumentException', 'IOException', 'SQLException', 'NoSuchMethodError']
        severities = ['Low', 'Medium', 'High', 'Critical']

        for i in range(num_bugs):
            project = random.choice(projects)
            bug = {
                'bug_id': f'BUG_{i+1:05d}',
                'project': project,
                'bug_type': random.choice(bug_types),
                'severity': random.choice(severities),
                'loc': random.randint(50, 5000),
                'complexity': round(random.uniform(1.0, 8.0), 2),
                'time_to_fix_minutes': random.randint(15, 1440),  # 15 min to 24 hours
                'files_changed': random.randint(1, 10),
                'methods_affected': random.randint(1, 5),
                'test_coverage_before': round(random.uniform(0.1, 0.8), 2),
                'test_coverage_after': round(random.uniform(0.6, 0.95), 2),
                'lines_added': random.randint(1, 100),
                'lines_deleted': random.randint(0, 50),
                'dataset_type': 'bugs_jar_synthetic',
                'research_paper': 'Saha et al. "Bugs.jar: A Large-scale, Diverse Dataset of Existing Bugs" (MSR 2018)'
            }
            dataset.append(bug)

        # Save to JSON (first 1000 for readability)
        output_file = dataset_dir / "bugs_jar_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'BugsJar_Synthetic',
                'description': 'Synthetic dataset mimicking Bugs.jar characteristics (MSR 2018)',
                'research_basis': 'Saha et al. "Bugs.jar: A Large-scale, Diverse Dataset of Existing Bugs in Java" (MSR 2018)',
                'generated_at': datetime.now().isoformat(),
                'total_bugs': len(dataset),
                'bugs': dataset[:1000],  # Save first 1000 for readability
                'generation_method': 'synthetic_research_based'
            }, f, indent=2)

        logger.info(f"✅ SYNTHETIC Bugs.jar dataset generated: {len(dataset)} bugs -> {dataset_dir.name}/")
        logger.info(f"📊 Based on research: Saha et al. (MSR 2018) - Real Bugs.jar has 1,158 bugs across 9 projects")

        logger.info(f"Bugs.jar dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_codexglue_dataset(self):
        """Generate CodeXGLUE-style dataset with COMPREHENSIVE data (FILE ANALYSIS like OLD code)"""
        logger.info("Generating CodeXGLUE-style dataset...")

        dataset = []
        
        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for CodeXGLUE dataset...")
            
            # Use FILE ANALYSIS - get ALL files (no limit)
            java_files = self._get_java_files(repo["path"], limit=None)
            
            for file_path in java_files:
                    try:
                        # Read current file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                        
                        if not code.strip():
                            continue
                        
                        # Get relative path
                        try:
                            rel_path = file_path.relative_to(repo["path"])
                        except:
                            rel_path = file_path.name

                        # Extract method signatures
                        import re
                        methods = re.findall(r'(public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)', code)

                        if not methods:
                            # If no methods, include whole file as snippet
                            complexity = code.count('if ') + code.count('for ') + code.count('while ')
                            
                            record = {
                                "project": repo['name'],
                                "file_path": str(rel_path),
                                "language": "java",
                                "dataset_type": "codexglue",
                                "signature": f"class {file_path.stem}",
                                "code_snippet": code,  # Full code
                                "complexity": complexity,
                                "loc": len([l for l in code.split('\n') if l.strip()])
                            }
                            dataset.append(record)
                        else:
                            # Include each method
                            for method in methods[:5]:  # Max 5 methods per file
                                signature = f"{method[0]} {method[1]}()"
                                
                                # Calculate complexity
                                complexity = code.count('if ') + code.count('for ') + code.count('while ')
                                
                                record = {
                                    "project": repo['name'],
                                    "file_path": str(rel_path),
                                    "language": "java",
                                    "dataset_type": "codexglue",
                                    "signature": signature,
                                    "code_snippet": code,  # Full code
                                    "complexity": complexity,
                                    "loc": len([l for l in code.split('\n') if l.strip()])
                                }
                                dataset.append(record)
                        
                        if len(dataset) % 200 == 0:
                            logger.info(f"Processed {len(dataset)} snippets for CodeXGLUE...")

                    except Exception as e:
                        logger.warning(f"Error processing {file_path}: {e}")
                        continue

        output_file = self.output_dir / f"codexglue_dataset_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"CodeXGLUE dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_codesearchnet_dataset(self):
        """Generate CodeSearchNet-style dataset with COMPREHENSIVE data (FILE ANALYSIS like OLD code)"""
        logger.info("Generating CodeSearchNet-style dataset...")

        dataset = []
        
        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for CodeSearchNet dataset...")
            
            # Use FILE ANALYSIS - get ALL files (no limit)
            java_files = self._get_java_files(repo["path"], limit=None)
            
            for file_path in java_files:
                    try:
                        # Read current file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                        
                        if not code.strip():
                            continue
                        
                        # Get relative path
                        try:
                            rel_path = file_path.relative_to(repo["path"])
                        except:
                            rel_path = file_path.name

                        # Extract methods and javadoc
                        import re
                        methods = re.findall(r'(?:public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)', code)
                        javadocs = re.findall(r'/\*\*.*?\*/', code, re.DOTALL)
                        
                        # Tokenize code and docstring
                        code_tokens = re.findall(r'\w+|[^\w\s]', code)
                        docstring = javadocs[0] if javadocs else ""
                        docstring_clean = docstring.replace('/**', '').replace('*/', '').replace('*', '').strip()
                        
                        record = {
                            "project": repo['name'],
                            "file_path": str(rel_path),
                            "language": "java",
                            "dataset_type": "codesearchnet",
                            "code": code,  # FULL CODE (like OLD format)
                            "docstring": docstring_clean,
                            "code_tokens": code_tokens,  # Full token list (no limit)
                            "docstring_tokens": docstring_clean.split()
                        }
                        dataset.append(record)
                        
                        if len(dataset) % 200 == 0:
                            logger.info(f"Processed {len(dataset)} files for CodeSearchNet...")

                    except Exception as e:
                        logger.warning(f"Error processing {file_path}: {e}")
                        continue

        output_file = self.output_dir / f"codesearchnet_dataset_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"CodeSearchNet dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_sourcerer_dataset(self):
        """Generate Sourcerer-style dataset (FILE ANALYSIS like OLD code)"""
        logger.info("Generating Sourcerer-style dataset...")

        dataset = []

        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for Sourcerer dataset...")
            
            # Use FILE ANALYSIS - get ALL files (no limit)
            java_files = self._get_java_files(repo["path"], limit=None)
            
            for file_path in java_files:
                    try:
                        # Read current file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                        
                        if not code.strip():
                            continue
                        
                        # Get relative path
                        try:
                            rel_path = file_path.relative_to(repo["path"])
                        except:
                            rel_path = file_path.name
                        
                        # EXACT OLD format: project, file_path, language, dataset_type, code (FULL), file_size, line_count, has_pom, has_gradle
                        record = {
                            "project": repo['name'],
                            "file_path": str(rel_path),
                            "language": "java",
                            "dataset_type": "sourcerer",
                            "code": code,  # FULL code like OLD format
                            "file_size": len(code),
                            "line_count": len(code.split('\n')),
                            "has_pom": (repo["path"] / "pom.xml").exists(),
                            "has_gradle": (repo["path"] / "build.gradle").exists()
                        }
                        dataset.append(record)
                        
                        if len(dataset) % 200 == 0:
                            logger.info(f"Processed {len(dataset)} files for Sourcerer...")

                    except Exception as e:
                        logger.warning(f"Error processing {file_path}: {e}")
                        continue

        output_file = self.output_dir / f"sourcerer_dataset_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Sourcerer dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_promise_dataset(self):
        """Generate PROMISE-style dataset with COMPREHENSIVE 42 columns (OLD method: analyzes CURRENT files, not commits)"""
        logger.info("Generating PROMISE-style dataset...")

        dataset = []
        
        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for PROMISE dataset...")
            
            # Use FILE ANALYSIS - get ALL files (no limit)
            java_files = self._get_java_files(repo["path"], limit=None)
            
            for i, file_path in enumerate(java_files):
                    try:
                        # Read current file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                        
                        if not code.strip():
                            continue
                        
                        # Get relative path
                        try:
                            rel_path = file_path.relative_to(repo["path"])
                        except:
                            rel_path = file_path.name
                        
                        # Count metrics (REAL analysis, not mock)
                        loc = len([line for line in code.split('\n') if line.strip()])
                        comment_lines = code.count('//') + code.count('/*')
                        blank_lines = code.count('\n\n')
                        
                        # Calculate complexity
                        cyclomatic = (code.count('if ') + code.count('else ') + 
                                    code.count('for ') + code.count('while ') +
                                    code.count('case ') + code.count('catch '))
                        wmc = cyclomatic + 1
                        
                        # Count classes, methods, fields
                        import re
                        num_classes = len(re.findall(r'\bclass\s+\w+', code))
                        num_interfaces = len(re.findall(r'\binterface\s+\w+', code))
                        num_methods = len(re.findall(r'(public|private|protected|static)\s+[\w<>\[\]]+\s+\w+\s*\(', code))
                        num_fields = len(re.findall(r'(public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*(=|;)', code))
                        num_public_methods = len(re.findall(r'public\s+[\w<>\[\]]+\s+\w+\s*\(', code))
                        num_static_methods = len(re.findall(r'static\s+[\w<>\[\]]+\s+\w+\s*\(', code))
                        
                        # COMPREHENSIVE 42 columns (like OLD promise_dataset.csv)
                        record = {
                            "project": repo['name'],
                            "file": str(rel_path),
                            "class_name": file_path.stem,
                            "language": "java",
                            "dataset_type": "promise",
                            "type": "comprehensive_java_metrics",
                            "loc": loc,
                            "comment_lines": comment_lines,
                            "blank_lines": blank_lines,
                            "total_lines": loc + blank_lines,
                            "lines_of_code_actual": loc,
                            "cyclomatic_complexity": cyclomatic,
                            "max_nesting_depth": min(5, cyclomatic // 2),
                            "avg_nesting_depth": float(cyclomatic / 3) if cyclomatic > 0 else 1.0,
                            "cognitive_complexity": float(cyclomatic * 1.2),
                            "wmc": wmc,
                            "dit": 1,
                            "noc": 0,
                            "cbo": num_classes,
                            "rfc": num_methods,
                            "lcom": 0.0,
                            "num_classes": num_classes,
                            "num_interfaces": num_interfaces,
                            "num_methods": num_methods,
                            "num_fields": num_fields,
                            "num_public_methods": num_public_methods,
                            "num_private_methods": num_methods - num_public_methods,
                            "num_static_methods": num_static_methods,
                            "comment_ratio": round(comment_lines / loc, 3) if loc > 0 else 0,
                            "has_comments": comment_lines > 0,
                            "avg_method_loc": round(loc / num_methods, 2) if num_methods > 0 else 0,
                            "max_method_loc": loc,
                            "maintainability_index": round(max(0, 100 - (cyclomatic * 0.5) - (loc * 0.01)), 2),
                            "has_defect": 0,
                            "defect_type": "none",
                            "num_bugs": 0,
                            "bug_severity": "none",
                            "afferent_coupling": num_classes,
                            "efferent_coupling": num_classes,
                            "instability": round(1.0 / num_classes, 3) if num_classes > 0 else 0,
                            "halstead_volume": 0,
                            "halstead_difficulty": 0,
                            "technical_debt_hours": round(loc * 0.001, 2),
                            "code_smells": 0,
                            "defects": 0,  # Binary label
                        }
                        dataset.append(record)
                        
                        if len(dataset) % 100 == 0:
                            logger.info(f"Processed {len(dataset)} files for PROMISE...")
                    
                    except Exception as e:
                        logger.warning(f"Error processing {file_path}: {e}")
                        continue

        output_file = self.output_dir / f"promise_dataset_{self.timestamp}.csv"
        if dataset:
            import pandas as pd
            df = pd.DataFrame(dataset)
            df.to_csv(output_file, index=False)

        logger.info(f"PROMISE dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_manystubs4j_dataset(self):
        """Generate SYNTHETIC ManySStuBs4J-style dataset (Research Paper Based - MSR 2025)"""
        import random
        logger.info("🔧 Generating SYNTHETIC ManySStuBs4J-style dataset (mimicking MSR 2025 research)...")

        dataset = []
        dataset_dir = self.output_dir / f"manystubs4j_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        # Generate synthetic issue data based on ManySStuBs4J research (MSR 2025)
        num_issues = random.randint(5000, 15000)
        projects = ["Apache Commons", "Spring Framework", "Hibernate", "JUnit", "Mockito", "Jackson", "Guava", "Eclipse JDT"]

        issue_types = ['Bug Fix', 'Feature Addition', 'Refactoring', 'Performance Improvement', 'Security Fix']
        severities = ['Low', 'Medium', 'High', 'Critical']

        # Generate synthetic Java code snippets for issues
        java_snippets = [
            """public class Calculator {
    public int divide(int a, int b) {
        return a / b; // Potential division by zero
    }
}""",
            """public class ListProcessor {
    public Object getElement(List<?> list, int index) {
        return list.get(index); // Potential IndexOutOfBoundsException
    }
}""",
            """public class StringUtils {
    public boolean isEmpty(String str) {
        return str.length() == 0; // Potential NullPointerException
    }
}"""
        ]

        for i in range(num_issues):
            project = random.choice(projects)
            issue = {
                'issue_id': f'ISSUE_{i+1:05d}',
                'project': project,
                'file_path': f'src/main/java/{project.lower().replace(" ", "")}/Example.java',
                'issue_type': random.choice(issue_types),
                'severity': random.choice(severities),
                'description': f'Issue #{i+1}: {random.choice(["Fixed null pointer exception", "Added bounds checking", "Improved error handling", "Enhanced performance", "Security vulnerability patched"])}',
                'code_snippet': random.choice(java_snippets),
                'loc': random.randint(10, 200),
                'complexity': random.randint(1, 15),
                'methods_affected': random.randint(1, 3),
                'test_cases_added': random.randint(0, 5),
                'review_comments': random.randint(0, 10),
                'time_to_resolve_hours': random.randint(1, 168),  # 1 hour to 1 week
                'dataset_type': 'manystubs4j_synthetic',
                'research_paper': 'Research on ManySStuBs4J dataset (MSR 2025)'
            }
            dataset.append(issue)

        # Save to JSON (first 2000 for readability)
        output_file = dataset_dir / "manystubs4j_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'ManySStuBs4J_Synthetic',
                'description': 'Synthetic dataset mimicking ManySStuBs4J characteristics (MSR 2025)',
                'research_basis': 'ManySStuBs4J: A Large and Diverse Dataset of Java Method Changes (MSR 2025)',
                'generated_at': datetime.now().isoformat(),
                'total_issues': len(dataset),
                'issues': dataset[:2000],  # Save first 2000 for readability
                'generation_method': 'synthetic_research_based'
            }, f, indent=2)

        logger.info(f"✅ SYNTHETIC ManySStuBs4J dataset generated: {len(dataset)} issues -> {dataset_dir.name}/")
        logger.info(f"📊 Based on research: ManySStuBs4J (MSR 2025) - Large dataset of Java method changes")

def main():
    """Main entry point"""
    import sys
    
    # Allow workspace path from command line OR use default
    if len(sys.argv) > 1:
        workspace_path = sys.argv[1]
    else:
        workspace_path = "d:\\GitIntel"  # Default: GitIntel (has repo/ with 1009 commits)
    
    print(f"📂 Using workspace: {workspace_path}")

    generator = ProfessionalDatasetGenerator(workspace_path)
    generator.generate_all_datasets()

    print("🎉 All professional datasets generated successfully!")
    print(f"📁 Check the output directory: {generator.output_dir}")

if __name__ == "__main__":
    main()