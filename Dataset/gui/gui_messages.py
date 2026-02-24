"""MessagesMixin — message display, logging, and approval UI methods."""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import queue
import subprocess
import platform
from datetime import datetime
from typing import List, Dict
try:
    from .gui_types import MessageType, Task, TaskStatus
except ImportError:
    from gui_types import MessageType, Task, TaskStatus


class MessagesMixin:
    def add_agent_message(self, msg_type: MessageType, content: str, actions: List[Dict] = None):
        """Add a message to the agent panel"""
        self.message_queue.put((msg_type, content, actions or []))

    def process_message_queue(self):
        """Process messages from queue (thread-safe)"""
        try:
            while True:
                msg_type, content, actions = self.message_queue.get_nowait()
                self._display_message(msg_type, content, actions)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_message_queue)

    def _display_message(self, msg_type: MessageType, content: str, actions: List[Dict]):
        """Display a message in the agent panel"""
        self.message_text.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M")

        # Body tag per message type
        body_tag_map = {
            MessageType.SYSTEM:   'system',
            MessageType.USER:     'user',
            MessageType.THINKING: 'thinking',
            MessageType.ACTION:   'action',
            MessageType.SUCCESS:  'success',
            MessageType.ERROR:    'error',
            MessageType.QUESTION: 'question',
            MessageType.INFO:     'info',
        }
        body_tag = body_tag_map.get(msg_type, 'system')

        # Header tag + prefix icon per message type
        if msg_type == MessageType.USER:
            hdr_tag    = 'hdr_user'
            hdr_prefix = "YOU"
        elif msg_type == MessageType.SUCCESS:
            hdr_tag    = 'hdr_success'
            hdr_prefix = "AGENT ✓"
        elif msg_type == MessageType.ERROR:
            hdr_tag    = 'hdr_error'
            hdr_prefix = "AGENT ✗"
        elif msg_type == MessageType.QUESTION:
            hdr_tag    = 'hdr_question'
            hdr_prefix = "AGENT ?"
        elif msg_type == MessageType.SYSTEM:
            hdr_tag    = 'hdr_system'
            hdr_prefix = "SYSTEM"
        else:
            # THINKING, ACTION, INFO — all "agent" neutral
            hdr_tag    = 'hdr_agent'
            hdr_prefix = "AGENT"

        self.message_text.insert(tk.END, f"\n{hdr_prefix} [{timestamp}]\n", hdr_tag)
        self.message_text.insert(tk.END, f"{content}\n", body_tag)

        # Render action buttons if any
        if actions:
            for idx, action in enumerate(actions):
                label = action.get('label', 'Open')
                callback = action.get('callback')
                if callback:
                    btn = tk.Button(
                        self.message_text,
                        text=f"  {label}  ",
                        font=('Segoe UI', 8),
                        bg=self.colors['accent'],
                        fg='white',
                        relief='flat',
                        cursor='hand2',
                        command=callback
                    )
                    self.message_text.window_create(tk.END, window=btn)
                    # add small gap between buttons
                    if idx < len(actions) - 1:
                        self.message_text.insert(tk.END, "   ")
            # put a newline after all buttons (only one)
            self.message_text.insert(tk.END, "\n")

        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)

    def update_task_panel(self):
        """Update the task list panel"""
        # Clear existing widgets
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        # Count completed
        completed = sum(1 for t in self.task_manager.tasks 
                       if t.status == TaskStatus.COMPLETED)
        total = len(self.task_manager.tasks)
        self.task_progress_var.set(f"{completed}/{total} tasks")
        
        # Progress
        if total > 0:
            self.progress_var.set((completed / total) * 100)
        
        # Add task widgets
        for i, task in enumerate(self.task_manager.tasks):
            task_frame = ttk.Frame(self.task_list_frame)
            task_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Status indicator
            status_colors = {
                TaskStatus.PENDING: ' ',
                TaskStatus.WAITING_APPROVAL: ' ',
                TaskStatus.IN_PROGRESS: ' ',
                TaskStatus.COMPLETED: ' ',
                TaskStatus.FAILED: ' ',
                TaskStatus.SKIPPED: ' '
            }
            
            # Determine style based on status
            if task.status == TaskStatus.IN_PROGRESS or task.status == TaskStatus.WAITING_APPROVAL:
                style = 'TaskActive.TLabel'
                bg = '#e3f2fd'
            elif task.status == TaskStatus.COMPLETED:
                style = 'TaskDone.TLabel'
                bg = '#e8f5e9'
            elif task.status == TaskStatus.FAILED:
                style = 'TaskPending.TLabel'
                bg = '#ffebee'
            else:
                style = 'TaskPending.TLabel'
                bg = 'white'
            
            # Task content
            status_icon = status_colors.get(task.status, '⏳')
            task_text = f"{status_icon} {task.id}. {task.title}"
            
            task_label = ttk.Label(task_frame, text=task_text, style=style)
            task_label.pack(anchor=tk.W)
            
            # Description
            desc_label = ttk.Label(task_frame, text=f"   {task.description}",
                                   font=('Segoe UI', 9), foreground='gray')
            desc_label.pack(anchor=tk.W)
            
            # Result or error
            if task.result:
                result_label = ttk.Label(task_frame, text=f"   → {task.result}",
                                         font=('Segoe UI', 9), foreground='green')
                result_label.pack(anchor=tk.W)
            elif task.error:
                error_label = ttk.Label(task_frame, text=f"   ✗ {task.error}",
                                        font=('Segoe UI', 9), foreground='red')
                error_label.pack(anchor=tk.W)
                
            # Separator
            ttk.Separator(task_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
            

    def show_approval_request(self, task: Task):
        """Show approval request for a task"""
        self.approval_text.config(text=f"Task: {task.title}\n\n{task.description}\n\nApprove this action?")
        self.set_approval_visible(True)
        
        self.add_agent_message(MessageType.QUESTION,
            f"**Approval Required**\n\n"
            f"**Task:** {task.title}\n"
            f"**Description:** {task.description}\n\n"
            f"Please approve, reject, or skip this task."
        )

    def set_approval_visible(self, visible: bool):
        """Show or hide approval section"""
        if visible:
            self.approve_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            self.skip_btn.config(state=tk.NORMAL)
        else:
            self.approve_btn.config(state=tk.DISABLED)
            self.reject_btn.config(state=tk.DISABLED)
            self.skip_btn.config(state=tk.DISABLED)
            self.approval_text.config(text="No pending approvals")

    def log_to_formula(self, log_type: str, text: str):
        """Add log to formula execution logs"""
        if not hasattr(self, 'formula_execution_logs'):
            return
        
        import pandas as pd
        self.formula_execution_logs.configure(state=tk.NORMAL)
        timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
        self.formula_execution_logs.insert(tk.END, f"[{timestamp}] {text}\n", log_type)
        self.formula_execution_logs.see(tk.END)
        self.formula_execution_logs.configure(state=tk.DISABLED)

    def _show_formula_feedback(self, output_path, result_df, new_cols):
        """Show feedback dialog after formula generation"""
        # Create feedback dialog
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Formula Generation Complete")
        feedback_window.geometry("600x400")
        
        # Success message
        ttk.Label(feedback_window, text="Formula Generated Successfully!",
                 font=('Segoe UI', 14, 'bold'), foreground='green').pack(pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(feedback_window, text="  Results", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(stats_frame, text=f"Rows: {len(result_df)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"New Columns: {', '.join(new_cols)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(stats_frame, text=f"File: {output_path.name}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        # Actions
        actions_frame = ttk.LabelFrame(feedback_window, text="Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def open_csv():
            try:
                if platform.system() == 'Windows':
                    os.startfile(output_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', output_path])
                else:  # Linux
                    subprocess.run(['xdg-open', output_path])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
        
        def open_folder():
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['explorer', '/select,', str(output_path)])
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', '-R', str(output_path)])
                else:
                    subprocess.run(['xdg-open', str(output_path.parent)])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        
        ttk.Button(actions_frame, text="Open CSV", command=open_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="  Open Folder", command=open_folder).pack(side=tk.LEFT, padx=5)
        
        # Feedback
        feedback_frame = ttk.LabelFrame(feedback_window, text="Rate This Generation", padding=10)
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(feedback_frame, text="Was the result correct?").pack(anchor=tk.W)
        
        rating_var = tk.StringVar(value="")
        
        ttk.Radiobutton(feedback_frame, text="Perfect - exactly what I needed", 
                       variable=rating_var, value="perfect").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Good - mostly correct", 
                       variable=rating_var, value="good").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Okay - needs some fixes", 
                       variable=rating_var, value="okay").pack(anchor=tk.W)
        ttk.Radiobutton(feedback_frame, text="Wrong - incorrect results", 
                       variable=rating_var, value="wrong").pack(anchor=tk.W)
        
        def submit_feedback():
            rating = rating_var.get()
            if rating:
                self.log_system(f"User feedback: {rating} for {output_path.name}")
                messagebox.showinfo("Thank You!", "Feedback recorded!")
                feedback_window.destroy()
            else:
                messagebox.showwarning("No Rating", "Please select a rating first")
        
        ttk.Button(feedback_frame, text="Submit Feedback", command=submit_feedback,
                  style='Accent.TButton').pack(pady=10)
        
        ttk.Button(feedback_window, text="Close", command=feedback_window.destroy).pack(pady=10)

    def jury_log(self, message: str, tag: str = 'system'):
        """Log message to jury conversation panel"""
        if not hasattr(self, 'jury_conversation'):
            return
        
        self.jury_conversation.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.jury_conversation.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.jury_conversation.see(tk.END)
        self.jury_conversation.configure(state=tk.DISABLED)

    def log_system(self, text: str):
        """Add log to system logs tab"""
        if not hasattr(self, 'system_logs_text'):
            return
        
        import pandas as pd
        self.system_logs_text.configure(state=tk.NORMAL)
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        self.system_logs_text.insert(tk.END, f"[{timestamp}] {text}\n")
        self.system_logs_text.see(tk.END)
        self.system_logs_text.configure(state=tk.DISABLED)

    def orch_log_message(self, message: str, tag: str = 'info'):
        """Log message to orchestrator log"""
        if not hasattr(self, 'orch_log'):
            return
        self.orch_log.configure(state=tk.NORMAL)
        self.orch_log.insert(tk.END, f"{message}\n", tag)
        self.orch_log.see(tk.END)
        self.orch_log.configure(state=tk.DISABLED)

