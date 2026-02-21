#!/usr/bin/env python3
"""
Shared utilities for metrics_generators calculators.
Centralises file reading, directory traversal, and AST parsing
so individual calculators contain only core metric logic.
"""

import ast
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

class FileReader:
    """Centralised text-file reading (replaces 18+ open() calls)."""

    @staticmethod
    def read(file_path: str) -> str:
        """Return full file content as a string."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    @staticmethod
    def read_lines(file_path: str) -> List[str]:
        """Return file lines as a list (newlines preserved)."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()


# ---------------------------------------------------------------------------
# Directory traversal
# ---------------------------------------------------------------------------

class DirTraversal:
    """Centralised recursive directory file enumeration (replaces 4+ rglob patterns)."""

    DEFAULT_EXTENSIONS = ['.java', '.py', '.cpp', '.cs', '.js']

    @staticmethod
    def get_files(dir_path: str, extensions: List[str] = None) -> List[Path]:
        """
        Return all files under dir_path whose suffix is in extensions.

        Args:
            dir_path: Root directory to search.
            extensions: Suffixes to include, e.g. ['.java', '.py'].
                        Defaults to DEFAULT_EXTENSIONS.

        Returns:
            List of Path objects for matching files.
        """
        if extensions is None:
            extensions = DirTraversal.DEFAULT_EXTENSIONS

        result = []
        for p in Path(dir_path).rglob('*'):
            if p.is_file() and p.suffix in extensions:
                result.append(p)
        return result


# ---------------------------------------------------------------------------
# Java AST helpers
# ---------------------------------------------------------------------------

class JavaAST:
    """Centralised javalang parsing utilities (replaces 12+ javalang.parse calls)."""

    @staticmethod
    def parse(content: str):
        """
        Parse Java source code string.

        Returns:
            javalang CompilationUnit, or None on parse failure.
        """
        try:
            import javalang
            return javalang.parse.parse(content)
        except Exception:
            return None

    @staticmethod
    def parse_file(file_path: str) -> Tuple[Optional[object], str]:
        """
        Read and parse a Java source file.

        Returns:
            (tree, content) tuple.  tree is None when parsing fails.
        """
        content = FileReader.read(file_path)
        tree = JavaAST.parse(content)
        return tree, content

    @staticmethod
    def get_package(tree) -> str:
        """Return the package name from a parsed tree, or '' if absent."""
        try:
            return tree.package.name if tree.package else ""
        except Exception:
            return ""

    @staticmethod
    def class_full_name(package_name: str, class_node) -> str:
        """Build a fully-qualified class name from package + class node."""
        return f"{package_name}.{class_node.name}" if package_name else class_node.name

    @staticmethod
    def walk_body(nodes, node_type):
        """
        Recursively yield all javalang nodes of node_type within a body list.

        method.body in javalang is a plain Python list, not an AST node, so
        calling body.filter() raises AttributeError.  Use this instead of
        body.filter(SomeType).
        """
        import javalang
        for node in (nodes or []):
            if node is None:
                continue
            if isinstance(node, node_type):
                yield node
            if isinstance(node, javalang.ast.Node):
                for attr_name in node.attrs:
                    child = getattr(node, attr_name, None)
                    if isinstance(child, list):
                        yield from JavaAST.walk_body(child, node_type)
                    elif child is not None and isinstance(child, javalang.ast.Node):
                        yield from JavaAST.walk_body([child], node_type)


# ---------------------------------------------------------------------------
# Python AST helpers
# ---------------------------------------------------------------------------

class PythonAST:
    """Centralised ast parsing utilities (replaces 6+ ast.parse calls)."""

    @staticmethod
    def parse_file(file_path: str) -> Optional[ast.AST]:
        """
        Read and parse a Python source file.

        Returns:
            ast.Module, or None on parse failure.
        """
        try:
            content = FileReader.read(file_path)
            return ast.parse(content)
        except Exception:
            return None
