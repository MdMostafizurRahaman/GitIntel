#!/usr/bin/env python3
"""
BLOC (Blank Lines of Code) Calculator
Counts blank lines in source code
"""

from pathlib import Path
from typing import List


class BLOCCalculator:
    """Calculate BLOC - Blank Lines of Code"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate blank lines from a single file
        
        Args:
            file_path: Path to source file
            
        Returns:
            Count of blank lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            bloc_count = 0
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    bloc_count += 1
            
            return bloc_count
            
        except Exception:
            return 0
    
    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        """
        Calculate total blank lines from all files in directory
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include
            
        Returns:
            Total blank lines
        """
        if extensions is None:
            extensions = ['.java', '.py', '.cpp', '.cs', '.js']
        
        total_bloc = 0
        dir_obj = Path(dir_path)
        
        for file_path in dir_obj.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                total_bloc += BLOCCalculator.calculate_from_file(str(file_path))
        
        return total_bloc
