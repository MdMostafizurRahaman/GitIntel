"""
Enhanced Interactive GUI for Agentic Dataset Maker
===================================================
- Dropdown for existing metrics
- Custom metric input with LLM help
- LLM Jury validation display
- Preview before dataset generation
- Multiple feedback loops like GitHub Copilot
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QListWidget,
    QTabWidget, QGroupBox, QProgressBar, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QSplitter, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Import our systems
sys.path.append(str(Path(__file__).parent.parent))
from intelligent_metrics_system import AgenticDatasetMaker, MetricsCollector, FormulaParser
from llm_jury_system import LLMJurySystem, CodeProposal, JuryVote


class JuryProcessThread(QThread):
    """Background thread for LLM jury process"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object, list, str)  # proposal, votes, summary
    error = pyqtSignal(str)
    
    def __init__(self, jury_system, metric_description, available_metrics, num_judges):
        super().__init__()
        self.jury_system = jury_system
        self.metric_description = metric_description
        self.available_metrics = available_metrics
        self.num_judges = num_judges
    
    def run(self):
        try:
            self.progress.emit("🤖 Generator LLM is creating code...")
            proposal, votes, summary = self.jury_system.full_jury_process(
                self.metric_description,
                self.available_metrics,
                self.num_judges
            )
            self.finished.emit(proposal, votes, summary)
        except Exception as e:
            self.error.emit(str(e))


