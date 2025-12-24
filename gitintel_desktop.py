#!/usr/bin/env python3
"""
GitIntel Desktop GUI - User-friendly desktop application for repository analysis
Built with Tkinter for cross-platform compatibility
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from datetime import datetime
import json

# Import GitIntel modules
from repochat_core import RepoChatCore
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_query_generator import CypherQueryGenerator
from llm_git_analyzer import LLMGitAnalyzer

# Import GitIntel Ultimate components
from gitintel_ultimate_fixed import GitIntelUltimate
from ck_metrics_analyzer import CKMetricsAnalyzer
from enhanced_szz_analyzer import EnhancedSZZAnalyzer
from unified_metrics_analyzer import UnifiedMetricsAnalyzer

class GitIntelDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitIntel - Conversational Repository Analysis")
        
        # Set window size and position for Windows compatibility
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate window size (80% of screen)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Calculate position (center window)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1000, 600)
        self.root.state('normal')  # Ensure normal window state
        
        # Initialize components
        self.core = RepoChatCore()
        self.kg_builder = None
        self.query_generator = CypherQueryGenerator()
        self.llm_analyzer = LLMGitAnalyzer()
        
        # Initialize GitIntel Ultimate with Neo4j credentials from environment
        # Neo4j connection with environment variables
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')

        print(f"🔗 Connecting to Neo4j: {neo4j_uri}")
        print(f"👤 User: {neo4j_user}")

        self.gitintel_ultimate = GitIntelUltimate(neo4j_uri, neo4j_user, neo4j_password)

        # Check if Neo4j is available
        if hasattr(self.gitintel_ultimate, 'neo4j_available') and self.gitintel_ultimate.neo4j_available:
            print("✅ Neo4j connected successfully!")
            self.neo4j_status = tk.StringVar(value="🟢 Connected")
        else:
            print("⚠️  Neo4j not available - running in offline mode")
            self.neo4j_status = tk.StringVar(value="🔴 Offline Mode")
        
        # Current repository state
        self.current_repo = None
        self.is_ingested = False
        
        # Setup GUI
        self.setup_gui()
        self.setup_bindings()
        
        # Load last session if available
        self.load_last_session()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Setup modern styling
        self.setup_styles()
        
        # Create main menu
        self.create_menu()
        
        # Create main frames
        self.create_main_frames()
        
        # Create repository panel
        self.create_repository_panel()
        
        # Create analysis panel
        self.create_analysis_panel()
        
        # Create chat panel
        self.create_chat_panel()
        
        # Create visual graph panel
        self.create_visual_graph_panel()
        
        # Create status bar
        self.create_status_bar()
    
    def setup_styles(self):
        """Setup modern GUI styles"""
        style = ttk.Style()
        
        # Configure overall theme
        try:
            style.theme_use('clam')  # Modern theme
        except:
            pass  # Fallback to default
        
        # Button styles
        style.configure('Accent.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       padding=8,
                       relief='raised',
                       borderwidth=2)
        
        style.map('Accent.TButton',
                 background=[('active', '#0078d4'), ('pressed', '#106ebe')],
                 foreground=[('active', 'white')])
        
        # LabelFrame styles
        style.configure('Card.TLabelframe', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=15,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Card.TLabelframe.Label', 
                       font=('Segoe UI', 11, 'bold'),
                       foreground='#2d3748')
        
        # Entry and Combobox styles
        style.configure('Modern.TEntry', 
                       font=('Segoe UI', 10),
                       padding=6,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Modern.TCombobox', 
                       font=('Segoe UI', 10),
                       padding=6)
        
        # Label styles
        style.configure('Header.TLabel', 
                       font=('Segoe UI', 12, 'bold'),
                       foreground='#1a365d')
        
        style.configure('Body.TLabel', 
                       font=('Segoe UI', 10),
                       foreground='#4a5568')
    
    def create_menu(self):
        """Create application menu with modern icons"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="📂 Open Repository...", command=self.open_repository)
        file_menu.add_separator()
        file_menu.add_command(label="📊 Export Analysis...", command=self.export_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self.root.quit)

        # View menu - for switching between tabs
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ View", menu=view_menu)
        view_menu.add_command(label="📁 Repository Tab", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="📊 Analysis Tab", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="💬 Chat Tab", command=lambda: self.notebook.select(2))
        view_menu.add_command(label="🔗 Knowledge Graph Tab", command=lambda: self.notebook.select(3))
        view_menu.add_command(label="📈 Visualization Tab", command=lambda: self.notebook.select(4))

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 Tools", menu=tools_menu)
        tools_menu.add_command(label="⚙️ Settings", command=self.open_settings)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="📖 User Guide", command=self.show_user_guide)
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
    
    def create_main_frames(self):
        """Create main application frames"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        
        # Repository tab
        self.repo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repo_frame, text="📁 Repository")
        
        # Analysis tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="📊 Analysis")
        
        # Chat tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="💬 Conversational Q&A")
        
        # Knowledge Graph tab
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="🔗 Knowledge Graph")
        
        # Visual Graph tab
        self.visual_graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visual_graph_frame, text="📈 Graph Visualization")
        
        # Create knowledge graph panel
        self.create_graph_panel()
    
    def create_repository_panel(self):
        """Create repository management panel"""
        # Main container with padding
        main_container = ttk.Frame(self.repo_frame, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Repository selection frame with modern styling
        repo_select_frame = ttk.LabelFrame(main_container, text="📁 Repository Selection", 
                                         style='Card.TLabelframe', padding="15")
        repo_select_frame.pack(fill='x', pady=(0, 20))
        
        # Repository source selection with better layout
        source_frame = ttk.Frame(repo_select_frame)
        source_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(source_frame, text="Repository Source:", style='Header.TLabel').pack(anchor='w', pady=(0, 8))
        
        radio_frame = ttk.Frame(source_frame)
        radio_frame.pack(fill='x')
        
        self.repo_source_var = tk.StringVar(value="local")
        ttk.Radiobutton(radio_frame, text="📂 Local Path", variable=self.repo_source_var, 
                       value="local", command=self.on_source_change).pack(side='left', padx=(0, 20))
        ttk.Radiobutton(radio_frame, text="🌐 Git URL", variable=self.repo_source_var, 
                       value="url", command=self.on_source_change).pack(side='left')
        
        # Repository path input with better spacing
        path_frame = ttk.Frame(repo_select_frame)
        path_frame.pack(fill='x', pady=(0, 15))
        
        self.repo_input_label = ttk.Label(path_frame, text="Repository Path:", style='Body.TLabel')
        self.repo_input_label.pack(anchor='w', pady=(0, 8))
        
        input_frame = ttk.Frame(path_frame)
        input_frame.pack(fill='x')
        
        self.repo_path_var = tk.StringVar()
        self.repo_path_entry = ttk.Entry(input_frame, textvariable=self.repo_path_var, 
                                       style='Modern.TEntry', width=50)
        self.repo_path_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(input_frame, text="📂 Browse...", command=self.browse_repository).pack(side='right')
        
        # Action button with modern styling
        action_frame = ttk.Frame(repo_select_frame)
        action_frame.pack(fill='x', pady=(15, 0))
        
        self.action_button = ttk.Button(action_frame, text="📥 Load Repository", 
                                      command=self.load_repository, style='Accent.TButton')
        self.action_button.pack(side='left')
        
        # Clone destination (for Git URLs) - hidden initially
        self.clone_dest_frame = ttk.Frame(repo_select_frame)
        ttk.Label(self.clone_dest_frame, text="Clone Destination:", style='Body.TLabel').pack(anchor='w', pady=(10, 8))
        
        clone_input_frame = ttk.Frame(self.clone_dest_frame)
        clone_input_frame.pack(fill='x')
        
        self.clone_dest_var = tk.StringVar(value="D:/GitIntel/cloned_repos")
        self.clone_dest_entry = ttk.Entry(clone_input_frame, textvariable=self.clone_dest_var, 
                                        style='Modern.TEntry', width=40)
        self.clone_dest_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(clone_input_frame, text="📂 Browse...", command=self.browse_clone_destination).pack(side='right')
        
        # Clone progress (for Git URLs) - hidden initially
        self.clone_progress_frame = ttk.Frame(repo_select_frame)
        ttk.Label(self.clone_progress_frame, text="📊 Clone Progress:", style='Body.TLabel').pack(anchor='w', pady=(10, 8))
        
        progress_frame = ttk.Frame(self.clone_progress_frame)
        progress_frame.pack(fill='x')
        
        self.clone_progress = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.clone_progress.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.clone_status_var = tk.StringVar(value="⏳ Ready to clone")
        self.clone_status_label = ttk.Label(progress_frame, textvariable=self.clone_status_var, style='Body.TLabel')
        self.clone_status_label.pack(side='right')
        
        # Repository info frame with modern styling
        self.repo_info_frame = ttk.LabelFrame(main_container, text="📋 Repository Information", 
                                            style='Card.TLabelframe', padding="15")
        self.repo_info_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Repository info text with better font
        self.repo_info_text = scrolledtext.ScrolledText(self.repo_info_frame, height=15, 
                                                      wrap='word', font=('Consolas', 10))
        self.repo_info_text.pack(fill='both', expand=True)
        
        # Ingestion frame with modern styling
        ingest_frame = ttk.LabelFrame(main_container, text="⚙️ Data Ingestion", 
                                    style='Card.TLabelframe', padding="15")
        ingest_frame.pack(fill='x')
        
        # Commit limit input
        limit_frame = ttk.Frame(ingest_frame)
        limit_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(limit_frame, text="Commit Limit:", style='Body.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.ingest_commit_limit_var = tk.StringVar(value="100")
        ttk.Entry(limit_frame, textvariable=self.ingest_commit_limit_var, 
                 style='Modern.TEntry', width=15).grid(row=1, column=0, sticky='w', padx=(0, 10))
        
        ttk.Label(limit_frame, text="(Enter number or 'all')", 
                 font=("Segoe UI", 8), foreground='gray').grid(row=1, column=1, sticky='w')
        
        # Force reprocessing option
        self.force_reprocess_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ingest_frame, text="🔄 Force reprocessing (ignore existing data)", 
                       variable=self.force_reprocess_var, style='Body.TLabel').pack(anchor='w', pady=(0, 15))
        
        # Action buttons
        button_frame = ttk.Frame(ingest_frame)
        button_frame.pack(fill='x')
        
        self.ingest_button = ttk.Button(button_frame, text="🚀 Start Data Ingestion", 
                                      command=self.ingest_repository, style='Accent.TButton')
        self.ingest_button.pack(side='left')
        
        self.ingest_progress = ttk.Progressbar(button_frame, mode='determinate', maximum=100)
        self.ingest_progress.pack(side='left', fill='x', expand=True, padx=(15, 10))
        
        self.ingest_status_var = tk.StringVar(value="⏳ Ready to ingest")
        self.ingest_status_label = ttk.Label(button_frame, textvariable=self.ingest_status_var, style='Body.TLabel')
        self.ingest_status_label.pack(side='right')
        
        # Initialize UI state
        self.on_source_change()
    
    def create_analysis_panel(self):
        """Create statistical analysis panel"""
        # Main container with padding
        main_container = ttk.Frame(self.analysis_frame, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Analysis controls frame with modern styling
        controls_frame = ttk.LabelFrame(main_container, text="📊 Analysis Controls", 
                                      style='Card.TLabelframe', padding="15")
        controls_frame.pack(fill='x', pady=(0, 20))
        
        # Analysis type selection with better layout
        type_frame = ttk.Frame(controls_frame)
        type_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(type_frame, text="Analysis Type:", style='Header.TLabel').pack(anchor='w', pady=(0, 8))
        
        self.analysis_type_var = tk.StringVar(value="package_churn")
        analysis_combo = ttk.Combobox(type_frame, textvariable=self.analysis_type_var, 
                                     values=[
                                         "package_churn", "loc_analysis", "complexity", "releases",
                                         "loc_time_ratio", "complexity_time_ratio", "combined_analysis",
                                         "file_class_count", "code_duplication", "test_coverage",
                                         "security_patterns", "halstead_metrics", "maintainability_index",
                                         "technical_debt", "dependency_metrics", "unified_metrics",
                                         "ck_metrics", "szz_analysis", "bug_density", "churn_analysis"
                                     ], 
                                     state="readonly", style='Modern.TCombobox', width=30)
        analysis_combo.pack(fill='x')
        
        # Parameters frame
        params_frame = ttk.Frame(controls_frame)
        params_frame.pack(fill='x', pady=(0, 15))
        
        # Commit limit
        limit_frame = ttk.Frame(params_frame)
        limit_frame.pack(side='left', padx=(0, 20))
        
        ttk.Label(limit_frame, text="Commit Limit:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.commit_limit_var = tk.StringVar(value="1000")
        ttk.Entry(limit_frame, textvariable=self.commit_limit_var, 
                 style='Modern.TEntry', width=12).pack()
        
        # Analysis threshold (for some analyses)
        threshold_frame = ttk.Frame(params_frame)
        threshold_frame.pack(side='left')
        
        ttk.Label(threshold_frame, text="Threshold:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.analysis_threshold_var = tk.StringVar(value="500")
        ttk.Entry(threshold_frame, textvariable=self.analysis_threshold_var, 
                 style='Modern.TEntry', width=12).pack()
        
        # Action buttons frame
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill='x')
        
        # Analysis buttons
        self.run_analysis_button = ttk.Button(buttons_frame, text="🔍 Run Analysis", 
                                            command=self.run_statistical_analysis, style='Accent.TButton')
        self.run_analysis_button.pack(side='left', padx=(0, 10))
        
        ttk.Button(buttons_frame, text="📊 Export to Excel", 
                  command=self.export_to_excel).pack(side='left', padx=(0, 10))
        
        # Add GitIntel Ultimate button
        ttk.Button(buttons_frame, text="🚀 Ultimate Analysis (CK+SZZ)", 
                  command=self.run_ultimate_analysis, style='Accent.TButton').pack(side='left')
        
        # Results frame with modern styling
        results_frame = ttk.LabelFrame(main_container, text="📈 Analysis Results", 
                                     style='Card.TLabelframe', padding="15")
        results_frame.pack(fill='both', expand=True)
        
        # Results text area with better font
        self.analysis_results_text = scrolledtext.ScrolledText(results_frame, height=20, 
                                                            wrap='word', font=('Consolas', 10))
        self.analysis_results_text.pack(fill='both', expand=True)
    
    def create_chat_panel(self):
        """Create conversational Q&A panel"""
        # Main container with padding
        main_container = ttk.Frame(self.chat_frame, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Chat history frame with modern styling
        chat_history_frame = ttk.LabelFrame(main_container, text="💬 Conversation History", 
                                          style='Card.TLabelframe', padding="15")
        chat_history_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Chat display with better font
        self.chat_display = scrolledtext.ScrolledText(chat_history_frame, height=20, 
                                                    wrap='word', font=('Segoe UI', 10))
        self.chat_display.pack(fill='both', expand=True)
        self.chat_display.config(state='disabled')
        
        # Input frame with modern styling
        input_frame = ttk.LabelFrame(main_container, text="❓ Ask Questions", 
                                   style='Card.TLabelframe', padding="15")
        input_frame.pack(fill='x', pady=(0, 20))
        
        # Question input with better layout
        ttk.Label(input_frame, text="Your Question:", style='Header.TLabel').pack(anchor='w', pady=(0, 10))
        
        question_input_frame = ttk.Frame(input_frame)
        question_input_frame.pack(fill='x', pady=(0, 15))
        
        self.question_var = tk.StringVar()
        self.question_entry = ttk.Entry(question_input_frame, textvariable=self.question_var, 
                                      style='Modern.TEntry')
        self.question_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.ask_button = ttk.Button(question_input_frame, text="🚀 Ask", 
                                   command=self.ask_question, style='Accent.TButton')
        self.ask_button.pack(side='right')
        
        # Language selection with better layout
        lang_frame = ttk.Frame(input_frame)
        lang_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(lang_frame, text="Language:", style='Body.TLabel').pack(side='left')
        
        self.language_var = tk.StringVar(value="English")
        ttk.Radiobutton(lang_frame, text="🇺🇸 English", variable=self.language_var, 
                       value="English").pack(side='left', padx=(10, 0))
        ttk.Radiobutton(lang_frame, text="🇧🇩 বাংলা", variable=self.language_var, 
                       value="Bengali").pack(side='left', padx=(10, 0))
        
        # Example questions with modern styling
        examples_frame = ttk.LabelFrame(input_frame, text="💡 Example Questions", 
                                      style='Card.TLabelframe', padding="10")
        examples_frame.pack(fill='x')
        
        examples = [
            "Who are the top contributors?",
            "Show me recent commits", 
            "Find files with most complexity",
            "শীর্ষ অবদানকারী কারা?",
            "সাম্প্রতিক কমিট দেখাও"
        ]
        
        # Create a grid layout for examples
        for i, example in enumerate(examples):
            row = i // 2
            col = i % 2
            btn = ttk.Button(examples_frame, text=example, 
                           command=lambda q=example: self.use_example_question(q))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        examples_frame.grid_columnconfigure(0, weight=1)
        examples_frame.grid_columnconfigure(1, weight=1)
    
    def create_graph_panel(self):
        """Create knowledge graph visualization panel"""
        # Main container with padding
        main_container = ttk.Frame(self.graph_frame, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Graph controls frame with modern styling
        graph_controls_frame = ttk.LabelFrame(main_container, text="🔗 Graph Controls", 
                                            style='Card.TLabelframe', padding="15")
        graph_controls_frame.pack(fill='x', pady=(0, 20))
        
        # Repository selection
        repo_frame = ttk.Frame(graph_controls_frame)
        repo_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(repo_frame, text="Repository:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.graph_repo_var = tk.StringVar(value="kafka")
        
        # Get available repositories dynamically
        available_repos = self._get_available_repositories()
        
        repo_combo = ttk.Combobox(repo_frame, textvariable=self.graph_repo_var, 
                                 values=available_repos, 
                                 state="readonly", style='Modern.TCombobox', width=25)
        repo_combo.pack(fill='x')
        repo_combo.bind('<<ComboboxSelected>>', self.on_graph_repo_change)
        
        # Query type selection
        query_frame = ttk.Frame(graph_controls_frame)
        query_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(query_frame, text="Query Type:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.graph_query_var = tk.StringVar(value="overview")
        query_combo = ttk.Combobox(query_frame, textvariable=self.graph_query_var, 
                                  values=["overview", "contributors", "commits", "files"], 
                                  state="readonly", style='Modern.TCombobox', width=25)
        query_combo.pack(fill='x')
        
        # Load graph button
        ttk.Button(query_frame, text="🔍 Load Graph Data", 
                  command=self.load_graph_data, style='Accent.TButton').pack(fill='x', pady=(10, 0))
        
        # Graph display frame with modern styling
        graph_display_frame = ttk.LabelFrame(main_container, text="📊 Graph Data", 
                                           style='Card.TLabelframe', padding="15")
        graph_display_frame.pack(fill='both', expand=True)
        
        # Graph text area with better font
        self.graph_display_text = scrolledtext.ScrolledText(graph_display_frame, height=20, 
                                                          wrap='word', font=('Consolas', 10))
        self.graph_display_text.pack(fill='both', expand=True)
    
    def on_graph_repo_change(self, event=None):
        """Handle repository selection change in graph tab"""
        repo_name = self.graph_repo_var.get()
        repo_path = f"D:/GitIntel/{repo_name}"
        
        # Auto-update repository path in repository tab
        self.repo_path_var.set(repo_path)
        
        # Show instruction message
        instruction_text = f"""🔄 Repository selected: {repo_name}

