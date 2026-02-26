"""ChatMixin — agentic chat, intelligent request processor, agent query."""
import tkinter as tk
import threading
import os
import re
import json
import traceback
import pandas as pd
from typing import Dict

# Gemini removed — using IntegratedJurySystem exclusively

try:
    from .gui_types import MessageType
except ImportError:
    from gui_types import MessageType

try:
    from metrics_catalog import MetricsCatalog
except ImportError:
    MetricsCatalog = None

try:
    from autonomous_agent import AgentMode
except ImportError:
    AgentMode = None


class ChatMixin:
    def process_chat_input(self):
        """
        MAIN ENTRY POINT: Process chat input from unified interface
        Handles ALL user requirements:
        1. Repository path/link check
        2. Metric selection from 65+ catalog
        3. Natural language query interpretation
        4. LLM jury process for unknown metrics
        5. User approval workflow
        6. Real data generation (no mock)
        7. Visualization & feedback
        """
        query = self.unified_input_var.get().strip()
        
        if not query or 'Type:' in query:
            return
        
        # Show user message
        self.add_agent_message(MessageType.USER, f"{query}")
        self.unified_input_var.set("")
        self.current_query = query
        
        # Step 1: Check repository is set
        if not self.repo_path:
            self.add_agent_message(MessageType.ERROR, 
                "**Repository not set!**\n\n"
                "Please set a repository first:\n"
                "1. Enter path or GitHub URL above\n"
                "2. Click 'Set Repository'\n"
                "3. Then ask your question again")
            return
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query})

        # ── Primary path: IntegratedJurySystem (Jurry_1/2/3 keys) ──────────
        if self.integrated_jury:
            self._chat_jury_in_session = False   # fresh session
            self.add_agent_message(
                MessageType.INFO,
                "Task plan ready \u2014 click  [Start]  to begin the Jury workflow.",
            )
            self._populate_jury_task_plan()
            self.start_btn.config(
                state=tk.NORMAL,
                command=lambda q=query: self._start_jury_from_plan(q),
            )

        # ── Fallback: EnhancedAgenticSystem (Bedrock) ───────────────────────
        elif self.enhanced_system:
            threading.Thread(
                target=self._process_with_enhanced_system,
                args=(query,),
                daemon=True,
            ).start()

        else:
            self.add_agent_message(
                MessageType.ERROR,
                "No AI system initialised.\n"
                "Check that Jurry_1, Jurry_2, Jurry_3 keys are set in .env",
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # INTEGRATED JURY SYSTEM — MAIN CHAT THREADS
    # These back the primary agentic workflow triggered from process_chat_input.
    # ═══════════════════════════════════════════════════════════════════════════

    def _jury_chat_start_thread(self, query: str):
        """
        Background thread: start a fresh IntegratedJurySystem workflow.
        Jury 1 understands the requirement; if clear → Jury 2 + All-3 run.
        If Jury 1 needs clarification → result is surfaced to the user.
        """
        def progress(msg):
            self.root.after(0, lambda m=msg: self.add_agent_message(MessageType.THINKING, m))

        try:
            result = self.integrated_jury.run_full_workflow(
                user_question=query,
                repo_path=self.repo_path,
                progress_callback=progress,
            )
            self.root.after(0, lambda r=result: self._handle_jury_chat_result(r))
        except Exception as exc:
            err = str(exc)
            self.root.after(0, lambda e=err: self.add_agent_message(
                MessageType.ERROR, f"Jury workflow error: {e}"
            ))

    def _jury_chat_clarification_thread(self, user_feedback: str):
        """
        Background thread: relay user's clarification answer to Jury 1.
        Continues full workflow when requirements are clear.
        """
        def progress(msg):
            self.root.after(0, lambda m=msg: self.add_agent_message(MessageType.THINKING, m))

        try:
            result = self.integrated_jury.provide_clarification(user_feedback)

            if result["status"] == "clarified":
                # Requirements now clear → route through _handle_jury_chat_result
                # (which will show confirmation before starting code generation)
                self.root.after(0, lambda r=result: self._handle_jury_chat_result(r))
            else:
                self.root.after(0, lambda r=result: self._handle_jury_chat_result(r))

        except Exception as exc:
            err = str(exc)
            self.root.after(0, lambda e=err: self.add_agent_message(
                MessageType.ERROR, f"Jury clarification error: {e}"
            ))

    def _jury_chat_resume_thread(self, requirements: Dict, confidence: float):
        """
        Background thread: run phases 2+3 after requirement is confirmed.
        """
        def progress(msg):
            self.root.after(0, lambda m=msg: self.add_agent_message(MessageType.THINKING, m))

        try:
            result = self.integrated_jury.resume_after_clarification(
                requirements=requirements,
                confidence=confidence,
                progress_callback=progress,
            )
            self.root.after(0, lambda r=result: self._handle_jury_chat_result(r))
        except Exception as exc:
            err = str(exc)
            self.root.after(0, lambda e=err: self.add_agent_message(
                MessageType.ERROR, f"Jury generation error: {e}"
            ))

    def _handle_jury_chat_result(self, result: Dict):
        """
        Handle the dict returned by IntegratedJurySystem from the main chat panel.
        Dispatches to clarification / success / human-intervention display.
        """
        status = result.get("status")

        if status == "needs_clarification":
            # Jury 1 is asking a clarifying question
            questions = result.get("questions", ["Could you give more details?"])
            understanding = result.get("current_understanding", "")
            confidence = result.get("confidence", 0)

            question_block = "\n".join(f"  • {q}" for q in questions)
            self.add_agent_message(
                MessageType.QUESTION,
                f"I need a bit more information (confidence: {confidence}%):\n\n"
                f"{question_block}\n\n"
                f"Current understanding: {understanding}\n\n"
                "Please type your answer in the Feedback box below and click Send.",
            )
            # Mark that the next feedback should go to jury clarification
            self._chat_jury_in_session = True

        elif status == "clarified":
            # Jury 1 now understands — show breakdown + ask confirmation before code gen
            reqs = result["requirements"]
            conf = result.get("confidence", 100)
            goal = reqs.get('goal', '')
            metrics_needed  = reqs.get('metrics_needed', [])
            custom_metrics  = reqs.get('custom_metrics', [])   # derived/formula outputs
            fmt = reqs.get('output_format', 'csv')

            # Classify INPUT metrics as catalog-known vs truly unknown
            known_metrics   = []
            unknown_metrics = []
            if MetricsCatalog and metrics_needed:
                try:
                    catalog_keys = set(MetricsCatalog.get_all_metrics().keys())
                    for m in metrics_needed:
                        (known_metrics if m in catalog_keys else unknown_metrics).append(m)
                except Exception:
                    known_metrics = list(metrics_needed)
            else:
                known_metrics = list(metrics_needed)

            # Build the metrics display block
            all_input = ', '.join(metrics_needed) if metrics_needed else 'none'
            catalog_line = (
                f"  Catalog  ({len(known_metrics)} available) : "
                f"{', '.join(known_metrics) if known_metrics else 'none'}"
            )
            unknown_line = (
                f"\n  Unknown  ({len(unknown_metrics)} to synthesize) : "
                f"{', '.join(unknown_metrics)}"
            ) if unknown_metrics else ""
            formula_line = (
                f"\n  Formula  ({len(custom_metrics)} derived) : "
                f"{', '.join(custom_metrics)}"
                f"\n            → Jury 2 will generate code for these"
            ) if custom_metrics else ""

            self.add_agent_message(
                MessageType.INFO,
                f"Requirement understood ({conf}% confidence).\n\n"
                f"  Goal    : {goal}\n"
                f"  Inputs  : {all_input}\n"
                f"{catalog_line}{unknown_line}{formula_line}\n"
                f"  Format  : {fmt}\n\n"
                "Click  [Confirm]  to start code generation, or  [Cancel]  to stop.",
            )
            self._jury_chat_requirements = reqs
            self._jury_pending_requirements = (reqs, conf)
            self._update_plan_step("1", "done")
            self._update_plan_step("2", "active")
            self.confirm_label.config(text="Proceed with code generation (Jury 2)?")
            self.confirm_yes_btn.config(command=self._confirm_cp1_yes)
            self.confirm_no_btn.config(command=self._confirm_cp1_no)
            self.set_approval_visible(True)

        elif status == "success":
            code = result.get("code", "")
            iters = result.get("iterations", 1)
            tr = result.get("test_results", {})
            session_dir = result.get("session_dir", "N/A")
            token_usage = result.get("token_usage", {})
            # Store so _apply_jury_code_thread can save CSV to the right directory
            self._last_jury_session_dir = session_dir

            self.add_agent_message(
                MessageType.SUCCESS,
                f"Code generated and validated!\n\n"
                f"  Iterations   : {iters}/{self.integrated_jury.MAX_RETRIES}\n"
                f"  LLMs passed  : {tr.get('passing_llms', 0)}/3\n"
                f"  Tests passed : {tr.get('total_passed', 0)}/{tr.get('total_tests', 0)}\n\n"
                f"  Session saved to:\n  {session_dir}",
                actions=[
                    {
                        'label': 'Open Session Folder',
                        'callback': lambda p=session_dir: os.startfile(p) if os.path.exists(str(p)) else None,
                    },
                    {
                        'label': 'Token Usage',
                        'callback': lambda tu=token_usage: self._show_token_usage_popup(tu),
                    },
                ],
            )
            self._update_plan_step("2", "done")
            self._update_plan_step("3", "done")

            # Update status bar / output path
            self.output_path_var.set(f"Output: {session_dir}")
            self.status_var.set(f"Validated \u2014 {iters} iteration(s)")

            # Apply the validated code to generate the actual dataset — auto-start,
            # no second confirmation needed (user already confirmed at step 1).
            if code and self.repo_path:
                reqs = result.get("requirements", {})
                self._jury_pending_code = (code, reqs)
                self._last_jury_session_dir = session_dir
                self._update_plan_step("4", "active")
                fmt = (reqs.get("output_format") or "csv").upper()
                self.add_agent_message(
                    MessageType.THINKING,
                    f"Starting dataset application — generating {fmt} from repository…\n"
                    f"This may take a few minutes for large repos.",
                )
                import threading as _t
                _t.Thread(
                    target=self._apply_jury_code_thread,
                    args=(code, reqs),
                    daemon=True,
                ).start()
            elif code:
                # No repo — show the code for manual use
                preview = code[:600] + ("\n\u2026(truncated)" if len(code) > 600 else "")
                self.add_agent_message(
                    MessageType.INFO,
                    f"Generated code preview:\n\n{preview}\n\n"
                    f"Full code saved to: {session_dir}/generated_code.py",
                )
                self._update_plan_step("4", "done")

        elif status == "human_intervention_required":
            last_code_preview = (result.get("last_code") or "")[:400]
            self.add_agent_message(
                MessageType.ERROR,
                f"Could not validate after {self.integrated_jury.MAX_RETRIES} attempts.\n\n"
                f"{result.get('message', '')}\n\n"
                f"Session saved to: {result.get('session_dir', 'N/A')}\n"
                f"Please review generated_code.py in that folder.\n\n"
                f"Last generated code (preview):\n{last_code_preview}",
            )
        else:
            self.add_agent_message(
                MessageType.ERROR, f"Unexpected jury status: {status}"
            )

    def _show_token_usage_popup(self, token_usage: dict, is_ai_generation: bool = True):
        """Show a popup window with actual token usage broken down by algorithm phase."""
        C = self.colors

        phase_labels = {
            "phase1": "Phase 1  Requirement Understanding  (Jury 1)",
            "phase2": "Phase 2  Code Generation  (Jury 2)",
            "phase3": "Phase 3  Test Validation  (3× Claude)",
        }

        rows = []
        grand_in = grand_out = 0
        for key, label in phase_labels.items():
            counts = token_usage.get(key, {"input": 0, "output": 0})
            inp = counts.get("input",  0)
            out = counts.get("output", 0)
            grand_in  += inp
            grand_out += out
            rows.append((label, inp, out, inp + out))

        grand_total = grand_in + grand_out

        popup = tk.Toplevel(self.root)
        popup.title("Actual Token Usage — Dataset Generation")
        popup.configure(bg=C['bg'])
        popup.resizable(False, False)
        popup.grab_set()

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(popup, bg=C['topbar'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Actual Token Usage  —  This Generation Run",
                 font=('Segoe UI', 11, 'bold'),
                 fg=C['topbar_fg'], bg=C['topbar']).pack(
            side=tk.LEFT, padx=12, pady=8)

        # ── AI / No-AI badge ──────────────────────────────────────────────
        if not is_ai_generation:
            badge_text = "Benchmark / Metrics  —  No Claude AI used"
            badge_color = '#f78166'
        else:
            badge_text = "Jury System  —  Claude 3.5 Sonnet via AWS Bedrock"
            badge_color = '#57ab5a'
        tk.Label(popup, text=badge_text,
                 font=('Segoe UI', 8, 'bold'), fg=badge_color, bg=C['bg']).pack(
            anchor=tk.W, padx=14, pady=(8, 0))

        # ── Table ─────────────────────────────────────────────────────────
        tbl = tk.Frame(popup, bg=C['panel'], padx=14, pady=10)
        tbl.pack(fill=tk.X, padx=12, pady=(6, 0))

        col_hdrs = [
            ("Algorithm / Phase",    36, tk.W),
            ("Input Tokens",         13, tk.E),
            ("Output Tokens",        13, tk.E),
            ("Total",                10, tk.E),
        ]
        for col, (htext, width, anchor) in enumerate(col_hdrs):
            tk.Label(tbl, text=htext, width=width, anchor=anchor,
                     font=('Segoe UI', 9, 'bold'),
                     fg='black', bg=C['panel']).grid(
                row=0, column=col, padx=(0, 6), pady=(0, 4), sticky=anchor)

        tk.Frame(tbl, bg=C['border'], height=1).grid(
            row=1, column=0, columnspan=4, sticky='ew', pady=(0, 6))

        # phase labels and all values in table should be bold black
        for r_idx, (phase, inp, out, tot) in enumerate(rows, start=2):
            tk.Label(tbl, text=phase, width=36, anchor=tk.W,
                     font=('Segoe UI', 9, 'bold'), fg='black',
                     bg=C['panel']).grid(row=r_idx, column=0,
                                          padx=(0, 6), pady=2, sticky=tk.W)
            for col_idx, val in enumerate((inp, out, tot), start=1):
                tk.Label(tbl, text=f"{val:,}", width=[13, 13, 10][col_idx - 1],
                         anchor=tk.E, font=('Consolas', 9, 'bold'), fg='black',
                         bg=C['panel']).grid(row=r_idx, column=col_idx,
                                              padx=(0, 6), pady=2, sticky=tk.E)

        # ── Total row ─────────────────────────────────────────────────────
        sep_row = len(rows) + 2
        tk.Frame(tbl, bg=C['border'], height=1).grid(
            row=sep_row, column=0, columnspan=4, sticky='ew', pady=(6, 4))

        tk.Label(tbl, text="TOTAL USED  (LLM only)", width=36, anchor=tk.W,
                 font=('Segoe UI', 9, 'bold'), fg='black',
                 bg=C['panel']).grid(row=sep_row + 1, column=0,
                                      padx=(0, 6), pady=2, sticky=tk.W)
        # total row values also bold black
        for col_idx, val in enumerate((grand_in, grand_out, grand_total), start=1):
            tk.Label(tbl, text=f"{val:,}", width=[13, 13, 10][col_idx - 1],
                     anchor=tk.E, font=('Consolas', 10, 'bold'), fg='black',
                     bg=C['panel']).grid(row=sep_row + 1, column=col_idx,
                                          padx=(0, 6), pady=2, sticky=tk.E)

        # ── Note ──────────────────────────────────────────────────────────
        if not is_ai_generation:
            note = (
                "This generation used a standard benchmark / metrics algorithm.\n"
                "No Claude AI calls were made — token usage is 0.\n"
                "Token usage is only non-zero when the Jury System generates\n"
                "custom metrics via the chat interface."
            )
        elif grand_total == 0:
            note = (
                "No token data captured. The generation may not have reached Phase 2.\n"
                "Token counts are read from the AWS Bedrock response usage field."
            )
        else:
            note = (
                "Token counts are read directly from the AWS Bedrock response\n"
                "usage field (input_tokens + output_tokens per API call).\n"
                "Phase 2 includes all code-generation and refinement iterations.\n"
                "Phase 4 runs the generated code locally — no LLM, not counted."
            )
        tk.Label(popup, text=note,
                 font=('Segoe UI', 8), fg=C['fg_muted'], bg=C['bg'],
                 justify=tk.LEFT, wraplength=500).pack(
            anchor=tk.W, padx=14, pady=(8, 4))

        # ── Close button ──────────────────────────────────────────────────
        tk.Button(popup, text="Close",
                  font=('Segoe UI', 9, 'bold'),
                  bg=C['accent'], fg='white',
                  relief='flat', cursor='hand2',
                  activebackground=C['accent_hover'],
                  command=popup.destroy).pack(pady=(4, 12), ipadx=16, ipady=4)

    def _extract_author_stats_fallback(self, repo_path: str) -> dict:
        """
        Correct GitPython author stats extractor.
        Uses commit.stats.total (correct) instead of diff.stats (non-existent).
        """
        try:
            import git
            from datetime import timezone
            repo = git.Repo(repo_path)
            stats = {}
            for commit in repo.iter_commits():
                author = commit.author.email
                dt = commit.committed_datetime
                # Normalise to offset-aware for comparison
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if author not in stats:
                    stats[author] = {
                        'num_commits': 0,
                        'first_commit': dt,
                        'last_commit': dt,
                        'loc_added': 0,
                        'loc_deleted': 0,
                    }
                stats[author]['num_commits'] += 1
                if dt < stats[author]['first_commit']:
                    stats[author]['first_commit'] = dt
                if dt > stats[author]['last_commit']:
                    stats[author]['last_commit'] = dt
                # commit.stats.total is the correct GitPython API
                try:
                    stats[author]['loc_added']   += commit.stats.total.get('insertions', 0)
                    stats[author]['loc_deleted']  += commit.stats.total.get('deletions', 0)
                except Exception:
                    pass
            return stats
        except Exception as e:
            print(f"Author stats fallback error: {e}")
            return {}

    def _apply_jury_code_thread(self, code: str, requirements: Dict):
        """
        Execute the jury-validated code against the repository.

        Detection order:
          1. Author-level  — module has get_author_stats()
          2. Full generator — module has generate_dataset(repo_path, output_dir)
          3. File-level    — module has calculate(file_path, repo_path)

        Always saves a real CSV to the session directory and shows a proper
        preview (authors + scores for author-level; file count for file-level).
        """
        self.root.after(0, lambda: self.add_agent_message(
            MessageType.THINKING, "Applying generated code to repository…"
        ))
        import tempfile, importlib.util, sys as _sys, time as _time

        # Resolve output directory
        session_dir = getattr(self, '_last_jury_session_dir', None)
        if not session_dir or session_dir == "N/A":
            session_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'generated_datasets', f'output_{int(_time.time())}',
            )
        os.makedirs(session_dir, exist_ok=True)
        output_csv = os.path.join(session_dir, 'dataset.csv')

        # ── Read Data Limit from sidebar ─────────────────────────────────
        raw_limit = (
            self.file_limit_var.get().strip().lower()
            if hasattr(self, 'file_limit_var') else 'all'
        )
        try:
            _file_limit = None if raw_limit in ('all', '', '0') else int(raw_limit)
        except ValueError:
            _file_limit = 500

        tmp_path = None
        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name

            # Make MetricsCatalog etc. importable by the generated module
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in _sys.path:
                _sys.path.insert(0, parent_dir)

            spec   = importlib.util.spec_from_file_location("_jury_generated", tmp_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # ── Strategy 0: Benchmark-centric (defects4j / bugsjar / etc.) ──
            # When the requirements list benchmarks, call each generator ONCE
            # with commit_limit = _file_limit, then flatten the JSON output to
            # CSV.  This avoids the LLM anti-pattern of calling generate_benchmark
            # once per file (which ignores the limit and blows up the runtime).
            benchmarks_needed = (requirements or {}).get("benchmarks_needed", [])
            if benchmarks_needed and self.repo_path:
                import json as _json2
                parent_dir2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir2 not in _sys.path:
                    _sys.path.insert(0, parent_dir2)
                from metrics_catalog import MetricsCatalog as _MC

                all_rows = []
                errors   = []
                for bname in benchmarks_needed:
                    self.root.after(0, lambda b=bname, lim=_file_limit: self.add_agent_message(
                        MessageType.THINKING,
                        f"Running {b} benchmark"
                        + (f" (limit: {lim} commits)" if lim else " (all commits)") + "…",
                    ))
                    try:
                        bres = _MC.generate_benchmark(
                            bname, self.repo_path,
                            output_dir=session_dir,
                            file_limit=_file_limit,   # mapped to commit_limit inside
                        )
                        if "error" in bres:
                            errors.append(f"{bname}: {bres['error']}")
                            continue
                        # Read flattened bug rows from the written JSON file
                        json_file = bres.get("json_file")
                        if json_file and os.path.exists(json_file):
                            with open(json_file, encoding="utf-8") as _jf:
                                jdata = _json2.load(_jf)
                            for bug in jdata.get("bugs", []):
                                row = {"benchmark": bname}
                                # Flatten: expand modified_files list to count only
                                flat = {
                                    k: (len(v) if isinstance(v, list) else v)
                                    for k, v in bug.items()
                                    if k != "modified_files"
                                }
                                row.update(flat)
                                all_rows.append(row)
                        else:
                            errors.append(f"{bname}: json_file not found in result")
                    except Exception as be:
                        errors.append(f"{bname}: {be}")

                if all_rows:
                    import csv as _csv3
                    seen = {}
                    for r in all_rows:
                        for k in r:
                            seen.setdefault(k, None)
                    cols = list(seen.keys())
                    with open(output_csv, "w", newline="", encoding="utf-8") as _f:
                        w = _csv3.DictWriter(_f, fieldnames=cols, extrasaction="ignore")
                        w.writeheader()
                        w.writerows(all_rows)
                    total = len(all_rows)
                    limit_note = (
                        f" (limited to {_file_limit} commits per benchmark)"
                        if _file_limit else ""
                    )
                    err_note = f"\n\n  Errors: {'; '.join(errors)}" if errors else ""
                    msg = (
                        f"Bug-commit dataset generated{limit_note} — {total} rows\n"
                        f"  Columns : {len(cols)}\n"
                        f"  Saved to:\n  {output_csv}"
                        f"{err_note}"
                    )
                    def _show_bench_success(m=msg, csv=output_csv, n=total):
                        folder = os.path.dirname(str(csv))
                        self.add_agent_message(MessageType.SUCCESS, m, actions=[{
                            'label': 'Open Dataset Folder',
                            'callback': lambda p=folder: os.startfile(p) if os.path.exists(p) else None,
                        }])
                        self._update_plan_step("4", "done")
                        self.status_var.set(f"Dataset ready — {n} bugs")
                        self.output_path_var.set(f"Output: {csv}")
                    self.root.after(0, _show_bench_success)
                    return
                elif errors:
                    # All benchmarks errored — fall through to per-file strategies
                    self.root.after(0, lambda e="; ".join(errors): self.add_agent_message(
                        MessageType.THINKING,
                        f"Benchmark strategy failed ({e}) — falling back to per-file mode…",
                    ))

            # ── Strategy 1: Author-level ──────────────────────────────────────
            if hasattr(module, 'get_author_stats') and self.repo_path:
                author_stats = module.get_author_stats(self.repo_path)

                # Generated code often uses diff.stats (wrong API) → use fallback
                if not author_stats:
                    self.root.after(0, lambda: self.add_agent_message(
                        MessageType.THINKING,
                        "Generated code used wrong API — using corrected git stats extractor…",
                    ))
                    author_stats = self._extract_author_stats_fallback(self.repo_path)

                if author_stats and hasattr(module, 'calculate_contribution_score'):
                    rows = module.calculate_contribution_score(author_stats)
                elif author_stats:
                    # Generate rows directly from stats if no score function
                    from datetime import datetime, timezone
                    now = datetime.now(tz=timezone.utc)
                    rows = []
                    for author, s in author_stats.items():
                        age = max((now - s['first_commit']).days, 1)
                        total_lines = s['loc_added'] + s['loc_deleted']
                        score = (s['num_commits'] + total_lines / 1000) / age
                        rows.append({
                            'author': author,
                            'num_commits': s['num_commits'],
                            'code_age_days': age,
                            'loc_added': s['loc_added'],
                            'loc_deleted': s['loc_deleted'],
                            'contribution_score': round(score, 6),
                        })
                else:
                    rows = []

                if rows:
                    df = pd.DataFrame(rows)
                    df.to_csv(output_csv, index=False)
                    total = len(rows)
                    top5  = sorted(rows, key=lambda r: r.get('contribution_score', 0), reverse=True)[:5]

                    header  = f"{'Author':<35} {'Score':>9} {'Commits':>8} {'Lines':>10}\n"
                    divider = "-" * 65 + "\n"
                    body = ""
                    for r in top5:
                        a = str(r.get('author', '?'))[:34]
                        body += (f"{a:<35} {r.get('contribution_score', 0):>9.4f}"
                                 f" {r.get('num_commits', 0):>8}"
                                 f" {r.get('loc_added', 0) + r.get('loc_deleted', 0):>10}\n")

                    preview = (
                        f"Author Contribution Dataset — {total} authors\n\n"
                        f"{header}{divider}{body}"
                        f"\n(showing top 5 of {total})\n\n"
                        f"Dataset saved to:\n  {output_csv}"
                    )
                    def _show_author_success(m=preview, csv=output_csv, n=total):
                        folder = os.path.dirname(str(csv))
                        self.add_agent_message(MessageType.SUCCESS, m, actions=[{
                            'label': 'Open Dataset Folder',
                            'callback': lambda p=folder: os.startfile(p) if os.path.exists(p) else None,
                        }])
                        self._update_plan_step("4", "done")
                        self.status_var.set(f"Dataset ready — {n} authors")
                        self.output_path_var.set(f"Output: {csv}")
                    self.root.after(0, _show_author_success)
                    return
                else:
                    self.root.after(0, lambda: self.add_agent_message(
                        MessageType.ERROR,
                        "Author stats returned empty — check repository git history.",
                    ))
                    return

            # ── Strategy 2b: generate_csv(repo_path, output_csv, file_limit) ───
            # Used when the injected CSV runner is present (output_format=csv)
            if hasattr(module, 'generate_csv') and self.repo_path:
                try:
                    result_csv = module.generate_csv(
                        self.repo_path, output_csv, file_limit=_file_limit
                    )
                    total = None
                    # Try to count rows in the written CSV
                    try:
                        import csv as _csv2
                        with open(result_csv, newline='', encoding='utf-8') as _f:
                            total = sum(1 for _ in _csv2.reader(_f)) - 1  # minus header
                    except Exception:
                        pass
                    limit_note = (
                        f" (limited to {_file_limit})"
                        if _file_limit else ""
                    )
                    msg = (
                        f"Dataset generated{limit_note} — "
                        + (f"{total} rows" if total is not None else "file saved") +
                        f"\n\nSaved to:\n  {result_csv}"
                    )
                    def _show_csv_success(m=msg, csv=result_csv):
                        folder = os.path.dirname(str(csv))
                        self.add_agent_message(MessageType.SUCCESS, m, actions=[{
                            'label': 'Open Dataset Folder',
                            'callback': lambda p=folder: os.startfile(p) if os.path.exists(p) else None,
                        }])
                        self._update_plan_step("4", "done")
                        self.output_path_var.set(f"Output: {csv}")
                        self.status_var.set(f"Dataset ready")
                    self.root.after(0, _show_csv_success)
                    return
                except Exception as csv_exc:
                    # Fall through to per-file strategy
                    self.root.after(0, lambda e=str(csv_exc): self.add_agent_message(
                        MessageType.THINKING,
                        f"generate_csv() failed ({e}) — falling back to per-file mode…",
                    ))

            # ── Strategy 2: generate_dataset(repo_path, output_dir) ──────────
            if hasattr(module, 'generate_dataset') and self.repo_path:
                result = module.generate_dataset(self.repo_path, session_dir)
                if isinstance(result, pd.DataFrame) and not result.empty:
                    result.to_csv(output_csv, index=False)
                    n = len(result)
                    preview = (
                        f"Dataset generated — {n} rows, {len(result.columns)} columns\n\n"
                        f"Saved to:\n  {output_csv}"
                    )
                    def _show_gen_success(m=preview, csv=output_csv):
                        folder = os.path.dirname(str(csv))
                        self.add_agent_message(MessageType.SUCCESS, m, actions=[{
                            'label': 'Open Dataset Folder',
                            'callback': lambda p=folder: os.startfile(p) if os.path.exists(p) else None,
                        }])
                        self._update_plan_step("4", "done")
                        self.output_path_var.set(f"Output: {csv}")
                    self.root.after(0, _show_gen_success)
                    return
            if not hasattr(module, "calculate"):
                raise AttributeError(
                    "Generated module has no usable entry point "
                    "(expected: calculate / get_author_stats / generate_dataset)"
                )

            # ── Determine which file extensions to scan from requirements ────
            lang = requirements.get('language', 'java') if requirements else 'java'
            ext_map = {
                'java':   ('.java',),
                'python': ('.py',),
                'any':    ('.java', '.py'),
            }
            target_exts = ext_map.get(lang, ('.java', '.py'))
            skip_dirs = {"target", "build", ".git", "__pycache__",
                         "node_modules", ".gradle", "dist", ".idea", ".mvn"}

            source_files = []
            if self.repo_path:
                for root_dir, dirs, files in os.walk(self.repo_path):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for fname in files:
                        if fname.endswith(target_exts):
                            source_files.append(os.path.join(root_dir, fname))
            if not source_files:
                source_files = [__file__]

            # ── Apply the sidebar Data Limit setting ──────────────────────
            total_found = len(source_files)
            if _file_limit:
                source_files = source_files[:_file_limit]

            total_files = len(source_files)
            limit_note = (
                f" (limited to {_file_limit} of {total_found})"
                if _file_limit and _file_limit < total_found
                else ""
            )
            self.root.after(0, lambda n=total_files, note=limit_note: self.add_agent_message(
                MessageType.THINKING,
                f"Running metric code on {n} file(s){note}…",
            ))

            def _flatten(d: dict, prefix: str = '') -> dict:
                """Flatten a nested dict, joining keys with '.'"""
                out = {}
                for k, v in d.items():
                    key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
                    if isinstance(v, dict):
                        out.update(_flatten(v, key))
                    elif isinstance(v, list):
                        out[key] = str(v)  # stringify lists
                    else:
                        out[key] = v
                return out

            file_rows = []
            for idx, fp in enumerate(source_files, 1):
                try:
                    res = module.calculate(fp, self.repo_path)
                    if isinstance(res, dict):
                        # Pull from 'metrics' sub-key if present, else use full dict
                        core = res.get('metrics') if isinstance(res.get('metrics'), dict) else res
                        row = {'file': os.path.relpath(fp, self.repo_path)
                               if self.repo_path else os.path.basename(fp)}
                        row.update(_flatten({k: v for k, v in core.items()
                                             if k not in ('benchmarks', 'error')}))
                        if res.get('error'):
                            row['_error'] = str(res['error'])
                    else:
                        row = {'file': os.path.basename(fp), '_error': f"bad return: {type(res)}"}
                    file_rows.append(row)
                except Exception as e:
                    file_rows.append({
                        'file': os.path.relpath(fp, self.repo_path)
                                if self.repo_path else os.path.basename(fp),
                        '_error': str(e),
                    })

                if idx % 50 == 0:
                    self.root.after(0, lambda i=idx, t=total_files: self.add_agent_message(
                        MessageType.THINKING, f"Progress: {i}/{t} files…"
                    ))

            if not file_rows:
                raise RuntimeError("calculate() produced no rows — check generated code")

            # ── Save in requested output format ───────────────────────────────
            output_fmt = (requirements.get('output_format', 'csv') if requirements else 'csv') or 'csv'
            # Build stable column order
            seen_cols: dict = {}
            for row in file_rows:
                for k in row:
                    seen_cols.setdefault(k, None)
            all_cols = list(seen_cols.keys())

            import json as _json
            if output_fmt == 'jsonl':
                output_csv = output_csv.replace('.csv', '.jsonl')
                with open(output_csv, 'w', encoding='utf-8') as _f:
                    for row in file_rows:
                        _f.write(_json.dumps(row, default=str) + '\n')
            elif output_fmt == 'json':
                output_csv = output_csv.replace('.csv', '.json')
                with open(output_csv, 'w', encoding='utf-8') as _f:
                    _json.dump(file_rows, _f, indent=2, default=str)
            else:
                import csv as _csv
                with open(output_csv, 'w', newline='', encoding='utf-8') as _f:
                    writer = _csv.DictWriter(_f, fieldnames=all_cols, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(file_rows)

            total = len(file_rows)
            ok    = sum(1 for r in file_rows if '_error' not in r)
            preview = (
                f"Dataset generated — {ok}/{total} files processed\n"
                f"Columns  : {len(all_cols)}\n"
                f"Format   : {output_fmt}\n\n"
                f"Saved to:\n  {output_csv}"
            )
            def _show_file_success(m=preview, csv=output_csv, n=total):
                folder = os.path.dirname(str(csv))
                self.add_agent_message(MessageType.SUCCESS, m, actions=[{
                    'label': 'Open Dataset Folder',
                    'callback': lambda p=folder: os.startfile(p) if os.path.exists(p) else None,
                }])
                self._update_plan_step("4", "done")
                self.status_var.set(f"Dataset ready — {n} files")
                self.output_path_var.set(f"Output: {csv}")
            self.root.after(0, _show_file_success)

        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda e=msg: self.add_agent_message(
                MessageType.ERROR,
                f"Code execution error: {e}\n"
                "(The generated code was saved to the session directory)",
            ))
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _open_output_folder(self):
        """Open the dataset output folder in Windows Explorer."""
        import subprocess
        session_dir = getattr(self, '_last_jury_session_dir', None)
        if not session_dir or not os.path.isdir(session_dir):
            # Try to extract from output_path_var label
            label = self.output_path_var.get()
            if label.startswith("Output: "):
                candidate = label[len("Output: "):]
                if os.path.isfile(candidate):
                    session_dir = os.path.dirname(candidate)
                elif os.path.isdir(candidate):
                    session_dir = candidate
        if session_dir and os.path.isdir(session_dir):
            subprocess.Popen(f'explorer "{session_dir}"')
        else:
            self.add_agent_message(
                MessageType.ERROR,
                "Output folder not found. Generate a dataset first.",
            )

    # ═══════════════════════════════════════════════════════════════════════
    # FORMULA TAB METHODS (TAB 2 - ISOLATED)
    # ═══════════════════════════════════════════════════════════════════════
    

