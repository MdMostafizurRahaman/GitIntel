#!/usr/bin/env python3
"""Nesting Depth Calculator - max nesting depth for Java and Python"""
import ast
from typing import Dict
from metrics_generators.shared_utils import JavaAST, PythonAST


class MaxNestingDepthCalculator:
    """Calculate maximum nesting depth of control structures."""

    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree = PythonAST.parse_file(file_path)
        if tree is None:
            return results
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                results[node.name] = MaxNestingDepthCalculator._py_depth(node)
        return results

    @staticmethod
    def _py_depth(node, current: int = 0) -> int:
        max_d = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                d = MaxNestingDepthCalculator._py_depth(child, current + 1)
                max_d = max(max_d, d)
            else:
                d = MaxNestingDepthCalculator._py_depth(child, current)
                max_d = max(max_d, d)
        return max_d

    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        """Calculate max nesting depth per method using javalang AST."""
        import javalang
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        for _, method in tree.filter(javalang.tree.MethodDeclaration):
            if method.body:
                depth = MaxNestingDepthCalculator._java_depth(method.body)
            else:
                depth = 0
            results[method.name] = depth
        return results

    @staticmethod
    def _java_depth(nodes, current: int = 0) -> int:
        """Recursively compute max nesting depth within a list of javalang statements."""
        import javalang
        NESTING_TYPES = (
            javalang.tree.IfStatement,
            javalang.tree.ForStatement,
            javalang.tree.WhileStatement,
            javalang.tree.DoStatement,
            javalang.tree.SwitchStatement,
            javalang.tree.TryStatement,
        )
        max_d = current
        for node in (nodes or []):
            if node is None or not isinstance(node, javalang.ast.Node):
                continue
            if isinstance(node, NESTING_TYPES):
                # This node adds one nesting level; recurse into its children
                child_nodes = []
                for attr_name in node.attrs:
                    child = getattr(node, attr_name, None)
                    if isinstance(child, list):
                        child_nodes.extend(child)
                    elif child is not None and isinstance(child, javalang.ast.Node):
                        child_nodes.append(child)
                d = MaxNestingDepthCalculator._java_depth(child_nodes, current + 1)
                max_d = max(max_d, d)
            else:
                # Non-nesting node: recurse into children at same depth
                child_nodes = []
                for attr_name in node.attrs:
                    child = getattr(node, attr_name, None)
                    if isinstance(child, list):
                        child_nodes.extend(child)
                    elif child is not None and isinstance(child, javalang.ast.Node):
                        child_nodes.append(child)
                d = MaxNestingDepthCalculator._java_depth(child_nodes, current)
                max_d = max(max_d, d)
        return max_d


# Alias for backwards compatibility
NestingDepthCalculator = MaxNestingDepthCalculator
