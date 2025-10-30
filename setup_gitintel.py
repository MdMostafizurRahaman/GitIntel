#!/usr/bin/env python3
"""
GitIntel Setup and Installation Script
Sets up the unified GitIntel platform with all dependencies
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """Print GitIntel setup banner"""
    print("🚀 GitIntel Setup")
    print("=" * 50)
    print("Setting up Unified Repository Intelligence Platform")
    print("Traditional Analytics + RepoChat Integration")
    print()

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    requirements = [
        "pydriller>=2.5.0",
        "google-generativeai>=0.3.0",
        "neo4j>=5.0.0",
        "xlsxwriter>=3.0.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "plotly>=5.0.0",
        "python-dotenv>=0.19.0",
        "click>=8.0.0",
        "rich>=12.0.0",
        "tqdm>=4.62.0"
    ]
    
    for requirement in requirements:
        try:
            print(f"   Installing {requirement}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", requirement
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ {requirement} installed")
        except subprocess.CalledProcessError:
            print(f"   ⚠️ Failed to install {requirement}")
    
    print("✅ Dependencies installation complete")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "analysis_output",
        "reports", 
        "cache",
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ Created {directory}/")
    
    print("✅ Directory structure created")

def setup_configuration():
    """Setup configuration files"""
    print("⚙️ Setting up configuration...")
    
    # Create .env file template
    env_template = """# GitIntel Environment Configuration
# Copy this to .env and fill in your values

# Google Gemini API Key for LLM features
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j Database (optional, defaults to in-memory)
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Output preferences
DEFAULT_LANGUAGE=bengali
EXCEL_OUTPUT=true
VERBOSE_LOGGING=false
"""
    
    with open(".env.template", "w") as f:
        f.write(env_template)
    
    print("   ✅ Created .env.template")
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("   💡 Copy .env.template to .env and configure your API keys")
    
    print("✅ Configuration setup complete")

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import pydriller
        print("   ✅ PyDriller import successful")
        
        try:
            import google.generativeai
            print("   ✅ Google Generative AI import successful")
        except ImportError:
            print("   ⚠️ Google Generative AI import failed (API key needed)")
        
        try:
            import neo4j
            print("   ✅ Neo4j import successful")
        except ImportError:
            print("   ⚠️ Neo4j import failed (will use in-memory fallback)")
        
        import xlsxwriter
        print("   ✅ Excel writer import successful")
        
        # Test GitIntel import
        sys.path.append(".")
        try:
            from gitintel import GitIntelEngine
            print("   ✅ GitIntel engine import successful")
        except ImportError as e:
            print(f"   ⚠️ GitIntel import failed: {e}")
        
        print("✅ Installation test complete")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples"""
    print("📖 Usage Examples:")
    print("=" * 30)
    print()
    
    examples = [
        ("Basic Analysis", "python gitintel.py --repo ./your-project"),
        ("Full Report", "python gitintel.py --repo ./your-project --full-report"),
        ("Interactive Q&A", "python gitintel.py --repo ./your-project --interactive"),
        ("Ask Question", 'python gitintel.py --repo ./your-project --ask "Who are the top contributors?"'),
        ("Bengali Question", 'python gitintel.py --ask "কে সবচেয়ে বেশি commit করেছে?"'),
        ("Traditional Only", "python gitintel.py --repo ./your-project --analyze traditional"),
        ("Quick Insights", "python gitintel.py --repo ./your-project --insights")
    ]
    
    for title, command in examples:
        print(f"🔹 {title}:")
        print(f"   {command}")
        print()

def create_sample_script():
    """Create a sample demo script"""
    print("📝 Creating sample demo script...")
    
    demo_script = '''#!/usr/bin/env python3
"""
GitIntel Demo Script
Demonstrates unified Traditional Analytics + RepoChat features
"""

import os
import sys
from pathlib import Path

# Add GitIntel to path
sys.path.append(str(Path(__file__).parent))

from gitintel import GitIntelEngine

def demo_gitintel():
    """Demonstrate GitIntel features"""
    print("🎭 GitIntel Demo")
    print("=" * 40)
    
    # Replace with your repository path
    repo_path = input("Enter repository path (or press Enter for current directory): ").strip()
    if not repo_path:
        repo_path = "."
    
    if not os.path.exists(repo_path):
        print(f"❌ Repository not found: {repo_path}")
        return
    
    # Initialize GitIntel
    engine = GitIntelEngine(verbose=True)
    engine.setup(repo_path)
    
    print("\\n1️⃣ Traditional Analysis Demo")
    print("-" * 30)
    traditional_results = engine.run_traditional_analysis(repo_path)
    
    if "error" not in traditional_results:
        print("✅ Traditional analysis complete!")
        print(f"📊 Found {len(traditional_results.get('contributors', []))} contributors")
    
    print("\\n2️⃣ Knowledge Graph Demo")  
    print("-" * 25)
    kg_results = engine.build_knowledge_graph(repo_path)
    
    if "error" not in kg_results:
        print("✅ Knowledge graph built!")
    
    print("\\n3️⃣ Correlation Demo")
    print("-" * 20)
    correlations = engine.correlate_insights(traditional_results, kg_results)
    
    for insight in correlations.get("enhanced_insights", []):
        print(f"💡 {insight}")
    
    print("\\n4️⃣ Interactive Q&A Demo")
    print("-" * 25)
    
    sample_questions = [
        "Who are the top contributors?",
        "কে সবচেয়ে বেশি commit করেছে?",
        "Which files have high complexity?"
    ]
    
    for question in sample_questions:
        print(f"❓ {question}")
        answer = engine.ask_question(question)
        print(f"🤖 {answer[:100]}...")
        print()
    
    print("✅ Demo complete! Try running:")
    print("   python gitintel.py --repo . --interactive")

if __name__ == "__main__":
    demo_gitintel()
'''
    
    with open("demo_gitintel.py", "w") as f:
        f.write(demo_script)
    
    print("   ✅ Created demo_gitintel.py")
    print("   💡 Run: python demo_gitintel.py")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"❌ Dependency installation failed: {e}")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup configuration
    setup_configuration()
    
    # Test installation
    if not test_installation():
        print("⚠️ Some components may not work properly")
        print("Check the error messages above and install missing dependencies")
    
    # Create demo script
    create_sample_script()
    
    # Show usage
    show_usage_examples()
    
    print("🎉 GitIntel setup complete!")
    print()
    print("Next steps:")
    print("1. Copy .env.template to .env and add your API keys")
    print("2. Run: python demo_gitintel.py")
    print("3. Try: python gitintel.py --repo ./your-project --interactive")
    print()
    print("🇧🇩 Bengali questions supported!")
    print("🚀 Happy analyzing!")

if __name__ == "__main__":
    main()