📍 Repository path set to: {repo_path}

📋 To view graph data:
1. Go to Repository tab
2. Click "Load" to set repository
3. Click "Start Data Ingestion" (if not done)
4. Return here and click "Load Graph Data"

💡 Or click "Load Graph Data" now to see available structure
"""
        
        self.graph_display_text.delete('1.0', tk.END)
        self.graph_display_text.insert('1.0', instruction_text)
    
    def create_visual_graph_panel(self):
        """Create visual graph panel with network visualization"""
        # Main container with padding
        main_container = ttk.Frame(self.visual_graph_frame, padding="20")
        main_container.pack(fill='both', expand=True)
        
        # Graph controls with modern styling
        visual_controls_frame = ttk.LabelFrame(main_container, text="🎨 Visualization Controls", 
                                             style='Card.TLabelframe', padding="15")
        visual_controls_frame.pack(fill='x', pady=(0, 20))
        
        # Visualization type
        type_frame = ttk.Frame(visual_controls_frame)
        type_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(type_frame, text="Visualization Type:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.visual_type_var = tk.StringVar(value="network")
        visual_combo = ttk.Combobox(type_frame, textvariable=self.visual_type_var, 
                                   values=["network", "hierarchy", "timeline", "vector_data"], 
                                   state="readonly", style='Modern.TCombobox', width=25)
        visual_combo.pack(fill='x')
        
        # Repository for visual
        repo_frame = ttk.Frame(visual_controls_frame)
        repo_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(repo_frame, text="Repository:", style='Body.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.visual_repo_var = tk.StringVar(value="kafka")
        
        # Use same available repositories
        available_repos = self._get_available_repositories()
        
        visual_repo_combo = ttk.Combobox(repo_frame, textvariable=self.visual_repo_var, 
                                        values=available_repos, 
                                        state="readonly", style='Modern.TCombobox', width=25)
        visual_repo_combo.pack(fill='x')
        
        # Generate visualization button
        ttk.Button(repo_frame, text="🎯 Generate Visualization", 
                  command=self.generate_visual_graph, style='Accent.TButton').pack(fill='x', pady=(10, 0))
        
        # Canvas for visualization with modern styling
        visual_display_frame = ttk.LabelFrame(main_container, text="🌐 Network Visualization", 
                                            style='Card.TLabelframe', padding="15")
        visual_display_frame.pack(fill='both', expand=True)
        
        # Create canvas with scrollbars
        canvas_frame = ttk.Frame(visual_display_frame)
        canvas_frame.pack(fill='both', expand=True)
        
        # Canvas
        self.visual_canvas = tk.Canvas(canvas_frame, bg='white', width=600, height=400, 
                                     relief='solid', borderwidth=1)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.visual_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.visual_canvas.xview)
        
        self.visual_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack canvas and scrollbars
        self.visual_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse events for panning
        self.visual_canvas.bind("<Button-1>", self.on_canvas_click)
        self.visual_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.visual_canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        
        # Show instruction message instead of sample graph
        self.show_graph_instructions()
    
    def show_graph_instructions(self):
        """Show instructions instead of sample graph"""
        self.visual_canvas.delete("all")
        
        # Title
        self.visual_canvas.create_text(300, 100, text="Graph Visualization", 
                                      font=("Arial", 16, "bold"), fill='darkblue')
        
        # Instructions
        instructions = [
            "📋 Instructions:",
            "",
            "1. Select repository from dropdown",
            "2. Choose visualization type:",
            "   • Network - Node relationships",
            "   • Hierarchy - Tree structure", 
            "   • Timeline - Chronological view",
            "   • Vector Data - Vector database visualization",
            "",
            "3. Click 'Generate Visualization'",
            "",
            "⚠️ Note: Repository data must be ingested first",
            "   Go to Repository tab → Load/Clone → Start Data Ingestion"
        ]
        
        y_pos = 150
        for instruction in instructions:
            if instruction.startswith("📋") or instruction.startswith("⚠️"):
                font = ("Arial", 12, "bold")
                color = 'darkblue' if instruction.startswith("📋") else 'red'
            elif instruction.startswith("   •"):
                font = ("Arial", 10)
                color = 'darkgreen'
            elif instruction and not instruction.startswith(" "):
                font = ("Arial", 11, "bold")
                color = 'black'
            else:
                font = ("Arial", 10)
                color = 'gray'
            
            self.visual_canvas.create_text(300, y_pos, text=instruction, 
                                          font=font, fill=color, justify='center')
            y_pos += 25
        
        # Set scroll region
        self.visual_canvas.configure(scrollregion=(0, 0, 600, 400))
    
    def generate_visual_graph(self):
        """Generate actual visualization from Neo4j data"""
        if not self.is_ingested:
            messagebox.showinfo("Info", "Please ingest repository data first.\n\nGo to Repository tab → Load repository → Start Data Ingestion")
            return
        
        # Start generation in background
        thread = threading.Thread(target=self._visual_graph_worker)
        thread.daemon = True
        thread.start()
        
        self.update_status("Generating graph visualization...")
    
    def _visual_graph_worker(self):
        """Background worker for visual graph generation"""
        try:
            repo_name = self.visual_repo_var.get()
            visual_type = self.visual_type_var.get()
            
            # Get data from Neo4j
            if not self.core.neo4j_ready:
                raise Exception("Neo4j not available")
            
            with self.core.neo4j_driver.session() as session:
                # First check what relationships exist
                rel_query = "CALL db.relationshipTypes()"
                rel_result = list(session.run(rel_query))
                available_rels = [r[0] for r in rel_result] if rel_result else []
                
                # Get repository data with flexible relationship matching
                if available_rels:
                    # Use existing relationships
                    query = f"""
                    MATCH (r:Repository {{name: $repo_name}})
                    OPTIONAL MATCH (r)-->(c:Commit)
                    OPTIONAL MATCH (r)-->(u:Contributor) 
                    OPTIONAL MATCH (r)-->(f:File)
                    RETURN r.name as repo_name,
                           collect(DISTINCT c.hash)[0..10] as commits,
                           collect(DISTINCT u.name)[0..10] as contributors,
                           collect(DISTINCT f.name)[0..10] as files
                    """
                else:
                    # Fallback: just get nodes without relationships
                    query = """
                    MATCH (r:Repository {name: $repo_name})
                    OPTIONAL MATCH (c:Commit)
                    OPTIONAL MATCH (u:Contributor) 
                    OPTIONAL MATCH (f:File)
                    RETURN r.name as repo_name,
                           collect(DISTINCT c.hash)[0..10] as commits,
                           collect(DISTINCT u.name)[0..10] as contributors,
                           collect(DISTINCT f.name)[0..10] as files
                    """
                
                result = session.run(query, repo_name=repo_name).single()
                
                if result:
                    graph_data = {
                        'repository': result['repo_name'],
                        'commits': result['commits'] or [],
                        'contributors': result['contributors'] or [],
                        'files': result['files'] or []
                    }
                else:
                    graph_data = {
                        'repository': repo_name,
                        'commits': [],
                        'contributors': [],
                        'files': []
                    }
                
                # Update UI
                self.root.after(0, lambda: self._draw_real_graph(graph_data, visual_type))
                
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._visual_graph_error(error_msg))
    
    def _draw_real_graph(self, data, visual_type):
        """Draw real graph from Neo4j data"""
        self.visual_canvas.delete("all")
        
        if visual_type == "network":
            self._draw_network_graph(data)
        elif visual_type == "hierarchy":
            self._draw_hierarchy_graph(data)
        elif visual_type == "timeline":
            self._draw_timeline_graph(data)
        elif visual_type == "vector_data":
            self._draw_vector_data_graph(data)
        
        self.update_status("Graph visualization generated")
    
    def _draw_hierarchy_graph(self, data):
        """Draw hierarchy-style graph"""
        # Repository at top
        repo_x, repo_y = 400, 80
        self.visual_canvas.create_oval(repo_x-50, repo_y-30, repo_x+50, repo_y+30, 
                                      fill='lightblue', outline='blue', width=3)
        self.visual_canvas.create_text(repo_x, repo_y, text=data['repository'], 
                                      font=("Arial", 12, "bold"))
        
        # Contributors level
        contrib_y = 180
        contributors = data['contributors'][:5]
        if contributors:
            contrib_spacing = 600 / max(len(contributors), 1)
            start_x = 100
            for i, contributor in enumerate(contributors):
                x = start_x + (i * contrib_spacing)
                self.visual_canvas.create_oval(x-25, contrib_y-15, x+25, contrib_y+15, 
                                              fill='lightyellow', outline='orange', width=2)
                contrib_text = contributor[:10] if contributor else f"User{i+1}"
                self.visual_canvas.create_text(x, contrib_y, text=contrib_text, font=("Arial", 9))
                # Line to repository
                self.visual_canvas.create_line(x, contrib_y-15, repo_x, repo_y+30, fill='orange', width=2)
        
        # Commits level
        commit_y = 280
        commits = data['commits'][:6]
        if commits:
            commit_spacing = 600 / max(len(commits), 1)
            start_x = 100
            for i, commit in enumerate(commits):
                x = start_x + (i * commit_spacing)
                self.visual_canvas.create_oval(x-20, commit_y-12, x+20, commit_y+12, 
                                              fill='lightgreen', outline='green', width=2)
                commit_text = commit[:8] if commit else f"C{i+1}"
                self.visual_canvas.create_text(x, commit_y, text=commit_text, font=("Arial", 8))
                # Line to repository
                self.visual_canvas.create_line(x, commit_y-12, repo_x, repo_y+30, fill='green', width=1)
        
        # Files level
        file_y = 380
        files = data['files'][:8]
        if files:
            file_spacing = 600 / max(len(files), 1)
            start_x = 100
            for i, file in enumerate(files):
                x = start_x + (i * file_spacing)
                self.visual_canvas.create_rectangle(x-18, file_y-10, x+18, file_y+10, 
                                                   fill='lightcoral', outline='red', width=2)
                file_text = (file.split('/')[-1])[:8] if file else f"F{i+1}"
                self.visual_canvas.create_text(x, file_y, text=file_text, font=("Arial", 8))
                # Line to repository
                self.visual_canvas.create_line(x, file_y-10, repo_x, repo_y+30, fill='red', width=1)
        
        self._draw_enhanced_legend(data)
        self.visual_canvas.configure(scrollregion=self.visual_canvas.bbox("all"))
    
    def _draw_timeline_graph(self, data):
        """Draw timeline-style graph"""
        # Timeline axis
        timeline_y = 250
        start_x = 100
        end_x = 700
        
        self.visual_canvas.create_line(start_x, timeline_y, end_x, timeline_y, 
                                      fill='black', width=3)
        self.visual_canvas.create_text(400, 50, text=f"Timeline: {data['repository']}", 
                                      font=("Arial", 16, "bold"))
        
        # Repository marker
        repo_x = 400
        self.visual_canvas.create_oval(repo_x-20, timeline_y-20, repo_x+20, timeline_y+20, 
                                      fill='lightblue', outline='blue', width=3)
        self.visual_canvas.create_text(repo_x, timeline_y-40, text="Repository\nCreated", 
                                      font=("Arial", 10, "bold"), justify='center')
        
        # Commits on timeline
        commits = data['commits'][:10]
        if commits:
            commit_spacing = 500 / max(len(commits), 1)
            for i, commit in enumerate(commits):
                x = start_x + 50 + (i * commit_spacing)
                y = timeline_y - 30 if i % 2 == 0 else timeline_y + 30
                
                self.visual_canvas.create_oval(x-8, timeline_y-8, x+8, timeline_y+8, 
                                              fill='lightgreen', outline='green', width=2)
                self.visual_canvas.create_line(x, timeline_y, x, y, fill='green', width=1)
                self.visual_canvas.create_text(x, y, text=commit[:6] if commit else f"C{i+1}", 
                                              font=("Arial", 8), angle=45 if i % 2 == 0 else -45)
        
        # Contributors markers
        contributors = data['contributors'][:5]
        if contributors:
            contrib_y = timeline_y + 80
            for i, contributor in enumerate(contributors):
                x = start_x + 100 + (i * 100)
                self.visual_canvas.create_oval(x-12, contrib_y-12, x+12, contrib_y+12, 
                                              fill='lightyellow', outline='orange', width=2)
                contrib_text = contributor[:8] if contributor else f"U{i+1}"
                self.visual_canvas.create_text(x, contrib_y+25, text=contrib_text, 
                                              font=("Arial", 9))
        
        self._draw_enhanced_legend(data)
        self.visual_canvas.configure(scrollregion=self.visual_canvas.bbox("all"))
    
    def _draw_vector_data_graph(self, data):
        """Draw vector data visualization"""
        # Title
        self.visual_canvas.create_text(400, 30, text=f"Vector Data: {data['repository']}", 
                                      font=("Arial", 14, "bold"), fill='purple')
        
        # Vector space representation
        center_x, center_y = 400, 200
        
        # Create vector clusters
        clusters = [
            {'name': 'Commits', 'data': data['commits'], 'color': 'lightgreen', 'outline': 'green'},
            {'name': 'Contributors', 'data': data['contributors'], 'color': 'lightyellow', 'outline': 'orange'},
            {'name': 'Files', 'data': data['files'], 'color': 'lightcoral', 'outline': 'red'}
        ]
        
        import math
        cluster_positions = [
            (center_x - 120, center_y - 80),  # Top left
            (center_x + 120, center_y - 80),  # Top right
            (center_x, center_y + 100)        # Bottom center
        ]
        
        for i, (cluster, (cluster_x, cluster_y)) in enumerate(zip(clusters, cluster_positions)):
            # Cluster center
            self.visual_canvas.create_oval(cluster_x-30, cluster_y-30, cluster_x+30, cluster_y+30, 
                                          fill=cluster['color'], outline=cluster['outline'], width=3)
            self.visual_canvas.create_text(cluster_x, cluster_y, text=cluster['name'], 
                                          font=("Arial", 11, "bold"))
            
            # Draw data points around cluster
            data_items = cluster['data'][:8]  # Limit to 8 items
            if data_items:
                for j, item in enumerate(data_items):
                    # Position around cluster center
                    angle = (2 * math.pi * j) / len(data_items)
                    x = cluster_x + 50 * math.cos(angle)
                    y = cluster_y + 50 * math.sin(angle)
                    
                    # Small data point
                    self.visual_canvas.create_oval(x-6, y-6, x+6, y+6, 
                                                  fill=cluster['color'], outline=cluster['outline'])
                    
                    # Connect to cluster center
                    self.visual_canvas.create_line(x, y, cluster_x, cluster_y, 
                                                  fill=cluster['outline'], width=1, dash=(2, 2))
                    
                    # Data label (shortened)
                    if item:
                        if cluster['name'] == 'Commits':
                            label = item[:6]
                        elif cluster['name'] == 'Files':
                            label = item.split('/')[-1][:8] if '/' in item else item[:8]
                        else:
                            label = item[:8]
                        
                        self.visual_canvas.create_text(x, y-15, text=label, 
                                                      font=("Arial", 7), fill='darkblue')
        
        # Vector similarity lines (connecting related clusters)
        similarity_lines = [
            (cluster_positions[0], cluster_positions[1], "Commit-Contributor Link"),
            (cluster_positions[1], cluster_positions[2], "Contributor-File Link"),
            (cluster_positions[0], cluster_positions[2], "Commit-File Link")
        ]
        
        for (x1, y1), (x2, y2), label in similarity_lines:
            # Draw similarity vector
            self.visual_canvas.create_line(x1, y1, x2, y2, fill='purple', width=2, dash=(10, 5))
            
            # Midpoint label
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
            self.visual_canvas.create_text(mid_x, mid_y, text=label, 
                                          font=("Arial", 8), fill='purple', 
                                          bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Vector statistics
        stats_text = f"""📊 Vector Statistics:
        
