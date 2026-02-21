#!/usr/bin/env python3
"""BLOC (Blank Lines of Code) Calculator"""
from typing import List
from metrics_generators.shared_utils import FileReader, DirTraversal


class BLOCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            return sum(1 for l in FileReader.read_lines(file_path) if not l.strip())
        except Exception:
            return 0

    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        total = 0
        for fp in DirTraversal.get_files(dir_path, extensions):
            total += BLOCCalculator.calculate_from_file(str(fp))
        return total
