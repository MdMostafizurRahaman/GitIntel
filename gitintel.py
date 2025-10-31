#!/usr/bin/env python3
"""
GitIntel - Unified Repository Intelligence Platform
Integrates Traditional Analytics with RepoChat Intelligence

Author: GitIntel Team
Version: 2.0.0 - Fully Integrated CLI
"""

import argparse
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from llm_git_analyzer import LLMGitAnalyzer
from repochat_core import RepoChatCore
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_query_generator import CypherQueryGenerator

class GitIntelEngine:
    """Unified GitIntel Engine combining traditional analytics with RepoChat"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.traditional_analyzer = None
        self.repochat_core = None
        self.kg_builder = None
        self.query_generator = None
        self.metrics = None
        self.current_repo_path = None
        self.integration_context = {}
    
    def setup(self, repo_path):
        """Initialize both engines for the repository"""
        try:
            self.current_repo_path = repo_path
            
            # Initialize traditional analyzer
            self.traditional_analyzer = LLMGitAnalyzer()
            self.traditional_analyzer.set_repository(repo_path)
            
            # Initialize RepoChat components
            self.repochat_core = RepoChatCore(
                neo4j_uri="bolt://localhost:7687",  # Default Neo4j URI
                neo4j_user="neo4j",
                neo4j_password="password"
            )
            self.repochat_core.set_repository(repo_path)
            
            self.kg_builder = KnowledgeGraphBuilder()
            self.query_generator = CypherQueryGenerator()
            
            if self.verbose:
                print(f"✅ GitIntel Engine initialized for: {repo_path}")
                
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Engine setup failed: {e}")
            return False
    
    def is_traditional_command(self, command):
        """Determine if command is for traditional analytics"""
        traditional_keywords = [
            'package churn', 'loc analysis', 'complexity analysis',
            'release', 'চার্ন', 'বিশ্লেষণ', 'করো', 'দেখাও',
            'clone', 'set_repo', 'analysis', 'excel', 'report'
        ]
        
        return any(keyword in command.lower() for keyword in traditional_keywords)
    
    def is_question_command(self, command):
        """Determine if command is a question for RepoChat"""
        question_indicators = [
            'who', 'what', 'which', 'how', 'when', 'where', 'why',
            'কে', 'কি', 'কোন', 'কিভাবে', 'কখন', 'কোথায়', 'কেন',
            'show me', 'find', 'list', 'দেখাও', 'খুঁজে', 'তালিকা',
            'contributors', 'commits', 'files', 'changes'
        ]
        
        return any(indicator in command.lower() for indicator in question_indicators)
    
    def process_command(self, command):
        """Smart command routing between traditional analytics and Q&A"""
        if not command.strip():
            return "❌ Please provide a command"
        
        # Handle repository setup commands
        if command.startswith('set_repo ') or command.startswith('clone '):
            try:
                if command.startswith('clone '):
                    # TODO: Add git clone functionality
                    return "❌ Clone functionality not implemented yet"
                elif command.startswith('set_repo '):
                    repo_path = command.split('set_repo ', 1)[1].strip()
                    if self.setup(repo_path):
                        return f"✅ Repository set: {repo_path}"
                    else:
                        return f"❌ Failed to set repository: {repo_path}"
            except Exception as e:
                return f"❌ Failed to set repository: {e}"
        
        # For other commands, check if repository is set
        if not self.current_repo_path:
            return "❌ No repository set. Please use 'set_repo <path>' or --repo <path> first."
        
        # Determine command type and route accordingly
        if self.is_traditional_command(command):
            if self.verbose:
                print("🔄 Routing to Traditional Analytics...")
            return self.run_traditional_command(command)
            
        elif self.is_question_command(command):
            if self.verbose:
                print("🔄 Routing to RepoChat Q&A...")
            return self.run_question_command(command)
            
        else:
            # Default to Q&A for ambiguous commands
            if self.verbose:
                print("🔄 Routing to RepoChat Q&A (default)...")
            return self.run_question_command(command)
    
    def run_traditional_command(self, command):
        """Execute traditional analytics command"""
        try:
            if not self.traditional_analyzer:
                return "❌ Traditional analyzer not initialized"
            
            # Process command using LLM analyzer
            result = self.traditional_analyzer.process_natural_language_command(command)
            
            if result.get('success'):
                return result.get('result', '✅ Analysis completed')
            else:
                return f"❌ {result.get('error', 'Analysis failed')}"
                
        except Exception as e:
            return f"❌ Traditional analysis error: {e}"
    
    def run_question_command(self, question):
        """Execute Q&A command through RepoChat"""
        try:
            if not self.repochat_core:
                return "❌ RepoChat not initialized"
            
            # Check if we have repository metadata, if not extract it
            if not self.repochat_core.repo_metadata or not self.repochat_core.repo_metadata.get('contributors'):
                if self.verbose:
                    print("🔄 Extracting repository metadata for first-time Q&A...")
                self.repochat_core.extract_metadata()
            
            # Process question using RepoChatCore
            response = self.repochat_core.ask_question(question)
            return response
            
        except Exception as e:
            return self.generate_fallback_response(question)
    
    def build_knowledge_graph(self):
        """Build knowledge graph for RepoChat"""
        try:
            if not self.kg_builder:
                return False
            
            self.kg_builder.set_repository(self.current_repo_path)
            success = self.kg_builder.build_full_knowledge_graph()
            
            if success and self.verbose:
                print("✅ Knowledge graph built successfully")
            
            return success
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Knowledge graph building failed: {e}")
            return False
    
    def generate_fallback_response(self, question):
        """Generate fallback response when RepoChat fails"""
        try:
            # Use traditional analyzer as fallback
            if self.traditional_analyzer:
                result = self.traditional_analyzer.process_natural_language_command(question)
                if result.get('success'):
                    return f"🤖 {result.get('result', 'Analysis completed')}"
            
            return f"❌ Could not process question: {question}"
            
        except Exception as e:
            return f"❌ Error processing question: {e}"


class GitIntelCLI:
    """Command Line Interface for GitIntel"""
    
    def __init__(self):
        self.engine = GitIntelEngine()
    
    def create_parser(self):
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="GitIntel - Unified Repository Intelligence Platform",
            epilog="""
