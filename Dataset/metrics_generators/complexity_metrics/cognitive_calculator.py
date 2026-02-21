#!/usr/bin/env python3
"""Cognitive Complexity Calculator
Implements SonarSource Cognitive Complexity (G. Ann Campbell, 2016/2018):
  - Each control structure adds +1 base + current nesting depth
  - else/else-if adds flat +1 (no nesting penalty)
  - switch adds flat +1 (not penalised per case)
  - try adds nesting depth but no score
  - catch adds +1 + nesting depth
  - Nesting depth increments when entering loops, if/else-if, switch, catch bodies
"""
import javalang
import ast
from typing import Dict
from metrics_generators.shared_utils import JavaAST, PythonAST


class CognitiveComplexityCalculator:

    @staticmethod
    def calculate_from_java_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree, _ = JavaAST.parse_file(file_path)
        if tree is None:
            return results
        for _, method in tree.filter(javalang.tree.MethodDeclaration):
            body = method.body or []
            results[method.name] = CognitiveComplexityCalculator._java_cognitive(body, 0)
        return results

    @staticmethod
    def _java_cognitive(stmts, nesting: int) -> int:
        """
        Recursively compute cognitive complexity for a list of statements.

        Rules (SonarSource spec):
          if            -> +1 + nesting, then-body at nesting+1
          else-if       -> +1 flat,      processed at same nesting
          else          -> +1 flat,      else-body at nesting+1
          while/for/do  -> +1 + nesting, body at nesting+1
          switch        -> +1 flat,      case bodies at nesting+1
          try           -> 0,            block at nesting+1
          catch         -> +1 + nesting, block at nesting+1
        """
        if stmts is None:
            return 0

        score = 0
        items = stmts if isinstance(stmts, list) else [stmts]

        for node in items:
            if node is None:
                continue

            # --- If / else-if / else ---
            if isinstance(node, javalang.tree.IfStatement):
                score += 1 + nesting
                score += CognitiveComplexityCalculator._java_cognitive(
                    node.then_statement, nesting + 1)
                else_stmt = getattr(node, 'else_statement', None)
                if else_stmt is not None:
                    if isinstance(else_stmt, javalang.tree.IfStatement):
                        # else-if: flat +1, process nested if at same nesting level
                        score += 1
                        score += CognitiveComplexityCalculator._java_cognitive(
                            else_stmt, nesting)
                    else:
                        # plain else: flat +1, body at nesting+1
                        score += 1
                        score += CognitiveComplexityCalculator._java_cognitive(
                            else_stmt, nesting + 1)

            # --- While / do-while ---
            elif isinstance(node, (javalang.tree.WhileStatement,
                                   javalang.tree.DoStatement)):
                score += 1 + nesting
                score += CognitiveComplexityCalculator._java_cognitive(
                    getattr(node, 'body', None), nesting + 1)

            # --- for / enhanced for (same ForStatement node in javalang) ---
            elif isinstance(node, javalang.tree.ForStatement):
                score += 1 + nesting
                score += CognitiveComplexityCalculator._java_cognitive(
                    getattr(node, 'body', None), nesting + 1)

            # --- switch (flat +1 for the entire construct) ---
            elif isinstance(node, javalang.tree.SwitchStatement):
                score += 1   # flat — no nesting penalty for switch itself
                for case in (getattr(node, 'cases', None) or []):
                    score += CognitiveComplexityCalculator._java_cognitive(
                        getattr(case, 'statements', None) or [], nesting + 1)

            # --- try (no score; increases nesting) / catch (+1+nesting) ---
            elif isinstance(node, javalang.tree.TryStatement):
                # try block: nesting+1 but no score contribution
                score += CognitiveComplexityCalculator._java_cognitive(
                    getattr(node, 'block', None) or [], nesting + 1)
                for catch in (getattr(node, 'catches', None) or []):
                    score += 1 + nesting
                    score += CognitiveComplexityCalculator._java_cognitive(
                        getattr(catch, 'block', None) or [], nesting + 1)

            # --- Other compound statements: recurse without changing nesting ---
            else:
                for attr_name in ('block', 'statements', 'body'):
                    child = getattr(node, attr_name, None)
                    if child is not None:
                        score += CognitiveComplexityCalculator._java_cognitive(
                            child, nesting)

        return score

    # ------------------------------------------------------------------ Python
    @staticmethod
    def calculate_from_python_file(file_path: str) -> Dict[str, int]:
        results = {}
        tree = PythonAST.parse_file(file_path)
        if tree is None:
            return results
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                results[node.name] = CognitiveComplexityCalculator._python_cognitive(
                    node.body, 0)
        return results

    @staticmethod
    def _python_cognitive(stmts, nesting: int) -> int:
        """Python cognitive complexity with proper nesting tracking."""
        if not stmts:
            return 0
        score = 0
        items = stmts if isinstance(stmts, list) else [stmts]

        for node in items:
            if isinstance(node, ast.If):
                score += 1 + nesting
                score += CognitiveComplexityCalculator._python_cognitive(
                    node.body, nesting + 1)
                if node.orelse:
                    if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                        # elif: flat +1, same nesting level
                        score += 1
                        score += CognitiveComplexityCalculator._python_cognitive(
                            node.orelse, nesting)
                    else:
                        # else: flat +1
                        score += 1
                        score += CognitiveComplexityCalculator._python_cognitive(
                            node.orelse, nesting + 1)

            elif isinstance(node, (ast.While, ast.For)):
                score += 1 + nesting
                score += CognitiveComplexityCalculator._python_cognitive(
                    node.body, nesting + 1)

            elif isinstance(node, ast.Try):
                # try body increases nesting but no score
                score += CognitiveComplexityCalculator._python_cognitive(
                    node.body, nesting + 1)
                for handler in node.handlers:
                    score += 1 + nesting
                    score += CognitiveComplexityCalculator._python_cognitive(
                        handler.body, nesting + 1)

        return score
