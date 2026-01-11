#!/usr/bin/env python3
"""
KLOC (Thousands of Lines of Code) Calculator
Converts LOC to thousands (LOC / 1000)
"""

from .loc_calculator import LOCCalculator
from typing import Dict, List


class KLOCCalculator:
    """Calculate KLOC metric from source code"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> float:
        """
        Calculate KLOC from a single file
        Returns LOC / 1000
        
        Args:
            file_path: Path to source file
            
        Returns:
            KLOC value as float
        """
        loc = LOCCalculator.calculate_from_file(file_path)
        return loc / 1000.0
    
    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> float:
        """
        Calculate total KLOC from directory
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include
            
        Returns:
            Total KLOC as float
        """
        total_loc = LOCCalculator.calculate_from_directory(dir_path, extensions)
        return total_loc / 1000.0
    
    @staticmethod
    def calculate_from_files(file_paths: List[str]) -> float:
        """
        Calculate KLOC from multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Total KLOC
        """
        total_loc = 0
        for file_path in file_paths:
            total_loc += LOCCalculator.calculate_from_file(file_path)
        
        return total_loc / 1000.0
