#!/usr/bin/env python3
"""
Simple LLM-Powered Git Analysis CLI
For easy command execution and testing
"""

from llm_git_analyzer import LLMGitAnalyzer
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python llm_cli.py 'clone https://github.com/apache/maven'")
        print("  python llm_cli.py 'set_repo D:/GitIntel/maven'")
        print("  python llm_cli.py '500+ line changes দাও'")
        print("  python llm_cli.py 'LOC analysis করো'")
        print("  python llm_cli.py 'complexity report বানাও'")
        print("  python llm_cli.py 'release changes দেখাও'")
        return
    
    command = ' '.join(sys.argv[1:])
    
    try:
        analyzer = LLMGitAnalyzer()
        
        # Only auto-detect if no repository is currently set and it's not a set_repo or clone command
        if not command.startswith(('set_repo', 'clone')) and not analyzer.current_repo_path:
            # Try to find a repository in current directory or subdirectories
            potential_repos = []
            for item in os.listdir('.'):
                if os.path.isdir(item) and os.path.exists(os.path.join(item, '.git')):
                    potential_repos.append(os.path.abspath(item))
            
            if potential_repos:
                print(f"⚠️ Multiple repositories found. Please specify:")
                for i, repo in enumerate(potential_repos):
                    print(f"  {i+1}. {repo}")
                print(f"� Use: python llm_cli.py 'set_repo {potential_repos[0]}'")
                return
            elif os.path.exists('.git'):
                analyzer.set_repository(os.getcwd())
                print(f"📁 Using current directory as repository: {os.getcwd()}")
        
        # Process command
        if command.startswith('set_repo '):
            repo_path = command[9:].strip().strip('"\'')
            result = analyzer.set_repository(repo_path)
            if result:
                print("✅ Repository set successfully!")
            else:
                print("❌ Failed to set repository!")
        else:
            # Check if repository is set before analysis
            if not analyzer.current_repo_path and not command.startswith('clone'):
                print("❌ No repository set. Please use:")
                print("  python llm_cli.py 'clone https://github.com/apache/maven'")
                print("  python llm_cli.py 'set_repo D:/GitIntel/maven'")
                return
                
            result = analyzer.process_command(command)
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()