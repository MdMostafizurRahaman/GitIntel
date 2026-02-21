#!/usr/bin/env python3
"""CLOC (Comment Lines of Code) Calculator"""
from typing import List
from metrics_generators.shared_utils import FileReader, DirTraversal


class CLOCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            lines = FileReader.read_lines(file_path)
            cloc_count = 0
            in_block = False
            for line in lines:
                s = line.strip()
                if "/*" in s:
                    in_block = True
                if s.startswith("//") or s.startswith("#"):
                    cloc_count += 1
                elif in_block or s.startswith("*"):
                    cloc_count += 1
                if "*/" in s:
                    in_block = False
            return cloc_count
        except Exception:
            return 0

    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        total = 0
        for fp in DirTraversal.get_files(dir_path, extensions):
            total += CLOCCalculator.calculate_from_file(str(fp))
        return total

    @staticmethod
    def calculate_ratio(file_path: str) -> float:
        try:
            lines = FileReader.read_lines(file_path)
            loc = cloc = 0
            in_block = False
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                if "/*" in s:
                    in_block = True
                if s.startswith("//") or s.startswith("#") or in_block:
                    cloc += 1
                else:
                    loc += 1
                if "*/" in s:
                    in_block = False
            return cloc / loc if loc else 0.0
        except Exception:
            return 0.0
