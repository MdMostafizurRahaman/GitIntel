#!/usr/bin/env python3
"""
GitIntel Unified Interface Demo
Demonstrates how to use the integrated CLI for both traditional analytics and Q&A
"""

import os
import sys
from gitintel import GitIntelEngine

def demo_unified_interface():
    """Demonstrate the unified GitIntel interface"""
    print("🎭 GitIntel Unified Interface Demo")
    print("=" * 60)
    print("This demo shows how both traditional analytics and Q&A work together!")
    print()
    
    # Initialize engine
    engine = GitIntelEngine(verbose=True)
    
    # Check if we have a repository to work with
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    # Look for available repositories
    potential_repos = []
    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '.git')):
            potential_repos.append(item_path)
    
    if not potential_repos:
        print("⚠️ No Git repositories found for demo")
        print("Please ensure you have a Git repository available")
        return
    
    # Use the first available repository
    repo_path = potential_repos[0]
    
    try:
        print(f"🔧 Setting up with repository: {os.path.basename(repo_path)}")
        engine.setup(repo_path)
        print("✅ Setup complete!")
        print()
        
        # Demo traditional analytics commands
        print("📊 TRADITIONAL ANALYTICS DEMO")
        print("=" * 40)
        
        traditional_commands = [
            "package churn first 100 commits",
            "loc analysis first 50 commits",
            "complexity analysis করো",
        ]
        
        for cmd in traditional_commands:
            print(f"💻 Command: {cmd}")
            result = engine.process_command(cmd)
            print(f"📝 Result: {result[:200]}..." if len(result) > 200 else f"📝 Result: {result}")
            print()
        
        # Demo Q&A commands
        print("🤖 INTERACTIVE Q&A DEMO")
        print("=" * 40)
        
        # Build knowledge graph first
        print("🧠 Building knowledge graph for Q&A...")
        kg_built = engine.build_knowledge_graph()
        
        qa_commands = [
            "Who are the top contributors?",
            "Which files change most frequently?",
            "কে সবচেয়ে বেশি commit করেছে?",
            "What is the repository structure like?"
        ]
        
        for question in qa_commands:
            print(f"❓ Question: {question}")
            answer = engine.process_command(question)
            print(f"🤖 Answer: {answer[:300]}..." if len(answer) > 300 else f"🤖 Answer: {answer}")
            print()
        
        # Demo mixed commands
        print("🔄 MIXED COMMAND DEMO")
        print("=" * 40)
        print("Showing how the system automatically routes different types of commands:")
        
        mixed_commands = [
            ("Traditional", "release changes দেখাও"),
            ("Q&A", "Show me bug-fixing commits"),
            ("Traditional", "complexity first 200 commits"),
            ("Q&A", "কোন package এ সবচেয়ে বেশি complexity?")
        ]
        
        for cmd_type, cmd in mixed_commands:
            print(f"🎯 Expected: {cmd_type} | Command: {cmd}")
            
            # Check routing
            is_traditional = engine.is_traditional_command(cmd)
            is_question = engine.is_question_command(cmd)
            
            routing = "Traditional" if is_traditional else "Q&A" if is_question else "Q&A (default)"
            print(f"🔀 Routed to: {routing}")
            
            result = engine.process_command(cmd)
            print(f"📝 Result: {result[:150]}..." if len(result) > 150 else f"📝 Result: {result}")
            print()
        
        print("✅ Demo completed successfully!")
        print("\n💡 Usage Examples:")
        print("   python gitintel.py --repo ./myproject 'package churn first 500 commits'")
        print("   python gitintel.py --repo ./myproject 'Who are the top contributors?'")
        print("   python gitintel.py --repo ./myproject --interactive")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_unified_interface()