"""DatasetMixin — dataset generation, selection dialogs, catalog planning."""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import traceback
import os, sys, json
import subprocess
import pandas as pd
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Optional
try:
    from .gui_types import MessageType
except ImportError:
    from gui_types import MessageType

try:
    from dataset_helpers import safe_print
except ImportError:
    def safe_print(*args, **kwargs):
        print(*args, **kwargs)

try:
    from dataset_generators import MetricsHelper
    METRICS_HELPER_AVAILABLE = True
except Exception:
    MetricsHelper = None
    METRICS_HELPER_AVAILABLE = False

try:
    from dataset_generator import ProfessionalDatasetGenerator
except ImportError:
    ProfessionalDatasetGenerator = None


class DatasetMixin:
    def generate_from_selection(self):
        """Generate dataset from checkbox/metrics selection"""
        benchmarks = self.get_selected_benchmarks()
        metrics = self.selected_metrics
        combine = self.combine_var.get()

        # Read commit/file limit from sidebar
        raw = self.file_limit_var.get().strip().lower()
        try:
            commit_limit = None if raw in ('all', '', '0') else int(raw)
        except ValueError:
            commit_limit = 500

        if not benchmarks and not metrics:
            messagebox.showwarning("Selection Required",
                "Please select a benchmark OR some metrics, or use Chat to describe what you need.")
            return

        if not self.repo_path:
            messagebox.showwarning("Repository Required", "Please set a repository first.")
            return

        # Show what we're generating
        desc = []
        if benchmarks:
            desc.append(f"Benchmarks: {', '.join(benchmarks)}")
        if metrics:
            desc.append(f"Metrics: {len(metrics)} selected")
        if combine:
            desc.append("(Combined)")

        self.add_agent_message(MessageType.USER, f"Generate dataset: {', '.join(desc)}")
        self.add_agent_message(MessageType.THINKING, "Creating generation plan...")

        # Start generation based on selection
        if benchmarks and not metrics:
            for bname in benchmarks:
                threading.Thread(target=self._generate_benchmark_dataset,
                                 args=(bname, commit_limit), daemon=True).start()
        elif metrics and not benchmarks:
            threading.Thread(target=self._generate_metrics_dataset,
                             args=(metrics,), daemon=True).start()
        else:
            for bname in benchmarks:
                threading.Thread(target=self._generate_benchmark_dataset,
                                 args=(bname, commit_limit), daemon=True).start()
            threading.Thread(target=self._generate_metrics_dataset,
                             args=(metrics,), daemon=True).start()
    
    def clear_selection(self):
        """Clear all selections"""
        self.benchmark_var.set("None")
        self.selected_metrics = []
        self.selected_metrics_count.set("0/65 selected")
        self.combine_var.set(False)
        self.add_agent_message(MessageType.INFO, "Selection cleared")
    
    def _generate_benchmark_dataset(self, benchmark: str, commit_limit: int = None):
        """Generate pure benchmark dataset"""
        try:
            from dataset_generator import ProfessionalDatasetGenerator
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            self.add_agent_message(MessageType.ACTION, f"Generating {benchmark}...")

            generator = ProfessionalDatasetGenerator(
                workspace_path=str(self.repo_path),
                commit_limit=commit_limit,
                timestamp=timestamp
            )
            
            method_map = {
                "Defects4J": generator.generate_defects4j_dataset,
                "Bugs.jar": generator.generate_bugs_jar_dataset,
                "PROMISE": generator.generate_promise_dataset,
                "CodeXGLUE": generator.generate_codexglue_dataset,
                "CodeSearchNet": generator.generate_codesearchnet_dataset,
                "ManySStuBs4J": generator.generate_manystubs4j_dataset,
                "Sourcerer": generator.generate_sourcerer_dataset
            }
            
            if benchmark in method_map:
                result = method_map[benchmark]()

                # Create individual folder link for benchmark dataset
                output_msg = f"{benchmark} dataset generated successfully!"
                if isinstance(result, dict) and 'output_dir' in result:
                    output_folder = result.get('output_dir', '')
                    self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                        output_msg,
                        actions=[{
                            'label': 'Open Dataset Folder',
                            'callback': lambda p=output_folder: os.startfile(p) if sys.platform == 'win32' else subprocess.Popen(['xdg-open', p])
                        }]
                    ))
                else:
                    self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, output_msg))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))
    
    def _generate_metrics_dataset(self, metrics: List[str]):
        """Generate metrics dataset directly"""
        try:
            self.add_agent_message(MessageType.ACTION, f"Generating dataset with {len(metrics)} metrics...")

            # Ensure metrics_helper is initialized
            if not self.metrics_helper and METRICS_HELPER_AVAILABLE:
                try:
                    self.metrics_helper = MetricsHelper(str(self.repo_path))
                    self.add_agent_message(MessageType.INFO, "MetricsHelper initialized")
                except Exception as e:
                    self.add_agent_message(MessageType.ERROR, f"Failed to initialize MetricsHelper: {e}")
                    return

            if not self.metrics_helper:
                self.add_agent_message(MessageType.ERROR, "MetricsHelper not available")
                return

            threading.Thread(
                target=self._generate_metrics_dataset_direct,
                args=(metrics,),
                daemon=True
            ).start()

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))

    def open_generated_dataset(self, filepath: Optional[str] = None):
        """Open generated dataset in default application or display in new window"""
        try:
            if filepath is None:
                # Try to find the most recent dataset
                generated_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "generated_datasets"
                if not generated_dir.exists():
                    self.add_agent_message(MessageType.ERROR, "No generated datasets found")
                    return
                
                csv_files = sorted(generated_dir.glob("*.csv"), key=os.path.getmtime, reverse=True)
                if not csv_files:
                    self.add_agent_message(MessageType.ERROR, "No CSV files found in generated_datasets")
                    return
                
                filepath = str(csv_files[0])
            
            # Try to open with default application
            import subprocess
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', filepath])
            else:
                subprocess.Popen(['xdg-open', filepath])
            
            self.add_agent_message(MessageType.INFO, f"Opened: {os.path.basename(filepath)}")
        except Exception as e:
            self.add_agent_message(MessageType.ERROR, f"Could not open file: {str(e)[:100]}")
    
    def view_agent_session_logs(self):
        """Display list of recent agent session logs"""
        try:
            session_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "agent_sessions"
            if not session_dir.exists():
                self.add_agent_message(MessageType.ERROR, "No agent session logs found")
                return
            
            session_files = sorted(session_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
            
            if not session_files:
                self.add_agent_message(MessageType.INFO, "No session logs available")
                return
            
            self.add_agent_message(MessageType.SUCCESS, f"Found {len(session_files)} agent sessions:")
            for session_file in session_files[:10]:  # Show last 10
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                    session_info = f"  • {data.get('session_id', 'unknown')} - {data.get('agent_system', 'unknown')} "
                    session_info += f"({data.get('metrics_count', 0)} metrics, "
                    session_info += f"{data.get('rows', 0)} rows)"
                    self.add_agent_message(MessageType.INFO, session_info)
                except:
                    pass
        except Exception as e:
            self.add_agent_message(MessageType.ERROR, f"Error reading sessions: {str(e)[:100]}")
    
    def _generate_combined_dataset(self, benchmark: str, metrics: List[str]):
        """Generate combined benchmark + custom metrics"""
        try:
            self.add_agent_message(MessageType.ACTION, 
                f"Generating combined: {benchmark} + {len(metrics)} custom metrics...")
            
            # First generate benchmark
            self._generate_benchmark_dataset(benchmark)
            
            # Then add custom metrics
            # TODO: Merge benchmark output with custom metrics
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"  Combined dataset ready: {benchmark} base + {len(metrics)} extra metrics"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.add_agent_message(MessageType.ERROR, f"Error: {msg}"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DYNAMIC FORMULA GENERATOR (Multi-LLM Jury System)
    # ═══════════════════════════════════════════════════════════════════════════
    

    def show_benchmark_options(self):
        """Show benchmark dataset options with selection"""
        # Create benchmark window
        benchmark_window = tk.Toplevel(self.root)
        benchmark_window.title("  Benchmark Datasets")
        benchmark_window.geometry("700x700")
        benchmark_window.grab_set()
        
        # Header
        header = ttk.Label(benchmark_window, text="Select Benchmark Datasets",
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(benchmark_window, text="  Available Benchmarks", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollable content
        canvas = tk.Canvas(info_frame)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store benchmark variables
        benchmark_vars = {}
        
        # Add benchmarks with checkboxes
        for benchmark_name, benchmark_info in self.BENCHMARK_DATASETS.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=8)
            
            # Checkbox
            var = tk.BooleanVar(value=False)
            benchmark_vars[benchmark_name] = var
            
            cb = ttk.Checkbutton(frame, text=benchmark_name, variable=var)
            cb.pack(anchor=tk.W)
            
            # Description
            desc_label = ttk.Label(frame, text=f"   {benchmark_info['description']}", 
                                  font=('Segoe UI', 9))
            desc_label.pack(anchor=tk.W, padx=20)
            
            # Format
            format_label = ttk.Label(frame, text=f"   Format: {benchmark_info['format']}", 
                                    font=('Segoe UI', 8), foreground='gray')
            format_label.pack(anchor=tk.W, padx=40)
            
            ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ═══════════════════════════════════════════════════════════════════
        # CLASS LIMIT INPUT
        # ═══════════════════════════════════════════════════════════════════
        limit_frame = ttk.LabelFrame(benchmark_window, text="  Dataset Size", padding=10)
        limit_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(limit_frame, text="How many classes to analyze?",
                 font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        
        limit_subframe = ttk.Frame(limit_frame)
        limit_subframe.pack(fill=tk.X, pady=5)
        
        class_limit_var = tk.StringVar(value="all")
        
        ttk.Radiobutton(limit_subframe, text="All classes in repository",
                       variable=class_limit_var, value="all").pack(anchor=tk.W)
        
        custom_frame = ttk.Frame(limit_subframe)
        custom_frame.pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(custom_frame, text="First",
                       variable=class_limit_var, value="custom").pack(side=tk.LEFT)
        
        class_count_var = tk.StringVar(value="100")
        class_count_entry = ttk.Entry(custom_frame, textvariable=class_count_var, width=10)
        class_count_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(custom_frame, text="classes").pack(side=tk.LEFT)
        
        # ═══════════════════════════════════════════════════════════════════
        # QUICK SELECT BUTTONS
        # ═══════════════════════════════════════════════════════════════════
        quick_frame = ttk.LabelFrame(benchmark_window, text="Quick Select", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def select_all():
            for var in benchmark_vars.values():
                var.set(True)
            update_count()
        
        def deselect_all():
            for var in benchmark_vars.values():
                var.set(False)
            update_count()
        
        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Select All", command=select_all,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All", command=deselect_all).pack(side=tk.LEFT, padx=2)
        
        # Selected count
        count_var = tk.StringVar(value="Selected: 0")
        count_label = ttk.Label(quick_frame, textvariable=count_var,
                               font=('Segoe UI', 10, 'bold'))
        count_label.pack(anchor=tk.E, pady=(5, 0))
        
        def update_count():
            count = sum(1 for var in benchmark_vars.values() if var.get())
            count_var.set(f"Selected: {count}/{len(benchmark_vars)}")
        
        # Trace changes
        for var in benchmark_vars.values():
            var.trace('w', lambda *args: update_count())
        
        # ═══════════════════════════════════════════════════════════════════
        # BUTTON SECTION
        # ═══════════════════════════════════════════════════════════════════
        button_frame = ttk.Frame(benchmark_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_benchmarks():
            selected = [name for name, var in benchmark_vars.items() if var.get()]
            
            if not selected:
                messagebox.showwarning("Warning", "Please select at least one benchmark")
                return
            
            # Get class limit
            if class_limit_var.get() == "all":
                class_limit = None  # All classes
            else:
                try:
                    class_limit = int(class_count_var.get())
                except:
                    messagebox.showerror("Error", "Invalid class count. Please enter a number.")
                    return
            
            # Save to config
            self.dataset_config['selected_benchmarks'] = selected
            self.dataset_config['class_limit'] = class_limit
            
            benchmark_window.destroy()
            
            # DIRECTLY GENERATE - NO PLAN, NO APPROVAL!
            benchmark_str = ', '.join(selected[:3])
            if len(selected) > 3:
                benchmark_str += f", ... and {len(selected)-3} more"
            
            self.add_agent_message(MessageType.SYSTEM,
                f"Generating {len(selected)} benchmark dataset(s)...\n"
                f"Benchmarks: {benchmark_str}"
            )
            
            # Generate directly in thread
            def generate():
                result = self.task_generate_benchmark_output(selected)
                self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS, result))
            
            threading.Thread(target=generate, daemon=True).start()
        
        ttk.Button(button_frame, text="Apply Selection",
                  command=apply_benchmarks, style='Accent.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Cancel",
                  command=benchmark_window.destroy).pack(side=tk.LEFT, padx=2)
        
    def show_metrics_selector(self):
        """Show metrics selector dialog - ALL 65 metrics from catalog"""
        # Create metrics window
        metrics_window = tk.Toplevel(self.root)
        metrics_window.title("  Select Metrics (65 Available)")
        metrics_window.geometry("900x700")
        metrics_window.grab_set()
        
        # Header
        header = ttk.Label(metrics_window, text="Select Metrics from Catalog (65 Total)",
                          font=('Segoe UI', 12, 'bold'))
        header.pack(pady=10)
        
        # Get ALL metrics from catalog
        if not self.catalog:
            messagebox.showerror("Error", "Metrics catalog not available")
            metrics_window.destroy()
            return
        
        all_metrics = self.catalog.get_all_metrics()
        categories_dict = {}
        
        # Organize by category
        for key, metric in all_metrics.items():
            cat = metric.get('category', 'other').upper()
            if cat not in categories_dict:
                categories_dict[cat] = {}
            categories_dict[cat][key] = metric.get('name', key)
        
        # Info label showing actual count
        info_label = ttk.Label(metrics_window, 
                              text=f"Total: {len(all_metrics)} metrics across {len(categories_dict)} categories",
                              font=('Segoe UI', 9), foreground='blue')
        info_label.pack(pady=(0, 10))
        
        # Category tabs
        notebook = ttk.Notebook(metrics_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        metric_vars = {}
        
        # Create tab for each category
        for category, metrics_in_cat in sorted(categories_dict.items()):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=f"{category} ({len(metrics_in_cat)})")
            
            # Scrollable content
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Add metrics checkboxes
            for metric_key, metric_name in sorted(metrics_in_cat.items()):
                var = tk.BooleanVar(value=metric_key in self.selected_metrics)
                metric_vars[metric_key] = var
                
                chk = ttk.Checkbutton(scrollable_frame, text=f"{metric_name} ({metric_key})",
                                     variable=var)
                chk.pack(anchor=tk.W, padx=10, pady=2)
        
        # Bottom buttons
        btn_frame = ttk.Frame(metrics_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Select/Deselect all
        ttk.Button(btn_frame, text="Select All",
                  command=lambda: [v.set(True) for v in metric_vars.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All",
                  command=lambda: [v.set(False) for v in metric_vars.values()]).pack(side=tk.LEFT, padx=2)
        
        # Save button
        def save_selection():
            self.selected_metrics = [k for k, v in metric_vars.items() if v.get()]
            self.selected_metrics_count.set(f"{len(self.selected_metrics)}/65 selected")
            self.add_agent_message(MessageType.SUCCESS, 
                f"Selected {len(self.selected_metrics)} metrics")
            metrics_window.destroy()
        
        ttk.Button(btn_frame, text="  Save Selection",
                  command=save_selection,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=2)
        
        ttk.Button(btn_frame, text="✗ Cancel",
                  command=metrics_window.destroy).pack(side=tk.RIGHT, padx=2)
    

    def _create_plan_from_benchmarks(self, selected_benchmarks: List[str]):
        """Create a task plan for benchmark dataset"""
        # Clear existing tasks
        self.task_manager.clear_tasks()
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Creating plan for benchmark dataset with {len(selected_benchmarks)} benchmark(s)...")
        
        # Create tasks for benchmarks - NO individual approvals
        self.task_manager.add_task(
            "Verify Repository",
            "Check if the repository is valid and accessible",
            action=self.task_verify_repo,
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Analyze Repository",
            f"Extract REAL metrics from repository",
            action=lambda: self.task_analyze_benchmarks(selected_benchmarks),
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Generate Dataset",
            f"Create {len(selected_benchmarks)} benchmark dataset(s) with REAL data",
            action=lambda: self.task_generate_benchmark_output(selected_benchmarks),
            requires_approval=False
        )
        
        self.task_manager.add_task(
            "Save to Output",
            "Save generated datasets to output folder",
            action=self.task_validate,
            requires_approval=False
        )
        
        # Show summary
        summary = f"""
**Plan Created with {len(self.task_manager.tasks)} tasks:**

"""
        for task in self.task_manager.tasks:
            summary += f"  {task.id}. {task.title}\n"
        
        benchmark_list = ', '.join(selected_benchmarks[:3])
        if len(selected_benchmarks) > 3:
            benchmark_list += f", ... and {len(selected_benchmarks)-3} more"
            
        summary += f"""
**Configuration:**
- Dataset Type: Benchmark
- Benchmarks: {benchmark_list}
- Output Format: CSV/JSON

Click **▶ Start Execution** to begin.
"""
        
        self.add_agent_message(MessageType.INFO, summary)
        
        # Enable start button
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
    
    def _create_plan_from_metrics(self, selected_metrics: List[str]):
        """Create dataset using enhanced system - no more task overhead!"""
        if not self.repo_path:
            self.add_agent_message(MessageType.ERROR, "   Repository path not set")
            return
        
        # Update enhanced system with selected metrics
        self.dataset_config['selected_metrics'] = selected_metrics
        
        self.add_agent_message(MessageType.SYSTEM,
            f"Generating dataset with {len(selected_metrics)} metrics...")
        
        # Run generation in background thread to avoid freezing GUI
        thread = threading.Thread(
            target=self._generate_metrics_dataset_direct,
            args=(selected_metrics,),
            daemon=True
        )
        thread.start()
    
    def _generate_metrics_dataset_direct(self, selected_metrics: List[str]):
        """Generate dataset directly using analyzer tools"""
        try:
            # CRITICAL: Check if metrics_helper is available
            if not self.metrics_helper:
                safe_print("self.metrics_helper is None in _generate_metrics_dataset_direct!")
                safe_print(f"  repo_path: {self.repo_path}")
                safe_print(f"  METRICS_HELPER_AVAILABLE: {METRICS_HELPER_AVAILABLE}")
                
                # Try to reinitialize
                if METRICS_HELPER_AVAILABLE and self.repo_path:
                    try:
                        safe_print("Re-initializing MetricsHelper...")
                        self.metrics_helper = MetricsHelper(str(self.repo_path))
                        safe_print(" MetricsHelper re-initialized!")
                    except Exception as e:
                        safe_print(f"  Could not re-initialize MetricsHelper: {e}")
                        self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                            f"   MetricsHelper not available - cannot extract metrics"))
                        return
                else:
                    self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                        f"   MetricsHelper not available - please restart application"))
                    return
            
            safe_print(f"Starting with {len(selected_metrics)} selected metrics")
            safe_print(f"MetricsHelper status: {self.metrics_helper is not None}")
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING, 
                f"[STEP 1] Scanning repository..."))
            
            # Get all Java files
            java_files = []
            for root_dir, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv']]
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root_dir, file))

            # Apply file limit from GUI
            raw_limit = self.file_limit_var.get().strip() if hasattr(self, 'file_limit_var') else 'All'
            if raw_limit and raw_limit.lower() not in ('all', '0', ''):
                try:
                    limit_num = int(raw_limit)
                    java_files = java_files[:limit_num]
                except ValueError:
                    pass

            self.root.after(0, lambda n=len(java_files): self.add_agent_message(MessageType.SUCCESS,
                f"Found {n} Java files (limit: {raw_limit})"))

            # Extract metrics from each file
            self.root.after(0, lambda n=len(java_files): self.add_agent_message(MessageType.THINKING,
                f"[STEP 2] Extracting metrics from {n} files..."))
            
            all_metrics = []
            total_files = len(java_files)

            # Debug first file info before parallel run
            if java_files:
                safe_print(f"\n========== PROCESSING FIRST FILE ==========")
                safe_print(f"File path: {java_files[0]}")
                safe_print(f"self.metrics_helper exists: {self.metrics_helper is not None}")
                safe_print(f"selected_metrics count: {len(selected_metrics)}")
                safe_print(f"selected_metrics sample: {selected_metrics[:5]}")

            processed_count = [0]
            count_lock = threading.Lock()
            progress_step = max(1, total_files // 10)

            def _process_file(file_path):
                try:
                    fm = self._extract_file_metrics(file_path, selected_metrics)
                    fm['file'] = file_path.replace(self.repo_path, '').lstrip(os.sep)
                    with count_lock:
                        processed_count[0] += 1
                        cnt = processed_count[0]
                    if cnt % progress_step == 0 or cnt == total_files:
                        self.root.after(0, lambda i=cnt, t=total_files:
                            self.add_agent_message(MessageType.INFO,
                            f"Processed {i}/{t} files ({int(i/t*100)}%)..."))
                    return fm
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                results = list(executor.map(_process_file, java_files))

            all_metrics = [r for r in results if r is not None]

            # Debug first file result
            if all_metrics:
                first = all_metrics[0]
                safe_print(f"\nFIRST FILE RESULT")
                safe_print(f"  Type: {type(first)}")
                safe_print(f"  Keys: {list(first.keys())}")
                safe_print(f"  Count: {len(first)}")
                safe_print(f"  Sample values: {list(first.items())[:3]}")
                print(f" Keys: {list(first.keys())}, Count: {len(first)}")
                print(f" Content preview: {dict(list(first.items())[:5])}")
            
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Extracted metrics from {len(all_metrics)} files"))
            
            # Apply custom formulas if any
            if hasattr(self, 'custom_metrics_to_apply') and self.custom_metrics_to_apply:
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"[STEP 3] Applying {len(self.custom_metrics_to_apply)} custom formula(s)..."))
                
                for formula_name, formula_def in self.custom_metrics_to_apply.items():
                    for row in all_metrics:
                        try:
                            # Safe formula evaluation
                            result = self._safe_eval_formula(formula_def['formula'], row)
                            row[formula_name] = result
                        except:
                            row[formula_name] = None
            
            # Save to CSV
            self.root.after(0, lambda: self.add_agent_message(MessageType.THINKING,
                f"[STEP 4] Saving dataset to CSV..."))
            
            output_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "generated_datasets"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"custom_dataset_{timestamp}.csv"
            
            # DEBUG: Check first row metrics
            if all_metrics and len(all_metrics) > 0:
                first_row = all_metrics[0]
                num_cols = len(first_row)
                col_names = list(first_row.keys())
                print(f"First row has {num_cols} columns: {col_names}")
                self.root.after(0, lambda: self.add_agent_message(MessageType.INFO,
                    f"  First row keys: {col_names}"))
            
            df = pd.DataFrame(all_metrics)
            df.to_csv(output_file, index=False)
            
            # Success message
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Dataset saved: {output_file.name}",
                actions=[{
                    'label': 'Open Dataset Folder',
                    'callback': lambda p=str(output_file): os.startfile(p) if sys.platform == 'win32' else subprocess.Popen(['open', p]) if sys.platform == 'darwin' else subprocess.Popen(['xdg-open', p])
                }]
            ))
            self.root.after(0, lambda: self.add_agent_message(MessageType.SUCCESS,
                f"Generated: {len(all_metrics)} rows × {len(df.columns)} metrics"))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_agent_message(MessageType.ERROR,
                f"{str(e)[:100]}"))
            print(f"Error:\n{traceback.format_exc()}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # AUTONOMOUS AGENT METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    

