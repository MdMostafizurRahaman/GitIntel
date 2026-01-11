"""
Dataset Generators - Main Orchestrator
Run all 7 real dataset generators from one place
"""

import sys
from pathlib import Path

# Import all generators
from defects4j_generator import ProfessionalDefects4JGenerator
from bugsjar_generator import ProfessionalBugsJarGenerator
from manystubs4j_generator import ManySStuBs4JGenerator
from codexglue_generator import CodeXGLUEGenerator
from codesearchnet_generator import CodeSearchNetGenerator
from sourcerer_generator import SourcererGenerator
from promise_generator import ProfessionalPROMISEGenerator


def print_menu():
    """Show menu"""
    print("\n" + "="*70)
    print("REAL DATASET GENERATORS - NO SYNTHETIC DATA")
    print("="*70)
    print("\nAvailable Datasets (All extract REAL data only):")
    print("\n1. Defects4J       - Real bug-fixing commits from Git")
    print("2. Bugs.jar        - Real commit analysis from Git")
    print("3. ManySStuBs4J    - Real method-level changes from Git")
    print("4. CodeXGLUE       - Real code structure from files")
    print("5. CodeSearchNet   - Real code with documentation from files")
    print("6. Sourcerer       - Real repository statistics from files")
    print("7. PROMISE         - Real 42-column metrics from files")
    print("\n8. Generate ALL datasets")
    print("0. Exit")
    print("="*70)


def run_defects4j(repo_path: str):
    """Run Defects4J generator"""
    print("\nGenerating Defects4J dataset...")
    generator = ProfessionalDefects4JGenerator(repo_path, commit_limit=10)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS Defects4J: {result['total_bugs']} bug instances")
        print(f"Output: {result['output_dir']}")
        return True


def run_bugsjar(repo_path: str):
    """Run Bugs.jar generator"""
    print("\nGenerating Bugs.jar dataset...")
    generator = ProfessionalBugsJarGenerator(repo_path, commit_limit=10)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS Bugs.jar: {result['total_commits']} commits")
        print(f"Output: {result['output_dir']}")
        return True


def run_manystubs(repo_path: str):
    """Run ManySStuBs4J generator"""
    print("\nGenerating ManySStuBs4J dataset...")
    generator = ManySStuBs4JGenerator(repo_path)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS ManySStuBs4J: {result['total_stubs']} method stubs")
        print(f"Output: {result['output_dir']}")
        return True


def run_codexglue(repo_path: str):
    """Run CodeXGLUE generator"""
    print("\nGenerating CodeXGLUE dataset...")
    generator = CodeXGLUEGenerator(repo_path, file_limit=500)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS CodeXGLUE: {result['total_files']} files")
        print(f"Output: {result['output_dir']}")
        return True


def run_codesearchnet(repo_path: str):
    """Run CodeSearchNet generator"""
    print("\nGenerating CodeSearchNet dataset...")
    generator = CodeSearchNetGenerator(repo_path, file_limit=500)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS CodeSearchNet: {result['total_files']} files")
        print(f"Output: {result['output_dir']}")
        return True


def run_sourcerer(repo_path: str):
    """Run Sourcerer generator"""
    print("\nGenerating Sourcerer dataset...")
    generator = SourcererGenerator(repo_path)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS Sourcerer: {result['total_files']} files, {result['total_loc']} LOC")
        print(f"Output: {result['output_dir']}")
        return True


def run_promise(repo_path: str):
    """Run PROMISE generator"""
    print("\nGenerating PROMISE dataset...")
    generator = ProfessionalPROMISEGenerator(repo_path, file_limit=120)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return False
    else:
        print(f"SUCCESS PROMISE: {result['total_files']} files with {result['columns']} columns")
        print(f"Output: {result['output_dir']}")
        return True


def run_all(repo_path: str):
    """Run all generators"""
    print("\n" + "GENERATING ALL 7 DATASETS ".center(70, "="))
    
    results = []
    
    results.append(("Defects4J", run_defects4j(repo_path)))
    results.append(("Bugs.jar", run_bugsjar(repo_path)))
    results.append(("ManySStuBs4J", run_manystubs(repo_path)))
    results.append(("CodeXGLUE", run_codexglue(repo_path)))
    results.append(("CodeSearchNet", run_codesearchnet(repo_path)))
    results.append(("Sourcerer", run_sourcerer(repo_path)))
    results.append(("PROMISE", run_promise(repo_path)))
    
    # Summary
    print("\n" + "SUMMARY ".center(70, "="))
    success_count = sum(1 for _, success in results if success)
    
    for name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"{name:20} {status}")
    
    print(f"\nCompleted: {success_count}/7 datasets generated successfully")
    print("="*70)


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command-line mode
        repo_path = sys.argv[1]
        choice = sys.argv[2] if len(sys.argv) > 2 else "8"
    else:
        # Interactive mode
        print_menu()
        
        repo_path = input("\nEnter repository path: ").strip()
        if not repo_path or not Path(repo_path).exists():
            print("ERROR: Invalid repository path")
            return
        
        choice = input("\nEnter choice (0-8): ").strip()
    
    # Execute choice
    if choice == "1":
        run_defects4j(repo_path)
    elif choice == "2":
        run_bugsjar(repo_path)
    elif choice == "3":
        run_manystubs(repo_path)
    elif choice == "4":
        run_codexglue(repo_path)
    elif choice == "5":
        run_codesearchnet(repo_path)
    elif choice == "6":
        run_sourcerer(repo_path)
    elif choice == "7":
        run_promise(repo_path)
    elif choice == "8":
        run_all(repo_path)
    elif choice == "0":
        print("Goodbye!")
    else:
        print("ERROR: Invalid choice")


if __name__ == "__main__":
    main()
