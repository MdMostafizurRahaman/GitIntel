#!/usr/bin/env python3
"""
RepoChat CLI - LLM-Powered Repository Question-Answering with Knowledge Graphs
Based on RepoChat paper implementation as a CLI tool
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from repochat_core import RepoChatCore
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_query_generator import CypherQueryGenerator
from repochat_metrics import RepositoryMetrics

class RepoChatCLI:
    def __init__(self):
        self.core = RepoChatCore()
        self.kg_builder = KnowledgeGraphBuilder()
        self.query_generator = CypherQueryGenerator()
        self.metrics = RepositoryMetrics()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_repository(self, repo_path: str) -> bool:
        """Setup repository for analysis"""
        try:
            print(f"🔍 Setting up repository: {repo_path}")
            
            if not os.path.exists(repo_path):
                print(f"❌ Repository path does not exist: {repo_path}")
                return False
                
            if not os.path.exists(os.path.join(repo_path, '.git')):
                print(f"❌ Not a git repository: {repo_path}")
                return False
                
            self.core.set_repository(repo_path)
            print(f"✅ Repository setup complete: {repo_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up repository: {e}")
            return False
    
    def ingest_repository(self, repo_path: str = None) -> bool:
        """Data Ingestion Step - Build Knowledge Graph"""
        try:
            if repo_path:
                if not self.setup_repository(repo_path):
                    return False
            
            if not self.core.current_repo_path:
                print("❌ No repository set. Use: repochat_cli.py --repo <path>")
                return False
                
            print("📊 Starting Data Ingestion Process...")
            print("=" * 50)
            
            # Step 1: Extract repository metadata
            print("1️⃣ Extracting repository metadata...")
            metadata = self.core.extract_metadata()
            
            # Step 2: Build knowledge graph
            print("2️⃣ Building knowledge graph...")
            kg_success = self.kg_builder.build_knowledge_graph(
                self.core.current_repo_path, 
                metadata
            )
            
            if not kg_success:
                print("❌ Failed to build knowledge graph")
                return False
                
            # Step 3: Generate metrics baseline
            print("3️⃣ Generating repository metrics...")
            self.metrics.generate_baseline_metrics(self.core.current_repo_path)
            
            print("✅ Data ingestion complete!")
            print(f"📈 Knowledge graph nodes: {self.kg_builder.get_node_count()}")
            print(f"🔗 Knowledge graph relationships: {self.kg_builder.get_relationship_count()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during data ingestion: {e}")
            self.logger.error(f"Data ingestion failed: {e}")
            return False
    
    def ask_question(self, question: str) -> str:
        """Interaction Step - Answer repository question"""
        try:
            if not self.core.current_repo_path:
                return "❌ No repository set. Please run ingestion first."
            
            if not self.kg_builder.has_knowledge_graph():
                return "❌ Knowledge graph not built. Please run ingestion first."
            
            print(f"❓ Question: {question}")
            print("🔍 Processing...")
            
            # Step 1: Generate Cypher query from natural language
            cypher_query = self.query_generator.generate_query(question)
            if not cypher_query:
                return "❌ Could not understand the question. Please rephrase."
            
            print(f"🔧 Generated Query: {cypher_query}")
            
            # Step 2: Execute query against knowledge graph
            query_results = self.kg_builder.execute_query(cypher_query)
            
            # Step 3: Generate natural language response
            response = self.query_generator.generate_response(question, query_results)
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Error processing question: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def interactive_mode(self):
        """Interactive CLI mode for repository questions"""
        print("🤖 RepoChat - LLM-Powered Repository Q&A")
        print("=" * 50)
        
        if not self.core.current_repo_path:
            print("⚠️ No repository set. Please specify repository path.")
            repo_path = input("Enter repository path: ").strip()
            if not self.setup_repository(repo_path):
                return
        
        if not self.kg_builder.has_knowledge_graph():
            print("⚠️ Knowledge graph not found. Starting data ingestion...")
            if not self.ingest_repository():
                return
        
        print("\n🎯 Available Question Types:")
        print("- Who are the most active contributors?")
        print("- Which files change most frequently?") 
        print("- What are the most complex packages?")
        print("- How many issues were fixed last month?")
        print("- Which developer introduced the most bugs?")
        print("- What is the code churn trend?")
        print("- Show me release-wise changes")
        print("- ওই package এ কত line change হইছে? (Bengali supported)")
        print("\nType 'quit' to exit, 'help' for commands")
        print()
        
        while True:
            try:
                question = input("RepoChat>>> ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    self.show_help()
                    continue
                
                if question.lower() == 'status':
                    self.show_status()
                    continue
                    
                if question.lower().startswith('ingest'):
                    self.ingest_repository()
                    continue
                
                if question:
                    response = self.ask_question(question)
                    print(f"🤖 {response}")
                    print()
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
    
    def show_help(self):
        """Show help information"""
        print("\n📚 RepoChat Help")
        print("=" * 30)
        print("Commands:")
        print("  help     - Show this help")
        print("  status   - Show repository status")
        print("  ingest   - Rebuild knowledge graph")
        print("  quit     - Exit RepoChat")
        print("\nQuestion Examples:")
        print("  'Who committed the most code?'")
        print("  'Which files have highest complexity?'")
        print("  'Show me bug-fixing commits'")
        print("  'What is the package churn analysis?'")
        print("  'কোন developer সবচেয়ে বেশি commit করছে?' (Bengali)")
        print()
    
    def show_status(self):
        """Show current repository status"""
        print("\n📊 Repository Status")
        print("=" * 30)
        print(f"Repository: {self.core.current_repo_path or 'Not set'}")
        print(f"Knowledge Graph: {'✅ Ready' if self.kg_builder.has_knowledge_graph() else '❌ Not built'}")
        
        if self.kg_builder.has_knowledge_graph():
            print(f"Nodes: {self.kg_builder.get_node_count()}")
            print(f"Relationships: {self.kg_builder.get_relationship_count()}")
            
        if self.core.current_repo_path:
            # Show basic repo stats
            stats = self.core.get_basic_stats()
            print(f"Total Commits: {stats.get('commits', 'Unknown')}")
            print(f"Total Files: {stats.get('files', 'Unknown')}")
            print(f"Contributors: {stats.get('contributors', 'Unknown')}")
        print()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='RepoChat - LLM-Powered Repository Question-Answering CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup and start interactive mode
  python repochat_cli.py --repo D:/GitIntel/kafka
  
  # Ingest repository data
  python repochat_cli.py --repo D:/GitIntel/maven --ingest
  
  # Ask a specific question
  python repochat_cli.py --repo D:/GitIntel/kafka --ask "Who are the top contributors?"
  
  # Bengali questions supported
  python repochat_cli.py --ask "কোন file এ সবচেয়ে বেশি bug আছে?"
        """
    )
    
    parser.add_argument('--repo', '-r', 
                       help='Repository path to analyze')
    parser.add_argument('--ingest', '-i', action='store_true',
                       help='Run data ingestion to build knowledge graph')
    parser.add_argument('--ask', '-a', 
                       help='Ask a specific question about the repository')
    parser.add_argument('--interactive', '-int', action='store_true',
                       help='Start interactive mode (default)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize RepoChat CLI
    repochat = RepoChatCLI()
    
    # Setup repository if provided
    if args.repo:
        if not repochat.setup_repository(args.repo):
            sys.exit(1)
    
    # Handle specific operations
    if args.ingest:
        success = repochat.ingest_repository()
        if not success:
            sys.exit(1)
        print("✅ Data ingestion completed successfully!")
        
        # If only ingestion was requested, exit
        if not args.ask and not args.interactive:
            return
    
    if args.ask:
        # Single question mode
        response = repochat.ask_question(args.ask)
        print(f"🤖 {response}")
        return
    
    # Default: interactive mode
    repochat.interactive_mode()

if __name__ == "__main__":
    main()