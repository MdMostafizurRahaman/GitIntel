#!/usr/bin/env python3
"""
Simple Neo4j + RAG Test
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
load_dotenv()

from repochat_core import RepoChatCore

def quick_test():
    """Quick test of Neo4j + RAG"""
    print("🧪 Quick Neo4j + RAG Test")
    print("="*40)
    
    # Initialize
    core = RepoChatCore()
    
    if not core.neo4j_ready:
        print("❌ Neo4j not connected")
        return False
    
    print("✅ Neo4j connected")
    
    # Set repository
    repo_path = os.path.abspath(".")
    core.set_repository(repo_path)
    
    # Test simple questions
    questions = [
        "Who are the top contributors?",
        "Give me an overview",
        "কে সবচেয়ে বেশি কাজ করেছে?"
    ]
    
    for question in questions:
        print(f"\n❓ {question}")
        print("-" * 50)
        
        try:
            response = core.ask_question(question)
            print(f"✅ {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    quick_test()