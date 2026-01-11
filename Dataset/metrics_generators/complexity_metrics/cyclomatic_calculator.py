#!/usr/bin/env python3
"""
Cyclomatic Complexity Calculator
Real implementation using AST parsing
"""

import javalang
import ast
from typing import Dict
from pathlib import Path


class CyclomaticComplexityCalculator:
    """Calculate cyclomatic complexity from source code"""
    
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        """
        Calculate cyclomatic complexity for each method in Java file
        CC = number of independent paths through code (1 + decision points)
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping method names to complexity values
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            
            for path, method in tree.filter(javalang.tree.MethodDeclaration):
                complexity = 1  # Base complexity
                
                if method.body:
                    # Count decision points
                    for _, _ in method.body.filter(javalang.tree.IfStatement):
                        complexity += 1
                    
                    for _, _ in method.body.filter(javalang.tree.WhileStatement):
                        complexity += 1
                    
                    for _, _ in method.body.filter(javalang.tree.ForStatement):
                        complexity += 1
                    
                    for _, _ in method.body.filter(javalang.tree.SwitchStatement):
                        complexity += 1
                    
                    for _, _ in method.body.filter(javalang.tree.CatchClause):
                        complexity += 1
                    
                    # Ternary operators
                    for _, _ in method.body.filter(javalang.tree.TernaryExpression):
                        complexity += 1
                    
                    # Logical operators
                    for _, node in method.body.filter(javalang.tree.BinaryOperation):
                        if node.operator in ['&&', '||']:
                            complexity += 1
                
                results[method.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        """
        Calculate cyclomatic complexity for Python functions
        
        Args:
            file_path: Path to Python source file
            
        Returns:
            Dictionary mapping function names to complexity values
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = CyclomaticComplexityCalculator._python_complexity(node)
                    results[node.name] = complexity
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _python_complexity(node) -> int:
        """Calculate complexity of Python function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
