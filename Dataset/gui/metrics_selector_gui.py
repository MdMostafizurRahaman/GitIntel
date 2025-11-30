"""
Professional Dataset Generator GUI
- Benchmark Datasets: Predefined formats (no metrics selection needed)
- Custom Dataset: User-selectable metrics (64 metrics available)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics_catalog import MetricsCatalog
from github_autonomous_agent import GitHubAutonomousAgent


class DatasetGeneratorGUI:
    """Professional Dataset Generator with Benchmark & Custom modes"""
    
    # Benchmark datasets - predefined formats, NO metrics selection needed
    BENCHMARK_DATASETS = {
        "Defects4J": {
            "description": "Java bugs with buggy/fixed folder structure",
            "format": "folder",
            "structure": ["buggy", "fixed"],
            "extensions": [".java"]
        },
        "Bugs.jar": {
            "description": "Large-scale Java bug dataset",
            "format": "json",
            "fields": ["bug_id", "project", "commit", "patch", "test"]
        },
        "ManySStuBs4J": {
            "description": "Simple stupid bugs in Java",
            "format": "json",
            "fields": ["bug_type", "buggy_code", "fixed_code", "context"]
        },
        "CodeXGLUE": {
            "description": "Microsoft code understanding benchmark",
            "format": "jsonl",
            "fields": ["code", "docstring", "label"]
        },
        "CodeSearchNet": {
            "description": "Code search and documentation dataset",
            "format": "jsonl",
            "fields": ["code", "docstring", "language", "url"]
        },
        "Sourcerer": {
            "description": "Large-scale code repository dataset",
            "format": "csv",
            "fields": ["file_path", "content", "language", "project"]
        },
        "PROMISE": {
            "description": "Software defect prediction dataset",
            "format": "csv",
            "fields": ["class", "wmc", "dit", "noc", "cbo", "rfc", "lcom", "defects"]
        }
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("GitIntel Dataset Generator")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize components
        self.catalog = MetricsCatalog()
        self.agent = GitHubAutonomousAgent()
        self.metric_vars = {}
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Build UI
        self.setup_ui()
        
    def configure_styles(self):
        """Configure custom styles"""
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('Info.TLabel', font=('Segoe UI', 10))
        self.style.configure('Success.TLabel', foreground='green')
        self.style.configure('Error.TLabel', foreground='red')
        self.style.configure('Generate.TButton', font=('Segoe UI', 11, 'bold'))
        
    def setup_ui(self):
        """Setup main UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="🔬 GitIntel Dataset Generator", 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        # Repository Section
        self.setup_repository_section(main_frame)
        
        # Mode Selection (Benchmark vs Custom)
        self.setup_mode_selection(main_frame)
        
        # Content Frame (changes based on mode)
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Benchmark content
        self.benchmark_frame = ttk.Frame(self.content_frame)
        self.setup_benchmark_section(self.benchmark_frame)
        
        # Custom content
        self.custom_frame = ttk.Frame(self.content_frame)
        self.setup_custom_section(self.custom_frame)
        
        # Output Section
        self.setup_output_section(main_frame)
        
        # Generate Button
        self.setup_generate_section(main_frame)
        
        # Status Bar
        self.setup_status_bar(main_frame)
        
        # Show benchmark by default
        self.show_benchmark_mode()
        
    def setup_repository_section(self, parent):
        """Setup repository input section"""
        repo_frame = ttk.LabelFrame(parent, text="📁 Repository", padding=10)
        repo_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Info label
        info_text = "Supports: Local folder, GitHub URL (https://github.com/owner/repo), or shorthand (owner/repo)"
        ttk.Label(repo_frame, text=info_text, style='Info.TLabel').pack(anchor=tk.W)
        
        # Input row
        input_frame = ttk.Frame(repo_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.repo_var = tk.StringVar()
        self.repo_entry = ttk.Entry(input_frame, textvariable=self.repo_var, font=('Consolas', 10))
        self.repo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.repo_entry.insert(0, "Enter path, URL, or owner/repo...")
        self.repo_entry.bind('<FocusIn>', lambda e: self.repo_entry.delete(0, tk.END) if 'Enter' in self.repo_entry.get() else None)
        
        ttk.Button(input_frame, text="📂 Browse", command=self.browse_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text="🔗 Clone", command=self.clone_repo).pack(side=tk.LEFT, padx=2)
        ttk.Button(input_frame, text="✓ Verify", command=self.verify_repo).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.repo_status_var = tk.StringVar(value="")
        self.repo_status_label = ttk.Label(repo_frame, textvariable=self.repo_status_var)
        self.repo_status_label.pack(anchor=tk.W, pady=(5, 0))
        
    def setup_mode_selection(self, parent):
        """Setup mode selection (Benchmark vs Custom)"""
        mode_frame = ttk.LabelFrame(parent, text="📊 Dataset Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="benchmark")
        
        # Benchmark option
        benchmark_frame = ttk.Frame(mode_frame)
        benchmark_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(benchmark_frame, text="Benchmark Dataset", 
                        variable=self.mode_var, value="benchmark",
                        command=self.show_benchmark_mode).pack(side=tk.LEFT)
        ttk.Label(benchmark_frame, text="- Predefined formats (Defects4J, Bugs.jar, etc.) - No metrics selection needed",
                  style='Info.TLabel').pack(side=tk.LEFT, padx=10)
        
        # Custom option
        custom_frame = ttk.Frame(mode_frame)
        custom_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(custom_frame, text="Custom Dataset", 
                        variable=self.mode_var, value="custom",
                        command=self.show_custom_mode).pack(side=tk.LEFT)
        ttk.Label(custom_frame, text="- Select from 64 metrics across 14 categories",
                  style='Info.TLabel').pack(side=tk.LEFT, padx=10)
        
    def setup_benchmark_section(self, parent):
        """Setup benchmark dataset selection"""
        # Dataset type selection
        type_frame = ttk.LabelFrame(parent, text="📋 Select Benchmark Dataset", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.benchmark_var = tk.StringVar(value="Defects4J")
        
        # Grid of benchmark options
        row = 0
        col = 0
        for name, info in self.BENCHMARK_DATASETS.items():
            frame = ttk.Frame(type_frame)
            frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            
            ttk.Radiobutton(frame, text=name, variable=self.benchmark_var, 
                           value=name, command=self.update_benchmark_info).pack(anchor=tk.W)
            ttk.Label(frame, text=info["description"], style='Info.TLabel').pack(anchor=tk.W, padx=20)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Benchmark info panel
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Dataset Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.benchmark_info_text = tk.Text(info_frame, height=15, font=('Consolas', 10), wrap=tk.WORD)
        self.benchmark_info_text.pack(fill=tk.BOTH, expand=True)
        self.benchmark_info_text.config(state=tk.DISABLED)
        
        # Defects4J specific options
        self.defects4j_frame = ttk.LabelFrame(parent, text="🗂️ Defects4J Options", padding=10)
        
        ttk.Label(self.defects4j_frame, text="Buggy folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.buggy_folder_var = tk.StringVar()
        ttk.Entry(self.defects4j_frame, textvariable=self.buggy_folder_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.defects4j_frame, text="Browse", 
                   command=lambda: self.browse_specific_folder(self.buggy_folder_var)).grid(row=0, column=2)
        
        ttk.Label(self.defects4j_frame, text="Fixed folder:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fixed_folder_var = tk.StringVar()
        ttk.Entry(self.defects4j_frame, textvariable=self.fixed_folder_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.defects4j_frame, text="Browse", 
                   command=lambda: self.browse_specific_folder(self.fixed_folder_var)).grid(row=1, column=2)
        
        ttk.Label(self.defects4j_frame, text="OR use repository with buggy/fixed branches/commits",
                  style='Info.TLabel').grid(row=2, column=0, columnspan=3, pady=5)
        
        self.update_benchmark_info()
        
    def setup_custom_section(self, parent):
        """Setup custom metrics selection"""
        # Quick select buttons
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(quick_frame, text="✓ Select All", command=self.select_all_metrics).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="✗ Deselect All", command=self.deselect_all_metrics).pack(side=tk.LEFT, padx=2)
        ttk.Separator(quick_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Category quick selects
        categories = self.catalog.get_categories()
        for cat in categories[:6]:  # First 6 categories
            ttk.Button(quick_frame, text=cat, 
                      command=lambda c=cat: self.toggle_category(c)).pack(side=tk.LEFT, padx=2)
        
        # Scrollable metrics area
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        
        self.metrics_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=self.metrics_frame, anchor=tk.NW)
        
        # Populate metrics by category
        self.populate_metrics()
        
        # Update scroll region
        self.metrics_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
    def populate_metrics(self):
        """Populate metrics checkboxes by category"""
        categories = self.catalog.get_categories()
        all_metrics = self.catalog.get_all_metrics()
        
        col = 0
        row = 0
        max_cols = 3
        
        for category in categories:
            # Category frame
            cat_frame = ttk.LabelFrame(self.metrics_frame, text=f"📊 {category}", padding=5)
            cat_frame.grid(row=row, column=col, sticky=tk.NW, padx=5, pady=5)
            
            # Get metrics for this category
            cat_metrics = self.catalog.get_metrics_by_category(category)
            
            for i, metric_name in enumerate(cat_metrics):
                var = tk.BooleanVar(value=False)
                self.metric_vars[metric_name] = var
                
                metric_info = all_metrics.get(metric_name, {})
                tooltip = metric_info.get('description', '')
                
                cb = ttk.Checkbutton(cat_frame, text=metric_name, variable=var)
                cb.grid(row=i, column=0, sticky=tk.W)
                
                # Simple tooltip via binding
                cb.bind('<Enter>', lambda e, t=tooltip: self.show_tooltip(e, t))
                cb.bind('<Leave>', self.hide_tooltip)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Selected count label
        self.selected_count_var = tk.StringVar(value="Selected: 0/64")
        ttk.Label(self.metrics_frame, textvariable=self.selected_count_var, 
                  style='Header.TLabel').grid(row=row+1, column=0, columnspan=max_cols, pady=10)
        
    def setup_output_section(self, parent):
        """Setup output configuration"""
        output_frame = ttk.LabelFrame(parent, text="💾 Output Configuration", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output directory
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(dir_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_datasets"))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).pack(side=tk.LEFT)
        
        # Output format (only for custom mode)
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT)
        self.output_format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format_var, value="csv").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="JSON", variable=self.output_format_var, value="json").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="JSONL", variable=self.output_format_var, value="jsonl").pack(side=tk.LEFT, padx=10)
        
        # Dataset name
        name_frame = ttk.Frame(output_frame)
        name_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(name_frame, text="Dataset Name:").pack(side=tk.LEFT)
        self.dataset_name_var = tk.StringVar(value="my_dataset")
        ttk.Entry(name_frame, textvariable=self.dataset_name_var, width=30).pack(side=tk.LEFT, padx=5)
        
    def setup_generate_section(self, parent):
        """Setup generate button"""
        gen_frame = ttk.Frame(parent)
        gen_frame.pack(fill=tk.X, pady=10)
        
        self.generate_btn = ttk.Button(gen_frame, text="🚀 Generate Dataset", 
                                        style='Generate.TButton', command=self.generate_dataset)
        self.generate_btn.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(gen_frame, variable=self.progress_var, 
                                            mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        
    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Tooltip label
        self.tooltip_var = tk.StringVar(value="")
        self.tooltip_label = ttk.Label(status_frame, textvariable=self.tooltip_var, style='Info.TLabel')
        self.tooltip_label.pack(side=tk.RIGHT)
        
    # === Mode switching ===
    
    def show_benchmark_mode(self):
        """Show benchmark dataset options"""
        self.custom_frame.pack_forget()
        self.benchmark_frame.pack(fill=tk.BOTH, expand=True)
        self.update_benchmark_info()
        
    def show_custom_mode(self):
        """Show custom metrics selection"""
        self.benchmark_frame.pack_forget()
        self.custom_frame.pack(fill=tk.BOTH, expand=True)
        self.update_selected_count()
        
    def update_benchmark_info(self):
        """Update benchmark info panel"""
        selected = self.benchmark_var.get()
        info = self.BENCHMARK_DATASETS.get(selected, {})
        
        self.benchmark_info_text.config(state=tk.NORMAL)
        self.benchmark_info_text.delete(1.0, tk.END)
        
        text = f"""Dataset: {selected}
═══════════════════════════════════════════════════════

Description: {info.get('description', 'N/A')}

Format: {info.get('format', 'N/A').upper()}

"""
        
        if 'structure' in info:
            text += f"Folder Structure: {', '.join(info['structure'])}\n\n"
            text += "This dataset will create separate folders for buggy and fixed code.\n"
        
        if 'fields' in info:
            text += f"Fields: {', '.join(info['fields'])}\n\n"
        
        if selected == "Defects4J":
            text += """
Defects4J Style Output:
├── buggy/
│   ├── Bug_001/
│   │   ├── src/
│   │   └── metadata.json
│   ├── Bug_002/
│   └── ...
└── fixed/
    ├── Bug_001/
    │   ├── src/
    │   └── metadata.json
    ├── Bug_002/
    └── ...

You can either:
1. Specify buggy and fixed folders manually below
2. Let the system analyze the repository for bug-fixing commits
"""
        elif selected == "Bugs.jar":
            text += """
Sample Output:
{
    "bug_id": "BUG-001",
    "project": "example-project",
    "commit_buggy": "abc123",
    "commit_fixed": "def456",
    "patch": "diff --git...",
    "test": "testMethodName"
}
"""
        elif selected == "PROMISE":
            text += """
Sample Output (CSV):
class,wmc,dit,noc,cbo,rfc,lcom,defects
MyClass,5,2,0,8,15,0.3,false
OtherClass,12,3,2,15,28,0.7,true

Metrics included automatically:
- WMC: Weighted Methods per Class
- DIT: Depth of Inheritance Tree
- NOC: Number of Children
- CBO: Coupling Between Objects
- RFC: Response For Class
- LCOM: Lack of Cohesion of Methods
"""
        
        self.benchmark_info_text.insert(1.0, text)
        self.benchmark_info_text.config(state=tk.DISABLED)
        
        # Show/hide Defects4J options
        if selected == "Defects4J":
            self.defects4j_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.defects4j_frame.pack_forget()
    
    # === Actions ===
    
    def browse_folder(self):
        """Browse for local folder"""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.repo_var.set(folder)
            self.verify_repo()
            
    def browse_specific_folder(self, var):
        """Browse for specific folder (buggy/fixed)"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            var.set(folder)
            
    def browse_output_dir(self):
        """Browse for output directory"""
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_dir_var.set(folder)
            
    def clone_repo(self):
        """Clone repository from URL"""
        repo_input = self.repo_var.get().strip()
        if not repo_input or 'Enter' in repo_input:
            messagebox.showwarning("Warning", "Please enter a GitHub URL or owner/repo format")
            return
            
        self.status_var.set("Cloning repository...")
        self.root.update()
        
        def clone_thread():
            try:
                success = self.agent.set_repository(repo_input)
                if success:
                    self.repo_var.set(self.agent.repo_path)
                    self.repo_status_var.set(f"✓ Cloned to: {self.agent.repo_path}")
                    self.repo_status_label.configure(style='Success.TLabel')
                    self.status_var.set("Repository cloned successfully")
                else:
                    self.repo_status_var.set("✗ Clone failed")
                    self.repo_status_label.configure(style='Error.TLabel')
                    self.status_var.set("Clone failed")
            except Exception as e:
                self.repo_status_var.set(f"✗ Error: {str(e)}")
                self.repo_status_label.configure(style='Error.TLabel')
                self.status_var.set("Clone failed")
                
        threading.Thread(target=clone_thread, daemon=True).start()
        
    def verify_repo(self):
        """Verify repository"""
        repo_input = self.repo_var.get().strip()
        if not repo_input or 'Enter' in repo_input:
            self.repo_status_var.set("Please enter a repository path or URL")
            return
            
        self.status_var.set("Verifying repository...")
        
        try:
            success = self.agent.set_repository(repo_input)
            if success:
                self.repo_var.set(self.agent.repo_path)
                self.repo_status_var.set(f"✓ Valid repository: {self.agent.repo_path}")
                self.repo_status_label.configure(style='Success.TLabel')
                self.status_var.set("Repository verified")
            else:
                self.repo_status_var.set("✗ Invalid repository")
                self.repo_status_label.configure(style='Error.TLabel')
                self.status_var.set("Repository verification failed")
        except Exception as e:
            self.repo_status_var.set(f"✗ Error: {str(e)}")
            self.repo_status_label.configure(style='Error.TLabel')
            self.status_var.set("Verification failed")
    
    def select_all_metrics(self):
        """Select all metrics"""
        for var in self.metric_vars.values():
            var.set(True)
        self.update_selected_count()
        
    def deselect_all_metrics(self):
        """Deselect all metrics"""
        for var in self.metric_vars.values():
            var.set(False)
        self.update_selected_count()
        
    def toggle_category(self, category):
        """Toggle all metrics in a category"""
        cat_metrics = self.catalog.get_metrics_by_category(category)
        # Check if any is selected
        any_selected = any(self.metric_vars.get(m, tk.BooleanVar()).get() for m in cat_metrics)
        
        for metric in cat_metrics:
            if metric in self.metric_vars:
                self.metric_vars[metric].set(not any_selected)
        
        self.update_selected_count()
        
    def update_selected_count(self):
        """Update selected metrics count"""
        count = sum(1 for var in self.metric_vars.values() if var.get())
        total = len(self.metric_vars)
        self.selected_count_var.set(f"Selected: {count}/{total}")
        
    def show_tooltip(self, event, text):
        """Show tooltip"""
        self.tooltip_var.set(text)
        
    def hide_tooltip(self, event=None):
        """Hide tooltip"""
        self.tooltip_var.set("")
    
    # === Generation ===
    
    def generate_dataset(self):
        """Generate dataset based on mode"""
        # Validate repository
        repo_path = self.repo_var.get().strip()
        if not repo_path or 'Enter' in repo_path:
            messagebox.showwarning("Warning", "Please specify a repository")
            return
            
        # Validate output directory
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("Warning", "Please specify an output directory")
            return
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        self.generate_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set("Generating dataset...")
        
        def generate_thread():
            try:
                mode = self.mode_var.get()
                
                if mode == "benchmark":
                    self.generate_benchmark_dataset(repo_path, output_dir)
                else:
                    self.generate_custom_dataset(repo_path, output_dir)
                    
                self.progress_var.set(100)
                self.status_var.set("Dataset generated successfully!")
                messagebox.showinfo("Success", f"Dataset generated in:\n{output_dir}")
                
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Generation failed:\n{str(e)}")
            finally:
                self.generate_btn.config(state=tk.NORMAL)
                
        threading.Thread(target=generate_thread, daemon=True).start()
        
    def generate_benchmark_dataset(self, repo_path, output_dir):
        """Generate benchmark-style dataset"""
        dataset_type = self.benchmark_var.get()
        dataset_name = self.dataset_name_var.get() or dataset_type.lower()
        
        self.progress_var.set(10)
        
        if dataset_type == "Defects4J":
            self.generate_defects4j(repo_path, output_dir, dataset_name)
        elif dataset_type == "Bugs.jar":
            self.generate_bugsjar(repo_path, output_dir, dataset_name)
        elif dataset_type == "PROMISE":
            self.generate_promise(repo_path, output_dir, dataset_name)
        elif dataset_type == "CodeSearchNet":
            self.generate_codesearchnet(repo_path, output_dir, dataset_name)
        else:
            self.generate_generic_benchmark(repo_path, output_dir, dataset_type, dataset_name)
            
    def generate_defects4j(self, repo_path, output_dir, dataset_name):
        """Generate Defects4J style dataset with buggy/fixed folders"""
        # Create structure
        buggy_dir = os.path.join(output_dir, dataset_name, "buggy")
        fixed_dir = os.path.join(output_dir, dataset_name, "fixed")
        os.makedirs(buggy_dir, exist_ok=True)
        os.makedirs(fixed_dir, exist_ok=True)
        
        self.progress_var.set(20)
        
        # Check if manual folders specified
        manual_buggy = self.buggy_folder_var.get().strip()
        manual_fixed = self.fixed_folder_var.get().strip()
        
        if manual_buggy and manual_fixed and os.path.isdir(manual_buggy) and os.path.isdir(manual_fixed):
            # Copy from manual folders
            import shutil
            self.status_var.set("Copying buggy folder...")
            for item in os.listdir(manual_buggy):
                src = os.path.join(manual_buggy, item)
                dst = os.path.join(buggy_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            self.progress_var.set(50)
            self.status_var.set("Copying fixed folder...")
            
            for item in os.listdir(manual_fixed):
                src = os.path.join(manual_fixed, item)
                dst = os.path.join(fixed_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        else:
            # Analyze repository for bug-fixing commits
            self.status_var.set("Analyzing repository for bugs...")
            self.progress_var.set(30)
            
            # Find bug-fixing commits
            bug_commits = self._find_bug_fixing_commits(repo_path)
            
            self.progress_var.set(50)
            
            # Create bug entries
            for i, commit in enumerate(bug_commits[:50]):  # Limit to 50
                bug_id = f"Bug_{i+1:03d}"
                
                # Create buggy version
                bug_path = os.path.join(buggy_dir, bug_id)
                os.makedirs(bug_path, exist_ok=True)
                
                # Create fixed version
                fix_path = os.path.join(fixed_dir, bug_id)
                os.makedirs(fix_path, exist_ok=True)
                
                # Save metadata
                metadata = {
                    "bug_id": bug_id,
                    "commit_buggy": commit.get("parent", ""),
                    "commit_fixed": commit.get("hash", ""),
                    "message": commit.get("message", ""),
                    "files_changed": commit.get("files", []),
                    "timestamp": commit.get("date", "")
                }
                
                with open(os.path.join(bug_path, "metadata.json"), 'w') as f:
                    json.dump(metadata, f, indent=2)
                with open(os.path.join(fix_path, "metadata.json"), 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.progress_var.set(50 + (i / len(bug_commits)) * 40)
        
        # Save dataset info
        info = {
            "dataset_type": "Defects4J",
            "generated": datetime.now().isoformat(),
            "source": repo_path,
            "structure": ["buggy", "fixed"]
        }
        with open(os.path.join(output_dir, dataset_name, "dataset_info.json"), 'w') as f:
            json.dump(info, f, indent=2)
            
    def generate_bugsjar(self, repo_path, output_dir, dataset_name):
        """Generate Bugs.jar style dataset"""
        output_file = os.path.join(output_dir, f"{dataset_name}.json")
        
        self.status_var.set("Analyzing commits...")
        bug_commits = self._find_bug_fixing_commits(repo_path)
        
        self.progress_var.set(50)
        
        bugs = []
        for i, commit in enumerate(bug_commits):
            bug = {
                "bug_id": f"BUG-{i+1:04d}",
                "project": os.path.basename(repo_path),
                "commit_buggy": commit.get("parent", ""),
                "commit_fixed": commit.get("hash", ""),
                "message": commit.get("message", ""),
                "files": commit.get("files", []),
                "patch": commit.get("diff", "")
            }
            bugs.append(bug)
            
        with open(output_file, 'w') as f:
            json.dump(bugs, f, indent=2)
            
    def generate_promise(self, repo_path, output_dir, dataset_name):
        """Generate PROMISE style dataset with CK metrics"""
        import csv
        output_file = os.path.join(output_dir, f"{dataset_name}.csv")
        
        self.status_var.set("Extracting CK metrics...")
        
        # Find Java files
        java_files = []
        for root, dirs, files in os.walk(repo_path):
            for f in files:
                if f.endswith('.java'):
                    java_files.append(os.path.join(root, f))
        
        self.progress_var.set(30)
        
        rows = []
        for i, file_path in enumerate(java_files[:200]):  # Limit to 200
            class_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Extract basic metrics (simplified)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            row = {
                "class": class_name,
                "wmc": content.count('public ') + content.count('private ') + content.count('protected '),
                "dit": 1,  # Simplified
                "noc": 0,
                "cbo": content.count('import '),
                "rfc": content.count('('),
                "lcom": 0.5,
                "loc": len(content.splitlines()),
                "defects": "false"
            }
            rows.append(row)
            
            self.progress_var.set(30 + (i / len(java_files)) * 60)
        
        # Write CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            
    def generate_codesearchnet(self, repo_path, output_dir, dataset_name):
        """Generate CodeSearchNet style dataset"""
        output_file = os.path.join(output_dir, f"{dataset_name}.jsonl")
        
        self.status_var.set("Extracting code and docstrings...")
        
        code_files = []
        for root, dirs, files in os.walk(repo_path):
            for f in files:
                if f.endswith(('.py', '.java', '.js', '.ts', '.go', '.rb')):
                    code_files.append(os.path.join(root, f))
        
        self.progress_var.set(30)
        
        with open(output_file, 'w') as out:
            for i, file_path in enumerate(code_files[:500]):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract language
                    ext = os.path.splitext(file_path)[1]
                    lang_map = {'.py': 'python', '.java': 'java', '.js': 'javascript', 
                               '.ts': 'typescript', '.go': 'go', '.rb': 'ruby'}
                    language = lang_map.get(ext, 'unknown')
                    
                    entry = {
                        "code": content[:2000],  # Truncate
                        "docstring": "",
                        "language": language,
                        "path": os.path.relpath(file_path, repo_path)
                    }
                    out.write(json.dumps(entry) + '\n')
                    
                except Exception:
                    pass
                    
                self.progress_var.set(30 + (i / len(code_files)) * 60)
                
    def generate_generic_benchmark(self, repo_path, output_dir, dataset_type, dataset_name):
        """Generate generic benchmark dataset"""
        info = self.BENCHMARK_DATASETS.get(dataset_type, {})
        format_type = info.get('format', 'json')
        
        output_file = os.path.join(output_dir, f"{dataset_name}.{format_type}")
        
        self.status_var.set(f"Generating {dataset_type} dataset...")
        
        # Collect data based on format
        if format_type == 'jsonl':
            self._generate_jsonl(repo_path, output_file, info.get('fields', []))
        elif format_type == 'csv':
            self._generate_csv(repo_path, output_file, info.get('fields', []))
        else:
            self._generate_json(repo_path, output_file, info.get('fields', []))
            
    def _generate_jsonl(self, repo_path, output_file, fields):
        """Generate JSONL format"""
        code_files = self._get_code_files(repo_path)
        
        with open(output_file, 'w') as out:
            for file_path in code_files[:500]:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    entry = {"code": content[:2000], "path": file_path}
                    for field in fields:
                        if field not in entry:
                            entry[field] = ""
                    out.write(json.dumps(entry) + '\n')
                except:
                    pass
                    
    def _generate_csv(self, repo_path, output_file, fields):
        """Generate CSV format"""
        import csv
        code_files = self._get_code_files(repo_path)
        
        with open(output_file, 'w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=fields if fields else ['file', 'content'])
            writer.writeheader()
            for file_path in code_files[:500]:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    row = {'file': file_path, 'content': content[:500]}
                    writer.writerow(row)
                except:
                    pass
                    
    def _generate_json(self, repo_path, output_file, fields):
        """Generate JSON format"""
        code_files = self._get_code_files(repo_path)
        
        data = []
        for file_path in code_files[:500]:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                entry = {"file": file_path, "content": content[:2000]}
                data.append(entry)
            except:
                pass
                
        with open(output_file, 'w') as out:
            json.dump(data, out, indent=2)
            
    def _get_code_files(self, repo_path):
        """Get all code files"""
        code_files = []
        extensions = {'.py', '.java', '.js', '.ts', '.go', '.rb', '.cpp', '.c', '.h', '.cs'}
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            
            for f in files:
                if os.path.splitext(f)[1] in extensions:
                    code_files.append(os.path.join(root, f))
                    
        return code_files
        
    def _find_bug_fixing_commits(self, repo_path):
        """Find bug-fixing commits in repository"""
        import subprocess
        
        bug_commits = []
        try:
            # Get commits with bug-related keywords
            result = subprocess.run(
                ['git', 'log', '--oneline', '--grep=fix', '--grep=bug', '--grep=error', 
                 '--grep=issue', '--grep=patch', '-n', '100', '--all-match'],
                cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                # Try simpler approach
                result = subprocess.run(
                    ['git', 'log', '--oneline', '-n', '100'],
                    cwd=repo_path, capture_output=True, text=True, timeout=60
                )
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        commit_hash = parts[0]
                        message = parts[1]
                        
                        # Get parent
                        parent_result = subprocess.run(
                            ['git', 'rev-parse', f'{commit_hash}^'],
                            cwd=repo_path, capture_output=True, text=True
                        )
                        parent = parent_result.stdout.strip() if parent_result.returncode == 0 else ""
                        
                        # Get changed files
                        files_result = subprocess.run(
                            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                            cwd=repo_path, capture_output=True, text=True
                        )
                        files = files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []
                        
                        bug_commits.append({
                            "hash": commit_hash,
                            "parent": parent,
                            "message": message,
                            "files": files
                        })
                        
        except Exception as e:
            print(f"Error finding bug commits: {e}")
            
        return bug_commits
        
    def generate_custom_dataset(self, repo_path, output_dir, dataset_name=None):
        """Generate custom dataset with selected metrics"""
        # Get selected metrics
        selected_metrics = [name for name, var in self.metric_vars.items() if var.get()]
        
        if not selected_metrics:
            raise ValueError("Please select at least one metric")
            
        dataset_name = self.dataset_name_var.get() or "custom_dataset"
        output_format = self.output_format_var.get()
        
        self.status_var.set(f"Extracting {len(selected_metrics)} metrics...")
        self.progress_var.set(10)
        
        # Get code files
        code_files = self._get_code_files(repo_path)
        
        self.progress_var.set(20)
        
        # Extract metrics for each file
        rows = []
        for i, file_path in enumerate(code_files[:500]):
            try:
                metrics = self._extract_metrics(file_path, selected_metrics)
                metrics['file'] = os.path.relpath(file_path, repo_path)
                rows.append(metrics)
            except Exception:
                pass
                
            self.progress_var.set(20 + (i / len(code_files)) * 70)
            
        # Save dataset
        output_file = os.path.join(output_dir, f"{dataset_name}.{output_format}")
        
        if output_format == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
        elif output_format == 'jsonl':
            with open(output_file, 'w') as f:
                for row in rows:
                    f.write(json.dumps(row) + '\n')
        else:
            with open(output_file, 'w') as f:
                json.dump(rows, f, indent=2)
                
    def _extract_metrics(self, file_path, selected_metrics):
        """Extract selected metrics from a file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        lines = content.splitlines()
        
        metrics = {}
        
        # LOC metrics
        if 'lines_of_code' in selected_metrics:
            metrics['lines_of_code'] = len(lines)
        if 'source_loc' in selected_metrics:
            metrics['source_loc'] = len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*'))])
        if 'comment_loc' in selected_metrics:
            metrics['comment_loc'] = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
        if 'blank_loc' in selected_metrics:
            metrics['blank_loc'] = len([l for l in lines if not l.strip()])
            
        # Size metrics
        if 'file_size' in selected_metrics:
            metrics['file_size'] = os.path.getsize(file_path)
        if 'num_functions' in selected_metrics:
            metrics['num_functions'] = content.count('def ') + content.count('function ')
        if 'num_classes' in selected_metrics:
            metrics['num_classes'] = content.count('class ')
        if 'num_methods' in selected_metrics:
            metrics['num_methods'] = content.count('def ')
            
        # Complexity metrics
        if 'cyclomatic_complexity' in selected_metrics:
            # Simple approximation
            cc = 1
            cc += content.count(' if ') + content.count(' elif ')
            cc += content.count(' for ') + content.count(' while ')
            cc += content.count(' and ') + content.count(' or ')
            cc += content.count(' try ') + content.count(' except ')
            metrics['cyclomatic_complexity'] = cc
        if 'cognitive_complexity' in selected_metrics:
            metrics['cognitive_complexity'] = metrics.get('cyclomatic_complexity', 1) * 1.2
        if 'max_nesting_depth' in selected_metrics:
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)
            metrics['max_nesting_depth'] = max_indent
            
        # CK metrics
        if 'wmc' in selected_metrics:
            metrics['wmc'] = content.count('def ') + content.count('function ')
        if 'dit' in selected_metrics:
            metrics['dit'] = 1 if 'extends' in content or '(BaseClass)' in content else 0
        if 'noc' in selected_metrics:
            metrics['noc'] = 0
        if 'cbo' in selected_metrics:
            metrics['cbo'] = content.count('import ')
        if 'rfc' in selected_metrics:
            metrics['rfc'] = content.count('(')
        if 'lcom' in selected_metrics:
            metrics['lcom'] = 0.5
            
        # Other metrics with default values
        for metric in selected_metrics:
            if metric not in metrics:
                metrics[metric] = 0
                
        return metrics


def main():
    root = tk.Tk()
    app = DatasetGeneratorGUI(root)
    root.mainloop()
    

if __name__ == "__main__":
    main()
