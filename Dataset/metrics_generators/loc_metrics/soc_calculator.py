#!/usr/bin/env python3
"""
SOC (Source Lines of Code) Calculator
Counts source lines excluding non-executable statements
"""

import re
from pathlib import Path
from typing import List


class SOCCalculator:
    """Calculate SOC - Source Lines of Code (executable only)"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate executable source lines from a single file
        Excludes blank lines, pure comments, and import statements
        
        Args:
            file_path: Path to source file
            
        Returns:
            Count of executable source lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            soc_count = 0
            in_block_comment = False
            
            for line in lines:
                stripped = line.strip()
                
                # Skip blank lines
                if not stripped:
                    continue
                
                # Track multi-line comments
                if '/*' in stripped:
                    in_block_comment = True
                
                if in_block_comment:
                    if '*/' in stripped:
                        in_block_comment = False
                    continue
                
                # Skip single-line comments
                if stripped.startswith('//') or stripped.startswith('#'):
                    continue
                
                # Skip import/package statements (non-executable)
                if stripped.startswith('import ') or stripped.startswith('package '):
                    continue
                
                # Skip from statements (Python)
                if stripped.startswith('from ') and ' import ' in stripped:
                    continue
                
                # Count as executable source line
                soc_count += 1
            
            return soc_count
            
        except Exception:
            return 0
    
    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        """
        Calculate total executable source lines from directory
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include
            
        Returns:
            Total executable source lines
        """
        if extensions is None:
            extensions = ['.java', '.py', '.cpp', '.cs', '.js']
        
        total_soc = 0
        dir_obj = Path(dir_path)
        
        for file_path in dir_obj.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                total_soc += SOCCalculator.calculate_from_file(str(file_path))
        
        return total_soc
