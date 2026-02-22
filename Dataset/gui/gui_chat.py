"""ChatMixin — agentic chat, intelligent request processor, agent query."""
import tkinter as tk
import threading
import os
import re
import json
import traceback
import pandas as pd
from typing import Dict

genai = None
try:
    import google.generativeai as genai
except ImportError:
    pass

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
            metrics_needed = reqs.get('metrics_needed', [])
            fmt = reqs.get('output_format', 'csv')

            # Classify metrics as catalog-known vs unknown (will be custom-synthesized)
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

            # Check if this is a "metrics dataset" request vs "custom metric" request
            goal_lower = goal.lower()
            is_metrics_dataset = any(word in goal_lower for word in ['dataset', 'extract', 'collect', 'analyze', 'all metrics'])

            # If user wants a metrics dataset (not custom code), auto-select appropriate metrics
            if is_metrics_dataset:
                # Use specified metrics, or all 65 if none specified
                metrics_to_use = known_metrics if known_metrics else list(MetricsCatalog.get_all_metrics().keys())
                if metrics_to_use:
                    self.add_agent_message(
                        MessageType.THINKING,
                        f"Generating metrics dataset with {len(metrics_to_use)} metrics..."
                    )
                    self.selected_metrics = metrics_to_use
                    self.selected_metrics_count.set(f"{len(metrics_to_use)}/65 selected")
                    # Trigger dataset generation directly
                    self.root.after(100, lambda m=metrics_to_use: self._generate_metrics_dataset(m))
                    return

            # Otherwise, proceed with custom code generation (original path)
            metrics_line = ', '.join(metrics_needed) if metrics_needed else 'none'
            catalog_line = (
                f"  Catalog : {len(known_metrics)} known"
                + (f", {len(unknown_metrics)} custom (will be synthesized)"
                   if unknown_metrics else "")
            )
            unknown_line = (
                f"\n  Custom  : {', '.join(unknown_metrics)}" if unknown_metrics else ""
            )

            self.add_agent_message(
                MessageType.INFO,
                f"Requirement understood ({conf}% confidence).\n\n"
                f"  Goal    : {goal}\n"
                f"  Metrics : {metrics_line}\n"
                f"{catalog_line}{unknown_line}\n"
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

            self.add_agent_message(
                MessageType.SUCCESS,
                f"Code generated and validated!\n\n"
                f"  Iterations   : {iters}/{self.integrated_jury.MAX_RETRIES}\n"
                f"  LLMs passed  : {tr.get('passing_llms', 0)}/3\n"
                f"  Tests passed : {tr.get('total_passed', 0)}/{tr.get('total_tests', 0)}\n\n"
                f"  Session saved to:\n  {session_dir}",
            )
            self._update_plan_step("2", "done")
            self._update_plan_step("3", "done")

            # Update status bar / output path
            self.output_path_var.set(f"Output: {session_dir}")
            self.status_var.set(f"Validated \u2014 {iters} iteration(s)")

            # Apply the validated code to generate the actual dataset
            if code and self.repo_path:
                self._jury_pending_code = (code, result.get("requirements", {}))
                self._update_plan_step("4", "active")
                self.confirm_label.config(
                    text=f"Code validated! ({tr.get('passing_llms', 0)}/3 juries, "
                         f"{tr.get('total_passed', 0)}/{tr.get('total_tests', 0)} tests)\n"
                         f"Click Confirm to generate the actual dataset CSV."
                )
                self.confirm_yes_btn.config(command=self._confirm_cp2_yes)
                self.confirm_no_btn.config(command=self._confirm_cp2_no)
                self.set_approval_visible(True)
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

    def _apply_jury_code_thread(self, code: str, requirements: Dict):
        """
        Execute the jury-validated code against the repository and display results.
        Collects up to 5 files as a preview.
        """
        self.root.after(0, lambda: self.add_agent_message(
            MessageType.THINKING, "Applying generated code to repository…"
        ))
        import tempfile, importlib.util

        tmp_path = None
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name

            # Dynamically load the generated module
            spec = importlib.util.spec_from_file_location("_jury_generated", tmp_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "calculate"):
                raise AttributeError("Generated module must define  calculate(file_path, repo_path)")

            # Find code files in repo (first 5)
            source_files = []
            if self.repo_path:
                for root_dir, dirs, files in os.walk(self.repo_path):
                    dirs[:] = [
                        d for d in dirs
                        if d not in {"target", "build", ".git", "__pycache__", "node_modules"}
                    ]
                    for fname in files:
                        if fname.endswith((".java", ".py")):
                            source_files.append(os.path.join(root_dir, fname))
                        if len(source_files) >= 5:
                            break
                    if len(source_files) >= 5:
                        break

            if not source_files:
                source_files = [__file__]   # fallback: this file

            results = []
            for fp in source_files:
                try:
                    res = module.calculate(fp, self.repo_path)
                    res["_file"] = fp
                    results.append(res)
                except Exception as e:
                    results.append({"_file": fp, "error": str(e)})

            # Build a human-readable preview
            lines = [f"Dataset preview ({len(results)} file(s)):"]
            for r in results:
                fname = os.path.basename(r.get("_file", "?"))
                metrics = {k: v for k, v in r.items() if not k.startswith("_")}
                if metrics.get("error"):
                    lines.append(f"  {fname}: ERROR — {metrics['error']}")
                else:
                    m = metrics.get("metrics", metrics)
                    non_zero = sum(1 for v in m.values() if v and v != 0)
                    lines.append(
                        f"  {fname}: {len(m)} metrics, {non_zero} non-zero"
                    )

            output_msg = "\n".join(lines)
            self.root.after(0, lambda m=output_msg: (
                self.add_agent_message(MessageType.SUCCESS, m),
                self._update_plan_step("4", "done"),
                self.status_var.set("Dataset generation complete"),
            ))

        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda e=msg: self.add_agent_message(
                MessageType.ERROR,
                f"Code execution note: {e}\n"
                "(The code was still saved to the session directory)",
            ))
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _intelligent_chat_processor(self, query: str):
        """
        INTELLIGENT PROCESSOR - Handles all requirements
        
        Flow:
        1. Interpret query with LLM
        2. Check if all metrics are known
        3. If unknown metrics → Start LLM Jury Process
        4. Show understanding → Ask user approval
        5. Generate real dataset from repo
        6. Create visualizations
        7. Collect feedback
        """
        if not self.api_key:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "  API key missing. Set GEMINI_API_KEY in .env"))
            return
        
        try:
            # Step 1: INTERPRET QUERY
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, 
                "Analyzing your request..."))
            
            # Get available metrics
            available_metrics = {}
            if self.catalog:
                available_metrics = self.catalog.get_all_metrics()
            
            # Build analysis prompt
            analysis_prompt = f"""You are an intelligent dataset generation assistant.

USER QUERY: "{query}"

AVAILABLE METRICS ({len(available_metrics)}):
{json.dumps(list(available_metrics.keys())[:50], indent=2)}... (and {len(available_metrics)-50 if len(available_metrics)>50 else 0} more)

AVAILABLE BENCHMARKS:
- Defects4J (Java bugs, buggy/fixed versions)
- Bugs.jar (Large-scale Java bugs)
- PROMISE (Defect prediction)
- CodeXGLUE (Microsoft code benchmark)
- CodeSearchNet (Code-to-documentation)
- ManySStuBs4J (Simple stupid bugs)
- Sourcerer (Large-scale mining)

ANALYZE and return JSON:
{{
    "understood": true/false,
    "clarification_needed": "question if unclear, null otherwise",
    "intent": "benchmark|custom_metrics|combined|custom_formula|analysis",
    "is_formula": true/false,
    "formula_expression": "the complete formula if is_formula=true",
    "formula_name": "name of the custom metric being calculated",
    "base_metrics_needed": ["list", "of", "metrics", "needed", "for", "formula"],
    "unknown_base_metrics": [
        {{
            "name": "metric_name",
            "description": "what this base metric represents",
            "extract_from": "git_history|code_analysis|file_system"
        }}
    ],
    "benchmark": "name or null",
    "known_metrics": ["list", "of", "known", "metric", "names"],
    "summary": "Clear summary of what will be generated",
    "ready": true/false
}}

CRITICAL RULES:
- If query contains math operators (/, *, +, -, **) → set is_formula=true
- For formulas: Extract ALL base metrics needed (both sides of operators)
- Example: "max(commits_by_author) / commit_count"
  → formula_name: "Code Ownership Concentration"
  → base_metrics_needed: ["commits_by_author", "commit_count"]
  → unknown_base_metrics: [{{"name": "commits_by_author", "description": "per-author commit counts", "extract_from": "git_history"}}]
- If base metric is UNKNOWN → add to unknown_base_metrics (NOT unknown_metrics)
- Ask clarification if unclear what formula calculates
"""
            
            if genai is not None:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-flash-latest')
            else:
                model = None

            # Try Gemini first, with AWS Bedrock fallback on quota errors
            try:
                if model is None:
                    raise Exception("429: genai not installed — using AWS Bedrock fallback")
                response = model.generate_content(analysis_prompt)
                text = response.text.strip()
            except Exception as gemini_error:
                error_msg = str(gemini_error).lower()
                
                # Check if quota exceeded
                if ('429' in error_msg or 'quota' in error_msg or 'resourceexhausted' in error_msg):
                    self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                        "  Gemini quota exceeded. Using AWS Bedrock fallback..."))
                    
                    # Try AWS Bedrock fallback
                    if hasattr(self, 'llm_jury_system') and self.llm_jury_system and self.llm_jury_system.use_aws_fallback:
                        try:
                            aws_response = self.llm_jury_system.multi_provider.generate_content(analysis_prompt)
                            
                            # Debug: Check what AWS returned
                            print(f"AWS Response type: {type(aws_response)}")
                            print(f"AWS Response keys: {aws_response.keys() if isinstance(aws_response, dict) else 'not a dict'}")
                            
                            # Extract text from AWS response
                            if isinstance(aws_response, dict):
                                text = aws_response.get('text', '') or aws_response.get('content', '')
                            else:
                                text = str(aws_response)
                            
                            # Validate response is not empty
                            if not text or len(text.strip()) < 10:
                                raise Exception(f"AWS response empty or too short: {text[:100]}")
                            
                            text = text.strip()
                            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                                "  AWS Bedrock responded successfully"))
                        except Exception as aws_error:
                            print(f"AWS error details: {aws_error}")
                            raise Exception(f"Both Gemini and AWS Bedrock failed. Gemini: {gemini_error}. AWS: {aws_error}")
                    else:
                        raise Exception(f"Gemini quota exceeded and AWS Bedrock not configured. Error: {gemini_error}")
                else:
                    raise gemini_error
            
            # Parse JSON response
            text = text.strip()
            if not text:
                raise Exception("Empty response received from LLM")
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            # Validate JSON before parsing
            if not text or text == 'null':
                raise Exception(f"Invalid response text: {text}")
            
            try:
                understanding = json.loads(text)
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, show user the error and ask for clarification
                print(f"  JSON parsing failed. AWS response preview: {text[:300]}")
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"Failed to parse response (AWS Bedrock returned text but not valid JSON).\n\n"
                    f"Response preview: {text[:200]}\n\n"
                    f"This might be a provider issue. Try again with a simpler request."))
                return
            
            # Step 2: CHECK IF CLARIFICATION NEEDED
            if not understanding.get('understood', False) or understanding.get('clarification_needed'):
                question = understanding.get('clarification_needed', 
                                            'Can you provide more details?')
                self.root.after(0, lambda q=question: self.add_agent_message(
                    MessageType.QUESTION, f"{q}"))
                return
            
            # Step 3: CHECK IF FORMULA OR UNKNOWN METRICS
            is_formula = understanding.get('is_formula', False)
            unknown_base_metrics = understanding.get('unknown_base_metrics', [])
            
            # If formula with unknown base metrics → ASK USER first
            if is_formula and unknown_base_metrics:
                formula_name = understanding.get('formula_name', 'custom metric')
                formula_expr = understanding.get('formula_expression', '')
                
                unknown_list = "\n".join([
                    f"  • {m['name']}: {m['description']} (from {m.get('extract_from', 'unknown')})"
                    for m in unknown_base_metrics
                ])
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                    f"**CLARIFICATION NEEDED**\n\n"
                    f"You want to calculate: **{formula_name}**\n"
                    f"Formula: `{formula_expr}`\n\n"
                    f"But these base metrics are NOT available:\n{unknown_list}\n\n"
                    f"Should I:\n"
                    f"    Extract them from repository using Jury-generated code?\n"
                    f"    Use alternative/approximation?\n\n"
                    f"Type 'extract' or 'yes' to proceed with extraction, or describe alternative."))
                
                # Store for later
                self.current_plan = understanding
                self.awaiting_extraction_approval = True
                return
            
            # Legacy: Handle non-formula unknown metrics
            unknown_metrics = understanding.get('unknown_metrics', [])
            
            if unknown_metrics and self.llm_jury_system:
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"Found {len(unknown_metrics)} unknown metric(s). "
                    f"Starting LLM Jury Process to validate..."))
                
                # Process each unknown metric through jury
                validated_metrics = []
                
                for unk in unknown_metrics:
                    metric_name = unk.get('name', 'custom_metric')
                    metric_desc = unk.get('description', metric_name)
                    
                    self.root.after(0, lambda n=metric_name: self.add_agent_message(
                        MessageType.THINKING, f"Jury evaluating: {n}..."))
                    
                    try:
                        # Step 1: Prepare formula structure for LLMCodeJurySystem
                        # Extract what metrics are needed from the formula/expression
                        formula_text = metric_desc
                        
                        # Look for known metric names in the formula
                        all_metrics = list(available_metrics.keys()) + [
                            'lines_added', 'lines_deleted', 'commit_count', 'commits_per_file', 'author_count',
                            'code_smells', 'cyclomatic_complexity', 'cognitive_complexity'
                        ]
                        metrics_in_formula = [m for m in all_metrics if m.lower() in formula_text.lower()]
                        
                        formula_structure = [{
                            'name': metric_name,
                            'description': metric_desc,
                            'expression': formula_text,
                            'required_columns': metrics_in_formula if metrics_in_formula else list(available_metrics.keys())[:20]
                        }]
                        
                        # Create dummy dataframe with available metrics as columns
                        # CRITICAL: Always include git metrics even if not in catalog
                        metrics_for_dummy = list(available_metrics.keys())[:20]
                        
                        # Ensure git metrics are in the dummy data if formula mentions them
                        git_metrics = ['lines_added', 'lines_deleted', 'commit_count', 'commits_per_file', 'author_count']
                        code_metrics = ['code_smells', 'cyclomatic_complexity', 'cognitive_complexity']
                        all_possible_metrics = metrics_for_dummy + git_metrics + code_metrics
                        
                        # Filter to unique and only use first 30
                        unique_metrics = list(dict.fromkeys(all_possible_metrics))[:30]
                        
                        dummy_data = pd.DataFrame({
                            metric: [0] for metric in unique_metrics
                        })
                        
                        # Step 2: Generate code
                        self.root.after(0, lambda: self.add_agent_message(
                            MessageType.INFO, "Generator LLM creating code..."))
                        
                        generated_code = self.llm_jury_system.generate_code(
                            formula_structure, 
                            dummy_data
                        )
                        
                        if not generated_code:
                            self.root.after(0, lambda n=metric_name: 
                                self.add_agent_message(MessageType.ERROR, 
                                    f"  {n}: Code generation failed"))
                            continue
                        
                        # Step 3: Verify with jury
                        self.root.after(0, lambda: self.add_agent_message(
                            MessageType.INFO, "3 Judge LLMs verifying..."))
                        
                        verification = self.llm_jury_system.verify_code_with_jury(
                            generated_code,
                            formula_structure
                        )
                        
                        # Check votes
                        votes = verification.get('votes', [])
                        approved_count = sum(1 for name, verdict in votes 
                                           if verdict.get('verdict') == 'APPROVE')
                        
                        # Show each judge's vote
                        for judge_name, verdict in votes:
                            status = " " if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                            self.root.after(0, lambda j=judge_name, s=status, v=verdict: 
                                self.add_agent_message(MessageType.INFO, 
                                    f"{s} {j}: {v.get('verdict')}"))
                        
                        # Need majority approval
                        if approved_count >= 2:  # At least 2 out of 3
                            validated_metrics.append({
                                'name': metric_name,
                                'description': metric_desc,
                                'code': generated_code,
                                'jury_summary': f"{approved_count}/3 judges approved"
                            })
                            self.root.after(0, lambda n=metric_name, c=approved_count: 
                                self.add_agent_message(MessageType.SUCCESS, 
                                    f"  {n}: Approved by {c}/3 judges"))
                        else:
                            self.root.after(0, lambda n=metric_name, c=approved_count: 
                                self.add_agent_message(MessageType.ERROR, 
                                    f"  {n}: Rejected - only {c}/3 judges approved"))
                    
                    except Exception as e:
                        self.root.after(0, lambda n=metric_name, err=str(e): 
                            self.add_agent_message(MessageType.ERROR, 
                                f"  {n}: Error - {err}"))
                
                # Add validated metrics to known list
                understanding['validated_custom_metrics'] = validated_metrics
            
            # Step 4: SHOW UNDERSTANDING & ASK APPROVAL
            known_metrics = understanding.get('known_metrics', [])
            validated_custom = understanding.get('validated_custom_metrics', [])
            
            approval_msg = f"""  **HERE'S MY UNDERSTANDING:**

{understanding.get('summary', 'Generate dataset')}

**Type:** {understanding.get('intent', 'custom')}
**Repository:** {self.repo_path}
**Known Metrics:** {len(known_metrics)} metrics
  → {', '.join(known_metrics[:10])}{"..." if len(known_metrics) > 10 else ""}
"""
            
            if validated_custom:
                approval_msg += f"\n**Custom Metrics (Jury Approved):** {len(validated_custom)}\n"
                for vc in validated_custom:
                    approval_msg += f"    {vc['name']}: {vc['jury_summary']}\n"
            
            if understanding.get('benchmark'):
                approval_msg += f"**Benchmark Format:** {understanding['benchmark']}\n"
            
            approval_msg += "\n**DATA SOURCE:** Real data from your repository (NO MOCK DATA)\n"
            approval_msg += "\n  **Type 'yes' or 'approve' to proceed**\n  **Type 'no' or describe changes to modify**"
            
            self.root.after(0, lambda m=approval_msg: self.add_agent_message(
                MessageType.QUESTION, m))
            
            #   IMPORTANT: Ask user for file limit BEFORE processing
            self.root.after(100, lambda: self.add_agent_message(MessageType.QUESTION,
                f"  **HOW MANY FILES TO PROCESS?**\n\n"
                f"Default: 100 files\n\n"
                f"Enter a number or type 'all' for entire repo\n"
                f"(Larger = slower, but more comprehensive)\n\n"
                f"Current setting: {self.file_limit_var.get()}"))
            
            # Store for approval
            self.current_plan = understanding
            self.conversation_history.append({
                "role": "assistant", 
                "content": approval_msg,
                "plan": understanding
            })
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda err=str(e), detail=error_detail:
                self.add_agent_message(MessageType.ERROR,
                    f"  Analysis error: {err}\n\nDetails:\n{detail}"))
    
    def _process_formula_extraction(self):
        """
        Process formula extraction using Jury System
        
        Flow:
        1. Get unknown base metrics from current_plan
        2. Create extraction code using Generator LLM
        3. Verify with 3 Judge LLMs
        4. If approved → Extract data and apply formula
        5. Show results to user
        """
        if not self.current_plan:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "  No plan found"))
            return
        
        try:
            unknown_base = self.current_plan.get('unknown_base_metrics', [])
            formula_name = self.current_plan.get('formula_name', 'custom metric')
            formula_expr = self.current_plan.get('formula_expression', '')
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"Starting Jury Process for: **{formula_name}**"))
            
            # Combine all unknown metrics into ONE extraction task
            combined_description = f"""Extract base metrics for formula: {formula_expr}

Required metrics:
{chr(10).join([f"- {m['name']}: {m['description']} (from {m.get('extract_from', 'unknown')})" for m in unknown_base])}

These metrics will be used to calculate: {formula_name}
"""
            
            # Step 1: Generate extraction code
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "Generator LLM creating extraction code..."))
            
            formula_structure = [{
                'name': formula_name,
                'description': combined_description,
                'expression': formula_expr,
                'required_columns': [m['name'] for m in unknown_base]
            }]
            
            # Create dummy dataframe with repository structure
            dummy_data = pd.DataFrame({
                'file': ['example.java'],
                'commit_count': [100]  # Include known metrics
            })
            
            generated_code = self.llm_jury_system.generate_code(
                formula_structure,
                dummy_data
            )
            
            if not generated_code:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    "  Code generation failed"))
                return
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"  Code generated ({len(generated_code)} chars)"))
            
            # Step 2: Verify with jury
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "3 Judge LLMs verifying..."))
            
            verification = self.llm_jury_system.verify_code_with_jury(
                generated_code,
                formula_structure
            )
            
            votes = verification.get('votes', [])
            approved_count = sum(1 for name, verdict in votes 
                               if verdict.get('verdict') == 'APPROVE')
            
            # Show each judge's vote
            for judge_name, verdict in votes:
                status = " " if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                reason = verdict.get('reason', 'No reason provided')
                self.root.after(0, lambda j=judge_name, s=status, v=verdict.get('verdict'): 
                    self.add_agent_message(MessageType.INFO, 
                        f"{s} {j}: {v}"))
            
            # Need majority approval (2/3)
            if approved_count >= 2:
                self.root.after(0, lambda n=formula_name, c=approved_count: 
                    self.add_agent_message(MessageType.SUCCESS, 
                        f"  **{n}**: Approved by {c}/3 judges"))
                
                # Store validated code
                if 'validated_custom_metrics' not in self.current_plan:
                    self.current_plan['validated_custom_metrics'] = []
                
                self.current_plan['validated_custom_metrics'].append({
                    'name': formula_name,
                    'expression': formula_expr,
                    'code': generated_code,
                    'jury_summary': f"{approved_count}/3 judges approved"
                })
                
                # Now ask for final approval
                self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                    f"  **Formula validation complete!**\n\n"
                    f"**Metric:** {formula_name}\n"
                    f"**Formula:** `{formula_expr}`\n"
                    f"**Jury Result:** {approved_count}/3 approved\n\n"
                    f"Ready to extract data and apply formula?\n\n"
                    f"Type 'yes' to proceed"))
                
            else:
                self.root.after(0, lambda n=formula_name, c=approved_count: 
                    self.add_agent_message(MessageType.ERROR, 
                        f"**{n}**: Rejected - only {c}/3 judges approved\n\n"
                        f"Please rephrase your formula or try a different approach."))
                self.current_plan = None
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda err=str(e), detail=error_detail:
                self.add_agent_message(MessageType.ERROR,
                    f"Extraction error: {err}\n\nDetails:\n{detail}"))

    def _process_agentic_chat(self, query: str):
        """Legacy method - redirects to new intelligent processor"""
        self._intelligent_chat_processor(query)
    
    def _execute_understood_request(self):
        """Execute the understood request"""
        if not self.understood_request:
            return
        
        req = self.understood_request
        dtype = req.get('dataset_type', 'custom')
        
        self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION, 
            "Starting generation based on your request..."))
        
        if dtype == 'benchmark' and req.get('benchmark'):
            threading.Thread(target=self._generate_benchmark_dataset,
                           args=(req['benchmark'],), daemon=True).start()
        elif dtype == 'custom' and req.get('custom_description'):
            # Use LLM Jury for custom metric
            threading.Thread(target=self._generate_custom_with_jury,
                           args=(req['custom_description'],), daemon=True).start()
        elif req.get('metrics'):
            self.selected_metrics = req['metrics']
            threading.Thread(target=self._generate_metrics_dataset,
                           args=(req['metrics'],), daemon=True).start()
        else:
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                "Please select metrics or benchmark, or describe a custom metric."))
    
    def _generate_custom_with_jury(self, description: str):
        """Generate custom metric using LLM Jury system"""
        if not self.llm_jury or not self.llm_jury.enabled:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "LLM Jury System not available. Check API keys in .env"))
            return
        
        def progress_callback(msg):
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, msg))
        
        try:
            # Get available metrics
            available = self.catalog.get_all_metrics() if self.catalog else {}
            
            # Full jury process
            result = self.llm_jury.full_jury_process(
                description, available, num_judges=3, on_progress=progress_callback
            )
            
            if result.get('success') and result.get('approved'):
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"  Custom metric approved!\n\n"
                    f"**Name:** {result['proposal'].get('metric_name')}\n"
                    f"**Jury:** {result['jury_result']['summary']}\n\n"
                    f"Generating dataset with this metric..."))
                
                # TODO: Actually generate dataset with custom metric code
            else:
                issues = result.get('jury_result', {}).get('votes', [])
                issue_text = "\n".join([f"- Judge {v.get('judge_id')}: {v.get('reasoning', 'No reason')}" 
                                       for v in issues])
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"   Custom metric rejected by jury:\n{issue_text}"))
        
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Jury error: {msg}"))
            

    def _clear_agent_input_placeholder(self):
        """LEGACY - not needed anymore"""
        pass
    
    def process_agent_query(self):
        """LEGACY - redirects to unified processor"""
        self.process_unified_input()
    
    def _execute_agent_query(self, query: str):
        """Execute agent query in background thread"""
        try:
            # Parse mode from query
            mode_str = self.agent_mode_var.get()
            mode = AgentMode.ASK if mode_str == "ask" else AgentMode.AGENT
            
            # Add thinking message
            self.add_agent_message(MessageType.THINKING, f"Analyzing: {query}")
            
            # Parse input
            actual_mode, actual_query = self.autonomous_agent.parse_user_input(
                f"/{mode_str} {query}" if mode_str == "ask" else query
            )
            
            # Generate plan
            self.add_agent_message(MessageType.ACTION, "Generating task plan...")
            plan = self.autonomous_agent.generate_task_plan(actual_query)
            
            # Show plan details
            self.add_agent_message(MessageType.INFO, 
                f"Intent: {plan.get('intent')}\n"
                f"  Metrics: {', '.join(plan.get('metrics', []))}\n"
                f"  Type: {plan.get('dataset_type')}"
            )
            
            # Show tasks
            tasks_text = "Tasks:\n"
            for i, task in enumerate(plan.get('tasks', []), 1):
                auto = " " if task.get('auto_execute') else " "
                tasks_text += f"  {i}. {auto} {task.get('task')}\n"
            self.add_agent_message(MessageType.INFO, tasks_text)
            
            # Execute based on mode
            if mode == AgentMode.ASK:
                self._execute_agent_ask_mode(plan)
            else:
                self._execute_agent_autonomous_mode(plan)
                
        except Exception as e:
            self.add_agent_message(MessageType.ERROR, f"   Error: {str(e)}")
    
    def _execute_agent_ask_mode(self, plan: dict):
        """Execute agent in ASK mode"""
        self.add_agent_message(MessageType.ACTION, 
            "  ASK MODE - Permission required for each task\n\n"
            "Approval workflow initiated. Check task panel for approval buttons."
        )
        
        # Create tasks in task manager
        self.task_manager.clear_tasks()
        for task_data in plan.get('tasks', []):
            self.task_manager.add_task(
                title=task_data.get('task', 'Task'),
                description=task_data.get('description', ''),
                requires_approval=True
            )
        
        # Update UI
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.add_agent_message(MessageType.INFO, 
            "Plan ready. Click ▶ Start Execution in task panel."
        )
    
    def _execute_agent_autonomous_mode(self, plan: dict):
        """Execute agent in AGENT mode (autonomous)"""
        self.add_agent_message(MessageType.ACTION, 
            "AGENT MODE - Autonomous execution started"
        )
        
        # Execute plan
        result = self.autonomous_agent.execute_plan(plan, AgentMode.AGENT)
        
        # Show execution messages
        for msg in result.get('messages', []):
            self.add_agent_message(MessageType.ACTION, msg)
        
        # Show result
        if result['success']:
            self.add_agent_message(MessageType.SUCCESS,
                f"Completed {result['tasks_completed']}/{result['tasks_total']} tasks"
            )
            
            # Show output file if generated
            if result.get('output_file'):
                file_size = os.path.getsize(result['output_file']) if os.path.exists(result['output_file']) else 0
                self.add_agent_message(MessageType.INFO,
                    f"  **Output Dataset:**\n"
                    f"   File: {result['output_file']}\n"
                    f"   Size: {file_size:,} bytes"
                )
            
            # Ask for feedback
            self.add_agent_message(MessageType.QUESTION,
                "Do you have feedback or need changes?\n\n"
                "Type your feedback in the agent input field and press Enter."
            )
        else:
            self.add_agent_message(MessageType.ERROR,
                f"Execution had failures\n"
                f"Completed: {result['tasks_completed']}/{result['tasks_total']}"
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FORMULA TAB METHODS (TAB 2 - ISOLATED)
    # ═══════════════════════════════════════════════════════════════════════
    

