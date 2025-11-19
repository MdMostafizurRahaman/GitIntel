#!/usr/bin/env python3
"""
Dataset Management System - Installation Verification Script
ইনস্টলেশন যাচাইকরণ স্ক্রিপ্ট
"""

import sys
import os
import subprocess
import json
from pathlib import Path

class VerificationReport:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_check(self, name, status, details=""):
        """Add a check result"""
        result = {
            "name": name,
            "status": status,
            "details": details
        }
        self.checks.append(result)
        
        if status == "✅ PASS":
            self.passed += 1
        elif status == "❌ FAIL":
            self.failed += 1
        elif status == "⚠️  WARNING":
            self.warnings += 1
    
    def print_report(self):
        """Print verification report"""
        print("\n" + "="*60)
        print("Dataset Management System - Installation Verification")
        print("="*60 + "\n")
        
        for check in self.checks:
            print(f"{check['status']} {check['name']}")
            if check['details']:
                print(f"   └─ {check['details']}")
        
        print("\n" + "="*60)
        print(f"Results: {self.passed} passed, {self.failed} failed, {self.warnings} warnings")
        print("="*60 + "\n")
        
        return self.failed == 0

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return "✅ PASS", f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return "❌ FAIL", f"Python {version.major}.{version.minor} (need 3.8+)"

def check_module(module_name):
    """Check if a Python module is installed"""
    try:
        __import__(module_name)
        return True, f"Installed"
    except ImportError:
        return False, f"Not installed"

def check_python_packages():
    """Check required Python packages"""
    report = VerificationReport()
    
    packages = {
        "neo4j": "Neo4j database driver",
        "click": "CLI framework",
        "PyQt5": "GUI framework",
        "fastapi": "API framework",
        "uvicorn": "ASGI server",
        "pandas": "Data processing",
        "requests": "HTTP client",
    }
    
    for package, description in packages.items():
        success, details = check_module(package)
        status = "✅ PASS" if success else "❌ FAIL"
        report.add_check(f"Python Package: {package}", status, f"{description} - {details}")
    
    return report

def check_folders():
    """Check if required folders exist"""
    report = VerificationReport()
    
    base_dir = Path(__file__).parent
    required_folders = [
        "config",
        "extractors",
        "processors",
        "labelers",
        "neo4j",
        "cli",
        "gui",
        "api",
        "utils",
        "docs",
    ]
    
    for folder in required_folders:
        folder_path = base_dir / folder
        if folder_path.exists() and folder_path.is_dir():
            status = "✅ PASS"
            details = f"Found at {folder_path}"
        else:
            status = "❌ FAIL"
            details = f"Missing at {folder_path}"
        report.add_check(f"Folder: {folder}", status, details)
    
    return report

def check_files():
    """Check if required files exist"""
    report = VerificationReport()
    
    base_dir = Path(__file__).parent
    required_files = {
        "config/config.py": "Configuration file",
        "extractors/base_extractor.py": "Base extractor class",
        "extractors/factory.py": "Extractor factory",
        "processors/base_processor.py": "Processing pipeline",
        "labelers/labeler.py": "Labeling system",
        "neo4j/manager.py": "Neo4j manager",
        "neo4j/schema.py": "Database schema",
        "cli/main.py": "CLI application",
        "gui/app.py": "GUI application",
        "api/server.py": "API server",
        "utils/logger.py": "Logging utility",
        "utils/helpers.py": "Helper functions",
        "requirements.txt": "Python dependencies",
        "README.md": "Main documentation",
        "SUMMARY.md": "Quick summary",
        "INDEX.py": "Quick reference",
    }
    
    for file_path, description in required_files.items():
        full_path = base_dir / file_path
        if full_path.exists() and full_path.is_file():
            status = "✅ PASS"
            size = full_path.stat().st_size
            details = f"{description} - {size:,} bytes"
        else:
            status = "❌ FAIL"
            details = f"{description} - Missing"
        report.add_check(f"File: {file_path}", status, details)
    
    return report

def check_neo4j():
    """Check Neo4j connectivity"""
    report = VerificationReport()
    
    try:
        from neo4j import GraphDatabase
        
        # Try to get Neo4j config
        try:
            from config.config import NEO4J_CONFIG
            config = NEO4J_CONFIG
        except:
            config = {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password"),
            }
        
        # Try to connect
        try:
            driver = GraphDatabase.driver(
                config["uri"],
                auth=(config["user"], config["password"])
            )
            with driver.session() as session:
                result = session.run("RETURN 1")
            driver.close()
            
            report.add_check(
                "Neo4j Connection",
                "✅ PASS",
                f"Successfully connected to {config['uri']}"
            )
        except Exception as e:
            report.add_check(
                "Neo4j Connection",
                "⚠️  WARNING",
                f"Could not connect: {str(e)[:50]}... (Make sure Neo4j is running)"
            )
    except ImportError:
        report.add_check(
            "Neo4j Connection",
            "⚠️  WARNING",
            "Neo4j driver not installed (run: pip install neo4j)"
        )
    
    return report

