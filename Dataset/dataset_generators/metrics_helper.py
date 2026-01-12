import sys
import os
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from metrics_generators import MasterMetricsGenerator
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("WARNING: metrics_generators not available. Will use simple fallback metrics.")

# Import simple metrics as fallback
try:
    from .simple_metrics import SimpleMetricsExtractor
    SIMPLE_METRICS_AVAILABLE = True
except ImportError:
    SIMPLE_METRICS_AVAILABLE = False
    print("WARNING: simple_metrics not available either")


class MetricsHelper:
    """Helper class for all dataset generators to use real metrics"""
    
    def __init__(self, repo_path: str):
        """
        Initialize metrics helper for a repository
        
        Args:
            repo_path: Path to source code repository
        """
        if not METRICS_AVAILABLE:
            raise ImportError("metrics_generators package not found")
        
        self.repo_path = repo_path
        self.generator = MasterMetricsGenerator(repo_path)
    
    def get_all_metrics(self, file_path: str = None) -> Dict[str, Any]:
        """
        Get all 64 metrics for a file or repository
        
        Args:
            file_path: Specific file path (absolute or relative to repo) or None for entire repo
            
        Returns:
            Dictionary with all calculated metrics
        """
        try:
            # Full path to file
            if file_path:
                # Handle both absolute and relative paths
                if os.path.isabs(file_path):
                    # Already absolute path
                    actual_path = file_path
                else:
                    # Relative path - join with repo_path
                    actual_path = str(Path(self.repo_path) / file_path)
                
                # Check if file exists
                if not os.path.isfile(actual_path):
                    print(f"[WARNING MetricsHelper] File not found: {actual_path}")
                    return {'metrics': {}}
                
                result = self.generator.generate_all_metrics(actual_path)
                # Debug logging
                if result and 'metrics' in result:
                    metric_count = len(result['metrics'])
                    if metric_count > 0:
                        print(f"[DEBUG MetricsHelper] {os.path.basename(actual_path)}: {metric_count} metrics")
                    else:
                        print(f"[WARNING MetricsHelper] {os.path.basename(actual_path)}: 0 metrics returned!")
                return result
            else:
                return self.generator.generate_all_metrics()
        except Exception as e:
            print(f"[ERROR MetricsHelper] Exception for {file_path}: {type(e).__name__}: {str(e)[:100]}")
            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()[:500]}")
            return {'metrics': {}}
    
    def get_loc_metrics(self, file_path: str) -> Dict[str, int]:
        """Get Lines of Code metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            return {
                'loc': metrics.get('metrics', {}).get('loc', 0),
                'kloc': metrics.get('metrics', {}).get('kloc', 0),
                'soc': metrics.get('metrics', {}).get('soc', 0),
                'cloc': metrics.get('metrics', {}).get('cloc', 0),
                'bloc': metrics.get('metrics', {}).get('bloc', 0),
            }
        except:
            return {'loc': 0, 'kloc': 0, 'soc': 0, 'cloc': 0, 'bloc': 0}
    
    def get_ck_metrics(self, file_path: str) -> Dict[str, float]:
        """Get Chidamber-Kemerer metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            m = metrics.get('metrics', {})
            return {
                'wmc': m.get('wmc', 0),
                'dit': m.get('dit', 0),
                'noc': m.get('noc', 0),
                'cbo': m.get('cbo', 0),
                'rfc': m.get('rfc', 0),
                'lcom': m.get('lcom', 0),
            }
        except:
            return {'wmc': 0, 'dit': 0, 'noc': 0, 'cbo': 0, 'rfc': 0, 'lcom': 0}
    
    def get_complexity_metrics(self, file_path: str) -> Dict[str, float]:
        """Get code complexity metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            m = metrics.get('metrics', {})
            return {
                'cyclomatic_complexity': m.get('cyclomatic_complexity', 0),
                'cognitive_complexity': m.get('cognitive_complexity', 0),
                'essential_complexity': m.get('essential_complexity', 0),
                'max_nesting_depth': m.get('max_nesting_depth', 0),
            }
        except:
            return {'cyclomatic_complexity': 0, 'cognitive_complexity': 0, 
                    'essential_complexity': 0, 'max_nesting_depth': 0}
    
    def get_halstead_metrics(self, file_path: str) -> Dict[str, float]:
        """Get Halstead metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            m = metrics.get('metrics', {})
            return {
                'halstead_volume': m.get('halstead_volume', 0),
                'halstead_difficulty': m.get('halstead_difficulty', 0),
                'halstead_effort': m.get('halstead_effort', 0),
                'halstead_time': m.get('halstead_time', 0),
                'halstead_bugs': m.get('halstead_bugs', 0),
            }
        except:
            return {'halstead_volume': 0, 'halstead_difficulty': 0, 
                    'halstead_effort': 0, 'halstead_time': 0, 'halstead_bugs': 0}
    
    def get_defect_metrics(self, file_path: str) -> Dict[str, Any]:
        """Get defect prediction metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            m = metrics.get('metrics', {})
            return {
                'bug_count': m.get('bug_count', 0),
                'bug_density': m.get('bug_density', 0),
                'vulnerabilities': m.get('vulnerabilities', 0),
                'is_defective': m.get('is_defective', False),
            }
        except:
            return {'bug_count': 0, 'bug_density': 0, 'vulnerabilities': 0, 'is_defective': False}
    
    def get_quality_metrics(self, file_path: str) -> Dict[str, float]:
        """Get code quality metrics"""
        try:
            metrics = self.get_all_metrics(file_path)
            m = metrics.get('metrics', {})
            return {
                'code_duplication': m.get('code_duplication', 0),
                'comment_ratio': m.get('comment_ratio', 0),
                'documentation_coverage': m.get('documentation_coverage', 0),
            }
        except:
            return {'code_duplication': 0, 'comment_ratio': 0, 'documentation_coverage': 0}


def get_metrics_helper(repo_path: str) -> MetricsHelper:
    """Factory function to create metrics helper instance"""
    return MetricsHelper(repo_path)
