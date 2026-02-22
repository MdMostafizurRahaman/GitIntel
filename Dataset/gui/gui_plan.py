"""PlanMixin — plan creation, approval flow, and task execution."""
import tkinter as tk
from tkinter import ttk
import threading
import traceback
try:
    from .gui_types import MessageType, Task, TaskStatus, TaskManager
except ImportError:
    from gui_types import MessageType, Task, TaskStatus, TaskManager


class PlanMixin:
    def _approve_plan(self):
        """Approve the plan and generate preview"""
        self.add_agent_message(MessageType.SUCCESS, "Plan approved. Generating preview...")
        thread = threading.Thread(target=self._generate_preview_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_preview_thread(self):
        """Generate preview in background"""
        try:
            result = self.enhanced_system.generate_preview()
            self._display_enhanced_messages()
            
            # Show preview in GUI (handled by _enhanced_conversation_thread logic)
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Preview generation failed: {str(e)}"))
    
    def _reject_plan(self):
        """Reject the plan"""
        self.add_agent_message(MessageType.ERROR, "  Plan rejected. Describe what you need differently.")
    
    def _modify_plan(self):
        """Modify the plan"""
        self.add_agent_message(MessageType.QUESTION, 
            "What would you like to change? Describe the modifications:")
        self._setup_enhanced_input_handler("Modifications")
    
    def _confirm_generation(self):
        """Confirm final dataset generation"""
        self.add_agent_message(MessageType.SUCCESS, "Confirmed. Generating full dataset...")
        thread = threading.Thread(target=self._generate_full_dataset_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_full_dataset_thread(self):
        """Generate full dataset in background"""
        try:
            result = self.enhanced_system.generate_full_dataset()
            self._display_enhanced_messages()
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR, 
                f"Generation failed: {str(e)}"))
    
    def _cancel_generation(self):
        """Cancel dataset generation"""
        self.add_agent_message(MessageType.ERROR, "  Generation cancelled.")
    
    def _generate_tasks_from_config(self):
        """Generate task plan from stored dataset config"""
        if not hasattr(self, 'dataset_config') or not self.dataset_config:
            self.add_agent_message(MessageType.ERROR, "  No configuration available")
            return
        
        config = self.dataset_config
        
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        self.add_agent_message(MessageType.SYSTEM, " Creating task plan...")
        
        # Task 1: Verify repository
        if self.repo_path:
            self.task_manager.add_task(
                "Verify Repository",
                f"Check repository: {self.repo_path}",
                action=self.task_verify_repo,
                requires_approval=False
            )
        
        # Task 2: Extract/Calculate metrics
        metrics_str = ', '.join(config.get('metrics', [])) if config.get('metrics') else 'custom formula'
        self.task_manager.add_task(
            "Extract Metrics",
            f"Calculate metrics: {metrics_str}",
            action=lambda: self.task_extract_custom_formula(config),
            requires_approval=False
        )
        
        # Task 3: Apply formula if present
        if config.get('custom'):
            self.task_manager.add_task(
                "Apply Custom Formula",
                f"Calculate: {config.get('custom')}",
                action=lambda: self.task_apply_formula(config),
                requires_approval=False
            )
        
        # Task 4: Generate output
        self.task_manager.add_task(
            "Generate Dataset",
            "Create output file",
            action=lambda: self.task_generate_output(config),
            requires_approval=False
        )
        
        # Show summary
        summary = f"""**Task Plan Created ({len(self.task_manager.tasks)} tasks)**

Ready to execute. Click **▶ Start Execution** to begin."""
        
        self.add_agent_message(MessageType.SUCCESS, summary)
        
        # Enable start button
        self.start_btn.config(state=tk.NORMAL)
    
    def _create_default_task_plan(self):
        """Create a default task plan when no specific config is available"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        # Use last_user_request to create a config
        if hasattr(self, 'last_user_request') and self.last_user_request:
            # Create a basic config from the request
            self.dataset_config = {
                'metrics': [],
                'format': 'csv',
                'custom': self.last_user_request
            }
            self._generate_tasks_from_config()
        else:
            self.add_agent_message(MessageType.ERROR, 
                "Unable to create task plan. Please describe what dataset you need.")
    
    def _setup_approval_buttons(self, on_approve, on_reject, on_modify=None):
        """Setup approval buttons in agent panel"""
        # Create button frame
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Approve", command=on_approve,
                   style='Approve.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="  Reject", command=on_reject,
                   style='Reject.TButton').pack(side=tk.LEFT, padx=5)
        
        if on_modify:
            ttk.Button(btn_frame, text="Modify", command=on_modify).pack(side=tk.LEFT, padx=5)
    
    def _setup_final_approval_buttons(self, on_confirm, on_cancel):
        """Setup final approval buttons"""
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Confirm & Generate", command=on_confirm,
                   style='Approve.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel,
                   style='Reject.TButton').pack(side=tk.LEFT, padx=5)
    

    def _create_plan_from_input(self, user_input: str):
        """Parse user input and create a task plan"""
        user_lower = user_input.lower()
        
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        # Analyze what user wants
        detected = {
            'benchmark': None,
            'metrics': [],
            'format': 'csv',
            'language': None
        }
        
        # Detect benchmark dataset
        for benchmark in self.BENCHMARK_DATASETS.keys():
            if benchmark.lower() in user_lower:
                detected['benchmark'] = benchmark
                break
                
        # Detect metrics categories
        metric_keywords = {
            'complexity': ['cyclomatic', 'cognitive', 'nesting'],
            'ck': ['wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom'],
            'size': ['loc', 'lines', 'sloc'],
            'quality': ['maintainability', 'comment'],
            'coupling': ['coupling', 'afferent', 'efferent'],
            'defect': ['bug', 'defect', 'vulnerability']
        }
        
        for category, keywords in metric_keywords.items():
            for kw in keywords:
                if kw in user_lower:
                    detected['metrics'].append(category)
                    break
                    
        # Detect language
        languages = ['java', 'python', 'javascript', 'typescript', 'go', 'ruby', 'c++', 'c#']
        for lang in languages:
            if lang in user_lower:
                detected['language'] = lang
                break
                
        # Detect output format
        for fmt in ['csv', 'json', 'jsonl', 'excel', 'parquet']:
            if fmt in user_lower:
                detected['format'] = fmt
                break
        
        # Create task plan based on detection
        self.add_agent_message(MessageType.SYSTEM, 
            f"I understand you want to create a dataset. Here's my plan:")
        
        # Task 1: Verify repository
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=True
        )
        
        # Task 2: Analyze repository structure
        self.task_manager.add_task(
            "Analyze Repository",
            "Scan the repository to understand its structure",
            action=self.task_analyze_repo,
            requires_approval=True
        )
        
        # Task 3 depends on what was detected
        if detected['benchmark']:
            self.task_manager.add_task(
                f"Setup {detected['benchmark']} Format",
                f"Configure dataset in {detected['benchmark']} format",
                action=lambda: self.task_setup_benchmark(detected['benchmark']),
                requires_approval=True
            )
            
            self.task_manager.add_task(
                "Find Bug-Fixing Commits",
                "Identify commits that fix bugs in the repository",
                action=self.task_find_bugs,
                requires_approval=True
            )
        else:
            # Custom metrics selection
            if detected['metrics']:
                metrics_str = ', '.join(detected['metrics'])
                self.task_manager.add_task(
                    "Select Metrics",
                    f"Configure metrics: {metrics_str}",
                    action=lambda: self.task_select_metrics(detected['metrics']),
                    requires_approval=True
                )
            else:
                self.task_manager.add_task(
                    "Select Metrics",
                    "Choose metrics for the dataset (none detected, will use defaults)",
                    action=lambda: self.task_select_metrics(['size', 'complexity']),
                    requires_approval=True
                )
        
        # Task: Extract data
        self.task_manager.add_task(
            "Extract Data",
            f"Process files and extract {detected['format']} data",
            action=lambda: self.task_extract_data(detected),
            requires_approval=True
        )
        
        # Task: Generate output
        self.task_manager.add_task(
            "Generate Dataset",
            f"Create output file in {detected['format'].upper()} format",
            action=lambda: self.task_generate_output(detected),
            requires_approval=True
        )
        
        # Task: Validate
        self.task_manager.add_task(
            "Validate Dataset",
            "Check the generated dataset for completeness",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary
        summary = f"""
