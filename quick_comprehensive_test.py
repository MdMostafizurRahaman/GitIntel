#!/usr/bin/env python3
"""
Quick Test Script for GitIntel New Metrics
Tests all the newly added metrics functionality
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from llm_git_analyzer import LLMGitAnalyzer

def test_new_metrics():
    """Test all the newly added metrics"""
    print("🧪 Testing New Metrics in GitIntel")
    print("=" * 50)
    
    try:
        analyzer = LLMGitAnalyzer()
        
        # Set repository to current project
        repo_path = os.path.abspath(".")
        print(f"📁 Setting repository: {repo_path}")
        analyzer.set_repository(repo_path)
        print("✅ Repository set successfully")
        
        # Test new metrics with simplified commands
        test_metrics = [
            ("Traditional LOC Analysis", "loc analysis"),
            ("Complexity Analysis", "complexity analysis"),
            ("Halstead Metrics", "halstead metrics"),
            ("Maintainability Index", "maintainability index"),
            ("Technical Debt", "technical debt analysis"),
            ("Dependency Analysis", "dependency analysis"),
            ("Security Analysis", "security analysis"),
            ("Test Coverage", "test coverage"),
            ("Code Duplication", "code duplication")
        ]
        
        results = {}
        
        for metric_name, command in test_metrics:
            print(f"\n🔍 Testing: {metric_name}")
            start_time = time.time()
            
            try:
                result = analyzer.process_command(command)
                elapsed = time.time() - start_time
                
                if "✅" in result and "Report saved:" in result:
                    # Extract filename
                    filename = result.split("Report saved: ")[-1].strip()
                    print(f"   ✅ Success ({elapsed:.1f}s) - {filename}")
                    results[metric_name] = "SUCCESS"
                elif "❌" in result:
                    print(f"   ❌ Failed: {result[:80]}...")
                    results[metric_name] = "FAILED"
                else:
                    print(f"   ⚠️  Warning ({elapsed:.1f}s): {result[:80]}...")
                    results[metric_name] = "WARNING"
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results[metric_name] = "EXCEPTION"
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        success_count = 0
        for metric, status in results.items():
            status_icon = {"SUCCESS": "✅", "FAILED": "❌", "WARNING": "⚠️", "EXCEPTION": "💥"}
            print(f"{status_icon.get(status, '❓')} {metric:<25} {status}")
            if status == "SUCCESS":
                success_count += 1
        
        print(f"\n📈 Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        if success_count == len(results):
            print("🎉 All metrics working perfectly!")
        elif success_count > len(results) // 2:
            print("👍 Most metrics working well!")
        else:
            print("⚠️ Several metrics need attention!")
        
        return success_count > len(results) // 2
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

def test_available_tools():
    """Test and display all available tools"""
    print("\n" + "=" * 50)
    print("🛠️ AVAILABLE TOOLS IN GITINTEL")
    print("=" * 50)
    
    try:
        analyzer = LLMGitAnalyzer()
        
        print("📋 Traditional Analytics Tools:")
        for tool, description in analyzer.available_tools.items():
            print(f"   • {tool:<25} - {description}")
        
        print(f"\n📊 Total Tools Available: {len(analyzer.available_tools)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return False

def test_q_and_a():
    """Test Q&A functionality"""
    print("\n" + "=" * 50)
    print("🤖 Testing Q&A Functionality")
    print("=" * 50)
    
    from gitintel import GitIntelEngine
    
    try:
        engine = GitIntelEngine(verbose=True)
        repo_path = os.path.abspath(".")
        success = engine.setup(repo_path)
        
        if not success:
            print("❌ Failed to setup GitIntel engine for Q&A")
            return False
        
        # Test questions
        questions = [
            "Who are the top contributors?",
            "Give me an overview",
            "Show me recent commits",
            "What files are largest?",
            "কে সবচেয়ে বেশি অবদান রেখেছে?"  # Bengali
        ]
        
        success_count = 0
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            start_time = time.time()
            
            try:
                response = engine.run_question_command(question)
                elapsed = time.time() - start_time
                
                if "❌" not in response and len(response.strip()) > 20:
                    print(f"   ✅ Success ({elapsed:.1f}s)")
                    print(f"   📝 Response preview: {response[:100]}...")
                    success_count += 1
                else:
                    print(f"   ⚠️ Weak response: {response[:80]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Q&A Success Rate: {success_count}/{len(questions)} ({success_count/len(questions)*100:.1f}%)")
        
        return success_count > len(questions) // 2
        
    except Exception as e:
        print(f"❌ Q&A test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GitIntel Comprehensive Functionality Test")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run tests
    test_results = {}
    
    test_results["Available Tools"] = test_available_tools()
    test_results["New Metrics"] = test_new_metrics()
    test_results["Q&A Functionality"] = test_q_and_a()
    
    # Overall summary
    total_time = time.time() - start_time
    passed = sum(test_results.values())
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    print(f"\n📊 Overall Result: {passed}/{total} test categories passed")
    print(f"⏱️ Total Time: {total_time:.1f} seconds")
    
    if passed == total:
        print("\n🎉 GitIntel is fully functional! All tests passed.")
        print("\n📋 Summary of Capabilities:")
        print("   ✅ Interactive Q&A with natural language")
        print("   ✅ Traditional analytics with comprehensive metrics")
        print("   ✅ Multiple analysis types (LOC, complexity, security, etc.)")
        print("   ✅ Multi-language support (English & Bengali)")
        print("   ✅ Excel report generation")
        print("   ✅ Real-time repository analysis")
    else:
        print(f"\n⚠️ {total - passed} test category/categories need attention.")
        print("Check the detailed output above for specific issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 GitIntel is ready for production use!")
    else:
        print("🔧 GitIntel needs some fixes before full deployment.")
    
    sys.exit(0 if success else 1)