class EnhancedInteractiveGUI(QMainWindow):
    """
    Main GUI - Interactive like GitHub Copilot
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize systems
        self.dataset_maker = AgenticDatasetMaker()
        self.jury_system = LLMJurySystem()
        
        # State
        self.selected_repos: List[str] = []
        self.available_metrics: Dict = {}
        self.custom_metrics: Dict[str, str] = {}  # name -> formula/code
        self.approved_proposals: Dict[str, CodeProposal] = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("🤖 Agentic Dataset Maker - LLM Jury Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Left panel: Configuration
        left_panel = self.create_left_panel()
        
        # Right panel: Preview & Results
        right_panel = self.create_right_panel()
        
        # Add to main layout with splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 800])
        
        main_layout.addWidget(splitter)
        
        self.show()
    
    def create_left_panel(self) -> QWidget:
        """Create left configuration panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Title
        title = QLabel("📊 Dataset Configuration")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        # Tab 1: Repository Selection
        repo_tab = self.create_repo_tab()
        tabs.addTab(repo_tab, "📁 Repositories")
        
        # Tab 2: Metrics Selection
        metrics_tab = self.create_metrics_tab()
        tabs.addTab(metrics_tab, "📏 Metrics")
        
        # Tab 3: Custom Metrics (LLM Jury)
        custom_tab = self.create_custom_metrics_tab()
        tabs.addTab(custom_tab, "🤖 Custom Metrics")
        
        layout.addWidget(tabs)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        preview_btn = QPushButton("👁️ Preview Dataset")
        preview_btn.clicked.connect(self.preview_dataset)
        preview_btn.setStyleSheet("background-color: #0066cc; color: white; padding: 10px;")
        
        generate_btn = QPushButton("✅ Generate Dataset")
        generate_btn.clicked.connect(self.generate_dataset)
        generate_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px;")
        
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(generate_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def create_repo_tab(self) -> QWidget:
        """Create repository selection tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Instructions
        info = QLabel("Select git repositories to analyze:")
        layout.addWidget(info)
        
        # Add repo button
        add_btn = QPushButton("➕ Add Repository")
        add_btn.clicked.connect(self.add_repository)
        layout.addWidget(add_btn)
        
        # Repo list
        self.repo_list = QListWidget()
        layout.addWidget(self.repo_list)
        
        # Remove repo button
        remove_btn = QPushButton("❌ Remove Selected")
        remove_btn.clicked.connect(self.remove_repository)
        layout.addWidget(remove_btn)
        
        # Analyze sample repo button
        analyze_btn = QPushButton("🔍 Analyze Sample for Available Metrics")
        analyze_btn.clicked.connect(self.analyze_sample_repo)
        layout.addWidget(analyze_btn)
        
        return widget
    
    def create_metrics_tab(self) -> QWidget:
        """Create metrics selection tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Instructions
        info = QLabel("Select metrics to include in dataset:")
        layout.addWidget(info)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search:")
        self.metric_search = QLineEdit()
        self.metric_search.setPlaceholderText("Type to filter metrics...")
        self.metric_search.textChanged.connect(self.filter_metrics)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.metric_search)
        layout.addLayout(search_layout)
        
        # Metrics list with checkboxes
        self.metrics_list = QListWidget()
        self.metrics_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.metrics_list)
        
        # Quick select buttons
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.metrics_list.selectAll())
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self.metrics_list.clearSelection())
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_custom_metrics_tab(self) -> QWidget:
        """Create custom metrics tab with LLM jury"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Instructions
        info = QLabel("🤖 Create custom metrics using LLM Jury System")
        info.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(info)
        
        # Input method selection
        method_group = QGroupBox("Input Method")
        method_layout = QVBoxLayout()
        
        self.formula_radio = QCheckBox("Simple Formula (No LLM needed)")
        self.formula_radio.setChecked(True)
        self.formula_radio.toggled.connect(self.toggle_input_method)
        
        self.llm_radio = QCheckBox("Natural Language Description (LLM Jury)")
        
        method_layout.addWidget(self.formula_radio)
        method_layout.addWidget(self.llm_radio)
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Metric name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Metric Name:"))
        self.custom_metric_name = QLineEdit()
        self.custom_metric_name.setPlaceholderText("e.g., developer_experience_score")
        name_layout.addWidget(self.custom_metric_name)
        layout.addLayout(name_layout)
        
        # Input area (formula or description)
        self.input_label = QLabel("Formula:")
        layout.addWidget(self.input_label)
        
        self.custom_input = QTextEdit()
        self.custom_input.setPlaceholderText(
            "Formula: total_commits / project_age_days\n"
            "or\n"
            "Description: Calculate developer productivity based on commits and code quality"
        )
        self.custom_input.setMaximumHeight(100)
        layout.addWidget(self.custom_input)
        
        # Jury settings (for LLM mode)
        jury_group = QGroupBox("🏛️ LLM Jury Settings")
        jury_layout = QHBoxLayout()
        jury_layout.addWidget(QLabel("Number of Judges:"))
        self.num_judges = QSpinBox()
        self.num_judges.setMinimum(3)
        self.num_judges.setMaximum(5)
        self.num_judges.setValue(3)
        jury_layout.addWidget(self.num_judges)
        jury_group.setLayout(jury_layout)
        layout.addWidget(jury_group)
        self.jury_group = jury_group
        self.jury_group.setVisible(False)
        
        # Create/Validate button
        create_btn = QPushButton("✨ Create & Validate Metric")
        create_btn.clicked.connect(self.create_custom_metric)
        create_btn.setStyleSheet("background-color: #6f42c1; color: white; padding: 8px;")
        layout.addWidget(create_btn)
        
        # Progress bar
        self.jury_progress = QProgressBar()
        self.jury_progress.setVisible(False)
        layout.addWidget(self.jury_progress)
        
        # Jury results area
        self.jury_results = QTextEdit()
        self.jury_results.setReadOnly(True)
        self.jury_results.setPlaceholderText("LLM Jury results will appear here...")
        layout.addWidget(self.jury_results)
        
        # Approved custom metrics list
        layout.addWidget(QLabel("✅ Approved Custom Metrics:"))
        self.approved_metrics_list = QListWidget()
        layout.addWidget(self.approved_metrics_list)
        
        # Remove button
        remove_custom_btn = QPushButton("❌ Remove Selected")
        remove_custom_btn.clicked.connect(self.remove_custom_metric)
        layout.addWidget(remove_custom_btn)
        
        return widget
    
    def create_right_panel(self) -> QWidget:
        """Create right preview panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Title
        title = QLabel("👁️ Preview & Results")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Tabs for different views
        tabs = QTabWidget()
        
        # Preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout()
        preview_tab.setLayout(preview_layout)
        
        self.preview_table = QTableWidget()
        preview_layout.addWidget(self.preview_table)
        
        tabs.addTab(preview_tab, "📊 Data Preview")
        
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout()
        summary_tab.setLayout(summary_layout)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        tabs.addTab(summary_tab, "📋 Summary")
        
        # LLM Conversation tab
        llm_tab = QWidget()
        llm_layout = QVBoxLayout()
        llm_tab.setLayout(llm_layout)
        
        self.llm_conversation = QTextEdit()
        self.llm_conversation.setReadOnly(True)
        llm_layout.addWidget(self.llm_conversation)
        
        tabs.addTab(llm_tab, "💬 LLM Conversation")
        
        layout.addWidget(tabs)
        
        return panel
    
    def toggle_input_method(self, checked):
        """Toggle between formula and LLM description mode"""
        if self.formula_radio.isChecked():
            self.input_label.setText("Formula:")
            self.custom_input.setPlaceholderText("e.g., total_commits / project_age_days")
            self.jury_group.setVisible(False)
            self.llm_radio.setChecked(False)
        else:
            self.input_label.setText("Natural Language Description:")
            self.custom_input.setPlaceholderText(
                "Describe the metric in natural language.\n"
                "e.g., 'Calculate team productivity by dividing total commits by number of authors and project age'"
            )
            self.jury_group.setVisible(True)
            self.llm_radio.setChecked(True)
    
    def add_repository(self):
        """Add repository to list"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if dir_path:
            self.selected_repos.append(dir_path)
            self.repo_list.addItem(dir_path)
    
    def remove_repository(self):
        """Remove selected repository"""
        current_row = self.repo_list.currentRow()
        if current_row >= 0:
            self.selected_repos.pop(current_row)
            self.repo_list.takeItem(current_row)
    
    def analyze_sample_repo(self):
        """Analyze first repo to get available metrics"""
        if not self.selected_repos:
            QMessageBox.warning(self, "Warning", "Please add at least one repository first!")
            return
        
        sample_repo = self.selected_repos[0]
        collector = MetricsCollector(Path(sample_repo))
        self.available_metrics = collector.collect_all_metrics()
        
        # Populate metrics list
        self.metrics_list.clear()
        for metric_name in sorted(self.available_metrics.keys()):
            if not isinstance(self.available_metrics[metric_name], (int, float)):
                continue  # Skip non-numeric metrics
            self.metrics_list.addItem(metric_name)
        
        # Select all by default
        self.metrics_list.selectAll()
        
        QMessageBox.information(
            self,
            "Success",
            f"Found {self.metrics_list.count()} metrics in {Path(sample_repo).name}"
        )
    
    def filter_metrics(self, text):
        """Filter metrics list based on search"""
        for i in range(self.metrics_list.count()):
            item = self.metrics_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def create_custom_metric(self):
        """Create and validate custom metric"""
        metric_name = self.custom_metric_name.text().strip()
        metric_input = self.custom_input.toPlainText().strip()
        
        if not metric_name or not metric_input:
            QMessageBox.warning(self, "Warning", "Please provide both name and formula/description!")
            return
        
        if self.formula_radio.isChecked():
            # Simple formula - validate directly
            self.validate_formula(metric_name, metric_input)
        else:
            # LLM description - start jury process
            self.start_jury_process(metric_name, metric_input)
    
    def validate_formula(self, name, formula):
        """Validate simple formula"""
        if not self.available_metrics:
            QMessageBox.warning(self, "Warning", "Please analyze a repository first!")
            return
        
        parser = FormulaParser(self.available_metrics)
        is_valid, message = parser.validate_formula(formula)
        
        if is_valid:
            self.custom_metrics[name] = formula
            self.approved_metrics_list.addItem(f"✅ {name}: {formula}")
            self.jury_results.append(f"\n✅ Formula validated: {name}\n{message}\n")
            QMessageBox.information(self, "Success", f"Formula '{name}' validated successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Formula validation failed:\n{message}")
    
    def start_jury_process(self, metric_name, description):
        """Start LLM jury process in background"""
        if not self.available_metrics:
            QMessageBox.warning(self, "Warning", "Please analyze a repository first!")
            return
        
        self.jury_progress.setVisible(True)
        self.jury_progress.setRange(0, 0)  # Indeterminate
        
        self.jury_thread = JuryProcessThread(
            self.jury_system,
            description,
            self.available_metrics,
            self.num_judges.value()
        )
        
        self.jury_thread.progress.connect(self.update_jury_progress)
        self.jury_thread.finished.connect(lambda p, v, s: self.jury_process_finished(metric_name, p, v, s))
        self.jury_thread.error.connect(self.jury_process_error)
        
        self.jury_thread.start()
        
        self.llm_conversation.append(f"\n{'='*60}\n")
        self.llm_conversation.append(f"🎬 Starting LLM Jury Process for: {metric_name}\n")
        self.llm_conversation.append(f"Description: {description}\n")
        self.llm_conversation.append(f"{'='*60}\n")
    
    def update_jury_progress(self, message):
        """Update jury progress"""
        self.llm_conversation.append(f"{message}\n")
    
    def jury_process_finished(self, metric_name, proposal, votes, summary):
        """Handle jury process completion"""
        self.jury_progress.setVisible(False)
        
        self.llm_conversation.append(f"\n{summary}\n")
        
        if proposal:
            # Show jury votes
            self.jury_results.clear()
            self.jury_results.append(f"🏛️ LLM JURY RESULTS\n{'='*50}\n")
            self.jury_results.append(f"Metric: {proposal.metric_name}\n")
            self.jury_results.append(f"Description: {proposal.description}\n\n")
            
            for vote in votes:
                color = "green" if vote.result.value == "approved" else "red"
                self.jury_results.append(f"{vote.judge_id}: {vote.result.value.upper()} (Score: {vote.score})\n")
                self.jury_results.append(f"Reasoning: {vote.reasoning}\n\n")
            
            self.jury_results.append(f"\n{'='*50}\n")
            self.jury_results.append(f"Generated Code:\n\n{proposal.code}\n")
            
            # Ask user to approve
            reply = QMessageBox.question(
                self,
                "Approve Code?",
                f"The jury has validated this code.\n\n{summary}\n\nDo you want to approve and use it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.approved_proposals[metric_name] = proposal
                self.approved_metrics_list.addItem(f"🤖 {metric_name} (LLM Generated)")
                self.llm_conversation.append(f"✅ User approved: {metric_name}\n")
        else:
            self.jury_results.append(f"❌ Jury could not approve the code:\n{summary}\n")
            QMessageBox.warning(self, "Not Approved", f"The jury could not approve this code:\n\n{summary}")
    
    def jury_process_error(self, error_msg):
        """Handle jury process error"""
        self.jury_progress.setVisible(False)
        QMessageBox.critical(self, "Error", f"Jury process error:\n{error_msg}")
    
    def remove_custom_metric(self):
        """Remove custom metric"""
        current_row = self.approved_metrics_list.currentRow()
        if current_row >= 0:
            item_text = self.approved_metrics_list.item(current_row).text()
            metric_name = item_text.split(":")[0].replace("✅ ", "").replace("🤖 ", "").strip()
            
            if metric_name in self.custom_metrics:
                del self.custom_metrics[metric_name]
            if metric_name in self.approved_proposals:
                del self.approved_proposals[metric_name]
            
            self.approved_metrics_list.takeItem(current_row)
    
    def preview_dataset(self):
        """Preview dataset before generating"""
        if not self.selected_repos:
            QMessageBox.warning(self, "Warning", "Please add repositories first!")
            return
        
        # Get selected metrics
        selected_metrics = [
            self.metrics_list.item(i).text()
            for i in range(self.metrics_list.count())
            if self.metrics_list.item(i).isSelected()
        ]
        
        if not selected_metrics and not self.custom_metrics:
            QMessageBox.warning(self, "Warning", "Please select at least one metric!")
            return
        
        # Show preview
        self.preview_table.clear()
        self.preview_table.setColumnCount(len(selected_metrics) + len(self.custom_metrics) + 1)
        self.preview_table.setRowCount(len(self.selected_repos))
        
        headers = ["Repository"] + selected_metrics + list(self.custom_metrics.keys())
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # Fill with sample data
        for row, repo_path in enumerate(self.selected_repos):
            self.preview_table.setItem(row, 0, QTableWidgetItem(Path(repo_path).name))
            for col in range(1, len(headers)):
                self.preview_table.setItem(row, col, QTableWidgetItem("..."))
        
        # Update summary
        self.summary_text.clear()
        self.summary_text.append(f"📊 Dataset Preview\n{'='*50}\n")
        self.summary_text.append(f"Repositories: {len(self.selected_repos)}\n")
        self.summary_text.append(f"Base Metrics: {len(selected_metrics)}\n")
        self.summary_text.append(f"Custom Metrics: {len(self.custom_metrics)}\n")
        self.summary_text.append(f"LLM Generated: {len(self.approved_proposals)}\n")
        self.summary_text.append(f"Total Columns: {len(headers)}\n")
    
    def generate_dataset(self):
        """Generate final dataset"""
        if not self.selected_repos:
            QMessageBox.warning(self, "Warning", "Please add repositories first!")
            return
        
        # Ask for output filename
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Dataset",
            "dataset.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # Generate dataset
            df = self.dataset_maker.generate_dataset(
                repo_paths=self.selected_repos,
                custom_formulas=self.custom_metrics,
                output_filename=Path(filename).name
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"Dataset generated successfully!\n\nSaved to: {filename}\n\nRows: {len(df)}\nColumns: {len(df.columns)}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate dataset:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    gui = EnhancedInteractiveGUI()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
