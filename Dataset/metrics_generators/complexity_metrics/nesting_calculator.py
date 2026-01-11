#!/usr/bin/env python3
"""
Maximum Nesting Depth Calculator
Real implementation - measures deepest nesting level in code
"""

import javalang
import ast
from typing import Dict


class MaxNestingDepthCalculator:
    """Calculate maximum nesting depth in source code"""
    
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        """
        Calculate max nesting depth for each method
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            Dictionary mapping method names to max nesting depth
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            
            for path, method in tree.filter(javalang.tree.MethodDeclaration):
                if method.body:
                    depth = MaxNestingDepthCalculator._calculate_java_depth(method.body, 0)
                else:
                    depth = 0
                
                results[method.name] = depth
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _calculate_java_depth(node, current_depth: int = 0) -> int:
        """Recursively calculate maximum nesting depth"""
        max_depth = current_depth
        
        try:
            # Check for nested structures
            for _, child in node.filter(javalang.tree.Block):
                child_depth = MaxNestingDepthCalculator._calculate_java_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            
            for _, child in node.filter(javalang.tree.IfStatement):
                child_depth = current_depth + 1
                max_depth = max(max_depth, child_depth)
            
            for _, child in node.filter(javalang.tree.ForStatement):
                child_depth = current_depth + 1
                max_depth = max(max_depth, child_depth)
            
            for _, child in node.filter(javalang.tree.WhileStatement):
                child_depth = current_depth + 1
                max_depth = max(max_depth, child_depth)
        except:
            pass
        
        return max_depth
    
    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        """
        Calculate max nesting depth for Python functions
        
        Args:
            file_path: Path to Python source file
            
        Returns:
            Dictionary mapping function names to max nesting depth
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    depth = MaxNestingDepthCalculator._python_depth(node)
                    results[node.name] = depth
            
            return results
            
        except Exception:
            return results
    
    @staticmethod
    def _python_depth(node, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of Python function"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = MaxNestingDepthCalculator._python_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = MaxNestingDepthCalculator._python_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
