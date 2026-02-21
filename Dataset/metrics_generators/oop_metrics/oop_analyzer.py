#!/usr/bin/env python3
"""OOP Metrics Analyzer - classes, methods, fields, inheritance, polymorphism"""
import re
from typing import Dict
from metrics_generators.shared_utils import FileReader


class OOPAnalyzer:
    @staticmethod
    def analyze_file(file_path: str) -> Dict:
        try:
            code = FileReader.read(file_path)
            if file_path.endswith(".java"):
                return OOPAnalyzer._java(code)
            elif file_path.endswith(".py"):
                return OOPAnalyzer._python(code)
            return OOPAnalyzer._empty()
        except Exception:
            return OOPAnalyzer._empty()

    @staticmethod
    def _java(code: str) -> Dict:
        pub_m  = re.findall(r"\bpublic\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(", code)
        priv_m = re.findall(r"\bprivate\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(", code)
        prot_m = re.findall(r"\bprotected\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(", code)
        pub_f  = re.findall(r"\bpublic\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]", code)
        priv_f = re.findall(r"\bprivate\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]", code)
        prot_f = re.findall(r"\bprotected\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]", code)
        all_m = len(pub_m) + len(priv_m) + len(prot_m)
        all_f = len(pub_f) + len(priv_f) + len(prot_f)
        total = all_m + all_f
        private = len(priv_m) + len(priv_f)
        extends = re.findall(r"\bextends\s+\w+", code)
        implements = re.findall(r"\bimplements\s+\w+", code)
        overrides = re.findall(r"@Override", code)
        return {
            "num_classes": len(re.findall(r"\bclass\s+\w+", code)),
            "num_interfaces": len(re.findall(r"\binterface\s+\w+", code)),
            "num_abstract_classes": len(re.findall(r"\babstract\s+class\s+\w+", code)),
            "num_public_methods": len(pub_m), "num_private_methods": len(priv_m),
            "num_protected_methods": len(prot_m), "num_methods": all_m,
            "num_public_fields": len(pub_f), "num_private_fields": len(priv_f),
            "num_protected_fields": len(prot_f), "num_fields": all_f,
            "inheritance_depth": min(len(extends), 5),
            "polymorphism_factor": len(implements) + len(overrides),
            "encapsulation_ratio": round(private / total, 3) if total > 0 else 0,
        }

    @staticmethod
    def _python(code: str) -> Dict:
        all_m  = re.findall(r"^\s+def\s+\w+\s*\(", code, re.MULTILINE)
        priv_m = re.findall(r"^\s+def\s+__\w+\s*\(", code, re.MULTILINE)
        prot_m = re.findall(r"^\s+def\s+_\w+\s*\(", code, re.MULTILINE)
        all_f  = re.findall(r"^\s+self\.\w+\s*=", code, re.MULTILINE)
        priv_f = re.findall(r"^\s+self\.__\w+\s*=", code, re.MULTILINE)
        prot_f = re.findall(r"^\s+self\._\w+\s*=", code, re.MULTILINE)
        pub_m_count = len(all_m) - len(priv_m) - len(prot_m)
        pub_f_count = len(all_f) - len(priv_f) - len(prot_f)
        total = len(all_m) + len(all_f)
        private = len(priv_m) + len(priv_f)
        return {
            "num_classes": len(re.findall(r"^class\s+\w+", code, re.MULTILINE)),
            "num_interfaces": 0,
            "num_abstract_classes": len(re.findall(r"from\s+abc\s+import|ABC", code)),
            "num_public_methods": pub_m_count, "num_private_methods": len(priv_m),
            "num_protected_methods": len(prot_m), "num_methods": len(all_m),
            "num_public_fields": pub_f_count, "num_private_fields": len(priv_f),
            "num_protected_fields": len(prot_f), "num_fields": len(all_f),
            "inheritance_depth": min(len(re.findall(r"class\s+\w+\((\w+)\)", code)), 5),
            "polymorphism_factor": len(re.findall(r"super\(\)\.", code)),
            "encapsulation_ratio": round(private / total, 3) if total > 0 else 0,
        }

    @staticmethod
    def _empty() -> Dict:
        return {k: 0 for k in (
            "num_classes","num_interfaces","num_abstract_classes",
            "num_public_methods","num_private_methods","num_protected_methods","num_methods",
            "num_public_fields","num_private_fields","num_protected_fields","num_fields",
            "inheritance_depth","polymorphism_factor","encapsulation_ratio",
        )}
