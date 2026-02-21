#!/usr/bin/env python3
"""
IntegratedJurySystem — LLM-driven agentic dataset generator

Architecture
============
  Jury 1 (Claude via AWS Bedrock)  → Requirement Understanding + iterative clarification
  Jury 2 (Claude via AWS Bedrock)  → MetricsCatalog check + Python code synthesis
  All 3  (Claude via AWS Bedrock)  → Independent unit-test generation + validation
  Max 5 code-refinement retries before raising human_intervention_required
"""

import os
import sys
import json
import time
import uuid
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

# ── AWS Bedrock / Claude availability ────────────────────────────────────────
try:
    import boto3
    from botocore.exceptions import ClientError
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False
    boto3 = None

# ── Metrics catalog summary (built once at import time) ──────────────────────
_CATALOG_SUMMARY: Optional[str] = None


def _build_catalog_summary() -> str:
    try:
        root = Path(__file__).parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from metrics_catalog import MetricsCatalog
        metrics = MetricsCatalog.get_all_metrics()
        benchmarks = MetricsCatalog.get_benchmarks()

        lines = [f"METRICS ({len(metrics)} total):"]
        by_cat: Dict[str, List[str]] = {}
        for k, v in metrics.items():
            by_cat.setdefault(v["category"], []).append(k)
        for cat, keys in sorted(by_cat.items()):
            lines.append(f"  [{cat.upper()}]: {', '.join(keys)}")

        lines.append("\nBENCHMARKS:")
        for k, v in benchmarks.items():
            lines.append(f"  - {k}: {v['name']} — {v['description']}")
        return "\n".join(lines)
    except Exception as e:
        return f"(catalog unavailable: {e})"


def _get_catalog_summary() -> str:
    global _CATALOG_SUMMARY
    if _CATALOG_SUMMARY is None:
        _CATALOG_SUMMARY = _build_catalog_summary()
    return _CATALOG_SUMMARY


