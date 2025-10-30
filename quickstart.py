#!/usr/bin/env python3
"""
GitIntel Quick Start Wizard
Interactive setup and onboarding for new users
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

class GitIntelWizard:
    def __init__(self):
        self.config = {}
        self.repo_path = None
        
    def print_welcome(self):
        """Print welcome message"""
        print("🎉 Welcome to GitIntel!")
        print("=" * 50)
        print("Let's get you started with repository intelligence")
        print("Traditional Analytics + AI-Powered Insights")
        print()
        
    def check_prerequisites(self):
        """Check if system is ready"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
            
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check if git is available
        try:
            subprocess.check_output(['git', '--version'], stderr=subprocess.STDOUT)
            print("✅ Git available")
        except:
            print("⚠️ Git not found (some features may be limited)")
            
        return True
        
    def select_repository(self):
        """Help user select repository to analyze"""
        print("\n📁 Repository Selection")
        print("-" * 25)
        
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
        
        # Check if current directory is a git repo
        if os.path.exists(os.path.join(current_dir, '.git')):
            use_current = input("Current directory is a Git repository. Analyze it? (y/n): ").lower()
            if use_current == 'y':
                self.repo_path = current_dir
                print(f"✅ Selected: {current_dir}")
                return True
        
        # Ask for repository path
        while True:
            repo_input = input("Enter repository path (or 'q' to quit): ").strip()
            
            if repo_input.lower() == 'q':
                return False
                
            if not repo_input:
                repo_input = current_dir
                
            if os.path.exists(repo_input):
                if os.path.exists(os.path.join(repo_input, '.git')):
                    self.repo_path = os.path.abspath(repo_input)
                    print(f"✅ Selected: {self.repo_path}")
                    return True
                else:
                    print("❌ Not a Git repository")
            else:
                print("❌ Path not found")
                
    def configure_api_key(self):
        """Help configure API key"""
        print("\n🔑 API Configuration")
        print("-" * 20)
        
        print("GitIntel uses Google Gemini for AI features.")
        print("You can get a free API key at: https://makersuite.google.com/app/apikey")
        print()
        
        has_key = input("Do you have a Gemini API key? (y/n): ").lower()
        
        if has_key == 'y':
            api_key = input("Enter your Gemini API key: ").strip()
            if api_key:
                self.config['GEMINI_API_KEY'] = api_key
                print("✅ API key configured")
                return True
        
        print("ℹ️ You can add the API key later to .env file")
        print("ℹ️ Basic analysis will work without API key")
        return False
        
    def choose_analysis_mode(self):
        """Let user choose analysis type"""
        print("\n🎯 Analysis Mode")
        print("-" * 15)
        
        modes = [
            ("1", "Quick Insights", "Fast overview of repository"),
            ("2", "Traditional Analysis", "Detailed statistical analysis"),
            ("3", "AI Q&A Demo", "Interactive question answering"),
            ("4", "Full Analysis", "Complete traditional + AI analysis"),
            ("5", "Custom", "I'll choose options myself")
        ]
        
        for num, title, desc in modes:
            print(f"{num}. {title} - {desc}")
            
        while True:
            choice = input("\nSelect analysis mode (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print("Invalid choice. Please select 1-5.")
            
    def run_analysis(self, mode):
        """Run the selected analysis"""
        print(f"\n🚀 Running Analysis")
        print("-" * 20)
        
        # Base command
        cmd = [sys.executable, "gitintel.py", "--repo", self.repo_path]
        
        if mode == "1":  # Quick insights
            cmd.extend(["--insights"])
            print("Running quick insights...")
            
        elif mode == "2":  # Traditional
            cmd.extend(["--analyze", "traditional", "--full-report"])
            print("Running traditional analysis...")
            
        elif mode == "3":  # AI Q&A Demo
            print("Starting interactive Q&A session...")
            print("Try asking questions like:")
            print("  • Who are the top contributors?")
            print("  • কারা এই প্রজেক্টের প্রধান ডেভেলপার?")
            print("  • Which files have high complexity?")
            cmd.extend(["--interactive"])
            
        elif mode == "4":  # Full analysis
            cmd.extend(["--full-report"])
            print("Running complete analysis...")
            
        elif mode == "5":  # Custom
            print("Run custom analysis with: python gitintel.py --help")
            return
            
        # Add verbose flag
        cmd.append("--verbose")
        
        # Set environment if API key configured
        env = os.environ.copy()
        if 'GEMINI_API_KEY' in self.config:
            env['GEMINI_API_KEY'] = self.config['GEMINI_API_KEY']
            
        try:
            print(f"Command: {' '.join(cmd)}")
            print("=" * 50)
            subprocess.run(cmd, env=env)
        except KeyboardInterrupt:
            print("\n❌ Analysis interrupted")
        except Exception as e:
            print(f"❌ Error running analysis: {e}")
            
    def create_env_file(self):
        """Create .env file with configuration"""
        if not self.config:
            return
            
        print("\n💾 Saving Configuration")
        print("-" * 22)
        
        env_content = "# GitIntel Environment Configuration\n"
        
        if 'GEMINI_API_KEY' in self.config:
            env_content += f"GEMINI_API_KEY={self.config['GEMINI_API_KEY']}\n"
            
        env_content += """
# Neo4j Database (optional)
# NEO4J_HOST=localhost
# NEO4J_PORT=7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password

# Preferences
DEFAULT_LANGUAGE=bengali
EXCEL_OUTPUT=true
VERBOSE_LOGGING=false
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
            
        print("✅ Configuration saved to .env")
        
    def show_next_steps(self):
        """Show what user can do next"""
        print("\n🎯 What's Next?")
        print("-" * 15)
        
        print("Try these commands:")
        print()
        
        print("🔍 Quick Analysis:")
        print(f"   python gitintel.py --repo '{self.repo_path}' --insights")
        print()
        
        print("💬 Ask Questions:")
        print(f"   python gitintel.py --repo '{self.repo_path}' --ask \"Who are the top contributors?\"")
        print(f"   python gitintel.py --ask \"কারা প্রধান ডেভেলপার?\"")
        print()
        
        print("📊 Full Report:")
        print(f"   python gitintel.py --repo '{self.repo_path}' --full-report")
        print()
        
        print("🤖 Interactive Session:")
        print(f"   python gitintel.py --repo '{self.repo_path}' --interactive")
        print()
        
        print("📚 Help:")
        print("   python gitintel.py --help")
        print()
        
        print("🔗 Documentation: README_GITINTEL.md")
        
    def run_wizard(self):
        """Run the complete wizard"""
        self.print_welcome()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met")
            return False
            
        # Select repository
        if not self.select_repository():
            print("❌ No repository selected")
            return False
            
        # Configure API key
        self.configure_api_key()
        
        # Create .env file
        self.create_env_file()
        
        # Choose analysis mode
        mode = self.choose_analysis_mode()
        
        # Run analysis
        self.run_analysis(mode)
        
        # Show next steps
        self.show_next_steps()
        
        print("\n🎉 Setup Complete!")
        print("Happy analyzing with GitIntel! 🚀")
        
        return True

def main():
    """Main wizard function"""
    wizard = GitIntelWizard()
    wizard.run_wizard()

if __name__ == "__main__":
    main()