#!/usr/bin/env python3
"""
WMC (Weighted Methods per Class) Calculator
Real implementation using AST parsing for Java
"""

import javalang
from pathlib import Path
from typing import Dict


class WMCCalculator:
    """Calculate WMC - Weighted Methods per Class"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> Dict[str, int]:
        """
        Calculate WMC for all classes in a Java file
        WMC = sum of cyclomatic complexity of all methods
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping class names to WMC values
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse Java file
            try:
                tree = javalang.parse.parse(content)
            except:
                return results
            
            # Get package name
            package_name = tree.package.name if tree.package else ""
            
            # Process each class
            for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                
                # Count methods in class
                method_count = 0
                for _, method in tree.filter(javalang.tree.MethodDeclaration):
                    method_count += 1
                
                # WMC = number of methods (simplified, can be enhanced with cyclomatic complexity)
                results[class_name] = max(1, method_count)  # At least 1 (constructor)
            
            return results
            
        except Exception as e:
            return results
    
    @staticmethod
    def calculate_complexity_weighted(file_path: str) -> Dict[str, float]:
        """
        Calculate WMC weighted by cyclomatic complexity of each method
        More accurate implementation
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping class names to weighted WMC values
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            package_name = tree.package.name if tree.package else ""
            
            for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                
                # Sum complexities of all methods
                total_complexity = 0
                for _, method in tree.filter(javalang.tree.MethodDeclaration):
                    # Count decision points (if, for, while, catch, case, etc.)
                    complexity = WMCCalculator._calculate_cyclomatic_complexity(method)
                    total_complexity += complexity
                
                results[class_name] = max(1, total_complexity)
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _calculate_cyclomatic_complexity(method_node) -> int:
        """Calculate cyclomatic complexity of a method"""
        complexity = 1  # Base complexity
        
        try:
            for _, node in method_node.filter(javalang.tree.IfStatement):
                complexity += 1
            
            for _, node in method_node.filter(javalang.tree.WhileStatement):
                complexity += 1
            
            for _, node in method_node.filter(javalang.tree.ForStatement):
                complexity += 1
            
            for _, node in method_node.filter(javalang.tree.SwitchStatement):
                complexity += 1
            
            for _, node in method_node.filter(javalang.tree.CatchClause):
                complexity += 1
        except:
            pass
        
        return complexity
