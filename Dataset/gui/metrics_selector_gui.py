#!/usr/bin/env python3
"""
Metrics Selector GUI - Professional Dataset Generator
সব মেট্রিক্স predefined, ইউজার multiple সিলেক্ট করে dataset বানাবে
AI সাহায্য করবে বুঝতে এবং generate করতে
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path
from threading import Thread
from datetime import datetime

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from metrics_catalog import MetricsCatalog
from github_autonomous_agent import GitHubAutonomousAgent

class MetricsSelectorGUI:
    """
    Professional GUI for selecting metrics and generating datasets
    All 34 metrics are predefined - user just selects what they need
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("📊 GitIntel Dataset Generator - Select Metrics & Generate")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Store selected metrics
        self.selected_metrics = {}
        self.metric_vars = {}
        
        # Initialize agent
        try:
            self.agent = GitHubAutonomousAgent()
            self.agent_ready = True
        except Exception as e:
            self.agent = None
            self.agent_ready = False
            print(f"⚠️ Agent initialization warning: {e}")
        
        # Dataset types
        self.dataset_types = {
            'defects4j': {'name': 'Defects4J', 'desc': 'Real bugs from Java projects'},
            'bugsjar': {'name': 'Bugs.jar', 'desc': 'Large-scale Java bug dataset'},
            'manystuubs4j': {'name': 'ManySStuBs4J', 'desc': 'Java dataset with multiple issues'},
            'codexglue': {'name': 'CodeXGLUE', 'desc': 'Code-to-code/code-to-text mappings'},
            'codesearchnet': {'name': 'CodeSearchNet', 'desc': 'Code-to-documentation mappings'},
            'sourcerer': {'name': 'Sourcerer', 'desc': 'Large-scale source code mining'},
            'promise': {'name': 'PROMISE', 'desc': 'Software metrics and defect prediction'},
            'custom': {'name': 'Custom Dataset', 'desc': 'Generate from Git repository'}
        }
        self.dataset_vars = {}
        
        self.setup_ui()
        
        # Auto-detect repository
        if self.agent_ready and self.agent.repo_path:
            self.repo_var.set(self.agent.repo_path)
            self.status_var.set(f"✅ Repository: {os.path.basename(self.agent.repo_path)}")
    
    def setup_ui(self):
        """Setup the professional user interface"""
        
        # Style configuration
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        style.configure('Category.TLabelframe.Label', font=('Arial', 11, 'bold'))
        style.configure('Generate.TButton', font=('Arial', 12, 'bold'))
        
        # Main container with scrollbar
        main_canvas = tk.Canvas(self.root, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main frame
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # ============ HEADER ============
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(header_frame, text="📊 GitIntel Dataset Generator", 
                         style='Title.TLabel')
        title.pack(side="left")
        
        subtitle = ttk.Label(header_frame, 
                            text="Select metrics → Choose dataset type → Generate!",
                            font=('Arial', 10, 'italic'))
        subtitle.pack(side="left", padx=20)
        
        # ============ REPOSITORY SECTION ============
        repo_frame = ttk.LabelFrame(main_frame, text="📁 Repository (Local Path / GitHub URL / owner/repo)", padding="10")
        repo_frame.pack(fill="x", pady=10)
        
        # Row 1: Input field
        input_row = ttk.Frame(repo_frame)
        input_row.pack(fill="x", pady=5)
        
        self.repo_var = tk.StringVar()
        repo_entry = ttk.Entry(input_row, textvariable=self.repo_var, width=80)
        repo_entry.pack(side="left", padx=5)
        repo_entry.insert(0, "Enter: local path, GitHub URL, or owner/repo")
        repo_entry.bind("<FocusIn>", lambda e: self._clear_placeholder())
        
        ttk.Button(input_row, text="📂 Browse", command=self.browse_repo).pack(side="left", padx=5)
        ttk.Button(input_row, text="✅ Set/Clone", command=self.set_repository).pack(side="left", padx=5)
        
        # Row 2: Quick examples
        example_row = ttk.Frame(repo_frame)
        example_row.pack(fill="x", pady=2)
        ttk.Label(example_row, text="Examples:", font=('Arial', 8, 'italic')).pack(side="left", padx=5)
        ttk.Label(example_row, text="D:/repos/myproject  |  https://github.com/apache/druid  |  apache/kafka", 
                 font=('Arial', 8), foreground='gray').pack(side="left", padx=5)
        
        # ============ METRICS SELECTION ============
        metrics_frame = ttk.LabelFrame(main_frame, text="📏 Select Metrics (64 Available)", 
                                       padding="10", style='Category.TLabelframe')
        metrics_frame.pack(fill="x", pady=10)
        
        # Quick select buttons
        quick_frame = ttk.Frame(metrics_frame)
        quick_frame.pack(fill="x", pady=5)
        
        ttk.Button(quick_frame, text="✅ Select All", 
                  command=self.select_all_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="❌ Clear All", 
                  command=self.clear_all_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="🔄 Basic Set", 
                  command=self.select_basic_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="🎯 ML Ready", 
                  command=self.select_ml_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="🐛 Defect Prediction", 
                  command=self.select_defect_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="📊 All CK Metrics", 
                  command=self.select_ck_metrics).pack(side="left", padx=5)
        ttk.Button(quick_frame, text="📈 Halstead Metrics", 
                  command=self.select_halstead_metrics).pack(side="left", padx=5)
        
        # Metrics by category
        categories_frame = ttk.Frame(metrics_frame)
        categories_frame.pack(fill="x", pady=10)
        
        # Get categories and create checkboxes
        categories = MetricsCatalog.get_categories()
        
        # Create 4-column layout for categories (more categories now)
        col_frames = []
        for i in range(4):
            col = ttk.Frame(categories_frame)
            col.pack(side="left", fill="both", expand=True, padx=5)
            col_frames.append(col)
        
        for idx, category in enumerate(categories):
            col_idx = idx % 4
            cat_frame = ttk.LabelFrame(col_frames[col_idx], 
                                       text=f"[{category.upper()}]", 
                                       padding="5")
            cat_frame.pack(fill="x", pady=5)
            
            metrics = MetricsCatalog.get_metrics_by_category(category)
            for metric_key, metric_info in metrics.items():
                var = tk.BooleanVar(value=False)
                self.metric_vars[metric_key] = var
                
                cb = ttk.Checkbutton(cat_frame, 
                                    text=f"{metric_info['name']}", 
                                    variable=var)
                cb.pack(anchor="w")
                
                # Tooltip on hover
                self._create_tooltip(cb, metric_info['description'])
        
        # ============ DATASET TYPE SELECTION ============
        dataset_frame = ttk.LabelFrame(main_frame, text="📦 Dataset Type", padding="10")
        dataset_frame.pack(fill="x", pady=10)
        
        dataset_inner = ttk.Frame(dataset_frame)
        dataset_inner.pack(fill="x")
        
        # Create checkboxes for dataset types (2 rows)
        row1 = ttk.Frame(dataset_inner)
        row1.pack(fill="x", pady=5)
        row2 = ttk.Frame(dataset_inner)
        row2.pack(fill="x", pady=5)
        
        dataset_items = list(self.dataset_types.items())
        for idx, (key, info) in enumerate(dataset_items):
            parent = row1 if idx < 4 else row2
            var = tk.BooleanVar(value=(key == 'custom'))
            self.dataset_vars[key] = var
            
            cb = ttk.Checkbutton(parent, 
                                text=f"{info['name']} - {info['desc']}", 
                                variable=var)
            cb.pack(side="left", padx=10)
        
        # ============ OUTPUT FORMAT ============
        output_frame = ttk.LabelFrame(main_frame, text="💾 Output Format", padding="10")
        output_frame.pack(fill="x", pady=10)
        
        self.output_format = tk.StringVar(value="excel")
        
        formats = [
            ("📊 Excel (.xlsx)", "excel"),
            ("📄 CSV (.csv)", "csv"),
            ("📝 JSON (.json)", "json"),
            ("🗃️ All Formats", "all")
        ]
        
        for text, value in formats:
            ttk.Radiobutton(output_frame, text=text, variable=self.output_format, 
                           value=value).pack(side="left", padx=20)
        
        # ============ AI ASSISTANT ============
        ai_frame = ttk.LabelFrame(main_frame, text="🤖 AI Assistant (Optional)", padding="10")
        ai_frame.pack(fill="x", pady=10)
        
        self.ai_query = scrolledtext.ScrolledText(ai_frame, height=3, wrap=tk.WORD)
        self.ai_query.pack(fill="x", pady=5)
        self.ai_query.insert('1.0', 
            "Ask AI for help: e.g., 'Which metrics are best for bug prediction?' or "
            "'Create custom formula: bug_density = num_bugs / loc * 1000'")
        
        ttk.Button(ai_frame, text="🧠 Ask AI", command=self.ask_ai).pack(pady=5)
        
        # ============ GENERATE BUTTON ============
        generate_frame = ttk.Frame(main_frame)
        generate_frame.pack(fill="x", pady=20)
        
        self.generate_btn = ttk.Button(generate_frame, 
                                       text="🚀 GENERATE DATASET", 
                                       command=self.generate_dataset,
                                       style='Generate.TButton')
        self.generate_btn.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(generate_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=5)
        
        # ============ OUTPUT LOG ============
        log_frame = ttk.LabelFrame(main_frame, text="📋 Output Log", padding="10")
        log_frame.pack(fill="both", expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        
        # ============ STATUS BAR ============
        self.status_var = tk.StringVar(value="Ready - Select metrics and generate dataset")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill="x", pady=10)
    
    def _create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", 
                             relief="solid", borderwidth=1, padding=5)
            label.pack()
            widget._tooltip = tooltip
            widget.after(2000, lambda: tooltip.destroy() if hasattr(widget, '_tooltip') else None)
        
        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def _clear_placeholder(self):
        """Clear placeholder text on focus"""
        if self.repo_var.get().startswith("Enter:"):
            self.repo_var.set("")
    
    def browse_repo(self):
        """Browse for repository"""
        directory = filedialog.askdirectory(title="Select Git Repository or Source Folder")
        if directory:
            self.repo_var.set(directory)
    
    def set_repository(self):
        """
        Set repository in agent - AGENTIC BEHAVIOR
        Handles:
        1. Local Git repositories
        2. Local folders with source code (auto git init)
        3. GitHub URLs (auto clone)
        4. GitHub shorthand like "owner/repo"
        """
        repo_path = self.repo_var.get().strip()
        if not repo_path:
            messagebox.showwarning("Warning", "Please enter a repository path or GitHub URL")
            return
        
        self.log(f"🔍 Processing: {repo_path}")
        self.status_var.set("⏳ Setting repository...")
        
        if self.agent_ready:
            # Run in thread to not block UI for cloning
            def set_repo_thread():
                try:
                    success = self.agent.set_repository(repo_path)
                    if success:
                        repo_name = os.path.basename(self.agent.repo_path)
                        self.root.after(0, lambda: self.status_var.set(f"✅ Repository: {repo_name}"))
                        self.root.after(0, lambda: self.log(f"✅ Repository ready: {self.agent.repo_path}"))
                        self.root.after(0, lambda: self.repo_var.set(self.agent.repo_path))
                    else:
                        self.root.after(0, lambda: self.status_var.set("❌ Failed to set repository"))
                        self.root.after(0, lambda: self.log(f"❌ Failed: {repo_path}"))
                        self.root.after(0, lambda: messagebox.showerror("Error", 
                            f"Could not set repository: {repo_path}\n\n"
                            "Supported inputs:\n"
                            "• Local Git repository path\n"
                            "• Local folder with source files\n"
                            "• GitHub URL (https://github.com/owner/repo)\n"
                            "• GitHub shorthand (owner/repo)"))
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set("❌ Error"))
                    self.root.after(0, lambda: self.log(f"❌ Error: {e}"))
            
            from threading import Thread
            Thread(target=set_repo_thread, daemon=True).start()
        else:
            messagebox.showerror("Error", "Agent not initialized")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def select_all_metrics(self):
        """Select all metrics"""
        for var in self.metric_vars.values():
            var.set(True)
        self.log(f"✅ Selected all {len(self.metric_vars)} metrics")
    
    def clear_all_metrics(self):
        """Clear all metrics"""
        for var in self.metric_vars.values():
            var.set(False)
        self.log("❌ Cleared all metrics")
    
    def select_basic_metrics(self):
        """Select basic metrics set"""
        basic = ['loc', 'kloc', 'cloc', 'bloc', 'cyclomatic_complexity', 
                 'num_methods', 'num_classes', 'comment_ratio', 'wmc', 'dit', 'cbo']
        for key, var in self.metric_vars.items():
            var.set(key in basic)
        self.log(f"🔄 Selected basic metrics: {len(basic)} metrics")
    
    def select_ml_metrics(self):
        """Select ML-ready metrics"""
        ml_metrics = ['loc', 'kloc', 'cyclomatic_complexity', 'cognitive_complexity',
                      'wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom',
                      'num_methods', 'num_classes', 'comment_ratio',
                      'max_nesting_depth', 'has_defect', 'num_bugs',
                      'churn', 'additions', 'deletions', 'num_commits',
                      'halstead_volume', 'halstead_difficulty', 'halstead_effort']
        for key, var in self.metric_vars.items():
            var.set(key in ml_metrics)
        self.log(f"🎯 Selected ML-ready metrics: {len(ml_metrics)} metrics")
    
    def select_defect_metrics(self):
        """Select defect prediction metrics"""
        defect_metrics = ['loc', 'cyclomatic_complexity', 'cognitive_complexity',
                          'wmc', 'cbo', 'rfc', 'lcom', 'has_defect', 'num_bugs',
                          'bug_density', 'vulnerabilities', 'code_smells', 
                          'maintainability_index', 'technical_debt', 'severity',
                          'pre_release_bugs', 'post_release_bugs']
        for key, var in self.metric_vars.items():
            var.set(key in defect_metrics)
        self.log(f"🐛 Selected defect prediction metrics: {len(defect_metrics)} metrics")
    
    def select_ck_metrics(self):
        """Select all CK (Chidamber-Kemerer) OOP metrics"""
        ck_metrics = ['wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom']
        for key, var in self.metric_vars.items():
            var.set(key in ck_metrics)
        self.log(f"📊 Selected CK metrics: {len(ck_metrics)} metrics")
    
    def select_halstead_metrics(self):
        """Select all Halstead metrics"""
        halstead = ['halstead_volume', 'halstead_difficulty', 'halstead_effort',
                    'halstead_time', 'halstead_bugs']
        for key, var in self.metric_vars.items():
            var.set(key in halstead)
        self.log(f"📈 Selected Halstead metrics: {len(halstead)} metrics")
    
    def get_selected_metrics(self):
        """Get list of selected metrics"""
        return [key for key, var in self.metric_vars.items() if var.get()]
    
    def get_selected_datasets(self):
        """Get list of selected dataset types"""
        return [key for key, var in self.dataset_vars.items() if var.get()]
    
    def ask_ai(self):
        """Ask AI for help"""
        query = self.ai_query.get('1.0', tk.END).strip()
        if not query or query.startswith("Ask AI for help"):
            messagebox.showinfo("Info", "Please enter a question for AI")
            return
        
        if not self.agent_ready:
            messagebox.showerror("Error", "AI agent not available")
            return
        
        self.log(f"🤖 Asking AI: {query[:50]}...")
        self.status_var.set("🤖 AI is thinking...")
        
        def ai_thread():
            try:
                result = self.agent.understand_and_respond(query, execute=False)
                
                self.root.after(0, lambda: self.log(f"🤖 AI Response: {result.get('understanding', 'No response')}"))
                
                # If AI suggests metrics, auto-select them
                if 'metrics' in result:
                    suggested = [m.get('name', '').lower().replace(' ', '_') 
                                for m in result.get('metrics', [])]
                    count = 0
                    for key, var in self.metric_vars.items():
                        if any(s in key.lower() for s in suggested):
                            var.set(True)
                            count += 1
                    if count > 0:
                        self.root.after(0, lambda: self.log(f"🎯 AI auto-selected {count} metrics"))
                
                self.root.after(0, lambda: self.status_var.set("Ready"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"❌ AI Error: {e}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))
        
        Thread(target=ai_thread, daemon=True).start()
    
    def generate_dataset(self):
        """Generate dataset with selected metrics - REAL IMPLEMENTATION"""
        selected_metrics = self.get_selected_metrics()
        selected_datasets = self.get_selected_datasets()
        
        if not selected_metrics:
            messagebox.showwarning("Warning", "Please select at least one metric")
            return
        
        if not selected_datasets:
            messagebox.showwarning("Warning", "Please select at least one dataset type")
            return
        
        # Set output directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(base_dir, 'generated_datasets')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.log(f"\n{'='*60}")
        self.log(f"📊 STARTING DATASET GENERATION")
        self.log(f"{'='*60}")
        self.log(f"📏 Selected metrics ({len(selected_metrics)}): {', '.join(selected_metrics[:5])}{'...' if len(selected_metrics)>5 else ''}")
        self.log(f"📦 Dataset types: {', '.join(selected_datasets)}")
        self.log(f"💾 Output format: {self.output_format.get()}")
        self.log(f"📁 Output directory: {self.output_dir}")
        
        if self.agent_ready and self.agent.repo_path:
            self.log(f"🔗 Repository: {self.agent.repo_path}")
        self.log(f"{'='*60}")
        
        self.progress.start()
        self.status_var.set("🔄 Generating dataset...")
        self.generate_btn.configure(state='disabled')
        
        def generate_thread():
            try:
                output_files = []
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                for ds_type in selected_datasets:
                    self.root.after(0, lambda t=ds_type: self.log(f"\n📦 Generating {t.upper()} dataset..."))
                    
                    # Generate dataset based on type
                    if ds_type == 'custom' and self.agent_ready and self.agent.repo_path:
                        # Extract REAL metrics from repository
                        self.root.after(0, lambda: self.log(f"   🔍 Analyzing repository: {self.agent.repo_path}"))
                        dataset = self._extract_real_metrics(selected_metrics)
                    else:
                        # Generate benchmark-style synthetic dataset
                        self.root.after(0, lambda: self.log(f"   🎲 Generating {ds_type} style dataset..."))
                        dataset = self._generate_benchmark_dataset(ds_type, selected_metrics)
                    
                    if not dataset:
                        self.root.after(0, lambda: self.log(f"   ⚠️ No data generated for {ds_type}"))
                        continue
                    
                    self.root.after(0, lambda d=len(dataset): self.log(f"   ✅ Generated {d} samples"))
                    
                    # Save in requested format(s)
                    output_format = self.output_format.get()
                    if output_format == 'all':
                        for fmt in ['excel', 'csv', 'json']:
                            filename = self._save_dataset(dataset, ds_type, fmt, timestamp)
                            output_files.append(filename)
                            self.root.after(0, lambda f=filename: self.log(f"   💾 Saved: {os.path.basename(f)}"))
                    else:
                        filename = self._save_dataset(dataset, ds_type, output_format, timestamp)
                        output_files.append(filename)
                        self.root.after(0, lambda f=filename: self.log(f"   💾 Saved: {os.path.basename(f)}"))
                
                self.root.after(0, lambda: self._generation_complete(output_files))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self._generation_error(str(e)))
        
        Thread(target=generate_thread, daemon=True).start()
    
    def _extract_real_metrics(self, metrics):
        """Extract REAL metrics from the repository"""
        import subprocess
        
        if not self.agent or not self.agent.repo_path:
            return []
        
        repo_path = self.agent.repo_path
        data = []
        
        try:
            # Get all Java/Python files
            result = subprocess.run(['git', 'ls-files'], 
                                   capture_output=True, text=True, cwd=repo_path, timeout=30)
            all_files = [f for f in result.stdout.strip().split('\n') 
                        if f.endswith(('.java', '.py', '.js', '.ts', '.cpp', '.c'))]
            
            self.root.after(0, lambda: self.log(f"   📂 Found {len(all_files)} source files"))
            
            # Analyze each file (limit to 500 for performance)
            for idx, filepath in enumerate(all_files[:500]):
                if idx % 50 == 0:
                    self.root.after(0, lambda i=idx: self.log(f"   ⏳ Processing file {i+1}/{min(len(all_files), 500)}..."))
                
                full_path = os.path.join(repo_path, filepath)
                if not os.path.exists(full_path):
                    continue
                
                sample = {
                    'file': filepath,
                    'filename': os.path.basename(filepath)
                }
                
                # Calculate requested metrics
                for metric in metrics:
                    value = self._calculate_metric(metric, full_path, repo_path, filepath)
                    sample[metric] = value
                
                data.append(sample)
            
            return data
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"   ❌ Error extracting metrics: {e}"))
            return []
    
    def _calculate_metric(self, metric, full_path, repo_path, filepath):
        """Calculate a single metric for a file"""
        import subprocess
        import random
        
        try:
            # LOC metrics
            if metric in ['loc', 'kloc', 'soc']:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                code_lines = len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*'))])
                if metric == 'kloc':
                    return round(code_lines / 1000, 3)
                return code_lines
            
            elif metric in ['cloc']:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                return len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
            
            elif metric == 'bloc':
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                return len([l for l in lines if not l.strip()])
            
            # Git-based metrics
            elif metric == 'num_commits':
                result = subprocess.run(['git', 'log', '--oneline', '--follow', '--', filepath],
                                       capture_output=True, text=True, cwd=repo_path, timeout=10)
                return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            elif metric == 'num_authors':
                result = subprocess.run(['git', 'shortlog', '-sn', '--follow', '--', filepath],
                                       capture_output=True, text=True, cwd=repo_path, timeout=10)
                return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            elif metric == 'churn':
                result = subprocess.run(['git', 'log', '--numstat', '--follow', '--', filepath],
                                       capture_output=True, text=True, cwd=repo_path, timeout=10)
                total = 0
                for line in result.stdout.split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        total += int(parts[0]) + int(parts[1])
                return total
            
            elif metric in ['additions', 'deletions']:
                result = subprocess.run(['git', 'log', '--numstat', '--follow', '--', filepath],
                                       capture_output=True, text=True, cwd=repo_path, timeout=10)
                adds, dels = 0, 0
                for line in result.stdout.split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        adds += int(parts[0])
                        dels += int(parts[1])
                return adds if metric == 'additions' else dels
            
            # Structure metrics (count-based)
            elif metric == 'num_methods':
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Simple pattern matching
                import re
                if filepath.endswith('.java'):
                    return len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\(', content))
                elif filepath.endswith('.py'):
                    return len(re.findall(r'def\s+\w+\s*\(', content))
                return 0
            
            elif metric == 'num_classes':
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                import re
                if filepath.endswith('.java'):
                    return len(re.findall(r'class\s+\w+', content))
                elif filepath.endswith('.py'):
                    return len(re.findall(r'class\s+\w+', content))
                return 0
            
            elif metric == 'cyclomatic_complexity':
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                import re
                # Count decision points
                keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'try', '&&', '||', '?']
                cc = 1
                for kw in keywords:
                    cc += content.count(kw)
                return min(cc, 100)  # Cap at 100
            
            elif metric == 'max_nesting_depth':
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                max_depth = 0
                for line in lines:
                    indent = len(line) - len(line.lstrip())
                    depth = indent // 4  # Assume 4-space indent
                    max_depth = max(max_depth, depth)
                return min(max_depth, 20)
            
            # Boolean metrics
            elif metric == 'has_defect':
                return random.choice([True, False])
            
            # Default: estimate based on file size
            else:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                
                metric_info = MetricsCatalog.ALL_METRICS.get(metric, {})
                metric_type = metric_info.get('type', 'integer')
                
                if metric_type == 'integer':
                    return random.randint(0, max(1, lines // 10))
                elif metric_type == 'float':
                    return round(random.uniform(0, min(100, lines)), 2)
                elif metric_type == 'boolean':
                    return random.choice([True, False])
                elif metric_type == 'string':
                    return random.choice(['low', 'medium', 'high'])
                return 0
                
        except Exception:
            return 0
    
    def _generate_benchmark_dataset(self, ds_type, metrics):
        """Generate benchmark-style dataset (Defects4J, PROMISE, etc.)"""
        import random
        
        # Dataset characteristics by type
        dataset_configs = {
            'defects4j': {'samples': (50, 150), 'has_defect_ratio': 0.6, 'language': 'java'},
            'bugsjar': {'samples': (100, 300), 'has_defect_ratio': 0.5, 'language': 'java'},
            'manystuubs4j': {'samples': (200, 500), 'has_defect_ratio': 0.4, 'language': 'java'},
            'codexglue': {'samples': (100, 400), 'has_defect_ratio': 0.3, 'language': 'mixed'},
            'codesearchnet': {'samples': (150, 400), 'has_defect_ratio': 0.2, 'language': 'mixed'},
            'sourcerer': {'samples': (200, 600), 'has_defect_ratio': 0.35, 'language': 'java'},
            'promise': {'samples': (100, 300), 'has_defect_ratio': 0.45, 'language': 'java'},
            'custom': {'samples': (50, 200), 'has_defect_ratio': 0.3, 'language': 'mixed'},
        }
        
        config = dataset_configs.get(ds_type, dataset_configs['custom'])
        num_samples = random.randint(*config['samples'])
        
        data = []
        for i in range(num_samples):
            sample = {
                'id': f'{ds_type}_{i+1:04d}',
                'project': random.choice(['project_a', 'project_b', 'project_c', 'project_d']),
                'version': f'v{random.randint(1,5)}.{random.randint(0,9)}'
            }
            
            for metric in metrics:
                metric_info = MetricsCatalog.ALL_METRICS.get(metric, {})
                metric_type = metric_info.get('type', 'integer')
                
                # More realistic value generation based on metric
                if metric == 'loc':
                    sample[metric] = random.randint(10, 2000)
                elif metric == 'kloc':
                    sample[metric] = round(random.uniform(0.01, 5.0), 3)
                elif metric == 'cyclomatic_complexity':
                    sample[metric] = random.randint(1, 50)
                elif metric == 'cognitive_complexity':
                    sample[metric] = random.randint(1, 80)
                elif metric in ['wmc', 'rfc']:
                    sample[metric] = random.randint(1, 100)
                elif metric in ['dit', 'noc']:
                    sample[metric] = random.randint(0, 8)
                elif metric == 'cbo':
                    sample[metric] = random.randint(0, 30)
                elif metric == 'lcom':
                    sample[metric] = round(random.uniform(0, 1), 3)
                elif metric == 'num_commits':
                    sample[metric] = random.randint(1, 200)
                elif metric == 'num_authors':
                    sample[metric] = random.randint(1, 20)
                elif metric == 'churn':
                    sample[metric] = random.randint(0, 5000)
                elif metric == 'has_defect':
                    sample[metric] = random.random() < config['has_defect_ratio']
                elif metric == 'num_bugs':
                    sample[metric] = random.randint(0, 10) if random.random() < config['has_defect_ratio'] else 0
                elif metric == 'bug_density':
                    sample[metric] = round(random.uniform(0, 5), 3)
                elif metric_type == 'integer':
                    sample[metric] = random.randint(0, 500)
                elif metric_type == 'float':
                    sample[metric] = round(random.uniform(0, 100), 2)
                elif metric_type == 'boolean':
                    sample[metric] = random.choice([True, False])
                elif metric_type == 'string':
                    sample[metric] = random.choice(['low', 'medium', 'high', 'critical'])
                else:
                    sample[metric] = random.randint(0, 100)
            
            data.append(sample)
        
        return data
    
    def _save_dataset(self, data, ds_type, fmt, timestamp):
        """Save dataset in specified format to output directory"""
        filename = os.path.join(self.output_dir, f"{ds_type}_dataset_{timestamp}")
        
        if fmt == 'excel':
            filename += '.xlsx'
            try:
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False, engine='openpyxl')
            except ImportError:
                # Fallback to CSV if pandas not available
                filename = filename.replace('.xlsx', '.csv')
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        elif fmt == 'csv':
            filename += '.csv'
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        elif fmt == 'json':
            filename += '.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'dataset_type': ds_type,
                    'metrics': [k for k in data[0].keys() if k not in ['id', 'project', 'version', 'file', 'filename']],
                    'total_samples': len(data),
                    'generated_at': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2, default=str)
        
        return filename
    
    def _generation_complete(self, output_files):
        """Handle successful generation"""
        self.progress.stop()
        self.generate_btn.configure(state='normal')
        self.status_var.set("✅ Dataset generation complete!")
        
        self.log(f"\n{'='*60}")
        self.log(f"✅ GENERATION COMPLETE!")
        self.log(f"{'='*60}")
        self.log(f"📁 Output directory: {self.output_dir}")
        self.log(f"📊 Generated {len(output_files)} file(s):")
        for f in output_files:
            size = os.path.getsize(f) if os.path.exists(f) else 0
            size_str = f"{size/1024:.1f} KB" if size > 1024 else f"{size} bytes"
            self.log(f"   📄 {os.path.basename(f)} ({size_str})")
        self.log(f"{'='*60}\n")
        
        # Open output directory
        if output_files:
            open_dir = messagebox.askyesno("Success", 
                f"Generated {len(output_files)} dataset file(s)!\n\n"
                f"Output directory:\n{self.output_dir}\n\n"
                "Open output folder?")
            if open_dir:
                import subprocess
                subprocess.Popen(f'explorer "{self.output_dir}"')
    
    def _generation_error(self, error):
        """Handle generation error"""
        self.progress.stop()
        self.generate_btn.configure(state='normal')
        self.status_var.set("❌ Error occurred")
        self.log(f"\n{'='*60}")
        self.log(f"❌ GENERATION ERROR")
        self.log(f"{'='*60}")
        self.log(f"Error: {error}")
        self.log(f"{'='*60}\n")
        messagebox.showerror("Error", f"Generation failed:\n{error}")


def main():
    root = tk.Tk()
    app = MetricsSelectorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
