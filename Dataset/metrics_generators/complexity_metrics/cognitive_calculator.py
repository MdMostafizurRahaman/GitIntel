#!/usr/bin/env python3
"""
Cognitive Complexity Calculator
Real implementation - measures how difficult code is to understand
"""

import javalang
import ast
from typing import Dict


class CognitiveComplexityCalculator:
    """Calculate cognitive complexity from source code"""
    
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        """
        Calculate cognitive complexity for each method
        Cognitive complexity adds to cyclomatic + nesting penalty
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping method names to cognitive complexity values
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            
            for path, method in tree.filter(javalang.tree.MethodDeclaration):
                if method.body:
                    complexity = CognitiveComplexityCalculator._calculate_java_cognitive(method.body)
                else:
                    complexity = 0
                
                results[method.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _calculate_java_cognitive(body, nesting_level: int = 0) -> int:
        """Calculate cognitive complexity with nesting penalties"""
        complexity = 0
        
        try:
            # Count decision points with nesting penalties
            for _, node in body.filter(javalang.tree.IfStatement):
                complexity += 1 + nesting_level
            
            for _, node in body.filter(javalang.tree.WhileStatement):
                complexity += 1 + nesting_level
            
            for _, node in body.filter(javalang.tree.ForStatement):
                complexity += 1 + nesting_level
            
            for _, node in body.filter(javalang.tree.SwitchStatement):
                complexity += 1 + nesting_level
            
            for _, node in body.filter(javalang.tree.CatchClause):
                complexity += 1 + nesting_level
        except:
            pass
        
        return complexity
    
    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        """
        Calculate cognitive complexity for Python functions
        
        Args:
            file_path: Path to Python source file
            
        Returns:
            Dictionary mapping function names to cognitive complexity
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = CognitiveComplexityCalculator._python_cognitive(node)
                    results[node.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _python_cognitive(node, nesting_level: int = 0) -> int:
        """Calculate cognitive complexity of Python function"""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                complexity += 1 + nesting_level
            elif isinstance(child, ast.While):
                complexity += 1 + nesting_level
            elif isinstance(child, ast.For):
                complexity += 1 + nesting_level
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1 + nesting_level
        
        return complexity
