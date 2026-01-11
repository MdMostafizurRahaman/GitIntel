import os
import json
import csv
import sys
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

try:
    from pydriller import Repository
    PYDRILLER_AVAILABLE = True
except ImportError:
    PYDRILLER_AVAILABLE = False

# Import metrics helper (NO duplicate code)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from metrics_helper import MetricsHelper
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfessionalBugsJarGenerator:
    """Professional Bugs.jar using PyDriller + 64 real metrics"""
    
    def __init__(self, repo_path: str, output_dir: str = None, commit_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.commit_limit = commit_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a Git repository: {repo_path}")
        
        if not PYDRILLER_AVAILABLE:
            raise ImportError("PyDriller required. Install: pip install pydriller")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics helper for 64 real metrics
        self.metrics_helper = None
        if METRICS_AVAILABLE:
            try:
                self.metrics_helper = MetricsHelper(str(self.repo_path))
            except Exception as e:
                logger.warning(f"Metrics not available: {e}")
        
        logger.info(f"Initialized Professional Bugs.jar generator with {'64 metrics' if self.metrics_helper else 'PyDriller metrics only'}")
    
    def _classify_commit(self, commit) -> str:
        """Classify commit type"""
        msg_lower = commit.msg.lower()
        
        if any(k in msg_lower for k in ['fix', 'bug', 'error', 'issue']):
            return 'BUG_FIX'
        elif any(k in msg_lower for k in ['feat', 'add', 'new', 'implement']):
            return 'FEATURE'
        elif any(k in msg_lower for k in ['refactor', 'clean', 'improve']):
            return 'REFACTOR'
        elif any(k in msg_lower for k in ['test', 'spec']):
            return 'TEST'
        elif any(k in msg_lower for k in ['doc', 'comment', 'readme']):
            return 'DOCUMENTATION'
        else:
            return 'OTHER'
    
    def generate(self) -> Dict:
        """Generate professional Bugs.jar dataset"""
        logger.info("Generating PROFESSIONAL Bugs.jar dataset using PyDriller...")
        
        dataset = []
        dataset_dir = self.output_dir / f"professional_bugsjar_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)
        
        project_name = self.repo_path.name
        
        try:
            commit_count = 0
            
            for commit in Repository(str(self.repo_path)).traverse_commits():
                if self.commit_limit and commit_count >= self.commit_limit:
                    break
                
                commit_count += 1
                
                # Get Java files modified
                java_files = [m for m in commit.modified_files if m.filename.endswith('.java')]
                
                if not java_files:
                    continue
                
                # Professional metrics from PyDriller
                total_complexity_before = sum(m.complexity_before if hasattr(m, 'complexity_before') else 0 
                                             for m in java_files)
                total_complexity_after = sum(m.complexity if hasattr(m, 'complexity') else 0 
                                            for m in java_files)
                
                total_nloc_before = sum(m.nloc_before if hasattr(m, 'nloc_before') else 0 
                                       for m in java_files)
                total_nloc_after = sum(m.nloc if hasattr(m, 'nloc') else 0 
                                      for m in java_files)
                
                # Get 64 real metrics for first modified file (if available)
                file_metrics = {}
                if self.metrics_helper and java_files:
                    try:
                        first_java_file = java_files[0].filename
                        metrics_data = self.metrics_helper.get_all_metrics(first_java_file)
                        file_metrics = metrics_data.get('metrics', {})
                    except:
                        pass
                
                record = {
                    "commit_id": commit_count,
                    "commit_hash": commit.hash,
                    "author_name": commit.author.name,
                    "author_email": commit.author.email,
                    "commit_date": commit.committer_date.isoformat(),
                    "commit_message": commit.msg,
                    
                    # Classification
                    "commit_type": self._classify_commit(commit),
                    "is_merge": commit.merge,
                    
                    # File changes (accurate)
                    "files_changed": len(commit.modified_files),
                    "java_files_changed": len(java_files),
                    
                    # Line changes (accurate from PyDriller)
                    "lines_added": sum(m.added_lines for m in java_files),
                    "lines_deleted": sum(m.deleted_lines for m in java_files),
                    
                    # NLOC changes (professional metric)
                    "nloc_before": total_nloc_before,
                    "nloc_after": total_nloc_after,
                    "nloc_delta": total_nloc_after - total_nloc_before,
                    
                    # 64 REAL METRICS from MasterMetricsGenerator (NO fake data)
                    **file_metrics,
                    
                    # Complexity changes (professional metric)
                    "complexity_before": total_complexity_before,
                    "complexity_after": total_complexity_after,
                    "complexity_delta": total_complexity_after - total_complexity_before,
                    
                    # Method-level changes
                    "methods_changed": sum(len(m.changed_methods) if hasattr(m, 'changed_methods') else 0 
                                          for m in java_files),
                    
                    # Files list
                    "java_files": [m.filename for m in java_files],
                    
                    # Quality indicators
                    "has_test_changes": any(m.filename.lower().endswith('test.java') 
                                           for m in commit.modified_files),
                    
                    # Tool info
                    "extraction_tool": "PyDriller",
                    "quality": "professional_grade"
                }
                
                dataset.append(record)
                
                if commit_count % 100 == 0:
                    logger.info(f"Processed {commit_count} commits...")
            
            logger.info(f"Analyzed {len(dataset)} commits with PyDriller")
            
            if not dataset:
                return {"error": "No commits with Java changes found"}
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}
        
        # Save JSON
        output_file = dataset_dir / "professional_bugsjar_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'BugsJar_Professional',
                'description': 'Professional Bugs.jar using PyDriller for accurate analysis',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_commits': len(dataset),
                'tools_used': ['PyDriller'],
                'data': dataset,
                'extraction_method': 'pydriller_commit_analysis',
                'quality': 'professional_grade'
            }, f, indent=2, ensure_ascii=False)
        
        # Save CSV
        csv_file = dataset_dir / "professional_bugsjar_dataset.csv"
        if dataset:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                # Remove nested lists for CSV
                csv_data = []
                for record in dataset:
                    csv_record = {k: v for k, v in record.items() if k != 'java_files'}
                    csv_record['java_files_list'] = ';'.join(record['java_files'])
                    csv_data.append(csv_record)
                
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
        
        logger.info(f"SUCCESS: Professional Bugs.jar: {len(dataset)} commits -> {dataset_dir}")
        
        return {
            "status": "success",
            "total_commits": len(dataset),
            "output_dir": str(dataset_dir),
            "output_file": str(output_file),
            "csv_file": str(csv_file),
            "quality": "professional_grade"
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python professional_bugsjar_generator.py <repo_path> [commit_limit]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    commit_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    generator = ProfessionalBugsJarGenerator(repo_path, commit_limit=commit_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    else:
        print(f"SUCCESS! Analyzed {result['total_commits']} commits")
        print(f"Quality: {result['quality']}")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
