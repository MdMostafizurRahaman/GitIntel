#!/usr/bin/env python3
"""
RepoChat Integration Demo - Combining LLM Analysis with Knowledge Graph QA
"""

import subprocess
import os
import sys
from datetime import datetime

class RepoAnalysisWorkflow:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo_name = os.path.basename(repo_path)
        
    def run_complete_analysis(self):
        """Run complete repository analysis workflow"""
        print(f"🚀 Complete Repository Analysis Workflow")
        print(f"📂 Repository: {self.repo_name}")
        print("=" * 60)
        
        # Step 1: Traditional LLM Analysis (from existing tools)
        print("\n1️⃣ Traditional Analysis (LLM + PyDriller)")
        print("-" * 40)
        self.run_traditional_analysis()
        
        # Step 2: Knowledge Graph Construction
        print("\n2️⃣ Knowledge Graph Construction (RepoChat)")
        print("-" * 40)
        self.build_knowledge_graph()
        
        # Step 3: Interactive Q&A
        print("\n3️⃣ Interactive Question-Answering")
        print("-" * 40)
        self.run_sample_questions()
        
        # Step 4: Combined Insights
        print("\n4️⃣ Combined Analysis Insights")
        print("-" * 40)
        self.generate_combined_insights()
    
    def run_traditional_analysis(self):
        """Run traditional LLM-based analysis"""
        analyses = [
            ("LOC Analysis", f'python llm_cli.py --repo "{self.repo_path}" "LOC analysis first 500 commits"'),
            ("Package Churn", f'python llm_cli.py --repo "{self.repo_path}" "package churn first 500 commits"'),
            ("Complexity Analysis", f'python llm_cli.py --repo "{self.repo_path}" "complexity analysis"')
        ]
        
        for name, command in analyses:
            print(f"📊 Running {name}...")
            print(f"Command: {command}")
            try:
                # For demo, just show what would be executed
                print(f"✅ {name} would generate Excel report")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
            print()
    
    def build_knowledge_graph(self):
        """Build knowledge graph for interactive Q&A"""
        print("🏗️ Building Knowledge Graph...")
        command = f'python repochat_cli.py --repo "{self.repo_path}" --ingest'
        print(f"Command: {command}")
        
        try:
            # For demo, just show what would be executed
            print("✅ Knowledge graph would be constructed with:")
            print("   - Repository metadata")
            print("   - Commit history analysis")
            print("   - File complexity metrics")
            print("   - Contributor relationships") 
            print("   - Bug-fixing patterns")
        except Exception as e:
            print(f"❌ Knowledge graph construction failed: {e}")
    
    def run_sample_questions(self):
        """Run sample questions to demonstrate capabilities"""
        questions = [
            # English questions
            ("English", "Who are the top 5 contributors?", "Shows contributor ranking with commit counts"),
            ("English", "Which files have the highest complexity?", "Identifies complex files for refactoring"),
            ("English", "Show me recent bug-fixing commits", "Lists commits that fixed bugs"),
            ("English", "What packages have the most code churn?", "Highlights unstable code areas"),
            
            # Bengali questions  
            ("Bengali", "কে সবচেয়ে বেশি commit করেছে?", "সবচেয়ে active developer দেখায়"),
            ("Bengali", "কোন file এ বেশি bug আছে?", "Bug-prone files চিহ্নিত করে"),
            ("Bengali", "test coverage কত percentage?", "Testing metrics দেখায়"),
        ]
        
        print("❓ Sample Questions & Expected Responses:")
        print()
        
        for lang, question, description in questions:
            print(f"🗣️ {lang}: \"{question}\"")
            print(f"📝 Expected: {description}")
            command = f'python repochat_cli.py --ask "{question}"'
            print(f"🔧 Command: {command}")
            print()
    
    def generate_combined_insights(self):
        """Generate insights combining both approaches"""
        print("🔗 Combined Analysis Benefits:")
        print()
        
        insights = [
            {
                "title": "Excel Reports + Interactive Q&A",
                "description": "Get detailed Excel reports from LLM analysis, then ask specific questions about the data",
                "example": "After getting package churn Excel → Ask 'Which contributors modified high-churn packages?'"
            },
            {
                "title": "Quantitative + Qualitative Analysis", 
                "description": "Combine hard metrics with contextual understanding",
                "example": "LOC metrics + 'Why did complexity increase in specific time periods?'"
            },
            {
                "title": "Historical Trends + Current State",
                "description": "Understand how repository evolved and current patterns",
                "example": "Monthly commit trends + 'Which new contributors are most active?'"
            },
            {
                "title": "Cross-Language Analysis",
                "description": "Ask questions in Bengali or English, get same insights",
                "example": "'বাগ fix rate কেমন?' = 'What is the bug fix rate?'"
            }
        ]
        
        for i, insight in enumerate(insights, 1):
            print(f"{i}. **{insight['title']}**")
            print(f"   📋 {insight['description']}")
            print(f"   💡 Example: {insight['example']}")
            print()
    
    def show_workflow_commands(self):
        """Show complete workflow commands"""
        print(f"📋 Complete Workflow Commands for {self.repo_name}")
        print("=" * 50)
        
        print("# Step 1: Traditional Analysis")
        print(f'python llm_cli.py "set_repo {self.repo_path}"')
        print(f'python llm_cli.py "LOC analysis first 500 commits"')
        print(f'python llm_cli.py "package churn analysis"')
        print(f'python llm_cli.py "complexity analysis"')
        print()
        
        print("# Step 2: Knowledge Graph Setup") 
        print(f'python repochat_cli.py --repo "{self.repo_path}" --ingest')
        print()
        
        print("# Step 3: Interactive Questions")
        print(f'python repochat_cli.py --repo "{self.repo_path}"')
        print("# Then ask questions interactively, or:")
        print(f'python repochat_cli.py --ask "Who are the top contributors?"')
        print(f'python repochat_cli.py --ask "কোন package এ বেশি complexity?"')
        print()

def main():
    """Main demo function"""
    print("🎭 RepoChat Integration Demo")
    print("=" * 50)
    
    # Available repositories
    repos = [
        r"D:\GitIntel\kafka",
        r"D:\GitIntel\maven",
        r"D:\GitIntel\Spring-Boot-in-Detailed-Way"
    ]
    
    print("📂 Available Repositories:")
    available_repos = []
    for i, repo in enumerate(repos, 1):
        if os.path.exists(repo):
            print(f"   {i}. {os.path.basename(repo)} ✅")
            available_repos.append(repo)
        else:
            print(f"   {i}. {os.path.basename(repo)} ❌ (not found)")
    
    if not available_repos:
        print("❌ No repositories found. Please check paths in demo script.")
        return
    
    # Use first available repository for demo
    demo_repo = available_repos[0]
    workflow = RepoAnalysisWorkflow(demo_repo)
    
    print(f"\n🎯 Demo using: {os.path.basename(demo_repo)}")
    print("=" * 30)
    
    # Show what the complete workflow would look like
    workflow.run_complete_analysis()
    
    print("\n📜 Ready-to-Use Commands:")
    print("=" * 30)
    workflow.show_workflow_commands()
    
    print("\n🎉 Demo Complete!")
    print("Try the commands above to see RepoChat in action.")

if __name__ == "__main__":
    main()