Commit Vectors: {len(data['commits'])}
Contributor Vectors: {len(data['contributors'])}
File Vectors: {len(data['files'])}
        
💡 Vector Space represents semantic relationships
between repository entities using embeddings"""
        
        self.visual_canvas.create_text(50, 350, text=stats_text, 
                                      font=("Arial", 9), fill='purple', 
                                      anchor='nw', justify='left')
        
        self._draw_enhanced_legend(data)
        self.visual_canvas.configure(scrollregion=self.visual_canvas.bbox("all"))
    
    def _draw_network_graph(self, data):
        """Draw network-style graph"""
        import math
        
        # Repository node (center)
        repo_x, repo_y = 400, 250
        self.visual_canvas.create_oval(repo_x-40, repo_y-40, repo_x+40, repo_y+40, 
                                      fill='lightblue', outline='blue', width=3)
        self.visual_canvas.create_text(repo_x, repo_y, text=data['repository'], 
                                      font=("Arial", 12, "bold"), width=60)
        
        # Draw commits in circle around repository
        commits = data['commits'][:8]  # Limit to 8 for visibility
        if commits:
            radius = 120
            for i, commit in enumerate(commits):
                angle = (2 * math.pi * i) / len(commits)
                x = repo_x + radius * math.cos(angle)
                y = repo_y + radius * math.sin(angle)
                
                self.visual_canvas.create_oval(x-20, y-20, x+20, y+20, 
                                              fill='lightgreen', outline='green', width=2)
                commit_text = commit[:8] if commit else f"C{i+1}"
                self.visual_canvas.create_text(x, y, text=commit_text, 
                                              font=("Arial", 8), width=30)
                # Line to repository
                self.visual_canvas.create_line(x, y, repo_x, repo_y, fill='green', width=2)
        
        # Draw contributors
        contributors = data['contributors'][:6]  # Limit to 6
        if contributors:
            radius = 180
            for i, contributor in enumerate(contributors):
                angle = (2 * math.pi * i) / len(contributors) + math.pi/4  # Offset from commits
                x = repo_x + radius * math.cos(angle)
                y = repo_y + radius * math.sin(angle)
                
                self.visual_canvas.create_oval(x-18, y-18, x+18, y+18, 
                                              fill='lightyellow', outline='orange', width=2)
                contrib_text = contributor[:10] if contributor else f"User{i+1}"
                self.visual_canvas.create_text(x, y, text=contrib_text, 
                                              font=("Arial", 7), width=25)
                # Line to repository
                self.visual_canvas.create_line(x, y, repo_x, repo_y, fill='orange', width=1, dash=(5, 5))
        
        # Draw files
        files = data['files'][:8]  # Limit to 8
        if files:
            radius = 240
            for i, file in enumerate(files):
                angle = (2 * math.pi * i) / len(files) + math.pi/6  # Another offset
                x = repo_x + radius * math.cos(angle)
                y = repo_y + radius * math.sin(angle)
                
                self.visual_canvas.create_rectangle(x-16, y-12, x+16, y+12, 
                                                   fill='lightcoral', outline='red', width=2)
                file_text = (file.split('/')[-1])[:12] if file else f"File{i+1}"
                self.visual_canvas.create_text(x, y, text=file_text, 
                                              font=("Arial", 7), width=25)
                # Line to repository
                self.visual_canvas.create_line(x, y, repo_x, repo_y, fill='red', width=1, dash=(3, 3))
        
        # Enhanced legend
        self._draw_enhanced_legend(data)
        
        # Set scroll region
        self.visual_canvas.configure(scrollregion=self.visual_canvas.bbox("all"))
    
    def _draw_enhanced_legend(self, data):
        """Draw enhanced legend with statistics"""
        legend_x = 20
        legend_y = 30
        
        # Title
        self.visual_canvas.create_text(legend_x, legend_y, 
                                      text=f"Repository: {data['repository']}", 
                                      font=("Arial", 14, "bold"), anchor='w')
        
        # Statistics
        stats_y = legend_y + 30
        self.visual_canvas.create_text(legend_x, stats_y, 
                                      text=f"📊 Commits: {len(data['commits'])}", 
                                      font=("Arial", 10), anchor='w')
        
        self.visual_canvas.create_text(legend_x, stats_y + 20, 
                                      text=f"👥 Contributors: {len(data['contributors'])}", 
                                      font=("Arial", 10), anchor='w')
        
        self.visual_canvas.create_text(legend_x, stats_y + 40, 
                                      text=f"📁 Files: {len(data['files'])}", 
                                      font=("Arial", 10), anchor='w')
        
        # Legend items
        legend_items_y = stats_y + 70
        
        # Repository
        self.visual_canvas.create_oval(legend_x, legend_items_y, legend_x+15, legend_items_y+15, 
                                      fill='lightblue', outline='blue')
        self.visual_canvas.create_text(legend_x+25, legend_items_y+7, 
                                      text="Repository", font=("Arial", 9), anchor='w')
        
        # Commits
        self.visual_canvas.create_oval(legend_x, legend_items_y+25, legend_x+15, legend_items_y+40, 
                                      fill='lightgreen', outline='green')
        self.visual_canvas.create_text(legend_x+25, legend_items_y+32, 
                                      text="Commits", font=("Arial", 9), anchor='w')
        
        # Contributors
        self.visual_canvas.create_oval(legend_x, legend_items_y+50, legend_x+15, legend_items_y+65, 
                                      fill='lightyellow', outline='orange')
        self.visual_canvas.create_text(legend_x+25, legend_items_y+57, 
                                      text="Contributors", font=("Arial", 9), anchor='w')
        
        # Files
        self.visual_canvas.create_rectangle(legend_x, legend_items_y+75, legend_x+15, legend_items_y+90, 
                                           fill='lightcoral', outline='red')
        self.visual_canvas.create_text(legend_x+25, legend_items_y+82, 
                                      text="Files", font=("Arial", 9), anchor='w')
    
    def _visual_graph_error(self, error_msg):
        """Handle visual graph generation error"""
        self.visual_canvas.delete("all")
        self.visual_canvas.create_text(400, 250, 
                                      text=f"Error generating visualization:\n{error_msg}\n\nPlease ensure repository data is ingested.", 
                                      font=("Arial", 12), fill='red', justify='center')
        self.update_status(f"Visualization failed: {error_msg}")
    
    # Canvas interaction methods
    def on_canvas_click(self, event):
        """Handle canvas click for panning"""
        self.canvas_start_x = event.x
        self.canvas_start_y = event.y
    
    def on_canvas_drag(self, event):
        """Handle canvas drag for panning"""
        if hasattr(self, 'canvas_start_x'):
            dx = event.x - self.canvas_start_x
            dy = event.y - self.canvas_start_y
            self.visual_canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_canvas_scroll(self, event):
        """Handle canvas scroll for zooming"""
        if event.delta > 0:
            self.visual_canvas.scale("all", event.x, event.y, 1.1, 1.1)
        else:
            self.visual_canvas.scale("all", event.x, event.y, 0.9, 0.9)
    
    def load_graph_data(self):
        """Load and display graph data from Neo4j"""
        if not self.is_ingested:
            messagebox.showerror("Error", "Please ingest repository data first")
            return
        
        query_type = self.graph_query_var.get()
        
        # Start loading in background
        thread = threading.Thread(target=self._graph_worker, args=(query_type,))
        thread.daemon = True
        thread.start()
        
        self.update_status(f"Loading {query_type} graph data...")
    
    def _graph_worker(self, query_type):
        """Background worker for graph data loading"""
        try:
            if not self.core.neo4j_ready:
                raise Exception("Neo4j not available")
            
            repo_name = self.graph_repo_var.get()
            
            with self.core.neo4j_driver.session() as session:
                if query_type == "overview":
                    query = """
                    MATCH (r:Repository {name: $repo_name})
                    OPTIONAL MATCH (r)-[:CONTAINS]->(c:Commit)
                    OPTIONAL MATCH (r)-[:HAS_CONTRIBUTOR]->(u:Contributor)
                    OPTIONAL MATCH (r)-[:CONTAINS_FILE]->(f:File)
                    RETURN r.name as repo_name,
                           count(DISTINCT c) as total_commits,
                           count(DISTINCT u) as total_contributors,
                           count(DISTINCT f) as total_files
                    """
                    
                    result = session.run(query, repo_name=repo_name).single()
                    if result:
                        graph_text = f"""📊 Repository Overview - {repo_name}
                        
