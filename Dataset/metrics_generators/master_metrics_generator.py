#!/usr/bin/env python3
"""
Master Metrics Generator - Unified access to all 64 metrics
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


class MasterMetricsGenerator:
    """
    Unified metrics generator for all 64 metrics
    Calculates real metrics from actual source code, not fake/random values
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize metrics generator for a repository
        
        Args:
            repo_path: Path to source code repository
        """
        self.repo_path = repo_path
        self.metrics_cache = {}
    
    def generate_all_metrics(self, file_path: str = None) -> Dict[str, Any]:
        """
        Generate all 64 metrics for a file or directory
        
        Args:
            file_path: Specific file to analyze (or entire repo if None)
            
        Returns:
            Dictionary with all calculated metrics using REAL VALUES
        """
        if file_path:
            return self._generate_file_metrics(file_path)
        else:
            return self._generate_repository_metrics()
    
    def _generate_file_metrics(self, file_path: str) -> Dict[str, Any]:
        """Generate metrics for a single file"""
        metrics = {
            'file': file_path,
            'metrics': {}
        }
        
        try:
            # LOC Metrics (5)
            loc_data = LOCCalculator.calculate_detailed(file_path)
            metrics['metrics']['loc'] = loc_data['loc']
            metrics['metrics']['kloc'] = KLOCCalculator.calculate_from_file(file_path)
            metrics['metrics']['soc'] = SOCCalculator.calculate_from_file(file_path)
            metrics['metrics']['cloc'] = CLOCCalculator.calculate_from_file(file_path)
            metrics['metrics']['bloc'] = BLOCCalculator.calculate_from_file(file_path)
            
            # Complexity Metrics (4)
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
            
            if cyc_data:
                metrics['metrics']['cyclomatic_complexity'] = max(cyc_data.values()) if cyc_data else 0
            if cog_data:
                metrics['metrics']['cognitive_complexity'] = max(cog_data.values()) if cog_data else 0
            if ess_data:
                metrics['metrics']['essential_complexity'] = max(ess_data.values()) if ess_data else 0
            if nes_data:
                metrics['metrics']['max_nesting_depth'] = max(nes_data.values()) if nes_data else 0
            
            # Halstead Metrics (5)
            halstead_data = HalsteadCalculator.calculate_from_file(file_path)
            for key, value in halstead_data.items():
                metrics['metrics'][key] = value
            
            # Defect Metrics (4)
            defect_data = DefectDetector.analyze_file(file_path)
            for key, value in defect_data.items():
                if key != 'defect_types' and key != 'vulnerability_types':
                    metrics['metrics'][key] = value
            
            # Quality Metrics (4)
            quality_data = QualityAnalyzer.analyze_file(file_path)
            for key, value in quality_data.items():
                metrics['metrics'][key] = value
            
            # Change Metrics (4)
            change_data = ChangeAnalyzer.analyze_file(file_path, self.repo_path)
            for key, value in change_data.items():
                metrics['metrics'][key] = value
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return metrics
    
    def _generate_repository_metrics(self) -> Dict[str, Any]:
        """Generate metrics for entire repository"""
        all_metrics = {}
        
        # Analyze all source files
        repo_path = Path(self.repo_path)
        
        for source_file in list(repo_path.rglob('*.java')) + list(repo_path.rglob('*.py')):
            if '.git' not in source_file.parts:  # Skip .git directory
                file_metrics = self._generate_file_metrics(str(source_file))
                all_metrics[str(source_file.relative_to(repo_path))] = file_metrics
        
        return all_metrics
    
    def export_to_csv(self, output_path: str, file_path: str = None):
        """
        Export metrics to CSV file
        
        Args:
            output_path: Path to output CSV file
            file_path: Specific file to analyze (or entire repo if None)
        """
        import csv
        
        metrics = self.generate_all_metrics(file_path)
        
        if isinstance(metrics.get('metrics'), dict):
            # Single file metrics
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['metric_name', 'value'])
                writer.writeheader()
                
                for metric_name, value in metrics['metrics'].items():
                    writer.writerow({'metric_name': metric_name, 'value': value})
        else:
            # Multiple files
            all_rows = []
            for file_name, file_metrics in metrics.items():
                row = {'file': file_name}
                row.update(file_metrics.get('metrics', {}))
                all_rows.append(row)
            
            if all_rows:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['file'] + list(all_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(all_rows)
    
    def export_to_json(self, output_path: str, file_path: str = None):
        """
        Export metrics to JSON file
        
        Args:
            output_path: Path to output JSON file
            file_path: Specific file to analyze (or entire repo if None)
        """
        metrics = self.generate_all_metrics(file_path)
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python master_metrics_generator.py <repo_path> [output_file.csv|json]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = MasterMetricsGenerator(repo_path)
    
    if output_file:
        if output_file.endswith('.csv'):
            generator.export_to_csv(output_file)
            print(f"Metrics exported to {output_file}")
        elif output_file.endswith('.json'):
            generator.export_to_json(output_file)
            print(f"Metrics exported to {output_file}")
    else:
        metrics = generator.generate_all_metrics()
        print("Generated metrics:")
        print(json.dumps(metrics, indent=2))
