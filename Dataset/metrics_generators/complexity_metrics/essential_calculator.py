#!/usr/bin/env python3
"""
Essential Complexity Calculator
Real implementation - measures unstructured code patterns
"""

import javalang
import ast
from typing import Dict


class EssentialComplexityCalculator:
    """Calculate essential complexity - unstructured constructs"""
    
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        """
        Calculate essential complexity for each method
        Measures complexity from unstructured constructs (goto, break, continue)
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping method names to essential complexity
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            
            for path, method in tree.filter(javalang.tree.MethodDeclaration):
                complexity = 0
                
                if method.body:
                    # Count break statements (unstructured)
                    for _, _ in method.body.filter(javalang.tree.BreakStatement):
                        complexity += 1
                    
                    # Count continue statements
                    for _, _ in method.body.filter(javalang.tree.ContinueStatement):
                        complexity += 1
                    
                    # Count nested loops (structural complexity)
                    loop_count = 0
                    for _, _ in method.body.filter(javalang.tree.ForStatement):
                        loop_count += 1
                    for _, _ in method.body.filter(javalang.tree.WhileStatement):
                        loop_count += 1
                    
                    complexity = max(complexity, min(loop_count, 3))
                
                results[method.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        """
        Calculate essential complexity for Python functions
        
        Args:
            file_path: Path to Python source file
            
        Returns:
            Dictionary mapping function names to essential complexity
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = EssentialComplexityCalculator._python_essential(node)
                    results[node.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _python_essential(node) -> int:
        """Calculate essential complexity of Python function"""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.Break, ast.Continue)):
                complexity += 1
        
        return complexity