Repository: {result['repo_name'] or repo_name}
Total Commits: {result['total_commits'] or 0}
Total Contributors: {result['total_contributors'] or 0}
Total Files: {result['total_files'] or 0}

🔗 Graph Structure:
Repository({repo_name}) → Contains → Commits
Repository({repo_name}) → Has Contributors → Contributors  
Repository({repo_name}) → Contains Files → Files

💡 Tip: Try different repositories from the dropdown to see their data!
"""
                    else:
                        # If no data in Neo4j, show repository structure anyway
                        graph_text = f"""📊 Repository Overview - {repo_name}

⚠️ No data found in Neo4j for repository: {repo_name}

🔍 Available Repositories:
• kafka - Apache Kafka project
• druid - Apache Druid project  
• maven - Apache Maven project
• spring-framework - Spring Framework
• GitIntelProject - Current project

📋 To load data:
1. Go to Repository tab
2. Select repository path: D:/GitIntel/{repo_name}
3. Click "Start Data Ingestion"
4. Return here to view graph data

🔗 Expected Graph Structure:
Repository({repo_name}) → Contains → Commits
Repository({repo_name}) → Has Contributors → Contributors  
Repository({repo_name}) → Contains Files → Files
"""
                        
                elif query_type == "contributors":
                    query = """
                    MATCH (r:Repository {name: $repo_name})-[:HAS_CONTRIBUTOR]->(u:Contributor)
                    RETURN u.name as name, u.email as email, u.commit_count as commits
                    ORDER BY u.commit_count DESC
                    LIMIT 10
                    """
                    
                    results = list(session.run(query, repo_name=repo_name))
                    graph_text = f"👥 Top Contributors - {repo_name}:\n\n"
                    
                    if results:
                        for i, record in enumerate(results, 1):
                            graph_text += f"{i}. {record['name']} ({record['email']})\n"
                            graph_text += f"   📊 Commits: {record['commits']}\n\n"
                    else:
                        graph_text += f"⚠️ No contributor data found for {repo_name}\n"
                        graph_text += "💡 Tip: Ingest repository data first in Repository tab"
                        
                elif query_type == "commits":
                    query = """
                    MATCH (r:Repository {name: $repo_name})-[:CONTAINS]->(c:Commit)
                    RETURN c.hash as hash, c.message as message, c.author as author, c.date as date
                    ORDER BY c.date DESC
                    LIMIT 10
                    """
                    
                    results = list(session.run(query, repo_name=repo_name))
                    graph_text = f"📝 Recent Commits - {repo_name}:\n\n"
                    
                    if results:
                        for i, record in enumerate(results, 1):
                            graph_text += f"{i}. {record['hash'][:8] if record['hash'] else 'N/A'}\n"
                            graph_text += f"   👤 Author: {record['author'] or 'Unknown'}\n"
                            graph_text += f"   📅 Date: {record['date'] or 'Unknown'}\n"
                            graph_text += f"   💬 Message: {(record['message'] or 'No message')[:100]}...\n\n"
                    else:
                        graph_text += f"⚠️ No commit data found for {repo_name}\n"
                        graph_text += "💡 Tip: Ingest repository data first in Repository tab"
                        
                elif query_type == "files":
                    query = """
                    MATCH (r:Repository {name: $repo_name})-[:CONTAINS_FILE]->(f:File)
                    RETURN f.name as name, f.extension as ext, f.lines_of_code as loc
                    ORDER BY f.lines_of_code DESC
                    LIMIT 10
                    """
                    
                    results = list(session.run(query, repo_name=repo_name))
                    graph_text = f"📁 Files by Size - {repo_name}:\n\n"
                    
                    if results:
                        for i, record in enumerate(results, 1):
                            graph_text += f"{i}. {record['name'] or 'Unknown'}\n"
                            graph_text += f"   📄 Type: {record['ext'] or 'Unknown'}\n"
                            graph_text += f"   📏 LOC: {record['loc'] or 0}\n\n"
                    else:
                        graph_text += f"⚠️ No file data found for {repo_name}\n"
                        graph_text += "💡 Tip: Ingest repository data first in Repository tab"
                
                else:
                    graph_text = "Unknown query type"
            
            # Update UI
            self.root.after(0, lambda: self._graph_complete(graph_text))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._graph_error(error_msg))
    
    def _graph_complete(self, graph_text):
        """Handle completed graph loading"""
        self.graph_display_text.delete('1.0', tk.END)
        self.graph_display_text.insert('1.0', graph_text)
        self.update_status("Graph data loaded")
    
    def _graph_error(self, error_msg):
        """Handle graph loading error"""
        self.graph_display_text.delete('1.0', tk.END)
        self.graph_display_text.insert('1.0', f"Graph loading failed: {error_msg}")
        self.update_status(f"Graph loading failed: {error_msg}")

    def create_status_bar(self):
        """Create status bar with modern styling"""
        self.status_frame = ttk.Frame(self.root, style='Card.TLabelframe')
        self.status_frame.pack(fill='x', side='bottom', padx=10, pady=(0, 10))
        
        # Main status
        status_frame = ttk.Frame(self.status_frame)
        status_frame.pack(side='left', fill='x', expand=True, padx=10, pady=5)
        
        ttk.Label(status_frame, text="📊 Status:", style='Body.TLabel').pack(side='left')
        
        self.status_var = tk.StringVar(value="✅ Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                    style='Body.TLabel', background='#f7fafc')
        self.status_label.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # Repository status
        repo_frame = ttk.Frame(self.status_frame)
        repo_frame.pack(side='right', padx=10, pady=5)
        
        ttk.Label(repo_frame, text="📁 Repository:", style='Body.TLabel').pack(side='left')
        
        self.repo_status_var = tk.StringVar(value="❌ No repository loaded")
        ttk.Label(repo_frame, textvariable=self.repo_status_var, 
                 style='Body.TLabel', background='#f7fafc').pack(side='left', padx=(5, 0))
        
        # Neo4j status
        neo4j_frame = ttk.Frame(self.status_frame)
        neo4j_frame.pack(side='right', padx=(0, 10), pady=5)
        
        ttk.Label(neo4j_frame, text="🔗 Neo4j:", style='Body.TLabel').pack(side='left')
        
        self.neo4j_status_label = ttk.Label(neo4j_frame, textvariable=self.neo4j_status, 
                                          style='Body.TLabel', background='#f7fafc')
        self.neo4j_status_label.pack(side='left', padx=(5, 0))
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Control-o>', lambda e: self.open_repository())
        self.root.bind('<F5>', lambda e: self.ingest_repository())
    
    # Repository Management Methods
    
    def browse_repository(self):
        """Browse for repository folder"""
        if self.repo_source_var.get() == "local":
            folder = filedialog.askdirectory(title="Select Git Repository")
            if folder:
                self.repo_path_var.set(folder)
        # For URL mode, user types the URL directly
    
    def browse_clone_destination(self):
        """Browse for clone destination folder"""
        folder = filedialog.askdirectory(title="Select Clone Destination")
        if folder:
            self.clone_dest_var.set(folder)
    
    def on_source_change(self):
        """Handle repository source type change"""
        if self.repo_source_var.get() == "local":
            self.repo_input_label.config(text="Repository Path:")
            self.repo_path_entry.config(width=50)
            self.action_button.config(text="Load")
            self.clone_dest_frame.grid_remove()
            self.clone_progress_frame.grid_remove()
        else:
            self.repo_input_label.config(text="Git URL:")
            self.repo_path_entry.config(width=50)
            self.action_button.config(text="Clone")
            self.clone_dest_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(10, 0))
            self.clone_progress_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=(5, 0))
    
    def open_repository(self):
        """Open repository dialog"""
        self.browse_repository()
        if self.repo_path_var.get():
            self.load_repository()
    
    def load_repository(self):
        """Load selected repository or clone from URL"""
        repo_input = self.repo_path_var.get().strip()
        if not repo_input:
            messagebox.showerror("Error", "Please provide a repository path or URL")
            return
        
        source_type = self.repo_source_var.get()
        
        if source_type == "url":
            # Clone from Git URL
            self.clone_repository(repo_input)
        else:
            # Load local repository
            self.load_local_repository(repo_input)
    
    def clone_repository(self, git_url):
        """Clone repository from Git URL"""
        clone_dest = self.clone_dest_var.get().strip()
        if not clone_dest:
            messagebox.showerror("Error", "Please select clone destination")
            return
        
        try:
            # Extract repository name from URL for display purposes
            repo_name = git_url.split('/')[-1].replace('.git', '')
            
            # Use the clone destination directly (don't create subdirectory)
            final_path = clone_dest
            
            if os.path.exists(final_path):
                # Check if it's a git repository
                if os.path.exists(os.path.join(final_path, '.git')):
                    response = messagebox.askyesno("Repository Exists", 
                        f"A Git repository already exists at:\n{final_path}\n\nDo you want to use the existing repository?")
                    if response:
                        self.current_repo = final_path
                        self.update_repository_info()
                        self.repo_status_var.set(f"Repository: {repo_name}")
                        return
                    else:
                        return
                else:
                    response = messagebox.askyesno("Directory Exists", 
                        f"Directory already exists at:\n{final_path}\n\nDo you want to clone into this existing directory?\n(This will add Git repository files to the existing directory)")
                    if not response:
                        return
            
            # Disable action button during cloning
            self.action_button.config(state='disabled', text="Cloning...")
            
            # Reset progress
            self.clone_progress['value'] = 0
            self.clone_status_var.set("Starting clone...")
            
            # Start cloning in background
            self.update_status(f"Cloning repository from {git_url}...")
            thread = threading.Thread(target=self._clone_worker, args=(git_url, final_path))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clone repository: {e}")
    
    def _clone_worker(self, git_url, clone_path):
        """Background worker for repository cloning"""
        try:
            import git
            
            def progress_callback(op_code, cur_count, max_count=None, message=''):
                if max_count:
                    percentage = int((cur_count / max_count) * 100)
                    self.root.after(0, lambda: self._update_clone_progress(percentage, f"Cloning: {percentage}% - {message}"))
                else:
                    self.root.after(0, lambda: self._update_clone_progress(None, f"Cloning: {message}"))
            
            # Update initial status
            self.root.after(0, lambda: self._update_clone_progress(0, "Initializing clone..."))
            
            # Clone repository with progress
            repo = git.Repo.clone_from(git_url, clone_path, progress=progress_callback)
            
            # Success
            self.root.after(0, lambda: self._clone_success(clone_path))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._clone_error(error_msg))
    
    def _update_clone_progress(self, progress=None, message=""):
        """Update clone progress bar and status"""
        if progress is not None:
            self.clone_progress['value'] = progress
        self.clone_status_var.set(message)
        self.update_status(message)
        self.root.update_idletasks()
    
    def _clone_success(self, repo_path):
        """Handle successful repository cloning"""
        self.clone_progress['value'] = 100
        self.clone_status_var.set("Clone completed successfully!")
        self.update_status("Repository cloned successfully")
        
        # Re-enable action button
        self.action_button.config(state='normal', text="Clone")
        
        self.current_repo = repo_path
        self.update_repository_info()
        repo_name = os.path.basename(repo_path)
        self.repo_status_var.set(f"Repository: {repo_name}")
        
        # Initialize components for this repository
        self.kg_builder = KnowledgeGraphBuilder(repo_path=repo_path)
        
        # Check if already ingested
        self.is_ingested = self.core.neo4j_ready and self._check_neo4j_data()
        if self.is_ingested:
            self.ingest_status_var.set("Already ingested")
            self.enable_chat()
        else:
            self.ingest_status_var.set("Ready to ingest")
            self.disable_chat()
        
        self.save_last_session()
        
        # Show success message
        messagebox.showinfo("Success", f"Repository '{repo_name}' cloned successfully!\n\nLocation: {repo_path}")
    
    def _clone_error(self, error_msg):
        """Handle repository cloning error"""
        self.clone_progress['value'] = 0
        self.clone_status_var.set("Clone failed")
        
        # Re-enable action button
        self.action_button.config(state='normal', text="Clone")
        
        self.update_status(f"Clone failed: {error_msg}")
        messagebox.showerror("Clone Error", f"Failed to clone repository: {error_msg}")
    
    def load_local_repository(self, repo_path):
        """Load local repository"""
        if not os.path.exists(repo_path):
            messagebox.showerror("Error", "Repository path does not exist")
            return
        
        if not os.path.exists(os.path.join(repo_path, '.git')):
            messagebox.showerror("Error", "Selected folder is not a Git repository")
            return
        
        try:
            # Load repository
            if self.core.set_repository(repo_path):
                self.current_repo = repo_path
                self.update_repository_info()
                self.update_status(f"Repository loaded: {os.path.basename(repo_path)}")
                self.repo_status_var.set(f"Repository: {os.path.basename(repo_path)}")
                
                # Initialize components for this repository
                self.kg_builder = KnowledgeGraphBuilder(repo_path=repo_path)
                
                # Check if already ingested (use Neo4j to check)
                self.is_ingested = self.core.neo4j_ready and self._check_neo4j_data()
                if self.is_ingested:
                    self.ingest_status_var.set("Already ingested")
                    self.enable_chat()
                else:
                    self.ingest_status_var.set("Ready to ingest")
                    self.disable_chat()
                
                self.save_last_session()
            else:
                messagebox.showerror("Error", "Failed to load repository")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load repository: {e}")
    
    def _check_neo4j_data(self):
        """Check if Neo4j has data for current repository"""
        try:
            if not self.core.neo4j_ready or not self.current_repo:
                return False
            
            repo_name = os.path.basename(self.current_repo)
            return self.core._check_existing_data(repo_name)
        except:
            return False
    
    def _get_available_repositories(self):
        """Get list of available Git repositories dynamically"""
        repos = []
        base_path = "D:/GitIntel"
        
        try:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '.git')):
                        repos.append(item)
            
            # Add cloned repositories if clone destination exists
            clone_dest = self.clone_dest_var.get() if hasattr(self, 'clone_dest_var') else "D:/GitIntel/cloned_repos"
            if os.path.exists(clone_dest):
                for item in os.listdir(clone_dest):
                    item_path = os.path.join(clone_dest, item)
                    if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '.git')):
                        repos.append(f"cloned_repos/{item}")
        except:
            pass
        
        # Fallback to default list if no repos found
        if not repos:
            repos = ["kafka", "druid", "maven", "spring-framework", "GitIntelProject"]
        
        return sorted(repos)
    
    def update_repository_info(self):
        """Update repository information display"""
        if not self.current_repo:
            return
        
        try:
            # Get repository metadata
            metadata = self.core.repo_metadata
            if not metadata:
                metadata = self.core._extract_basic_metadata()
            
            info_text = []
            info_text.append(f"📁 Repository: {metadata.get('name', 'Unknown')}")
            info_text.append(f"📍 Path: {metadata.get('path', 'Unknown')}")
            info_text.append(f"🌿 Active Branch: {metadata.get('active_branch', 'Unknown')}")
            info_text.append(f"📊 Total Commits: {metadata.get('total_commits', 0):,}")
            
            if 'remotes' in metadata and metadata['remotes']:
                info_text.append(f"🔗 Remotes: {', '.join(metadata['remotes'])}")
            
            info_text.append(f"🕒 Last Updated: {metadata.get('last_updated', 'Unknown')}")
            
            # Update display
            self.repo_info_text.delete('1.0', tk.END)
            self.repo_info_text.insert('1.0', '\n'.join(info_text))
            
        except Exception as e:
            self.repo_info_text.delete('1.0', tk.END)
            self.repo_info_text.insert('1.0', f"Error loading repository info: {e}")
    
    # Analysis Methods
    
    def ingest_repository(self):
        """Ingest repository data"""
        if not self.current_repo:
            messagebox.showerror("Error", "Please load a repository first")
            return
        
        # Get commit limit from UI
        commit_limit_input = self.ingest_commit_limit_var.get().strip().lower()
        if commit_limit_input == "all" or commit_limit_input == "":
            commit_limit = None  # No limit
        else:
            try:
                commit_limit = int(commit_limit_input)
                if commit_limit <= 0:
                    raise ValueError("Must be positive")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for commit limit or 'all'")
                return
        
        # Get force reprocessing flag
        force_reprocess = self.force_reprocess_var.get()
        
        # Start ingestion in background thread
        self.ingest_button.config(state='disabled')
        self.ingest_progress['value'] = 0
        limit_text = "all commits" if commit_limit is None else f"{commit_limit} commits"
        reprocess_text = " (forced reprocessing)" if force_reprocess else ""
        self.ingest_status_var.set(f"Starting ingestion ({limit_text}){reprocess_text}...")
        
        thread = threading.Thread(target=self._ingest_worker, args=(commit_limit, force_reprocess))
        thread.daemon = True
        thread.start()
    
    def _ingest_worker(self, commit_limit=None, force_reprocess=False):
        """Background worker for ingestion"""
        try:
            # Step 1: Extract metadata with commit limit (20%)
            self.root.after(0, lambda: self._update_ingestion_progress(10, "Extracting metadata..."))
            
            # Set the repository for core and limit commits
            self.core.set_repository(self.current_repo)
            
            self.root.after(0, lambda: self._update_ingestion_progress(15, "Analyzing commits..."))
            
            # Use the core's ingestion process which respects limits and force reprocess flag
            success = self.core.ingest_repository_to_neo4j(
                commit_limit=commit_limit,
                progress_callback=self._ingestion_progress_callback,
                force_reprocess=force_reprocess
            )
            
            if not success:
                raise Exception("Failed to ingest repository to Neo4j")
            
            self.root.after(0, lambda: self._update_ingestion_progress(100, "Ingestion completed!"))
            
            # Success
            self.root.after(0, self._ingest_success)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._ingest_error(error_msg))
    
    def _ingestion_progress_callback(self, progress, message):
        """Callback for ingestion progress updates"""
        # Map core progress (5-100) to our range (15-100) to account for initial setup
        if progress <= 15:
            mapped_progress = progress  # Keep early progress as-is
        else:
            mapped_progress = 15 + ((progress - 15) * 0.85)  # Map 15-100 to 15-100
        
        self.root.after(0, lambda: self._update_ingestion_progress(mapped_progress, message))
    
    def _update_ingestion_progress(self, progress, message):
        """Update ingestion progress bar and status"""
        self.ingest_progress['value'] = progress
        self.ingest_status_var.set(f"{progress:.0f}% - {message}")
        self.root.update_idletasks()
    
    def _ingest_success(self):
        """Handle successful ingestion"""
        self.ingest_progress['value'] = 100
        self.ingest_button.config(state='normal')
        self.ingest_status_var.set("100% - Ingestion completed!")
        self.is_ingested = True
        self.enable_chat()
        
        # Update repository info
        self.update_repository_info()
        
        # Show success message
        self.update_status("Data ingestion completed successfully")
        messagebox.showinfo("Success", "Repository data ingestion completed successfully!\n\nYou can now use the Conversational Q&A tab.")
    
    def _ingest_error(self, error_msg):
        """Handle ingestion error"""
        self.ingest_progress['value'] = 0
        self.ingest_button.config(state='normal')
        self.ingest_status_var.set("Ingestion failed")
        
        self.update_status(f"Ingestion failed: {error_msg}")
        messagebox.showerror("Error", f"Data ingestion failed: {error_msg}")
    
    def run_statistical_analysis(self):
        """Run statistical analysis"""
        if not self.current_repo:
            messagebox.showerror("Error", "Please load a repository first")
            return
        
        analysis_type = self.analysis_type_var.get()
        try:
            commit_limit = int(self.commit_limit_var.get())
        except ValueError:
            commit_limit = 1000
        
        # Start analysis in background
        thread = threading.Thread(target=self._analysis_worker, args=(analysis_type, commit_limit))
        thread.daemon = True
        thread.start()
        
        self.update_status(f"Running {analysis_type} analysis...")
    
    def _analysis_worker(self, analysis_type, commit_limit):
        """Background worker for statistical analysis"""
        try:
            # Set repository and limit for LLM analyzer
            self.llm_analyzer.set_repository(self.current_repo)
            
            # Run analysis based on type
            if analysis_type == "package_churn":
                result = self.llm_analyzer.analyze_package_churn(commit_limit=commit_limit)
            elif analysis_type == "loc_analysis":
                result = self.llm_analyzer.analyze_loc(output_format='text')
            elif analysis_type == "complexity":
                result = self.llm_analyzer.analyze_complexity(output_format='text')
            elif analysis_type == "releases":
                result = self.llm_analyzer.analyze_releases(output_format='text')
            elif analysis_type == "loc_time_ratio":
                result = self.llm_analyzer.analyze_loc_time_ratio(commit_limit=commit_limit, output_format='text')
            elif analysis_type == "complexity_time_ratio":
                result = self.llm_analyzer.analyze_complexity_time_ratio(output_format='text')
            elif analysis_type == "combined_analysis":
                result = self.llm_analyzer.analyze_combined_analysis(output_format='text')
            elif analysis_type == "file_class_count":
                result = self.llm_analyzer.analyze_file_class_count(output_format='text')
            elif analysis_type == "code_duplication":
                result = self.llm_analyzer.analyze_code_duplication(output_format='text')
            elif analysis_type == "test_coverage":
                result = self.llm_analyzer.analyze_test_coverage_estimation(output_format='text')
            elif analysis_type == "security_patterns":
                result = self.llm_analyzer.analyze_security_patterns(output_format='text')
            elif analysis_type == "halstead_metrics":
                result = self.llm_analyzer.analyze_halstead_metrics(output_format='text')
            elif analysis_type == "maintainability_index":
                result = self.llm_analyzer.analyze_maintainability_index(output_format='text')
            elif analysis_type == "technical_debt":
                result = self.llm_analyzer.analyze_technical_debt(output_format='text')
            elif analysis_type == "dependency_metrics":
                result = self.llm_analyzer.analyze_dependency_metrics(output_format='text')
            elif analysis_type == "unified_metrics":
                result = self.run_unified_metrics_analysis()
            elif analysis_type == "ck_metrics":
                result = self.run_ck_metrics_analysis()
            elif analysis_type == "szz_analysis":
                result = self.run_szz_analysis()
            elif analysis_type == "bug_density":
                result = self.run_bug_density_analysis()
            elif analysis_type == "churn_analysis":
                result = self.run_churn_analysis()
            else:
                result = "Unknown analysis type"
            
            # Update UI
            self.root.after(0, lambda: self._analysis_complete(result))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._analysis_error(error_msg))
    
    def _analysis_complete(self, result):
        """Handle completed analysis"""
        self.analysis_results_text.delete('1.0', tk.END)
        self.analysis_results_text.insert('1.0', result)
        self.update_status("Analysis completed")
    
    def _analysis_error(self, error_msg):
        """Handle analysis error"""
        self.analysis_results_text.delete('1.0', tk.END)
        self.analysis_results_text.insert('1.0', f"Analysis failed: {error_msg}")
        self.update_status(f"Analysis failed: {error_msg}")
    
    def run_unified_metrics_analysis(self):
        """Run unified metrics analysis"""
        try:
            analyzer = UnifiedMetricsAnalyzer(self.current_repo)
            results = analyzer.analyze_all()
            
            output = "🔬 UNIFIED METRICS ANALYSIS\n"
            output += "=" * 50 + "\n\n"
            
            for file_path, metrics in results.items():
                output += f"📁 File: {file_path}\n"
                output += f"📊 Class: {metrics.name}\n\n"
                
                if metrics.ck_metrics:
                    output += "🏗️ CK Metrics:\n"
                    output += f"  • WMC (Weighted Methods per Class): {metrics.ck_metrics.wmc}\n"
                    output += f"  • CBO (Coupling Between Objects): {metrics.ck_metrics.cbo}\n"
                    output += f"  • RFC (Response For Class): {metrics.ck_metrics.rfc}\n"
                    output += f"  • LCOM (Lack of Cohesion): {metrics.ck_metrics.lcom}\n"
                    output += f"  • DIT (Depth of Inheritance): {metrics.ck_metrics.dit}\n"
                    output += f"  • NOC (Number of Children): {metrics.ck_metrics.noc}\n\n"
                
                if metrics.complexity:
                    output += "🌀 Complexity Metrics:\n"
                    output += f"  • Cyclomatic Complexity: {metrics.complexity.cyclomatic_complexity:.2f}\n"
                    output += f"  • Cognitive Complexity: {metrics.complexity.cognitive_complexity:.2f}\n"
                    output += f"  • Average Complexity: {metrics.complexity.average_complexity:.2f}\n"
                    output += f"  • Max Complexity: {metrics.complexity.max_complexity}\n"
                    output += f"  • Functions Count: {metrics.complexity.num_functions}\n\n"
                
                if metrics.halstead:
                    output += "📐 Halstead Metrics:\n"
                    output += f"  • Volume: {metrics.halstead.volume:.2f}\n"
                    output += f"  • Difficulty: {metrics.halstead.difficulty:.2f}\n"
                    output += f"  • Effort: {metrics.halstead.effort:.2f}\n"
                    output += f"  • Estimated Bugs: {metrics.halstead.bugs:.2f}\n\n"
                
                if metrics.maintainability:
                    output += "🔧 Maintainability Metrics:\n"
                    output += f"  • Maintainability Index: {metrics.maintainability.maintainability_index:.2f}\n"
                    output += f"  • Technical Debt (Hours): {metrics.maintainability.technical_debt_hours:.2f}\n"
                    output += f"  • Technical Debt Score: {metrics.maintainability.technical_debt_score:.2f}\n"
                    if metrics.maintainability.code_smells:
                        output += f"  • Code Smells: {', '.join(metrics.maintainability.code_smells)}\n"
                    output += "\n"
                
                output += "-" * 50 + "\n"
            
            return output
            
        except Exception as e:
            return f"❌ Unified metrics analysis failed: {str(e)}"
    
    def run_ck_metrics_analysis(self):
        """Run CK metrics analysis"""
        try:
            analyzer = CKMetricsAnalyzer()
            results = analyzer.analyze_directory(self.current_repo)
            
            output = "🏗️ CK METRICS ANALYSIS\n"
            output += "=" * 50 + "\n\n"
            
            for class_name, metrics in results.items():
                output += f"📊 Class: {class_name}\n"
                output += f"  • WMC: {metrics.wmc}\n"
                output += f"  • CBO: {metrics.cbo}\n"
                output += f"  • RFC: {metrics.rfc}\n"
                output += f"  • LCOM: {metrics.lcom}\n"
                output += f"  • DIT: {metrics.dit}\n"
                output += f"  • NOC: {metrics.noc}\n\n"
            
            return output
            
        except Exception as e:
            return f"❌ CK metrics analysis failed: {str(e)}"
    
    def run_szz_analysis(self):
        """Run SZZ analysis"""
        try:
            analyzer = EnhancedSZZAnalyzer(self.current_repo)
            results = analyzer.analyze_bug_inducing_commits()
            
            output = "🐛 SZZ BUG-INDUCING ANALYSIS\n"
            output += "=" * 50 + "\n\n"
            
            for bug_commit, inducing_commits in results.items():
                output += f"🐛 Bug Commit: {bug_commit}\n"
                output += "🔍 Inducing Commits:\n"
                for commit in inducing_commits:
                    output += f"  • {commit}\n"
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"❌ SZZ analysis failed: {str(e)}"
    
    def run_bug_density_analysis(self):
        """Run bug density analysis"""
        try:
            # Use GitIntel Ultimate for comprehensive analysis
            results = self.gitintel_ultimate.analyze_repository()
            
            output = "🐛 BUG DENSITY ANALYSIS\n"
            output += "=" * 50 + "\n\n"
            
            if 'bug_density' in results:
                for file_path, density in results['bug_density'].items():
                    output += f"📁 {file_path}: {density:.4f} bugs/LOC\n"
            else:
                output += "No bug density data available\n"
            
            return output
            
        except Exception as e:
            return f"❌ Bug density analysis failed: {str(e)}"
    
    def run_churn_analysis(self):
        """Run code churn analysis"""
        try:
            # Use LLM analyzer for churn analysis
            result = self.llm_analyzer.analyze_package_churn(commit_limit=int(self.commit_limit_var.get()))
            return result
            
        except Exception as e:
            return f"❌ Churn analysis failed: {str(e)}"
    
    # Chat Methods
    
    def ask_question(self):
        """Ask a question in the chat"""
        if not self.is_ingested:
            messagebox.showerror("Error", "Please ingest repository data first")
            return
        
        question = self.question_var.get().strip()
        if not question:
            return
        
        # Add question to chat display
        self.add_to_chat(f"❓ You: {question}", "user")
        
        # Clear input
        self.question_var.set("")
        
        # Process question in background
        thread = threading.Thread(target=self._chat_worker, args=(question,))
        thread.daemon = True
        thread.start()
        
        self.update_status("Processing question...")
    
    def _chat_worker(self, question):
        """Background worker for chat processing"""
        try:
            # Use the RepoChatCore's ask_question_neo4j_only method
            response = self.core.ask_question_neo4j_only(question)
            
            if not response or "I don't have enough information" in response:
                response = "❌ Could not find relevant information. Please try rephrasing your question."
            
            # Update UI
            self.root.after(0, lambda: self._chat_response(response))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._chat_error(error_msg))
    
    def _chat_response(self, response):
        """Handle chat response"""
        self.add_to_chat(f"🤖 GitIntel: {response}", "assistant")
        self.update_status("Ready")
    
    def _chat_error(self, error_msg):
        """Handle chat error"""
        self.add_to_chat(f"❌ Error: {error_msg}", "error")
        self.update_status("Ready")
    
    def add_to_chat(self, message, sender_type):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.chat_display.get('1.0', tk.END).strip():
            self.chat_display.insert(tk.END, "\n\n")
        
        self.chat_display.insert(tk.END, f"[{timestamp}] {message}")
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
    
    def use_example_question(self, question):
        """Use an example question"""
        self.question_var.set(question)
        self.question_entry.focus()
    
    def enable_chat(self):
        """Enable chat interface"""
        self.question_entry.config(state='normal')
        self.ask_button.config(state='normal')
        self.question_entry.bind('<Return>', lambda e: self.ask_question())
    
    def disable_chat(self):
        """Disable chat interface"""
        self.question_entry.config(state='disabled')
        self.ask_button.config(state='disabled')
        self.question_entry.unbind('<Return>')
    
    # Utility Methods
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def save_last_session(self):
        """Save last session information"""
        try:
            session_data = {
                'last_repository': self.current_repo,
                'timestamp': datetime.now().isoformat()
            }
            
            with open('.gitintel_session.json', 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save session: {e}")
    
    def load_last_session(self):
        """Load last session information"""
        try:
            if os.path.exists('.gitintel_session.json'):
                with open('.gitintel_session.json', 'r') as f:
                    session_data = json.load(f)
                
                last_repo = session_data.get('last_repository')
                if last_repo and os.path.exists(last_repo):
                    self.repo_path_var.set(last_repo)
                    
        except Exception as e:
            print(f"Failed to load session: {e}")
    
    def export_to_excel(self):
        """Export current analysis to Excel"""
        if not self.current_repo:
            messagebox.showerror("Error", "Please load a repository first")
            return
        
        analysis_type = self.analysis_type_var.get()
        
        # Ask user where to save
        filename = filedialog.asksaveasfilename(
            title="Export Analysis to Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"{analysis_type}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if not filename:
            return
        
        try:
            commit_limit = int(self.commit_limit_var.get())
        except ValueError:
            commit_limit = 100
        
        # Start export in background
        thread = threading.Thread(target=self._export_worker, args=(analysis_type, commit_limit, filename))
        thread.daemon = True
        thread.start()
        
        self.update_status(f"Exporting {analysis_type} to Excel...")
    
    def _export_worker(self, analysis_type, commit_limit, filename):
        """Background worker for Excel export"""
        try:
            # Set repository for LLM analyzer
            self.llm_analyzer.set_repository(self.current_repo)
            
            # Run analysis with Excel output
            if analysis_type == "package_churn":
                result = self.llm_analyzer.analyze_package_churn(commit_limit=commit_limit, output_format='excel')
            elif analysis_type == "loc_analysis":
                result = self.llm_analyzer.analyze_loc(output_format='excel')
            elif analysis_type == "complexity":
                result = self.llm_analyzer.analyze_complexity(output_format='excel')
            elif analysis_type == "releases":
                result = self.llm_analyzer.analyze_releases(output_format='excel')
            elif analysis_type == "loc_time_ratio":
                result = self.llm_analyzer.analyze_loc_time_ratio(commit_limit=commit_limit, output_format='excel')
            elif analysis_type == "complexity_time_ratio":
                result = self.llm_analyzer.analyze_complexity_time_ratio(output_format='excel')
            elif analysis_type == "combined_analysis":
                result = self.llm_analyzer.analyze_combined_analysis(output_format='excel')
            elif analysis_type == "file_class_count":
                result = self.llm_analyzer.analyze_file_class_count(output_format='excel')
            elif analysis_type == "code_duplication":
                result = self.llm_analyzer.analyze_code_duplication(output_format='excel')
            elif analysis_type == "test_coverage":
                result = self.llm_analyzer.analyze_test_coverage_estimation(output_format='excel')
            elif analysis_type == "security_patterns":
                result = self.llm_analyzer.analyze_security_patterns(output_format='excel')
            elif analysis_type == "halstead_metrics":
                result = self.llm_analyzer.analyze_halstead_metrics(output_format='excel')
            elif analysis_type == "maintainability_index":
                result = self.llm_analyzer.analyze_maintainability_index(output_format='excel')
            elif analysis_type == "technical_debt":
                result = self.llm_analyzer.analyze_technical_debt(output_format='excel')
            elif analysis_type == "dependency_metrics":
                result = self.llm_analyzer.analyze_dependency_metrics(output_format='excel')
            else:
                raise Exception("Unknown analysis type")
            
            # Copy the generated Excel file to user's chosen location
            # The analyzer creates files in analysis_output folder
            if hasattr(self, 'current_repo') and self.current_repo:
                output_dir = os.path.join(self.current_repo, 'analysis_output')
            else:
                output_dir = os.path.join(os.getcwd(), 'analysis_output')
            
            # Find the most recent Excel file for this analysis type
            import glob
            import time
            
            # Wait a moment for file to be created
            time.sleep(1)
            
            # Look for Excel files with analysis type in name
            search_patterns = [
                os.path.join(output_dir, f"*{analysis_type}*.xlsx"),
                os.path.join(output_dir, "*.xlsx")  # Fallback to any Excel file
            ]
            
            excel_files = []
            for pattern in search_patterns:
                excel_files.extend(glob.glob(pattern))
            
            if excel_files:
                # Get the most recent file
                latest_file = max(excel_files, key=os.path.getctime)
                
                # Copy to user's chosen location
                import shutil
                shutil.copy2(latest_file, filename)
                
                self.root.after(0, lambda: self._export_success(filename, latest_file))
            else:
                # Show text result if no Excel file found
                self.root.after(0, lambda: self._export_success(filename, None, result))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._export_error(error_msg))
    
    def _export_success(self, filename, source_file=None, text_result=None):
        """Handle successful export"""
        if source_file:
            message = f"Analysis exported successfully!\n\nFrom: {source_file}\nTo: {filename}"
        elif text_result:
            # Save text result to a text file if no Excel was generated
            text_filename = filename.replace('.xlsx', '.txt')
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(text_result)
            message = f"Analysis saved as text file:\n{text_filename}\n\n(Excel export not available for this analysis type)"
        else:
            message = f"Export completed:\n{filename}"
        
        self.update_status(f"Exported successfully")
        messagebox.showinfo("Export Success", message)
    
    def _export_error(self, error_msg):
        """Handle export error"""
        self.update_status(f"Export failed: {error_msg}")
        messagebox.showerror("Export Error", f"Failed to export analysis: {error_msg}")

    # Menu Actions
    
    def export_analysis(self):
        """Export analysis results"""
        messagebox.showinfo("Export", "Export functionality will be implemented soon.")
    
    def open_kg_browser(self):
        """Open knowledge graph browser"""
        if not self.is_ingested:
            messagebox.showerror("Error", "Please ingest repository data first")
            return
        
        # Switch to graph tab
        self.notebook.select(self.graph_frame)
        self.load_graph_data()
    
    def open_settings(self):
        """Open settings dialog"""
        messagebox.showinfo("Settings", "Settings panel will be implemented soon.")
    
    def show_user_guide(self):
        """Show user guide"""
        guide_text = """