def check_cli():
    """Check CLI functionality"""
    report = VerificationReport()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--help"],
            capture_output=True,
            timeout=5,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0 and b"list-datasets" in result.stdout:
            report.add_check(
                "CLI Command",
                "✅ PASS",
                "CLI module loads and responds correctly"
            )
        else:
            report.add_check(
                "CLI Command",
                "⚠️  WARNING",
                f"CLI returned code {result.returncode}"
            )
    except subprocess.TimeoutExpired:
        report.add_check(
            "CLI Command",
            "⚠️  WARNING",
            "CLI command timed out"
        )
    except Exception as e:
        report.add_check(
            "CLI Command",
            "❌ FAIL",
            f"Error: {str(e)[:50]}"
        )
    
    return report

def check_gui():
    """Check GUI availability"""
    report = VerificationReport()
    
    try:
        from PyQt5.QtWidgets import QApplication
        report.add_check(
            "GUI Framework",
            "✅ PASS",
            "PyQt5 is installed and available"
        )
    except ImportError:
        report.add_check(
            "GUI Framework",
            "❌ FAIL",
            "PyQt5 not installed (run: pip install PyQt5)"
        )

    return report

def check_api():
    """Check API server functionality"""
    report = VerificationReport()
    
    try:
        import fastapi
        import uvicorn
        report.add_check(
            "API Framework",
            "✅ PASS",
            f"FastAPI {fastapi.__version__} and uvicorn available"
        )
    except ImportError as e:
        report.add_check(
            "API Framework",
            "❌ FAIL",
            f"Missing: {str(e)}"
        )
    
    return report

def main():
    """Run all verification checks"""
    print("\n🔍 Starting Installation Verification...\n")
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    all_reports = []
    
    # Python Version
    print("Checking Python version...")
    report = VerificationReport()
    status, details = check_python_version()
    report.add_check("Python Version", status, details)
    report.print_report()
    all_reports.append(report)
    
    # Python Packages
    print("Checking Python packages...")
    report = check_python_packages()
    report.print_report()
    all_reports.append(report)
    
    # Folders
    print("Checking folders...")
    report = check_folders()
    report.print_report()
    all_reports.append(report)
    
    # Files
    print("Checking files...")
    report = check_files()
    report.print_report()
    all_reports.append(report)
    
    # Neo4j
    print("Checking Neo4j...")
    report = check_neo4j()
    report.print_report()
    all_reports.append(report)
    
    # CLI
    print("Checking CLI...")
    report = check_cli()
    report.print_report()
    all_reports.append(report)
    
    # GUI
    print("Checking GUI...")
    report = check_gui()
    report.print_report()
    all_reports.append(report)
    
    # API
    print("Checking API...")
    report = check_api()
    report.print_report()
    all_reports.append(report)
    
    # Summary
    total_passed = sum(r.passed for r in all_reports)
    total_failed = sum(r.failed for r in all_reports)
    total_warnings = sum(r.warnings for r in all_reports)
    
    print("\n" + "="*60)
    print("OVERALL VERIFICATION SUMMARY")
    print("="*60)
    print(f"✅ Passed:  {total_passed}")
    print(f"❌ Failed:  {total_failed}")
    print(f"⚠️  Warnings: {total_warnings}")
    print("="*60 + "\n")
    
    if total_failed == 0:
        print("🎉 Installation verification PASSED!")
        print("\n📖 Next steps:")
        print("   1. Read docs/SETUP.md for detailed configuration")
        print("   2. Configure Neo4j connection (.env file)")
        print("   3. Test with: python -m cli.main status")
        print("   4. Choose your interface: CLI, GUI, or API")
        print("\n✨ System is ready to use!\n")
        return 0
    else:
        print("⚠️  Installation verification FAILED or has warnings")
        print("\n📖 Fix issues:")
        print("   1. Read the error messages above")
        print("   2. Install missing packages: pip install -r requirements.txt")
        print("   3. Ensure Neo4j is running and configured")
        print("   4. Check docs/SETUP.md for detailed help\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
