#!/usr/bin/env python3
"""
LOC (Lines of Code) Calculator - Real implementation
Counts total lines excluding comments and blank lines
"""

import re
from pathlib import Path
from typing import Dict, List


class LOCCalculator:
    """Calculate actual Lines of Code from source files"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate LOC from a single file
        Excludes blank lines and comment lines
        
        Args:
            file_path: Path to source file
            
        Returns:
            Integer count of lines of code
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            loc_count = 0
            for line in lines:
                stripped = line.strip()
                
                # Skip blank lines
                if not stripped:
                    continue
                
                # Skip single-line comments (// style)
                if stripped.startswith('//'):
                    continue
                
                # Skip single-line comments (# style for Python)
                if stripped.startswith('#'):
                    continue
                
                # Skip javadoc/docstring lines
                if stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('*/'):
                    continue
                
                # Count this line as code
                loc_count += 1
            
            return loc_count
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0
    
    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        """
        Calculate total LOC from all files in directory
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include (e.g., ['.java', '.py'])
            
        Returns:
            Total lines of code
        """
        if extensions is None:
            extensions = ['.java', '.py', '.cpp', '.cs', '.js']
        
        total_loc = 0
        dir_obj = Path(dir_path)
        
        for file_path in dir_obj.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                total_loc += LOCCalculator.calculate_from_file(str(file_path))
        
        return total_loc
    
    @staticmethod
    def calculate_detailed(file_path: str) -> Dict[str, int]:
        """
        Calculate detailed LOC breakdown
        
        Returns:
            Dict with 'loc', 'blank_lines', 'comment_lines' counts
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            loc_count = 0
            blank_count = 0
            comment_count = 0
            
            for line in lines:
                stripped = line.strip()
                
                if not stripped:
                    blank_count += 1
                    continue
                
                if stripped.startswith('//') or stripped.startswith('#'):
                    comment_count += 1
                    continue
                
                if stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('*/'):
                    comment_count += 1
                    continue
                
                loc_count += 1
            
            return {
                'loc': loc_count,
                'blank_lines': blank_count,
                'comment_lines': comment_count,
                'total_lines': len(lines)
            }
            
        except Exception as e:
            return {
                'loc': 0,
                'blank_lines': 0,
                'comment_lines': 0,
                'total_lines': 0
            }
