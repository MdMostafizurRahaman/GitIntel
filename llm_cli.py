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
        print("  python llm_cli.py 'set_repo D:/GitIntel/kafka'")
        print("  python llm_cli.py '500+ line changes দাও'")
        print("  python llm_cli.py 'LOC analysis করো'")
        print("  python llm_cli.py 'complexity report বানাও'")
        print("  python llm_cli.py 'release changes দেখাও'")
        return
    
    command = ' '.join(sys.argv[1:])
    
    try:
        analyzer = LLMGitAnalyzer()
        
        # Auto-detect repository if not set
        if not command.startswith('set_repo'):
            # Try to find a repository in current directory or subdirectories
            potential_repos = []
            for item in os.listdir('.'):
                if os.path.isdir(item) and os.path.exists(os.path.join(item, '.git')):
                    potential_repos.append(os.path.abspath(item))
            
            if potential_repos:
                analyzer.set_repository(potential_repos[0])
                print(f"📁 Auto-detected repository: {potential_repos[0]}")
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
            result = analyzer.process_command(command)
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()