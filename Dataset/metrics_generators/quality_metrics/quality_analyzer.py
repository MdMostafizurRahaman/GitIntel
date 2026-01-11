#!/usr/bin/env python3
"""
Quality Metrics Calculator
Measures code quality indicators like duplication, documentation, comments
"""

import re
from pathlib import Path
from typing import Dict
from collections import defaultdict


class QualityAnalyzer:
    """Analyze code quality metrics"""
    
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, float]:
        """
        Analyze code quality from a file
        
        Args:
            file_path: Path to source file
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Calculate duplication
            duplication = QualityAnalyzer._calculate_duplication(lines)
            
            # Calculate documentation coverage
            docs = QualityAnalyzer._analyze_documentation(content)
            
            # Calculate comment ratio
            from ..loc_metrics import CLOCCalculator
            cloc = CLOCCalculator.calculate_from_file(file_path)
            
            from ..loc_metrics import LOCCalculator
            loc_details = LOCCalculator.calculate_detailed(file_path)
            loc_total = loc_details.get('loc', 1)
            
            comment_ratio = (cloc / loc_total * 100) if loc_total > 0 else 0
            
            return {
                'code_duplication': round(duplication, 2),
                'comment_ratio': round(comment_ratio, 2),
                'documentation_coverage': round(docs['coverage'], 2),
                'documented_functions': docs['documented'],
                'total_functions': docs['total']
            }
            
        except Exception:
            return QualityAnalyzer._empty_quality()
    
    @staticmethod
    def _calculate_duplication(lines: list) -> float:
        """
        Calculate code duplication percentage
        Returns percentage of duplicate lines
        """
        if not lines:
            return 0.0
        
        # Group lines by length to find potential duplicates
        line_groups = defaultdict(int)
        total_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('#'):
                line_groups[stripped] += 1
                total_lines += 1
        
        if total_lines == 0:
            return 0.0
        
        # Count duplicate lines (lines that appear more than once)
        duplicate_count = sum(count - 1 for count in line_groups.values() if count > 1)
        
        return (duplicate_count / total_lines * 100) if total_lines > 0 else 0.0
    
    @staticmethod
    def _analyze_documentation(content: str) -> Dict:
        """
        Analyze documentation in code
        
        Returns:
            Dictionary with 'coverage', 'documented', 'total'
        """
        # Count javadoc/docstring blocks
        javadoc_pattern = r'/\*\*.*?\*/'
        docstring_pattern = r'""".*?"""'
        
        javadoc_blocks = len(re.findall(javadoc_pattern, content, re.DOTALL))
        docstring_blocks = len(re.findall(docstring_pattern, content, re.DOTALL))
        
        # Count function/method definitions
        method_pattern = r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\('
        methods = len(re.findall(method_pattern, content))
        
        total_documented = javadoc_blocks + docstring_blocks
        
        coverage = (total_documented / max(1, methods) * 100) if methods > 0 else 0
        
        return {
            'coverage': coverage,
            'documented': total_documented,
            'total': methods
        }
    
    @staticmethod
    def _empty_quality() -> Dict:
        """Return empty quality metrics"""
        return {
            'code_duplication': 0.0,
            'comment_ratio': 0.0,
            'documentation_coverage': 0.0,
            'documented_functions': 0,
            'total_functions': 0
        }
