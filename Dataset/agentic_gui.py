"""
🤖 Agentic Dataset Generator - Integrated GUI
==============================================

Integrates the truly agentic system with existing GUI
Features:
- Latest Gemini 2.5 models
- Extensive user communication
- ONLY real repository data
- Preview before generation
- Confirmation required at every step
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from agentic_dataset_system import AgenticDatasetSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticDatasetGUI:
    """GUI for the truly agentic dataset generation system"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Agentic Dataset Generator - Real Data Only")
        self.root.geometry("1000x800")
        
        # Initialize agentic system
        try:
            self.system = AgenticDatasetSystem()
            self.system_ready = True
        except Exception as e:
            self.system = None
            self.system_ready = False
            messagebox.showerror("Error", f"Failed to initialize system: {e}")
        
        self.conversation_active = False
        self.preview_generated = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="🤖 Agentic Dataset Generator", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        subtitle = ttk.Label(main_frame, 
                            text="AI asks questions, shows preview, gets confirmation - Uses ONLY real repository data",
                            font=('Arial', 10, 'italic'))
        subtitle.grid(row=1, column=0, pady=5, sticky=tk.W)
        
        # Repository selection
        repo_frame = ttk.LabelFrame(main_frame, text="📁 Repository (Real Data Source)", padding="10")
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
        
        # Metrics info
        self.metrics_label = ttk.Label(repo_frame, text="Available metrics: Not loaded yet", 
                                       font=('Arial', 9, 'italic'))
        self.metrics_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # Conversation area
        conv_frame = ttk.LabelFrame(main_frame, text="💬 Conversation with AI Agent", padding="10")
        conv_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        conv_frame.columnconfigure(0, weight=1)
        conv_frame.rowconfigure(0, weight=1)
        
        # Conversation display
        self.conv_text = scrolledtext.ScrolledText(conv_frame, wrap=tk.WORD, height=20,
                                                   font=('Consolas', 10))
        self.conv_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure tags for colors
        self.conv_text.tag_config("user", foreground="blue", font=('Consolas', 10, 'bold'))
        self.conv_text.tag_config("agent", foreground="green", font=('Consolas', 10))
        self.conv_text.tag_config("system", foreground="red", font=('Consolas', 10, 'italic'))
        
        # Input area
        input_frame = ttk.Frame(conv_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=3,
                                                    font=('Consolas', 10))
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # Button frame
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="🚀 Start Conversation", 
                                    command=self.start_conversation)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.respond_btn = ttk.Button(btn_frame, text="💬 Respond", 
                                     command=self.respond_to_agent, state=tk.DISABLED)
        self.respond_btn.pack(side=tk.LEFT, padx=5)
        
        self.preview_btn = ttk.Button(btn_frame, text="👁️ Generate Preview", 
                                     command=self.generate_preview, state=tk.DISABLED)
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        self.confirm_btn = ttk.Button(btn_frame, text="✅ Confirm & Generate", 
                                     command=self.confirm_generate, state=tk.DISABLED)
        self.confirm_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="🗑️ Clear", 
                              command=self.clear_conversation)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Set repository to begin" if self.system_ready else "System not available")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # Add hint text
        self.add_to_conversation("🤖 SYSTEM", """Welcome to the Agentic Dataset Generator!

This system:
✅ Asks clarifying questions until it fully understands your needs
✅ Uses ONLY real data from your Git repository (NO MOCK DATA)
✅ Shows you a preview of the dataset before generating
✅ Requires your confirmation before proceeding

Steps:
1. Set your Git repository path
2. Describe what dataset you want
3. Answer the AI's questions
4. Review the preview
5. Confirm to generate the final dataset

Let's begin! Set a repository and tell me what you need.""", "system")
    
    def browse_repo(self):
        """Browse for repository directory"""
        directory = filedialog.askdirectory(title="Select Git Repository")
        if directory:
            self.repo_var.set(directory)
    
    def set_repository(self):
        """Set the repository in the system"""
        if not self.system_ready:
            messagebox.showerror("Error", "System not initialized")
            return
        
        repo_path = self.repo_var.get().strip()
        if not repo_path:
            messagebox.showwarning("Warning", "Please select a repository")
            return
        
        self.status_var.set("⏳ Analyzing repository...")
        self.root.update()
        
        def set_repo_thread():
            try:
                success = self.system.set_repository(repo_path)
                
                if success:
                    metrics_count = len(self.system.available_metrics)
                    self.root.after(0, lambda: self.on_repo_set_success(metrics_count))
                else:
                    self.root.after(0, lambda: self.on_repo_set_error("Failed to set repository"))
            except Exception as e:
                self.root.after(0, lambda: self.on_repo_set_error(str(e)))
        
        thread = threading.Thread(target=set_repo_thread, daemon=True)
        thread.start()
    
    def on_repo_set_success(self, metrics_count):
        """Handle successful repository set"""
        self.status_var.set(f"✅ Repository set - {metrics_count} metrics available")
        self.metrics_label.config(text=f"Available metrics: {metrics_count} (extracted from real repository)")
        self.start_btn.config(state=tk.NORMAL)
        
        self.add_to_conversation("🤖 SYSTEM", 
                               f"✅ Repository analyzed!\n{metrics_count} real metrics available.\nDescribe what dataset you want to generate.", 
                               "system")
    
    def on_repo_set_error(self, error_msg):
        """Handle repository set error"""
        self.status_var.set(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", f"Failed to set repository: {error_msg}")
    
    def start_conversation(self):
        """Start conversation with agent"""
        if not self.system or not self.system.repo_path:
            messagebox.showwarning("Warning", "Please set a repository first")
            return
        
        user_request = self.input_text.get("1.0", tk.END).strip()
        if not user_request:
            messagebox.showwarning("Warning", "Please describe what dataset you want")
            return
        
        self.add_to_conversation("👤 YOU", user_request, "user")
        self.input_text.delete("1.0", tk.END)
        
        self.status_var.set("⏳ Agent is analyzing...")
        self.start_btn.config(state=tk.DISABLED)
        
        def conversation_thread():
            try:
                response = self.system.start_conversation(user_request)
                self.root.after(0, lambda: self.on_agent_response(response))
            except Exception as e:
                self.root.after(0, lambda: self.on_conversation_error(str(e)))
        
        thread = threading.Thread(target=conversation_thread, daemon=True)
        thread.start()
    
    def respond_to_agent(self):
        """Respond to agent's questions"""
        user_response = self.input_text.get("1.0", tk.END).strip()
        if not user_response:
            messagebox.showwarning("Warning", "Please enter your response")
            return
        
        self.add_to_conversation("👤 YOU", user_response, "user")
        self.input_text.delete("1.0", tk.END)
        
        self.status_var.set("⏳ Agent is processing...")
        self.respond_btn.config(state=tk.DISABLED)
        
        def respond_thread():
            try:
                response = self.system.continue_conversation(user_response)
                self.root.after(0, lambda: self.on_agent_response(response))
            except Exception as e:
                self.root.after(0, lambda: self.on_conversation_error(str(e)))
        
        thread = threading.Thread(target=respond_thread, daemon=True)
        thread.start()
    
    def on_agent_response(self, response):
        """Handle agent's response"""
        self.add_to_conversation("🤖 AGENT", response, "agent")
        self.status_var.set("✅ Agent responded - Read and reply")
        
        self.conversation_active = True
        self.respond_btn.config(state=tk.NORMAL)
        
        # Check if agent is ready for preview
        if self.system.current_requirement and not self.system.current_requirement.confirmed:
            if "proceed" in response.lower() or "confirm" in response.lower():
                self.preview_btn.config(state=tk.NORMAL)
                self.add_to_conversation("🤖 SYSTEM", 
                                       "\n💡 Ready for preview? Click 'Generate Preview' button to see how the dataset will look!", 
                                       "system")
    
    def generate_preview(self):
        """Generate dataset preview"""
        self.status_var.set("⏳ Extracting REAL data from repository...")
        self.preview_btn.config(state=tk.DISABLED)
        
        def preview_thread():
            try:
                preview = self.system.generate_preview()
                
                if preview:
                    preview_text = self.system.show_preview_to_user()
                    self.root.after(0, lambda: self.on_preview_generated(preview_text))
                else:
                    self.root.after(0, lambda: self.on_preview_error("Failed to generate preview"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_preview_error(str(e)))
        
        thread = threading.Thread(target=preview_thread, daemon=True)
        thread.start()
    
    def on_preview_generated(self, preview_text):
        """Handle successful preview generation"""
        self.add_to_conversation("📊 PREVIEW", preview_text, "system")
        self.status_var.set("✅ Preview generated from REAL data")
        
        self.preview_generated = True
        self.confirm_btn.config(state=tk.NORMAL)
        self.preview_btn.config(state=tk.DISABLED)
    
    def on_preview_error(self, error_msg):
        """Handle preview error"""
        self.status_var.set(f"❌ Preview error: {error_msg}")
        self.add_to_conversation("❌ ERROR", f"Failed to generate preview: {error_msg}", "system")
        self.preview_btn.config(state=tk.NORMAL)
    
    def confirm_generate(self):
        """Confirm and generate full dataset"""
        confirm = messagebox.askyesno("Confirm Generation", 
                                     "Generate full dataset with REAL repository data?\n\nThis cannot be undone.")
        
        if not confirm:
            return
        
        self.status_var.set("⏳ Generating full dataset from repository...")
        self.confirm_btn.config(state=tk.DISABLED)
        
        def generate_thread():
            try:
                output_path = self.system.generate_full_dataset()
                
                if output_path:
                    self.root.after(0, lambda: self.on_generation_success(output_path))
                else:
                    self.root.after(0, lambda: self.on_generation_error("Generation failed"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_generation_error(str(e)))
        
        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()
    
    def on_generation_success(self, output_path):
        """Handle successful dataset generation"""
        self.status_var.set(f"✅ Dataset generated!")
        self.add_to_conversation("✅ SUCCESS", 
                               f"Full dataset generated successfully!\n\nSaved to: {output_path}\n\nThis contains REAL data from your repository.", 
                               "system")
        
        messagebox.showinfo("Success", f"Dataset generated successfully!\n\nSaved to:\n{output_path}")
        
        # Reset for new conversation
        self.conversation_active = False
        self.preview_generated = False
        self.start_btn.config(state=tk.NORMAL)
        self.respond_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
        self.confirm_btn.config(state=tk.DISABLED)
    
    def on_generation_error(self, error_msg):
        """Handle generation error"""
        self.status_var.set(f"❌ Generation error")
        self.add_to_conversation("❌ ERROR", f"Failed to generate dataset: {error_msg}", "system")
        messagebox.showerror("Error", f"Failed to generate dataset:\n{error_msg}")
        self.confirm_btn.config(state=tk.NORMAL)
    
    def on_conversation_error(self, error_msg):
        """Handle conversation error"""
        self.status_var.set(f"❌ Error: {error_msg}")
        self.add_to_conversation("❌ ERROR", error_msg, "system")
        self.respond_btn.config(state=tk.NORMAL)
    
    def add_to_conversation(self, prefix, message, tag):
        """Add message to conversation display"""
        self.conv_text.insert(tk.END, f"\n{prefix}:\n", tag)
        self.conv_text.insert(tk.END, f"{message}\n{'='*80}\n")
        self.conv_text.see(tk.END)
    
    def clear_conversation(self):
        """Clear the conversation"""
        if self.conversation_active:
            confirm = messagebox.askyesno("Clear Conversation", 
                                         "Are you sure? This will reset the current conversation.")
            if not confirm:
                return
        
        self.conv_text.delete("1.0", tk.END)
        self.input_text.delete("1.0", tk.END)
        self.conversation_active = False
        self.preview_generated = False
        
        if self.system:
            self.system.conversation_history = []
            self.system.current_requirement = None
            self.system.current_preview = None
        
        self.start_btn.config(state=tk.NORMAL if self.system and self.system.repo_path else tk.DISABLED)
        self.respond_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
        self.confirm_btn.config(state=tk.DISABLED)
        
        self.status_var.set("Conversation cleared - Start fresh")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AgenticDatasetGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
