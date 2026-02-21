#!/usr/bin/env python3
"""NOC (Number of Children) Calculator"""
import javalang
from typing import Dict
from collections import defaultdict
from metrics_generators.shared_utils import JavaAST, DirTraversal


class NOCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        # NOC requires multi-file analysis; single file always 0
        return 0

    @staticmethod
    def calculate_from_directory(dir_path: str) -> Dict[str, int]:
        inheritance = defaultdict(list)
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
                        inheritance[pname].append(cname)
            except Exception:
                continue
        return {c: len(inheritance.get(c, [])) for c in all_classes}