# ════════════════════════════════════════════════════════════════════════════
class IntegratedJurySystem:
    """
    Full agentic pipeline:
      Phase 1 — Jury 1  : understand + iteratively clarify the requirement
      Phase 2 — Jury 2  : check MetricsCatalog; call existing functions OR
                           synthesize clean Python code for custom metrics
      Phase 3 — All 3   : each generates unit tests independently → execute →
                           ≥2/3 LLMs must have ≥2/3 of their tests pass
      Retries — up to MAX_RETRIES; on exhaust → human_intervention_required
    """

    MAX_RETRIES = 5
    CONFIDENCE_THRESHOLD = 75   # % below which Jury 1 asks one more question

    # Claude model on AWS Bedrock (cross-region inference profile)
    _CLAUDE_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    _MAX_TOKENS = 8192

    # ── Construction ─────────────────────────────────────────────────────────
    def __init__(self):
        if not BEDROCK_AVAILABLE:
            raise ImportError(
                "boto3 is required for AWS Bedrock. "
                "Run: pip install boto3"
            )

        aws_key    = os.getenv("AWS_ACCESS_KEY_ID", "")
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not aws_key or not aws_secret:
            raise ValueError(
                "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not found in environment. "
                "Check .env"
            )

        self._bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
        )

        self.session_id = (
            f"jury_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"_{uuid.uuid4().hex[:6]}"
        )
        self.session_dir: Optional[str] = None
        self.repo_path: Optional[str] = None

        # Clarification state
        self._clarification_history: List[Dict] = []
        self._clarification_attempts: int = 0  # Track attempts to avoid infinite loops
        self._last_clarification_question: str = ""  # Track last question to detect duplicates
        self.MAX_CLARIFICATIONS: int = 3  # Cap at 3 clarification rounds

    # ── Public API ────────────────────────────────────────────────────────────

    def run_full_workflow(
        self,
        user_question: str,
        repo_path: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """
        Main entry point.
        Returns one of:
          {'status': 'needs_clarification', 'questions': [...], 'confidence': N, ...}
          {'status': 'success', 'code': '...', 'iterations': N, 'test_results': {...}, ...}
          {'status': 'human_intervention_required', 'message': '...', ...}
        """
        log = self._make_logger(progress_callback)

        # Initialise session directory
        base = Path(__file__).parent / "generated_datasets"
        base.mkdir(exist_ok=True)
        self.session_dir = str(base / self.session_id)
        Path(self.session_dir).mkdir(parents=True, exist_ok=True)
        self.repo_path = repo_path

        # Save original prompt
        try:
            Path(self.session_dir, "prompt.txt").write_text(
                user_question, encoding="utf-8"
            )
        except Exception:
            pass

        self._clarification_history = [{"role": "user", "content": user_question}]
        self._clarification_attempts = 0  # Reset for each workflow
        self._last_clarification_question = ""  # Reset for each workflow

        log("=" * 60)
        log("PHASE 1 — Requirement Understanding  (Jury 1 / Claude)")
        log("=" * 60)
        phase1 = self._phase1_understand_with_history(self._clarification_history)

        if phase1["status"] == "needs_clarification":
            return phase1  # GUI must call provide_clarification() next

        # Requirements are clear → run phases 2 + 3
        return self.resume_after_clarification(
            requirements=phase1["requirements"],
            confidence=phase1["confidence"],
            progress_callback=progress_callback,
        )

    def provide_clarification(self, user_feedback: str) -> Dict:
        """
        Called by the GUI when the user answers a clarifying question.
        Returns same shape as run_full_workflow.
        """
        self._clarification_attempts += 1
        self._clarification_history.append({"role": "user", "content": user_feedback})
        result = self._phase1_understand_with_history(self._clarification_history)
        return result

    def resume_after_clarification(
        self,
        requirements: Dict,
        confidence: float,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """Run phases 2 and 3 once requirements are fully understood."""
        log = self._make_logger(progress_callback)

        # Persist requirements to session dir
        if self.session_dir:
            req_path = Path(self.session_dir) / "requirements.json"
            req_path.write_text(json.dumps(requirements, indent=2), encoding="utf-8")

        # ── Phase 2: Generate code ─────────────────────────────────────────
        log("=" * 60)
        log("PHASE 2 — Catalog Check + Code Generation  (Jury 2 / Claude)")
        log("=" * 60)
        gen = self._phase2_generate(requirements, log)
        code = gen.get("code", "")
        log(f"  Type      : {gen.get('type', 'unknown')}")
        log(f"  Catalog   : {gen.get('catalog_calls', [])}")
        log(f"  Code size : {len(code)} chars")

        # ── Phase 3: Iterative test+validate loop ──────────────────────────
        log("=" * 60)
        log("PHASE 3 — Unit Test Generation + Validation  (3 × Claude)")
        log("=" * 60)

        iterations: List[Dict] = []
        final_code = code
        feedback: Optional[str] = None
        test_results: Dict = {}

        for attempt in range(1, self.MAX_RETRIES + 1):
            log(f"\n  Iteration {attempt}/{self.MAX_RETRIES}")

            if attempt > 1 and feedback:
                log("  Jury 2 refining code based on test failures...")
                refined = self._phase2_refine(requirements, final_code, feedback)
                final_code = refined.get("code", final_code)
                log(f"  Refined -> {len(final_code)} chars  ({refined.get('changes_made', '')})")

            log("  All 3 Claude instances generating + executing unit tests...")
            test_results = self._phase3_validate(final_code, requirements, log)

            iterations.append(
                {
                    "attempt": attempt,
                    "passed": test_results["total_passed"],
                    "total": test_results["total_tests"],
                    "passing_llms": test_results["passing_llms"],
                }
            )

            log(
                f"  Result : {test_results['passing_llms']}/3 passed  "
                f"({test_results['total_passed']}/{test_results['total_tests']} tests)"
            )

            if test_results["passing_llms"] >= 2:
                self._save_session(final_code, requirements, test_results, iterations, "success")
                log(f"\n  Code validated in {attempt} iteration(s)")
                return {
                    "status": "success",
                    "code": final_code,
                    "iterations": attempt,
                    "test_results": test_results,
                    "requirements": requirements,
                    "session_id": self.session_id,
                    "session_dir": self.session_dir,
                }

            feedback = test_results.get("failure_summary", "Tests failed — code needs fixing")
            log(f"  Failed: {feedback[:200]}")

        # Exhausted retries
        self._save_session(final_code, requirements, test_results, iterations, "failed")
        log(f"\n  FAILED after {self.MAX_RETRIES} iterations — human intervention required")
        return {
            "status": "human_intervention_required",
            "message": (
                f"Code could not be validated after {self.MAX_RETRIES} attempts.\n"
                f"Last run: {test_results.get('total_passed', 0)}/"
                f"{test_results.get('total_tests', 1)} tests passed.\n"
                f"Manual review of the generated code is required."
            ),
            "last_code": final_code,
            "last_feedback": feedback,
            "iterations": iterations,
            "session_id": self.session_id,
            "session_dir": self.session_dir,
        }

    # ── Phase 1: Jury 1 — Requirement Understanding ──────────────────────────

    def _phase1_understand_with_history(self, history: List[Dict]) -> Dict:
        """
        Jury 1 reads the full conversation and either:
          - Returns {'status': 'needs_clarification', 'questions': [...], ...}
          - Returns {'status': 'clarified',            'requirements': {...}, ...}

        NOTE: Caps clarifications at MAX_CLARIFICATIONS (~3 rounds) to avoid infinite loops.
        """
        # If we've asked too many clarification rounds, force acceptance of current understanding
        if self._clarification_attempts >= self.MAX_CLARIFICATIONS:
            return self._extract_requirements_from_history(history, allow_partial=True)

        conversation = "\n".join(
            f"{'USER' if h['role'] == 'user' else 'ASSISTANT'}: {h['content']}"
            for h in history
        )
        catalog = _get_catalog_summary()

        # Create a friendly list of example metrics and benchmarks for context
        example_metrics = [
            "cyclomatic_complexity", "cognitive_complexity", "lines_of_code",
            "maintainability_index", "code_duplication", "test_coverage",
            "commit_frequency", "code_churn", "function_length", "halstead_metrics"
        ]
        example_benchmarks = ["promise", "defects4j", "bugsjar","codexglue", "codesearchnet"]

        metrics_list = ", ".join(example_metrics)
        benchmarks_list = ", ".join(example_benchmarks)

        prompt = f"""You are Jury 1 — the Requirement Analyst for a software-engineering dataset generator.

EXAMPLE METRICS (in catalog):
{metrics_list}
(+ many more; see full catalog below)

EXAMPLE BENCHMARKS (pre-built datasets):
{benchmarks_list}
(+ 2 more: manystubs4j, sourcerer)

FULL AVAILABLE CATALOG:
{catalog}

CONVERSATION:
{conversation}

YOUR TASK:
1. Understand what dataset the user wants.
2. Decide if you have enough information (confidence ≥ {self.CONFIDENCE_THRESHOLD}%).
3. If NOT clear: ask exactly ONE concise clarifying question (must NOT be similar to previous questions in this conversation).
4. If CLEAR: return the structured requirement spec.

Return ONLY valid JSON (no markdown fences, no extra text):
{{
  "status": "needs_clarification" | "clear",
  "confidence": <0-100 integer>,
  "current_understanding": "<1-2 sentence summary of what you think the user wants>",
  "questions": ["<single clarifying question if status=needs_clarification, else empty list>"],
  "requirements": {{
    "goal": "<what dataset to generate, in plain English>",
    "metrics_needed": ["<exact metric key from catalog, e.g. cyclomatic_complexity>"],
    "benchmarks_needed": ["<exact benchmark key from catalog, e.g. promise, defects4j>"],
    "custom_metrics": [
      {{
        "name": "<metric name>",
        "description": "<what it measures>",
        "formula_hint": "<formula if user specified>"
      }}
    ],
    "output_format": "csv" | "json" | "jsonl",
    "repo_required": true | false,
    "language": "java" | "python" | "any",
    "notes": "<any other details>"
  }}
}}

RULES:
- status "needs_clarification" → questions list MUST have exactly 1 question; requirements MAY be partial.
- status "clear" → requirements MUST be fully filled; questions list MUST be empty.
- Use EXACT metric keys from the catalog (never invent names).
- Unknown / custom requests go under custom_metrics.
"""
        raw = self._call_llm(prompt, parse_json=True)

        if "error" in raw:
            # LLM call failed — ask a safe fallback question
            self._clarification_history.append({
                "role": "assistant",
                "content": "Please describe your requirement more clearly.",
            })
            return {
                "status": "needs_clarification",
                "confidence": 0,
                "current_understanding": "Could not parse the request.",
                "questions": [
                    "Could you describe more specifically what dataset or metric you want to create?"
                ],
            }

        status = raw.get("status", "needs_clarification")
        confidence = int(raw.get("confidence", 0))

        if status == "clear" and confidence >= self.CONFIDENCE_THRESHOLD:
            return {
                "status": "clarified",
                "confidence": confidence,
                "current_understanding": raw.get("current_understanding", ""),
                "requirements": raw.get("requirements", {}),
            }
        else:
            # Record assistant turn in history so next round has context
            questions = raw.get("questions") or ["Could you give more details?"]
            question_text = questions[0] if questions else "Could you give more details?"
            self._last_clarification_question = question_text  # Track for duplicate detection

            self._clarification_history.append({
                "role": "assistant",
                "content": (
                    raw.get("current_understanding", "") + "\n" + question_text
                ),
            })
            return {
                "status": "needs_clarification",
                "confidence": confidence,
                "current_understanding": raw.get("current_understanding", ""),
                "questions": [question_text],
            }

    def _extract_requirements_from_history(
        self, history: List[Dict], allow_partial: bool = False
    ) -> Dict:
        """
        Extract requirements from history when clarifications max out.
        Used to force termination of clarification loop after MAX_CLARIFICATIONS attempts.
        """
        conversation = "\n".join(
            f"{'USER' if h['role'] == 'user' else 'ASSISTANT'}: {h['content']}"
            for h in history
        )
        catalog = _get_catalog_summary()

        # Include context about available metrics and benchmarks
        example_metrics = [
            "cyclomatic_complexity", "cognitive_complexity", "lines_of_code",
            "maintainability_index", "code_duplication", "test coverage",
            "commit_frequency", "code_churn", "function_length", "halstead_metrics"
        ]
        example_benchmarks = ["promise", "defects4j", "bugsjar", "codexglue", "codesearchnet"]
        metrics_list = ", ".join(example_metrics)
        benchmarks_list = ", ".join(example_benchmarks)

        prompt = f"""You are Jury 1 — the Requirement Analyst. The user has been asked several clarifying questions,
and we've reached the maximum number of clarifications allowed.

AVAILABLE EXAMPLES:
Metrics: {metrics_list} (+ many more in full catalog)
Benchmarks: {benchmarks_list} (+ 2 more: manystubs4j, sourcerer)

NOW: Extract the BEST UNDERSTANDING of what they want from the conversation, even if not 100% clear:

CONVERSATION:
{conversation}

AVAILABLE CATALOG:
{catalog}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "status": "clear",
  "confidence": <estimated confidence 0-100>,
  "current_understanding": "<what we think they want based on conversation>",
  "questions": [],
  "requirements": {{
    "goal": "<best guess of what they want>",
    "metrics_needed": ["<metric keys from catalog>"],
    "benchmarks_needed": ["<benchmark keys>"],
    "custom_metrics": [],
    "output_format": "csv",
    "repo_required": true,
    "language": "any",
    "notes": "<anything that was unclear or assumed>"
  }}
}}
"""
        raw = self._call_llm(prompt, parse_json=True)

        if "error" in raw:
            raw = {
                "status": "clear",
                "confidence": 60,
                "current_understanding": conversation[:200],
                "questions": [],
                "requirements": {
                    "goal": "Generate dataset from repository",
                    "metrics_needed": [],
                    "benchmarks_needed": [],
                    "custom_metrics": [],
                    "output_format": "csv",
                    "repo_required": True,
                    "language": "any",
                    "notes": "Could not fully clarify requirements due to LLM error"
                }
            }

        return {
            "status": "clarified",
            "confidence": raw.get("confidence", 60),
            "current_understanding": raw.get("current_understanding", ""),
            "requirements": raw.get("requirements", {}),
        }

    # ── Phase 2: Jury 2 — Catalog Check + Code Generation ────────────────────

    def _phase2_generate(
        self, requirements: Dict, log: Callable[[str], None] = None
    ) -> Dict:
        """Jury 2 checks catalog then synthesises code."""
        if log is None:
            log = lambda _: None

        catalog = _get_catalog_summary()
        prompt = f"""You are Jury 2 — the Code Generator for a software-engineering dataset pipeline.

TASK: Generate a self-contained Python module that fulfils this requirement:
{json.dumps(requirements, indent=2)}

AVAILABLE CATALOG API (prefer these over writing from scratch):
{catalog}

Python API you must use:
  import sys, os; sys.path.insert(0, '<dataset_root>')
  from metrics_catalog import MetricsCatalog

  # All 64 metrics for a single file:
  MetricsCatalog.calculate_all_metrics(file_path: str, repo_path: str = None) -> dict

  # Specific categories:
  MetricsCatalog.calculate_loc_metrics(file_path)          # loc, cloc, bloc, soc
  MetricsCatalog.calculate_ck_metrics(file_path)            # wmc, dit, noc, cbo, rfc, lcom
  MetricsCatalog.calculate_complexity_metrics(file_path)   # cyclomatic, cognitive, ...

  # Benchmark generation:
  MetricsCatalog.generate_benchmark(
      benchmark_name: str,   # 'promise'|'defects4j'|'bugsjar'|
                              # 'codesearchnet'|'codexglue'|'manystubs4j'|'sourcerer'
      repo_path: str,
      output_dir: str = None,
      file_limit: int = None
  ) -> dict

CODE REQUIREMENTS:
1. The module MUST expose a function:
       def calculate(file_path: str, repo_path: str = None) -> dict
2. Always catch all exceptions — never crash.
3. Return dict with at minimum: {{"metrics": {{...}}, "benchmarks": {{...}}, "error": None}}
4. Keep the code clean, well-commented and importable.
5. Prefer catalog functions; only write custom logic for custom_metrics not in catalog.

Return ONLY valid JSON (no markdown fences):
{{
  "type": "catalog_only" | "catalog_plus_custom" | "fully_custom",
  "catalog_calls": ["<functions used>"],
  "code": "<complete Python module source code as a string — use \\n for newlines>",
  "description": "<one-sentence summary>"
}}
"""
        raw = self._call_llm(prompt, parse_json=True)

        if "error" in raw or "code" not in raw or not raw.get("code", "").strip():
            log("  Jury 2: LLM call failed — using fallback catalog wrapper")
            return {
                "type": "catalog_only",
                "catalog_calls": ["calculate_all_metrics"],
                "code": self._fallback_code(requirements),
                "description": "Auto-fallback: wraps MetricsCatalog.calculate_all_metrics",
            }

        return raw

    def _phase2_refine(
        self, requirements: Dict, current_code: str, feedback: str
    ) -> Dict:
        """Jury 2 fixes failing code given test-error feedback."""
        prompt = f"""You are Jury 2 — Code Refiner.

This Python code was generated but FAILED unit tests:

```python
{current_code}
```

TEST FAILURE FEEDBACK:
{feedback}

ORIGINAL REQUIREMENTS:
{json.dumps(requirements, indent=2)}

Fix the code so tests pass. Return ONLY valid JSON (no markdown fences):
{{
  "code": "<complete fixed Python module>",
  "changes_made": "<short description of what was fixed>"
}}
"""
        raw = self._call_llm(prompt, parse_json=True)
        if "error" in raw or "code" not in raw:
            return {"code": current_code, "changes_made": "no change (refine LLM failed)"}
        return raw

    def _fallback_code(self, requirements: Dict) -> str:
        """Minimal safe wrapper used when Jury 2 LLM call fails."""
        benchmarks = [
            b for b in requirements.get("benchmarks_needed", []) if b
        ]
        bench_block = ""
        if benchmarks:
            bench_block = (
                "    for _b in " + repr(benchmarks) + ":\n"
                "        try:\n"
                "            result['benchmarks'][_b] = MetricsCatalog.generate_benchmark(\n"
                "                benchmark_name=_b, repo_path=repo_path or '.'\n"
                "            )\n"
                "        except Exception as _e:\n"
                "            result['benchmarks'][_b] = {'error': str(_e)}\n"
            )

        return (
            "#!/usr/bin/env python3\n"
            '"""Auto-generated dataset calculator (fallback wrapper)"""\n'
            "import os, sys\n"
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
            "from metrics_catalog import MetricsCatalog\n\n"
            "def calculate(file_path: str, repo_path: str = None) -> dict:\n"
            "    result = {'metrics': {}, 'benchmarks': {}, 'error': None}\n"
            "    try:\n"
            "        result['metrics'] = MetricsCatalog.calculate_all_metrics(\n"
            "            file_path=file_path, repo_path=repo_path\n"
            "        )\n"
            + bench_block +
            "    except Exception as e:\n"
            "        result['error'] = str(e)\n"
            "    return result\n"
        )

    # ── Phase 3: All 3 — Unit Test Generation + Validation ───────────────────

    def _phase3_validate(
        self,
        code: str,
        requirements: Dict,
        log: Callable[[str], None],
    ) -> Dict:
        """
        Three independent Claude calls each generate unit tests → execute.
        A slot "passes" when ≥ 2/3 of its own tests pass.
        Returns summary dict.
        """
        # Three independent jury slots — all use same Bedrock client, different prompts
        jury_slots = ["Jury1", "Jury2", "Jury3"]

        passing_llms = 0
        total_passed = 0
        total_tests = 0
        all_failures: List[str] = []

        for jury_name in jury_slots:
            log(f"    {jury_name}: generating unit tests...")
            test_code = self._generate_tests(code, requirements, jury_name)
            if not test_code:
                log(f"    {jury_name}: test generation returned empty — counting as fail")
                all_failures.append(f"{jury_name}: test generation failed")
                total_tests += 1
                continue

            # Save this jury's test file to session directory
            if self.session_dir:
                try:
                    fname = f"jury{jury_slots.index(jury_name) + 1}_tests.py"
                    Path(self.session_dir, fname).write_text(test_code, encoding="utf-8")
                except Exception:
                    pass

            log(f"    {jury_name}: executing tests...")
            exec_res = self._run_tests(code, test_code)
            p = exec_res["passed"]
            t = exec_res["total"]
            total_passed += p
            total_tests += t

            log(f"    {jury_name}: {p}/{t} tests passed")

            # This jury "passes" if it achieved ≥2/3 of its own tests
            threshold = max(1, (t * 2 + 2) // 3)
            if p >= threshold:
                passing_llms += 1
            else:
                all_failures.append(
                    f"{jury_name} ({p}/{t} passed):\n"
                    + exec_res.get("output", "")[:600]
                )

        return {
            "passing_llms": passing_llms,
            "total_passed": total_passed,
            "total_tests": max(total_tests, 1),
            "failure_summary": "\n\n".join(all_failures),
        }

    def _generate_tests(
        self,
        code: str,
        requirements: Dict,
        jury_name: str,
    ) -> str:
        """One Claude call writes unittest code for the generated module."""
        prompt = f"""You are {jury_name} — an expert Python test writer.

Write unit tests using the standard `unittest` module for this Python code:

```python
{code}
```

Requirements the code should fulfil:
{json.dumps(requirements, indent=2)}

IMPORTANT: The module is available as `generated_metric`. You MUST import like this:
    from generated_metric import calculate

Your tests must:
1. Start with: from generated_metric import calculate
2. Call calculate(file_path, repo_path=None) — use __file__ as the file_path argument
3. Assert the return value is a dict
4. Assert there is no unhandled exception
5. Add at least 3 distinct test methods

Use ONLY `unittest` (no pytest, no third-party deps).

Return ONLY the raw Python test code — no markdown fences, no explanation:
"""
        raw = self._call_llm(prompt, parse_json=False)

        # Strip accidental markdown
        if "```python" in raw:
            raw = raw.split("```python")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        # Fix wrong module name: LLMs sometimes invent a different module name.
        # Replace any "from X import calculate" or "import X" (where X != generated_metric)
        # with the correct form.
        import re
        raw = re.sub(
            r'^from\s+(?!generated_metric)\w+\s+import\s+calculate\b',
            'from generated_metric import calculate',
            raw,
            flags=re.MULTILINE,
        )
        # Also handle standalone "import wrong_name" followed by "wrong_name.calculate"
        wrong_import = re.search(
            r'^import\s+(?!generated_metric|sys|os|unittest|json|re|ast|tempfile|pathlib)(\w+)',
            raw,
            flags=re.MULTILINE,
        )
        if wrong_import:
            wrong_name = wrong_import.group(1)
            raw = re.sub(rf'^import\s+{re.escape(wrong_name)}\b', '', raw, flags=re.MULTILINE)
            raw = re.sub(rf'\b{re.escape(wrong_name)}\.calculate\b', 'calculate', raw)
            # Ensure the correct import is present
            if 'from generated_metric import calculate' not in raw:
                raw = 'from generated_metric import calculate\n' + raw

        return raw

    def _run_tests(self, code: str, test_code: str) -> Dict:
        """
        Write module + tests to a temp directory and run via unittest.
        Parses stdout/stderr to count pass/fail.
        """
        import tempfile

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp = Path(tmp_dir)

                # Generated metric module
                (tmp / "generated_metric.py").write_text(code, encoding="utf-8")

                # Test file: prepend sys.path so it can import the module
                dataset_root = str(Path(__file__).parent)
                preamble = (
                    "import sys, os\n"
                    f"sys.path.insert(0, r'{tmp_dir}')\n"
                    f"sys.path.insert(0, r'{dataset_root}')\n"
                    "import generated_metric\n\n"
                )
                (tmp / "test_generated.py").write_text(
                    preamble + test_code, encoding="utf-8"
                )

                proc = subprocess.run(
                    [sys.executable, "-m", "unittest", "test_generated", "-v"],
                    cwd=str(tmp),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                output = proc.stdout + proc.stderr

                # unittest -v writes "test_xxx ... ok" or "test_xxx ... FAIL"
                passed = output.count(" ... ok")
                failed = output.count(" ... FAIL") + output.count(" ... ERROR")
                total = passed + failed
                if total == 0:
                    # Could not parse — check return code
                    total = 1
                    if proc.returncode != 0:
                        failed = 1
                    else:
                        passed = 1

                return {
                    "passed": passed,
                    "failed": failed,
                    "total": total,
                    "output": output if failed else "",
                }

        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 1,
                "total": 1,
                "output": "Test execution timed out (60 s)",
            }
        except Exception as exc:
            return {
                "passed": 0,
                "failed": 1,
                "total": 1,
                "output": str(exc),
            }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str, parse_json: bool = False):
        """Call Claude via AWS Bedrock; optionally parse JSON response."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self._MAX_TOKENS,
                    "messages": [{"role": "user", "content": prompt}],
                })
                response = self._bedrock.invoke_model(
                    modelId=self._CLAUDE_MODEL,
                    body=body,
                )
                result = json.loads(response["body"].read())
                text = result["content"][0]["text"].strip()

                if parse_json:
                    # Strip markdown fences if model added them
                    for fence in ("```json", "```"):
                        if fence in text:
                            text = text.split(fence)[1].split("```")[0].strip()
                            break
                    return json.loads(text)
                return text

            except json.JSONDecodeError as jde:
                if parse_json:
                    return {"error": f"JSON parse error: {jde}"}
                return f"[JSON parse error: {jde}]"
            except Exception as exc:
                err_str = str(exc)
                # Throttling: wait and retry
                if (
                    "ThrottlingException" in err_str
                    or "throttl" in err_str.lower()
                    or "Too Many Requests" in err_str
                ):
                    wait = 10 * (attempt + 1)
                    time.sleep(wait)
                    continue
                # Permanent error — return immediately
                if parse_json:
                    return {"error": err_str}
                return f"[LLM error: {err_str}]"

        # All retries exhausted
        if parse_json:
            return {"error": "Throttled: rate limit exceeded after retries"}
        return "[LLM error: throttled after retries]"

    @staticmethod
    def _make_logger(
        callback: Optional[Callable[[str], None]]
    ) -> Callable[[str], None]:
        if callback:
            return callback
        return print  # fallback: print to console

    def _save_session(
        self,
        code: str,
        requirements: Dict,
        test_results: Dict,
        iterations: List[Dict],
        status: str,
    ) -> None:
        """Persist final artefacts to session_dir."""
        if not self.session_dir:
            return
        try:
            sd = Path(self.session_dir)
            (sd / "generated_code.py").write_text(code, encoding="utf-8")
            summary = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "requirements": requirements,
                "iterations": iterations,
                "test_results": {
                    "passing_llms": test_results.get("passing_llms", 0),
                    "total_passed": test_results.get("total_passed", 0),
                    "total_tests": test_results.get("total_tests", 0),
                },
            }
            (sd / "session_summary.json").write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
# Quick smoke-test
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")

    jury = IntegratedJurySystem()
    print(f"Session : {jury.session_id}")
    print(f"Model   : {jury._CLAUDE_MODEL}")

    result = jury.run_full_workflow(
        user_question="Calculate cyclomatic complexity and LCOM for Java files",
        progress_callback=print,
    )
    print(json.dumps(result, indent=2, default=str))
