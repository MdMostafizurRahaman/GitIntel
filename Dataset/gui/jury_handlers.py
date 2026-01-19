"""
Handler Methods for Integrated Jury System in GUI
Add these methods to the AgenticDatasetGUI class in main.py
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import threading
from typing import Dict
from integrated_jury_system import IntegratedJurySystem

# Add these methods to the AgenticDatasetGUI class:

def jury_log(self, message: str, tag: str = 'system'):
    """Log message to jury conversation panel"""
    if not hasattr(self, 'jury_conversation'):
        return
    
    self.jury_conversation.configure(state=tk.NORMAL)
    timestamp = datetime.now().strftime('%H:%M:%S')
    self.jury_conversation.insert(tk.END, f"[{timestamp}] {message}\n", tag)
    self.jury_conversation.see(tk.END)
    self.jury_conversation.configure(state=tk.DISABLED)

def jury_start_new_request(self):
    """Start a new request in integrated jury system"""
    if not self.integrated_jury:
        messagebox.showerror("Error", "Integrated jury system not available")
        return
    
    user_question = self.jury_input.get('1.0', tk.END).strip()
    
    if not user_question:
        messagebox.showwarning("Empty Input", "Please describe what you need")
        return
    
    # Clear input
    self.jury_input.delete('1.0', tk.END)
    
    # Log user question
    self.jury_log(f"YOU: {user_question}", 'question')
    self.jury_log("Starting integrated jury workflow...", 'thinking')
    
    # Update status
    self.jury_status_var.set("Processing your request...")
    self.jury_session_active = True
    self.jury_session_info.set(f"Session: {self.integrated_jury.session_id}")
    
    # Run workflow in background thread
    thread = threading.Thread(
        target=self._jury_run_workflow_thread,
        args=(user_question,),
        daemon=True
    )
    thread.start()

def _jury_run_workflow_thread(self, user_question: str):
    """Run integrated jury workflow in background thread"""
    try:
        def progress_callback(msg):
            self.root.after(0, lambda: self.jury_log(msg, 'system'))
        
        result = self.integrated_jury.run_full_workflow(
            user_question=user_question,
            progress_callback=progress_callback
        )
        
        # Handle result on main thread
        self.root.after(0, lambda: self._jury_handle_result(result))
        
    except Exception as e:
        error_msg = f"ERROR: {str(e)}"
        self.root.after(0, lambda: self.jury_log(error_msg, 'error'))
        self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

def _jury_handle_result(self, result: Dict):
    """Handle result from jury workflow"""
    status = result.get('status')
    
    if status == 'needs_clarification':
        # Need user to answer clarifying questions
        self.jury_clarification_pending = True
        self.jury_answer_btn.configure(state=tk.NORMAL)
        
        self.jury_log("I need more information to help you:", 'question')
        for q in result.get('questions', []):
            self.jury_log(f"  • {q}", 'question')
        
        self.jury_log(f"\nMy current understanding ({result.get('confidence', 0)}% confident):", 'thinking')
        self.jury_log(result.get('current_understanding', ''), 'thinking')
        
        self.jury_status_var.set("Please answer the clarifying questions above")
        
    elif status == 'success':
        # Success! Show code
        self.jury_clarification_pending = False
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        self.jury_log("SUCCESS! Code generated and validated!", 'system')
        self.jury_log(f"\nIterations: {result['iterations']}", 'system')
        self.jury_log(f"Test Results: {result['test_results']['passing_llms']}/3 LLMs passed", 'system')
        self.jury_log(f"Total Tests: {result['test_results']['total_passed']}/{result['test_results']['total_tests']} passed", 'system')
        
        self.jury_log("\n" + "="*60, 'system')
        self.jury_log("GENERATED CODE:", 'system')
        self.jury_log("="*60, 'system')
        self.jury_log(result['code'], 'answer')
        
        self.jury_status_var.set("✅ Complete! Code ready to use")
        self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
        
        # Offer to save code
        self.root.after(100, lambda: self._jury_offer_save_code(result))
        
    elif status == 'human_intervention_required':
        # Failed after max iterations
        self.jury_clarification_pending = False
        self.jury_answer_btn.configure(state=tk.DISABLED)
        
        self.jury_log("HUMAN INTERVENTION NEEDED", 'error')
        self.jury_log(f"\n{result['message']}", 'error')
        self.jury_log(f"\nAttempted {len(result['iterations'])} iterations", 'error')
        
        if result.get('last_code'):
            self.jury_log("\nLast generated code (may have issues):", 'thinking')
            self.jury_log(result['last_code'], 'answer')
        
        if result.get('last_feedback'):
            self.jury_log("\nLast test feedback:", 'error')
            self.jury_log(result['last_feedback'], 'error')
        
        self.jury_status_var.set("Failed - Human help needed")
        self.jury_session_info.set(f"Session: {result['session_id']} | Results: {result['session_dir']}")
        
    else:
        self.jury_log(f"Unknown status: {status}", 'error')

def jury_provide_feedback(self):
    """Provide answers to clarifying questions"""
    if not self.jury_clarification_pending:
        messagebox.showinfo("Info", "No clarification needed at this time")
        return
    
    user_feedback = self.jury_input.get('1.0', tk.END).strip()
    
    if not user_feedback:
        messagebox.showwarning("Empty Input", "Please provide your answers")
        return
    
    # Clear input
    self.jury_input.delete('1.0', tk.END)
    
    # Log feedback
    self.jury_log(f"\nYOU: {user_feedback}", 'answer')
    self.jury_log("Processing your feedback...", 'thinking')
    
    # Update status
    self.jury_status_var.set("Processing feedback...")
    self.jury_answer_btn.configure(state=tk.DISABLED)
    
    # Continue clarification in thread
    thread = threading.Thread(
        target=self._jury_continue_clarification_thread,
        args=(user_feedback,),
        daemon=True
    )
    thread.start()

def _jury_continue_clarification_thread(self, user_feedback: str):
    """Continue clarification process in background"""
    try:
        result = self.integrated_jury.provide_clarification(user_feedback)
        
        if result['status'] == 'clarified':
            # Ready to proceed! Now run full generation
            self.root.after(0, lambda: self.jury_log("✅ Requirements clarified! Starting code generation...", 'system'))
            
            # Continue with full workflow
            def progress_callback(msg):
                self.root.after(0, lambda: self.jury_log(msg, 'system'))
            
            # Note: We need to manually continue the workflow here
            # For now, ask user to restart with clarified requirements
            self.root.after(0, lambda: self.jury_log("Please describe your requirement again with the clarifications", 'question'))
            self.root.after(0, lambda: self.jury_status_var.set("Ready for new request"))
            
        else:
            # Need more clarification
            self.root.after(0, lambda: self._jury_handle_more_clarification(result))
            
    except Exception as e:
        error_msg = f"ERROR: {str(e)}"
        self.root.after(0, lambda: self.jury_log(error_msg, 'error'))
        self.root.after(0, lambda: self.jury_status_var.set("Error occurred"))

def _jury_handle_more_clarification(self, result: Dict):
    """Handle need for more clarification"""
    self.jury_clarification_pending = True
    self.jury_answer_btn.configure(state=tk.NORMAL)
    
    self.jury_log("\nI still need a bit more information:", 'question')
    for q in result.get('questions', []):
        self.jury_log(f"  • {q}", 'question')
    
    self.jury_log(f"\nMy understanding so far ({result.get('confidence', 0)}% confident):", 'thinking')
    self.jury_log(result.get('current_understanding', ''), 'thinking')
    
    self.jury_status_var.set("Please provide more details")

def jury_reset_session(self):
    """Reset jury session"""
    if self.jury_session_active:
        confirm = messagebox.askyesno("Confirm Reset", 
                                      "Are you sure you want to reset the current session?")
        if not confirm:
            return
    
    # Reset state
    self.integrated_jury = IntegratedJurySystem()
    self.jury_session_active = False
    self.jury_clarification_pending = False
    
    # Clear UI
    self.jury_conversation.configure(state=tk.NORMAL)
    self.jury_conversation.delete('1.0', tk.END)
    self.jury_conversation.configure(state=tk.DISABLED)
    
    self.jury_input.delete('1.0', tk.END)
    
    # Reset status
    self.jury_status_var.set("Ready to help! Describe what you need...")
    self.jury_session_info.set("No active session")
    self.jury_answer_btn.configure(state=tk.DISABLED)
    
    self.jury_log("Session reset. Ready for new request!", 'system')

def _jury_offer_save_code(self, result: Dict):
    """Offer to save generated code"""
    response = messagebox.askyesnocancel(
        "Save Code?",
        f"Code generated successfully!\n\n"
        f"Function: {result['function_name']}\n"
        f"Tests passed: {result['test_results']['passing_llms']}/3 LLMs\n\n"
        f"Would you like to save the code to a file?"
    )
    
    if response is None:  # Cancel
        return
    
    if response:  # Yes - save
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
            initialfile=f"{result['function_name']}.py"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(f"# Generated by Integrated Jury System\n")
                    f.write(f"# Session: {result['session_id']}\n")
                    f.write(f"# Validation: {result['test_results']['passing_llms']}/3 LLMs passed\n")
                    f.write(f"# Description: {result['description']}\n\n")
                    f.write(result['code'])
                
                messagebox.showinfo("Success", f"Code saved to:\n{file_path}")
                self.jury_log(f"\nCode saved to: {file_path}", 'system')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save code:\n{str(e)}")
