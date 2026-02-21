#!/usr/bin/env python3
"""WMC (Weighted Methods per Class) Calculator"""
import javalang
from typing import Dict
from metrics_generators.shared_utils import JavaAST


class WMCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        pkg = JavaAST.get_package(tree)
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = JavaAST.class_full_name(pkg, class_node)
            # Count only methods belonging to THIS class, not the whole file
            method_count = len(class_node.methods) if class_node.methods else 0
            results[class_name] = max(1, method_count)
        return results

    @staticmethod
    def calculate_complexity_weighted(file_path: str) -> Dict[str, float]:
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        pkg = JavaAST.get_package(tree)
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = JavaAST.class_full_name(pkg, class_node)
            # Sum complexity of methods in THIS class only
            total = sum(
                WMCCalculator._cyclomatic(m)
                for m in (class_node.methods or [])
            )
            results[class_name] = max(1, total)
        return results

    @staticmethod
    def _cyclomatic(method_node) -> int:
        complexity = 1
        try:
            for _, _ in method_node.filter(javalang.tree.IfStatement):
                complexity += 1
            for _, _ in method_node.filter(javalang.tree.WhileStatement):
                complexity += 1
            for _, _ in method_node.filter(javalang.tree.ForStatement):
                complexity += 1
            for _, _ in method_node.filter(javalang.tree.SwitchStatement):
                complexity += 1
            for _, _ in method_node.filter(javalang.tree.CatchClause):
                complexity += 1
        except Exception:
            pass
        return complexity
