#!/usr/bin/env python3
"""Cyclomatic Complexity Calculator"""
import javalang
import ast
from typing import Dict
from metrics_generators.shared_utils import JavaAST, PythonAST


class CyclomaticComplexityCalculator:
    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        for _, method in tree.filter(javalang.tree.MethodDeclaration):
            complexity = 1
            if method.body:
                for _ in JavaAST.walk_body(method.body, javalang.tree.IfStatement):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.WhileStatement):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.ForStatement):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.SwitchStatement):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.CatchClause):
                    complexity += 1
                for _ in JavaAST.walk_body(method.body, javalang.tree.TernaryExpression):
                    complexity += 1
                for node in JavaAST.walk_body(method.body, javalang.tree.BinaryOperation):
                    if node.operator in ["&&", "||"]:
                        complexity += 1
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
                results[node.name] = CyclomaticComplexityCalculator._python_complexity(node)
        return results

    @staticmethod
    def _python_complexity(node) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
