"""RepoMixin — repository browse, clone, and set operations."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os, subprocess
from pathlib import Path
try:
    from .gui_types import MessageType
except ImportError:
    from gui_types import MessageType


class RepoMixin:
    def browse_folder(self):
        """Browse for repository folder"""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.repo_var.set(folder)
            self.set_repository()
    
    def clone_repository(self):
        """Clone a Git repository from URL directly to GitIntelProject/clone/<repo_name>"""
        repo_input = self.repo_var.get().strip()
        
        # Validate input
        if not repo_input or 'Enter' in repo_input:
            messagebox.showwarning("Clone Repository", 
                "Please enter a GitHub URL (e.g., https://github.com/user/repo) or owner/repo")
            return
        
        # Convert owner/repo to full URL
        if '/' in repo_input and not repo_input.startswith(('http://', 'https://', 'git@')):
            repo_input = f"https://github.com/{repo_input}.git"
        
        # Check if it looks like a Git URL
        if not any(x in repo_input.lower() for x in ['github.com', 'gitlab.com', 'bitbucket.org', '.git']):
            messagebox.showwarning("Clone Repository",
                "Please enter a valid Git repository URL\n\nExamples:\n" +
                "• https://github.com/apache/kafka\n" +
                "• apache/kafka\n" +
                "• git@github.com:apache/kafka.git")
            return
        
        # Create clone dialog
        clone_dialog = tk.Toplevel(self.root)
        clone_dialog.title("Clone Repository")
        clone_dialog.geometry("800x550")
        clone_dialog.grab_set()
        
        # Header
        ttk.Label(clone_dialog, text="Clone Git Repository", 
                  font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        # Repository URL display
        url_frame = ttk.LabelFrame(clone_dialog, text="Repository URL", padding=10)
        url_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        url_text = tk.Text(url_frame, height=2, wrap=tk.WORD, font=('Consolas', 9))
        url_text.pack(fill=tk.X)
        url_text.insert('1.0', repo_input)
        url_text.config(state=tk.DISABLED)
        
        # Auto-destination info (NO SELECTION - FIXED PATH)
        dest_frame = ttk.LabelFrame(clone_dialog, text="Auto Clone Destination (FIXED)", padding=10)
        dest_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Extract repo name from URL
        repo_name = repo_input.rstrip('/').split('/')[-1].replace('.git', '')
        
        # FIXED destination: GitIntelProject/clone/<repo_name>
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        clone_base = os.path.join(base_dir, "clone")
        final_dest = os.path.join(clone_base, repo_name)
        
        dest_display = tk.Text(dest_frame, height=2, wrap=tk.WORD, font=('Consolas', 9))
        dest_display.pack(fill=tk.X)
        dest_display.insert('1.0', final_dest)
        dest_display.config(state=tk.DISABLED)
        
        ttk.Label(dest_frame, text="  .git will be at this location", font=('Segoe UI', 9)).pack()
        
        # Progress area
        progress_frame = ttk.LabelFrame(clone_dialog, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        progress_text = scrolledtext.ScrolledText(progress_frame, height=15,
                                                   font=('Consolas', 8), wrap=tk.WORD)
        progress_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(clone_dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        clone_btn = ttk.Button(btn_frame, text="Start Clone (Fixed Path)", style='Accent.TButton')
        cancel_btn = ttk.Button(btn_frame, text="Cancel")
        
        def log_progress(message):
            """Thread-safe progress logging"""
            def update_text():
                if progress_text.winfo_exists():
                    progress_text.insert(tk.END, message + '\n')
                    progress_text.see(tk.END)
            clone_dialog.after(0, update_text)
        
        def start_clone():
            """Start cloning to FIXED GitIntelProject/clone/<repo_name>"""
            clone_btn.config(state=tk.DISABLED)
            cancel_btn.config(text="Close")
            
            def clone_thread():
                try:
                    # Create clone base directory
                    os.makedirs(clone_base, exist_ok=True)
                    log_progress(f"  Auto-destination: {clone_base}")
                    
                    # Check if already exists
                    if os.path.exists(final_dest):
                        log_progress(f"  Repository exists: {repo_name}")
                        log_progress(f"  Using existing clone at: {final_dest}")
                        
                        # Verify .git exists
                        if os.path.isdir(os.path.join(final_dest, '.git')):
                            log_progress(f"  .git directory confirmed")
                        else:
                            log_progress(f"   WARNING: .git directory NOT found!")
                    else:
                        log_progress(f"  Cloning {repo_name}...")
                        log_progress(f"   This may take a few minutes...")
                        
                        # Run git clone
                        process = subprocess.Popen(
                            ['git', 'clone', '--progress', repo_input, final_dest],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            bufsize=1
                        )
                        
                        # Stream output
                        for line in process.stdout:
                            log_progress(line.strip())
                        
                        process.wait()
                        
                        if process.returncode == 0:
                            log_progress(f"\n  Repository cloned successfully!")
                            
                            # Verify .git exists
                            if os.path.isdir(os.path.join(final_dest, '.git')):
                                log_progress(f"  .git directory confirmed")
                            else:
                                log_progress(f"   WARNING: .git directory NOT found after clone!")
                        else:
                            log_progress(f"\n  Clone failed with code {process.returncode}")
                            return
                    
                    # Set the repository in main window
                    log_progress(f"\n   Setting up repository...")
                    self.root.after(0, lambda: self.repo_var.set(final_dest))
                    self.root.after(0, lambda: self.set_repository())
                    
                    log_progress(f"\n  Ready! All work will happen in: {clone_base}")
                    clone_dialog.after(2000, clone_dialog.destroy)
                    
                except subprocess.CalledProcessError as e:
                    log_progress(f"\n  Git error: {e}")
                    log_progress(f"   Make sure Git is installed and URL is correct")
                except Exception as e:
                    log_progress(f"\n  Unexpected error: {e}")
                finally:
                    clone_dialog.after(0, lambda: clone_btn.config(state=tk.NORMAL))
            
            threading.Thread(target=clone_thread, daemon=True).start()
        
        clone_btn.config(command=start_clone)
        cancel_btn.config(command=clone_dialog.destroy)
        
        clone_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        cancel_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            
    def set_repository(self):
        """Set the repository — supports local paths and GitHub URLs"""
        repo_input = self.repo_var.get().strip()
        if not repo_input or 'Enter' in repo_input:
            messagebox.showwarning("Warning", "Please enter a repository path or GitHub URL")
            return

        try:
            self.repo_status.config(text="[...] Processing...", foreground='blue')
            self.root.update()

            # If enhanced_system is available, delegate to it
            if self.enhanced_system is not None:
                repo_info = self.enhanced_system.set_repository(repo_input)
                self.repo_path = str(self.enhanced_system.repo_path)
                repo_name = os.path.basename(self.repo_path)
                self.repo_status.config(text=repo_name, foreground='green')
                # Update topbar label from main thread
                self.root.after(0, lambda: self.topbar_repo_var.set(f"Repo: {repo_name}"))
                self.add_agent_message(MessageType.SUCCESS,
                    f"Repository set: {repo_name}\n"
                    f"Metrics discovered: {len(self.enhanced_system.available_metrics)}")
                return

            # Direct path handling (enhanced_system not available)
            path = Path(repo_input)

            if path.is_dir():
                self.repo_path = str(path.resolve())
                repo_name = path.name
                self.repo_status.config(text=repo_name, foreground='green')
                java_count = sum(1 for _ in path.rglob('*.java') if _.is_file())
                py_count   = sum(1 for _ in path.rglob('*.py')   if _.is_file())
                # Update topbar label from main thread
                self.root.after(0, lambda n=repo_name: self.topbar_repo_var.set(f"Repo: {n}"))
                self.add_agent_message(
                    MessageType.SUCCESS,
                    f"Repository set: {repo_name}\n"
                    f"  Java files  : {java_count}\n"
                    f"  Python files: {py_count}\n\n"
                    f"Ready — type your dataset request below.",
                )
            else:
                self.repo_status.config(text="Invalid path", foreground='red')
                self.add_agent_message(
                    MessageType.ERROR,
                    f"Path not found: {repo_input}\n"
                    "Please enter a valid local directory path.\n"
                    "Use the 'Browse' button to select a folder.",
                )

        except Exception as e:
            self.repo_status.config(text="Failed to set repository", foreground='red')
            self.add_agent_message(
                MessageType.ERROR,
                f"Repository setup failed: {str(e)[:150]}",
            )
            

