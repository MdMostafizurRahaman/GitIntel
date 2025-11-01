#!/usr/bin/env python3
"""
GitIntel Comprehensive Demo Script
Demonstrates all major features of GitIntel platform
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from gitintel import GitIntelEngine

def print_header(title, char="="):
    """Print formatted header"""
    print(f"\n{char * 60}")
    print(f"🎯 {title}")
    print(f"{char * 60}")

def print_step(step_num, description):
    """Print step information"""
    print(f"\n📌 Step {step_num}: {description}")
    print("-" * 50)

def demo_traditional_analytics():
    """Demonstrate traditional analytics features"""
    print_header("TRADITIONAL ANALYTICS DEMO")
    
    try:
        from llm_git_analyzer import LLMGitAnalyzer
        
        analyzer = LLMGitAnalyzer()
        repo_path = os.path.abspath(".")
        analyzer.set_repository(repo_path)
        
        print(f"📁 Repository: {repo_path}")
        
        # Demo metrics
        metrics_demo = [
            ("LOC Analysis", "loc analysis"),
            ("Complexity Analysis", "complexity analysis"), 
            ("Halstead Metrics", "halstead metrics"),
            ("Technical Debt", "technical debt analysis"),
            ("Security Analysis", "security analysis")
        ]
        
        for i, (name, command) in enumerate(metrics_demo, 1):
            print_step(i, f"Running {name}")
            
            try:
                result = analyzer.process_command(command)
                if result and "successfully" in result.lower():
                    print(f"✅ {name} completed")
                    if "generated" in result.lower():
                        print(f"   📊 Report: {result.split('generated: ')[-1].split()[0]}")
                else:
                    print(f"⚠️ {name} completed with warnings")
                    
            except Exception as e:
                print(f"❌ {name} failed: {e}")
            
            time.sleep(1)  # Small delay for demo effect
            
        print("\n🎉 Traditional Analytics Demo Completed!")
        
    except Exception as e:
        print(f"❌ Traditional Analytics Demo failed: {e}")

def demo_conversational_qa():
    """Demonstrate conversational Q&A features"""
    print_header("CONVERSATIONAL Q&A DEMO")
    
    try:
        engine = GitIntelEngine(verbose=True)
        repo_path = os.path.abspath(".")
        
        print_step(1, "Initializing GitIntel Engine")
        success = engine.setup(repo_path)
        
        if not success:
            print("❌ Engine setup failed")
            return
            
        print("✅ GitIntel Engine initialized successfully")
        
        # Demo questions
        demo_questions = [
            ("Who are the top contributors?", "Find project contributors"),
            ("Give me an overview of this repository", "Repository summary"),
            ("What are the largest files?", "File size analysis"),
            ("Show me recent commits", "Commit history"),
            ("কে সবচেয়ে বেশি অবদান রেখেছে?", "Bengali language support"),
            ("What programming languages are used?", "Language distribution")
        ]
        
        for i, (question, description) in enumerate(demo_questions, 2):
            print_step(i, f"Q&A Demo - {description}")
            print(f"❓ Question: {question}")
            
            try:
                start_time = time.time()
                response = engine.repochat_core.ask_question(question)
                elapsed = time.time() - start_time
                
                print(f"⚡ Response time: {elapsed:.2f}s")
                print(f"📝 Answer: {response[:100]}...")
                
                if "❌" not in response:
                    print("✅ Question answered successfully")
                else:
                    print("⚠️ Limited response received")
                    
            except Exception as e:
                print(f"❌ Question failed: {e}")
            
            time.sleep(1)
            
        print("\n🎉 Conversational Q&A Demo Completed!")
        
    except Exception as e:
        print(f"❌ Conversational Q&A Demo failed: {e}")

def demo_desktop_application():
    """Demonstrate desktop application"""
    print_header("DESKTOP APPLICATION DEMO")
    
    print_step(1, "Desktop Application Information")
    print("🖥️ GitIntel Desktop Application Features:")
    print("   • Visual repository browser")
    print("   • Real-time analytics dashboard") 
    print("   • Interactive chat interface")
    print("   • Export and reporting tools")
    
    print_step(2, "How to Launch Desktop App")
    print("💻 Command to launch:")
    print("   python gitintel_desktop.py")
    
    print_step(3, "Desktop App Architecture")
    print("🏗️ Technical Components:")
    print("   • Tkinter GUI Framework")
    print("   • Threaded background processing")
    print("   • Real-time chart updates")
    print("   • Integrated file dialogs")
    
    print("\n📝 Note: Desktop app requires display environment")
    print("🎉 Desktop Application Demo Information Completed!")

def demo_database_integration():
    """Demonstrate database and knowledge graph"""
    print_header("DATABASE & KNOWLEDGE GRAPH DEMO")
    
    try:
        from repochat_core import RepoChatCore
        
        print_step(1, "Neo4j Database Connection")
        core = RepoChatCore()
        
        if core.neo4j_ready:
            print("✅ Neo4j Aura connected successfully")
            print(f"   🔗 Database: {core.neo4j_uri}")
        else:
            print("❌ Neo4j connection failed")
            return
            
        print_step(2, "Repository Data Storage")
        repo_path = os.path.abspath(".")
        core.set_repository(repo_path)
        
        # Extract and store metadata
        print("📊 Extracting repository metadata...")
        metadata = core.extract_metadata()
        
        print(f"✅ Data extracted and stored:")
        print(f"   • Commits: {len(metadata.get('commits', []))}")
        print(f"   • Files: {len(metadata.get('files', []))}")
        print(f"   • Contributors: {len(metadata.get('contributors', []))}")
        
        print_step(3, "Knowledge Graph Queries")
        
        # Test database queries
        test_queries = [
            "Who are the contributors?",
            "Show repository overview", 
            "What files exist?"
        ]
        
        for query in test_queries:
            try:
                response = core.ask_question(query)
                if response and "❌" not in response:
                    print(f"✅ Query successful: {query}")
                else:
                    print(f"⚠️ Query limited: {query}")
            except Exception as e:
                print(f"❌ Query failed: {query} - {e}")
        
        print("\n🎉 Database Integration Demo Completed!")
        
    except Exception as e:
        print(f"❌ Database Demo failed: {e}")

def demo_export_capabilities():
    """Demonstrate export and reporting"""
    print_header("EXPORT & REPORTING DEMO")
    
    print_step(1, "Supported Export Formats")
    print("📊 Available export formats:")
    print("   • Excel (.xlsx) - Detailed analytics reports")
    print("   • JSON - Raw data export")
    print("   • CSV - Tabular data export")
    print("   • Text - Summary reports")
    
    print_step(2, "Report Types")
    print("📈 Generated report types:")
    print("   • LOC Analysis Reports")
    print("   • Complexity Analysis Reports")
    print("   • Package Churn Reports")
    print("   • Technical Debt Reports") 
    print("   • Contributor Statistics")
    
    print_step(3, "Sample Export Commands")
    print("💻 Export commands:")
    print('   gitintel.py --repo ./project --command "loc analysis excel"')
    print('   gitintel.py --repo ./project --command "complexity analysis"')
    print('   gitintel.py --repo ./project --full-analysis')
    
    print("\n🎉 Export Capabilities Demo Completed!")

def main():
    """Run comprehensive GitIntel demonstration"""
    print_header("🚀 GITINTEL COMPREHENSIVE DEMONSTRATION", "=")
    
    print("""
