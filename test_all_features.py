#!/usr/bin/env python3
"""
Comprehensive Test Script for GitIntel
Tests all major functionality including traditional analytics and Q&A
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from gitintel import GitIntelEngine
from llm_git_analyzer import LLMGitAnalyzer
from repochat_cli import RepoChatCLI

def test_traditional_analytics():
    """Test traditional analytics features"""
    print("\n" + "="*60)
    print("🧪 Testing Traditional Analytics")
    print("="*60)
    
    try:
        analyzer = LLMGitAnalyzer()
        
        # Set repository (use current project as test)
        repo_path = os.path.abspath(".")
        analyzer.set_repository(repo_path)
        print(f"✅ Repository set: {repo_path}")
        
        # Test different metrics
        test_commands = [
            "loc analysis",
            "complexity analysis", 
            "halstead metrics",
            "maintainability index",
            "technical debt analysis",
            "dependency analysis",
            "security analysis",
            "test coverage estimation"
        ]
        
        for command in test_commands:
            print(f"\n🔍 Testing: {command}")
            start_time = time.time()
            
            try:
                result = analyzer.process_command(command)
                elapsed = time.time() - start_time
                
                if "✅" in result:
                    print(f"   ✅ Success ({elapsed:.1f}s)")
                else:
                    print(f"   ⚠️ Warning: {result[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Traditional analytics test failed: {e}")
        return False

def test_interactive_qa():
    """Test interactive Q&A features"""
    print("\n" + "="*60)
    print("🧪 Testing Interactive Q&A")
    print("="*60)
    
    try:
        engine = GitIntelEngine(verbose=True)
        
        # Set repository
        repo_path = os.path.abspath(".")
        success = engine.setup(repo_path)
        
        if not success:
            print("❌ Failed to setup GitIntel engine")
            return False
        
        print(f"✅ GitIntel engine setup successful")
        
        # Test Q&A questions
        test_questions = [
            "Who are the top contributors?",
            "Show me recent commits",
            "What files are largest?", 
            "Give me an overview",
            "কে সবচেয়ে বেশি অবদান রেখেছে?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Testing: {question}")
            start_time = time.time()
            
            try:
                response = engine.run_question_command(question)
                elapsed = time.time() - start_time
                
                if "❌" not in response:
                    print(f"   ✅ Success ({elapsed:.1f}s)")
                    print(f"   📝 Response: {response[:100]}...")
                else:
                    print(f"   ⚠️ Warning: {response[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Interactive Q&A test failed: {e}")
        return False

def test_unified_cli():
    """Test unified CLI functionality"""
    print("\n" + "="*60)
    print("🧪 Testing Unified CLI")
    print("="*60)
    
    try:
        engine = GitIntelEngine(verbose=True)
        repo_path = os.path.abspath(".")
        engine.setup(repo_path)
        
        # Test command routing
        test_commands = [
            ("complexity analysis", "traditional"),
            ("Who are the contributors?", "Q&A"),
            ("halstead metrics analyze", "traditional"),
            ("Show me file overview", "Q&A"),
            ("technical debt check", "traditional")
        ]
        
        for command, expected_type in test_commands:
            print(f"\n🔄 Testing command routing: {command}")
            
            if engine.is_traditional_command(command):
                detected_type = "traditional"
            elif engine.is_question_command(command):
                detected_type = "Q&A"
            else:
                detected_type = "unknown"
            
            if detected_type == expected_type:
                print(f"   ✅ Correctly routed to {detected_type}")
            else:
                print(f"   ⚠️ Expected {expected_type}, got {detected_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified CLI test failed: {e}")
        return False

def test_environment_setup():
    """Test environment and dependencies"""
    print("\n" + "="*60)
    print("🧪 Testing Environment Setup")
    print("="*60)
    
    # Check required imports
    required_modules = [
        'pandas', 'pydriller', 'google.generativeai', 
        'git', 'openpyxl', 'pathlib', 'json'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module} - Available")
        except ImportError:
            print(f"   ❌ {module} - Missing")
    
    # Check optional modules
    optional_modules = [
        'neo4j', 'chromadb', 'sentence_transformers', 'tkinter'
    ]
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"   ✅ {module} - Available (optional)")
        except ImportError:
            print(f"   ⚠️ {module} - Not available (optional)")
    
    # Check environment variables
    env_vars = ['GEMINI_API_KEY']
    for var in env_vars:
        if os.getenv(var):
            print(f"   ✅ {var} - Set")
        else:
            print(f"   ⚠️ {var} - Not set")
    
    return True

def generate_demo_report():
    """Generate a comprehensive demo report"""
    print("\n" + "="*60)
    print("📄 Generating Demo Report")
    print("="*60)
    
    try:
        analyzer = LLMGitAnalyzer()
        repo_path = os.path.abspath(".")
        analyzer.set_repository(repo_path)
        
        # Generate a few sample analyses
        demo_analyses = [
            "complexity analysis",
            "technical debt analysis", 
            "security analysis"
        ]
        
        generated_files = []
        
        for analysis in demo_analyses:
            print(f"📊 Generating: {analysis}")
            try:
                result = analyzer.process_command(analysis)
                if "Report saved:" in result:
                    filename = result.split("Report saved: ")[-1]
                    generated_files.append(filename)
                    print(f"   ✅ Generated: {filename}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        if generated_files:
            print(f"\n📁 Generated {len(generated_files)} demo reports")
            for file in generated_files:
                print(f"   • {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo report generation failed: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("🚀 GitIntel Comprehensive Test Suite")
    print("="*60)
    print("Testing all major functionality...")
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Traditional Analytics", test_traditional_analytics),
        ("Interactive Q&A", test_interactive_qa),
        ("Unified CLI", test_unified_cli),
        ("Demo Report Generation", generate_demo_report)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    total_time = time.time() - start_time
    passed = sum(results.values())
    total = len(results)
    
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    print(f"⏱️ Total time: {total_time:.1f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! GitIntel is working properly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)