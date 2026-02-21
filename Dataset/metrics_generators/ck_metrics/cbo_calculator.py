#!/usr/bin/env python3
"""CBO (Coupling Between Objects) Calculator"""
import re
from metrics_generators.shared_utils import FileReader


class CBOCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            content = FileReader.read(file_path)
            imports = set(re.findall(r"import\s+([\w\.]+);", content))
            class_refs = set(re.findall(r"\bnew\s+(\w+)\s*\(", content))
            type_refs = set(re.findall(r":\s*(\w+)\s*[,\)]", content))
            return len(imports | class_refs | type_refs)
        except Exception:
            return 0
