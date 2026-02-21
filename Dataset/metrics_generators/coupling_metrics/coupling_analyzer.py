#!/usr/bin/env python3
"""Coupling Metrics Calculator - afferent/efferent coupling, instability, abstractness"""
import javalang
import re
from typing import Dict
from metrics_generators.shared_utils import FileReader, JavaAST, DirTraversal


class CouplingAnalyzer:
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, int]:
        """Analyze coupling metrics for a single file."""
        try:
            content = FileReader.read(file_path)
            imports = set(re.findall(r"import\s+([\w\.]+);", content))
            return {"afferent_coupling": 0, "efferent_coupling": len(imports)}
        except Exception:
            return {"afferent_coupling": 0, "efferent_coupling": 0}

    @staticmethod
    def analyze_directory(dir_path: str) -> Dict[str, Dict[str, int]]:
        """Analyze coupling for all Java files in directory."""
        metrics = {}
        for java_file in DirTraversal.get_files(dir_path, [".java"]):
            try:
                tree, _ = JavaAST.parse_file(str(java_file))
                if tree is None:
                    continue
                pkg = JavaAST.get_package(tree)
                for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
                    cname = JavaAST.class_full_name(pkg, class_node)
                    afferent = CouplingAnalyzer._calculate_afferent(cname, dir_path)
                    efferent = CouplingAnalyzer._calculate_efferent(class_node, pkg)
                    total = afferent + efferent
                    metrics[cname] = {
                        "afferent_coupling": afferent,
                        "efferent_coupling": efferent,
                        "instability": round(efferent / total, 2) if total > 0 else 0,
                        "is_abstract": "abstract" in class_node.modifiers,
                    }
            except Exception:
                continue
        return metrics

    @staticmethod
    def _calculate_afferent(class_name: str, dir_path: str) -> int:
        simple_name = class_name.split(".")[-1]
        count = 0
        for java_file in DirTraversal.get_files(dir_path, [".java"]):
            try:
                if simple_name in FileReader.read(str(java_file)):
                    count += 1
            except Exception:
                continue
        return count

    @staticmethod
    def _calculate_efferent(class_node, package_name: str) -> int:
        deps = set()
        try:
            if hasattr(class_node, "extends") and class_node.extends:
                deps.add(class_node.extends.name)
            if hasattr(class_node, "implements") and class_node.implements:
                for iface in class_node.implements:
                    deps.add(iface.name)
            if hasattr(class_node, "body"):
                for member in class_node.body:
                    if hasattr(member, "type") and hasattr(member.type, "name"):
                        deps.add(member.type.name)
        except Exception:
            pass
        return len(deps)
