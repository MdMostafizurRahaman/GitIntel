#!/usr/bin/env python3
"""Essential Complexity Calculator - measures unstructured code patterns"""
import javalang
import ast
from typing import Dict
from metrics_generators.shared_utils import JavaAST, PythonAST


class EssentialComplexityCalculator:
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        for _, method in tree.filter(javalang.tree.MethodDeclaration):
            complexity = 0
            if method.body:
                for _ in JavaAST.walk_body(method.body, javalang.tree.BreakStatement):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.ContinueStatement):
                    complexity += 1
                loop_count = (
                    sum(1 for _ in JavaAST.walk_body(method.body, javalang.tree.ForStatement)) +
                    sum(1 for _ in JavaAST.walk_body(method.body, javalang.tree.WhileStatement))
                )
                complexity = max(complexity, min(loop_count, 3))
            results[method.name] = complexity
        return results

    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree = PythonAST.parse_file(file_path)
        if tree is None:
            return results
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                results[node.name] = EssentialComplexityCalculator._python_essential(node)
        return results

    @staticmethod
    def _python_essential(node) -> int:
        return sum(1 for c in ast.walk(node) if isinstance(c, (ast.Break, ast.Continue)))