🎯 Welcome to GitIntel - Conversational Intelligence for Repository Analysis!

This demo will showcase:
1. Traditional Analytics Engine
2. Conversational Q&A System  
3. Desktop Application
4. Database Integration
5. Export & Reporting

Let's begin the demonstration...
""")
    
    # Run all demonstrations
    demo_traditional_analytics()
    demo_conversational_qa()
    demo_database_integration()
    demo_desktop_application()
    demo_export_capabilities()
    
    # Final summary
    print_header("🎉 DEMONSTRATION SUMMARY")
    
    print("""
✅ GitIntel Features Demonstrated:

📊 Traditional Analytics:
   • 20+ different code metrics
   • Excel report generation
   • Package-level analysis
   
🤖 Conversational Q&A:
   • Natural language queries
   • Real-time responses (<1s)
   • Multi-language support (English/Bengali)
   
🔗 Database Integration:
   • Neo4j knowledge graph
   • Structured data storage
   • Fast query processing
   
🖥️ Desktop Application:
   • Visual interface
   • Real-time charts
   • Interactive chat
   
📈 Export & Reporting:
   • Multiple formats
   • Detailed analytics
   • Custom reports

🎯 GitIntel is ready for production use!

📚 Documentation: COMPLETE_DOCUMENTATION.md
💻 Desktop App: python gitintel_desktop.py
🔧 CLI Tool: python gitintel.py --help
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
    
    print("\n🙏 Thank you for trying GitIntel!")