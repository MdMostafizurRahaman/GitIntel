#!/usr/bin/env python3
"""
Integration Guide: Autonomous Agent with GUI
============================================

This shows how to integrate the AutonomousDatasetAgent with the Tkinter GUI.
"""

from autonomous_agent import AutonomousDatasetAgent, AgentMode
import queue
import threading


class AgentIntegration:
    """Integration layer between GUI and Autonomous Agent"""
    
    def __init__(self, gui_callback=None):
        """
        Initialize the integration
        
        Args:
            gui_callback: Function to call for GUI updates
                         callback(message_type, content)
                         message_type: 'thinking', 'action', 'result', 'question'
        """
        self.agent = AutonomousDatasetAgent()
        self.gui_callback = gui_callback
        self.message_queue = queue.Queue()
        self.execution_thread = None
    
    def process_user_message(self, user_message: str) -> None:
        """
        Process user message in a separate thread
        
        Usage in GUI:
        ```
        integration.process_user_message(user_input)
        ```
        """
        # Parse mode and query
        mode, query = self.agent.parse_user_input(user_message)
        
        # Start execution in separate thread
        self.execution_thread = threading.Thread(
            target=self._execute_async,
            args=(mode, query)
        )
        self.execution_thread.daemon = True
        self.execution_thread.start()
    
    def _execute_async(self, mode: AgentMode, query: str) -> None:
        """Execute plan asynchronously"""
        try:
            # Show thinking
            self._emit("thinking", f"💭 Analyzing: {query}")
            
            # Generate plan
            plan = self.agent.generate_task_plan(query)
            
            # Show plan
            self._emit("info", f"🎯 Intent: {plan.get('intent')}")
            self._emit("info", f"📊 Metrics: {', '.join(plan.get('metrics', []))}")
            self._emit("info", f"📈 Type: {plan.get('dataset_type')}")
            
            # Show tasks
            self._emit("info", "\n📋 Tasks:")
            for i, task in enumerate(plan.get('tasks', []), 1):
                auto = "🤖" if task.get('auto_execute') else "❓"
                self._emit("info", f"  {i}. {auto} {task.get('task')}")
            
            # Execute
            if mode == AgentMode.ASK:
                self._execute_ask_mode(plan)
            else:
                self._execute_agent_mode(plan)
                
        except Exception as e:
            self._emit("error", f"❌ Error: {str(e)}")
    
    def _execute_ask_mode(self, plan: dict) -> None:
        """
        Execute in ASK mode - always asks for permission
        
        Flow:
        1. Show plan
        2. Ask "Start execution?" → Wait for approval
        3. For each task:
           a. Ask "Approve this task?" → Wait for approval
           b. Execute if approved
           c. Show result
        """
        self._emit("action", "▶️ ASK MODE - Will ask permission for each task")
        
        # Ask for overall approval
        self._emit("question", "Start execution in ASK mode?")
        # In GUI, this would wait for user response
        
        # For now, execute without individual task approval
        result = self.agent.execute_plan(plan, AgentMode.ASK)
        
        for msg in result.get('messages', []):
            self._emit("action", msg)
        
        if result['success']:
            self._emit("result", 
                f"✅ Completed {result['tasks_completed']}/{result['tasks_total']} tasks")
        else:
            self._emit("error", "❌ Execution had failures")
    
    def _execute_agent_mode(self, plan: dict) -> None:
        """
        Execute in AGENT mode - autonomous execution with feedback
        
        Flow:
        1. Show plan
        2. Execute all tasks automatically (no permission)
        3. Show results
        4. Ask "Any feedback or changes?"
        5. If feedback:
           a. Process with LLM
           b. Suggest improvements
           c. Option to regenerate dataset
        """
        self._emit("action", "🤖 AGENT MODE - Autonomous execution")
        
        # Execute all tasks automatically
        result = self.agent.execute_plan(plan, AgentMode.AGENT)
        
        for msg in result.get('messages', []):
            self._emit("action", msg)
        
        if result['success']:
            self._emit("result", 
                f"✅ Completed {result['tasks_completed']}/{result['tasks_total']} tasks")
            self._emit("question", "💬 Feedback or changes needed? (reply or skip)")
        else:
            self._emit("error", "❌ Execution had failures")
    
    def provide_feedback(self, feedback: str) -> None:
        """
        Provide feedback in AGENT mode
        
        Usage:
        ```
        integration.provide_feedback("Add more records to the dataset")
        ```
        """
        feedback_result = self.agent.process_user_feedback(feedback)
        
        self._emit("thinking", f"💭 Processing: {feedback}")
        self._emit("info", feedback_result.get('suggestion', 'Feedback noted'))
    
    def set_repository(self, repo_path: str) -> bool:
        """Set repository for analysis"""
        return self.agent.set_repository(repo_path)
    
    def _emit(self, message_type: str, content: str) -> None:
        """Emit message to GUI"""
        if self.gui_callback:
            self.gui_callback(message_type, content)
        else:
            # Console output for testing
            print(f"[{message_type.upper()}] {content}")


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE GUI USAGE
# ═══════════════════════════════════════════════════════════════════════════════

def example_gui_integration():
    """
    Example of how to integrate with Tkinter GUI
    
    In your GUI code, do this:
    
    ```python
    # In __init__:
    self.agent_integration = AgentIntegration(gui_callback=self.on_agent_message)
    
    # When user sends message:
    def on_user_message(event):
        user_input = self.input_field.get()
        self.input_field.delete(0, tk.END)
        
        # Show user message
        self.append_message("👤 You", user_input)
        
        # Process with agent
        self.agent_integration.process_user_message(user_input)
    
    # Callback from agent:
    def on_agent_message(message_type: str, content: str):
        if message_type == 'thinking':
            icon = "💭"
        elif message_type == 'action':
            icon = "⚡"
        elif message_type == 'result':
            icon = "✅"
        elif message_type == 'error':
            icon = "❌"
        elif message_type == 'question':
            icon = "❓"
        else:
            icon = "ℹ️"
        
        self.append_message("🤖 Agent", f"{icon} {content}")
        
        # If it's a question, show response buttons
        if message_type == 'question':
            self.show_approval_buttons()
    ```
    """
    pass


if __name__ == "__main__":
    print("=" * 80)
    print("Integration Guide: Autonomous Agent with GUI")
    print("=" * 80)
    print("\nSee the example_gui_integration() function for implementation details")
    print("\nBasic usage:")
    print("  1. Create: integration = AgentIntegration(gui_callback=...)")
    print("  2. Use: integration.process_user_message(user_input)")
    print("  3. Receive: Callbacks for agent messages")
    print("\n" + "=" * 80)
