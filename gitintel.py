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
from repochat_metrics import RepositoryMetrics

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
        if self.verbose:
            print("🔧 Setting up GitIntel engines...")
            
        # Validate repository path
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")
            
        self.current_repo_path = repo_path
            
        # Setup Traditional Analytics
        try:
            self.traditional_analyzer = LLMGitAnalyzer()
            self.traditional_analyzer.set_repository(repo_path)
            if self.verbose:
                print("✅ Traditional Analytics engine ready")
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Traditional Analytics setup warning: {e}")
            
        # Setup RepoChat
        try:
            self.repochat_core = RepoChatCore()
            self.repochat_core.set_repository(repo_path)
            self.kg_builder = KnowledgeGraphBuilder(repo_path=repo_path)
            # Set repository for KG builder to update graph file
            if hasattr(self, 'kg_builder') and self.kg_builder:
                self.kg_builder.set_repository(repo_path)
            self.query_generator = CypherQueryGenerator()
            self.metrics = RepositoryMetrics()
            if self.verbose:
                print("✅ RepoChat engine ready")
        except Exception as e:
            if self.verbose:
                print(f"⚠️ RepoChat setup warning: {e}")
            
        if self.verbose:
            print("🚀 GitIntel ready for analysis!")
    
    def is_traditional_command(self, command):
        """Determine if command is for traditional analytics"""
        traditional_keywords = [
            'package churn', 'churn', 'loc', 'lines of code', 'complexity',
            'release', 'excel', 'report', 'analysis', 'statistics',
            'clone', 'set_repo', 'first', 'commits',
            # Bengali keywords
            'প্যাকেজ', 'churn', 'analysis', 'করো', 'দাও', 'report', 'বানাও', 'দেখাও'
        ]
        
        command_lower = command.lower()
        return any(keyword in command_lower for keyword in traditional_keywords)
    
    def is_question_command(self, command):
        """Determine if command is a question for RepoChat"""
        question_indicators = [
            'who', 'what', 'which', 'how', 'when', 'where', 'why',
            'show me', 'tell me', 'find', 'identify', 'list',
            # Bengali question words
            'কে', 'কি', 'কোন', 'কেমন', 'কখন', 'কোথায়', 'কেন',
            'দেখাও', 'বলো', 'খুঁজে', 'চিহ্নিত', 'তালিকা'
        ]
        
        command_lower = command.lower()
        # Check for question words or question mark
        return ('?' in command or 
                any(indicator in command_lower for indicator in question_indicators))
    
    def process_command(self, command):
        """Smart command routing between traditional analytics and Q&A"""
        command = command.strip()
        
        # Initialize traditional analyzer for repo management commands
        if command.startswith(('clone ', 'set_repo ')) and not self.traditional_analyzer:
            try:
                self.traditional_analyzer = LLMGitAnalyzer()
            except Exception as e:
                return f"❌ Failed to initialize traditional analyzer: {e}"
        
        # Handle repository management commands (these don't need existing repo)
        if command.startswith('clone '):
            if self.traditional_analyzer:
                return self.traditional_analyzer.process_command(command)
            else:
                return "❌ Traditional analyzer not available for cloning"
                
        elif command.startswith('set_repo '):
            repo_path = command[9:].strip().strip('"\'')
            try:
                self.setup(repo_path)
                return f"✅ Repository set successfully: {repo_path}"
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
        if not self.traditional_analyzer:
            return "❌ Traditional analytics engine not available"
            
        try:
            if self.verbose:
                print(f"📊 Processing traditional command: {command}")
            result = self.traditional_analyzer.process_command(command)
            
            # Store context for future questions
            self.integration_context['last_traditional_analysis'] = {
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
            
            return result
            
        except Exception as e:
            return f"❌ Traditional analysis failed: {e}"
    
    def run_question_command(self, question):
        """Execute Q&A command through RepoChat"""
        if not self.repochat_core:
            return "❌ RepoChat engine not available"
            
        try:
            if self.verbose:
                print(f"🤖 Processing question: {question}")
                
            # Build knowledge graph if not already built
            if not self.kg_builder.has_knowledge_graph():
                if self.verbose:
                    print("🔄 Building knowledge graph for Q&A...")
                self.build_knowledge_graph()
            
            # Generate Cypher query
            cypher_query = self.query_generator.generate_query(question)
            if not cypher_query:
                # Fallback to simple analysis if query generation fails
                return self.generate_fallback_response(question)
            
            # Execute query
            query_results = self.kg_builder.execute_query(cypher_query)
            
            # Generate response
            response = self.query_generator.generate_response(
                question, query_results
            )
            
            # Store context
            self.integration_context['last_question'] = {
                'question': question,
                'timestamp': datetime.now().isoformat(),
                'response': response
            }
            
            return response
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Q&A processing error: {e}")
            return self.generate_fallback_response(question)
    
    def build_knowledge_graph(self):
        """Build knowledge graph for RepoChat"""
        if not self.kg_builder or not self.current_repo_path:
            return False
            
        try:
            if self.verbose:
                print("🧠 Building knowledge graph...")
                
            # Extract metadata
            metadata = self.repochat_core.extract_metadata()
            
            # Build graph
            success = self.kg_builder.build_knowledge_graph(
                self.current_repo_path, metadata
            )
            
            if success and self.verbose:
                print(f"✅ Knowledge graph built successfully")
                
            return success
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Knowledge graph building failed: {e}")
            return False
    
    def generate_fallback_response(self, question):
        """Generate fallback response when RepoChat fails"""
        if not self.repochat_core:
            return "❌ Unable to process question - RepoChat unavailable"
            
        try:
            # Try to get basic repository stats
            stats = self.repochat_core.get_basic_stats()
            
            question_lower = question.lower()
            
            # Handle common question patterns
            if any(word in question_lower for word in ['contributor', 'author', 'commit', 'কে', 'commits']):
                contributors = stats.get('top_contributors', [])
                if contributors:
                    response = "🤖 Top contributors based on commit count:\n"
                    for i, contrib in enumerate(contributors[:5], 1):
                        response += f"   {i}. {contrib['name']} - {contrib['commits']} commits\n"
                    return response
                    
            elif any(word in question_lower for word in ['file', 'change', 'modify', 'ফাইল']):
                files = stats.get('frequently_changed_files', [])
                if files:
                    response = "🤖 Frequently changed files:\n"
                    for i, file_info in enumerate(files[:5], 1):
                        response += f"   {i}. {file_info['file']} - {file_info['changes']} changes\n"
                    return response
                    
            elif any(word in question_lower for word in ['complexity', 'complex', 'জটিল']):
                return ("🤖 For complexity analysis, try using traditional analytics:\n"
                       "   Example: 'complexity analysis first 500 commits'")
                       
            # Generic response with available information
            response = f"🤖 Repository Summary:\n"
            response += f"   • Total commits: {stats.get('total_commits', 'Unknown')}\n"
            response += f"   • Total files: {stats.get('total_files', 'Unknown')}\n"
            response += f"   • Contributors: {stats.get('contributors_count', 'Unknown')}\n"
            response += f"   • Repository: {os.path.basename(self.current_repo_path)}\n\n"
            response += "💡 For detailed analysis, try:\n"
            response += "   • Traditional analytics: 'package churn analysis'\n"
            response += "   • Specific questions: 'Who are the top contributors?'"
            
            return response
            
        except Exception as e:
            return f"❌ Unable to process question: {e}"

class GitIntelCLI:
    """Command Line Interface for GitIntel"""
    
    def __init__(self):
        self.engine = GitIntelEngine()
        
    def create_parser(self):
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="GitIntel - Unified Repository Intelligence Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Unified interface - all commands in one place
  python gitintel.py --repo ./project "package churn first 500 commits"
  python gitintel.py --repo ./project "Who are the top contributors?"
  python gitintel.py --repo ./project "কে সবচেয়ে বেশি commit করেছে?"
  
  # Repository management
  python gitintel.py "clone https://github.com/apache/kafka"
  python gitintel.py "set_repo D:/GitIntel/kafka"
  
  # Traditional analytics (Excel reports)
  python gitintel.py --repo ./project "loc analysis first 1000 commits"
  python gitintel.py --repo ./project "complexity report বানাও"
  python gitintel.py --repo ./project "release changes দেখাও"
  
  # Interactive Q&A
  python gitintel.py --repo ./project "Which files have highest complexity?"
  python gitintel.py --repo ./project "Show me recent bug fixes"
  
  # Interactive mode
  python gitintel.py --repo ./project --interactive
  
  # Mixed commands (traditional + Q&A)
  python gitintel.py --repo ./project --analyze combined
            """
        )
        
        parser.add_argument(
            "command",
            nargs="*",
            help="Command to execute (traditional analysis or Q&A question)"
        )
        
        parser.add_argument(
            "--repo", "-r",
            type=str,
            help="Repository path to analyze"
        )
        
        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Start interactive mode"
        )
        
        parser.add_argument(
            "--analyze", 
            choices=["traditional", "repochat", "combined"],
            help="Run comprehensive analysis"
        )
        
        parser.add_argument(
            "--build-kg",
            action="store_true",
            help="Build knowledge graph for better Q&A"
        )
        
        parser.add_argument(
            "--status",
            action="store_true",
            help="Show repository status and available features"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
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
                print(f"❌ Repository setup failed: {e}")
                return
        else:
            # Try to detect repository in current directory
            current_dir = os.getcwd()
            if os.path.exists(os.path.join(current_dir, '.git')):
                try:
                    self.engine.setup(current_dir)
                    print(f"✅ Using current directory: {current_dir}")
                except Exception as e:
                    print(f"⚠️ Current directory setup warning: {e}")
            else:
                print("⚠️ No repository set. Use 'set_repo <path>' or 'clone <url>'")
        
        print("🚀 Ready for commands!")
        print()
        
        while True:
            try:
                command = input("GitIntel>>> ").strip()
                
                if command.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if command.lower() == 'help':
                    self.show_interactive_help()
                    continue
                    
                if command.lower() == 'status':
                    self.show_status()
                    continue
                    
                if not command:
                    continue
                    
                # Process command through unified engine
                result = self.engine.process_command(command)
                print(result)
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Session ended by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
    
    def show_interactive_help(self):
        """Show help for interactive session"""
        print("\n💡 GitIntel Unified Commands:")
        print("=" * 50)
        print("\n📊 Traditional Analytics (Excel Reports):")
        print("   • package churn first 1000 commits")
        print("   • loc analysis first 500 commits")  
        print("   • complexity analysis করো")
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
        print("\n📊 GitIntel System Status")
        print("=" * 40)
        print(f"Repository: {self.engine.current_repo_path or 'Not set'}")
        print(f"Traditional Analytics: {'✅ Ready' if self.engine.traditional_analyzer else '❌ Not available'}")
        print(f"RepoChat Q&A: {'✅ Ready' if self.engine.repochat_core else '❌ Not available'}")
        
        if self.engine.kg_builder:
            kg_status = "✅ Built" if self.engine.kg_builder.has_knowledge_graph() else "⚠️ Not built"
            print(f"Knowledge Graph: {kg_status}")
        
        if self.engine.current_repo_path:
            try:
                stats = self.engine.repochat_core.get_basic_stats() if self.engine.repochat_core else {}
                print(f"Total Commits: {stats.get('total_commits', 'Unknown')}")
                print(f"Total Files: {stats.get('total_files', 'Unknown')}")
                print(f"Contributors: {stats.get('contributors_count', 'Unknown')}")
            except:
                print("Repository stats: Not available")
        print()
    
    def run(self):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Configure engine verbosity
        self.engine.verbose = args.verbose
        
        # Handle repository setup first
        if args.repo:
            try:
                self.engine.setup(args.repo)
                if args.verbose:
                    print(f"✅ Repository set: {args.repo}")
            except Exception as e:
                print(f"❌ Repository setup failed: {e}")
                return 1
        
        # Handle status command (after potential repo setup)
        if args.status:
            self.show_status()
            return 0
        
        # Handle knowledge graph building
        if args.build_kg:
            if not self.engine.current_repo_path:
                print("❌ No repository set. Use --repo <path>")
                return 1
            print("🧠 Building knowledge graph...")
            success = self.engine.build_knowledge_graph()
            if success:
                print("✅ Knowledge graph built successfully!")
            else:
                print("❌ Knowledge graph building failed")
            return 0
        
        # Handle comprehensive analysis
        if args.analyze:
            if not self.engine.current_repo_path:
                print("❌ No repository set. Use --repo <path>")
                return 1
                
            print(f"🚀 Running {args.analyze} analysis...")
            
            if args.analyze == "traditional":
                result = self.engine.run_traditional_command("package churn first 1000 commits")
                print(result)
            elif args.analyze == "repochat":
                success = self.engine.build_knowledge_graph()
                if success:
                    print("✅ RepoChat system ready for questions!")
                else:
                    print("❌ RepoChat setup failed")
            elif args.analyze == "combined":
                # Run traditional analysis
                print("📊 Running traditional analytics...")
                trad_result = self.engine.run_traditional_command("package churn first 500 commits")
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
                            print(f"✅ Using current directory: {current_dir}")
                    except Exception as e:
                        if args.verbose:
                            print(f"⚠️ Current directory setup failed: {e}")
            
            # Process command
            result = self.engine.process_command(command)
            print(result)
            return 0
        
        # Default: show help and start interactive mode
        parser.print_help()
        print("\n🚀 Starting interactive mode...")
        self.interactive_session(args.repo)
        return 0

def main():
    """Main function"""
    try:
        cli = GitIntelCLI()
        return cli.run()
    except KeyboardInterrupt:
        print("\n👋 GitIntel session ended")
        return 0
    except Exception as e:
        print(f"❌ GitIntel error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())