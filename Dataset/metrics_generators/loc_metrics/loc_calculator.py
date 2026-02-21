#!/usr/bin/env python3
"""LOC (Lines of Code) Calculator"""
from typing import Dict, List
from metrics_generators.shared_utils import FileReader, DirTraversal


class LOCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            lines = FileReader.read_lines(file_path)
            loc_count = 0
            for line in lines:
                s = line.strip()
                if not s:
                    continue
                if s.startswith("//") or s.startswith("#"):
                    continue
                if s.startswith("/*") or s.startswith("*") or s.startswith("*/"):
                    continue
                loc_count += 1
            return loc_count
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0

    @staticmethod
    def calculate_from_directory(dir_path: str, extensions: List[str] = None) -> int:
        total = 0
        for fp in DirTraversal.get_files(dir_path, extensions):
            total += LOCCalculator.calculate_from_file(str(fp))
        return total

    @staticmethod
    def calculate_detailed(file_path: str) -> Dict[str, int]:
        try:
            lines = FileReader.read_lines(file_path)
            loc = blank = comment = 0
            for line in lines:
                s = line.strip()
                if not s:
                    blank += 1
                elif (s.startswith("//") or s.startswith("#") or
                      s.startswith("/*") or s.startswith("*") or s.startswith("*/")):
                    comment += 1
                else:
                    loc += 1
            return {"loc": loc, "blank_lines": blank, "comment_lines": comment,
                    "total_lines": len(lines)}
        except Exception:
            return {"loc": 0, "blank_lines": 0, "comment_lines": 0, "total_lines": 0}
