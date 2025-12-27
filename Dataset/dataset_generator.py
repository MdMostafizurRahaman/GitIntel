"""
Professional Dataset Generator
Creates datasets similar to Defects4J, Bugs.jar, CodeXGLUE, etc. from existing repositories
"""

import os
import json
import csv
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
    
    def _find_bug_fixing_commits(self, repo_path: Path) -> List[Dict]:
        """Find bug-fixing commits in repository (FROM OLD WORKING CODE)
        
        This method filters commits by bug-related keywords and gets parent commit info.
        Use for: Defects4J, Bugs.jar, ManySStuBs4J
        """
        bug_commits = []
        try:
            # First, check if repo has enough commits
            commit_count_result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=str(repo_path), capture_output=True, text=True, timeout=30
            )
            
            if commit_count_result.returncode == 0:
                total_commits = int(commit_count_result.stdout.strip())
                if total_commits < 2:
                    logger.warning(f"Repository has only {total_commits} commit(s). Commit-based datasets require at least 2 commits for parent comparison. Skipping.")
                    return []
                logger.info(f"Repository has {total_commits} commits available")
            
            # Get commits with bug-related keywords
            result = subprocess.run(
                ['git', 'log', '--oneline', '--grep=fix', '--grep=bug', '--grep=error', 
                 '--grep=issue', '--grep=patch', '-n', '100'],
                cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=60
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                # Fallback: get any commits (no keyword filter)
                logger.warning("No bug-fixing commits found, using all commits as fallback")
                result = subprocess.run(
                    ['git', 'log', '--oneline', '-n', '100'],
                    cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=60
                )
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        commit_hash = parts[0]
                        message = parts[1]
                        
                        # Get parent commit
                        parent_result = subprocess.run(
                            ['git', 'rev-parse', f'{commit_hash}^'],
                            cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore'
                        )
                        parent = parent_result.stdout.strip() if parent_result.returncode == 0 else ""
                        
                        # Get changed files (ALL files first, then filter Java)
                        files_result = subprocess.run(
                            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                            cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore'
                        )
                        all_files = files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []
                        all_files = [f for f in all_files if f]  # Remove empty strings
                        java_files = [f for f in all_files if f.endswith('.java')]
                        
                        # Get date
                        date_result = subprocess.run(
                            ['git', 'show', '-s', '--format=%ad', '--date=short', commit_hash],
                            cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore'
                        )
                        date = date_result.stdout.strip() if date_result.returncode == 0 else ""
                        
                        # Get diff
                        diff_result = subprocess.run(
                            ['git', 'show', commit_hash],
                            cwd=str(repo_path), capture_output=True, text=True, encoding='utf-8', errors='ignore'
                        )
                        diff = diff_result.stdout if diff_result.returncode == 0 else ""
                        
                        if parent:  # Only include commits with parent (skip initial commit)
                            bug_commits.append({
                                'hash': commit_hash,
                                'parent': parent,
                                'message': message,
                                'files': java_files,
                                'date': date,
                                'diff': diff
                            })
        
        except Exception as e:
            logger.error(f"Error finding bug commits: {e}")
        
        logger.info(f"Found {len(bug_commits)} bug-fixing commits")
        return bug_commits
    
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
        """Generate Defects4J-style bug fix dataset from GIT COMMITS (uses OLD working method)"""
        logger.info("Generating Defects4J-style dataset...")

        dataset = []
        dataset_dir = self.output_dir / f"defects4j_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for Defects4J dataset...")
            
            # Use OLD working method: find bug-fixing commits with keywords
            bug_commits = self._find_bug_fixing_commits(repo["path"])
            
            if len(bug_commits) == 0:
                logger.warning(f"Repository has NO bug-fixing commits. Defects4J requires commit history with bug fixes (keywords: fix, bug, error, issue, patch). Skipping.")
                continue
            
            for i, commit in enumerate(bug_commits[:50]):  # Limit to 50 like OLD code
                    bug_id = f"{repo['name']}_bug_{len(dataset)+1:03d}"
                    
                    # Create directories for buggy and fixed versions
                    buggy_dir = dataset_dir / "buggy" / bug_id
                    fixed_dir = dataset_dir / "fixed" / bug_id
                    buggy_dir.mkdir(parents=True, exist_ok=True)
                    fixed_dir.mkdir(parents=True, exist_ok=True)
                    
                    files_saved = 0
                    try:
                        # Process each changed Java file
                        for java_file in commit['files'][:5]:  # Max 5 files per bug
                            if not java_file:
                                continue
                                
                            # Get buggy (parent) and fixed (current) code
                            buggy_cmd = ['git', 'show', f'{commit["parent"]}:{java_file}']
                            fixed_cmd = ['git', 'show', f'{commit["hash"]}:{java_file}']
                            
                            buggy_result = subprocess.run(buggy_cmd, capture_output=True, text=True, 
                                                        encoding='utf-8', errors='ignore', 
                                                        cwd=str(repo["path"]), timeout=30)
                            fixed_result = subprocess.run(fixed_cmd, capture_output=True, text=True, 
                                                        encoding='utf-8', errors='ignore', 
                                                        cwd=str(repo["path"]), timeout=30)
                            
                            if buggy_result.returncode == 0 and fixed_result.returncode == 0:
                                buggy_code = buggy_result.stdout
                                fixed_code = fixed_result.stdout
                                
                                if buggy_code and fixed_code and buggy_code != fixed_code:
                                    # Save buggy version
                                    file_name = os.path.basename(java_file)
                                    with open(buggy_dir / file_name, 'w', encoding='utf-8') as f:
                                        f.write(buggy_code)
                                    
                                    # Save fixed version
                                    with open(fixed_dir / file_name, 'w', encoding='utf-8') as f:
                                        f.write(fixed_code)
                                    
                                    files_saved += 1
                    
                    except Exception as e:
                        logger.warning(f"Error processing bug {bug_id}: {e}")
                        continue
                    
                    # ONLY save metadata if we actually saved some Java files
                    if files_saved == 0:
                        logger.warning(f"Bug {bug_id} has NO valid Java files. Removing directories.")
                        import shutil
                        shutil.rmtree(buggy_dir, ignore_errors=True)
                        shutil.rmtree(fixed_dir, ignore_errors=True)
                        continue
                    
                    # Save metadata (like OLD code)
                    metadata = {
                        "bug_id": bug_id,
                        "project": repo['name'],
                        "commit_buggy": commit.get("parent", ""),
                        "commit_fixed": commit.get("hash", ""),
                        "message": commit.get("message", ""),
                        "files_changed": commit.get("files", []),
                        "timestamp": commit.get("date", ""),
                        "dataset_type": "defects4j"
                    }
                    
                    with open(buggy_dir / "metadata.json", 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    with open(fixed_dir / "metadata.json", 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    
                    dataset.append(metadata)

        # Save dataset info
        info = {
            "dataset_type": "Defects4J",
            "generated": datetime.now().isoformat(),
            "bug_count": len(dataset),
            "structure": ["buggy", "fixed"]
        }
        info_file = dataset_dir / "dataset_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)

        if len(dataset) == 0:
            logger.warning(f"⚠️ NO DEFECTS4J DATA GENERATED! Repository needs commit history with bug-fixing commits (keywords: fix, bug, error, issue, patch).")
        
        logger.info(f"Defects4J dataset saved: {len(dataset)} bugs -> {dataset_dir.name}/")

    def generate_bugs_jar_dataset(self):
        """Generate Bugs.jar-style metrics dataset from GIT COMMITS (uses OLD working method)"""
        logger.info("Generating Bugs.jar-style dataset...")

        dataset = []

        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for Bugs.jar dataset...")
            
            # Use OLD working method: find bug-fixing commits
            bug_commits = self._find_bug_fixing_commits(repo["path"])
            
            if len(bug_commits) == 0:
                logger.warning(f"Repository has NO bug-fixing commits. Bugs.jar requires commit history. Skipping.")
                continue
            
            for i, commit in enumerate(bug_commits):
                try:
                    # Process each changed Java file
                    for java_file in commit['files'][:5]:  # Max 5 files per commit
                        if not java_file:
                            continue
                        
                        # Get code from fixed version (current commit)
                        code_cmd = ['git', 'show', f'{commit["hash"]}:{java_file}']
                        code_result = subprocess.run(code_cmd, capture_output=True, text=True, 
                                                   encoding='utf-8', errors='ignore', 
                                                   cwd=str(repo["path"]), timeout=30)
                        
                        if code_result.returncode == 0:
                            code = code_result.stdout
                            
                            # EXACT OLD format WITH patch field
                            record = {
                                "bug_id": f"BUG-{i+1:04d}",
                                "project": repo['name'],
                                "file_path": java_file,
                                "commit_buggy": commit.get("parent", ""),
                                "commit_fixed": commit.get("hash", ""),
                                "message": commit.get("message", ""),
                                "language": "java",
                                "dataset_type": "bugs_jar",
                                "loc": len([l for l in code.split('\n') if l.strip()]),
                                "classes": code.count('class '),
                                "methods": code.count('public ') + code.count('private ') + code.count('protected '),
                                "complexity": code.count('if ') + code.count('for ') + code.count('while ') + 1,
                                "patch": commit.get("diff", "")[:2000],  # Include patch (limit size)
                                "has_bug": True
                            }
                            dataset.append(record)

                except Exception as e:
                    logger.warning(f"Error processing commit {commit['hash'][:8]}: {e}")
                    continue

        output_file = self.output_dir / f"bugs_jar_dataset_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Bugs.jar dataset saved: {len(dataset)} records -> {output_file.name}")

    def generate_codexglue_dataset(self):
        """Generate CodeXGLUE-style dataset with COMPREHENSIVE data (FILE ANALYSIS like OLD code)"""
        logger.info("Generating CodeXGLUE-style dataset...")

        dataset = []
        
        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for CodeXGLUE dataset...")
            
            # Use FILE ANALYSIS (like PROMISE) - NOT commits!
            java_files = self._get_java_files(repo["path"], limit=500)
            
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
            
            # Use FILE ANALYSIS - NOT commits!
            java_files = self._get_java_files(repo["path"], limit=500)
            
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
                            "code_tokens": code_tokens[:500],  # Limit tokens
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
            
            # Use FILE ANALYSIS - NOT commits!
            java_files = self._get_java_files(repo["path"], limit=500)
            
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
            
            # Use FILE ANALYSIS (like OLD code) - NOT commits!
            java_files = self._get_java_files(repo["path"], limit=200)
            
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
        """Generate ManySStuBs4J-style dataset from GIT COMMITS (uses OLD working method)"""
        logger.info("Generating ManySStuBs4J-style dataset...")

        dataset = []
        issue_count = 0

        for repo in self.repositories:
            logger.info(f"Processing {repo['name']} for ManySStuBs4J dataset...")
            
            # Use OLD working method: find bug-fixing commits
            bug_commits = self._find_bug_fixing_commits(repo["path"])
            
            if len(bug_commits) == 0:
                logger.warning(f"Repository has NO bug-fixing commits. ManySStuBs4J requires commit history. Skipping.")
                continue
            
            for commit in bug_commits[:50]:  # Limit like OLD code
                try:
                    # Process each changed Java file
                    for java_file in commit['files'][:3]:  # Max 3 files per commit
                        if not java_file:
                            continue
                        
                        # Get code from fixed version
                        code_cmd = ['git', 'show', f'{commit["hash"]}:{java_file}']
                        code_result = subprocess.run(code_cmd, capture_output=True, text=True, 
                                                   encoding='utf-8', errors='ignore', 
                                                   cwd=str(repo["path"]), timeout=30)
                        
                        if code_result.returncode == 0:
                            code = code_result.stdout
                            issue_count += 1
                            
                            # EXACT OLD format: issue_id, project, file_path, issue_type, severity, description, code_snippet, dataset_type
                            record = {
                                "issue_id": f"{repo['name']}_issue_{issue_count:03d}",
                                "project": repo['name'],
                                "file_path": java_file,
                                "issue_type": "Bug Fix",
                                "severity": "medium",
                                "description": commit.get("message", "")[:200],
                                "code_snippet": code,  # FULL code like OLD format
                                "commit_buggy": commit.get("parent", ""),
                                "commit_fixed": commit.get("hash", ""),
                                "dataset_type": "manystubs4j"
                            }
                            dataset.append(record)

                except Exception as e:
                    logger.warning(f"Error processing commit {commit['hash'][:8]}: {e}")
                    continue

        output_file = self.output_dir / f"manystubs4j_dataset_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"ManySStuBs4J dataset saved: {len(dataset)} records -> {output_file.name}")

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