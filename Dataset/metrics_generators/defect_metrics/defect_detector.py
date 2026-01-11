#!/usr/bin/env python3
"""
Defect Metrics Calculator
Detects bugs and defects in code using pattern analysis
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess


class DefectDetector:
    """Detect defects and calculate defect metrics"""
    
    # Common bug patterns
    BUG_PATTERNS = {
        'null_pointer': r'\..*?\(.*?\);?',  # Potential null deref
        'uninitialized': r'if\s*\(\w+\)\s*{',  # Unchecked variable usage
        'array_bounds': r'\[\s*\w+\s*\]',  # Array access without bounds check
        'resource_leak': r'new\s+(FileInputStream|InputStream|Scanner)',  # Resource not closed
        'sql_injection': r'\".*?\+\s*\w+',  # String concatenation in SQL
    }
    
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, any]:
        """
        Analyze file for defects
        
        Args:
            file_path: Path to source file
            
        Returns:
            Dictionary with defect metrics
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            defects = []
            vulnerabilities = []
            
            # Pattern-based defect detection
            for pattern_name, pattern in DefectDetector.BUG_PATTERNS.items():
                matches = list(re.finditer(pattern, content))
                if matches:
                    for match in matches:
                        defects.append({
                            'type': pattern_name,
                            'line': content[:match.start()].count('\n') + 1,
                            'severity': 'medium'
                        })
            
            # Common vulnerability patterns
            vuln_patterns = {
                'hardcoded_password': r'password\s*=\s*["\']',
                'hardcoded_api_key': r'api[_-]?key\s*=\s*["\']',
                'sql_injection': r'execute\s*\(\s*["\'].*?\+',
            }
            
            for vuln_name, pattern in vuln_patterns.items():
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                vulnerabilities.extend([vuln_name] * len(matches))
            
            # Calculate metrics
            from ..loc_metrics import LOCCalculator
            loc_details = LOCCalculator.calculate_detailed(file_path)
            loc_total = loc_details.get('loc', 1)
            
            bug_density = (len(defects) / loc_total * 1000) if loc_total > 0 else 0
            
            return {
                'num_bugs': len(defects),
                'bug_density': round(bug_density, 2),
                'vulnerabilities': len(vulnerabilities),
                'has_defect': len(defects) > 0,
                'defect_types': list(set([d['type'] for d in defects])),
                'vulnerability_types': list(set(vulnerabilities))
            }
            
        except Exception:
            return DefectDetector._empty_defects()
    
    @staticmethod
    def _empty_defects() -> Dict:
        """Return empty defect metrics"""
        return {
            'num_bugs': 0,
            'bug_density': 0.0,
            'vulnerabilities': 0,
            'has_defect': False,
            'defect_types': [],
            'vulnerability_types': []
        }
