#!/usr/bin/env python3
"""
GitIntel Main Interface - Unified Repository Analysis Tool
Combines original GitIntel features with RepoChat Q&A capabilities
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Original GitIntel modules
from gitintel import GitIntelEngine
from llm_git_analyzer import LLMGitAnalyzer

# RepoChat modules
from repochat_cli import RepoChatCLI
from repochat_core import RepoChatCore
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_query_generator import CypherQueryGenerator

class GitIntelMain:
    def __init__(self):
        self.gitintel_engine = GitIntelEngine()
        self.llm_analyzer = LLMGitAnalyzer()
        self.repochat = RepoChatCLI()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def show_main_menu(self):
        """Show main GitIntel menu with all available options"""
        print("\n" + "="*70)
        print("🚀 GitIntel - Advanced Repository Analysis & Q&A Platform")
        print("="*70)
        print("Choose your analysis mode:")
        print()
        print("📊 1. Original GitIntel Analysis")
        print("   - Package analysis")
        print("   - Commit patterns")
        print("   - Developer metrics")
        print("   - Code quality analysis")
        print()
        print("🧠 2. LLM-Powered Analysis")
        print("   - AI-driven insights")
        print("   - Code pattern detection")
        print("   - Intelligent recommendations")
        print()
        print("🤖 3. RepoChat - Interactive Q&A")
        print("   - Natural language queries")
        print("   - Knowledge graph exploration")
        print("   - Real-time repository questions")
        print()
        print("⚙️  4. Combined Analysis")
        print("   - Run all analysis types")
        print("   - Comprehensive report")
        print()
        print("❓ 5. Help & Documentation")
        print("📤 6. Exit")
        print()
    
    def run_original_analysis(self, repo_path: str):
        """Run original GitIntel analysis"""
        print("\n🔍 Running Original GitIntel Analysis...")
        print("="*50)
        
        try:
            # Set repository
            self.gitintel_engine.setup(repo_path)
            
            print("1️⃣ Running comprehensive analysis...")
            results = self.gitintel_engine.run_comprehensive_analysis()
            
            print("✅ Original analysis complete!")
            print(f"📁 Results available through GitIntel engine")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in original analysis: {e}")
            return None
    
    def run_llm_analysis(self, repo_path: str):
        """Run LLM-powered analysis"""
        print("\n🧠 Running LLM-Powered Analysis...")
        print("="*50)
        
        try:
            # Set repository
            self.llm_analyzer.set_repository(repo_path)
            
            print("1️⃣ Extracting repository context...")
            context = self.llm_analyzer.extract_context()
            
            print("2️⃣ Generating AI insights...")
            insights = self.llm_analyzer.generate_insights()
            
            print("3️⃣ Analyzing code patterns...")
            patterns = self.llm_analyzer.analyze_patterns()
            
            print("4️⃣ Creating recommendations...")
            recommendations = self.llm_analyzer.generate_recommendations()
            
            print("✅ LLM analysis complete!")
            
            return {
                'context': context,
                'insights': insights,
                'patterns': patterns,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"❌ Error in LLM analysis: {e}")
            print("💡 Tip: Make sure you have proper API keys configured")
            return None
    
    def run_repochat_analysis(self, repo_path: str):
        """Run RepoChat interactive Q&A"""
        print("\n🤖 Starting RepoChat - Interactive Q&A...")
        print("="*50)
        
        try:
            # Setup repository
            if not self.repochat.setup_repository(repo_path):
                return False
            
            # Check if knowledge graph exists, if not build it
            if not self.repochat.kg_builder.has_knowledge_graph():
                print("📊 Building knowledge graph for first-time analysis...")
                if not self.repochat.ingest_repository():
                    print("❌ Failed to build knowledge graph")
                    return False
            
            # Start interactive mode
            self.repochat.interactive_mode()
            return True
            
        except Exception as e:
            print(f"❌ Error in RepoChat: {e}")
            return False
    
    def run_combined_analysis(self, repo_path: str):
        """Run all analysis types and generate combined report"""
        print("\n⚙️ Running Combined Analysis...")
        print("="*50)
        
        results = {}
        
        # Run original analysis
        print("\n📊 Phase 1: Original Analysis")
        original_results = self.run_original_analysis(repo_path)
        if original_results:
            results['original'] = original_results
        
        # Run LLM analysis
        print("\n🧠 Phase 2: LLM Analysis")
        llm_results = self.run_llm_analysis(repo_path)
        if llm_results:
            results['llm'] = llm_results
        
        # Setup RepoChat knowledge graph
        print("\n🤖 Phase 3: Building Knowledge Graph")
        try:
            if self.repochat.setup_repository(repo_path):
                if not self.repochat.kg_builder.has_knowledge_graph():
                    self.repochat.ingest_repository()
                results['repochat'] = {
                    'status': 'ready',
                    'nodes': self.repochat.kg_builder.get_node_count(),
                    'relationships': self.repochat.kg_builder.get_relationship_count()
                }
        except Exception as e:
            print(f"⚠️ RepoChat setup warning: {e}")
        
        # Generate combined report
        print("\n📝 Phase 4: Generating Combined Report")
        self.generate_combined_report(repo_path, results)
        
        print("\n✅ Combined analysis complete!")
        print("🎯 You can now:")
        print("   - Review the comprehensive report")
        print("   - Use RepoChat for interactive Q&A")
        print("   - Explore specific analysis results")
        
        return results
    
    def generate_combined_report(self, repo_path: str, results: Dict):
        """Generate a combined analysis report"""
        report_path = os.path.join(repo_path, 'gitintel_combined_report.md')
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# GitIntel Combined Analysis Report\n\n")
                f.write(f"**Repository:** {os.path.basename(repo_path)}\n")
                f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Analysis Summary\n\n")
                
                if 'original' in results:
                    f.write("✅ **Original GitIntel Analysis:** Complete\n")
                else:
                    f.write("❌ **Original GitIntel Analysis:** Failed\n")
                
                if 'llm' in results:
                    f.write("✅ **LLM-Powered Analysis:** Complete\n")
                else:
                    f.write("❌ **LLM-Powered Analysis:** Failed\n")
                
                if 'repochat' in results:
                    f.write(f"✅ **RepoChat Knowledge Graph:** {results['repochat']['nodes']} nodes, {results['repochat']['relationships']} relationships\n")
                else:
                    f.write("❌ **RepoChat Knowledge Graph:** Failed\n")
                
                f.write("\n## Quick Actions\n\n")
                f.write("To continue your analysis:\n\n")
                f.write("```bash\n")
                f.write("# Interactive Q&A\n")
                f.write(f"python gitintel_main.py --repo \"{repo_path}\" --mode repochat\n\n")
                f.write("# Ask specific questions\n")
                f.write(f"python repochat_cli.py --repo \"{repo_path}\" --ask \"Who are the top contributors?\"\n")
                f.write("```\n\n")
                
                f.write("## Available Features\n\n")
                f.write("- 📊 Package and commit analysis\n")
                f.write("- 🧠 AI-powered insights\n")
                f.write("- 🤖 Natural language repository queries\n")
                f.write("- 📈 Developer productivity metrics\n")
                f.write("- 🔍 Code quality assessments\n")
                
            print(f"📄 Combined report saved: {report_path}")
            
        except Exception as e:
            print(f"⚠️ Could not save combined report: {e}")
    
    def show_help(self):
        """Show help and documentation"""
        print("\n📚 GitIntel Help & Documentation")
        print("="*50)
        print()
        print("🚀 **Quick Start:**")
        print("   python gitintel_main.py --repo /path/to/repository")
        print()
        print("🔧 **Available Modes:**")
        print("   --mode original    : Run original GitIntel analysis")
        print("   --mode llm         : Run LLM-powered analysis")
        print("   --mode repochat    : Start interactive Q&A")
        print("   --mode combined    : Run all analysis types")
        print()
        print("💬 **RepoChat Examples:**")
        print("   'Who are the top contributors?'")
        print("   'Which files change most frequently?'")
        print("   'Show me recent bug fixes'")
        print("   'What is the repository overview?'")
        print("   'কোন developer সবচেয়ে বেশি commit করছে?' (Bengali)")
        print()
        print("📁 **Output Files:**")
        print("   - analysis_output/     : Original analysis results")
        print("   - llm_analysis.json    : LLM insights")
        print("   - .repochat_graph.json : Knowledge graph data")
        print()
        print("🔑 **Configuration:**")
        print("   Set GEMINI_API_KEY for enhanced LLM features")
        print("   Set OPENAI_API_KEY for OpenAI integration")
        print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='GitIntel - Advanced Repository Analysis & Q&A Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with menu
  python gitintel_main.py
  
  # Analyze specific repository
  python gitintel_main.py --repo D:/GitIntel/kafka
  
  # Run specific analysis mode
  python gitintel_main.py --repo D:/GitIntel/kafka --mode repochat
  
  # Combined analysis
  python gitintel_main.py --repo D:/GitIntel/maven --mode combined
        """
    )
    
    parser.add_argument('--repo', '-r', 
                       help='Repository path to analyze')
    parser.add_argument('--mode', '-m', 
                       choices=['original', 'llm', 'repochat', 'combined'],
                       help='Analysis mode to run')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize GitIntel
    gitintel = GitIntelMain()
    
    # If no arguments, show interactive menu
    if not args.repo and not args.mode:
        while True:
            gitintel.show_main_menu()
            try:
                choice = input("Enter your choice (1-6): ").strip()
                
                if choice == '6':
                    print("👋 Goodbye!")
                    break
                
                if choice == '5':
                    gitintel.show_help()
                    continue
                
                # Get repository path
                if choice in ['1', '2', '3', '4']:
                    repo_path = input("\nEnter repository path: ").strip()
                    if not repo_path or not os.path.exists(repo_path):
                        print("❌ Invalid repository path!")
                        continue
                    
                    if choice == '1':
                        gitintel.run_original_analysis(repo_path)
                    elif choice == '2':
                        gitintel.run_llm_analysis(repo_path)
                    elif choice == '3':
                        gitintel.run_repochat_analysis(repo_path)
                    elif choice == '4':
                        gitintel.run_combined_analysis(repo_path)
                else:
                    print("❌ Invalid choice! Please enter 1-6.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("\nPress Enter to continue...")
        
        return
    
    # Command line mode
    if args.repo:
        repo_path = os.path.abspath(args.repo)
        
        if not os.path.exists(repo_path):
            print(f"❌ Repository path does not exist: {repo_path}")
            sys.exit(1)
        
        if not os.path.exists(os.path.join(repo_path, '.git')):
            print(f"❌ Not a git repository: {repo_path}")
            sys.exit(1)
        
        # Run specified mode or default to combined
        mode = args.mode or 'combined'
        
        if mode == 'original':
            gitintel.run_original_analysis(repo_path)
        elif mode == 'llm':
            gitintel.run_llm_analysis(repo_path)
        elif mode == 'repochat':
            gitintel.run_repochat_analysis(repo_path)
        elif mode == 'combined':
            gitintel.run_combined_analysis(repo_path)
        
    else:
        print("❌ Repository path is required!")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()