"""FormulaTabMixin — formula processing, enhanced system integration."""
import tkinter as tk
from tkinter import messagebox
import threading
import traceback
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from pathlib import Path
try:
    from .gui_types import MessageType
except ImportError:
    from gui_types import MessageType


class FormulaTabMixin:
    def process_unified_input(self):
        """LEGACY - redirect to chat input"""
        self.process_chat_input()
    
    def process_natural_language(self):
        """LEGACY - redirects to unified processor"""
        query = self.nl_input_var.get().strip() if hasattr(self, 'nl_input_var') else self.unified_input_var.get().strip()
        
        if not query or 'e.g.' in query or 'Type anything' in query:
            messagebox.showwarning("Input Required", "Please describe what you want to create")
            return
        
        # Store last request for feedback processing
        self.last_user_request = query
        
        # Show user message
        self.add_agent_message(MessageType.USER, query)
        if hasattr(self, 'nl_input_var'):
            self.nl_input_var.set("")
        else:
            self.unified_input_var.set("")
        
        # Show thinking
        self.add_agent_message(MessageType.THINKING, "Analyzing your request...")
        
        # CHECK: Is this a request for BENCHMARK dataset or REAL repo analysis?
        query_lower = query.lower()
        is_benchmark_request = any(b.lower() in query_lower for b in self.BENCHMARK_DATASETS.keys())
        
        if is_benchmark_request:
            # USE ORIGINAL: Benchmark dataset generation (predefined formats)
            self.add_agent_message(MessageType.INFO, 
                "Detected benchmark dataset request. Using predefined format generation.")
            threading.Thread(target=self._create_plan_from_input, 
                            args=(query,), daemon=True).start()
        else:
            # USE ENHANCED: Real repository analysis with LLM
            if not self.repo_path:
                self.add_agent_message(MessageType.ERROR, 
                    "ERROR real repository analysis requires a repository to be set first.")
                messagebox.showwarning("Repository Required", 
                    "For custom metrics analysis, please set a repository first.\n\n"
                    "Or use benchmark datasets (Defects4J, Bugs.jar, etc.) which don't need a repo.")
                return
            
            if self.enhanced_system:
                self.add_agent_message(MessageType.INFO, 
                    "Using AI-powered repository analysis with LLM.")
                self._process_with_enhanced_system(query)
            else:
                # Fallback to basic
                threading.Thread(target=self._create_plan_from_input, 
                                args=(query,), daemon=True).start()
    
    def _process_with_enhanced_system(self, query: str):
        """Process ALL queries via EnhancedAgenticSystem (Bedrock Claude 3) - NO hardcoded bypasses"""
        if not self.enhanced_system:
            self.add_agent_message(MessageType.ERROR, "  Agent not initialized")
            return
        
        # Set repository if not already set
        if not self.enhanced_system.repo_path or str(self.enhanced_system.repo_path) != str(self.repo_path):
            try:
                self.add_agent_message(MessageType.THINKING, 
                    "🔧 Setting up repository...")
                self.enhanced_system.set_repository(self.repo_path)
            except Exception as e:
                self.add_agent_message(MessageType.ERROR, f"Repository setup failed: {e}")
                return
        
        # Start conversation in background thread - Bedrock handles everything
        thread = threading.Thread(target=self._enhanced_conversation_thread, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _enhanced_conversation_thread(self, query: str):
        """Handle enhanced system conversation in background"""
        try:
            # Start conversation
            result = self.enhanced_system.start_conversation(query)
            
            # Display conversation messages
            self._display_enhanced_messages()
            
            # Handle result status
            while result['status'] in ['needs_feedback', 'needs_clarification', 'needs_approval_for_formula_generation', 
                                       'awaiting_approval', 'awaiting_final_approval']:
                
                if result['status'] == 'needs_feedback':
                    # Waiting for user to confirm analysis
                    self.awaiting_analysis_confirmation = True
                    self.root.after(0, lambda: self._setup_enhanced_input_handler("Type 'yes' to proceed, or describe what to change"))
                    break
                
                elif result['status'] == 'needs_clarification':
                    # Wait for user response
                    question = result['question']
                    self.root.after(0, lambda: self._setup_enhanced_input_handler(question))
                    break
                    
                elif result['status'] == 'needs_approval_for_formula_generation':
                    # Show formulas that need to be generated
                    formulas_text = "**New Formulas Needed:**\n\n"
                    for formula_name in result['missing_formulas']:
                        formulas_text += f"  • {formula_name}\n"
                    formulas_text += "\nLLM will generate Python code for these. Approve?"
                    
                    self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION, formulas_text))
                    self.root.after(0, lambda: self._setup_approval_buttons(
                        on_approve=lambda: self._approve_formula_generation(result),
                        on_reject=lambda: self._reject_formula_generation()
                    ))
                    break
                    
                elif result['status'] == 'awaiting_approval':
                    # Show plan approval buttons
                    self.root.after(0, lambda: self._setup_approval_buttons(
                        on_approve=lambda: self._approve_plan(),
                        on_reject=lambda: self._reject_plan(),
                        on_modify=lambda: self._modify_plan()
                    ))
                    break
                    
                elif result['status'] == 'awaiting_final_approval':
                    # Show final approval after preview
                    preview_text = f"**Preview Ready!**\n\n"
                    preview_text += f"**Total Rows:** {result['total_rows']}\n"
                    preview_text += f"**Columns:** {len(result['preview'])}\n\n"
                    
                    for col_preview in result['preview']:
                        preview_text += f"**{col_preview.column_name}** ({col_preview.data_type})\n"
                        preview_text += f"  Formula: {col_preview.formula}\n"
                        preview_text += f"    Sample: {col_preview.sample_values[:3]}\n"
                        if col_preview.min_value is not None:
                            preview_text += f"    Range: [{col_preview.min_value:.2f} - {col_preview.max_value:.2f}]\n"
                        preview_text += f"Unique: {col_preview.unique_count}\n\n"
                    
                    self.root.after(0, lambda: self.add_agent_message(MessageType.PREVIEW, preview_text))
                    self.root.after(0, lambda: self._setup_final_approval_buttons(
                        on_confirm=lambda: self._confirm_generation(),
                        on_cancel=lambda: self._cancel_generation()
                    ))
                    break
            
            # If completed, show result
            if result['status'] == 'completed':
                success_text = f"**Dataset Generated!**\n\n"
                success_text += f"**Files:**\n"
                success_text += f"  • CSV: {result['csv_file']}\n"
                success_text += f"  • JSON: {result['json_file']}\n"
                success_text += f"  • Metadata: {result['metadata_file']}\n\n"
                success_text += f"**Statistics:**\n"
                success_text += f"  • Rows: {result['rows']:,}\n"
                success_text += f"  • Columns: {result['columns']}\n"
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, success_text))
                
        except Exception as e:
            error_msg = f"**Error:** {str(e)}"
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, error_msg))
    
    def _display_enhanced_messages(self):
        """Display messages from enhanced system"""
        # Get conversation history
        history = self.enhanced_system.get_conversation_history()
        
        # Display new messages (skip already displayed ones)
        displayed_count = getattr(self, '_displayed_message_count', 0)
        new_messages = history[displayed_count:]
        
        for msg in new_messages:
            msg_type_str = msg['type']
            content = msg['content']
            
            # Map enhanced message types to GUI message types
            type_mapping = {
                'system': MessageType.SYSTEM,
                'user': MessageType.USER,
                'agent': MessageType.INFO,
                'thinking': MessageType.THINKING,
                'plan': MessageType.INFO,
                'question': MessageType.QUESTION,
                'preview': MessageType.INFO,
                'success': MessageType.SUCCESS,
                'error': MessageType.ERROR
            }
            
            gui_type = type_mapping.get(msg_type_str, MessageType.INFO)
            self.root.after(0, lambda c=content, t=gui_type: self.add_agent_message(t, c))
        
        self._displayed_message_count = len(history)
    
    def _setup_enhanced_input_handler(self, question: str):
        """Setup input handler for clarification question"""
        # Enable agent input for response
        if hasattr(self, 'agent_input'):
            self.agent_input.config(state=tk.NORMAL)
            self.agent_input.delete(0, tk.END)
            self.agent_input.insert(0, "Type your answer here...")
            self.agent_input.bind('<Return>', 
                lambda e: self._handle_clarification_response(self.agent_input.get()))
    
    def _enhanced_continue_conversation_thread(self, feedback: str):
        """Continue enhanced conversation after analysis confirmation"""
        try:
            # Send feedback to enhanced system
            result = self.enhanced_system.continue_conversation(feedback)
            
            # Display new messages
            self._display_enhanced_messages()
            
            # Handle result status
            while result['status'] in ['needs_feedback', 'needs_clarification', 'awaiting_approval']:
                
                if result['status'] == 'needs_feedback':
                    # Another analysis/confirmation round
                    self.awaiting_analysis_confirmation = True
                    self.root.after(0, lambda: self._setup_enhanced_input_handler("Confirm or describe changes"))
                    break
                
                elif result['status'] == 'needs_clarification':
                    # Ask clarification question
                    question = result.get('question', 'Please clarify')
                    self.root.after(0, lambda: self._setup_enhanced_input_handler(question))
                    break
                
                elif result['status'] == 'awaiting_approval':
                    # Show plan for approval
                    plan_text = result.get('plan', 'Plan ready for approval')
                    self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION, plan_text))
                    self.root.after(0, lambda: self._setup_approval_buttons(
                        on_approve=lambda: self._approve_plan(),
                        on_reject=lambda: self._reject_plan()
                    ))
                    break
            
            # If completed, show result
            if result['status'] == 'completed':
                success_text = f"**Dataset Generated!**\n\n"
                success_text += f"**Files:**\n"
                for key, value in result.get('files', {}).items():
                    success_text += f"  • {key}: {value}\n"
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, success_text))
        
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, f"Error: {str(e)}"))
    
    def _handle_clarification_response(self, response: str):
        """Handle user's clarification response"""
        if not response or 'Type your answer' in response:
            return
        
        self.add_agent_message(MessageType.USER, f"  {response}")
        
        # Continue conversation in background
        thread = threading.Thread(target=self._continue_enhanced_conversation, args=(response,))
        thread.daemon = True
        thread.start()
    
    def _continue_enhanced_conversation(self, response: str):
        """Continue the enhanced conversation - triggers dataset generation when ready"""
        try:
            result = self.enhanced_system.continue_conversation(response)
            self._display_enhanced_messages()
            
            # Handle all possible statuses - same logic as _enhanced_conversation_thread
            if result['status'] == 'needs_clarification':
                question = result.get('question', '')
                self.root.after(0, lambda: self._setup_enhanced_input_handler(question))
            
            elif result['status'] == 'awaiting_approval':
                self.root.after(0, lambda: self._setup_approval_buttons(
                    on_approve=lambda: self._approve_plan(),
                    on_reject=lambda: self._reject_plan(),
                    on_modify=lambda: self._modify_plan()
                ))
            
            elif result['status'] == 'awaiting_final_approval':
                preview_text = "**Preview Ready! Confirm to generate?**\n\n"
                for col_preview in result.get('preview', []):
                    preview_text += f"• **{col_preview.column_name}**: {col_preview.formula}\n"
                    preview_text += f"  Sample: {col_preview.sample_values[:3]}\n"
                self.root.after(0, lambda: self.add_agent_message(MessageType.PREVIEW, preview_text))
                self.root.after(0, lambda: self._setup_final_approval_buttons(
                    on_confirm=lambda: self._confirm_generation(),
                    on_cancel=lambda: self._cancel_generation()
                ))
            
            elif result['status'] == 'completed':
                success_text = f"  **Dataset Generated!**\n\n"
                success_text += f"  CSV: {result.get('csv_file', 'N/A')}\n"
                success_text += f"  JSON: {result.get('json_file', 'N/A')}\n"
                success_text += f"  Rows: {result.get('rows', 'N/A')}, Columns: {result.get('columns', 'N/A')}"
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, success_text))

        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Error: {str(e)}"))
    

    def _approve_formula_generation(self, result):
        """Approve formula generation and execute comprehensive test validation"""
        self.add_agent_message(MessageType.SUCCESS, "Formula generation approved. Running jury verification...")
        
        # Generate formulas with jury verification
        self.enhanced_system._generate_missing_formulas()
        
        # Capture generated formulas for later use in dataset generation
        if self.enhanced_system.generated_formulas:
            self.custom_metrics_to_apply = self.enhanced_system.generated_formulas
            num_formulas = len(self.enhanced_system.generated_formulas)
            self.add_agent_message(MessageType.SUCCESS, 
                f"{num_formulas} custom formula(s) approved by jury")
            
            # Display all messages including jury voting
            self._display_enhanced_messages()
            
            # ═══════════════════════════════════════════════════════════════
            # NEW: Execute comprehensive test validation with 5-iteration retry
            # ═══════════════════════════════════════════════════════════════
            if self.test_executor and hasattr(self, 'repo_path') and self.repo_path:
                self.add_agent_message(MessageType.THINKING, 
                    "Starting unit test generation and validation...\n"
                    "System will: Generate tests → Execute → Retry up to 5 times if needed")
                
                # Prepare sample data from repository
                sample_data = self._prepare_sample_data_for_testing()
                
                validation_success = True
                for idx, formula in enumerate(self.enhanced_system.generated_formulas, 1):
                    self.add_agent_message(MessageType.INFO,
                        f"\n{'='*60}\n"
                        f"Formula {idx}/{num_formulas}: {formula.name}\n"
                        f"{'='*60}")
                    
                    try:
                        # Execute full workflow with test generation, execution, and auto-fix
                        report = self.test_executor.execute_full_workflow(
                            metric_description=formula.description,
                            available_metrics=self.available_metrics or {},
                            sample_data=sample_data,
                            base_metrics=self.available_metrics or {},
                            num_judges=3,
                            auto_fix=True  # Enable 5-iteration retry
                        )
                        
                        # Display comprehensive test results
                        self._display_test_results(report, formula.name)
                        
                        if not report['overall_success']:
                            self.add_agent_message(MessageType.ERROR,
                                f"Test validation FAILED for '{formula.name}' after 5 iterations\n"
                                f" Human review required\n"
                                f" Check: {report['stages'].get('validation', {}).get('run_directory', 'N/A')}")
                            validation_success = False
                            # Don't break - test all formulas to show complete status
                    
                    except Exception as e:
                        self.add_agent_message(MessageType.ERROR,
                            f"Test execution failed for '{formula.name}': {str(e)[:200]}")
                        validation_success = False
                
                if validation_success:
                    self.add_agent_message(MessageType.SUCCESS,
                        f"\nAll {num_formulas} formula(s) validated successfully!\n"
                        f"Ready for full dataset generation with validated code")
                else:
                    self.add_agent_message(MessageType.ERROR,
                        f"\n Some formulas failed validation\n"
                        f"   Review failed tests before dataset generation")
            else:
                if not self.test_executor:
                    self.add_agent_message(MessageType.ERROR,
                        "Test executor not available - skipping test validation")
                else:
                    self.add_agent_message(MessageType.ERROR,
                        "No repository set - skipping test validation")
        
        # Display final messages
        self._display_enhanced_messages()
        
        # Prepare for full dataset generation using enhanced_system
        self.add_agent_message(MessageType.THINKING, 
            "Preparing full dataset generation with all 65+ metrics...")
        
        # Mark that we should use enhanced_system for generation
        self.use_enhanced_generation = True
    
    def _reject_formula_generation(self):
        """Reject formula generation"""
        self.add_agent_message(MessageType.ERROR, "  Formula generation rejected. Operation cancelled.")
    
    def _prepare_sample_data_for_testing(self) -> Dict:
        """Prepare sample data from repository for test execution"""
        try:
            # Try to get real metrics from repository
            if hasattr(self, 'available_metrics') and self.available_metrics:
                # Use existing metrics if available
                return dict(list(self.available_metrics.values())[:1][0]) if self.available_metrics.values() else {}
            
            # Fallback: Generate sample data
            sample_data = {
                'lines_of_code': 1000,
                'cyclomatic_complexity': 5,
                'bug_count': 3,
                'test_coverage': 0.75,
                'code_churn': 150,
                'commit_count': 50
            }
            return sample_data
        except Exception as e:
            print(f"Could not prepare sample data: {e}")
            return {'lines_of_code': 1000, 'bug_count': 5}
    
    def _display_test_results(self, report: Dict, formula_name: str):
        """
        Display comprehensive test execution results in GUI
        Shows: Code generation → Test generation → Execution → Iterations → Final status
        """
        stages = report.get('stages', {})
        
        # Stage 1: Code Generation Status
        if 'code_generation' in stages:
            code_info = stages['code_generation']
            if code_info['status'] == 'approved':
                self.add_agent_message(MessageType.SUCCESS,
                    f"Stage 1: Code generation approved by {code_info.get('votes', 3)} judges")
            else:
                self.add_agent_message(MessageType.ERROR,
                    f"Stage 1: Code generation failed")
                return
        
        # Stage 2: Test Generation Status
        if 'test_generation' in stages:
            test_info = stages['test_generation']
            test_count = test_info.get('test_count', 0)
            quality_score = test_info.get('quality_score', 0)
            
            status_icon = "OK" if test_info.get('is_approved', False) else "[WARNING]"
            self.add_agent_message(MessageType.INFO,
                f"{status_icon} Stage 2: Generated {test_count} unit tests "
                f"(Quality: {quality_score:.0f}%)")
        
        # Stage 3: Test Execution with Iteration Details
        if 'test_execution' in stages:
            exec_info = stages['test_execution']
            iteration = exec_info.get('iteration', 1)
            passed = exec_info.get('passed', 0)
            failed = exec_info.get('failed', 0)
            errors = exec_info.get('errors', 0)
            total = exec_info.get('total_tests', 0)
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            required = (total * 2 + 2) // 3  # 2/3 threshold
            
            self.add_agent_message(MessageType.INFO,
                f"[STEP 3] Test Execution - Iteration {iteration}/5\n"
                f"   Passed: {passed}/{total} tests ({pass_rate:.1f}%)\n"
                f"   Failed: {failed} tests\n"
                f"   Errors: {errors}\n"
                f"   Required: {required}/{total} ({required/total*100:.0f}%) for approval")
        
        # Stage 4: Final Validation Status
        if 'validation' in stages:
            val_info = stages['validation']
            
            if val_info['status'] == 'success':
                iterations_taken = val_info.get('iteration', 1)
                total_tests = val_info.get('total_tests', 0)
                passed_final = val_info.get('passed', 0)
                
                self.add_agent_message(MessageType.SUCCESS,
                    f"VALIDATION SUCCESSFUL for '{formula_name}'\n"
                    f"Iterations: {iterations_taken}/5\n"
                    f"Final: {passed_final}/{total_tests} tests passed\n"
                    f"Results: {val_info.get('run_directory', 'N/A')}")
            
            elif val_info['status'] == 'failed_max_retries':
                iterations = val_info.get('iterations', 5)
                last_passed = val_info.get('last_passed', 0)
                last_failed = val_info.get('last_failed', 0)
                run_dir = val_info.get('run_directory', 'N/A')
                
                self.add_agent_message(MessageType.ERROR,
                    f"VALIDATION FAILED for '{formula_name}'\n"
                    f" Max iterations reached: {iterations}/5\n"
                    f" Last result: {last_passed} passed, {last_failed} failed\n"
                    f" Manual review required\n"
                    f" Check iteration logs: {run_dir}\n"
                    f" {val_info.get('note', 'See logs for details')}")
            else:
                self.add_agent_message(MessageType.ERROR,
                    f"Validation failed with status: {val_info['status']}")
    
    def _reject_formula_generation_old(self):
        """Reject formula generation (renamed old method)"""
        self.add_agent_message(MessageType.ERROR, "  Formula generation rejected. Operation cancelled.")
    

    def process_dynamic_formulas(self):
        """Process dynamic formulas using Multi-LLM Jury System"""
        if not hasattr(self, 'llm_jury_system') or not self.llm_jury_system:
            self.add_agent_message(MessageType.ERROR, 
                "Multi-LLM Jury System not available. Check .env for API keys.")
            return
        
        formula_text = self.formula_input.get('1.0', tk.END).strip()
        if not formula_text or 'Example:' in formula_text:
            self.add_agent_message(MessageType.ERROR, "Please enter formula request")
            return
        
        # Clear formula input
        self.formula_input.delete('1.0', tk.END)
        
        self.add_agent_message(MessageType.USER, f"Dynamic Formula Request:\n{formula_text}")
        self.add_agent_message(MessageType.THINKING, "Starting Multi-LLM Jury System...")
        
        # Run in background
        threading.Thread(target=self._execute_dynamic_formulas, 
                        args=(formula_text,), daemon=True).start()
    
    def _execute_dynamic_formulas(self, formula_text: str):
        """Execute dynamic formula generation with Multi-LLM Jury"""
        try:
            # Step 1: Understand request
            self.root.after(0, lambda: self.jury_status_var.set("Understanding request..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION, 
                "Step 1: Generator LLM understanding your request..."))
            
            understanding = self.llm_jury_system.understand_user_request(formula_text)
            formulas = understanding.get('formulas', [])
            
            if not formulas:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    "Could not extract formulas from request. Try being more specific."))
                self.root.after(0, lambda: self.jury_status_var.set("Ready | 1 Generator + 3 Verifiers"))
                return
            
            # Show what was understood and ASK FOR CONFIRMATION
            formula_list = "\n".join([f"  {i+1}. {f.get('name', 'Unknown')}: {f.get('expression', 'N/A')}" 
                                     for i, f in enumerate(formulas)])
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                f"I understood your request:\n\n"
                f"Formulas to calculate:\n{formula_list}\n\n"
                f"Data source: Mock data (50 rows)\n"
                f"Output folder: generate_dataset/\n\n"
                f"  This will:\n"
                f"  1. Generate Python code dynamically (Generator LLM)\n"
                f"  2. Verify with 3 independent LLMs (Jury)\n"
                f"  3. Execute code temporarily (self-destructs after)\n"
                f"  4. Save result CSV to generate_dataset/\n\n"
                f"Cost: ~$0.005 (5 AWS calls)\n\n"
                f"Type 'yes' or 'confirm' in chat to proceed, or 'no' to cancel."))
            
            # Store for later execution
            self.pending_formula_execution = {
                'formulas': formulas,
                'formula_text': formula_text
            }
            self.root.after(0, lambda: self.jury_status_var.set("Waiting for your confirmation..."))
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"Understanding error: {e}\n\nDetails:\n{error_detail}"))
            self.root.after(0, lambda: self.jury_status_var.set("Error - check logs"))
    
    def _continue_formula_execution(self):
        """Continue formula execution after user confirmation"""
        if not hasattr(self, 'pending_formula_execution') or not self.pending_formula_execution:
            self.add_agent_message(MessageType.ERROR, "No pending formula execution")
            return
        
        formulas = self.pending_formula_execution['formulas']
        
        self.add_agent_message(MessageType.ACTION, "  Confirmed! Starting execution...")
        
        # Run in background thread
        threading.Thread(target=self._run_formula_generation, 
                        args=(formulas,), daemon=True).start()
    
    def _run_formula_generation(self, formulas):
        """Actually run the formula generation (called after confirmation)"""
        try:
            # Step 2: Generate code
            self.root.after(0, lambda: self.jury_status_var.set("Generating code..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 2: Generator LLM writing Python code dynamically..."))
            
            # Create mock data for testing
            mock_data = pd.DataFrame({
                'lines_of_code': np.random.randint(100, 5000, 50),
                'bug_count': np.random.randint(0, 50, 50),
                'commit_count': np.random.randint(10, 500, 50),
                'code_smells': np.random.randint(0, 100, 50),
                'complexity': np.random.randint(1, 50, 50),
                'maintainability_index': np.random.randint(0, 100, 50),
                'test_coverage': np.random.randint(0, 100, 50),
                'loc_added': np.random.randint(0, 1000, 50),
                'loc_deleted': np.random.randint(0, 800, 50),
                'commits_by_author': np.random.randint(1, 200, 50)
            })
            
            # Pass DataFrame directly (not columns list)
            code = self.llm_jury_system.generate_code(formulas, mock_data)
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                f"Code generated ({len(code)} characters)"))
            
            # Step 3: Jury verification
            self.root.after(0, lambda: self.jury_status_var.set("Jury verifying code..."))
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 3: 3 Verifier LLMs checking code correctness..."))
            
            verification = self.llm_jury_system.verify_code_with_jury(code, formulas)
            
            # Show verification results (votes are tuples: (name, verdict_dict))
            approval_rate = verification.get('approval_rate', 0)
            votes_text = "\n".join([
                f"{name}: {verdict.get('verdict', 'UNKNOWN')} (confidence: {verdict.get('confidence', 0):.0%})"
                for name, verdict in verification.get('votes', [])
            ])
            
            if verification.get('approved'):
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"APPROVED by jury ({approval_rate:.0%}):\n{votes_text}"))
                
                # Step 4: Execute code
                self.root.after(0, lambda: self.jury_status_var.set("Executing & self-destructing..."))
                self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                    "Step 4: Executing code temporarily (will auto-delete)..."))
                
                result_df = self.llm_jury_system.execute_temporary_code(code, mock_data)
                
                # Show results
                new_cols = [col for col in result_df.columns if col not in mock_data.columns]
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"SUCCESS! Added {len(new_cols)} new columns:\n" +
                    "\n".join([f"  - {col}" for col in new_cols]) +
                    f"\n\nSample values:\n{result_df[new_cols].head(3).to_string() if new_cols else 'None'}"))
                
                # Save to CORRECT folder: generate_dataset/
                output_dir = Path('generate_dataset')
                output_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f'dynamic_formulas_{timestamp}.csv'
                result_df.to_csv(output_path, index=False)
                
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                    f"  Dataset saved to: {output_path}\n"
                    f"  Rows: {len(result_df)}, Columns: {len(result_df.columns)}\n"
                    f"Estimated cost: ~$0.005"))
                
            else:
                self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                    f"  REJECTED by jury ({approval_rate:.0%}):\n{votes_text}\n\n"
                    f"The generated code did not pass verification. Please try rewording your formula."))
            
            self.root.after(0, lambda: self.jury_status_var.set("Ready | 1 Generator + 3 Verifiers"))
            
            # Clear pending
            self.pending_formula_execution = None
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"Execution error: {e}\n\nDetails:\n{error_detail}"))
            self.root.after(0, lambda: self.jury_status_var.set("Error - check logs"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AGENTIC CHAT SYSTEM (TAB 1 - DATASET GENERATOR ONLY)
    # ═══════════════════════════════════════════════════════════════════════════
    

    def execute_formula_only(self):
        """Execute formula from Formula Tab - COMPLETELY ISOLATED"""
        formula_text = self.formula_text_input.get('1.0', tk.END).strip()
        
        if not formula_text:
            self.log_to_formula("error", "   Please enter a formula")
            return
        
        self.log_to_formula("info", f"Starting formula generation...\n   Input: {formula_text[:150]}...")
        self.formula_status_display.set("Processing...")
        
        # Run in background
        threading.Thread(target=self._execute_formula_background, args=(formula_text,), daemon=True).start()
    
    def _execute_formula_background(self, formula_text: str):
        """Execute formula - ONLY REAL DATA, NO MOCK"""
        try:
            # Get repository path - MUST BE SET
            repo_path = self.repo_var.get() if hasattr(self, 'repo_var') else None
            
            if not repo_path or repo_path == "Not set":
                self.root.after(0, lambda: self.log_to_formula("error", 
                    "   ERROR: No repository set!\n\n"
                    "Please set repository first in Tab 1 (Dataset Generator).\n"
                    "Formula generation requires REAL data from your repository."))
                self.root.after(0, lambda: self.formula_status_display.set("Error - No repository"))
                return
            
            # Try to find existing analysis data
            data = None
            output_dir = Path(repo_path).parent / "output"
            
            if output_dir.exists():
                csv_files = list(output_dir.glob("*.csv"))
                if csv_files:
                    try:
                        # Load most recent CSV
                        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
                        data = pd.read_csv(latest_csv)
                        self.root.after(0, lambda: self.log_to_formula("success", 
                            f"Loaded REAL data: {latest_csv.name}\n   Rows: {len(data)}\n   Columns: {list(data.columns)[:10]}..."))
                    except Exception as e:
                        self.root.after(0, lambda err=str(e): self.log_to_formula("error", 
                            f"   Could not load CSV: {err}"))
            
            # If still no data, show error - NO MOCK DATA
            if data is None or data.empty:
                self.root.after(0, lambda: self.log_to_formula("error", 
                    f"ERROR: No data found in repository!\n\n"
                    f"Searched: {output_dir}\n"
                    f"Please analyze repository first:\n"
                    f"  1. Go to Tab 1 (Dataset Generator)\n"
                    f"  2. Click 'Analyze Repository'\n"
                    f"  3. Wait for CSV to be generated\n"
                    f"  4. Then come back here\n\n"
                    f"NO MOCK DATA IS USED - only real repository data."))
                self.root.after(0, lambda: self.formula_status_display.set("Error - No data"))
                return
            
            # Step 1: Understand
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 1] Understanding request..."))
            understanding = self.llm_jury_system.understand_user_request(formula_text)
            
            if not understanding or not understanding.get('formulas'):
                self.root.after(0, lambda: self.log_to_formula("error", "Failed to understand"))
                self.root.after(0, lambda: self.formula_status_display.set("Error"))
                return
            
            formulas = understanding['formulas']
            self.root.after(0, lambda: self.log_to_formula("success", f"Understood {len(formulas)} formula(s)"))
            
            # Step 2: Generate
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 2] Generating code..."))
            code = self.llm_jury_system.generate_code(formulas, data)
            
            if not code:
                self.root.after(0, lambda: self.log_to_formula("error", "Code generation failed"))
                self.root.after(0, lambda: self.formula_status_display.set("Error"))
                return
            
            self.root.after(0, lambda: self.log_to_formula("success", f"Code generated ({len(code)} chars)"))
            
            # Step 3: Verify
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 3] Jury verification..."))
            verification = self.llm_jury_system.verify_code_with_jury(code, formulas)
            
            for name, verdict in verification.get('votes', []):
                status = "OK" if verdict.get('verdict') == 'APPROVE' else "[ERROR]"
                self.root.after(0, lambda n=name, s=status, v=verdict: 
                               self.log_to_formula("info", f"{s} {n}: {v.get('verdict')}"))
            
            if not verification.get('approved'):
                self.root.after(0, lambda: self.log_to_formula("error", "Jury rejected"))
                self.root.after(0, lambda: self.formula_status_display.set("Rejected"))
                return
            
            # Step 4: Execute
            self.root.after(0, lambda: self.log_to_formula("info", "[STEP 4] Executing..."))
            result_df = self.llm_jury_system.execute_temporary_code(code, data.copy())
            
            new_cols = [col for col in result_df.columns if col not in data.columns]
            
            # Save
            output_dir = Path(__file__).parent.parent / "generate_dataset"
            output_dir.mkdir(exist_ok=True)
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"formula_output_{timestamp}.csv"
            result_df.to_csv(output_path, index=False)
            
            # Show preview (first 10 rows)
            preview_text = f"\nPREVIEW (showing 10/{len(result_df)} rows):\n{result_df[new_cols].head(10).to_string()}"
            
            self.root.after(0, lambda: self.log_to_formula("success", 
                f"SUCCESS!\n   Rows: {len(result_df)}\n   New Columns: {new_cols}\n   File: {output_path.name}{preview_text}"))
            self.root.after(0, lambda: self.formula_status_display.set(f"Success - {len(result_df)} rows, {len(new_cols)} column(s)"))
            self.root.after(0, lambda: self.log_system(f"Formula generated: {output_path.name} ({len(result_df)} rows)"))
            
            # Ask for feedback
            self.root.after(0, lambda path=output_path: self._show_formula_feedback(path, result_df, new_cols))
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.log_to_formula("error", f"Error: {str(e)[:200]}"))
            self.root.after(0, lambda: self.formula_status_display.set("Error"))
            self.root.after(0, lambda: self.log_system(f"Formula error: {str(e)}"))
    
    # ═══════════════════════════════════════════════════════════════════
    # INTEGRATED JURY SYSTEM HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    

