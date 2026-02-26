"""JuryTabMixin — jury confirmation gates and Tab 3 (Jury) methods."""
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import traceback
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict
import os
try:
    from .gui_types import MessageType
except ImportError:
    from gui_types import MessageType


class JuryTabMixin:
    def _on_confirm_yes(self):
        self.set_approval_visible(False)
        if hasattr(self, '_jury_confirm_event'):
            self._jury_confirm_result = True
            self._jury_confirm_event.set()
        self.task_manager.approve_current()

    def _on_confirm_no(self):
        self.set_approval_visible(False)
        if hasattr(self, '_jury_confirm_event'):
            self._jury_confirm_result = False
            self._jury_confirm_event.set()
        self.task_manager.reject_current()

    def _on_confirm_clarify(self):
        self.set_approval_visible(False)
        if hasattr(self, '_jury_confirm_event'):
            self._jury_confirm_result = 'clarify'
            self._jury_confirm_event.set()
        self.task_manager.skip_current()

    def _request_confirmation(self, message: str) -> bool:
        """
        Block the calling thread until the user clicks Confirm or Cancel.
        Returns True if confirmed, False if cancelled, 'clarify' if Clarify.
        Must be called from a background thread (not the GUI thread).
        """
        import threading as _threading
        self._jury_confirm_event = _threading.Event()
        self._jury_confirm_result = False

        def _show():
            self.confirm_label.config(text=message)
            self.set_approval_visible(True)

        self.root.after(0, _show)
        self._jury_confirm_event.wait()   # blocks until button clicked
        return self._jury_confirm_result

    # ── Task Plan helpers ──────────────────────────────────────────────────────
    def _populate_jury_task_plan(self):
        """Populate the center task list with the 4-step jury plan."""
        for w in self.task_list_frame.winfo_children():
            w.destroy()
        tasks = [
            ("1", "Requirement Understanding  (Jury 1)"),
            ("2", "Code Generation  (Jury 2)"),
            ("3", "Unit Test Validation  (3\u00d7 Claude)"),
            ("4", "Dataset Application"),
        ]
        self._plan_labels = {}
        for num, desc in tasks:
            row = tk.Frame(self.task_list_frame, bg=self.colors['bg'])
            row.pack(fill=tk.X, pady=3)
            icon = tk.Label(row, text="\u25cb", font=('Segoe UI', 11),
                            fg=self.colors['fg_muted'], bg=self.colors['bg'], width=3)
            icon.pack(side=tk.LEFT, padx=(4, 0))
            lbl = tk.Label(row, text=f"{num}. {desc}", font=('Segoe UI', 10),
                           fg=self.colors['fg'], bg=self.colors['bg'], anchor=tk.W)
            lbl.pack(side=tk.LEFT, fill=tk.X)
            self._plan_labels[num] = (icon, lbl)
        self.task_progress_var.set("0/4 tasks")
        self.progress_var.set(0)

    def _update_plan_step(self, step_num: str, state: str):
        """Update a task plan step icon/colour.  state: pending|active|done|failed."""
        if not hasattr(self, '_plan_labels') or step_num not in self._plan_labels:
            return
        icon, lbl = self._plan_labels[step_num]
        icons_map  = {'pending': '\u25cb', 'active': '\u23f3', 'done': '\u2713', 'failed': '\u2717'}
        colors_map = {
            'pending': (self.colors['fg_muted'], self.colors['fg_muted']),
            'active':  (self.colors['accent'],   self.colors['fg']),
            'done':    (self.colors['success'],   self.colors['fg']),
            'failed':  (self.colors['error'],     self.colors['error']),
        }
        ic, tc = colors_map.get(state, colors_map['pending'])
        icon.config(text=icons_map.get(state, '\u25cb'), fg=ic)
        lbl.config(fg=tc)
        done_count = sum(
            1 for _, (i, _) in self._plan_labels.items()
            if i.cget('text') == '\u2713'
        )
        self.task_progress_var.set(f"{done_count}/4 tasks")
        self.progress_var.set(done_count * 25)

    def _start_jury_from_plan(self, query: str):
        """Called when user clicks [Start] after task plan is shown."""
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self._update_plan_step("1", "active")
        self.add_agent_message(
            MessageType.THINKING,
            "Starting Integrated Jury workflow\u2026\n"
            "  Jury 1: understanding your requirement\n"
            "  Jury 2: checking catalog + generating code\n"
            "  Jury 1/2/3: validating with unit tests",
        )
        threading.Thread(
            target=self._jury_chat_start_thread,
            args=(query,),
            daemon=True,
        ).start()

    def _confirm_cp1_yes(self):
        """Checkpoint 1 confirmed \u2014 proceed with code generation."""
        self.set_approval_visible(False)
        self.confirm_yes_btn.config(command=self._on_confirm_yes)
        self.confirm_no_btn.config(command=self._on_confirm_no)
        if hasattr(self, '_jury_pending_requirements'):
            reqs, conf = self._jury_pending_requirements
            self.add_agent_message(
                MessageType.THINKING, "Running code generation + unit tests\u2026"
            )
            threading.Thread(
                target=self._jury_chat_resume_thread,
                args=(reqs, conf),
                daemon=True,
            ).start()

    def _confirm_cp1_no(self):
        """Checkpoint 1 cancelled \u2014 abort code generation."""
        self.set_approval_visible(False)
        self.confirm_yes_btn.config(command=self._on_confirm_yes)
        self.confirm_no_btn.config(command=self._on_confirm_no)
        self._update_plan_step("2", "failed")
        self._update_plan_step("3", "failed")
        self._update_plan_step("4", "failed")
        self.add_agent_message(MessageType.INFO, "Code generation cancelled by user.")

    def _confirm_cp2_yes(self):
        """Checkpoint 2 confirmed \u2014 apply code to repo and generate CSV."""
        self.set_approval_visible(False)
        self.confirm_yes_btn.config(command=self._on_confirm_yes)
        self.confirm_no_btn.config(command=self._on_confirm_no)
        if hasattr(self, '_jury_pending_code'):
            code, reqs = self._jury_pending_code
            threading.Thread(
                target=self._apply_jury_code_thread,
                args=(code, reqs),
                daemon=True,
            ).start()

    def _confirm_cp2_no(self):
        """Checkpoint 2 cancelled \u2014 do not apply code to repo."""
        self.set_approval_visible(False)
        self.confirm_yes_btn.config(command=self._on_confirm_yes)
        self.confirm_no_btn.config(command=self._on_confirm_no)
        self._update_plan_step("4", "failed")
        self.add_agent_message(MessageType.INFO, "Dataset application cancelled by user.")

    # ═══════════════════════════════════════════════════════════════════════════
    # MESSAGE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TASK PANEL
    # ═══════════════════════════════════════════════════════════════════════════
    
    # NATURAL LANGUAGE PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    

    def jury_start_new_request(self):
        """Start a new request in integrated jury system"""
        if not self.integrated_jury:
            messagebox.showerror("Error", "Integrated jury system not available")
            return
        
        user_question = self.jury_input.get('1.0', tk.END).strip()
        
        if not user_question:
            messagebox.showwarning("Empty Input", "Please describe what you need")
            return
        
        # Clear input
        self.jury_input.delete('1.0', tk.END)
        
        # Log user question
        self.jury_log(f"YOU: {user_question}", 'question')
        self.jury_log("Starting integrated jury workflow...", 'thinking')
        
        # Update status
        self.jury_status_var.set("Processing your request...")
        self.jury_session_active = True
        self.jury_session_info.set(f"Session: {self.integrated_jury.session_id}")
        
        # Run workflow in background thread
        thread = threading.Thread(
            target=self._jury_run_workflow_thread,
            args=(user_question,),
            daemon=True
        )
        thread.start()

    def _jury_run_workflow_thread(self, user_question: str):
        """Run integrated jury workflow in background thread"""
        try:
            def progress_callback(msg):
                self.root.after(0, lambda m=msg: self.jury_log(m, 'system'))
            
            result = self.integrated_jury.run_full_workflow(
                user_question=user_question,
                progress_callback=progress_callback
            )
            
            # Handle result on main thread
            self.root.after(0, lambda r=result: self._jury_handle_result(r))
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda m=error_msg: self.jury_log(m, 'error'))
            self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

    def _jury_handle_result(self, result: Dict):
        """Handle result from jury workflow"""
        status = result.get('status')
        
        if status == 'needs_clarification':
            # Need user to answer clarifying questions
            self.jury_clarification_pending = True
            self.jury_answer_btn.configure(state=tk.NORMAL)
            
            self.jury_log("I need more information to help you:", 'question')
            for q in result.get('questions', []):
                self.jury_log(f"  • {q}", 'question')
            
            self.jury_log(f"\nMy current understanding ({result.get('confidence', 0)}% confident):", 'thinking')
            self.jury_log(result.get('current_understanding', ''), 'thinking')
            
            self.jury_status_var.set("Please answer the clarifying questions above")
            
        elif status == 'success':
            # Success! Show code
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)
            
            self.jury_log(" Code generated and validated!", 'system')
            self.jury_log(f"\nIterations: {result['iterations']}", 'system')
            self.jury_log(f"Test Results: {result['test_results']['passing_llms']}/3 LLMs passed", 'system')
            self.jury_log(f"Total Tests: {result['test_results']['total_passed']}/{result['test_results']['total_tests']} passed", 'system')
            
            self.jury_log("\n" + "="*60, 'system')
            self.jury_log("GENERATED CODE:", 'system')
            self.jury_log("="*60, 'system')
            self.jury_log(result['code'], 'answer')
            
            self.jury_status_var.set("Code ready to use")
            self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
            
            # Offer to save code
            self.root.after(100, lambda r=result: self._jury_offer_save_code(r))
            
        elif status == 'human_intervention_required':
            # Failed after max iterations
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)
            
            self.jury_log("  HUMAN INTERVENTION NEEDED", 'error')
            self.jury_log(f"\n{result['message']}", 'error')
            self.jury_log(f"\nAttempted {len(result['iterations'])} iterations", 'error')
            
            if result.get('last_code'):
                self.jury_log("\nLast generated code (may have issues):", 'thinking')
                self.jury_log(result['last_code'], 'answer')
            
            if result.get('last_feedback'):
                self.jury_log("\nLast test feedback:", 'error')
                self.jury_log(result['last_feedback'], 'error')
            
            self.jury_status_var.set("  Failed - Human help needed")
            self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
            
        else:
            self.jury_log(f"Unknown status: {status}", 'error')

    def jury_provide_feedback(self):
        """Provide answers to clarifying questions"""
        if not self.jury_clarification_pending:
            messagebox.showinfo("Info", "No clarification needed at this time")
            return
        
        user_feedback = self.jury_input.get('1.0', tk.END).strip()
        
        if not user_feedback:
            messagebox.showwarning("Empty Input", "Please provide your answers")
            return
        
        # Clear input
        self.jury_input.delete('1.0', tk.END)
        
        # Log feedback
        self.jury_log(f"\nYOU: {user_feedback}", 'answer')
        self.jury_log("Processing your feedback...", 'thinking')
        
        # Update status
        self.jury_status_var.set("Processing feedback...")
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        # Continue clarification in thread
        thread = threading.Thread(
            target=self._jury_continue_clarification_thread,
            args=(user_feedback,),
            daemon=True
        )
        thread.start()

    def _jury_resume_after_clarification_thread(self, requirements: Dict, confidence: float):
        """Auto-resume full workflow after clarification completes"""
        try:
            def progress_callback(msg):
                self.root.after(0, lambda m=msg: self.jury_log(m, 'system'))

            result = self.integrated_jury.resume_after_clarification(
                requirements=requirements,
                confidence=confidence,
                progress_callback=progress_callback
            )

            self.root.after(0, lambda r=result: self._jury_handle_result(r))

        except Exception as e:
            error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda m=error_msg: self.jury_log(m, 'error'))
            self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

    def _jury_continue_clarification_thread(self, user_feedback: str):
        """Continue clarification process in background"""
        try:
            result = self.integrated_jury.provide_clarification(user_feedback)
            
            self.root.after(0, lambda r=result: self._jury_handle_clarification_result(r))
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda m=error_msg: self.jury_log(m, 'error'))
            self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

    def _jury_handle_clarification_result(self, result: Dict):
        """Handle clarification result"""
        if result['status'] == 'clarified':
            self.jury_log(" Requirements fully understood! Automatically starting code generation...", 'system')
            self.jury_log(f"Confidence: {result.get('confidence', 100):.0f}%", 'thinking')
            self.jury_status_var.set("Requirements clear — generating code now...")
            self.jury_clarification_pending = False
            self.jury_answer_btn.configure(state=tk.DISABLED)

            # Auto-resume: run Phase 1.5 + Phase 2 with the clarified requirements
            thread = threading.Thread(
                target=self._jury_resume_after_clarification_thread,
                args=(result['requirements'], result.get('confidence', 100)),
                daemon=True
            )
            thread.start()
        else:
            # Need more clarification
            self.jury_clarification_pending = True
            self.jury_answer_btn.configure(state=tk.NORMAL)
            
            self.jury_log("\nI still need a bit more information:", 'question')
            for q in result.get('questions', []):
                self.jury_log(f"  • {q}", 'question')
            
            self.jury_log(f"\nMy understanding so far ({result.get('confidence', 0)}% confident):", 'thinking')
            self.jury_log(result.get('current_understanding', ''), 'thinking')
            
            self.jury_status_var.set("Please provide more details")

    def jury_reset_session(self):
        """Reset jury session"""
        if self.jury_session_active:
            confirm = messagebox.askyesno("Confirm Reset", 
                                          "Are you sure you want to reset the current session?")
            if not confirm:
                return
        
        # Reset state
        try:
            from integrated_jury_system import IntegratedJurySystem
            self.integrated_jury = IntegratedJurySystem()
            self.jury_session_active = False
            self.jury_clarification_pending = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset: {str(e)}")
            return
        
        # Clear UI
        self.jury_conversation.configure(state=tk.NORMAL)
        self.jury_conversation.delete('1.0', tk.END)
        self.jury_conversation.configure(state=tk.DISABLED)
        
        self.jury_input.delete('1.0', tk.END)
        
        # Reset status
        self.jury_status_var.set("Ready to help! Describe what you need...")
        self.jury_session_info.set("No active session")
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        self.jury_log("Session reset. Ready for new request!", 'system')

    def _jury_offer_save_code(self, result: Dict):
        """Offer to save generated code AND generate dataset with it"""
        
        # Offer dataset generation first
        dataset_response = messagebox.askyesnocancel(
            "Dataset Generation",
            f"  Code validated by {result['test_results']['passing_llms']}/3 LLMs!\n\n"
            f"Function: {result['function_name']}\n"
            f"Description: {result['description'][:100]}...\n\n"
            f"Would you like to generate a REAL dataset using this code?\n\n"
            f"• Yes → Generate dataset from your repository\n"
            f"• No → Just save the code file\n"
            f"• Cancel → Do nothing"
        )
        
        if dataset_response is None:  # Cancel
            return
        
        if dataset_response:  # Yes - Generate dataset
            if not hasattr(self, 'repo_path') or not self.repo_path:
                messagebox.showerror("Repository Required", 
                    "Please set a repository path first!\n\n"
                    "Go to Repository tab → Browse/Clone a repo")
                return
            
            self.jury_log("\n  Starting dataset generation with validated code...", 'system')
            
            # Convert jury result to custom metrics format
            custom_metric = self._convert_jury_to_metric_format(result)
            self.custom_metrics_to_apply = [custom_metric]
            
            # Show confirmation
            confirm = messagebox.askyesno(
                "Confirm Dataset Generation",
                f"Ready to generate dataset:\n\n"
                f"Repository: {self.repo_path}\n"
                f"Custom Metric: {result['function_name']}\n"
                f"Validated: {result['test_results']['total_passed']}/{result['test_results']['total_tests']} tests passed\n\n"
                f"This will extract base metrics from your repo\n"
                f"and apply the validated custom metric code.\n\n"
                f"Continue?"
            )
            
            if confirm:
                # Trigger dataset generation in background
                thread = threading.Thread(
                    target=self._generate_dataset_with_jury_code,
                    args=(result,),
                    daemon=True
                )
                thread.start()
            
        else:  # No - Just save code to file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                initialfile=f"{result['function_name']}.py"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w') as f:
                        f.write(f"# Generated by Integrated Jury System\n")
                        f.write(f"# Session: {result['session_id']}\n")
                        f.write(f"# Validation: {result['test_results']['passing_llms']}/3 LLMs passed\n")
                        f.write(f"# Description: {result['description']}\n\n")
                        f.write(result['code'])
                    
                    messagebox.showinfo("Success", f"Code saved to:\n{file_path}")
                    self.jury_log(f"\n💾 Code saved to: {file_path}", 'system')
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save code:\n{str(e)}")
    
    def _convert_jury_to_metric_format(self, jury_result: Dict) -> Dict:
        """Convert integrated jury result to custom metrics format for apply_custom_metrics"""
        return {
            'name': jury_result['function_name'],
            'expression': f"Generated by integrated jury system",
            'formula': jury_result['description'],
            'code': jury_result['code'],
            'custom_metrics': []  # Jury code should handle all dependencies
        }
    
    def _generate_dataset_with_jury_code(self, jury_result: Dict):
        """Generate dataset by directly executing the validated calculate() on every repo file."""
        import tempfile
        import importlib.util
        import sys as _sys
        import json as _json

        try:
            requirements = jury_result.get('requirements', {})
            lang         = requirements.get('language', 'java')
            output_fmt   = (requirements.get('output_format', 'csv') or 'csv')
            func_name    = jury_result.get('function_name', 'dataset')
            session_dir  = jury_result.get('session_dir')

            # ── Pick file extensions from requirements language ─────────────
            ext_map   = {'java': ('.java',), 'python': ('.py',), 'any': ('.java', '.py')}
            target_exts = ext_map.get(lang, ('.java',))
            skip_dirs = {'.git', 'build', 'target', '__pycache__', 'node_modules', '.gradle'}

            repo   = Path(self.repo_path)
            files  = [
                fp for pattern in target_exts
                for fp in repo.rglob(f'*{pattern}')
                if not any(p in skip_dirs for p in fp.parts)
            ]

            if not files:
                self.root.after(0, lambda: self.add_agent_message(
                    MessageType.ERROR,
                    f"No {lang} files found in: {self.repo_path}"))
                return

            self.root.after(0, lambda n=len(files): self.add_agent_message(
                MessageType.INFO, f"Found {n} file(s). Running validated metric code…"))

            # ── Load validated code as a module ────────────────────────────
            dataset_root = str(Path(__file__).parent.parent)
            tmp = Path(tempfile.mktemp(suffix='_jury_metric.py'))
            tmp.write_text(jury_result['code'], encoding='utf-8')

            try:
                for p in (dataset_root, str(tmp.parent)):
                    if p not in _sys.path:
                        _sys.path.insert(0, p)

                spec = importlib.util.spec_from_file_location('_jury_metric', tmp)
                mod  = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                def _flatten(d: dict, prefix: str = '') -> dict:
                    out = {}
                    for k, v in d.items():
                        key = f"{prefix}.{k}" if prefix else k
                        if isinstance(v, dict):
                            out.update(_flatten(v, key))
                        else:
                            out[key] = str(v) if isinstance(v, list) else v
                    return out

                rows  = []
                total = len(files)
                for idx, fp in enumerate(files, 1):
                    try:
                        result = mod.calculate(str(fp), str(repo))
                        if isinstance(result, dict):
                            core = result.get('metrics') if isinstance(result.get('metrics'), dict) else result
                            row  = {'file': str(fp.relative_to(repo))}
                            row.update(_flatten({k: v for k, v in core.items()
                                                 if k not in ('benchmarks', 'error')}))
                            if result.get('error'):
                                row['_error'] = str(result['error'])
                            rows.append(row)
                    except Exception:
                        pass

                    if idx % 50 == 0:
                        self.root.after(0, lambda i=idx, t=total: self.add_agent_message(
                            MessageType.INFO, f"Progress: {i}/{t}"))

            finally:
                try:
                    tmp.unlink()
                except Exception:
                    pass

            if not rows:
                self.root.after(0, lambda: self.add_agent_message(
                    MessageType.ERROR,
                    "No data extracted. Verify the metric code runs on your repo files."))
                return

            # ── Build column order ─────────────────────────────────────────
            seen: dict = {}
            for row in rows:
                for k in row:
                    seen.setdefault(k, None)
            all_cols = list(seen.keys())

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            out_dir   = Path(session_dir) if session_dir else Path('generated_datasets')
            out_dir.mkdir(parents=True, exist_ok=True)

            # ── Write output ───────────────────────────────────────────────
            if output_fmt == 'jsonl':
                out_file = out_dir / f"{func_name}_{timestamp}.jsonl"
                with open(out_file, 'w', encoding='utf-8') as f:
                    for row in rows:
                        f.write(_json.dumps(row, default=str) + '\n')
            elif output_fmt == 'json':
                out_file = out_dir / f"{func_name}_{timestamp}.json"
                with open(out_file, 'w', encoding='utf-8') as f:
                    _json.dump(rows, f, indent=2, default=str)
            else:
                out_file = out_dir / f"{func_name}_{timestamp}.csv"
                with open(out_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=all_cols, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(rows)

            msg = (
                f" Dataset saved!\n"
                f"  File    : {out_file}\n"
                f"  Records : {len(rows)}\n"
                f"  Columns : {len(all_cols)}\n"
                f"  Format  : {output_fmt}"
            )
            self.root.after(0, lambda m=msg: self.add_agent_message(MessageType.SUCCESS, m))
            self.root.after(0, lambda: messagebox.showinfo(
                "Dataset Generated!",
                f"File: {out_file}\nRecords: {len(rows)}\nColumns: {len(all_cols)}"
            ))

        except Exception as e:
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(
                MessageType.ERROR, f" Dataset generation failed:\n{msg}"))
    


