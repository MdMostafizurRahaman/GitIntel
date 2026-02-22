"""OrchestratorMixin — Tab 4 (Orchestrator) multi-agent workflow methods."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os, subprocess

try:
    from multi_agent_orchestrator import MultiAgentOrchestrator, WorkflowStatus
except ImportError:
    MultiAgentOrchestrator = None
    WorkflowStatus = None


class OrchestratorMixin:
    def orch_browse_repo(self):
        """Browse for repository folder in orchestrator tab"""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.orch_repo_var.set(folder)
    
    def orch_clone_repo(self):
        """Clone a Git repository in orchestrator tab"""
        repo_input = self.orch_repo_var.get().strip()
        
        if not repo_input:
            messagebox.showwarning("Clone Repository", 
                "Please enter a GitHub URL or owner/repo")
            return
        
        # Convert owner/repo to full URL
        if '/' in repo_input and not repo_input.startswith(('http://', 'https://', 'git@')):
            repo_input = f"https://github.com/{repo_input}.git"
        
        if not any(x in repo_input.lower() for x in ['github.com', 'gitlab.com', '.git']):
            messagebox.showwarning("Clone Repository",
                "Please enter a valid Git URL")
            return
        
        messagebox.showinfo("Clone Repository", 
            f"Clone functionality would clone:\n{repo_input}\n\nThis feature requires Git CLI installed.")
    
    def orch_load_metrics(self):
        """Load all metrics into listbox"""
        if not hasattr(self, 'catalog') or not self.catalog:
            return
        
        self.orch_metrics_listbox.delete(0, tk.END)
        all_metrics = self.catalog.get_all_metrics()
        
        for metric_name, info in all_metrics.items():
            display = f"{metric_name:30} - {info['description'][:50]}"
            self.orch_metrics_listbox.insert(tk.END, display)
    
    def orch_filter_metrics(self):
        """Filter metrics by category"""
        if not hasattr(self, 'catalog') or not self.catalog:
            return
        
        category = self.orch_category_var.get()
        self.orch_metrics_listbox.delete(0, tk.END)
        
        if category == "All":
            all_metrics = self.catalog.get_all_metrics()
        else:
            all_metrics = self.catalog.get_metrics_by_category(category.lower())
        
        for metric_name, info in all_metrics.items():
            display = f"{metric_name:30} - {info['description'][:50]}"
            self.orch_metrics_listbox.insert(tk.END, display)
    
    def orch_select_all(self):
        """Select all metrics"""
        self.orch_metrics_listbox.select_set(0, tk.END)
    
    def orch_clear_all(self):
        """Clear all selections"""
        self.orch_metrics_listbox.selection_clear(0, tk.END)
    
    def orch_popular_set(self):
        """Select popular metrics set"""
        popular = ['loc', 'cyclomatic_complexity', 'cbo', 'wmc', 'dit', 'churn', 
                   'bug_density', 'maintainability_index', 'test_coverage']
        
        self.orch_metrics_listbox.selection_clear(0, tk.END)
        
        for i in range(self.orch_metrics_listbox.size()):
            item_text = self.orch_metrics_listbox.get(i)
            for metric in popular:
                if item_text.startswith(metric):
                    self.orch_metrics_listbox.selection_set(i)
                    break
    
    def orch_start_workflow(self):
        """Start multi-agent workflow"""
        if not hasattr(self, 'orch_running'):
            self.orch_running = False
        
        if self.orch_running:
            messagebox.showwarning("Already Running", "Workflow is already in progress")
            return
        
        # Get configuration
        repo_path = self.orch_repo_var.get().strip()
        if not repo_path:
            messagebox.showwarning("Missing Repository", "Please select a repository")
            return
        
        user_request = self.orch_request_text.get('1.0', tk.END).strip()
        if not user_request or "Example:" in user_request:
            messagebox.showwarning("Missing Request", "Please describe what you want to generate")
            return
        
        # Get selected metrics
        selections = self.orch_metrics_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Metrics", "Please select at least one metric")
            return
        
        selected_metrics = []
        for i in selections:
            item_text = self.orch_metrics_listbox.get(i)
            metric_name = item_text.split()[0]  # First word is metric name
            selected_metrics.append(metric_name)
        
        # Clear logs
        if hasattr(self, 'orch_log'):
            self.orch_log.configure(state=tk.NORMAL)
            self.orch_log.delete('1.0', tk.END)
            self.orch_log.configure(state=tk.DISABLED)
        
        # Update status
        self.orch_running = True
        if hasattr(self, 'orch_status_var'):
            self.orch_status_var.set("Multi-Agent Workflow...")
        
        self.orch_log_message("="*70, 'info')
        self.orch_log_message("MULTI-AGENT WORKFLOW STARTING", 'success')
        self.orch_log_message("="*70, 'info')
        self.orch_log_message(f"Repository: {repo_path}", 'info')
        self.orch_log_message(f"User Request: {user_request[:100]}...", 'info')
        self.orch_log_message(f"Selected Metrics: {len(selected_metrics)}", 'info')
        self.orch_log_message("="*70, 'info')
        
        # Run in background thread
        thread = threading.Thread(
            target=self._orch_run_workflow_thread,
            args=(user_request, repo_path, selected_metrics),
            daemon=True
        )
        thread.start()
    
    def _orch_run_workflow_thread(self, user_request: str, repo_path: str, selected_metrics: list):
        """Run orchestrator workflow in background"""
        try:
            def progress_callback(msg: str):
                tag = 'info'
                if '[AGENT 1]' in msg:
                    tag = 'agent1'
                elif '[AGENT 2]' in msg:
                    tag = 'agent2'
                elif '[AGENTS 3-5]' in msg or '[TESTING]' in msg:
                    tag = 'agent3'
                elif '[SUCCESS]' in msg or 'SUCCESS' in msg or 'PASSED' in msg:
                    tag = 'success'
                elif '[ERROR]' in msg or 'ERROR' in msg or 'FAILED' in msg:
                    tag = 'error'
                elif '[WARNING]' in msg or 'WARNING' in msg:
                    tag = 'warning'
                
                self.root.after(0, lambda m=msg, t=tag: self.orch_log_message(m, t))
            
            self.root.after(0, lambda: self.orch_log_message("\nInitializing orchestrator...", 'info'))
            
            orchestrator = MultiAgentOrchestrator(
                progress_callback=progress_callback
            )
            
            result = orchestrator.run_full_workflow(
                user_request=user_request,
                repo_path=repo_path,
                selected_predefined_metrics=selected_metrics
            )
            
            self.root.after(0, lambda r=result: self._orch_handle_result(r))
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            self.root.after(0, lambda em=error_msg: self.orch_log_message(em, 'error'))
            if hasattr(self, 'orch_status_var'):
                self.root.after(0, lambda: self.orch_status_var.set(" Workflow Failed"))
            self.orch_running = False
    
    def _orch_handle_result(self, result):
        """Handle workflow result"""
        self.orch_running = False
        self.orch_result = result

        status = result.status
        
        self.orch_log_message("", 'info')
        self.orch_log_message("="*70, 'info')
        
        if status == WorkflowStatus.SUCCESS:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set(f" Dataset Generated ({result.iterations} iterations)")
            if hasattr(self, 'orch_progress_var'):
                self.orch_progress_var.set(f"Cycle: {result.iterations}/5 | Completed in {result.execution_time:.2f}s")
            
            self.orch_log_message("WORKFLOW COMPLETED SUCCESSFULLY", 'success')
            self.orch_log_message(f"Iterations: {result.iterations}", 'success')
            self.orch_log_message(f"Execution Time: {result.execution_time:.2f}s", 'success')
            
            if result.dataset is not None:
                self.orch_log_message(f"Dataset Shape: {result.dataset.shape}", 'success')
                self.orch_log_message(f"Output: {result.metadata.get('dataset_file', 'N/A')}", 'success')
                
                if hasattr(self, 'orch_results_text'):
                    self.orch_results_text.delete('1.0', tk.END)
                    self.orch_results_text.insert('1.0', result.dataset.to_string())
        
        elif status == WorkflowStatus.NEEDS_HUMAN_INTERVENTION:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set("  HUMAN INTERVENTION REQUIRED")
            if hasattr(self, 'orch_progress_var'):
                self.orch_progress_var.set(f"Cycle: {result.iterations}/5 | Max cycles exceeded")
            
            self.orch_log_message("HUMAN INTERVENTION REQUIRED", 'warning')
            self.orch_log_message(f"Error: {result.error_message}", 'warning')
            self.orch_log_message(f"Attempted {result.iterations} iterations", 'warning')
        
        else:
            if hasattr(self, 'orch_status_var'):
                self.orch_status_var.set(" WORKFLOW FAILED")
            self.orch_log_message("WORKFLOW FAILED", 'error')
            self.orch_log_message(f"Error: {result.error_message}", 'error')
        
        self.orch_log_message("="*70, 'info')
    
    def orch_pause(self):
        """Pause workflow"""
        if not self.orch_running:
            messagebox.showinfo("Not Running", "No workflow is currently running")
            return
        
        messagebox.showinfo("Pause", "Pause functionality will be implemented")
    
    def orch_reset(self):
        """Reset orchestrator state"""
        if self.orch_running:
            confirm = messagebox.askyesno("Confirm Reset", 
                                          "Workflow is running. Stop and reset?")
            if not confirm:
                return
        
        self.orch_running = False
        if hasattr(self, 'orch_log'):
            self.orch_log.configure(state=tk.NORMAL)
            self.orch_log.delete('1.0', tk.END)
            self.orch_log.configure(state=tk.DISABLED)
        
        if hasattr(self, 'orch_results_text'):
            self.orch_results_text.delete('1.0', tk.END)
        
        if hasattr(self, 'orch_status_var'):
            self.orch_status_var.set("⏸ Ready - Configure and start workflow")
        
        self.orch_log_message("Orchestrator reset. Ready for new workflow!", 'success')
    
    def orch_save_dataset(self):
        """Save generated dataset"""
        if not hasattr(self, 'orch_result') or not self.orch_result or not self.orch_result.dataset:
            messagebox.showwarning("No Dataset", "No dataset available to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Dataset",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.orch_result.dataset.to_json(file_path, orient='records', indent=2)
                else:
                    self.orch_result.dataset.to_csv(file_path, index=False)
                
                messagebox.showinfo("Success", f"Dataset saved to:\n{file_path}")
                self.orch_log_message(f"Dataset saved: {file_path}", 'success')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save dataset:\n{str(e)}")
    
    def orch_view_dataset(self):
        """View full dataset in new window"""
        if not hasattr(self, 'orch_result') or not self.orch_result or not self.orch_result.dataset:
            messagebox.showwarning("No Dataset", "No dataset available to view")
            return
        
        view_window = tk.Toplevel(self.root)
        view_window.title("Dataset Viewer")
        view_window.geometry("1000x600")
        
        frame = ttk.Frame(view_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.NONE, font=('Consolas', 9))
        text.pack(fill=tk.BOTH, expand=True)
        
        text.insert('1.0', self.orch_result.dataset.to_string())
        text.configure(state=tk.DISABLED)
    
    def orch_open_folder(self):
        """Open output folder"""
        if not self.orch_result or not self.orch_result.metadata.get('output_dir'):
            messagebox.showwarning("No Output", "No output directory available")
            return
        
        output_dir = self.orch_result.metadata['output_dir']
        
        if os.path.exists(output_dir):
            subprocess.Popen(['explorer', output_dir])
        else:
            messagebox.showwarning("Not Found", f"Directory not found:\n{output_dir}")


