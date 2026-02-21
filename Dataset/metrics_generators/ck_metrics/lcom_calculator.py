#!/usr/bin/env python3
"""LCOM (Lack of Cohesion of Methods) Calculator
Implements Chidamber & Kemerer (1994) LCOM1 definition:
  P = count of method pairs that share NO instance fields
  Q = count of method pairs that share AT LEAST ONE instance field
  LCOM1 = max(0, P - Q)
"""
import re
from typing import List, Set
from metrics_generators.shared_utils import FileReader


class LCOMCalculator:

    # Regex to find instance field names (non-static private/protected/public fields)
    _FIELD_DECL_RE = re.compile(
        r'\b(?:private|protected|public)\s+'
        r'(?:(?:final|volatile|transient)\s+)*'   # optional non-static modifiers
        r'(?!static\b)'                             # exclude static fields
        r'[\w<>\[\].,? ]+\s+'
        r'(\w+)\s*[;=,)]',
        re.MULTILINE,
    )

    # Also handle: private int x, y; (multiple declarators on one line)
    _MULTI_DECL_RE = re.compile(
        r'\b(?:private|protected|public)\s+'
        r'(?:(?:final|volatile|transient)\s+)*'
        r'[\w<>\[\].,? ]+\s+'
        r'(\w+)(?:\s*,\s*(\w+))*\s*;',
        re.MULTILINE,
    )

    @staticmethod
    def _extract_field_names(content: str) -> Set[str]:
        """Return set of instance field names declared in the source."""
        fields: Set[str] = set()
        # Remove string literals & comments first to avoid false matches
        clean = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)
        clean = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', clean)

        for m in LCOMCalculator._FIELD_DECL_RE.finditer(clean):
            name = m.group(1)
            if name and not name[0].isupper():   # skip class-type names
                fields.add(name)
        return fields

    @staticmethod
    def _extract_method_bodies(content: str) -> List[str]:
        """Return list of raw method body strings using brace matching."""
        bodies: List[str] = []
        # Find potential method entry points (modifier + return type + name + params + {)
        method_start_re = re.compile(
            r'\b(?:public|private|protected)\s+'
            r'(?:(?:static|final|synchronized|abstract|native|strictfp)\s+)*'
            r'[\w<>\[\].,?]+\s+'
            r'\w+\s*\([^)]*\)\s*'
            r'(?:throws\s+[\w\s,]+)?\s*\{',
            re.MULTILINE | re.DOTALL,
        )
        for m in method_start_re.finditer(content):
            start = m.end() - 1   # position of '{'
            depth = 0
            i = start
            while i < len(content):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        bodies.append(content[start:i + 1])
                        break
                i += 1
        return bodies

    @staticmethod
    def calculate_from_file(file_path: str) -> float:
        """
        Compute LCOM1 per Chidamber & Kemerer (1994):
          LCOM1 = max(0, P - Q)
        where P = pairs of methods with no shared instance fields,
              Q = pairs of methods sharing >= 1 instance field.
        Returns 0.0 for trivially cohesive or unanalysable classes.
        """
        try:
            content = FileReader.read(file_path)

            fields = LCOMCalculator._extract_field_names(content)
            if not fields:
                return 0.0   # no instance fields → trivially cohesive

            method_bodies = LCOMCalculator._extract_method_bodies(content)
            if len(method_bodies) <= 1:
                return 0.0   # 0 or 1 method → LCOM undefined, return 0

            # For each method body, find which declared fields it references
            method_field_sets: List[Set[str]] = []
            for body in method_bodies:
                used: Set[str] = set()
                # Remove string literals from body to avoid matching field names in strings
                clean_body = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', body)
                for field in fields:
                    if re.search(r'\b' + re.escape(field) + r'\b', clean_body):
                        used.add(field)
                method_field_sets.append(used)

            # Count P (disjoint pairs) and Q (overlapping pairs)
            P = Q = 0
            n = len(method_field_sets)
            for i in range(n):
                for j in range(i + 1, n):
                    if method_field_sets[i].isdisjoint(method_field_sets[j]):
                        P += 1
                    else:
                        Q += 1

            return float(max(0, P - Q))

        except Exception:
            return 0.0
