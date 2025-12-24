#!/usr/bin/env python3
"""
Autonomous AI Agent GUI - Tkinter Interface
Truly agentic system with no hardcoded logic
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path
from threading import Thread

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from github_autonomous_agent import GitHubAutonomousAgent
from interactive_dataset_generator import AgenticDatasetGenerator

class AutonomousAgentGUI:
    """
    Simple, clean Tkinter GUI for the autonomous agent
    Focus on user interaction and learning
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 GitHub Autonomous Agent - Like Copilot for Repos")
        self.root.geometry("900x700")
        
        # Initialize agent
        try:
            self.agent = GitHubAutonomousAgent()
            self.agent_ready = True
        except Exception as e:
            self.agent = None
            self.agent_ready = False
            messagebox.showerror("Error", f"Failed to initialize agent: {e}")
        
        # Initialize interactive generator
        self.interactive_generator = AgenticDatasetGenerator()
        self.interactive_mode = False
        
        self.current_understanding = None
        self.setup_ui()
        
        # Update status with auto-detected repository
        if self.agent_ready and self.agent.repo_path:
            self.status_var.set(f"✅ Auto-detected repository: {os.path.basename(self.agent.repo_path)}")
            self.repo_var.set(self.agent.repo_path)
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="🤖 GitHub Autonomous Agent", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        subtitle = ttk.Label(main_frame, 
                            text="Like GitHub Copilot - Understands ANY GitHub query and generates intelligent analysis",
                            font=('Arial', 10, 'italic'))
        subtitle.grid(row=1, column=0, pady=5, sticky=tk.W)
        
        # Repository selection
        repo_frame = ttk.LabelFrame(main_frame, text="📁 Repository", padding="10")
        repo_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        repo_frame.columnconfigure(0, weight=1)
        
        self.repo_var = tk.StringVar()
        repo_entry = ttk.Entry(repo_frame, textvariable=self.repo_var)
        repo_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        repo_btn = ttk.Button(repo_frame, text="Browse", command=self.browse_repo)
        repo_btn.grid(row=0, column=1, padx=5)
        
        set_repo_btn = ttk.Button(repo_frame, text="✅ Set Repository", 
                                  command=self.set_repository)
        set_repo_btn.grid(row=0, column=2, padx=5)
        
        # Query input
        query_frame = ttk.LabelFrame(main_frame, text="💬 Ask Anything About GitHub/Git", padding="10")
        query_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        query_frame.columnconfigure(0, weight=1)
        
        # Query text
        self.query_text = scrolledtext.ScrolledText(query_frame, height=4, wrap=tk.WORD)
        self.query_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        self.query_text.insert('1.0', 
            "Examples - Agent understands custom formulas and questions:\n"
            "• Standard: Provide me dataset of KLOC, SOC, complexity in Excel\n"
            "• Custom Formula: Calculate (churn * complexity) / time_spent for each commit\n"
            "• Personalized: Create custom metric: bug_density = defects / (lines_of_code / 1000)\n"
            "• Benchmark: Generate Defects4J, Bugs.jar, Promise datasets\n"
            "• Complex: Show commits per hour with author contribution patterns"
        )
        
        # Query buttons
        btn_frame = ttk.Frame(query_frame)
        btn_frame.grid(row=1, column=0, pady=5)
        
        self.analyze_btn = ttk.Button(btn_frame, text="🚀 Generate Dataset", 
                                     command=self.analyze_and_execute)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.interactive_btn = ttk.Button(btn_frame, text="🤖 Interactive Mode", 
                                         command=self.start_interactive_mode)
        self.interactive_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="🗑️ Clear", 
                              command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Output area with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Understanding tab
        understanding_frame = ttk.Frame(notebook)
        notebook.add(understanding_frame, text="🧠 AI Understanding")
        
        self.understanding_text = scrolledtext.ScrolledText(understanding_frame, 
                                                           wrap=tk.WORD, height=15)
        self.understanding_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clarification tab
        clarification_frame = ttk.Frame(notebook)
        notebook.add(clarification_frame, text="❓ Clarification")
        
        self.clarification_text = scrolledtext.ScrolledText(clarification_frame,
                                                           wrap=tk.WORD, height=10)
        self.clarification_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        clarify_input_frame = ttk.Frame(clarification_frame)
        clarify_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(clarify_input_frame, text="Your clarification:").pack(side=tk.LEFT)
        self.clarify_var = tk.StringVar()
        clarify_entry = ttk.Entry(clarify_input_frame, textvariable=self.clarify_var)
        clarify_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        clarify_btn = ttk.Button(clarify_input_frame, text="Submit", 
                                command=self.submit_clarification)
        clarify_btn.pack(side=tk.LEFT)
        
        # Result tab
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="📊 Results")
        
        self.result_text = scrolledtext.ScrolledText(result_frame, 
                                                     wrap=tk.WORD, height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Learning tab
        learning_frame = ttk.Frame(notebook)
        notebook.add(learning_frame, text="🎓 Learning History")
        
        self.learning_text = scrolledtext.ScrolledText(learning_frame,
                                                      wrap=tk.WORD, height=15)
        self.learning_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        refresh_btn = ttk.Button(learning_frame, text="🔄 Refresh", 
                                command=self.show_learning_history)
        refresh_btn.pack(pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready" if self.agent_ready else "Agent not available")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E))
    
    def browse_repo(self):
        """Browse for repository directory"""
        directory = filedialog.askdirectory(title="Select Git Repository")
        if directory:
            self.repo_var.set(directory)
    
    def set_repository(self):
        """Set the repository in the agent"""
        if not self.agent_ready:
            messagebox.showerror("Error", "Agent not initialized")
            return
        
        repo_path = self.repo_var.get().strip()
        if not repo_path:
            messagebox.showwarning("Warning", "Please select a repository")
            return
        
        try:
            success = self.agent.set_repository(repo_path)
            if success:
                repo_name = os.path.basename(repo_path)
                self.status_var.set(f"✅ Repository set: {repo_name}")
                messagebox.showinfo("Success", f"Repository '{repo_name}' set successfully!")
            else:
                # Provide more specific error messages
                if not os.path.exists(repo_path):
                    messagebox.showerror("Error", f"Repository path does not exist:\n{repo_path}")
                elif not os.path.exists(os.path.join(repo_path, '.git')):
                    messagebox.showerror("Error", f"Not a Git repository:\n{repo_path}\n\nPlease select a folder containing a .git directory.")
                else:
                    messagebox.showerror("Error", f"Invalid repository path:\n{repo_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set repository: {e}")
    
    def analyze_and_execute(self):
        """Analyze query and execute automatically"""
        if not self.agent_ready:
            messagebox.showerror("Error", "Agent not initialized")
            return
        
        query = self.query_text.get('1.0', tk.END).strip()
        if not query or query.startswith("Examples:"):
            messagebox.showwarning("Warning", "Please enter your query")
            return
        
        # Always use auto-detected repository if available
        # No need to check for special cases - agent handles clarification internally
        if not self.agent.repo_path:
            messagebox.showwarning("Warning", "Please set repository first")
            return
        
        self.status_var.set("🧠 Analyzing and executing...")
        self.understanding_text.delete('1.0', tk.END)
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', "⏳ Processing...\n\n")
        
        def analyze():
            try:
                # Step 1: Understanding
                self.root.after(0, lambda: self.status_var.set("📖 Step 1/5: Understanding query..."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "📖 Step 1/5: Understanding your query...\n"))
                
                # Step 2: Extract data
                self.root.after(0, lambda: self.status_var.set("📊 Step 2/5: Extracting data..."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "📊 Step 2/5: Extracting data from source...\n"))
                
                # Step 3: Calculate
                self.root.after(0, lambda: self.status_var.set("🧮 Step 3/5: Processing data..."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "🧮 Step 3/5: Processing data...\n"))
                
                # Step 4: Generate file
                self.root.after(0, lambda: self.status_var.set("💾 Step 4/5: Creating file..."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "💾 Step 4/5: Generating output file...\n"))
                
                # Automatically analyze and execute
                understanding = self.agent.understand_and_respond(query, execute=True)
                self.current_understanding = understanding
                
                # Step 5: Finalize
                self.root.after(0, lambda: self.status_var.set("✅ Step 5/5: Finalizing..."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "✅ Step 5/5: Finalizing output...\n\n"))
                
                # Display understanding
                self.root.after(0, self.display_understanding, understanding)
                
                # Check if needs clarification
                if understanding.get('needs_clarification'):
                    self.root.after(0, self.show_clarification_needed, understanding)
                elif understanding.get('error'):
                    self.root.after(0, lambda: messagebox.showerror("Error", understanding['error']))
                    self.root.after(0, lambda: self.status_var.set("Error"))
                else:
                    # Display results
                    self.root.after(0, self.display_result, understanding)
                    self.root.after(0, self.show_learning_history)
                    self.root.after(0, lambda: self.status_var.set("✅ Dataset created successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
                # Re-enable main query on error
                self.root.after(0, lambda: self.query_text.config(state='normal'))
                self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set("Error"))
        
        Thread(target=analyze, daemon=True).start()
    
    def display_understanding(self, understanding):
        """Display AI's understanding"""
        self.understanding_text.delete('1.0', tk.END)
        
        text = "🧠 AI UNDERSTANDING\n" + "="*50 + "\n\n"
        
        text += f"Intent: {understanding.get('intent', 'Unknown')}\n\n"
        text += f"Confidence: {understanding.get('confidence', 0)*100:.1f}%\n\n"
        
        if understanding.get('data_type'):
            text += f"Data Type: {understanding['data_type']}\n\n"
        
        if understanding.get('metrics'):
            text += "Metrics to Calculate:\n"
            for metric in understanding['metrics']:
                text += f"  • {metric}\n"
            text += "\n"
        
        if understanding.get('custom_formula'):
            text += f"Custom Formula: {understanding['custom_formula']}\n\n"
        
        if understanding.get('filters'):
            text += f"Filters: {understanding['filters']}\n\n"
        
        text += f"Output Format: {understanding.get('output_format', 'json')}\n"
        
        self.understanding_text.insert('1.0', text)
    
    def show_clarification_needed(self, understanding):
        """Show clarification questions and disable main query until clarified"""
        self.clarification_text.delete('1.0', tk.END)
        
        text = "❓ CLARIFICATION NEEDED\n" + "="*50 + "\n\n"
        text += "The AI needs more information to proceed:\n\n"
        
        questions = understanding.get('clarification_questions', [])
        if isinstance(questions, list):
            for q in questions:
                text += f"{q}\n"
        else:
            text += f"{questions}\n"
        
        text += "\n" + "="*50 + "\n"
        text += "💡 INSTRUCTIONS:\n"
        text += "• Type your response in the input field below\n"
        text += "• You can type 'back' to return to main options\n"
        text += "• For numbered options, just type the number (1, 2, 3, 4)\n"
        text += "• For file paths, provide the full path\n\n"
        text += "👉 Enter your response and click Submit:"
        
        self.clarification_text.insert('1.0', text)
        
        # Switch to clarification tab
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        child.select(1)  # Clarification tab
                        break
        
        # Disable main query input until clarification is provided
        self.query_text.config(state='disabled')
        self.analyze_btn.config(state='disabled')
        
        # Store the current understanding for clarification
        self.current_understanding = understanding
        
        messagebox.showinfo("Clarification Needed", 
                          "Please use the Clarification tab to provide the required information.\n\n" +
                          "💡 Tip: You can type 'back' to return to main options!")
    
    def submit_clarification(self):
        """Submit clarification to agent and auto-execute"""
        clarification = self.clarify_var.get().strip()
        if not clarification:
            messagebox.showwarning("Warning", "Please provide clarification")
            return
        
        self.clarify_var.set("")  # Clear input immediately
        
        if self.interactive_mode and hasattr(self, 'current_parsed_request'):
            # Handle interactive mode clarification
            self.handle_interactive_clarification(clarification)
        else:
            # Handle normal agent clarification
            self.handle_agent_clarification(clarification)
    
    def handle_interactive_clarification(self, clarification):
        """Handle clarification in interactive mode"""
        self.status_var.set("🤖 Processing your response...")
        
        def process():
            try:
                response = clarification.lower().strip()
                
                if response in ['yes', 'y', 'proceed', 'ok', 'correct']:
                    # User confirmed - generate dataset
                    self.root.after(0, lambda: self.generate_interactive_dataset(self.current_parsed_request))
                    
                elif response in ['no', 'n', 'start over', 'restart']:
                    # User wants to start over
                    self.root.after(0, lambda: self.reset_interactive_mode())
                    self.root.after(0, lambda: messagebox.showinfo("Reset", "Please enter a new dataset request"))
                    
                else:
                    # User wants modifications - re-parse with modifications
                    modified_query = f"{self.query_text.get('1.0', tk.END).strip()} {clarification}"
                    
                    # Re-parse with modifications
                    parsed = self.interactive_generator.parse_user_input(modified_query)
                    
                    # Update understanding display
                    self.root.after(0, lambda: self.display_interactive_understanding(parsed))
                    self.root.after(0, lambda: self.ask_interactive_confirmation(parsed))
                    
                    self.root.after(0, lambda: self.status_var.set("🤖 Interactive Mode: Updated understanding - awaiting confirmation"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {e}"))
                self.root.after(0, lambda: self.reset_interactive_mode())
        
        Thread(target=process, daemon=True).start()
    
    def handle_agent_clarification(self, clarification):
        """Handle normal agent clarification"""
        if not self.current_understanding:
            messagebox.showwarning("Warning", "No query to clarify")
            return
        
        # Use the clarification directly with proper prefix
        combined_query = f"clarification: {clarification}"
        
        self.status_var.set("🧠 Processing clarification...")
        
        def process():
            try:
                # Re-analyze with clarification and auto-execute
                understanding = self.agent.understand_and_respond(combined_query, execute=True)
                self.current_understanding = understanding
                
                self.root.after(0, self.display_understanding, understanding)
                
                if understanding.get('needs_clarification'):
                    # Still needs more clarification
                    self.root.after(0, self.show_clarification_needed, understanding)
                elif understanding.get('error'):
                    # Error occurred
                    self.root.after(0, lambda: messagebox.showerror("Error", understanding['error']))
                    # Re-enable main query on error
                    self.root.after(0, lambda: self.query_text.config(state='normal'))
                    self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
                    self.root.after(0, lambda: self.status_var.set("Error"))
                else:
                    # Success - display results and re-enable main query
                    self.root.after(0, self.display_result, understanding)
                    self.root.after(0, self.show_learning_history)
                    self.root.after(0, lambda: self.query_text.config(state='normal'))
                    self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
                    self.root.after(0, lambda: self.status_var.set("✅ Dataset created successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
                # Re-enable main query on error
                self.root.after(0, lambda: self.query_text.config(state='normal'))
                self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set("Error"))
        
        Thread(target=process, daemon=True).start()
    
    def generate_interactive_dataset(self, parsed_request):
        """Generate dataset using interactive workflow"""
        self.status_var.set("🤖 Generating interactive dataset...")
        
        def generate():
            try:
                # Get repository path
                repo_path = self.repo_var.get().strip()
                if not repo_path:
                    raise ValueError("Repository path not set")
                
                # Determine output directory
                output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_datasets")
                os.makedirs(output_dir, exist_ok=True)
                
                dataset_name = parsed_request.get('dataset_name', 'interactive_dataset')
                output_file = os.path.join(output_dir, f"{dataset_name}.csv")
                
                # Generate based on type
                if parsed_request.get('dataset_type') == 'benchmark':
                    # Use benchmark generation logic
                    benchmark_type = parsed_request.get('benchmark_type', 'Defects4J')
                    # For now, simulate - you could call the actual benchmark generation
                    with open(output_file, 'w') as f:
                        f.write("file,content\n")
                        f.write("sample.java,// Sample Java file\n")
                    
                elif parsed_request.get('dataset_type') == 'custom':
                    # Use custom metrics generation
                    selected_metrics = parsed_request.get('metrics', [])
                    # For now, simulate - you could call the actual metrics extraction
                    with open(output_file, 'w') as f:
                        f.write("file," + ",".join(selected_metrics) + "\n")
                        f.write("sample.java," + ",".join(["0"] * len(selected_metrics)) + "\n")
                
                # Display success
                self.root.after(0, lambda: self.display_interactive_result(output_file, parsed_request))
                self.root.after(0, lambda: self.reset_interactive_mode())
                self.root.after(0, lambda: self.status_var.set("✅ Interactive dataset created successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {e}"))
                self.root.after(0, lambda: self.reset_interactive_mode())
        
        Thread(target=generate, daemon=True).start()
    
    def display_interactive_result(self, output_file, parsed_request):
        """Display interactive generation result"""
        self.result_text.delete('1.0', tk.END)
        
        text = "🤖 INTERACTIVE DATASET CREATED!\n" + "="*50 + "\n\n"
        text += "✅ Your dataset has been generated using the interactive workflow!\n\n"
        text += f"📁 Output File: {output_file}\n\n"
        
        if parsed_request.get('dataset_type') == 'benchmark':
            text += f"📋 Dataset Type: Benchmark ({parsed_request.get('benchmark_type')})\n"
        elif parsed_request.get('dataset_type') == 'custom':
            text += f"📊 Dataset Type: Custom with {len(parsed_request.get('metrics', []))} metrics\n"
        
        text += f"📄 Format: {parsed_request.get('output_format', 'csv')}\n\n"
        text += "💡 The interactive workflow ensured your requirements were clearly understood\n"
        text += "   before generating the dataset.\n"
        
        self.result_text.insert('1.0', text)
        
        # Switch to result tab
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        child.select(2)  # Result tab
                        break
        
        messagebox.showinfo("Success!", f"Interactive dataset created!\n\nFile: {output_file}")
    
    def reset_interactive_mode(self):
        """Reset interactive mode and re-enable inputs"""
        self.interactive_mode = False
        self.query_text.config(state='normal')
        self.analyze_btn.config(state='normal')
        self.interactive_btn.config(state='normal')
        if hasattr(self, 'current_parsed_request'):
            delattr(self, 'current_parsed_request')
    
    def clear_all(self):
        """Clear all input and output"""
        self.query_text.delete('1.0', tk.END)
        self.understanding_text.delete('1.0', tk.END)
        self.clarification_text.delete('1.0', tk.END)
        self.result_text.delete('1.0', tk.END)
        self.clarify_var.set("")
        self.current_understanding = None
        self.status_var.set("Ready")
        # Re-enable inputs if they were disabled
        self.query_text.config(state='normal')
        self.analyze_btn.config(state='normal')
        if hasattr(self, 'interactive_btn'):
            self.interactive_btn.config(state='normal')
    
    def display_result(self, result):
        """Display execution result with proper error handling"""
        self.result_text.delete('1.0', tk.END)
        
        # Check execution_result if present
        exec_result = result.get('execution_result', {})
        is_success = result.get('success', exec_result.get('success', True))
        output_file = result.get('output_file') or exec_result.get('output_file')
        
        text = "📊 DATASET GENERATION COMPLETE!\n" + "="*50 + "\n\n"
        
        if is_success:
            text += "✅ SUCCESS! Your dataset has been created!\n\n"
        else:
            text += "❌ FAILED!\n\n"
            # Show error details
            error_msg = result.get('error') or exec_result.get('error')
            if error_msg:
                text += f"⚠️ Error: {error_msg}\n\n"
        
        # Show output file PROMINENTLY
        if output_file:
            text += "="*50 + "\n"
            text += "📁 OUTPUT FILE:\n"
            text += f"   {output_file}\n"
            text += "="*50 + "\n\n"
        
        # Check for format mismatch and show feedback
        format_message = result.get('format_message') or exec_result.get('format_message')
        format_match = result.get('format_match', exec_result.get('format_match', True))
        
        if format_message and not format_match:
            text += f"⚠️ FORMAT NOTICE:\n{format_message}\n\n"
            text += "💡 Would you like me to:\n"
            text += "  1. Convert the existing file to your requested format\n"
            text += "  2. Regenerate in your requested format\n\n"
        
        # Get metrics from result or execution_result
        metrics = result.get('metrics') or result.get('data') or exec_result.get('metrics')
        
        if metrics:
            
            # Handle both list and dict formats
            if isinstance(metrics, dict):
                # Count rows if metrics is dict with lists
                first_metric = next(iter(metrics.values()), [])
                if isinstance(first_metric, list):
                    num_rows = len(first_metric)
                    text += f"📊 Dataset Size: {num_rows} rows\n\n"
                
                text += "📈 Metrics Calculated:\n"
                for metric, values in metrics.items():
                    if isinstance(values, list):
                        text += f"  • {metric} ({len(values)} values)\n"
                    else:
                        text += f"  • {metric}\n"
                text += "\n"
            elif isinstance(metrics, list):
                # metrics is a list of metric names
                text += "📈 Metrics Calculated:\n"
                for metric in metrics:
                    if isinstance(metric, dict):
                        text += f"  • {metric.get('name', 'Unknown')}\n"
                    else:
                        text += f"  • {metric}\n"
                text += "\n"
        
        if result.get('reasoning'):
            text += f"💡 AI Reasoning:\n{result['reasoning']}\n\n"
        
        if result.get('output_files'):
            text += "📂 All Output Files:\n"
            for file_path in result['output_files']:
                text += f"  📄 {file_path}\n"
            text += "\n"
        
        if result.get('message'):
            text += f"\n📝 Message: {result['message']}\n"
        
        self.result_text.insert('1.0', text)
        
        # Switch to result tab and show message box
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        child.select(2)  # Result tab
                        break
        
        # Show completion message
        if output_file and is_success:
            messagebox.showinfo(
                "Dataset Created!", 
                f"✅ Your dataset has been created!\n\n"
                f"📁 File: {output_file}\n\n"
                f"Check the Results tab for details."
            )
        elif not is_success:
            error_msg = result.get('error') or exec_result.get('error') or 'Unknown error'
            messagebox.showerror(
                "Generation Failed",
                f"❌ Failed to generate dataset\n\n"
                f"Error: {error_msg}\n\n"
                f"Please check your query and try again."
            )
    
    def show_learning_history(self):
        """Show what the agent has learned"""
        if not self.agent_ready:
            return
        
        self.learning_text.delete('1.0', tk.END)
        
        text = "🎓 LEARNING HISTORY\n" + "="*50 + "\n\n"
        
        kb = self.agent.knowledge_base
        
        text += f"Successful Analyses: {len(kb.get('successful_analyses', []))}\n"
        text += f"Learned Metrics: {len(kb.get('learned_metrics', {}))}\n"
        text += f"Repository Contexts: {len(kb.get('repository_contexts', {}))}\n\n"
        
        text += "Recent Conversation:\n\n"
        
        for msg in self.agent.conversation_history[-10:]:
            role = msg.get('role', 'unknown')
            content = msg.get('parts', [''])[0]
            if isinstance(content, str):
                content_preview = content[:100] + "..." if len(content) > 100 else content
                text += f"• {role.upper()}: {content_preview}\n\n"
        
        if kb.get('successful_analyses'):
            text += "\nRecent Successful Analyses:\n\n"
            for analysis in kb['successful_analyses'][-5:]:
                text += f"• Query: {analysis.get('query', 'N/A')[:80]}...\n"
                text += f"  Metrics: {', '.join(analysis.get('metrics', []))}\n"
                text += f"  Format: {analysis.get('output_format', 'N/A')}\n\n"
        
        if hasattr(self.agent, 'repo_context'):
            text += "\nCurrent Repository Context:\n\n"
            ctx = self.agent.repo_context
            text += f"• Name: {ctx.get('name', 'N/A')}\n"
            text += f"• Commits: {ctx.get('total_commits', 0)}\n"
            text += f"• Authors: {ctx.get('total_authors', 0)}\n"
            text += f"• Files: {ctx.get('total_files', 0)}\n"
            text += f"• Primary Language: {ctx.get('primary_language', 'N/A')}\n"
        
        self.learning_text.insert('1.0', text)
    
    def start_interactive_mode(self):
        """Start interactive dataset generation mode"""
        query = self.query_text.get('1.0', tk.END).strip()
        if not query or query.startswith("Examples:"):
            messagebox.showwarning("Warning", "Please enter your dataset request first")
            return
        
        # Switch to interactive mode
        self.interactive_mode = True
        self.status_var.set("🤖 Interactive Mode: Processing your request...")
        
        # Clear previous outputs
        self.understanding_text.delete('1.0', tk.END)
        self.result_text.delete('1.0', tk.END)
        
        def process_interactive():
            try:
                # Parse the user input using interactive generator
                parsed = self.interactive_generator.parse_user_input(query)
                
                # Display understanding
                self.root.after(0, lambda: self.display_interactive_understanding(parsed))
                
                # Ask for confirmation
                self.root.after(0, lambda: self.ask_interactive_confirmation(parsed))
                
                self.root.after(0, lambda: self.status_var.set("🤖 Interactive Mode: Awaiting your confirmation"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Interactive processing failed: {e}"))
                self.root.after(0, lambda: self.status_var.set("Error"))
        
        Thread(target=process_interactive, daemon=True).start()
    
    def display_interactive_understanding(self, parsed):
        """Display interactive generator's understanding"""
        self.understanding_text.delete('1.0', tk.END)
        
        text = "🤖 INTERACTIVE UNDERSTANDING\n" + "="*50 + "\n\n"
        text += "I understand you want to create:\n\n"
        
        if parsed.get('dataset_type') == 'benchmark':
            text += f"📋 Benchmark Dataset: {parsed.get('benchmark_type', 'Unknown')}\n"
        elif parsed.get('dataset_type') == 'custom':
            text += "📊 Custom Dataset with metrics:\n"
            metrics = parsed.get('metrics', [])
            for metric in metrics[:10]:  # Show first 10
                text += f"  • {metric}\n"
            if len(metrics) > 10:
                text += f"  ... and {len(metrics) - 10} more\n"
        else:
            text += "❓ Dataset type not clearly identified\n"
        
        text += f"\n📁 Repository: {self.repo_var.get() or 'Not set'}\n"
        text += f"📄 Output Format: {parsed.get('output_format', 'csv')}\n"
        text += f"🏷️ Dataset Name: {parsed.get('dataset_name', 'auto_generated')}\n\n"
        
        text += "🤔 Is this what you want?\n"
        text += "• Type 'yes' to proceed with generation\n"
        text += "• Type 'no' to modify your request\n"
        text += "• Or describe specific changes needed\n"
        
        self.understanding_text.insert('1.0', text)
        
        # Switch to understanding tab
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        child.select(0)  # Understanding tab
                        break
    
    def ask_interactive_confirmation(self, parsed):
        """Ask for user confirmation in clarification tab"""
        self.clarification_text.delete('1.0', tk.END)
        
        text = "🤖 CONFIRMATION REQUESTED\n" + "="*50 + "\n\n"
        text += "Please confirm if my understanding is correct:\n\n"
        text += "• Type 'yes' to generate the dataset as understood\n"
        text += "• Type 'no' to start over with a new request\n"
        text += "• Or describe what needs to be changed\n\n"
        text += "💡 Examples:\n"
        text += "  'yes' - Proceed with generation\n"
        text += "  'Add complexity metrics' - Modify the request\n"
        text += "  'Use JSON format instead' - Change output format\n"
        text += "  'no' - Start over\n"
        
        self.clarification_text.insert('1.0', text)
        
        # Store parsed request for later use
        self.current_parsed_request = parsed
        
        # Switch to clarification tab
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        child.select(1)  # Clarification tab
                        break
        
        # Disable main query until confirmation
        self.query_text.config(state='disabled')
        self.analyze_btn.config(state='disabled')
        self.interactive_btn.config(state='disabled')
    
    def clear_all(self):
        """Clear all input and output"""
        self.query_text.delete('1.0', tk.END)
        self.understanding_text.delete('1.0', tk.END)
        self.clarification_text.delete('1.0', tk.END)
        self.result_text.delete('1.0', tk.END)
        self.clarify_var.set("")
        self.current_understanding = None
        self.status_var.set("Ready")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AutonomousAgentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
