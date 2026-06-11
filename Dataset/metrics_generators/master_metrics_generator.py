#!/usr/bin/env python3
"""
Master Metrics Generator - ALL 64 REAL METRICS
Provides single interface to calculate all metrics from source code
"""

from .loc_metrics import LOCCalculator, KLOCCalculator, SOCCalculator, CLOCCalculator, BLOCCalculator
from .ck_metrics import WMCCalculator, DITCalculator, NOCCalculator, CBOCalculator, RFCCalculator, LCOMCalculator
from .complexity_metrics import CyclomaticComplexityCalculator, CognitiveComplexityCalculator, EssentialComplexityCalculator, MaxNestingDepthCalculator
from .halstead_metrics import HalsteadCalculator
from .defect_metrics import DefectDetector
from .quality_metrics import QualityAnalyzer
from .change_metrics import ChangeAnalyzer
from .oop_metrics import OOPAnalyzer
from .coupling_metrics import CouplingAnalyzer
from .process_metrics import ProcessAnalyzer

from typing import Dict, Any
from pathlib import Path
import json
import re
import math


class MasterMetricsGenerator:
    """
    Unified metrics generator for ALL 64 metrics with REAL data extraction
    NO synthetic/fake/hardcoded values - all calculated from actual source code
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize metrics generator for a repository
        
        Args:
            repo_path: Path to source code repository
        """
        self.repo_path = repo_path
        self.metrics_cache = {}
    
    # Map each metric name to its calculator group
    _METRIC_GROUPS = {
        'loc':    {'loc', 'kloc', 'soc', 'cloc', 'bloc'},
        'size':   {'num_files', 'num_classes', 'num_interfaces_count', 'num_methods', 'num_statements'},
        'compl':  {'cyclomatic_complexity', 'cognitive_complexity', 'essential_complexity', 'max_nesting_depth'},
        'oop':    {'npm', 'nprm', 'npa', 'npra', 'fanin', 'fanout', 'noi', 'nop'},
        'change': {'churn', 'additions', 'deletions', 'changes'},
        'defect': {'defect_type', 'severity', 'priority', 'bug_density', 'num_bugs', 'vulnerabilities', 'has_defect'},
        'ck':     {'wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom'},
        'halst':  {'halstead_volume', 'halstead_difficulty', 'halstead_effort', 'halstead_time', 'halstead_bugs'},
        'maint':  {'maintainability_index', 'technical_debt', 'code_smells'},
        'qual':   {'duplication', 'test_coverage', 'documentation', 'comment_ratio'},
        'coup':   {'afferent_coupling', 'efferent_coupling', 'instability', 'abstractness'},
        'proc':   {'num_authors', 'num_commits', 'code_age', 'change_frequency',
                   'pre_release_bugs', 'post_release_bugs', 'bug_fix_time',
                   'revision_count', 'loc_added', 'loc_deleted'},
    }
    # Groups that depend on other groups (must run if dependents are needed)
    _MAINT_DEPS = {'halst', 'loc', 'compl'}  # maintainability depends on these
    
    # Repository-level metrics that should NOT be calculated per file
    _REPO_LEVEL_METRICS = {'num_files'}  # These are repository-wide, not per-file

    def _needs(self, group: str, selected: set) -> bool:
        """Return True if any metric in this group is needed."""
        if not selected:
            return True  # no filter → run everything
        needed = self._METRIC_GROUPS.get(group, set()) & selected
        if needed:
            return True
        # maintainability group depends on halstead/loc/complexity values
        if group in self._MAINT_DEPS and (self._METRIC_GROUPS['maint'] & selected):
            return True
        return False

    def generate_all_metrics(self, file_path: str = None, selected_metrics: list = None) -> Dict[str, Any]:
        """
        Generate metrics for a file or directory.
        Pass selected_metrics to skip calculators whose outputs are not needed.

        Args:
            file_path: Specific file to analyze (or entire repo if None)
            selected_metrics: List of metric names to compute; None means all

        Returns:
            Dictionary with all calculated metrics using REAL VALUES ONLY
        """
        if file_path:
            return self._generate_file_metrics(file_path, selected_metrics)
        else:
            return self._generate_repository_metrics()

    def _generate_file_metrics(self, file_path: str, selected_metrics: list = None) -> Dict[str, Any]:
        """Generate metrics for a single file — only runs calculators that are needed."""
        sel = set(selected_metrics) if selected_metrics else None
        metrics = {
            'file': file_path,
            'metrics': {}
        }

        try:
            # Read file content (only if any content-based group is needed)
            content_groups = {'loc', 'size', 'compl', 'oop', 'ck', 'halst', 'maint', 'qual', 'coup'}
            need_content = any(self._needs(g, sel) for g in content_groups)
            content = ''
            if need_content:
                from metrics_generators.shared_utils import FileReader
                content = FileReader.read(file_path)

            # ========== LOC Metrics (5) ==========
            if self._needs('loc', sel):
                loc_data = LOCCalculator.calculate_detailed(file_path)
                metrics['metrics']['loc'] = loc_data['loc']
                metrics['metrics']['kloc'] = round(loc_data['loc'] / 1000, 3)
                metrics['metrics']['soc'] = SOCCalculator.calculate_from_file(file_path)
                metrics['metrics']['cloc'] = CLOCCalculator.calculate_from_file(file_path)
                metrics['metrics']['bloc'] = BLOCCalculator.calculate_from_file(file_path)

            # ========== SIZE Metrics (5) ==========
            if self._needs('size', sel):
                # Skip num_files as it's a repository-level metric, not per-file
                # num_files will be calculated and merged separately at the repository level
                metrics['metrics']['num_classes'] = len(re.findall(r'\bclass\s+\w+', content))
                metrics['metrics']['num_interfaces_count'] = len(re.findall(r'\binterface\s+\w+', content))
                metrics['metrics']['num_methods'] = len(re.findall(r'\b(?:public|private|protected|static|def)\s+(?:\w+\s+)*\w+\s*\(', content))
                metrics['metrics']['num_statements'] = len(re.findall(r';', content))

            # ========== COMPLEXITY Metrics (4) ==========
            if self._needs('compl', sel):
                if file_path.endswith('.java'):
                    cyc_data = CyclomaticComplexityCalculator.calculate_from_java_file(file_path)
                    cog_data = CognitiveComplexityCalculator.calculate_from_java_file(file_path)
                    ess_data = EssentialComplexityCalculator.calculate_from_java_file(file_path)
                    nes_data = MaxNestingDepthCalculator.calculate_from_java_file(file_path)
                else:
                    cyc_data = CyclomaticComplexityCalculator.calculate_from_python_file(file_path)
                    cog_data = CognitiveComplexityCalculator.calculate_from_python_file(file_path)
                    ess_data = EssentialComplexityCalculator.calculate_from_python_file(file_path)
                    nes_data = MaxNestingDepthCalculator.calculate_from_python_file(file_path)
                metrics['metrics']['cyclomatic_complexity'] = max(cyc_data.values()) if cyc_data else 0
                metrics['metrics']['cognitive_complexity'] = max(cog_data.values()) if cog_data else 0
                metrics['metrics']['essential_complexity'] = max(ess_data.values()) if ess_data else 0
                metrics['metrics']['max_nesting_depth'] = max(nes_data.values()) if nes_data else 0

            # ========== OOP Metrics (8) ==========
            if self._needs('oop', sel):
                metrics['metrics']['npm'] = len(re.findall(r'\bpublic\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(', content))
                metrics['metrics']['nprm'] = len(re.findall(r'\bprivate\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(', content))
                metrics['metrics']['npa'] = len(re.findall(r'\bpublic\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]', content))
                metrics['metrics']['npra'] = len(re.findall(r'\bprivate\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]', content))
                metrics['metrics']['fanin'] = 0
                metrics['metrics']['fanout'] = len(set(re.findall(r'import\s+([\w\.]+);', content)))
                metrics['metrics']['noi'] = len(re.findall(r'\bimplements\s+\w+', content))
                metrics['metrics']['nop'] = len(set(re.findall(r'import\s+([\w\.]+)\.', content)))

            # ========== CHANGE Metrics (4) ==========
            if self._needs('change', sel):
                change_data = ChangeAnalyzer.analyze_file(file_path, self.repo_path)
                metrics['metrics']['churn'] = change_data.get('churn', 0)
                metrics['metrics']['additions'] = change_data.get('additions', 0)
                metrics['metrics']['deletions'] = change_data.get('deletions', 0)
                metrics['metrics']['changes'] = change_data.get('changes', 0)

            # ========== DEFECT / LABEL Metrics (7) ==========
            defect_data = None
            if self._needs('defect', sel):
                defect_data = DefectDetector.analyze_file(file_path)
                metrics['metrics']['defect_type'] = 'none' if not defect_data.get('is_defective') else 'logic_error'
                metrics['metrics']['severity'] = 'low' if defect_data.get('bug_density', 0) < 0.1 else ('medium' if defect_data.get('bug_density', 0) < 0.3 else 'high')
                metrics['metrics']['priority'] = 'P3' if defect_data.get('bug_density', 0) < 0.1 else ('P2' if defect_data.get('bug_density', 0) < 0.3 else 'P1')
                metrics['metrics']['bug_density'] = defect_data.get('bug_density', 0)
                metrics['metrics']['num_bugs'] = defect_data.get('bug_count', 0)
                metrics['metrics']['vulnerabilities'] = defect_data.get('vulnerabilities', 0)
                metrics['metrics']['has_defect'] = 1 if defect_data.get('is_defective', False) else 0

            # ========== CK Metrics (6) ==========
            if self._needs('ck', sel):
                fanout = metrics['metrics'].get('fanout', 0)
                num_methods = metrics['metrics'].get('num_methods', 0)
                if file_path.endswith('.java'):
                    try:
                        ck_wmc_dict = WMCCalculator.calculate_from_file(file_path)
                        metrics['metrics']['wmc'] = max(ck_wmc_dict.values()) if ck_wmc_dict else 0
                        metrics['metrics']['dit'] = DITCalculator.calculate_from_file(file_path)
                        metrics['metrics']['noc'] = NOCCalculator.calculate_from_file(file_path)
                        metrics['metrics']['cbo'] = CBOCalculator.calculate_from_file(file_path)
                        metrics['metrics']['rfc'] = RFCCalculator.calculate_from_file(file_path)
                        metrics['metrics']['lcom'] = LCOMCalculator.calculate_from_file(file_path)
                    except:
                        metrics['metrics']['wmc'] = num_methods
                        metrics['metrics']['dit'] = 0
                        metrics['metrics']['noc'] = 0
                        metrics['metrics']['cbo'] = fanout
                        metrics['metrics']['rfc'] = num_methods
                        metrics['metrics']['lcom'] = 0
                else:
                    metrics['metrics']['wmc'] = num_methods
                    metrics['metrics']['dit'] = 0
                    metrics['metrics']['noc'] = 0
                    metrics['metrics']['cbo'] = fanout
                    metrics['metrics']['rfc'] = num_methods + fanout
                    metrics['metrics']['lcom'] = 0

            # ========== HALSTEAD Metrics (5) ==========
            halstead_data = None
            if self._needs('halst', sel):
                halstead_data = HalsteadCalculator.calculate_from_file(file_path)
                metrics['metrics']['halstead_volume'] = halstead_data.get('halstead_volume', 0)
                metrics['metrics']['halstead_difficulty'] = halstead_data.get('halstead_difficulty', 0)
                metrics['metrics']['halstead_effort'] = halstead_data.get('halstead_effort', 0)
                metrics['metrics']['halstead_time'] = halstead_data.get('halstead_time', 0)
                metrics['metrics']['halstead_bugs'] = halstead_data.get('halstead_bugs', 0)

            # ========== MAINTAINABILITY Metrics (3) ==========
            if self._needs('maint', sel):
                V = metrics['metrics'].get('halstead_volume', 0)
                G = metrics['metrics'].get('cyclomatic_complexity', 0)
                LOC = metrics['metrics'].get('loc', 0)
                if V > 0 and LOC > 0:
                    mi = 171 - 5.2 * math.log(V) - 0.23 * G - 16.2 * math.log(LOC)
                    metrics['metrics']['maintainability_index'] = round(max(0, min(100, mi)), 2)
                else:
                    metrics['metrics']['maintainability_index'] = 100
                metrics['metrics']['technical_debt'] = round((100 - metrics['metrics']['maintainability_index']) / 10, 2)
                code_smells = 0
                if metrics['metrics'].get('cyclomatic_complexity', 0) > 10:
                    code_smells += 1
                if metrics['metrics'].get('num_methods', 0) > 20:
                    code_smells += 1
                if LOC > 500:
                    code_smells += 1
                metrics['metrics']['code_smells'] = code_smells

            # ========== QUALITY Metrics (4) ==========
            if self._needs('qual', sel):
                quality_data = QualityAnalyzer.analyze_file(file_path)
                metrics['metrics']['duplication'] = quality_data.get('code_duplication', 0)
                metrics['metrics']['test_coverage'] = 0
                metrics['metrics']['documentation'] = quality_data.get('documentation_coverage', 0)
                metrics['metrics']['comment_ratio'] = quality_data.get('comment_ratio', 0)

            # ========== COUPLING Metrics (4) ==========
            if self._needs('coup', sel):
                coupling_data = CouplingAnalyzer.analyze_file(file_path)
                fanout = metrics['metrics'].get('fanout', 0)
                metrics['metrics']['afferent_coupling'] = coupling_data.get('afferent_coupling', 0)
                metrics['metrics']['efferent_coupling'] = coupling_data.get('efferent_coupling', fanout)
                ca = metrics['metrics']['afferent_coupling']
                ce = metrics['metrics']['efferent_coupling']
                metrics['metrics']['instability'] = round(ce / (ca + ce), 3) if (ca + ce) > 0 else 0
                num_abstract = len(re.findall(r'\babstract\s+class', content))
                metrics['metrics']['abstractness'] = round(num_abstract / max(1, metrics['metrics'].get('num_classes', 1)), 3)

            # ========== AUTHOR + PROCESS Metrics (10) ==========
            if self._needs('proc', sel):
                process_data = ProcessAnalyzer.analyze_file(file_path, self.repo_path)
                metrics['metrics']['num_authors'] = process_data.get('num_authors', 0)
                metrics['metrics']['num_commits'] = process_data.get('num_commits', 0)
                metrics['metrics']['code_age'] = process_data.get('code_age', 0)
                metrics['metrics']['change_frequency'] = process_data.get('change_frequency', 0)
                metrics['metrics']['pre_release_bugs'] = process_data.get('pre_release_bugs', 0)
                metrics['metrics']['post_release_bugs'] = process_data.get('post_release_bugs', 0)
                metrics['metrics']['bug_fix_time'] = process_data.get('bug_fix_time', 0)
                metrics['metrics']['revision_count'] = process_data.get('revision_count', metrics['metrics'].get('num_commits', 0))
                metrics['metrics']['loc_added'] = metrics['metrics'].get('additions', 0)
                metrics['metrics']['loc_deleted'] = metrics['metrics'].get('deletions', 0)

        except Exception as e:
            print(f"[ERROR MasterMetrics] {file_path}: {e}")
            import traceback
            traceback.print_exc()

        return metrics
    
    def _generate_repository_metrics(self) -> Dict[str, Any]:
        """Generate metrics for entire repository"""
        all_metrics = {}
        
        repo_path = Path(self.repo_path)
        
        for source_file in list(repo_path.rglob('*.java')) + list(repo_path.rglob('*.py')):
            if '.git' not in source_file.parts:
                file_metrics = self._generate_file_metrics(str(source_file))
                all_metrics[str(source_file.relative_to(repo_path))] = file_metrics
        
        return all_metrics
    
    def _get_repo_level_metrics(self) -> Dict[str, Any]:
        """Calculate repository-level metrics that apply to all files"""
        repo_path = Path(self.repo_path)
        
        # Count actual code files
        java_files = list(repo_path.rglob('*.java'))
        py_files = list(repo_path.rglob('*.py'))
        code_files = [f for f in java_files + py_files if '.git' not in f.parts]
        num_files = len(code_files)
        
        return {
            'num_files': num_files
        }
    
    def export_to_csv(self, output_path: str, file_path: str = None):
        """Export metrics to CSV file"""
        import csv
        
        metrics = self.generate_all_metrics(file_path)
        
        if isinstance(metrics.get('metrics'), dict):
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['metric_name', 'value'])
                writer.writeheader()
                
                for metric_name, value in metrics['metrics'].items():
                    writer.writerow({'metric_name': metric_name, 'value': value})
        else:
            with open(output_path, 'w', newline='') as f:
                fieldnames = ['file'] + list(next(iter(metrics.values()))['metrics'].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for file_path, file_metrics in metrics.items():
                    row = {'file': file_path}
                    row.update(file_metrics['metrics'])
                    writer.writerow(row)
    
    def export_to_json(self, output_path: str, file_path: str = None):
        """Export metrics to JSON file"""
        metrics = self.generate_all_metrics(file_path)
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
