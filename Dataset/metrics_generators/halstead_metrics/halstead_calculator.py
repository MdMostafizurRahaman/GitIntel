#!/usr/bin/env python3
"""
Halstead Metrics Calculator - Real implementation
Calculates all 5 Halstead complexity metrics from code
"""

import re
from pathlib import Path
from typing import Dict, Tuple
import math


class HalsteadCalculator:
    """Calculate Halstead complexity metrics from source code"""
    
    # Java keywords and operators
    JAVA_KEYWORDS = {
        'public', 'private', 'protected', 'static', 'final', 'synchronized',
        'class', 'interface', 'enum', 'extends', 'implements', 'new',
        'return', 'if', 'else', 'for', 'while', 'do', 'switch', 'case',
        'try', 'catch', 'finally', 'throw', 'throws', 'void', 'int', 'long'
    }
    
    JAVA_OPERATORS = {
        '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
        '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '++', '--',
        '+=', '-=', '*=', '/=', '%='
    }
    
    @staticmethod
    def calculate_from_file(file_path: str) -> Dict[str, float]:
        """
        Calculate all Halstead metrics from a source file
        
        Args:
            file_path: Path to source code file
            
        Returns:
            Dictionary with keys:
            - halstead_volume: Program volume
            - halstead_difficulty: Program difficulty
            - halstead_effort: Programming effort
            - halstead_time: Estimated programming time
            - halstead_bugs: Estimated defects
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract tokens
            operators, operands = HalsteadCalculator._extract_tokens(content)
            
            if not operators or not operands:
                return HalsteadCalculator._empty_metrics()
            
            # Calculate metrics
            n1 = len(set(operators))  # Distinct operators
            n2 = len(set(operands))   # Distinct operands
            N1 = len(operators)       # Total operators
            N2 = len(operands)        # Total operands
            
            # Halstead equations
            N = N1 + N2  # Program length
            n = n1 + n2  # Program vocabulary
            
            # Volume (bits needed to specify program)
            volume = N * math.log2(n) if n > 1 else 0
            
            # Difficulty (effort per statement)
            difficulty = (n1 / 2.0) * (N2 / n2) if n2 > 0 else 0
            
            # Effort (mental effort to write program)
            effort = difficulty * volume
            
            # Time (estimated programming time in seconds)
            time_seconds = effort / 18.0
            
            # Bugs (estimated bugs delivered)
            bugs = effort ** (2/3) / 3000
            
            return {
                'halstead_volume': round(volume, 2),
                'halstead_difficulty': round(difficulty, 2),
                'halstead_effort': round(effort, 2),
                'halstead_time': round(time_seconds, 2),
                'halstead_bugs': round(bugs, 2),
                'n1_distinct_operators': n1,
                'n2_distinct_operands': n2,
                'N1_total_operators': N1,
                'N2_total_operands': N2,
                'N_program_length': N,
                'n_vocabulary': n
            }
            
        except Exception as e:
            return HalsteadCalculator._empty_metrics()
    
    @staticmethod
    def _extract_tokens(content: str) -> Tuple[list, list]:
        """
        Extract operators and operands from code
        
        Returns:
            Tuple of (operators_list, operands_list)
        """
        operators = []
        operands = []
        
        # Remove comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'#.*?$', '', content, flags=re.MULTILINE)
        
        # Remove strings
        content = re.sub(r'"(?:\\.|[^"\\])*"', '', content)
        content = re.sub(r"'(?:\\.|[^'\\])*'", '', content)
        
        # Extract operators
        for op in sorted(HalsteadCalculator.JAVA_OPERATORS, key=len, reverse=True):
            for match in re.finditer(re.escape(op), content):
                operators.append(op)
        
        # Extract identifiers (variable/function names)
        for match in re.finditer(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content):
            word = match.group()
            if word not in HalsteadCalculator.JAVA_KEYWORDS:
                operands.append(word)
        
        # Extract numbers
        for match in re.finditer(r'\b\d+\b', content):
            operands.append(match.group())
        
        return operators, operands
    
    @staticmethod
    def _empty_metrics() -> Dict[str, float]:
        """Return empty metrics when calculation fails"""
        return {
            'halstead_volume': 0.0,
            'halstead_difficulty': 0.0,
            'halstead_effort': 0.0,
            'halstead_time': 0.0,
            'halstead_bugs': 0.0,
            'n1_distinct_operators': 0,
            'n2_distinct_operands': 0,
            'N1_total_operators': 0,
            'N2_total_operands': 0,
            'N_program_length': 0,
            'n_vocabulary': 0
        }