**Plan Created with {len(self.task_manager.tasks)} tasks:**

"""
        for task in self.task_manager.tasks:
            summary += f"  {task.id}. {task.title}\n"
            
        summary += f"""
**Detected Configuration:**
- Dataset Type: {detected['benchmark'] or 'Custom'}
- Metrics: {', '.join(detected['metrics']) if detected['metrics'] else 'Default (size, complexity)'}
- Language Filter: {detected['language'] or 'All'}
- Output Format: {detected['format'].upper()}

Click **▶ Start Execution** to begin. I'll ask for your approval at each step.
"""
        
        self.add_agent_message(MessageType.INFO, summary)
        
        # Enable start button
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        
        # Store config
        self.dataset_config = detected
        
    # ═══════════════════════════════════════════════════════════════════════════
    # TASK EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════
    

    def start_execution(self):
        """Start executing the task plan"""
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.task_manager.is_running = True
        
        self.add_agent_message(MessageType.SYSTEM, "Starting execution...")
        
        threading.Thread(target=self._execute_tasks, daemon=True).start()
        
    def _execute_tasks(self):
        """Execute tasks one by one in SEPARATE THREAD to prevent GUI freeze"""
        def run_tasks_in_thread():
            for task in self.task_manager.tasks:
                if not self.task_manager.is_running:
                    break
                        
                # Execute task directly
                self.task_manager.set_task_status(task.id, TaskStatus.IN_PROGRESS)
                self.root.after(0, lambda t=task: self.add_agent_message(MessageType.ACTION, f"  Executing: {t.title}..."))
                
                try:
                    if task.action:
                        result = task.action()
                        self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                           result=str(result) if result else "Done")
                        self.root.after(0, lambda t=task: self.add_agent_message(MessageType.SUCCESS, 
                            f"Completed: {t.title}"))
                    else:
                        self.task_manager.set_task_status(task.id, TaskStatus.COMPLETED,
                                                           result="No action required")
                except Exception as e:
                    self.task_manager.set_task_status(task.id, TaskStatus.FAILED,
                                                       error=str(e))
                    self.root.after(0, lambda t=task, err=str(e): self.add_agent_message(MessageType.ERROR, 
                        f"Failed: {t.title}\nError: {err}"))
                        
            # Execution complete
            self.root.after(0, self._execution_complete)
        
        # Run in separate thread to prevent GUI freeze
        thread = threading.Thread(target=run_tasks_in_thread, daemon=True)
        thread.start()
        
    def _execution_complete(self):
        """Called when execution is complete"""
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.task_manager.is_running = False
        self.set_approval_visible(False)
        
        # Count results
        completed = sum(1 for t in self.task_manager.tasks 
                       if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.task_manager.tasks 
                    if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in self.task_manager.tasks 
                     if t.status == TaskStatus.SKIPPED)
        
        success_msg = "Dataset generated successfully!" if failed == 0 else "Some tasks failed. Please review."
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Execution Complete!\n\n"
            f"Completed: {completed}\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}\n\n"
            f"{success_msg}\n\n"
            f"**Next Steps:**\n"
            f"• Check the output in 'generated_datasets' folder\n"
            f"• Describe what you need to create a new dataset\n"
            f"• Or click **Clear Plan** to start fresh"
        )
        
        # Keep start button enabled but don't auto-start
        self.execution_complete = True
        
    def pause_execution(self):
        """Pause the execution"""
        self.task_manager.is_running = False
        self.pause_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.add_agent_message(MessageType.INFO, "Execution paused. Click Start to resume.")
        
    def clear_plan(self):
        """Clear the task plan"""
        self.task_manager.clear_tasks()
        self.progress_var.set(0)
        self.execution_complete = False
        self.add_agent_message(MessageType.INFO, "Plan cleared. Describe what you need to create a new plan.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # APPROVAL SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def approve_action(self):
        """Approve the current action"""
        self.set_approval_visible(False)
        self.task_manager.approve_current()
        self.add_agent_message(MessageType.SUCCESS, "Action approved!")
        
    def reject_action(self):
        """Reject the current action"""
        self.set_approval_visible(False)
        self.task_manager.reject_current()
        self.add_agent_message(MessageType.ERROR, "Action rejected.")
        
    def skip_action(self):
        """Skip the current action"""
        self.set_approval_visible(False)
        self.task_manager.skip_current()
        self.add_agent_message(MessageType.INFO, "Action skipped.")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # FEEDBACK SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def send_feedback(self):
        """
        Send user feedback - handles approval/rejection/modification
        """
        feedback = self.feedback_var.get().strip()
        if not feedback:
            return
            
        self.feedback_var.set("")
        
        # Show user message
        self.add_agent_message(MessageType.USER, f"{feedback}")
        
        # Add to conversation
        self.conversation_history.append({"role": "user", "content": feedback})
        
        feedback_lower = feedback.lower()

        # ── Highest priority: active jury clarification from main chat ───────
        if self._chat_jury_in_session and self.integrated_jury:
            self._chat_jury_in_session = False
            self.add_agent_message(MessageType.THINKING, "Processing your clarification…")
            threading.Thread(
                target=self._jury_chat_clarification_thread,
                args=(feedback,),
                daemon=True,
            ).start()
            return
        
        # Check if waiting for analysis confirmation (after metrics are shown)
        if hasattr(self, 'awaiting_analysis_confirmation') and self.awaiting_analysis_confirmation:
            self.awaiting_analysis_confirmation = False
            # Continue enhanced conversation with user feedback
            threading.Thread(target=self._enhanced_continue_conversation_thread, 
                           args=(feedback,), daemon=True).start()
            return
        
        # Check if waiting for extraction approval
        if hasattr(self, 'awaiting_extraction_approval') and self.awaiting_extraction_approval:
            if any(word in feedback_lower for word in ['extract', 'yes', 'ok', 'approve', 'proceed']):
                self.awaiting_extraction_approval = False
                self.add_agent_message(MessageType.SUCCESS, "Starting extraction with Jury Process...")
                
                # Start jury process for formula extraction
                threading.Thread(target=self._process_formula_extraction, daemon=True).start()
                return
            else:
                self.awaiting_extraction_approval = False
                self.add_agent_message(MessageType.INFO,
                    "Please describe an alternative approach or start a new query.")
                self.current_plan = None
                return
        
        # Check if user is approving
        if any(word in feedback_lower for word in ['yes', 'ok', 'approve', 'confirm', 'proceed', 'correct']):
            if self.current_plan:
                self.add_agent_message(MessageType.SUCCESS, "Approved! Generating dataset...")
                threading.Thread(target=self._execute_approved_plan, daemon=True).start()
            else:
                self.add_agent_message(MessageType.ERROR, 
                    "  No plan to approve. Please describe what dataset you need first.")
        
        # Check if user is rejecting/modifying
        elif any(word in feedback_lower for word in ['no', 'wrong', 'change', 'modify', 'different']):
            self.add_agent_message(MessageType.INFO, 
                "Please describe what you'd like to change, or start over with a new request.")
            self.current_plan = None
        
        # Help request
        elif any(word in feedback_lower for word in ['help', 'how', 'what can']):
            self.add_agent_message(MessageType.INFO,
                "**Here's what you can do:**\n\n"
                "**1. Describe your dataset:**\n"
                "   • 'Create a complexity dataset'\n"
                "   • 'I need CK metrics for Java files'\n"
                "   • 'Defects4J format with my data'\n\n"
                "**2. Custom metrics:**\n"
                "   • 'Calculate bug density per 1000 LOC'\n"
                "   • 'Create a metric for code smells'\n"
                "   → I'll use LLM Jury to validate!\n\n"
                "**3. Approve/Reject:**\n"
                "   • Type 'yes' to proceed\n"
                "   • Type 'no' to cancel\n\n"
                "**4. Quick options:**\n"
                "   • Select benchmarks above\n"
                "   • Choose metrics (65+ available)\n"
                "   • Click 'Generate Dataset'")
        
        # Treat as new query
        else:
            self.current_query = feedback
            # Route ALL new queries through enhanced_system (Bedrock) if available
            if self.enhanced_system and self.repo_path:
                threading.Thread(target=self._process_with_enhanced_system,
                               args=(feedback,), daemon=True).start()
            elif self.enhanced_system and not self.repo_path:
                self.add_agent_message(MessageType.QUESTION,
                    "  Please set a repository first (paste GitHub URL or folder path above), then ask again.")
            else:
                threading.Thread(target=self._intelligent_chat_processor, 
                               args=(feedback,), daemon=True).start()
    
    def _process_feedback(self, feedback: str):
        """Legacy feedback processor - redirects to send_feedback logic"""
        # This is now handled in send_feedback() above
        pass
    
    def _execute_approved_plan(self):
        """
        Execute the approved plan:
        1. Extract real data from repository
        2. Calculate known metrics
        3. Apply custom metrics (jury-approved)
        4. Generate output file
        5. Create visualizations
        6. Show results
        """
        if not self.current_plan:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                "No plan to execute"))
            return
        
        plan = self.current_plan
        
        try:
            # Clear old tasks
            self.root.after(0, self.task_manager.clear_tasks)
            
            # Step 1: Verify repository
            self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                "Step 1/5: Verifying repository..."))
            
            task1 = self.task_manager.add_task(
                "Verify Repository",
                f"Check {self.repo_path}",
                action=self.task_verify_repo,
                requires_approval=False
            )

            # ── ROUTE: benchmark intent vs custom-metric intent ──────────────
            intent = plan.get('intent', 'custom_metrics')
            benchmark_name = plan.get('benchmark')

            if intent == 'benchmark' and benchmark_name:
                # Route directly to the proper benchmark generator
                # (e.g. ManySStuBs4J → git commit traversal, NOT file-level MetricsHelper)
                self.root.after(0, lambda b=benchmark_name: self.add_agent_message(
                    MessageType.ACTION,
                    f"Step 2/3: Generating {b} dataset using dedicated generator..."))

                self.task_manager.add_task(
                    f"Generate {benchmark_name} Dataset",
                    f"Run {benchmark_name} generator (real git commit / code analysis)",
                    action=lambda b=benchmark_name: self.task_setup_benchmark(b),
                    requires_approval=False
                )

                self.task_manager.add_task(
                    "Validate Output",
                    "Check generated files",
                    action=self.task_validate,
                    requires_approval=False
                )

            else:
                # Custom metrics / formula intent → generic file-level extraction
                self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                    "Step 2/5: Extracting real data from repository..."))

                known_metrics = plan.get('known_metrics', [])
                validated_custom = plan.get('validated_custom_metrics', [])

                # Get file limit from GUI (user control!)
                file_limit = self.file_limit_var.get().strip()

                # Warn user if no limit or very high limit
                if not file_limit or file_limit.lower() == "all":
                    self.root.after(0, lambda: self.add_agent_message(MessageType.QUESTION,
                        f"**WARNING**: No file limit set!\n\n"
                        f"This will process ALL files in the repository which may take a very long time.\n\n"
                        f"**Recommended**: Set a file limit (e.g., 100) in the File Limit field above.\n\n"
                        f"Current setting: '{file_limit}' - Are you sure you want to continue?"))
                    return

                self.task_manager.add_task(
                    "Extract Metrics",
                    f"Calculate {len(known_metrics)} known + {len(validated_custom)} custom metrics from {file_limit} files",
                    action=lambda: self._extract_real_data(known_metrics, validated_custom, file_limit),
                    requires_approval=False
                )

                self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                    "Step 3/5: Generating dataset file..."))

                output_config = {
                    'format': 'csv',
                    'benchmark': benchmark_name,
                    'selected_metrics': known_metrics,
                    'custom_metrics': validated_custom,
                    'file_limit': self.file_limit_var.get() if hasattr(self, 'file_limit_var') else 'All'
                }

                self.task_manager.add_task(
                    "Generate Dataset",
                    "Create output CSV/JSON",
                    action=lambda: self.task_generate_output(output_config),
                    requires_approval=False
                )

                self.root.after(0, lambda: self.add_agent_message(MessageType.ACTION,
                    "Step 4/5: Creating visualizations..."))

                self.task_manager.add_task(
                    "Create Visualizations",
                    "Generate charts and graphs",
                    action=lambda: self._create_visualizations(output_config),
                    requires_approval=False
                )

                self.task_manager.add_task(
                    "Validate Output",
                    "Check generated files",
                    action=self.task_validate,
                    requires_approval=False
                )
            
            # Start execution
            self.root.after(0, lambda: self.add_agent_message(MessageType.SYSTEM,
                f"Plan created with {len(self.task_manager.tasks)} tasks. Executing..."))
            
            self.root.after(100, self.start_execution)
            
        except Exception as e:
            error_detail = traceback.format_exc()
            self.root.after(0, lambda e=str(e): self.add_agent_message(
                MessageType.ERROR, f"Execution failed: {e}"))
            print(f"Execution error: {error_detail}")
    