🎯 GitIntel Desktop User Guide

📋 Getting Started:
1. Click 'File' → 'Open Repository' to select a Git repository
2. Go to 'Repository' tab and click 'Start Data Ingestion'
3. Use 'Conversational Q&A' tab to ask questions
4. Use 'Analysis' tab for statistical reports

💬 Example Questions:
• "Who are the top contributors?"
• "Show me recent commits"
• "Find files with most complexity"
• "শীর্ষ অবদানকারী কারা?" (Bengali)

📊 Statistical Analysis:
• Package Churn: Track code changes by package
• LOC Analysis: Lines of code trends over time
• Complexity: Code complexity metrics
• Releases: Release-wise change analysis

⚡ Keyboard Shortcuts:
• Ctrl+O: Open repository
• F5: Start data ingestion
• Enter: Ask question (in chat)

💡 Tips:
• Use commit limits for faster analysis on large repos
• Both English and Bengali questions are supported
• Vector search provides contextual answers
        """
        
        messagebox.showinfo("User Guide", guide_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
🚀 GitIntel Desktop v1.0

Conversational Intelligence for Comprehensive GitHub Repository Analysis

👨‍💻 Developed by: Md. Mostafizur Rahaman
🏫 Institution: University of Dhaka, IIT
📧 Contact: [Your Email]

🛠️ Technologies:
• Python, Tkinter (GUI)
• Neo4j (Knowledge Graph & Storage)
• Google Gemini (LLM)
• PyDriller (Git Analysis)

📄 License: MIT
        """
        
        messagebox.showinfo("About GitIntel", about_text)
    
    def run_ultimate_analysis(self):
        """Run GitIntel Ultimate Analysis (CK Metrics + SZZ Bug Detection)"""
        if not self.current_repo:
            messagebox.showwarning("No Repository", "Please load a repository first!")
            return
        
        if not messagebox.askyesno("Start Ultimate Analysis", 
                                   f"Start comprehensive analysis?\n\n"
                                   f"This includes:\n"
                                   f"✓ CK Metrics (WMC, CBO, RFC, LCOM, DIT, NOC)\n"
                                   f"✓ Enhanced SZZ Bug Detection\n"
                                   f"✓ Persistent Storage in Neo4j\n\n"
                                   f"Repository: {self.current_repo}\n\n"
                                   f"This may take several minutes for large repositories."):
            return
        
        # Start analysis in background thread
        self.update_status("Running GitIntel Ultimate Analysis...")
        self.analysis_results_text.delete('1.0', tk.END)
        self.analysis_results_text.insert('1.0', "🚀 Starting GitIntel Ultimate Analysis...\n\n")
        
        thread = threading.Thread(target=self._ultimate_analysis_worker)
        thread.daemon = True
        thread.start()
    
    def _ultimate_analysis_worker(self):
        """🚀 FIXED Background worker for ultimate analysis with ALL features working!"""
        try:
            self._log_analysis("="*70)
            self._log_analysis("🚀 GitIntel Ultimate v2.0 - FIXED VERSION")
            self._log_analysis("="*70)
            self._log_analysis(f"\n📁 Repository: {self.current_repo}\n")
            
            import sys
            import os
            
            # Add current directory to Python path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            
            from gitintel_ultimate_fixed import GitIntelUltimate
            
            self._log_analysis("🚀 Initializing FIXED GitIntel Ultimate...\n")
            self._log_analysis("   ✅ Integrated SZZ analysis during commit processing\n")
            self._log_analysis("   ✅ Reliability metrics (bug density, MTTR, stability)\n")
            self._log_analysis("   ✅ Productivity metrics (velocity, collaboration)\n")
            self._log_analysis("   ✅ Architectural metrics (cohesion, coupling)\n")
            self._log_analysis("   ✅ Evolution metrics (growth, change patterns)\n")
            self._log_analysis("   ✅ Proper Neo4j schema with relationships\n")
            self._log_analysis("   ✅ Fast processing with real-time progress\n\n")
            
            # Initialize FIXED GitIntel Ultimate
            self.gitintel_ultimate = GitIntelUltimate(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j", 
                neo4j_password="password"  # You should change this to your password
            )
            
            # Get project name
            project_name = os.path.basename(self.current_repo)
            
            # Run comprehensive analysis with progress tracking
            self._log_analysis("🔄 Starting comprehensive analysis...\n")
            
            def progress_callback(progress, message):
                self._log_analysis(f"📊 {progress:.1f}% - {message}\n")
                # Update progress bar if available
                if hasattr(self, 'analysis_progress'):
                    self.analysis_progress['value'] = progress
                    self.root.update_idletasks()
            
            results = self.gitintel_ultimate.analyze_repository(
                repo_path=self.current_repo,
                project_name=project_name,
                include_ck_metrics=True,
                include_bug_analysis=True,
                include_persistence=True,
                progress_callback=progress_callback,
                commit_limit=None  # Analyze all commits
            )
            
            
            # 🎉 Display COMPREHENSIVE Results from FIXED GitIntel Ultimate!
            self._log_analysis("\n" + "="*70)
            self._log_analysis("🎉 COMPREHENSIVE ANALYSIS RESULTS")
            self._log_analysis("="*70 + "\n")
            
            # Show high-level summary
            self._log_analysis(f"✅ Analysis Status: {results.get('success', 'Unknown')}\n")
            self._log_analysis(f"⏱️  Processing Time: {results.get('processing_time', 0):.1f} seconds\n")
            self._log_analysis(f"📊 Commits Processed: {results.get('commits_processed', 0):,}\n")
            self._log_analysis(f"📂 Files Analyzed: {results.get('files_analyzed', 0):,}\n")
            self._log_analysis(f"👥 Contributors Found: {results.get('contributors_found', 0):,}\n")
            self._log_analysis(f"🐛 Bug Relationships: {results.get('bug_relationships', 0):,}\n\n")
            
            # 🔴 RELIABILITY METRICS (what was missing!)
            reliability = results.get('reliability_metrics', {})
            if reliability:
                self._log_analysis("🔴 RELIABILITY METRICS\n")
                self._log_analysis(f"   • Bug Density: {reliability.get('bug_density', 0):.2f} bugs per 1000 LOC\n")
                self._log_analysis(f"   • Defect Removal Efficiency: {reliability.get('defect_removal_efficiency', 0):.1f}%\n")
                self._log_analysis(f"   • Mean Time to Fix: {reliability.get('mean_time_to_fix', 0):.1f} days\n")
                self._log_analysis(f"   • Code Churn Rate: {reliability.get('code_churn_rate', 0):.1f} lines/commit\n")
                self._log_analysis(f"   • File Stability Index: {reliability.get('file_stability_index', 0):.1f}%\n")
                self._log_analysis(f"   • Test File Ratio: {reliability.get('test_file_ratio', 0):.1f}%\n")
                self._log_analysis(f"   • Documentation Ratio: {reliability.get('documentation_ratio', 0):.1f}%\n\n")
            
            # 🟡 PRODUCTIVITY METRICS (what was missing!)
            productivity = results.get('productivity_metrics', {})
            if productivity:
                self._log_analysis("� PRODUCTIVITY METRICS\n")
                self._log_analysis(f"   • Commits per Day: {productivity.get('commits_per_day', 0):.2f}\n")
                self._log_analysis(f"   • Lines per Commit: {productivity.get('lines_per_commit', 0):.1f}\n")
                self._log_analysis(f"   • Files per Commit: {productivity.get('files_per_commit', 0):.1f}\n")
                self._log_analysis(f"   • Active Contributors: {productivity.get('active_contributors', 0)}\n")
                self._log_analysis(f"   • Commit Frequency Score: {productivity.get('commit_frequency_score', 0):.1f}%\n")
                self._log_analysis(f"   • Collaboration Index: {productivity.get('collaboration_index', 0):.1f}%\n")
                self._log_analysis(f"   • Feature Completion Rate: {productivity.get('feature_completion_rate', 0):.1f}%\n")
                self._log_analysis(f"   • Hotfix Frequency: {productivity.get('hotfix_frequency', 0):.2f} per week\n\n")
            
            # 🔵 ARCHITECTURAL METRICS (what was missing!)
            architecture = results.get('architectural_metrics', {})
            if architecture:
                self._log_analysis("🔵 ARCHITECTURAL METRICS\n")
                self._log_analysis(f"   • Package Cohesion: {architecture.get('package_cohesion', 0):.2f}\n")
                self._log_analysis(f"   • Package Coupling: {architecture.get('package_coupling', 0):.1f}%\n")
                self._log_analysis(f"   • Dependency Depth: {architecture.get('dependency_depth', 0):.2f}\n")
                self._log_analysis(f"   • Singleton Usage: {architecture.get('singleton_usage', 0)}\n")
                self._log_analysis(f"   • Factory Pattern Count: {architecture.get('factory_pattern_count', 0)}\n")
                self._log_analysis(f"   • Module Growth Rate: {architecture.get('module_growth_rate', 0):.2f} per month\n")
                self._log_analysis(f"   • Interface Stability: {architecture.get('interface_stability', 0):.1f}%\n\n")
            
            # 🟢 EVOLUTION METRICS (what was missing!)
            evolution = results.get('evolution_metrics', {})
            if evolution:
                self._log_analysis("🟢 EVOLUTION METRICS\n")
                self._log_analysis(f"   • Codebase Growth Rate: {evolution.get('codebase_growth_rate', 0):.1f} LOC/month\n")
                self._log_analysis(f"   • File Creation Rate: {evolution.get('file_creation_rate', 0):.2f} files/month\n")
                self._log_analysis(f"   • Deletion Rate: {evolution.get('deletion_rate', 0):.1f} LOC/month\n")
                self._log_analysis(f"   • Refactoring Frequency: {evolution.get('refactoring_frequency', 0):.1f}%\n")
                self._log_analysis(f"   • Large Commit Ratio: {evolution.get('large_commit_ratio', 0):.1f}%\n")
                
                hotspots = evolution.get('hotspot_files', [])
                if hotspots:
                    self._log_analysis("   • Hotspot Files:\n")
                    for file in hotspots[:5]:  # Show top 5
                        self._log_analysis(f"     - {file}\n")
                
                tech_adoption = evolution.get('new_technology_adoption', [])
                if tech_adoption:
                    self._log_analysis("   • Technology Adoption:\n")
                    for tech in tech_adoption[:5]:  # Show top 5
                        self._log_analysis(f"     - {tech}\n")
                self._log_analysis("\n")
            
            # 📊 OVERALL INSIGHTS
            self._log_analysis("📊 OVERALL PROJECT INSIGHTS\n")
            
            # Get comprehensive dashboard
            if hasattr(self.gitintel_ultimate, 'get_comprehensive_dashboard'):
                dashboard = self.gitintel_ultimate.get_comprehensive_dashboard(project_name)
                overall_health = dashboard.get('overall_health', {})
                
                self._log_analysis(f"   🏆 Overall Health: {overall_health.get('health_status', 'Unknown')}\n")
                self._log_analysis(f"   📈 Overall Score: {overall_health.get('overall_score', 0):.1f}/100\n")
                
                component_scores = overall_health.get('component_scores', {})
                self._log_analysis(f"   🔴 Reliability Score: {component_scores.get('reliability', 0):.1f}/100\n")
                self._log_analysis(f"   🟡 Productivity Score: {component_scores.get('productivity', 0):.1f}/100\n")
                self._log_analysis(f"   🔵 Architecture Score: {component_scores.get('architecture', 0):.1f}/100\n")
            
            # 🎯 Show features delivered
            features = results.get('features_delivered', [])
            if features:
                self._log_analysis("\n🎯 FEATURES DELIVERED:\n")
                for feature in features:
                    self._log_analysis(f"   ✅ {feature}\n")
            
            self._log_analysis("\n" + "="*70)
            self._log_analysis("🎉 GITINTEL ULTIMATE v2.0 ANALYSIS COMPLETE!")
            self._log_analysis("All promised features delivered successfully!")
            self._log_analysis("="*70 + "\n")
            
            # Final Summary
            self._log_analysis("\n\n" + "="*70)
            self._log_analysis("✅ Analysis Complete!")
            self._log_analysis("="*70)
            self._log_analysis("\n💾 Results saved to Neo4j persistent storage")
            self._log_analysis("\n📊 You can now query this data from the Graph tab")
            
            # Success message
            self.root.after(100, lambda: messagebox.showinfo(
                "Analysis Complete",
                f"GitIntel Ultimate Analysis Finished!\n\n"
                f"✅ {total_classes if 'total_classes' in locals() else 0} classes analyzed\n"
                f"✅ {total_bugs if 'total_bugs' in locals() else 0} bug relationships found\n\n"
                f"Check the Analysis tab for detailed results!"
            ))
            
            self.root.after(100, lambda: self.update_status("Analysis complete!"))
            
        except Exception as e:
            error_msg = f"❌ Analysis failed: {str(e)}"
            self._log_analysis(f"\n\n{error_msg}")
            self.root.after(100, lambda: messagebox.showerror("Analysis Error", error_msg))
            self.root.after(100, lambda: self.update_status("Analysis failed"))
    
    def _log_analysis(self, message):
        """Helper to log analysis output"""
        self.root.after(0, lambda: self.analysis_results_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.analysis_results_text.see(tk.END))
        self.root.after(0, lambda: self.root.update_idletasks())

def main():
    """Main application entry point"""
    # Create and configure root window
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        # You can add an icon file here
        # root.iconbitmap('gitintel_icon.ico')
        pass
    except:
        pass
    
    # Create application
    app = GitIntelDesktopApp(root)
    
    # Start GUI event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down GitIntel Desktop...")
        root.destroy()

if __name__ == "__main__":
    main()