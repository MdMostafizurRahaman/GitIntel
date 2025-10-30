#!/usr/bin/env python3
"""
Advanced Git Repository Analyzer CLI with LLM Integration
Natural language command interface for Git repository analysis
"""

import argparse
import os
import sys
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime

from git_analyzer_tool import GitRepoAnalyzer

class GitAnalyzerCLI:
    def __init__(self):
        self.current_repo = None
        
    def detect_repo_path(self, user_input=""):
        """Detect Git repository path from current directory or user input"""
        
        # Check if user mentioned a specific path
        path_patterns = [
            r'in\s+([^\s]+)',
            r'from\s+([^\s]+)',
            r'repository\s+([^\s]+)',
            r'repo\s+([^\s]+)'
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                potential_path = match.group(1)
                if os.path.exists(potential_path) and os.path.isdir(os.path.join(potential_path, '.git')):
                    return potential_path
        
        # Check current directory and subdirectories
        current_dir = os.getcwd()
        
        # Check current directory
        if os.path.isdir(os.path.join(current_dir, '.git')):
            return current_dir
            
        # Check for common repo folder names in current directory
        common_names = ['kafka', 'spring-boot', 'Spring-Boot-in-Detailed-Way', 'MOOC-Java-course']
        for name in common_names:
            potential_path = os.path.join(current_dir, name)
            if os.path.exists(potential_path) and os.path.isdir(os.path.join(potential_path, '.git')):
                return potential_path
        
        # Check subdirectories for git repos
        try:
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path) and os.path.isdir(os.path.join(item_path, '.git')):
                    return item_path
        except PermissionError:
            pass
            
        return None
    
    def parse_command(self, command):
        """Parse natural language command and extract parameters"""
        command = command.lower().strip()
        
        # Default parameters
        params = {
            'action': 'analyze',
            'threshold': 500,
            'output_format': 'excel',
            'include_releases': False,
            'package_analysis': False,
            'commit_analysis': False,
            'dataset_generation': False
        }
        
        # Action detection
        if any(word in command for word in ['excel', 'spreadsheet', 'sheet']):
            params['output_format'] = 'excel'
            
        if any(word in command for word in ['package', 'packages']):
            params['package_analysis'] = True
            
        if any(word in command for word in ['commit', 'commits', 'change', 'changes']):
            params['commit_analysis'] = True
            
        if any(word in command for word in ['release', 'releases', 'version', 'tag']):
            params['include_releases'] = True
            
        if any(word in command for word in ['dataset', 'data', 'training', 'ml']):
            params['dataset_generation'] = True
        
        # Threshold detection
        threshold_match = re.search(r'(\d+)\s*line', command)
        if threshold_match:
            params['threshold'] = int(threshold_match.group(1))
        
        return params
    
    def execute_command(self, command, repo_path=None):
        """Execute parsed command"""
        
        # Detect repository if not provided
        if not repo_path:
            repo_path = self.detect_repo_path(command)
            
        if not repo_path:
            print("❌ No Git repository found. Please specify a repository path or run from a Git repository.")
            return False
            
        print(f"📁 Using repository: {repo_path}")
        
        # Parse command
        params = self.parse_command(command)
        
        try:
            if params['package_analysis'] or 'package' in command:
                print(f"📊 Analyzing packages with {params['threshold']}+ line changes...")
                
                # Create analyzer for this repo
                analyzer = GitRepoAnalyzer(repo_path)
                churn_df, summary_df = analyzer.analyze_package_churn(params['threshold'])
                
                # Generate Excel report
                excel_file = analyzer.generate_excel_report(churn_df, summary_df)
                
                result = {
                    'success': True,
                    'excel_file': excel_file,
                    'total_packages': len(summary_df),
                    'data': summary_df.to_dict('records')
                }
                
                if result['success']:
                    print(f"✅ Analysis complete!")
                    print(f"📄 Excel report: {result['excel_file']}")
                    print(f"📊 Found {result['total_packages']} packages exceeding threshold")
                    
                    if params['dataset_generation']:
                        print("🤖 Generating ML dataset...")
                        dataset_file = analyzer.generate_ml_dataset(result['data'])
                        print(f"📈 Dataset saved: {dataset_file}")
                        
                else:
                    print(f"❌ Analysis failed: {result['error']}")
                    
            elif params['include_releases'] or 'release' in command:
                print("🏷️ Analyzing releases and tags...")
                
                # Create analyzer for this repo
                analyzer = GitRepoAnalyzer(repo_path)
                result = analyzer.analyze_releases(repo_path, params['threshold'])
                
                if result['success']:
                    print(f"✅ Release analysis complete!")
                    print(f"📄 Excel report: {result['excel_file']}")
                    print(f"🏷️ Found {result['total_releases']} releases")
                else:
                    print(f"❌ Release analysis failed: {result['error']}")
                    
            else:
                print("🔍 Running general repository analysis...")
                
                # Create analyzer for this repo
                analyzer = GitRepoAnalyzer(repo_path)
                churn_df, summary_df = analyzer.analyze_package_churn(params['threshold'])
                
                # Generate Excel report
                excel_file = analyzer.generate_excel_report(churn_df, summary_df)
                
                result = {
                    'success': True,
                    'excel_file': excel_file,
                    'total_packages': len(summary_df)
                }
                
                if result['success']:
                    print(f"✅ Analysis complete!")
                    print(f"📄 Excel report: {result['excel_file']}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Error executing command: {str(e)}")
            return False
    
    def interactive_mode(self):
        """Start interactive command mode"""
        print("🚀 Git Repository Analyzer - Interactive Mode")
        print("Type your commands in natural language. Examples:")
        print("  • 'Show me packages with 500+ line changes in excel'")
        print("  • 'Analyze release changes and create dataset'")
        print("  • 'Generate excel for commits over 1000 lines'")
        print("  • Type 'exit' to quit")
        print("-" * 60)
        
        while True:
            try:
                command = input("\n🎯 Enter command: ").strip()
                
                if command.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                    
                if not command:
                    continue
                    
                print(f"\n⚡ Processing: {command}")
                self.execute_command(command)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Git Repository Analyzer with LLM Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --interactive
  %(prog)s --command "show packages with 500+ changes"
  %(prog)s --repo /path/to/repo --command "analyze releases"
  %(prog)s --threshold 1000 --excel --packages
        """
    )
    
    parser.add_argument(
        '--repo', '-r',
        help='Path to Git repository (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--command', '-c',
        help='Natural language command to execute'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive mode'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=int,
        default=500,
        help='Line change threshold (default: 500)'
    )
    
    parser.add_argument(
        '--packages', '-p',
        action='store_true',
        help='Analyze packages'
    )
    
    parser.add_argument(
        '--releases', '-R',
        action='store_true',
        help='Analyze releases'
    )
    
    parser.add_argument(
        '--excel', '-x',
        action='store_true',
        help='Generate Excel output'
    )
    
    parser.add_argument(
        '--dataset', '-d',
        action='store_true',
        help='Generate ML dataset'
    )
    
    args = parser.parse_args()
    
    cli = GitAnalyzerCLI()
    
    if args.interactive:
        cli.interactive_mode()
    elif args.command:
        cli.execute_command(args.command, args.repo)
    else:
        # Build command from arguments
        command_parts = []
        
        if args.packages:
            command_parts.append("analyze packages")
        if args.releases:
            command_parts.append("analyze releases")
        if args.excel:
            command_parts.append("generate excel")
        if args.dataset:
            command_parts.append("create dataset")
            
        if args.threshold != 500:
            command_parts.append(f"with {args.threshold} line threshold")
            
        if command_parts:
            command = " ".join(command_parts)
            cli.execute_command(command, args.repo)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()