#!/usr/bin/env python3
"""
RepoChat CLI Test and Demo Script
"""

import os
import sys
from pathlib import Path

def test_repochat_functionality():
    """Test basic RepoChat functionality"""
    print("🧪 Testing RepoChat CLI Functionality")
    print("=" * 50)
    
    # Test repository paths
    test_repos = [
        r"D:\GitIntel\kafka",
        r"D:\GitIntel\maven", 
        r"D:\GitIntel\Spring-Boot-in-Detailed-Way"
    ]
    
    print("📂 Available test repositories:")
    for i, repo in enumerate(test_repos, 1):
        status = "✅ Available" if os.path.exists(repo) else "❌ Missing"
        print(f"   {i}. {repo} - {status}")
    
    print("\n🎯 Sample Commands to Try:")
    print("=" * 30)
    
    # Basic setup commands
    print("📋 Setup Commands:")
    for repo in test_repos:
        if os.path.exists(repo):
            repo_name = os.path.basename(repo)
            print(f"python repochat_cli.py --repo \"{repo}\" --ingest")
            break
    
    print("\n❓ Sample Questions (English):")
    questions_en = [
        "Who are the top contributors?",
        "Which files change most frequently?", 
        "Show me bug-fixing commits",
        "What is the complexity analysis?",
        "Which packages have the most code churn?",
        "What is the test coverage ratio?",
        "Show me recent commits",
        "Which files are the largest?"
    ]
    
    for q in questions_en:
        print(f"python repochat_cli.py --ask \"{q}\"")
    
    print("\n❓ Sample Questions (Bengali):")
    questions_bn = [
        "কে সবচেয়ে বেশি commit করেছে?",
        "কোন file এ সবচেয়ে বেশি change হয়েছে?",
        "বাগ fix করার commit গুলো দেখাও",
        "কোন package এ complexity বেশি?", 
        "test coverage কত?",
        "কোন developer সবচেয়ে active?"
    ]
    
    for q in questions_bn:
        print(f"python repochat_cli.py --ask \"{q}\"")
    
    print("\n🔧 Testing Component Imports:")
    print("=" * 30)
    
    # Test imports
    try:
        from repochat_core import RepoChatCore
        print("✅ RepoChatCore imported successfully")
    except ImportError as e:
        print(f"❌ RepoChatCore import failed: {e}")
    
    try:
        from repochat_knowledge_graph import KnowledgeGraphBuilder
        print("✅ KnowledgeGraphBuilder imported successfully")
    except ImportError as e:
        print(f"❌ KnowledgeGraphBuilder import failed: {e}")
    
    try:
        from repochat_query_generator import CypherQueryGenerator
        print("✅ CypherQueryGenerator imported successfully")
    except ImportError as e:
        print(f"❌ CypherQueryGenerator import failed: {e}")
    
    try:
        from repochat_metrics import RepositoryMetrics
        print("✅ RepositoryMetrics imported successfully")
    except ImportError as e:
        print(f"❌ RepositoryMetrics import failed: {e}")
    
    print("\n🌐 Environment Check:")
    print("=" * 20)
    
    # Check environment
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print("✅ GEMINI_API_KEY is set")
    else:
        print("⚠️ GEMINI_API_KEY not set - will use fallback mode")
    
    # Check for .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️ .env file not found - create one with GEMINI_API_KEY")
    
    print("\n📚 Quick Start Guide:")
    print("=" * 20)
    print("1. Set up environment:")
    print("   echo \"GEMINI_API_KEY=your_key_here\" > .env")
    print("\n2. Run interactive mode:")
    print("   python repochat_cli.py --repo D:\\GitIntel\\kafka")
    print("\n3. Ask a question:")
    print("   python repochat_cli.py --ask \"Who are the top contributors?\"")
    print("\n4. Bengali question:")
    print("   python repochat_cli.py --ask \"কে সবচেয়ে বেশি commit করেছে?\"")
    
    print("\n✨ Ready to use RepoChat! Try the commands above.")

if __name__ == "__main__":
    test_repochat_functionality()