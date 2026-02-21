#!/usr/bin/env python3
"""Halstead Metrics Calculator - volume, difficulty, effort, time, bugs"""
import re, math
from typing import Dict, Tuple
from metrics_generators.shared_utils import FileReader


class HalsteadCalculator:
    JAVA_KEYWORDS = {
        "public","private","protected","static","final","synchronized",
        "class","interface","enum","extends","implements","new","return",
        "if","else","for","while","do","switch","case","try","catch",
        "finally","throw","throws","void","int","long",
    }
    JAVA_OPERATORS = {
        "+","-","*","/","%","=","==","!=","<",">","<=",">=",
        "&&","||","!","&","|","^","~","<<",">>","++","--",
        "+=","-=","*=","/=","%=",
    }

    @staticmethod
    def calculate_from_file(file_path: str) -> Dict[str, float]:
        try:
            content = FileReader.read(file_path)
            operators, operands = HalsteadCalculator._extract_tokens(content)
            if not operators or not operands:
                return HalsteadCalculator._empty()
            n1, n2 = len(set(operators)), len(set(operands))
            N1, N2 = len(operators), len(operands)
            N, n = N1 + N2, n1 + n2
            volume = N * math.log2(n) if n > 1 else 0
            difficulty = (n1 / 2.0) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
            return {
                "halstead_volume":     round(volume, 2),
                "halstead_difficulty": round(difficulty, 2),
                "halstead_effort":     round(effort, 2),
                "halstead_time":       round(effort / 18.0, 2),
                "halstead_bugs":       round(effort ** (2/3) / 3000, 2),
                "n1_distinct_operators": n1, "n2_distinct_operands": n2,
                "N1_total_operators": N1,    "N2_total_operands": N2,
                "N_program_length": N,       "n_vocabulary": n,
            }
        except Exception:
            return HalsteadCalculator._empty()

    @staticmethod
    def _extract_tokens(content: str) -> Tuple[list, list]:
        content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        content = re.sub(r"#.*?$", "", content, flags=re.MULTILINE)
        content = re.sub(r"\"(?:\\.|[^\"\\])*\"", "", content)
        content = re.sub(r"'(?:\\.|[^'\\])*'", "", content)
        operators = [op for op in sorted(HalsteadCalculator.JAVA_OPERATORS, key=len, reverse=True)
                     for _ in re.finditer(re.escape(op), content)]
        operands  = [m.group() for m in re.finditer(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)
                     if m.group() not in HalsteadCalculator.JAVA_KEYWORDS]
        operands += [m.group() for m in re.finditer(r"\b\d+\b", content)]
        return operators, operands

    @staticmethod
    def _empty() -> Dict[str, float]:
        return {k: 0.0 for k in (
            "halstead_volume","halstead_difficulty","halstead_effort",
            "halstead_time","halstead_bugs",
            "n1_distinct_operators","n2_distinct_operands",
            "N1_total_operators","N2_total_operands","N_program_length","n_vocabulary",
        )}
