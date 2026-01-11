import os
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManySStuBs4JGenerator:
    
    def __init__(self, repo_path: str, output_dir: str = None, commit_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.commit_limit = commit_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a Git repository: {repo_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ManySStuBs4J generator for {self.repo_path}")
    
    def generate(self) -> Dict:
        """Generate REAL ManySStuBs4J dataset from method-level changes"""
        logger.info("Generating REAL ManySStuBs4J dataset from method-level Git changes...")
        
        dataset = []
        dataset_dir = self.output_dir / f"manystubs4j_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)
        
        project_name = self.repo_path.name
        
        try:
            # Get ALL commits - FIX Unicode error
            result = subprocess.run(
                ['git', 'log', '--all', '--format=%H|%s', '--no-merges'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git log failed: {result.stderr}")
                return {"error": "Git log failed"}
            
            commits = [c for c in result.stdout.strip().split('\n') if c]
            logger.info(f"Found {len(commits)} commits")
            
            if not commits:
                logger.warning("No commits found")
                return {"error": "No commits found"}
            
            total_methods = 0
            for idx, commit_line in enumerate(commits[:self.commit_limit] if self.commit_limit else commits):
                parts = commit_line.split('|', 1)
                if len(parts) < 2:
                    continue
                
                commit_hash = parts[0]
                commit_msg = parts[1]
                
                # Get diff for Java files only with context - FIX Unicode error
                diff_result = subprocess.run(
                    ['git', 'show', '--unified=5', '--format=', commit_hash, '--', '*.java'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30
                )
                
                if diff_result.returncode != 0 or not diff_result.stdout.strip():
                    continue
                
                diff_text = diff_result.stdout
                
                # Extract method changes using regex patterns
                # Pattern 1: Method declaration in diff context
                method_pattern = r'@@.*?@@\s*.*?(public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
                method_changes = re.findall(method_pattern, diff_text, re.MULTILINE)
                
                # Pattern 2: Direct method changes
                direct_method_pattern = r'[+-]\s*(public|private|protected|static)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
                direct_changes = re.findall(direct_method_pattern, diff_text, re.MULTILINE)
                
                all_methods = method_changes + direct_changes
                
                if not all_methods:
                    continue
                
                # Count additions and deletions
                additions = len(re.findall(r'^\+[^+]', diff_text, re.MULTILINE))
                deletions = len(re.findall(r'^-[^-]', diff_text, re.MULTILINE))
                
                # Get changed files
                files_result = subprocess.run(
                    ['git', 'show', '--name-only', '--format=', commit_hash, '--', '*.java'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                changed_files = [f for f in files_result.stdout.strip().split('\n') if f and f.endswith('.java')]
                
                # Create entry for each method change
                for method_info in all_methods:
                    total_methods += 1
                    
                    issue = {
                        'issue_id': f'METHOD_{project_name}_{total_methods:05d}',
                        'project': project_name,
                        'commit_hash': commit_hash,
                        'commit_message': commit_msg,
                        'method_modifier': method_info[0],
                        'method_name': method_info[1],
                        'files_changed': len(changed_files),
                        'changed_files': changed_files[:5],  # First 5 files
                        'lines_added': additions,
                        'lines_deleted': deletions,
                        'total_changes': additions + deletions,
                        'diff_snippet': diff_text[:1000],  # First 1000 chars
                        'dataset_type': 'manystubs4j_real',
                        'extraction_method': 'method_level_git_analysis'
                    }
                    
                    dataset.append(issue)
                
                if (idx + 1) % 50 == 0:
                    logger.info(f"Processed {idx + 1} commits, found {total_methods} method changes...")
            
            logger.info(f"Extracted {total_methods} method changes from {len(commits)} commits")
            
        except subprocess.TimeoutExpired:
            logger.error("Git command timeout")
            return {"error": "Git command timeout"}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
        
        # Save to JSON
        output_file = dataset_dir / "manystubs4j_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'ManySStuBs4J_Real',
                'description': 'Real method-level changes extracted from Git history',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_method_changes': len(dataset),
                'issues': dataset,
                'extraction_method': 'method_level_git_analysis'
            }, f, indent=2)
        
        logger.info(f"REAL ManySStuBs4J dataset generated: {len(dataset)} method changes -> {dataset_dir}")
        
        return {
            "status": "success",
            "total_method_changes": len(dataset),
            "output_dir": str(dataset_dir),
            "output_file": str(output_file)
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python manystubs4j_generator.py <repo_path> [commit_limit]")
        print("Example: python manystubs4j_generator.py d:/GitIntel/repo 200")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    commit_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    generator = ManySStuBs4JGenerator(repo_path, commit_limit=commit_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_method_changes']} method changes")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
