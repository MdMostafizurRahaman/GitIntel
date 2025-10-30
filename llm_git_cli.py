#!/usr/bin/env python3
"""
LLM-Powered Git Analysis CLI
==========================

Natural language interface for Git repository analysis.
Supports commands like:
- "Find packages with 500+ line changes and create Excel"
- "Analyze releases and show what changed"
- "Clone repo https://github.com/user/repo and analyze"

Usage: python llm_git_cli.py "your command here"
"""

import argparse
import sys
import re
import subprocess
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMGitCLI:
    """Natural language command processor for Git analysis"""
    
    def __init__(self):
        self.current_repo = None
        self.threshold = 500
        
    def parse_command(self, command: str) -> dict:
        """Parse natural language command into structured parameters"""
        command = command.lower().strip()
        
        parsed = {
            'action': None,
            'repo_url': None,
            'repo_path': None,
            'threshold': 500,
            'output_excel': False,
            'analyze_releases': False,
            'from_tag': None,
            'to_tag': None
        }
        
        # Extract repository URL
        url_pattern = r'https?://github\.com/[^\s]+'
        url_match = re.search(url_pattern, command)
        if url_match:
            parsed['repo_url'] = url_match.group()
        
        # Extract threshold
        threshold_pattern = r'(\d+)\+?\s*line'
        threshold_match = re.search(threshold_pattern, command)
        if threshold_match:
            parsed['threshold'] = int(threshold_match.group(1))
        
        # Extract tags for release analysis
        tag_pattern = r'from\s+([v\d\.\-\w]+)\s+to\s+([v\d\.\-\w]+)'
        tag_match = re.search(tag_pattern, command)
        if tag_match:
            parsed['from_tag'] = tag_match.group(1)
            parsed['to_tag'] = tag_match.group(2)
            parsed['analyze_releases'] = True
        
        # Determine actions
        if any(word in command for word in ['excel', 'spreadsheet', 'xlsx']):
            parsed['output_excel'] = True
            
        if any(word in command for word in ['release', 'tag', 'version']):
            parsed['analyze_releases'] = True
            
        if any(word in command for word in ['clone', 'download', 'get']):
            parsed['action'] = 'clone_and_analyze'
        elif any(word in command for word in ['analyze', 'check', 'find']):
            parsed['action'] = 'analyze'
        elif any(word in command for word in ['package', 'churn']):
            parsed['action'] = 'package_analysis'
        else:
            parsed['action'] = 'analyze'  # Default action
            
        return parsed
    
    def suggest_repositories(self) -> list:
        """Suggest interesting repositories for analysis"""
        suggestions = [
            "https://github.com/spring-projects/spring-boot",
            "https://github.com/apache/kafka",
            "https://github.com/elastic/elasticsearch",
            "https://github.com/apache/hadoop",
            "https://github.com/Netflix/eureka",
            "https://github.com/alibaba/druid",
            "https://github.com/apache/dubbo",
            "https://github.com/SeleniumHQ/selenium",
            "https://github.com/apache/maven",
            "https://github.com/jenkinsci/jenkins"
        ]
        return suggestions
    
    def execute_analysis(self, parsed_command: dict) -> bool:
        """Execute the analysis based on parsed command"""
        try:
            # Build command arguments
            cmd_args = []
            
            # Determine repository path
            if parsed_command['repo_url']:
                cmd_args.extend(["--clone-repo", parsed_command['repo_url']])
                # Use current directory as repo path (will be updated after clone)
                repo_name = parsed_command['repo_url'].split('/')[-1].replace('.git', '')
                repo_path = str(Path.cwd() / repo_name)
                cmd_args.append(repo_path)
            elif parsed_command['repo_path']:
                cmd_args.append(parsed_command['repo_path'])
            else:
                # Check for known local repositories first
                local_repos = ['kafka', 'spring-boot', 'elasticsearch', 'hadoop']
                repo_path = '.'
                for repo in local_repos:
                    if os.path.exists(repo) and os.path.isdir(repo):
                        repo_path = repo
                        break
                cmd_args.append(repo_path)
            
            # Add analysis parameters
            cmd_args.extend(["--threshold", str(parsed_command['threshold'])])
            
            if parsed_command['output_excel']:
                cmd_args.append("--output-excel")
                
            if parsed_command['analyze_releases']:
                cmd_args.append("--analyze-releases")
                
            if parsed_command['from_tag']:
                cmd_args.extend(["--from-tag", parsed_command['from_tag']])
                
            if parsed_command['to_tag']:
                cmd_args.extend(["--to-tag", parsed_command['to_tag']])
            
            # Execute the analysis tool
            logger.info(f"Executing analysis with args: {cmd_args}")
            result = subprocess.run([
                sys.executable, "git_analyzer_tool.py"
            ] + cmd_args, check=True, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("Warnings:", result.stderr)
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Analysis failed: {e}")
            print(f"Error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def interactive_mode(self):
        """Start interactive mode for continuous commands"""
        print("🤖 LLM-Powered Git Analysis Tool")
        print("=" * 50)
        print("Enter natural language commands like:")
        print("  - 'Find packages with 500+ lines and create Excel'")
        print("  - 'Clone https://github.com/user/repo and analyze'")
        print("  - 'Check releases and show changes'")
        print("  - 'quit' to exit")
        print()
        
        while True:
            try:
                command = input("🔍 Enter command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if command.lower() in ['help', '?']:
                    self.show_help()
                    continue
                    
                if command.lower() == 'suggest':
                    print("📂 Suggested repositories:")
                    for i, repo in enumerate(self.suggest_repositories(), 1):
                        print(f"  {i}. {repo}")
                    continue
                
                if not command:
                    continue
                
                print(f"\n🧠 Processing: {command}")
                parsed = self.parse_command(command)
                print(f"📋 Parsed command: {parsed}")
                
                success = self.execute_analysis(parsed)
                if success:
                    print("✅ Analysis completed successfully!")
                else:
                    print("❌ Analysis failed!")
                    
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
🤖 LLM Git Analysis Tool Help
============================

Natural Language Commands:
--------------------------
• "Find packages with 500+ line changes"
• "Analyze packages over 1000 lines and create Excel"
• "Clone https://github.com/user/repo and analyze"
• "Check releases from v1.0 to v2.0"
• "Show what changed in latest release"
• "Analyze current repository and generate Excel"

Command Components:
------------------
• Threshold: "500+ lines", "over 1000 lines"
• Output: "create Excel", "generate spreadsheet"
• Repository: "clone https://github.com/...", "current repo"
• Releases: "check releases", "from v1.0 to v2.0"

Special Commands:
----------------
• "suggest" - Show suggested repositories
• "help" or "?" - Show this help
• "quit" or "exit" - Exit the tool

Examples:
---------
1. "Clone https://github.com/spring-projects/spring-boot and find packages with 1000+ lines"
2. "Analyze current repo releases and create Excel report"
3. "Check what changed from v2.0 to v3.0 and generate spreadsheet"
        """
        print(help_text)

def main():
    parser = argparse.ArgumentParser(description="LLM-Powered Git Analysis CLI")
    parser.add_argument("command", nargs='?', help="Natural language command")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Start interactive mode")
    
    args = parser.parse_args()
    
    cli = LLMGitCLI()
    
    if args.interactive or not args.command:
        cli.interactive_mode()
    else:
        print(f"🧠 Processing: {args.command}")
        parsed = cli.parse_command(args.command)
        print(f"📋 Parsed command: {parsed}")
        
        success = cli.execute_analysis(parsed)
        if success:
            print("✅ Analysis completed successfully!")
        else:
            print("❌ Analysis failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()