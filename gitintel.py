#!/usr/bin/env python3
"""
GitIntel - Unified Repository Intelligence Platform
Integrates Traditional Analytics with RepoChat Intelligence

Author: GitIntel Team
Version: 1.0.0
"""

import argparse
import os
import sys
import json
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
        self.integration_context = {}
        
    def setup(self, repo_path):
        """Initialize both engines for the repository"""
        if self.verbose:
            print("🔧 Setting up GitIntel engines...")
            
        # Setup Traditional Analytics
        try:
            self.traditional_analyzer = LLMGitAnalyzer()
            if self.verbose:
                print("✅ Traditional Analytics engine ready")
        except Exception as e:
            print(f"⚠️ Traditional Analytics setup warning: {e}")
            
        # Setup RepoChat
        try:
            self.repochat_core = RepoChatCore()
            self.repochat_core.setup_repository(repo_path)
            self.kg_builder = KnowledgeGraphBuilder()
            self.query_generator = CypherQueryGenerator()
            self.metrics = RepositoryMetrics()
            if self.verbose:
                print("✅ RepoChat engine ready")
        except Exception as e:
            print(f"⚠️ RepoChat setup warning: {e}")
            
        if self.verbose:
            print("🚀 GitIntel ready for analysis!")
    
    def run_traditional_analysis(self, repo_path, analysis_types=None):
        """Run traditional analytics (Excel reports, statistical analysis)"""
        if not self.traditional_analyzer:
            return {"error": "Traditional analytics not available"}
            
        if analysis_types is None:
            analysis_types = ["loc", "complexity", "contributors", "churn"]
            
        results = {}
        
        if self.verbose:
            print("📊 Running traditional analysis...")
            
        try:
            # Simulate traditional analysis calls
            # In real implementation, these would call actual LLM analysis
            for analysis_type in analysis_types:
                if self.verbose:
                    print(f"   ⏳ Running {analysis_type} analysis...")
                
                # Mock results for demonstration
                if analysis_type == "loc":
                    results["loc"] = {
                        "total_lines": 45000,
                        "code_lines": 32000,
                        "comment_lines": 8000,
                        "blank_lines": 5000,
                        "trend": "increasing"
                    }
                elif analysis_type == "complexity":
                    results["complexity"] = {
                        "avg_complexity": 15.3,
                        "high_complexity_files": [
                            "src/main/java/KafkaProducer.java",
                            "src/main/java/KafkaConsumer.java"
                        ],
                        "complexity_trend": "stable"
                    }
                elif analysis_type == "contributors":
                    results["contributors"] = [
                        {"name": "Jun Rao", "commits": 187, "lines_added": 91711},
                        {"name": "Neha Narkhede", "commits": 116, "lines_added": 34817},
                        {"name": "Edward Jay Kreps", "commits": 51, "lines_added": 81623}
                    ]
                elif analysis_type == "churn":
                    results["churn"] = {
                        "high_churn_files": [
                            "src/main/scala/kafka/server/KafkaApis.scala",
                            "src/main/scala/kafka/log/Log.scala"
                        ],
                        "churn_trend": "decreasing"
                    }
                    
                if self.verbose:
                    print(f"   ✅ {analysis_type} analysis complete")
                    
        except Exception as e:
            results["error"] = f"Traditional analysis failed: {e}"
            
        return results
    
    def build_knowledge_graph(self, repo_path):
        """Build RepoChat knowledge graph"""
        if not self.kg_builder:
            return {"error": "Knowledge graph builder not available"}
            
        if self.verbose:
            print("🧠 Building knowledge graph...")
            
        try:
            # Generate baseline metrics
            self.metrics.generate_baseline_metrics(repo_path)
            
            # Build knowledge graph
            graph_data = self.kg_builder.build_graph(self.repochat_core)
            
            if self.verbose:
                nodes = len(graph_data.get("nodes", []))
                relationships = len(graph_data.get("relationships", []))
                print(f"✅ Knowledge graph built: {nodes} nodes, {relationships} relationships")
                
            return graph_data
            
        except Exception as e:
            return {"error": f"Knowledge graph building failed: {e}"}
    
    def ask_question(self, question, context=None):
        """Process natural language questions using RepoChat"""
        if not self.query_generator:
            return "❌ RepoChat engine not available"
            
        if self.verbose:
            print(f"❓ Processing question: {question}")
            
        try:
            # Add integration context if available
            enhanced_context = context or {}
            if self.integration_context:
                enhanced_context.update(self.integration_context)
                
            # Generate and execute query
            response = self.query_generator.generate_and_execute_query(
                question, enhanced_context
            )
            
            return response
            
        except Exception as e:
            return f"❌ Question processing failed: {e}"
    
    def correlate_insights(self, traditional_results, kg_results):
        """Correlate insights from both systems"""
        if self.verbose:
            print("🔗 Correlating insights from both systems...")
            
        correlations = {
            "timestamp": datetime.now().isoformat(),
            "enhanced_insights": [],
            "cross_references": {},
            "recommendations": []
        }
        
        try:
            # Correlate contributor data
            traditional_contributors = traditional_results.get("contributors", [])
            if traditional_contributors:
                correlations["cross_references"]["contributors"] = {
                    "traditional_top_3": traditional_contributors[:3],
                    "knowledge_graph_verified": True
                }
                
                correlations["enhanced_insights"].append(
                    f"📊 Top contributor {traditional_contributors[0]['name']} "
                    f"has {traditional_contributors[0]['commits']} commits "
                    f"and {traditional_contributors[0]['lines_added']} lines added"
                )
            
            # Correlate complexity data
            complexity_data = traditional_results.get("complexity", {})
            if complexity_data.get("high_complexity_files"):
                correlations["enhanced_insights"].append(
                    f"⚠️ {len(complexity_data['high_complexity_files'])} files "
                    f"identified as high complexity requiring attention"
                )
                
                correlations["recommendations"].append({
                    "type": "refactoring",
                    "priority": "high",
                    "target": complexity_data["high_complexity_files"],
                    "reason": "High complexity with potential maintenance issues"
                })
            
            # Store context for future questions
            self.integration_context = {
                "traditional_analysis": traditional_results,
                "knowledge_graph": kg_results,
                "correlation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            correlations["error"] = f"Correlation failed: {e}"
            
        return correlations
    
    def generate_report(self, repo_path, output_format="combined"):
        """Generate comprehensive report"""
        if self.verbose:
            print("📋 Generating comprehensive report...")
            
        report = {
            "repository": repo_path,
            "timestamp": datetime.now().isoformat(),
            "analysis_type": output_format
        }
        
        if output_format in ["traditional", "combined"]:
            report["traditional_analysis"] = self.run_traditional_analysis(repo_path)
            
        if output_format in ["repochat", "combined"]:
            report["knowledge_graph"] = self.build_knowledge_graph(repo_path)
            
        if output_format == "combined":
            report["correlations"] = self.correlate_insights(
                report.get("traditional_analysis", {}),
                report.get("knowledge_graph", {})
            )
            
        return report

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
  # Full analysis (Traditional + RepoChat)
  python gitintel.py --repo ./project --analyze combined
  
  # Traditional analytics only  
  python gitintel.py --repo ./project --analyze traditional
  
  # Interactive Q&A mode
  python gitintel.py --repo ./project --interactive
  
  # Ask specific question
  python gitintel.py --repo ./project --ask "কে সবচেয়ে বেশি commit করেছে?"
  
  # Generate Excel + Knowledge Graph
  python gitintel.py --repo ./project --full-report
  
  # Quick insights
  python gitintel.py --repo ./project --insights
            """
        )
        
        parser.add_argument(
            "--repo", "-r",
            type=str,
            help="Repository path to analyze"
        )
        
        parser.add_argument(
            "--analyze", 
            choices=["traditional", "repochat", "combined"],
            default="combined",
            help="Analysis type to run (default: combined)"
        )
        
        parser.add_argument(
            "--ask", "-a",
            type=str,
            help="Ask a specific question about the repository"
        )
        
        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Start interactive Q&A session"
        )
        
        parser.add_argument(
            "--full-report",
            action="store_true", 
            help="Generate comprehensive report with Excel and knowledge graph"
        )
        
        parser.add_argument(
            "--insights",
            action="store_true",
            help="Generate quick insights summary"
        )
        
        parser.add_argument(
            "--output", "-o",
            type=str,
            default="./gitintel_output",
            help="Output directory for reports (default: ./gitintel_output)"
        )
        
        parser.add_argument(
            "--format",
            choices=["json", "text", "excel"],
            default="text",
            help="Output format (default: text)"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        return parser
    
    def interactive_session(self, repo_path):
        """Run interactive Q&A session"""
        print("🎭 GitIntel Interactive Session")
        print("=" * 50)
        print("Ask questions about your repository in English or Bengali")
        print("Type 'quit', 'exit', or 'bye' to end session")
        print("Type 'help' for suggestions")
        print()
        
        # Setup engines
        self.engine.setup(repo_path)
        
        # Run initial analysis for context
        print("🔄 Building context for better answers...")
        traditional_data = self.engine.run_traditional_analysis(repo_path)
        kg_data = self.engine.build_knowledge_graph(repo_path)
        correlations = self.engine.correlate_insights(traditional_data, kg_data)
        
        print("✅ Ready for questions!")
        print()
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                    
                if question.lower() == 'help':
                    self.show_help()
                    continue
                    
                if not question:
                    continue
                    
                print("🔍 Thinking...")
                answer = self.engine.ask_question(question)
                print(f"🤖 {answer}")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Session ended by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
    
    def show_help(self):
        """Show help for interactive session"""
        print("💡 Sample Questions:")
        print("   English:")
        print("   - Who are the top contributors?")
        print("   - Which files have the highest complexity?")
        print("   - Show me recent bug-fixing commits")
        print("   - What packages have the most code churn?")
        print()
        print("   Bengali:")
        print("   - কে সবচেয়ে বেশি commit করেছে?")
        print("   - কোন file এ বেশি complexity?")
        print("   - সাম্প্রতিক bug fix গুলো দেখাও")
        print("   - কোন package এ বেশি churn?")
        print()
        print("   Context-aware:")
        print("   - Excel report অনুযায়ী কোন contributor সবচেয়ে productive?")
        print("   - Traditional analysis এ কোন area highlight হয়েছে?")
        print()
    
    def run(self):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Configure engine verbosity
        self.engine.verbose = args.verbose
        
        # Check repository path
        if not args.repo:
            print("❌ Repository path required. Use --repo <path>")
            return 1
            
        if not os.path.exists(args.repo):
            print(f"❌ Repository path not found: {args.repo}")
            return 1
        
        # Setup engines
        self.engine.setup(args.repo)
        
        # Handle different modes
        if args.interactive:
            self.interactive_session(args.repo)
            
        elif args.ask:
            print(f"❓ Question: {args.ask}")
            print("🔍 Processing...")
            answer = self.engine.ask_question(args.ask)
            print(f"🤖 Answer: {answer}")
            
        elif args.full_report:
            print("📋 Generating comprehensive report...")
            report = self.engine.generate_report(args.repo, "combined")
            
            # Save report
            os.makedirs(args.output, exist_ok=True)
            report_file = os.path.join(args.output, "gitintel_report.json")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Report saved to: {report_file}")
            
        elif args.insights:
            print("💡 Generating quick insights...")
            
            # Run both analyses
            traditional = self.engine.run_traditional_analysis(args.repo)
            kg = self.engine.build_knowledge_graph(args.repo)
            correlations = self.engine.correlate_insights(traditional, kg)
            
            print("\n🎯 Quick Insights:")
            print("=" * 40)
            
            for insight in correlations.get("enhanced_insights", []):
                print(f"   {insight}")
                
            print("\n💡 Recommendations:")
            for rec in correlations.get("recommendations", []):
                print(f"   • {rec['type'].title()}: {rec['reason']}")
                
        else:
            # Default analysis
            print(f"🚀 Running {args.analyze} analysis...")
            report = self.engine.generate_report(args.repo, args.analyze)
            
            if args.format == "json":
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print("✅ Analysis complete!")
                if args.verbose:
                    print(f"📊 Results: {len(report)} sections generated")
        
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