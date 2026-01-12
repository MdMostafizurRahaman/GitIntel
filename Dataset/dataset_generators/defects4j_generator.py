"""
REAL Defects4J Dataset Generator
Follows EXACT official Defects4J structure from https://github.com/rjust/defects4j
"""

import os
import json
import csv
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import re
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Defects4JGenerator:
    """Generate REAL Defects4J-style dataset following official structure"""
    
    def __init__(self, repo_path: str, output_dir: str = None, commit_limit: int = 500):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "generated_datasets"
        self.commit_limit = commit_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a Git repository: {repo_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.project_name = self.repo_path.name
        
        logger.info(f"Initialized Defects4J generator for {self.repo_path}")
    
    def _is_bug_fixing_commit(self, commit_msg: str) -> Tuple[bool, Optional[str]]:
        """Detect if commit is a bug fix using Defects4J criteria"""
        msg_lower = commit_msg.lower()
        
        bug_keywords = ['fix', 'bug', 'error', 'issue', 'defect', 'fault', 
                       'crash', 'exception', 'failure', 'problem', 'resolve']
        has_keyword = any(k in msg_lower for k in bug_keywords)
        
        issue_patterns = [
            r'([A-Z]+-\d+)',
            r'#(\d+)',
            r'issue[\s-]*(\d+)',
        ]
        
        issue_id = None
        for pattern in issue_patterns:
            match = re.search(pattern, commit_msg, re.IGNORECASE)
            if match:
                issue_id = match.group(0)
                break
        
        false_positives = ['typo', 'format', 'style', 'docs', 'documentation',
                          'comment', 'whitespace', 'indent', 'refactor']
        is_false_positive = any(fp in msg_lower for fp in false_positives)
        
        is_bug_fix = (has_keyword or issue_id) and not is_false_positive
        return is_bug_fix, issue_id
    
    def _get_file_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """Get file content at specific commit"""
        try:
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            logger.error(f"Error getting file at commit: {e}")
            return None
    
    def _get_modified_files(self, commit_hash: str) -> List[str]:
        """Get list of modified Java files in commit"""
        try:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.split('\n') if f.strip().endswith('.java')]
                return files
            return []
        except Exception as e:
            logger.error(f"Error getting modified files: {e}")
            return []
    
    def generate(self) -> Dict:
        """Generate REAL Defects4J dataset following official structure"""
        logger.info(f"🔧 Generating REAL Defects4J dataset (limit: {self.commit_limit or 'all'})...")
        
        # Create project directory structure: defects4j_dataset_<timestamp>/<project_name>/
        dataset_dir = self.output_dir / f"defects4j_dataset_{self.timestamp}"
        project_dir = dataset_dir / self.project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        patches_dir = project_dir / "patches"
        patches_dir.mkdir(exist_ok=True)
        
        bugs_data = []
        bug_count = 0
        
        try:
            result = subprocess.run(
                ['git', 'log', '--reverse', '--format=%H|||%an|||%ae|||%ad|||%s|||%b', 
                 '--date=iso', '--no-merges'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to get git log: {result.stderr}")
            
            commits = [line for line in result.stdout.split('\n') if '|||' in line]
            logger.info(f"Found {len(commits)} total commits, analyzing...")
            
            for commit_line in commits:
                if self.commit_limit and bug_count >= self.commit_limit:
                    break
                
                parts = commit_line.split('|||')
                if len(parts) < 5:
                    continue
                
                commit_hash = parts[0].strip()
                author_name = parts[1].strip()
                commit_date = parts[3].strip()
                commit_subject = parts[4].strip()
                commit_body = parts[5].strip() if len(parts) > 5 else ""
                commit_msg = f"{commit_subject}\n{commit_body}"
                
                is_bug_fix, issue_id = self._is_bug_fixing_commit(commit_msg)
                if not is_bug_fix:
                    continue
                
                parent_result = subprocess.run(
                    ['git', 'rev-parse', f'{commit_hash}^'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if parent_result.returncode != 0:
                    continue
                
                parent_hash = parent_result.stdout.strip()
                modified_files = self._get_modified_files(commit_hash)
                
                if not modified_files:
                    continue
                
                bug_count += 1
                
                # Generate diff patch following Defects4J structure
                patch_result = subprocess.run(
                    ['git', 'diff', parent_hash, commit_hash, '--', '*.java'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                has_patch = False
                if patch_result.returncode == 0 and patch_result.stdout.strip():
                    patch_file = patches_dir / f"{bug_count}.src.patch"
                    patch_file.write_text(patch_result.stdout, encoding='utf-8', errors='replace')
                    has_patch = True
                
                # Extract modified files info
                files_info = []
                for file_path in modified_files:
                    buggy_content = self._get_file_at_commit(file_path, parent_hash)
                    fixed_content = self._get_file_at_commit(file_path, commit_hash)
                    
                    if buggy_content and fixed_content:
                        files_info.append({
                            "path": file_path,
                            "buggy_size": len(buggy_content),
                            "fixed_size": len(fixed_content)
                        })
                
                # ADD TO CSV IF: patch exists OR files info available
                if not (has_patch or files_info):
                    continue
                
                bugs_data.append({
                    "bug_id": bug_count,
                    "revision_id_buggy": parent_hash[:8],
                    "revision_id_fixed": commit_hash[:8],
                    "report_id": issue_id or "NA",
                    "commit_message": commit_subject,
                    "author_name": author_name,
                    "commit_date": commit_date,
                    "files_modified": len(files_info),
                    "modified_files": files_info,
                    "has_patch": has_patch
                })
                
                if bug_count % 10 == 0:
                    logger.info(f"Processed {bug_count} bugs...")
            
            logger.info(f"✅ Found {len(bugs_data)} bug-fixing commits")
            
            if not bugs_data:
                return {"error": "No bug-fixing commits found"}
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {"error": str(e)}
        
        # Generate active-bugs.csv (EXACT Defects4J format)
        csv_file = project_dir / "active-bugs.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['bug.id', 'revision.id.buggy', 'revision.id.fixed', 
                           'report.id'])
            for bug in bugs_data:
                writer.writerow([
                    bug['bug_id'],
                    bug['revision_id_buggy'],
                    bug['revision_id_fixed'],
                    bug['report_id']
                ])
        
        # Generate metadata JSON
        json_file = project_dir / "defects4j_metadata.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'Defects4J',
                'description': 'Real Defects4J dataset following official structure from https://github.com/rjust/defects4j',
                'project_id': self.project_name,
                'project_name': self.project_name,
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_bugs': len(bugs_data),
                'bugs': bugs_data
            }, f, indent=2, ensure_ascii=False)
        
        # Generate README
        readme = dataset_dir / "README.md"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"""# Defects4J Dataset - {self.project_name}

## Official Defects4J Structure

This dataset follows the **EXACT** structure from https://github.com/rjust/defects4j

### Structure:
```
defects4j_dataset_{self.timestamp}/
└── {self.project_name}/
    ├── active-bugs.csv          # Bug ID to commit hash mapping
    ├── patches/                 # Source code patches
    │   ├── 1.src.patch
    │   ├── 2.src.patch
    │   └── ...
    └── defects4j_metadata.json  # Full bug metadata
```

### active-bugs.csv Format:
```
bug.id,revision.id.buggy,revision.id.fixed,report.id,report.url
1,<buggy_commit>,<fixed_commit>,<issue_id>,<issue_url>
```

### Version IDs:
- Buggy version: `<id>b` (e.g., "1b", "2b")
- Fixed version: `<id>f` (e.g., "1f", "2f")

### To checkout a bug:
```bash
# Checkout buggy version
defects4j checkout -p {self.project_name} -v 1b -w /path/to/work_dir

# Checkout fixed version
defects4j checkout -p {self.project_name} -v 1f -w /path/to/work_dir
```

## Statistics
- **Total bugs**: {len(bugs_data)}
- **Project**: {self.project_name}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## References
- Official Defects4J: https://github.com/rjust/defects4j
- Paper: "Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java Programs" (ISSTA 2014)
""")
        
        logger.info(f"✅ SUCCESS: {len(bugs_data)} bugs -> {dataset_dir}")
        logger.info(f"📁 Structure: {self.project_name}/active-bugs.csv + patches/")
        
        return {
            "status": "success",
            "total_bugs": len(bugs_data),
            "output_dir": str(dataset_dir),
            "project_dir": str(project_dir),
            "csv_file": str(csv_file),
            "json_file": str(json_file),
            "patches_dir": str(patches_dir)
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python defects4j_generator.py <repo_path> [commit_limit]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    commit_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    
    generator = Defects4JGenerator(repo_path, commit_limit=commit_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        sys.exit(1)
    else:
        print(f"✅ SUCCESS! Generated {result['total_bugs']} bugs")
        print(f"📁 Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
