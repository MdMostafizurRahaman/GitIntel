#!/usr/bin/env python3
"""DIT (Depth of Inheritance Tree) Calculator"""
import javalang
from typing import Dict
from collections import defaultdict
from metrics_generators.shared_utils import FileReader, JavaAST, DirTraversal


class DITCalculator:
    @staticmethod
    def calculate_from_directory(dir_path: str) -> Dict[str, int]:
        inheritance_tree = defaultdict(str)
        all_classes = set()
        for java_file in DirTraversal.get_files(dir_path, [".java"]):
            try:
                tree, _ = JavaAST.parse_file(str(java_file))
                if tree is None:
                    continue
                pkg = JavaAST.get_package(tree)
                for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
                    cname = JavaAST.class_full_name(pkg, class_node)
                    all_classes.add(cname)
                    if class_node.extends:
                        parent = class_node.extends.name
                        pname = JavaAST.class_full_name(pkg, type("_", (), {"name": parent})())
                        inheritance_tree[cname] = pname
            except Exception:
                continue
        return {c: DITCalculator._depth(c, inheritance_tree) for c in all_classes}

    @staticmethod
    def _depth(class_name: str, tree: Dict, visited: set = None) -> int:
        if visited is None:
            visited = set()
        if class_name in visited or class_name not in tree:
            return 0
        visited.add(class_name)
        return 1 + DITCalculator._depth(tree[class_name], tree, visited.copy())

    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return 0
        pkg = JavaAST.get_package(tree)
        inheritance = {}
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            cname = JavaAST.class_full_name(pkg, class_node)
            if class_node.extends:
                parent = class_node.extends.name
                pname = JavaAST.class_full_name(pkg, type("_", (), {"name": parent})())
                inheritance[cname] = pname
        if not inheritance:
            return 0
        depths = [DITCalculator._depth(c, inheritance) for c in inheritance]
        return max(depths) if depths else 0