Examples:
  gitintel.py --repo ./myproject --interactive
  gitintel.py --repo ./myproject --command "package churn first 500 commits"
  gitintel.py --repo ./myproject --ask "Who are the top contributors?"
  gitintel.py --repo ./myproject --full-analysis
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument('--repo', '-r', 
                          help='Path to Git repository')
        
        parser.add_argument('--interactive', '-i', 
                          action='store_true',
                          help='Start interactive session')
        
        parser.add_argument('--command', '-c', 
                          nargs='*',
                          help='Execute specific command')
        
        parser.add_argument('--ask', '-a',
                          help='Ask a specific question')
        
        parser.add_argument('--full-analysis', '-f',
                          action='store_true',
                          help='Run full analysis (traditional + build KG)')
        
        parser.add_argument('--verbose', '-v',
                          action='store_true',
                          help='Verbose output')
        
        return parser
    
    def interactive_session(self, repo_path=None):
        """Run interactive session with unified command handling"""
        print("🎭 GitIntel Unified Interactive Session")
        print("=" * 60)
        print("📊 Traditional Analytics + 🤖 Interactive Q&A in one interface")
        print("Type commands in English or Bengali")
        print("Examples:")
        print("  - package churn first 500 commits")
        print("  - Who are the top contributors?")
        print("  - কোন file এ সবচেয়ে বেশি complexity?")
        print("  - complexity analysis করো")
        print("\nType 'help' for more examples, 'quit' to exit")
        print()
        
        # Setup repository if provided
        if repo_path:
            try:
                self.engine.setup(repo_path)
                print(f"✅ Repository ready: {repo_path}")
            except Exception as e:
                print(f"❌ Failed to setup repository: {e}")
        
        while True:
            try:
                command = input("🎯 GitIntel> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if command.lower() == 'help':
                    self.show_interactive_help()
                    continue
                
                if command.lower() == 'status':
                    self.show_status()
                    continue
                
                # Process command through unified engine
                result = self.engine.process_command(command)
                print(f"\n{result}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_interactive_help(self):
        """Show help for interactive session"""
        print("\n💡 GitIntel Unified Commands:")
        print("=" * 50)
        print("\n📊 Traditional Analytics (Excel Reports):")
        print("   • package churn first 1000 commits")
        print("   • loc analysis first 500 commits")  
        print("   • complexity analysis করো")
        print("   • halstead metrics analyze")
        print("   • maintainability index check")
        print("   • technical debt analysis")
        print("   • dependency analysis করো")
        print("   • code duplication check")
        print("   • test coverage estimation")
        print("   • security analysis run")
        print("   • release wise changes দেখাও")
        print("   • clone https://github.com/apache/maven")
        print("   • set_repo D:/GitIntel/myproject")
        
        print("\n🤖 Interactive Q&A (Knowledge Graph):")
        print("   • Who are the most active contributors?")
        print("   • Which files have the highest complexity?")
        print("   • Show me recent bug-fixing commits")
        print("   • What packages have the most code churn?")
        print("   • কে সবচেয়ে বেশি commit করেছে?")
        print("   • কোন file এ বেশি complexity আছে?")
        
        print("\n🔧 System Commands:")
        print("   • status - Show repository and system status")
        print("   • help - Show this help")
        print("   • quit - Exit GitIntel")
        
        print("\n💡 Smart Routing:")
        print("   GitIntel automatically detects whether your command")
        print("   needs traditional analytics or interactive Q&A!")
        print()
    
    def show_status(self):
        """Show current system status"""
        print("\n📊 GitIntel System Status:")
        print("=" * 40)
        print(f"Repository: {self.engine.current_repo_path or 'Not set'}")
        print(f"Traditional Analyzer: {'✅' if self.engine.traditional_analyzer else '❌'}")
        print(f"RepoChat Core: {'✅' if self.engine.repochat_core else '❌'}")
        print(f"Knowledge Graph: {'✅' if self.engine.kg_builder and self.engine.kg_builder.has_knowledge_graph() else '❌'}")
        print()
    
    def run(self):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Set verbose mode
        if args.verbose:
            self.engine.verbose = True
        
        # Setup repository if provided
        if args.repo:
            if not self.engine.setup(args.repo):
                print(f"❌ Failed to setup repository: {args.repo}")
                return 1
        
        # Handle full analysis
        if args.full_analysis:
            if not self.engine.current_repo_path:
                print("❌ No repository specified for full analysis")
                return 1
            
            print("🚀 Running full GitIntel analysis...")
            
            # Run traditional analysis
            print("📊 Running traditional analysis...")
            trad_result = self.engine.run_traditional_command("package churn first 1000 commits")
            if trad_result:
                print(trad_result)
                print()
                
                # Build knowledge graph
                print("🧠 Building knowledge graph...")
                kg_success = self.engine.build_knowledge_graph()
                if kg_success:
                    print("✅ Combined analysis complete! Ready for questions.")
                else:
                    print("⚠️ Knowledge graph building failed, but traditional analysis available")
            
            return 0
        
        # Handle interactive mode
        if args.interactive:
            self.interactive_session(args.repo)
            return 0
        
        # Handle direct command
        if args.command:
            command = " ".join(args.command)
            
            # Auto-detect repository if not set
            if not self.engine.current_repo_path and not command.startswith(('clone', 'set_repo')):
                current_dir = os.getcwd()
                if os.path.exists(os.path.join(current_dir, '.git')):
                    try:
                        self.engine.setup(current_dir)
                        if args.verbose:
                            print(f"✅ Auto-detected repository: {current_dir}")
                    except Exception:
                        pass
            
            result = self.engine.process_command(command)
            print(result)
            return 0
        
        # Handle direct question
        if args.ask:
            print(f"🔍 Processing question: {args.ask}")
            # Auto-detect repository if not set
            if not self.engine.current_repo_path:
                current_dir = os.getcwd()
                if os.path.exists(os.path.join(current_dir, '.git')):
                    try:
                        self.engine.setup(current_dir)
                        if args.verbose:
                            print(f"✅ Auto-detected repository: {current_dir}")
                    except Exception:
                        pass
            
            result = self.engine.run_question_command(args.ask)
            print(result)
            return 0
        
        # No specific action, show help
        parser.print_help()
        return 0


def main():
    """Main function"""
    try:
        cli = GitIntelCLI()
        return cli.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
