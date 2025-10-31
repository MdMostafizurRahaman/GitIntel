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
from rag_vector_database import RAGVectorDatabase
from llm_git_analyzer import LLMGitAnalyzer

class GitIntelDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitIntel - Conversational Repository Analysis")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Initialize components
        self.core = RepoChatCore()
        self.kg_builder = None
        self.query_generator = CypherQueryGenerator()
        self.rag_db = None
        self.llm_analyzer = LLMGitAnalyzer()
        
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
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Repository...", command=self.open_repository)
        file_menu.add_separator()
        file_menu.add_command(label="Export Analysis...", command=self.export_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Ingest Repository", command=self.ingest_repository)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Package Churn Analysis", command=self.analyze_package_churn)
        analysis_menu.add_command(label="LOC Analysis", command=self.analyze_loc)
        analysis_menu.add_command(label="Complexity Analysis", command=self.analyze_complexity)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Knowledge Graph Browser", command=self.open_kg_browser)
        tools_menu.add_command(label="Vector Database Stats", command=self.show_vector_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.open_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_frames(self):
        """Create main application frames"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        
        # Repository tab
        self.repo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repo_frame, text="Repository")
        
        # Analysis tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis")
        
        # Chat tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Conversational Q&A")
    
    def create_repository_panel(self):
        """Create repository management panel"""
        # Repository selection frame
        repo_select_frame = ttk.LabelFrame(self.repo_frame, text="Repository Selection", padding="10")
        repo_select_frame.pack(fill='x', padx=10, pady=10)
        
        # Repository path
        ttk.Label(repo_select_frame, text="Repository Path:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.repo_path_var = tk.StringVar()
        self.repo_path_entry = ttk.Entry(repo_select_frame, textvariable=self.repo_path_var, width=60)
        self.repo_path_entry.grid(row=1, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(repo_select_frame, text="Browse...", command=self.browse_repository).grid(row=1, column=1)
        ttk.Button(repo_select_frame, text="Load", command=self.load_repository).grid(row=1, column=2, padx=(5, 0))
        
        repo_select_frame.columnconfigure(0, weight=1)
        
        # Repository info frame
        self.repo_info_frame = ttk.LabelFrame(self.repo_frame, text="Repository Information", padding="10")
        self.repo_info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Repository info text
        self.repo_info_text = scrolledtext.ScrolledText(self.repo_info_frame, height=15, wrap='word')
        self.repo_info_text.pack(fill='both', expand=True)
        
        # Ingestion frame
        ingest_frame = ttk.LabelFrame(self.repo_frame, text="Data Ingestion", padding="10")
        ingest_frame.pack(fill='x', padx=10, pady=10)
        
        self.ingest_button = ttk.Button(ingest_frame, text="Start Data Ingestion", command=self.ingest_repository)
        self.ingest_button.pack(side='left')
        
        self.ingest_progress = ttk.Progressbar(ingest_frame, mode='indeterminate')
        self.ingest_progress.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        self.ingest_status_var = tk.StringVar(value="Ready to ingest")
        ttk.Label(ingest_frame, textvariable=self.ingest_status_var).pack(side='right')
    
    def create_analysis_panel(self):
        """Create statistical analysis panel"""
        # Analysis controls frame
        controls_frame = ttk.LabelFrame(self.analysis_frame, text="Analysis Controls", padding="10")
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        # Analysis type selection
        ttk.Label(controls_frame, text="Analysis Type:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.analysis_type_var = tk.StringVar(value="package_churn")
        analysis_combo = ttk.Combobox(controls_frame, textvariable=self.analysis_type_var, 
                                     values=["package_churn", "loc_analysis", "complexity", "releases"], 
                                     state="readonly", width=20)
        analysis_combo.grid(row=1, column=0, sticky='w', padx=(0, 10))
        
        # Commit limit
        ttk.Label(controls_frame, text="Commit Limit:").grid(row=0, column=1, sticky='w', pady=(0, 5))
        
        self.commit_limit_var = tk.StringVar(value="1000")
        ttk.Entry(controls_frame, textvariable=self.commit_limit_var, width=10).grid(row=1, column=1, sticky='w', padx=(0, 10))
        
        # Analysis button
        ttk.Button(controls_frame, text="Run Analysis", command=self.run_statistical_analysis).grid(row=1, column=2, padx=(10, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(self.analysis_frame, text="Analysis Results", padding="10")
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Results text area
        self.analysis_results_text = scrolledtext.ScrolledText(results_frame, height=20, wrap='word')
        self.analysis_results_text.pack(fill='both', expand=True)
    
    def create_chat_panel(self):
        """Create conversational Q&A panel"""
        # Chat history frame
        chat_history_frame = ttk.LabelFrame(self.chat_frame, text="Conversation History", padding="10")
        chat_history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_history_frame, height=20, wrap='word')
        self.chat_display.pack(fill='both', expand=True)
        self.chat_display.config(state='disabled')
        
        # Input frame
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Question input
        ttk.Label(input_frame, text="Ask a question:").pack(anchor='w')
        
        question_input_frame = ttk.Frame(input_frame)
        question_input_frame.pack(fill='x', pady=(5, 0))
        
        self.question_var = tk.StringVar()
        self.question_entry = ttk.Entry(question_input_frame, textvariable=self.question_var)
        self.question_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.ask_button = ttk.Button(question_input_frame, text="Ask", command=self.ask_question)
        self.ask_button.pack(side='right')
        
        # Language selection
        lang_frame = ttk.Frame(input_frame)
        lang_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(lang_frame, text="Language:").pack(side='left')
        
        self.language_var = tk.StringVar(value="English")
        ttk.Radiobutton(lang_frame, text="English", variable=self.language_var, value="English").pack(side='left', padx=(10, 0))
        ttk.Radiobutton(lang_frame, text="বাংলা", variable=self.language_var, value="Bengali").pack(side='left', padx=(10, 0))
        
        # Example questions
        examples_frame = ttk.LabelFrame(input_frame, text="Example Questions", padding="5")
        examples_frame.pack(fill='x', pady=(10, 0))
        
        examples = [
            "Who are the top contributors?",
            "Show me recent commits", 
            "Find files with most complexity",
            "শীর্ষ অবদানকারী কারা?",
            "সাম্প্রতিক কমিট দেখাও"
        ]
        
        for i, example in enumerate(examples):
            btn = ttk.Button(examples_frame, text=example, 
                           command=lambda q=example: self.use_example_question(q))
            btn.pack(side='left', padx=2, pady=2)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, relief='sunken')
        self.status_label.pack(side='left', fill='x', expand=True, padx=(10, 0), pady=5)
        
        # Repository status
        self.repo_status_var = tk.StringVar(value="No repository loaded")
        ttk.Label(self.status_frame, textvariable=self.repo_status_var, relief='sunken').pack(side='right', padx=(0, 10), pady=5)
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Control-o>', lambda e: self.open_repository())
        self.root.bind('<F5>', lambda e: self.ingest_repository())
    
    # Repository Management Methods
    
    def browse_repository(self):
        """Browse for repository folder"""
        folder = filedialog.askdirectory(title="Select Git Repository")
        if folder:
            self.repo_path_var.set(folder)
    
    def open_repository(self):
        """Open repository dialog"""
        self.browse_repository()
        if self.repo_path_var.get():
            self.load_repository()
    
    def load_repository(self):
        """Load selected repository"""
        repo_path = self.repo_path_var.get().strip()
        if not repo_path:
            messagebox.showerror("Error", "Please select a repository path")
            return
        
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
                self.rag_db = RAGVectorDatabase(repo_path=repo_path)
                
                # Check if already ingested
                self.is_ingested = self.kg_builder.has_knowledge_graph()
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
        
        # Start ingestion in background thread
        self.ingest_button.config(state='disabled')
        self.ingest_progress.start()
        self.ingest_status_var.set("Ingesting...")
        
        thread = threading.Thread(target=self._ingest_worker)
        thread.daemon = True
        thread.start()
    
    def _ingest_worker(self):
        """Background worker for ingestion"""
        try:
            # Step 1: Extract metadata
            self.root.after(0, lambda: self.ingest_status_var.set("Extracting metadata..."))
            metadata = self.core.extract_metadata()
            
            # Step 2: Build knowledge graph
            self.root.after(0, lambda: self.ingest_status_var.set("Building knowledge graph..."))
            kg_success = self.kg_builder.build_knowledge_graph(self.current_repo, metadata)
            
            if not kg_success:
                raise Exception("Failed to build knowledge graph")
            
            # Step 3: Build vector database
            self.root.after(0, lambda: self.ingest_status_var.set("Building vector database..."))
            
            # Prepare documents for RAG
            documents = []
            
            # Add commits
            for commit in metadata.get('commits', []):
                documents.append({**commit, 'type': 'commit'})
            
            # Add files
            for file_info in metadata.get('files', []):
                documents.append({**file_info, 'type': 'file'})
            
            # Add contributors
            for contributor in metadata.get('contributors', []):
                documents.append({**contributor, 'type': 'contributor'})
            
            # Add to vector database
            self.rag_db.add_documents(documents)
            
            # Success
            self.root.after(0, self._ingest_success)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._ingest_error(error_msg))
    
    def _ingest_success(self):
        """Handle successful ingestion"""
        self.ingest_progress.stop()
        self.ingest_button.config(state='normal')
        self.ingest_status_var.set("Ingestion completed")
        self.is_ingested = True
        self.enable_chat()
        
        # Update repository info
        self.update_repository_info()
        
        # Show success message
        self.update_status("Data ingestion completed successfully")
        messagebox.showinfo("Success", "Repository data ingestion completed successfully!\n\nYou can now use the Conversational Q&A tab.")
    
    def _ingest_error(self, error_msg):
        """Handle ingestion error"""
        self.ingest_progress.stop()
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
                result = self.llm_analyzer.analyze_loc_time_ratio(commit_limit=commit_limit)
            elif analysis_type == "complexity":
                result = self.llm_analyzer.analyze_complexity(commit_limit=commit_limit)
            elif analysis_type == "releases":
                result = self.llm_analyzer.analyze_releases(commit_limit=commit_limit)
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
            # Generate Cypher query
            cypher_query = self.query_generator.generate_query(question)
            
            if not cypher_query:
                response = "❌ Could not understand the question. Please rephrase."
            else:
                # Execute query
                query_results = self.kg_builder.execute_query(cypher_query)
                
                # Generate response
                response = self.query_generator.generate_response(question, query_results)
                
                # Get relevant context from RAG
                context = self.rag_db.get_relevant_context(question, limit=3)
                
                # Combine response with context if relevant
                if "No relevant context found" not in context:
                    response += f"\n\n📚 **Additional Context:**\n{context[:300]}..."
            
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
    
    # Menu Actions
    
    def export_analysis(self):
        """Export analysis results"""
        messagebox.showinfo("Export", "Export functionality will be implemented soon.")
    
    def analyze_package_churn(self):
        """Quick package churn analysis"""
        self.analysis_type_var.set("package_churn")
        self.notebook.select(self.analysis_frame)
        self.run_statistical_analysis()
    
    def analyze_loc(self):
        """Quick LOC analysis"""
        self.analysis_type_var.set("loc_analysis")
        self.notebook.select(self.analysis_frame)
        self.run_statistical_analysis()
    
    def analyze_complexity(self):
        """Quick complexity analysis"""
        self.analysis_type_var.set("complexity")
        self.notebook.select(self.analysis_frame)
        self.run_statistical_analysis()
    
    def open_kg_browser(self):
        """Open knowledge graph browser"""
        if not self.is_ingested:
            messagebox.showerror("Error", "Please ingest repository data first")
            return
        
        messagebox.showinfo("Knowledge Graph", "Knowledge Graph Browser will open in a separate window soon.")
    
    def show_vector_stats(self):
        """Show vector database statistics"""
        if not self.rag_db:
            messagebox.showerror("Error", "Vector database not initialized")
            return
        
        try:
            stats = self.rag_db.get_database_stats()
            
            stats_text = "📊 Vector Database Statistics\n"
            stats_text += "=" * 40 + "\n\n"
            
            for key, value in stats.items():
                if isinstance(value, dict):
                    stats_text += f"{key}:\n"
                    for sub_key, sub_value in value.items():
                        stats_text += f"  • {sub_key}: {sub_value}\n"
                else:
                    stats_text += f"{key}: {value}\n"
            
            messagebox.showinfo("Vector Database Statistics", stats_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get statistics: {e}")
    
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
• Neo4j (Knowledge Graph)
• ChromaDB/FAISS (Vector Database)
• Google Gemini (LLM)
• PyDriller (Git Analysis)

📄 License: MIT
        """
        
        messagebox.showinfo("About GitIntel", about_text)

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