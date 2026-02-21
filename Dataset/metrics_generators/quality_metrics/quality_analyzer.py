#!/usr/bin/env python3
"""Quality Metrics Calculator - duplication, comment ratio, documentation coverage"""
import re
from typing import Dict
from collections import defaultdict
from metrics_generators.shared_utils import FileReader


class QualityAnalyzer:
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, float]:
        try:
            content = FileReader.read(file_path)
            lines = content.split("\n")
            duplication = QualityAnalyzer._duplication(lines)
            docs = QualityAnalyzer._documentation(content)
            from metrics_generators.loc_metrics.cloc_calculator import CLOCCalculator
            from metrics_generators.loc_metrics.loc_calculator import LOCCalculator
            cloc = CLOCCalculator.calculate_from_file(file_path)
            loc_total = LOCCalculator.calculate_detailed(file_path).get("loc", 1)
            comment_ratio = cloc / loc_total * 100 if loc_total else 0
            return {
                "code_duplication": round(duplication, 2),
                "comment_ratio": round(comment_ratio, 2),
                "documentation_coverage": round(docs["coverage"], 2),
                "documented_functions": docs["documented"],
                "total_functions": docs["total"],
            }
        except Exception:
            return QualityAnalyzer._empty()

    @staticmethod
    def _duplication(lines: list) -> float:
        groups = defaultdict(int)
        total = 0
        for line in lines:
            s = line.strip()
            if s and not s.startswith("//") and not s.startswith("#"):
                groups[s] += 1
                total += 1
        if not total:
            return 0.0
        dupes = sum(c - 1 for c in groups.values() if c > 1)
        return dupes / total * 100

    @staticmethod
    def _documentation(content: str) -> Dict:
        javadoc = len(re.findall(r"/\*\*.*?\*/", content, re.DOTALL))
        docstr  = len(re.findall(r'''""".*?"""''', content, re.DOTALL))
        methods = len(re.findall(r"(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(", content))
        total_doc = javadoc + docstr
        return {
            "coverage": total_doc / max(1, methods) * 100 if methods else 0,
            "documented": total_doc,
            "total": methods,
        }

    @staticmethod
    def _empty() -> Dict:
        return {"code_duplication": 0.0, "comment_ratio": 0.0,
                "documentation_coverage": 0.0, "documented_functions": 0, "total_functions": 0}
