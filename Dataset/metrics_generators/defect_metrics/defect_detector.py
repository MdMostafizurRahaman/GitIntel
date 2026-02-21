#!/usr/bin/env python3
"""Defect Metrics Calculator - bug and vulnerability detection via pattern analysis"""
import re
from typing import Dict
from metrics_generators.shared_utils import FileReader


class DefectDetector:
    BUG_PATTERNS = {
        "null_pointer":   r"\..*?\(.*?\);?",
        "uninitialized":  r"if\s*\(\w+\)\s*{",
        "array_bounds":   r"\[\s*\w+\s*\]",
        "resource_leak":  r"new\s+(FileInputStream|InputStream|Scanner)",
        "sql_injection":  r"\".*?\+\s*\w+",
    }

    @staticmethod
    def analyze_file(file_path: str) -> Dict:
        try:
            content = FileReader.read(file_path)
            defects = []
            vulnerabilities = []

            for name, pat in DefectDetector.BUG_PATTERNS.items():
                for m in re.finditer(pat, content):
                    defects.append({
                        "type": name,
                        "line": content[: m.start()].count("\n") + 1,
                        "severity": "medium",
                    })

            for vname, pat in {
                "hardcoded_password": r"password\s*=\s*[\"\']",
                "hardcoded_api_key":  r"api[_-]?key\s*=\s*[\"\']",
                "sql_injection":      r"execute\s*\(\s*[\"\'].*?\+",
            }.items():
                vulnerabilities.extend([vname] * len(re.findall(pat, content, re.IGNORECASE)))

            from metrics_generators.loc_metrics.loc_calculator import LOCCalculator
            loc_total = LOCCalculator.calculate_detailed(file_path).get("loc", 1)
            bug_density = len(defects) / loc_total * 1000 if loc_total else 0

            return {
                "num_bugs": len(defects),
                "bug_density": round(bug_density, 2),
                "vulnerabilities": len(vulnerabilities),
                "has_defect": len(defects) > 0,
                "defect_types": list({d["type"] for d in defects}),
                "vulnerability_types": list(set(vulnerabilities)),
            }
        except Exception:
            return DefectDetector._empty()

    @staticmethod
    def _empty() -> Dict:
        return {
            "num_bugs": 0, "bug_density": 0.0, "vulnerabilities": 0,
            "has_defect": False, "defect_types": [], "vulnerability_types": [],
        }
