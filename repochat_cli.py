#!/usr/bin/env python3
"""
RepoChatCLI - Interactive Command Line Interface for Repository Q&A
Provides conversational intelligence for comprehensive GitHub repository analysis
"""

import os
import sys
import argparse
import logging
from typing import Optional
from datetime import datetime

from repochat_core import RepoChatCore
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_query_generator import CypherQueryGenerator

class RepoChatCLI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.core = RepoChatCore()
        self.kg_builder = None
        self.query_generator = CypherQueryGenerator()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def setup_repository(self, repo_path: str) -> bool:
        """Setup repository for analysis"""
        try:
            if not self.core.set_repository(repo_path):
                return False
            
            # Initialize knowledge graph builder for this repository
            self.kg_builder = KnowledgeGraphBuilder(repo_path=repo_path)
            
            print(f"✅ Repository set: {repo_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup repository: {e}")
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
            print("3️⃣ Generating analysis baseline...")
            self._generate_baseline_metrics(metadata)
            
            print("\n✅ Data ingestion completed successfully!")
            print("💡 You can now ask questions about the repository")
            print("Examples:")
            print("  • Who are the top contributors?")
            print("  • Show me recent commits")
            print("  • Find files with most complexity")
            print("  • শীর্ষ অবদানকারী কারা? (Bengali)")
            
            return True
            
        except Exception as e:
            print(f"❌ Data ingestion failed: {e}")
            import traceback
            traceback.print_exc()
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
            self.logger.error(f"Question processing failed: {e}")
            return f"❌ Error processing question: {e}"
    
    def interactive_mode(self):
        """Start interactive Q&A session"""
        if not self.core.current_repo_path:
            print("❌ No repository set. Please run ingestion first.")
            return
        
        if not self.kg_builder.has_knowledge_graph():
            print("❌ Knowledge graph not built. Please run ingestion first.")
            return
        
        print("\n🎯 Interactive RepoChat Mode")
        print("=" * 40)
        print("Ask questions about your repository!")
        print("Commands: 'quit', 'exit', 'help'")
        print("Languages: English, Bengali")
        print("-" * 40)
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    self._show_help()
                    continue
                
                # Process question
                response = self.ask_question(question)
                print(f"\n💬 {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _generate_baseline_metrics(self, metadata: dict):
        """Generate baseline metrics for the repository"""
        try:
            repo_info = metadata.get('repository', {})
            commits = metadata.get('commits', [])
            files = metadata.get('files', [])
            contributors = metadata.get('contributors', [])
            
            print(f"📈 Repository: {repo_info.get('name', 'Unknown')}")
            print(f"   • Total Commits: {len(commits):,}")
            print(f"   • Total Files: {len(files):,}")
            print(f"   • Contributors: {len(contributors)}")
            print(f"   • Size: {repo_info.get('size_mb', 0):.2f} MB")
            
            # Language breakdown
            language_stats = {}
            for file_info in files:
                lang = file_info.get('language', 'Unknown')
                if lang not in language_stats:
                    language_stats[lang] = {'count': 0, 'lines': 0}
                language_stats[lang]['count'] += 1
                language_stats[lang]['lines'] += file_info.get('lines_of_code', 0)
            
            print(f"   • Languages: {', '.join([f'{k} ({v['count']})' for k, v in sorted(language_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:5]])}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate baseline metrics: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("""
🆘 RepoChat Help

📋 Available Question Types:
  • Contributors: "Who are the top contributors?", "শীর্ষ অবদানকারী কারা?"
  • Commits: "Show me recent commits", "সাম্প্রতিক কমিট দেখাও"
  • Files: "Find largest files", "সবচেয়ে বড় ফাইল খুঁজে দাও"
  • Statistics: "Repository overview", "প্রকল্পের সংক্ষিপ্ত বিবরণ"
  • Search: "Find contributor rakib", "খুঁজে দাও রাকিব"

🌍 Supported Languages:
  • English: Natural language queries
  • Bengali: বাংলা প্রশ্ন সমর্থিত

💡 Example Questions:
  • "Who committed the most code?"
  • "Show me bug fixes from last week"
  • "Which files have the most lines?"
  • "Find commits by john"
  • "কে সবচেয়ে বেশি কোড লিখেছে?"

⚠️ Commands:
  • help - Show this help
  • quit/exit - Exit interactive mode
        """)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GitIntel RepoChat - Conversational Repository Analysis",
        epilog="Examples:\n"
               "  repochat_cli.py --repo /path/to/repo --ingest\n"
               "  repochat_cli.py --interactive\n"
               "  repochat_cli.py --ask \"Who are the top contributors?\"\n"
               "  repochat_cli.py --ask \"শীর্ষ অবদানকারী কারা?\"",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--repo', '-r',
        type=str,
        help='Path to Git repository for analysis'
    )
    
    parser.add_argument(
        '--ingest', '-i',
        action='store_true',
        help='Ingest repository data and build knowledge graph'
    )
    
    parser.add_argument(
        '--ask', '-a',
        type=str,
        help='Ask a question about the repository'
    )
    
    parser.add_argument(
        '--interactive', '-int',
        action='store_true',
        help='Start interactive Q&A session'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        help='Neo4j database URI (optional, defaults to in-memory)'
    )
    
    parser.add_argument(
        '--neo4j-password',
        type=str,
        help='Neo4j database password'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize RepoChatCLI
    repochat = RepoChatCLI()
    
    # Setup Neo4j if provided
    if args.neo4j_uri:
        repochat.kg_builder = KnowledgeGraphBuilder(
            neo4j_uri=args.neo4j_uri,
            neo4j_user='neo4j',
            neo4j_password=args.neo4j_password or 'password',
            repo_path=args.repo
        )
    
    # Handle repository setup
    if args.repo:
        if not repochat.setup_repository(args.repo):
            sys.exit(1)
    
    # Handle ingestion
    if args.ingest:
        if not args.repo:
            print("❌ --repo path required for ingestion")
            sys.exit(1)
        
        success = repochat.ingest_repository(args.repo)
        if not success:
            sys.exit(1)
        return
    
    # Handle single question
    if args.ask:
        response = repochat.ask_question(args.ask)
        print(f"\n💬 {response}")
        return
    
    # Handle interactive mode
    if args.interactive:
        repochat.interactive_mode()
        return
    
    # Default behavior
    if not any([args.ingest, args.ask, args.interactive]):
        print("🎯 GitIntel RepoChat - Conversational Repository Analysis")
        print("=" * 60)
        print("Usage examples:")
        print("  1. Ingest repository data:")
        print("     python repochat_cli.py --repo /path/to/repo --ingest")
        print("  2. Ask a question:")
        print("     python repochat_cli.py --ask \"Who are the top contributors?\"")
        print("  3. Interactive mode:")
        print("     python repochat_cli.py --interactive")
        print("\nFor more options: python repochat_cli.py --help")

if __name__ == "__main__":
    main()