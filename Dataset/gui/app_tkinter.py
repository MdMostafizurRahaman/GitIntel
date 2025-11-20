"""
Desktop GUI Application using tkinter (built-in Python)
Interactive dataset management interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
logger = logging.getLogger(__name__)

from extractors.factory import create_extractor, SUPPORTED_DATASETS
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner, DuplicateRemover
from labelers.labeler import BugSeverityLabeler, CodeComplexityLabeler, FeatureLabelClassifier
from agentic_dataset_maker import AgenticDatasetMaker

class DatasetManagerGUI:
    """Main GUI Application using tkinter"""

    def __init__(self, root):
        self.root = root
        self.root.title("Dataset Management System")
        self.root.geometry("1000x700")

        self.current_data = []
        self.current_stats = {}

        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets"""

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.extract_frame = ttk.Frame(self.notebook)
        self.agentic_frame = ttk.Frame(self.notebook)
        self.view_frame = ttk.Frame(self.notebook)
        self.export_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.extract_frame, text='Download Sources')
        self.notebook.add(self.agentic_frame, text='Create Dataset')
        self.notebook.add(self.view_frame, text='View Data')
        self.notebook.add(self.export_frame, text='Export')

        # Create tab contents
        self.create_extract_tab()
        self.create_agentic_tab()
        self.create_view_tab()
        self.create_export_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_extract_tab(self):
        """Create extraction tab"""
        frame = self.extract_frame

        # Title
        ttk.Label(frame, text="Download/Clone Dataset Sources", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=10)

        # Description
        desc_text = "Download files or clone Git repositories from URLs.\nFor local paths (already downloaded), output folder is optional."
        ttk.Label(frame, text=desc_text, wraplength=400).grid(row=1, column=0, columnspan=3, pady=5)

        # Source type selection
        ttk.Label(frame, text="Source Type:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.source_type_var = tk.StringVar(value="url")
        ttk.Radiobutton(frame, text="URL (Download/Clone)", variable=self.source_type_var, value="url").grid(row=2, column=1, sticky='w', padx=5, pady=5)
        ttk.Radiobutton(frame, text="Local Path (Already Downloaded)", variable=self.source_type_var, value="local").grid(row=2, column=2, sticky='w', padx=5, pady=5)

        # Source path
        ttk.Label(frame, text="Source:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.source_entry = ttk.Entry(frame)
        self.source_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=self.browse_source).grid(row=3, column=2, padx=5, pady=5)

        # Output path (only for URLs)
        ttk.Label(frame, text="Output Folder:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.output_entry = ttk.Entry(frame)
        self.output_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Choose Folder", command=self.browse_output_folder).grid(row=4, column=2, padx=5, pady=5)

        # Note about output folder
        self.output_note_label = ttk.Label(frame, text="Note: Output folder required for URLs, optional for local paths", foreground='blue')
        self.output_note_label.grid(row=5, column=0, columnspan=3, pady=2)

        # Download/Clone button
        ttk.Button(frame, text="Download/Clone", command=self.on_extract).grid(row=6, column=0, columnspan=3, pady=10)

        # Progress
        self.extract_progress = ttk.Progressbar(frame, mode='determinate')
        self.extract_progress.grid(row=7, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Log
        ttk.Label(frame, text="Log:").grid(row=8, column=0, sticky='w', padx=5, pady=5)
        self.extract_log = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.extract_log.grid(row=9, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(9, weight=1)

        # Bind source type change
        self.source_type_var.trace('w', self.on_source_type_change)

    def create_view_tab(self):
        """Create data view tab"""
        frame = self.view_frame

        # Load button
        ttk.Button(frame, text="Load Data File", command=self.on_load_data).grid(row=0, column=0, pady=10)

        # Stats
        ttk.Label(frame, text="Statistics:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.stats_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        self.stats_text.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)

        # Table (simplified - just text display)
        ttk.Label(frame, text="Data Preview (first 5 records):").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.data_preview = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.data_preview.grid(row=4, column=0, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(4, weight=1)

    def create_export_tab(self):
        """Create export tab"""
        frame = self.export_frame

        # Input file
        ttk.Label(frame, text="Data File:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.export_input = ttk.Entry(frame)
        self.export_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=lambda: self.browse_file(self.export_input)).grid(row=0, column=2, padx=5, pady=5)

        # Format selection
        ttk.Label(frame, text="Export Format:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.format_combo = ttk.Combobox(frame, values=["CSV", "JSON", "JSONL"], state='readonly')
        self.format_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        # Output path
        ttk.Label(frame, text="Output Folder:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.export_output = ttk.Entry(frame)
        self.export_output.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Choose Folder", command=self.browse_export_folder).grid(row=2, column=2, padx=5, pady=5)

        # Export button
        ttk.Button(frame, text="Export", command=self.on_export).grid(row=3, column=0, columnspan=3, pady=10)

        # Log
        ttk.Label(frame, text="Log:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.export_log = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.export_log.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

    def create_agentic_tab(self):
        """Create agentic dataset maker tab"""
        frame = self.agentic_frame

        # Create two main sections: input and results
        input_frame = ttk.LabelFrame(frame, text="Dataset Creation", padding=10)
        input_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        results_frame = ttk.LabelFrame(frame, text="Results & Files", padding=10)
        results_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Title
        ttk.Label(input_frame, text="Agentic Dataset Maker", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)

        # Description
        desc_text = "Create intelligent datasets using natural language queries.\nThe AI agent will understand your request and create the appropriate dataset."
        ttk.Label(input_frame, text=desc_text, wraplength=500).grid(row=1, column=0, columnspan=3, pady=5)

        # Query input
        ttk.Label(input_frame, text="Natural Language Query:").grid(row=2, column=0, sticky='w', pady=2)
        self.query_text = scrolledtext.ScrolledText(input_frame, height=3, wrap=tk.WORD)
        self.query_text.grid(row=3, column=0, columnspan=3, sticky='ew', pady=2)

        # Example queries
        ttk.Label(input_frame, text="Quick Examples:").grid(row=4, column=0, sticky='w', pady=2)
        examples = [
            "Create a dataset of Java bug fixes from Defects4J",
            "Generate a dataset with code complexity metrics from Promise dataset",
            "Extract bug severity labels from Bugs.jar dataset",
            "Create a multi-label dataset combining defects4j and promise data"
        ]
        self.example_combo = ttk.Combobox(input_frame, values=examples, state='readonly', width=50)
        self.example_combo.grid(row=4, column=1, columnspan=2, sticky='ew', pady=2)
        self.example_combo.bind('<<ComboboxSelected>>', self.on_example_selected)

        # Source path (optional)
        ttk.Label(input_frame, text="Source Path (optional):").grid(row=5, column=0, sticky='w', pady=2)
        self.source_path_entry = ttk.Entry(input_frame, width=40)
        self.source_path_entry.grid(row=5, column=1, sticky='ew', pady=2)
        ttk.Button(input_frame, text="Browse", command=self.browse_source_path).grid(row=5, column=2, pady=2)

        # Mode and output in one row
        ttk.Label(input_frame, text="Mode:").grid(row=6, column=0, sticky='w', pady=2)
        self.mode_var = tk.StringVar(value="interactive")
        ttk.Radiobutton(input_frame, text="Interactive", variable=self.mode_var, value="interactive").grid(row=6, column=1, sticky='w', pady=2)
        ttk.Radiobutton(input_frame, text="Direct API", variable=self.mode_var, value="direct").grid(row=6, column=2, sticky='w', pady=2)

        # Output directory
        ttk.Label(input_frame, text="Output Folder:").grid(row=7, column=0, sticky='w', pady=2)
        self.agentic_output = ttk.Entry(input_frame, width=40)
        self.agentic_output.grid(row=7, column=1, sticky='ew', pady=2)
        ttk.Button(input_frame, text="Browse", command=self.browse_agentic_output).grid(row=7, column=2, pady=2)

        # Create button
        ttk.Button(input_frame, text="🚀 Create Dataset", command=self.on_create_agentic).grid(row=8, column=0, columnspan=3, pady=10)

        # Progress
        self.agentic_progress = ttk.Progressbar(input_frame, mode='determinate')
        self.agentic_progress.grid(row=9, column=0, columnspan=3, sticky='ew', pady=2)

        # Configure input frame
        input_frame.columnconfigure(1, weight=1)

        # Results section
        # Status and summary
        status_frame = ttk.Frame(results_frame)
        status_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=2)

        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky='w')
        self.agentic_status = ttk.Label(status_frame, text="Ready", foreground='blue')
        self.agentic_status.grid(row=0, column=1, sticky='w', padx=(5,0))

        ttk.Label(status_frame, text="Records:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.records_label = ttk.Label(status_frame, text="0")
        self.records_label.grid(row=0, column=3, sticky='w', padx=(5,0))

        ttk.Label(status_frame, text="Files:").grid(row=0, column=4, sticky='w', padx=(20,0))
        self.files_label = ttk.Label(status_frame, text="0")
        self.files_label.grid(row=0, column=5, sticky='w', padx=(5,0))

        # Files list
        ttk.Label(results_frame, text="Generated Files:").grid(row=1, column=0, sticky='w', pady=2)
        ttk.Button(results_frame, text="📂 Open Output Folder", command=self.open_output_folder).grid(row=1, column=1, sticky='e', pady=2)

        # File listbox with scrollbar
        list_frame = ttk.Frame(results_frame)
        list_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=2)

        self.file_listbox = tk.Listbox(list_frame, height=8, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        self.file_listbox.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # File actions
        action_frame = ttk.Frame(results_frame)
        action_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)

        ttk.Button(action_frame, text="👁️ View File", command=self.view_selected_file).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="📄 Open in Editor", command=self.open_file_in_editor).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="🔄 Refresh List", command=self.refresh_file_list).grid(row=0, column=2, padx=2)

        # Log
        ttk.Label(results_frame, text="Agent Log:").grid(row=4, column=0, sticky='w', pady=2)
        self.agentic_log = scrolledtext.ScrolledText(results_frame, height=8, wrap=tk.WORD)
        self.agentic_log.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=2)

        # Configure results frame
        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=0)
        results_frame.rowconfigure(2, weight=1)
        results_frame.rowconfigure(5, weight=1)

        # Configure main frame
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        # Initialize variables
        self.agentic_files = []
        self.output_directory = ""
        
        # Clear source path field on init (avoid using old invalid paths)
        self.source_path_entry.delete(0, tk.END)

    # Event handlers

    def on_source_type_change(self, *args):
        """Handle source type change"""
        source_type = self.source_type_var.get()
        if source_type == "local":
            self.output_note_label.config(text="Note: Output folder optional for local paths (leave empty to use source directly)")
            # Clear output entry for local paths
            self.output_entry.delete(0, tk.END)
        else:  # url
            self.output_note_label.config(text="Note: Output folder required for URLs")

    def browse_source(self):
        """Browse for source directory"""
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, path)

    def browse_output(self):
        """Browse for output file"""
        path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def browse_output_folder(self):
        """Browse for output folder"""
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def browse_export_folder(self):
        """Browse for export output folder"""
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.export_output.delete(0, tk.END)
            self.export_output.insert(0, path)

    def on_extract(self):
        """Handle cloning/downloading"""
        source = self.source_entry.get()
        output_folder = self.output_entry.get()
        source_type = self.source_type_var.get()

        if not source:
            messagebox.showwarning("Error", "Please enter a source path or URL")
            return

        # Validation based on source type
        if source_type == "url":
            from urllib.parse import urlparse
            parsed = urlparse(source)
            is_url = parsed.scheme and parsed.netloc
            if not is_url and not ('github.com' in source or 'gitlab.com' in source or source.endswith('.git')):
                messagebox.showwarning("Error", "For URL mode, please enter a valid URL or Git repository link")
                return
            if not output_folder:
                messagebox.showwarning("Error", "Please select output folder for URL downloads")
                return
        else:  # local
            if not os.path.exists(source):
                messagebox.showwarning("Error", "Local path does not exist")
                return
            # For local paths, output folder is optional

        try:
            self.extract_log.delete(1.0, tk.END)
            self.extract_log.insert(tk.END, f"Processing {source_type} source: {source}\n")
            self.extract_progress['value'] = 10
            self.root.update()

            if source_type == "url":
                self.extract_log.insert(tk.END, "Downloading/cloning from URL...\n")
                self.extract_progress['value'] = 30
                self.root.update()

                # Create temporary directory for URL downloads
                import tempfile
                import shutil
                import subprocess
                import requests
                from pathlib import Path

                temp_dir = tempfile.mkdtemp(prefix="dataset_extract_")

                try:
                    if source.endswith('.git') or 'github.com' in source or 'gitlab.com' in source:
                        # Git repository
                        self.extract_log.insert(tk.END, f"Cloning repository: {source}\n")
                        subprocess.run(['git', 'clone', '--depth', '1', source, temp_dir],
                                     check=True, capture_output=True)
                        source_path = temp_dir
                    else:
                        # Regular URL - download file
                        self.extract_log.insert(tk.END, f"Downloading file: {source}\n")
                        response = requests.get(source)
                        response.raise_for_status()

                        # Determine filename
                        filename = source.split('/')[-1]
                        if not filename:
                            filename = 'downloaded_file'

                        file_path = Path(temp_dir) / filename
                        file_path.write_bytes(response.content)
                        source_path = str(file_path)
                except Exception as e:
                    # Clean up temp dir on error
                    if Path(temp_dir).exists():
                        shutil.rmtree(temp_dir)
                    raise e

                # Copy from temp to output folder
                self.extract_progress['value'] = 50
                self.root.update()

                if os.path.isfile(source_path):
                    # Single file
                    filename = os.path.basename(source_path)
                    output_file = os.path.join(output_folder, filename)
                    shutil.copy2(source_path, output_file)
                    final_path = output_file
                    self.extract_log.insert(tk.END, f"Copied file: {filename}\n")
                else:
                    # Directory
                    basename = os.path.basename(source_path.rstrip('/\\'))
                    output_path = os.path.join(output_folder, basename)

                    if os.path.exists(output_path):
                        shutil.rmtree(output_path)

                    shutil.copytree(source_path, output_path)
                    final_path = output_path
                    self.extract_log.insert(tk.END, f"Copied directory: {basename}\n")

                # Clean up temporary directory
                try:
                    shutil.rmtree(temp_dir)
                    self.extract_log.insert(tk.END, "✓ Cleaned up temporary files\n")
                except Exception as e:
                    self.extract_log.insert(tk.END, f"Warning: Could not clean up temp files: {e}\n")

            else:  # local path
                self.extract_log.insert(tk.END, "Using local path directly...\n")
                source_path = source
                final_path = source_path

                # If output folder is specified, copy to it
                if output_folder:
                    self.extract_progress['value'] = 50
                    self.root.update()

                    if os.path.isfile(source_path):
                        # Single file
                        filename = os.path.basename(source_path)
                        output_file = os.path.join(output_folder, filename)
                        shutil.copy2(source_path, output_file)
                        final_path = output_file
                        self.extract_log.insert(tk.END, f"Copied file to output: {filename}\n")
                    else:
                        # Directory
                        basename = os.path.basename(source_path.rstrip('/\\'))
                        output_path = os.path.join(output_folder, basename)

                        if os.path.exists(output_path):
                            shutil.rmtree(output_path)

                        shutil.copytree(source_path, output_path)
                        final_path = output_path
                        self.extract_log.insert(tk.END, f"Copied directory to output: {basename}\n")

            self.extract_progress['value'] = 100
            self.extract_log.insert(tk.END, f"✓ Operation completed successfully!\n")
            self.extract_log.insert(tk.END, f"✓ Final location: {final_path}\n")
            self.status_var.set("Download/Clone complete")

            # Show success message
            messagebox.showinfo("Success", f"Source processed successfully!\n\nLocation: {final_path}\n\nNow use 'Agentic Dataset Maker' tab to create datasets from this source.")

        except Exception as e:
            self.extract_log.insert(tk.END, f"✗ Error: {e}\n")
            messagebox.showerror("Error", str(e))

    def on_load_data(self):
        """Load and display data"""
        file_path = filedialog.askopenfilename(
            title="Load Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.current_data = data

            # Display stats
            stats = {
                "Total Records": len(data),
                "Fields": list(data[0].keys()) if data else []
            }
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, json.dumps(stats, indent=2))

            # Display preview (first 5 records)
            self.data_preview.delete(1.0, tk.END)
            for i, record in enumerate(data[:5]):
                self.data_preview.insert(tk.END, f"Record {i+1}:\n")
                for key, value in record.items():
                    # Truncate long values
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    self.data_preview.insert(tk.END, f"  {key}: {val_str}\n")
                self.data_preview.insert(tk.END, "\n")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def on_export(self):
        """Handle export"""
        if not self.current_data:
            messagebox.showwarning("Error", "No data to export. Load data first.")
            return

        input_file = self.export_input.get()
        output_folder = self.export_output.get()
        format_type = self.format_combo.get()

        if not output_folder or not format_type:
            messagebox.showwarning("Error", "Please specify output folder and format")
            return

        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if format_type == "JSON":
            output_file = os.path.join(output_folder, f"{base_name}_export.json")
        elif format_type == "CSV":
            output_file = os.path.join(output_folder, f"{base_name}_export.csv")
        elif format_type == "JSONL":
            output_file = os.path.join(output_folder, f"{base_name}_export.jsonl")

        try:
            self.export_log.delete(1.0, tk.END)
            self.export_log.insert(tk.END, f"Exporting to {format_type}...\n")

            if format_type == "JSON":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, indent=2, default=str, ensure_ascii=False)

            elif format_type == "CSV":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if self.current_data:
                        writer = csv.DictWriter(f, fieldnames=self.current_data[0].keys())
                        writer.writeheader()
                        writer.writerows(self.current_data)

            elif format_type == "JSONL":
                with open(output_file, 'w', encoding='utf-8') as f:
                    for record in self.current_data:
                        json.dump(record, f, default=str, ensure_ascii=False)
                        f.write('\n')

            self.export_log.insert(tk.END, f"✓ Exported {len(self.current_data)} records to {output_file}\n")
            messagebox.showinfo("Success", f"Data exported successfully!\n\nFile: {output_file}\nRecords: {len(self.current_data)}")

        except Exception as e:
            self.export_log.insert(tk.END, f"✗ Error: {e}\n")
            messagebox.showerror("Error", str(e))

    def on_example_selected(self, event=None):
        """Fill query with selected example"""
        example = self.example_combo.get()
        if example:
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END, example)
            # Clear source path when selecting example (since examples are for synthetic generation)
            self.source_path_entry.delete(0, tk.END)

    def browse_agentic_output(self):
        """Browse for agentic output directory"""
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.agentic_output.delete(0, tk.END)
            self.agentic_output.insert(0, path)

    def browse_source_path(self):
        """Browse for source path for agentic dataset maker"""
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_path_entry.delete(0, tk.END)
            self.source_path_entry.insert(0, path)

    def on_create_agentic(self):
        """Handle agentic dataset creation"""
        query = self.query_text.get(1.0, tk.END).strip()
        output_dir = self.agentic_output.get()
        source_path = self.source_path_entry.get() or None

        if not query:
            messagebox.showwarning("Error", "Please enter a natural language query")
            return

        if not output_dir:
            messagebox.showwarning("Error", "Please select output directory")
            return

        # DEBUG: Show what source path is being processed
        print(f"DEBUG: on_create_agentic called with source_path = '{source_path}'")
        
        # Validate and clean source path
        if source_path:
            try:
                print(f"DEBUG: Validating source path: {source_path}")
                # Check both existence and whether it's a valid PROMISE source
                if not os.path.exists(source_path):
                    print(f"DEBUG: Path does not exist: {source_path}")
                    self.agentic_log.delete(1.0, tk.END)
                    self.agentic_log.insert(tk.END, f"⚠️  Source path does not exist: {source_path}\n")
                    self.agentic_log.insert(tk.END, f"✓ Clearing invalid path and using synthetic data generation instead\n\n")
                    self.source_path_entry.delete(0, tk.END)  # Clear the invalid path
                    self.root.update()  # Force GUI update
                    source_path = None  # Don't use it
                elif os.path.isdir(source_path):
                    print(f"DEBUG: Path is directory, checking contents: {source_path}")
                    # Check if directory has valid PROMISE files
                    files_in_dir = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]
                    valid_promise_files = [f for f in files_in_dir if f.endswith(('.csv', '.json', '.arff'))]
                    print(f"DEBUG: Found {len(files_in_dir)} files, {len(valid_promise_files)} are PROMISE format")
                    
                    if not valid_promise_files:
                        # Directory exists but has no valid PROMISE files
                        self.agentic_log.delete(1.0, tk.END)
                        self.agentic_log.insert(tk.END, f"⚠️  Source directory has no valid PROMISE data files (.csv, .json, .arff): {source_path}\n")
                        self.agentic_log.insert(tk.END, f"   Found {len(files_in_dir)} files but none are PROMISE format\n")
                        self.agentic_log.insert(tk.END, f"✓ Clearing path and using synthetic data generation instead\n\n")
                        self.source_path_entry.delete(0, tk.END)  # Clear the invalid path
                        self.root.update()  # Force GUI update
                        source_path = None  # Don't use it
                        print(f"DEBUG: Cleared invalid source path, now source_path = {source_path}")
            except Exception as e:
                print(f"DEBUG: Exception during validation: {e}")
                self.agentic_log.delete(1.0, tk.END)
                self.agentic_log.insert(tk.END, f"⚠️  Error validating source path {source_path}: {e}\n")
                self.agentic_log.insert(tk.END, f"✓ Clearing path and using synthetic data generation instead\n\n")
                self.source_path_entry.delete(0, tk.END)  # Clear the invalid path
                source_path = None  # Don't use it

        print(f"DEBUG: After validation, source_path = '{source_path}'")

        try:
            self.agentic_log.delete(1.0, tk.END)
            self.agentic_status.config(text="Processing...", foreground='orange')
            self.records_label.config(text="0")
            self.files_label.config(text="0")
            self.file_listbox.delete(0, tk.END)
            self.agentic_files = []

            self.agentic_log.insert(tk.END, "🤖 Initializing Agentic Dataset Maker...\n")
            self.agentic_progress['value'] = 10
            self.root.update()

            # Create agent
            agent = AgenticDatasetMaker()
            self.agentic_log.insert(tk.END, "✅ Agent initialized successfully\n")
            self.agentic_progress['value'] = 20
            self.root.update()

            self.agentic_log.insert(tk.END, f"🔄 Processing query: {query[:50]}...\n")
            if source_path:
                self.agentic_log.insert(tk.END, f"📁 Using source path: {source_path}\n")
            self.agentic_progress['value'] = 30
            self.root.update()

            # Create dataset - use the validated source_path (which may be None)
            print(f"DEBUG: Calling create_dataset with source_path = '{source_path}'")
            result = agent.create_dataset(
                user_query=query, 
                interactive=False, 
                output_path=output_dir, 
                source_path=source_path
            )

            # Check if the result indicates success or failure
            if result.get('status') == 'success':
                self.agentic_progress['value'] = 100
                self.agentic_log.insert(tk.END, "🎉 Dataset creation completed!\n\n")
                self.agentic_log.insert(tk.END, f"📁 Results saved to: {result.get('output_path', 'N/A')}\n")
                self.agentic_log.insert(tk.END, f"📊 Records created: {result.get('total_records', 0)}\n")

                # Debug: Log the full result structure
                self.agentic_log.insert(tk.END, f"🔍 Debug - Result keys: {list(result.keys())}\n")
                self.agentic_log.insert(tk.END, f"🔍 Debug - Total records in result: {result.get('total_records', 'NOT_FOUND')}\n")

                # Handle files_created - if not present, create from output_path
                files_created = result.get('files_created', [])
                if not files_created and result.get('output_path'):
                    files_created = [result['output_path']]

                self.agentic_log.insert(tk.END, f"📄 Files generated: {len(files_created)}\n")

                # Update status
                self.agentic_status.config(text="Completed", foreground='green')
                self.records_label.config(text=str(result.get('total_records', 0)))
                self.files_label.config(text=str(len(files_created)))

                # Force GUI update
                self.root.update_idletasks()

                # Populate file list
                self.output_directory = result.get('output_path', output_dir)
                if self.output_directory and os.path.isfile(self.output_directory):
                    self.output_directory = os.path.dirname(self.output_directory)

                self.agentic_files = files_created
                self.refresh_file_list()

                # Show summary
                messagebox.showinfo("Success", f"Dataset created successfully!\n\nRecords: {result.get('total_records', 0)}\nFiles: {len(files_created)}\n\nCheck the Results section to view files.")
            
            else:
                # Handle failure case
                self.agentic_progress['value'] = 100
                error_message = result.get('error', 'Unknown error occurred')
                self.agentic_log.insert(tk.END, f"❌ Dataset creation failed!\n")
                self.agentic_log.insert(tk.END, f"Error: {error_message}\n")
                
                # Debug: Log the full result structure
                self.agentic_log.insert(tk.END, f"🔍 Debug - Result keys: {list(result.keys())}\n")
                self.agentic_log.insert(tk.END, f"🔍 Debug - Error details: {error_message}\n")

                # Update status
                self.agentic_status.config(text="Failed", foreground='red')
                self.records_label.config(text="0")
                self.files_label.config(text="0")
                self.file_listbox.delete(0, tk.END)
                self.agentic_files = []

                # Show error message
                messagebox.showerror("Dataset Creation Failed", f"The dataset creation failed:\n\n{error_message}")

        except Exception as e:
            self.agentic_status.config(text="Error", foreground='red')
            error_msg = f"❌ Error: {str(e)}\n"
            self.agentic_log.insert(tk.END, error_msg)
            # Show the full error details
            import traceback
            error_details = traceback.format_exc()
            self.agentic_log.insert(tk.END, f"🔍 Full error details:\n{error_details}\n")
            messagebox.showerror("Error", f"Dataset creation failed:\n\n{str(e)}")

    def open_output_folder(self):
        """Open the output folder in file explorer"""
        if not self.output_directory:
            messagebox.showwarning("Warning", "No output directory set")
            return

        try:
            import os
            os.startfile(self.output_directory)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def refresh_file_list(self):
        """Refresh the list of generated files"""
        self.file_listbox.delete(0, tk.END)

        if not self.output_directory or not self.agentic_files:
            return

        try:
            import os
            for file_path in self.agentic_files:
                if os.path.exists(file_path):
                    # Show relative path from output directory
                    rel_path = os.path.relpath(file_path, self.output_directory)
                    file_size = os.path.getsize(file_path)
                    size_str = self.format_file_size(file_size)
                    self.file_listbox.insert(tk.END, f"{rel_path} ({size_str})")
                else:
                    self.file_listbox.insert(tk.END, f"{os.path.basename(file_path)} (missing)")
        except Exception as e:
            self.file_listbox.insert(tk.END, f"Error loading files: {e}")

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def view_selected_file(self):
        """View the selected file content"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to view")
            return

        index = selection[0]
        if index >= len(self.agentic_files):
            return

        file_path = self.agentic_files[index]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create a new window to show file content
            view_window = tk.Toplevel(self.root)
            view_window.title(f"File Viewer - {os.path.basename(file_path)}")
            view_window.geometry("800x600")

            # Text widget with scrollbar
            text_frame = ttk.Frame(view_window)
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)

            text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
            text_widget.pack(fill='both', expand=True)

            # Load content
            text_widget.insert(tk.END, content)
            text_widget.config(state='disabled')  # Read-only

        except Exception as e:
            messagebox.showerror("Error", f"Could not view file: {e}")

    def open_file_in_editor(self):
        """Open the selected file in the default editor"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to open")
            return

        index = selection[0]
        if index >= len(self.agentic_files):
            return

        file_path = self.agentic_files[index]

        try:
            import os
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = DatasetManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
