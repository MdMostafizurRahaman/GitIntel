"""
Desktop GUI Application using tkinter (built-in Python)
Interactive dataset management interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import sys
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

from extractors.factory import create_extractor, SUPPORTED_DATASETS
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner, DuplicateRemover
from labelers.labeler import BugSeverityLabeler, CodeComplexityLabeler, FeatureLabelClassifier

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
        self.process_frame = ttk.Frame(self.notebook)
        self.label_frame = ttk.Frame(self.notebook)
        self.view_frame = ttk.Frame(self.notebook)
        self.export_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.extract_frame, text='Extract')
        self.notebook.add(self.process_frame, text='Process')
        self.notebook.add(self.label_frame, text='Label')
        self.notebook.add(self.view_frame, text='View Data')
        self.notebook.add(self.export_frame, text='Export')

        # Create tab contents
        self.create_extract_tab()
        self.create_process_tab()
        self.create_label_tab()
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

        # Dataset type selection
        ttk.Label(frame, text="Select Dataset Type:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.dataset_combo = ttk.Combobox(frame, values=list(SUPPORTED_DATASETS.keys()), state='readonly')
        self.dataset_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.dataset_combo.bind('<<ComboboxSelected>>', self.on_dataset_changed)

        # Description
        self.desc_label = ttk.Label(frame, text="", wraplength=400)
        self.desc_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        # Source path
        ttk.Label(frame, text="Source Path or URL:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.source_entry = ttk.Entry(frame)
        self.source_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=self.browse_source).grid(row=2, column=2, padx=5, pady=5)

        # Output path
        ttk.Label(frame, text="Output File:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.output_entry = ttk.Entry(frame)
        self.output_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Choose...", command=self.browse_output).grid(row=3, column=2, padx=5, pady=5)

        # Extract button
        ttk.Button(frame, text="Extract Data", command=self.on_extract).grid(row=4, column=0, columnspan=3, pady=10)

        # Progress
        self.extract_progress = ttk.Progressbar(frame, mode='determinate')
        self.extract_progress.grid(row=5, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Log
        ttk.Label(frame, text="Log:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.extract_log = scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD)
        self.extract_log.grid(row=7, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(7, weight=1)

    def create_process_tab(self):
        """Create processing tab"""
        frame = self.process_frame

        # Input file
        ttk.Label(frame, text="Input Data File:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.process_input = ttk.Entry(frame)
        self.process_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=lambda: self.browse_file(self.process_input)).grid(row=0, column=2, padx=5, pady=5)

        # Processing options
        ttk.Label(frame, text="Processing Options:").grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.norm_code_var = tk.BooleanVar()
        self.clean_text_var = tk.BooleanVar()
        self.remove_dup_var = tk.BooleanVar()

        ttk.Checkbutton(frame, text="Normalize Code", variable=self.norm_code_var).grid(row=2, column=0, columnspan=2, sticky='w', padx=25, pady=2)
        ttk.Checkbutton(frame, text="Clean Text", variable=self.clean_text_var).grid(row=3, column=0, columnspan=2, sticky='w', padx=25, pady=2)
        ttk.Checkbutton(frame, text="Remove Duplicates", variable=self.remove_dup_var).grid(row=4, column=0, columnspan=2, sticky='w', padx=25, pady=2)

        # Process button
        ttk.Button(frame, text="Process Data", command=self.on_process).grid(row=5, column=0, columnspan=3, pady=10)

        # Progress
        self.process_progress = ttk.Progressbar(frame, mode='determinate')
        self.process_progress.grid(row=6, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Log
        ttk.Label(frame, text="Log:").grid(row=7, column=0, sticky='w', padx=5, pady=5)
        self.process_log = scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD)
        self.process_log.grid(row=8, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(8, weight=1)

    def create_label_tab(self):
        """Create labeling tab"""
        frame = self.label_frame

        # Input file
        ttk.Label(frame, text="Input Data File:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.label_input = ttk.Entry(frame)
        self.label_input.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=lambda: self.browse_file(self.label_input)).grid(row=0, column=2, padx=5, pady=5)

        # Label type
        ttk.Label(frame, text="Label Type:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.label_type_combo = ttk.Combobox(frame, values=[
            "bug_severity",
            "code_complexity",
            "feature_type",
            "multi_label"
        ], state='readonly')
        self.label_type_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        # Label button
        ttk.Button(frame, text="Label Data", command=self.on_label).grid(row=2, column=0, columnspan=3, pady=10)

        # Progress
        self.label_progress = ttk.Progressbar(frame, mode='determinate')
        self.label_progress.grid(row=3, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Log
        ttk.Label(frame, text="Log:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.label_log = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.label_log.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

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
        ttk.Label(frame, text="Output File:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.export_output = ttk.Entry(frame)
        self.export_output.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(frame, text="Choose...", command=self.browse_output).grid(row=2, column=2, padx=5, pady=5)

        # Export button
        ttk.Button(frame, text="Export", command=self.on_export).grid(row=3, column=0, columnspan=3, pady=10)

        # Log
        ttk.Label(frame, text="Log:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.export_log = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.export_log.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

    # Event handlers

    def on_dataset_changed(self, event=None):
        """Update description when dataset changes"""
        dataset_type = self.dataset_combo.get()
        info = SUPPORTED_DATASETS.get(dataset_type, {})
        desc = f"{info.get('name', '')}: {info.get('description', '')}"
        self.desc_label.config(text=desc)

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

    def browse_file(self, entry_widget):
        """Browse for any file"""
        path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def on_extract(self):
        """Handle extraction"""
        dataset_type = self.dataset_combo.get()
        source = self.source_entry.get()
        output = self.output_entry.get()

        if not dataset_type or not source or not output:
            messagebox.showwarning("Error", "Please fill in all fields")
            return

        try:
            self.extract_log.delete(1.0, tk.END)
            self.extract_log.insert(tk.END, "Starting extraction...\n")
            self.extract_progress['value'] = 10
            self.root.update()

            extractor = create_extractor(dataset_type, source)
            self.extract_log.insert(tk.END, "Created extractor...\n")
            self.extract_progress['value'] = 30
            self.root.update()

            records = extractor.extract()
            self.extract_log.insert(tk.END, f"Extracted {len(records)} records...\n")
            self.extract_progress['value'] = 70
            self.root.update()

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, default=str, ensure_ascii=False)

            self.extract_progress['value'] = 100
            self.extract_log.insert(tk.END, f"✓ Saved to {output}\n")
            self.status_var.set(f"Extraction complete: {len(records)} records")

        except Exception as e:
            self.extract_log.insert(tk.END, f"✗ Error: {e}\n")
            messagebox.showerror("Error", str(e))

    def on_process(self):
        """Handle processing"""
        input_file = self.process_input.get()

        if not input_file:
            messagebox.showwarning("Error", "Please select input file")
            return

        try:
            self.process_log.delete(1.0, tk.END)
            self.process_log.insert(tk.END, "Loading data...\n")
            self.process_progress['value'] = 10
            self.root.update()

            with open(input_file, 'r', encoding='utf-8') as f:
                records = json.load(f)

            self.process_log.insert(tk.END, f"Loaded {len(records)} records\n")
            self.process_progress['value'] = 30
            self.root.update()

            pipeline = ProcessingPipeline()
            if self.norm_code_var.get():
                pipeline.add_processor(CodeNormalizer())
                self.process_log.insert(tk.END, "Added code normalizer\n")
            if self.clean_text_var.get():
                pipeline.add_processor(TextCleaner())
                self.process_log.insert(tk.END, "Added text cleaner\n")
            if self.remove_dup_var.get():
                pipeline.add_processor(DuplicateRemover())
                self.process_log.insert(tk.END, "Added duplicate remover\n")

            self.process_log.insert(tk.END, "Processing...\n")
            self.process_progress['value'] = 60
            self.root.update()

            processed = pipeline.process(records)

            # Save processed data
            output_file = input_file.replace('.json', '_processed.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=2, default=str, ensure_ascii=False)

            self.process_progress['value'] = 100
            self.process_log.insert(tk.END, f"✓ Processed {len(processed)} records\n")
            self.process_log.insert(tk.END, f"✓ Saved to {output_file}\n")
            self.current_data = processed
            self.status_var.set(f"Processing complete: {len(processed)} records")

        except Exception as e:
            self.process_log.insert(tk.END, f"✗ Error: {e}\n")
            messagebox.showerror("Error", str(e))

    def on_label(self):
        """Handle labeling"""
        input_file = self.label_input.get()
        label_type = self.label_type_combo.get()

        if not input_file or not label_type:
            messagebox.showwarning("Error", "Please select input file and label type")
            return

        try:
            self.label_log.delete(1.0, tk.END)
            self.label_log.insert(tk.END, f"Loading data for {label_type}...\n")
            self.label_progress['value'] = 20
            self.root.update()

            with open(input_file, 'r', encoding='utf-8') as f:
                records = json.load(f)

            self.label_log.insert(tk.END, f"Loaded {len(records)} records\n")
            self.label_progress['value'] = 40
            self.root.update()

            # Create appropriate labeler
            if label_type == "bug_severity":
                labeler = BugSeverityLabeler()
            elif label_type == "code_complexity":
                labeler = CodeComplexityLabeler()
            else:
                labeler = FeatureLabelClassifier()

            self.label_log.insert(tk.END, "Labeling...\n")
            self.label_progress['value'] = 70
            self.root.update()

            labeled = labeler.label(records)

            output_file = input_file.replace('.json', '_labeled.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(labeled, f, indent=2, default=str, ensure_ascii=False)

            self.label_progress['value'] = 100
            self.label_log.insert(tk.END, f"✓ Labeled {len(labeled)} records\n")
            self.label_log.insert(tk.END, f"✓ Saved to {output_file}\n")
            self.status_var.set("Labeling complete")

        except Exception as e:
            self.label_log.insert(tk.END, f"✗ Error: {e}\n")
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
        output_file = self.export_output.get()
        format_type = self.format_combo.get()

        if not output_file or not format_type:
            messagebox.showwarning("Error", "Please specify output file and format")
            return

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
            messagebox.showinfo("Success", "Data exported successfully")

        except Exception as e:
            self.export_log.insert(tk.END, f"✗ Error: {e}\n")
            messagebox.showerror("Error", str(e))

def main():
    """Main entry point"""
    root = tk.Tk()
    app = DatasetManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
