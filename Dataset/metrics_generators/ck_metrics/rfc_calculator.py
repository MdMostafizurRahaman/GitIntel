#!/usr/bin/env python3
"""RFC (Response For a Class) Calculator"""
import re
from metrics_generators.shared_utils import FileReader


class RFCCalculator:
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        try:
            content = FileReader.read(file_path)
            local_methods = len(re.findall(
                r"\b(?:public|private|protected)\s+(?:static\s+)?\w+\s+\w+\s*\(", content
            ))
            method_calls = len(set(re.findall(r"\.\w+\s*\(", content)))
            return local_methods + method_calls
        except Exception:
            return 0