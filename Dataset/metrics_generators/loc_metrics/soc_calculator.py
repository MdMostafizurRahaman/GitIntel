#!/usr/bin/env python3
"""SOC (Source Lines of Code) Calculator - executable lines only"""
from typing import List
from metrics_generators.shared_utils import FileReader, DirTraversal


class SOCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            lines = FileReader.read_lines(file_path)
            soc = 0
            in_block = False
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                if "/*" in s:
                    in_block = True
                if in_block:
                    if "*/" in s:
                        in_block = False
                    continue
                if s.startswith("//") or s.startswith("#"):
                    continue
                if s.startswith("import ") or s.startswith("package "):
                    continue
                if s.startswith("from ") and " import " in s:
                    continue
                soc += 1
            return soc
        except Exception:
            return 0

    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        total = 0
        for fp in DirTraversal.get_files(dir_path, extensions):
            total += SOCCalculator.calculate_from_file(str(fp))
        return total
