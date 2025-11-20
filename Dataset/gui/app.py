"""
Desktop GUI Application using PyQt5
Interactive dataset management interface
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QComboBox, QPushButton, QLabel, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar, QTextEdit, QSpinBox,
    QCheckBox, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

import logging
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from extractors.factory import create_extractor, SUPPORTED_DATASETS
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner, DuplicateRemover
from labelers.labeler import BugSeverityLabeler, CodeComplexityLabeler, FeatureLabelClassifier
from agentic_dataset_maker import AgenticDatasetMaker

class DatasetManagerGUI(QMainWindow):
    """Main GUI Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        self.current_data = []
        self.current_stats = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_agentic_tab(), "🤖 AI Agent")
        tabs.addTab(self.create_extract_tab(), "Extract")
        tabs.addTab(self.create_process_tab(), "Process")
        tabs.addTab(self.create_label_tab(), "Label")
        tabs.addTab(self.create_view_tab(), "View Data")
        tabs.addTab(self.create_export_tab(), "Export")
        
        # Set central widget
        self.setCentralWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_extract_tab(self):
        """Create extraction tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Dataset type selection
        layout.addWidget(QLabel("Select Dataset Type:"))
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems(list(SUPPORTED_DATASETS.keys()))
        layout.addWidget(self.dataset_combo)
        
        # Description
        self.desc_label = QLabel()
        self.dataset_combo.currentTextChanged.connect(self.on_dataset_changed)
        layout.addWidget(self.desc_label)
        
        # Source path
        layout.addWidget(QLabel("Source Path or URL:"))
        h_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter local path or URL (https://github.com/user/repo.git)")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_source)
        h_layout.addWidget(self.source_input)
        h_layout.addWidget(browse_btn)
        layout.addLayout(h_layout)
        
        # Output path
        layout.addWidget(QLabel("Output File:"))
        h_layout2 = QHBoxLayout()
        self.output_input = QLineEdit()
        save_btn = QPushButton("Choose...")
        save_btn.clicked.connect(self.browse_output)
        h_layout2.addWidget(self.output_input)
        h_layout2.addWidget(save_btn)
        layout.addLayout(h_layout2)
        
        # Extract button
        extract_btn = QPushButton("Extract Data")
        extract_btn.clicked.connect(self.on_extract)
        layout.addWidget(extract_btn)
        
        # Progress
        self.extract_progress = QProgressBar()
        layout.addWidget(self.extract_progress)
        
        # Log
        self.extract_log = QTextEdit()
        self.extract_log.setReadOnly(True)
        layout.addWidget(self.extract_log)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_process_tab(self):
        """Create processing tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Input file
        layout.addWidget(QLabel("Input Data File:"))
        h_layout = QHBoxLayout()
        self.process_input = QLineEdit()
        process_browse = QPushButton("Browse...")
        process_browse.clicked.connect(lambda: self.browse_file(self.process_input))
        h_layout.addWidget(self.process_input)
        h_layout.addWidget(process_browse)
        layout.addLayout(h_layout)
        
        # Processing options
        layout.addWidget(QLabel("Processing Options:"))
        self.norm_code_check = QCheckBox("Normalize Code")
        self.clean_text_check = QCheckBox("Clean Text")
        self.remove_dup_check = QCheckBox("Remove Duplicates")
        
        layout.addWidget(self.norm_code_check)
        layout.addWidget(self.clean_text_check)
        layout.addWidget(self.remove_dup_check)
        
        # Process button
        process_btn = QPushButton("Process Data")
        process_btn.clicked.connect(self.on_process)
        layout.addWidget(process_btn)
        
        # Progress and log
        self.process_progress = QProgressBar()
        self.process_log = QTextEdit()
        self.process_log.setReadOnly(True)
        layout.addWidget(self.process_progress)
        layout.addWidget(self.process_log)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_label_tab(self):
        """Create labeling tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Input file
        layout.addWidget(QLabel("Input Data File:"))
        h_layout = QHBoxLayout()
        self.label_input = QLineEdit()
        label_browse = QPushButton("Browse...")
        label_browse.clicked.connect(lambda: self.browse_file(self.label_input))
        h_layout.addWidget(self.label_input)
        h_layout.addWidget(label_browse)
        layout.addLayout(h_layout)
        
        # Label type
        layout.addWidget(QLabel("Label Type:"))
        self.label_type_combo = QComboBox()
        self.label_type_combo.addItems([
            "bug_severity",
            "code_complexity",
            "feature_type",
            "multi_label"
        ])
        layout.addWidget(self.label_type_combo)
        
        # Label button
        label_btn = QPushButton("Label Data")
        label_btn.clicked.connect(self.on_label)
        layout.addWidget(label_btn)
        
        # Progress and log
        self.label_progress = QProgressBar()
        self.label_log = QTextEdit()
        self.label_log.setReadOnly(True)
        layout.addWidget(self.label_progress)
        layout.addWidget(self.label_log)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_view_tab(self):
        """Create data view tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Load button
        load_btn = QPushButton("Load Data File")
        load_btn.clicked.connect(self.on_load_data)
        layout.addWidget(load_btn)
        
        # Stats
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(QLabel("Statistics:"))
        layout.addWidget(self.stats_text)
        
        # Table
        self.data_table = QTableWidget()
        layout.addWidget(QLabel("Data Preview:"))
        layout.addWidget(self.data_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_export_tab(self):
        """Create export tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Input file
        layout.addWidget(QLabel("Data File:"))
        h_layout = QHBoxLayout()
        self.export_input = QLineEdit()
        export_browse = QPushButton("Browse...")
        export_browse.clicked.connect(lambda: self.browse_file(self.export_input))
        h_layout.addWidget(self.export_input)
        h_layout.addWidget(export_browse)
        layout.addLayout(h_layout)
        
        # Format selection
        layout.addWidget(QLabel("Export Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "JSON", "JSONL", "Parquet"])
        layout.addWidget(self.format_combo)
        
        # Output path
        layout.addWidget(QLabel("Output File:"))
        h_layout2 = QHBoxLayout()
        self.export_output = QLineEdit()
        export_save = QPushButton("Choose...")
        export_save.clicked.connect(self.browse_output)
        h_layout2.addWidget(self.export_output)
        h_layout2.addWidget(export_save)
        layout.addLayout(h_layout2)
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.on_export)
        layout.addWidget(export_btn)
        
        # Log
        self.export_log = QTextEdit()
        self.export_log.setReadOnly(True)
        layout.addWidget(self.export_log)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_agentic_tab(self):
        """Create AI agentic dataset maker tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🤖 AI Agentic Dataset Maker")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Step 1: Repository Setup
        step1_label = QLabel("Step 1: Setup Repository")
        step1_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(step1_label)
        
        repo_group = QWidget()
        repo_layout = QVBoxLayout()
        
        # Repository input
        repo_layout.addWidget(QLabel("Repository (local path or Git URL):"))
        repo_h_layout = QHBoxLayout()
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("e.g., /path/to/project or https://github.com/user/repo.git")
        repo_browse_btn = QPushButton("Browse Local...")
        repo_browse_btn.clicked.connect(self.browse_repo)
        repo_clone_btn = QPushButton("Clone Git Repo")
        repo_clone_btn.clicked.connect(self.on_clone_repo)
        repo_h_layout.addWidget(self.repo_input)
        repo_h_layout.addWidget(repo_browse_btn)
        repo_h_layout.addWidget(repo_clone_btn)
        repo_layout.addLayout(repo_h_layout)
        
        # Setup button
        self.setup_repo_btn = QPushButton("✅ Setup Repository")
        self.setup_repo_btn.clicked.connect(self.on_setup_repo)
        repo_layout.addWidget(self.setup_repo_btn)
        
        repo_group.setLayout(repo_layout)
        layout.addWidget(repo_group)
        
        # Separator
        separator1 = QLabel("-" * 50)
        separator1.setAlignment(Qt.AlignCenter)
        layout.addWidget(separator1)
        
        # Step 2: Dataset Request
        step2_label = QLabel("Step 2: Describe Your Dataset")
        step2_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(step2_label)
        
        # User prompt input
        layout.addWidget(QLabel("Your Dataset Request:"))
        self.agentic_prompt = QTextEdit()
        self.agentic_prompt.setPlaceholderText("Example: Create a dataset with bug severity metrics from Java projects, including code complexity and feature classification...")
        self.agentic_prompt.setMaximumHeight(100)
        self.agentic_prompt.setEnabled(False)  # Disabled until repo is set up
        layout.addWidget(self.agentic_prompt)
        
        # Analyze button
        self.analyze_btn = QPushButton("🔍 Analyze Request")
        self.analyze_btn.clicked.connect(self.on_analyze_prompt)
        self.analyze_btn.setEnabled(False)  # Disabled until repo is set up
        layout.addWidget(self.analyze_btn)
        
        # Analysis results display
        layout.addWidget(QLabel("AI Analysis Results:"))
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setMaximumHeight(150)
        layout.addWidget(self.analysis_results)
        
        # Clarification section
        self.clarification_widget = QWidget()
        clarification_layout = QVBoxLayout()
        clarification_layout.addWidget(QLabel("🤔 Need Clarification:"))
        self.clarification_question = QLabel()
        clarification_layout.addWidget(self.clarification_question)
        self.clarification_input = QLineEdit()
        self.clarification_input.setPlaceholderText("Your clarification...")
        clarification_layout.addWidget(self.clarification_input)
        clarify_btn = QPushButton("Submit Clarification")
        clarify_btn.clicked.connect(self.on_submit_clarification)
        clarification_layout.addWidget(clarify_btn)
        self.clarification_widget.setLayout(clarification_layout)
        self.clarification_widget.hide()
        layout.addWidget(self.clarification_widget)
        
        # Separator
        separator2 = QLabel("-" * 50)
        separator2.setAlignment(Qt.AlignCenter)
        layout.addWidget(separator2)
        
        # Step 3: Generate Dataset
        step3_label = QLabel("Step 3: Generate Dataset")
        step3_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(step3_label)
        
        # Generate button
        self.generate_btn = QPushButton("🚀 Generate Dataset")
        self.generate_btn.clicked.connect(self.on_generate_dataset)
        self.generate_btn.setEnabled(False)  # Disabled until analysis is complete
        layout.addWidget(self.generate_btn)
        
        # Progress and log
        self.agentic_progress = QProgressBar()
        layout.addWidget(self.agentic_progress)
        
        self.agentic_log = QTextEdit()
        self.agentic_log.setReadOnly(True)
        layout.addWidget(self.agentic_log)
        
        # Initialize agentic maker
        self.agentic_maker = AgenticDatasetMaker()
        self.current_repo_path = None
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    # Callback methods
    
    def on_dataset_changed(self):
        """Update description when dataset changes"""
        dataset_type = self.dataset_combo.currentText()
        info = SUPPORTED_DATASETS.get(dataset_type, {})
        desc = f"{info.get('name', '')}: {info.get('description', '')}"
        self.desc_label.setText(desc)
    
    def browse_source(self):
        """Browse for source path"""
        path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.source_input.setText(path)
    
    def browse_output(self):
        """Browse for output file"""
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "JSON Files (*.json)")
        if path:
            self.output_input.setText(path)
    
    def browse_file(self, input_widget):
        """Browse for any file"""
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "JSON Files (*.json)")
        if path:
            input_widget.setText(path)
    
    def on_extract(self):
        """Handle extraction"""
        dataset_type = self.dataset_combo.currentText()
        source = self.source_input.text()
        output = self.output_input.text()
        
        if not source or not output:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        try:
            self.extract_log.clear()
            self.extract_log.append("Starting extraction...")
            
            extractor = create_extractor(dataset_type, source)
            records = extractor.extract()
            
            with open(output, 'w') as f:
                json.dump(records, f, indent=2, default=str)
            
            self.extract_log.append(f"✓ Extracted {len(records)} records")
            self.extract_log.append(f"✓ Saved to {output}")
            self.statusBar().showMessage(f"Extraction complete: {len(records)} records")
        
        except Exception as e:
            self.extract_log.append(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_process(self):
        """Handle processing"""
        input_file = self.process_input.text()
        
        if not input_file:
            QMessageBox.warning(self, "Error", "Please select input file")
            return
        
        try:
            self.process_log.clear()
            self.process_log.append("Loading data...")
            
            with open(input_file) as f:
                records = json.load(f)
            
            self.process_log.append(f"Loaded {len(records)} records")
            
            pipeline = ProcessingPipeline()
            if self.norm_code_check.isChecked():
                pipeline.add_processor(CodeNormalizer())
            if self.clean_text_check.isChecked():
                pipeline.add_processor(TextCleaner())
            if self.remove_dup_check.isChecked():
                pipeline.add_processor(DuplicateRemover())
            
            self.process_log.append("Processing...")
            processed = pipeline.process(records)
            
            # Save processed data
            output_file = input_file.replace('.json', '_processed.json')
            with open(output_file, 'w') as f:
                json.dump(processed, f, indent=2, default=str)
            
            self.process_log.append(f"✓ Processed {len(processed)} records")
            self.process_log.append(f"✓ Saved to {output_file}")
            self.current_data = processed
            self.statusBar().showMessage(f"Processing complete: {len(processed)} records")
        
        except Exception as e:
            self.process_log.append(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_label(self):
        """Handle labeling"""
        input_file = self.label_input.text()
        label_type = self.label_type_combo.currentText()
        
        if not input_file:
            QMessageBox.warning(self, "Error", "Please select input file")
            return
        
        try:
            self.label_log.clear()
            self.label_log.append(f"Loading data for {label_type}...")
            
            with open(input_file) as f:
                records = json.load(f)
            
            # Create appropriate labeler
            if label_type == "bug_severity":
                labeler = BugSeverityLabeler()
            elif label_type == "code_complexity":
                labeler = CodeComplexityLabeler()
            else:
                labeler = FeatureLabelClassifier()
            
            self.label_log.append("Labeling...")
            labeled = labeler.label(records)
            
            output_file = input_file.replace('.json', '_labeled.json')
            with open(output_file, 'w') as f:
                json.dump(labeled, f, indent=2, default=str)
            
            self.label_log.append(f"✓ Labeled {len(labeled)} records")
            self.label_log.append(f"✓ Saved to {output_file}")
            self.statusBar().showMessage(f"Labeling complete")
        
        except Exception as e:
            self.label_log.append(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_load_data(self):
        """Load and display data"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Data", "", "JSON Files (*.json)")
        if not file_path:
            return
        
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            self.current_data = data
            
            # Display stats
            stats = {
                "Total Records": len(data),
                "Fields": list(data[0].keys()) if data else []
            }
            self.stats_text.setText(json.dumps(stats, indent=2))
            
            # Display table
            self.data_table.setRowCount(min(len(data), 10))
            if data:
                self.data_table.setColumnCount(len(data[0]))
                self.data_table.setHorizontalHeaderLabels(data[0].keys())
                
                for row, record in enumerate(data[:10]):
                    for col, (key, value) in enumerate(record.items()):
                        self.data_table.setItem(row, col, QTableWidgetItem(str(value)[:50]))
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
    
    def on_export(self):
        """Handle export"""
        if not self.current_data:
            QMessageBox.warning(self, "Error", "No data to export")
            return
        
        output_file = self.export_output.text()
        if not output_file:
            QMessageBox.warning(self, "Error", "Please specify output file")
            return
        
        try:
            format_type = self.format_combo.currentText().lower()
            
            if format_type == "json":
                with open(output_file, 'w') as f:
                    json.dump(self.current_data, f, indent=2)
            
            elif format_type == "csv":
                import csv
                with open(output_file, 'w', newline='') as f:
                    if self.current_data:
                        writer = csv.DictWriter(f, fieldnames=self.current_data[0].keys())
                        writer.writeheader()
                        writer.writerows(self.current_data)
            
            self.export_log.setText(f"✓ Exported {len(self.current_data)} records to {output_file}")
            QMessageBox.information(self, "Success", "Data exported successfully")
        
        except Exception as e:
            self.export_log.setText(f"✗ Error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def browse_repo(self):
        """Browse for local repository"""
        path = QFileDialog.getExistingDirectory(self, "Select Repository Directory")
        if path:
            self.repo_input.setText(path)
    
    def on_clone_repo(self):
        """Handle git repository cloning"""
        repo_url = self.repo_input.text().strip()
        if not repo_url:
            QMessageBox.warning(self, "Error", "Please enter a Git repository URL")
            return
        
        try:
            self.agentic_log.clear()
            self.agentic_log.append(f"📥 Cloning repository: {repo_url}")
            
            # Determine clone directory name from URL
            import os
            from urllib.parse import urlparse
            
            parsed = urlparse(repo_url)
            repo_name = os.path.basename(parsed.path)
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            clone_path = os.path.join(os.getcwd(), repo_name)
            
            # Clone the repository
            import subprocess
            result = subprocess.run(['git', 'clone', repo_url, clone_path], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                self.repo_input.setText(clone_path)
                self.agentic_log.append(f"✅ Repository cloned to: {clone_path}")
                QMessageBox.information(self, "Success", f"Repository cloned successfully to {clone_path}")
            else:
                self.agentic_log.append(f"✗ Clone failed: {result.stderr}")
                QMessageBox.critical(self, "Error", f"Failed to clone repository: {result.stderr}")
        
        except Exception as e:
            self.agentic_log.append(f"✗ Clone error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_setup_repo(self):
        """Handle repository setup"""
        repo_path = self.repo_input.text().strip()
        if not repo_path:
            QMessageBox.warning(self, "Error", "Please specify repository path")
            return
        
        try:
            import os
            if not os.path.exists(repo_path):
                QMessageBox.warning(self, "Error", "Repository path does not exist")
                return
            
            self.agentic_log.clear()
            self.agentic_log.append(f"🔧 Setting up repository: {repo_path}")
            
            # Validate it's a git repository
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.exists(git_dir):
                self.agentic_log.append("⚠️  Warning: Not a Git repository")
            
            # Set current repo path
            self.current_repo_path = repo_path
            
            # Enable next steps
            self.agentic_prompt.setEnabled(True)
            self.analyze_btn.setEnabled(True)
            
            self.agentic_log.append("✅ Repository setup complete!")
            self.agentic_log.append("📝 You can now describe your dataset request")
            
            QMessageBox.information(self, "Success", "Repository setup complete! You can now proceed to Step 2.")
            
        except Exception as e:
            self.agentic_log.append(f"✗ Setup error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_analyze_prompt(self):
        """Handle prompt analysis"""
        prompt = self.agentic_prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a dataset request")
            return
        
        if not self.current_repo_path:
            QMessageBox.warning(self, "Error", "Please setup repository first (Step 1)")
            return
        
        try:
            self.analysis_results.clear()
            self.agentic_log.clear()
            self.agentic_log.append("🤖 Analyzing your request...")
            
            # Analyze the prompt
            analysis = self.agentic_maker.analyze_prompt(prompt)
            
            # Display analysis results
            self.analysis_results.setText(json.dumps(analysis, indent=2))
            
            # Check if clarification is needed
            if analysis.get('needs_clarification', False):
                self.clarification_question.setText(analysis.get('clarification_question', ''))
                self.clarification_widget.show()
                self.agentic_log.append("🤔 Need clarification from user")
                self.generate_btn.setEnabled(False)
            else:
                self.clarification_widget.hide()
                self.agentic_log.append("✅ Analysis complete - ready to generate dataset")
                self.generate_btn.setEnabled(True)
            
        except Exception as e:
            self.agentic_log.append(f"✗ Analysis error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_submit_clarification(self):
        """Handle clarification submission"""
        clarification = self.clarification_input.text().strip()
        if not clarification:
            QMessageBox.warning(self, "Error", "Please provide clarification")
            return
        
        try:
            self.agentic_log.append("📝 Processing clarification...")
            
            # Re-analyze with clarification
            prompt = self.agentic_prompt.toPlainText().strip()
            analysis = self.agentic_maker.analyze_prompt_with_clarification(prompt, clarification)
            
            # Update analysis results
            self.analysis_results.setText(json.dumps(analysis, indent=2))
            
            # Hide clarification widget
            self.clarification_widget.hide()
            self.clarification_input.clear()
            
            self.agentic_log.append("✅ Clarification processed - ready to generate dataset")
            self.generate_btn.setEnabled(True)
            
        except Exception as e:
            self.agentic_log.append(f"✗ Clarification error: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def on_generate_dataset(self):
        """Handle dataset generation with threading"""
        if not self.current_repo_path:
            QMessageBox.warning(self, "Error", "Please setup repository first")
            return

        # Disable the generate button to prevent multiple clicks
        self.generate_btn.setEnabled(False)
        self.agentic_log.clear()
        self.agentic_log.append("🚀 Starting dataset generation...")
        self.agentic_progress.setRange(0, 0)  # Indeterminate progress

        # Create worker thread
        self.worker = DatasetGenerationWorker(
            self.agentic_maker,
            self.agentic_prompt.toPlainText().strip(),
            self.current_repo_path
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        
        # Start the worker thread
        self.worker.start()

    def update_progress(self, message):
        """Update progress display"""
        self.agentic_log.append(message)

    def on_generation_finished(self, result):
        """Handle successful dataset generation"""
        self.agentic_progress.setRange(0, 100)
        self.agentic_progress.setValue(100)
        self.generate_btn.setEnabled(True)
        
        self.agentic_log.append(f"✅ Dataset generated successfully!")
        self.agentic_log.append(f"📊 Records: {result.get('total_records', 0)}")
        self.agentic_log.append(f"📁 Output: {result.get('output_path', 'N/A')}")
        
        # Update current data for viewing
        if result.get('data'):
            self.current_data = result['data']
        
        QMessageBox.information(self, "Success", "Dataset generated successfully!")

    def on_generation_error(self, error_msg):
        """Handle dataset generation error"""
        self.agentic_progress.setRange(0, 100)
        self.agentic_progress.setValue(0)
        self.generate_btn.setEnabled(True)
        
        self.agentic_log.append(f"✗ Generation error: {error_msg}")
        QMessageBox.critical(self, "Error", str(error_msg))


class DatasetGenerationWorker(QThread):
    """Worker thread for dataset generation to prevent GUI blocking"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, agentic_maker, prompt, source_path):
        super().__init__()
        self.agentic_maker = agentic_maker
        self.prompt = prompt
        self.source_path = source_path
    
    def run(self):
        """Run dataset generation in background thread"""
        try:
            self.progress.emit("🤖 Starting AI analysis...")
            
            # Generate dataset
            result = self.agentic_maker.create_dataset(
                user_query=self.prompt,
                source_path=self.source_path
            )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = DatasetManagerGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
