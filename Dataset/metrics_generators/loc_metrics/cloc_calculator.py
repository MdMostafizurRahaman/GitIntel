#!/usr/bin/env python3
"""
CLOC (Comment Lines of Code) Calculator
Counts actual comment lines in source code
"""

from pathlib import Path
from typing import Dict, List


class CLOCCalculator:
    """Calculate CLOC - Comment Lines of Code"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate comment lines from a single file
        
        Args:
            file_path: Path to source file
            
        Returns:
            Count of comment lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            cloc_count = 0
            in_block_comment = False
            
            for line in lines:
                stripped = line.strip()
                
                # Track multi-line comments
                if '/*' in stripped:
                    in_block_comment = True
                
                # Count comment lines
                if stripped.startswith('//') or stripped.startswith('#'):
                    cloc_count += 1
                elif in_block_comment or stripped.startswith('*'):
                    cloc_count += 1
                
                if '*/' in stripped:
                    in_block_comment = False
            
            return cloc_count
            
        except Exception as e:
            return 0
    
    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        """
        Calculate total comment lines from all files in directory
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include
            
        Returns:
            Total comment lines
        """
        if extensions is None:
            extensions = ['.java', '.py', '.cpp', '.cs', '.js']
        
        total_cloc = 0
        dir_obj = Path(dir_path)
        
        for file_path in dir_obj.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                total_cloc += CLOCCalculator.calculate_from_file(str(file_path))
        
        return total_cloc
    
    @staticmethod
    def calculate_ratio(file_path: str) -> float:
        """
        Calculate comment to code ratio
        
        Returns:
            Float ratio of comments to code
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            loc_count = 0
            cloc_count = 0
            in_block_comment = False
            
            for line in lines:
                stripped = line.strip()
                
                if not stripped:
                    continue
                
                if '/*' in stripped:
                    in_block_comment = True
                
                if stripped.startswith('//') or stripped.startswith('#') or in_block_comment:
                    cloc_count += 1
                else:
                    loc_count += 1
                
                if '*/' in stripped:
                    in_block_comment = False
            
            if loc_count == 0:
                return 0.0
            
            return cloc_count / loc_count
            
        except Exception:
            return 0.0
