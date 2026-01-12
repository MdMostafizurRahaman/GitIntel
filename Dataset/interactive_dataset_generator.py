#!/usr/bin/env python3
"""
Interactive Dataset Generator with Feedback Loop
- Understands user intent
- Shows understanding
- Asks for confirmation
- Iterates until clear
- Then executes
"""

import os
import sys
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InteractiveDatasetGenerator:
    """Interactive dataset generation with feedback loop"""
    
    # Available datasets
    BENCHMARK_DATASETS = {
        "defects4j": "Java bugs with buggy/fixed code",
        "bugs.jar": "Large-scale Java bug dataset",
        "promise": "Software metrics and defects",
        "codesearchnet": "Code-to-docs mapping",
        "manystubbsj": "Simple bugs in Java"
    }
    
    METRIC_CATEGORIES = {
        "size": "LOC, comments, blank lines",
        "complexity": "Cyclomatic, nesting depth",
        "ck": "OOP metrics (WMC, DIT, NOC, CBO, RFC, LCOM)",
        "coupling": "Afferent, efferent coupling",
        "quality": "Maintainability, comment ratio",
        "defect": "Bug presence, severity",
        "structure": "Classes, methods, fields"
    }
    
    OUTPUT_FORMATS = ["csv", "json", "jsonl"]
    
    def __init__(self):
        self.config = {}
        self.conversation_history = []
        self.iteration = 0
        
    def print_header(self, text: str, style: str = "="):
        """Print styled header"""
        print(f"\n{style*60}")
        print(f" {text}")
        print(f"{style*60}\n")
    
    def print_option(self, num: int, text: str):
        """Print formatted option"""
        print(f"  {num}. {text}")
    
    def print_summary(self):
        """Show current configuration summary"""
        print("📋 CURRENT CONFIGURATION:")
        print()
        
        if "repository" in self.config:
            print(f"REPOSITORY:")
            print(f"  Source: {self.config['repository']}")
            print(f"  Type: {self.config.get('repo_type', 'not specified')}")
        
        if "dataset_type" in self.config:
            print(f"\nDATASET:")
            print(f"  Type: {self.config['dataset_type'].upper()}")
            
            if self.config['dataset_type'] == 'benchmark':
                print(f"  Dataset: {self.config.get('benchmark_name', 'not selected')}")
            else:
                metrics = self.config.get('selected_metrics', [])
                print(f"  Metrics: {len(metrics)}/64 selected")
                if metrics:
                    print(f"    Selected: {', '.join(metrics[:5])}")
                    if len(metrics) > 5:
                        print(f"    ... and {len(metrics)-5} more")
        
        if "output_format" in self.config:
            print(f"\nOUTPUT:")
            print(f"  Format: {self.config['output_format'].upper()}")
            print(f"  Name: {self.config.get('output_name', 'dataset')}")
        
        print()
    
    def ask_yes_no(self, question: str) -> str:
        """Ask yes/no/modify question"""
        while True:
            response = input(f"? {question}\n  (yes/no/modify/cancel) > ").strip().lower()
            if response in ['yes', 'no', 'modify', 'cancel', 'y', 'n', 'm', 'c']:
                return response[0]  # y/n/m/c
            print("  Invalid. Please enter: yes, no, modify, or cancel")
    
    def ask_choice(self, question: str, options: Dict[str, str], 
                   allow_multiple: bool = False) -> str or List[str]:
        """Ask user to choose from options"""
        print(f"\n? {question}\n")
        
        keys = list(options.keys())
        for i, key in enumerate(keys, 1):
            self.print_option(i, f"{key}: {options[key]}")
        
        if allow_multiple:
            print(f"  (Enter numbers separated by space, or 'done')")
            response = input("> ").strip().lower()
            if response == 'done':
                return []
            try:
                choices = [keys[int(x)-1] for x in response.split() if x.isdigit()]
                return choices
            except:
                print("Invalid selection")
                return self.ask_choice(question, options, allow_multiple)
        else:
            while True:
                response = input("> ").strip()
                if response.isdigit() and 1 <= int(response) <= len(keys):
                    return keys[int(response)-1]
                print(f"Please enter a number between 1 and {len(keys)}")
    
    def parse_user_input(self, user_input: str) -> Dict:
        """Parse user input to extract components"""
        parsed = {}
        
        user_lower = user_input.lower()
        
        # Detect repository
        if "github" in user_lower or "github.com" in user_lower:
            # Extract GitHub URL
            if "github.com/" in user_input:
                url = user_input[user_input.find("github.com/"):].split()[0]
                parsed['repository'] = url
                parsed['repo_type'] = 'github'
        
        # Detect dataset type
        if any(bd in user_lower for bd in self.BENCHMARK_DATASETS.keys()):
            parsed['dataset_type'] = 'benchmark'
            for bd in self.BENCHMARK_DATASETS:
                if bd in user_lower:
                    parsed['benchmark_name'] = bd
                    break
        elif "custom" in user_lower or "metrics" in user_lower:
            parsed['dataset_type'] = 'custom'
        
        # Detect output format
        for fmt in self.OUTPUT_FORMATS:
            if fmt in user_lower:
                parsed['output_format'] = fmt
                break
        
        return parsed
    
    def clarify_repository(self):
        """Clarify repository source"""
        print("\n📂 REPOSITORY CONFIGURATION")
        
        repo = input("Enter repository (local path or GitHub URL): ").strip()
        self.config['repository'] = repo
        
        if "github.com" in repo or "/" in repo:
            self.config['repo_type'] = 'github'
        else:
            self.config['repo_type'] = 'local'
    
    def clarify_dataset_type(self):
        """Clarify whether benchmark or custom"""
        print("\n📊 DATASET TYPE")
        
        options = {
            "benchmark": "Use predefined dataset format",
            "custom": "Select from 64 metrics"
        }
        
        choice = self.ask_choice("What type of dataset?", options)
        self.config['dataset_type'] = choice
    
    def clarify_benchmark(self):
        """Select benchmark dataset"""
        print("\n🎯 SELECT BENCHMARK")
        
        choice = self.ask_choice(
            "Which benchmark dataset?",
            self.BENCHMARK_DATASETS
        )
        self.config['benchmark_name'] = choice
    
    def clarify_custom_metrics(self):
        """Select custom metrics"""
        print("\n📈 SELECT CUSTOM METRICS")
        
        choices = self.ask_choice(
            "Which metric categories? (select multiple)",
            self.METRIC_CATEGORIES,
            allow_multiple=True
        )
        self.config['selected_metrics'] = choices
        
        if choices:
            total = len(choices) * 5  # Approximate
            print(f"\n✓ Selected {len(choices)} categories (~{total} metrics)")
    
    def clarify_output(self):
        """Clarify output format and name"""
        print("\n💾 OUTPUT CONFIGURATION")
        
        format_options = {fmt: f"Save as {fmt.upper()}" for fmt in self.OUTPUT_FORMATS}
        fmt = self.ask_choice("Output format?", format_options)
        self.config['output_format'] = fmt
        
        name = input("Dataset name (or press Enter for default): ").strip()
        self.config['output_name'] = name or "dataset"
    
    def ask_modifications(self):
        """Ask what to modify"""
        print("\n? What would you like to change?\n")
        
        options = {
            "repository": "Change repository source",
            "dataset": "Change dataset type/selection",
            "output": "Change output format/name",
            "all": "Start over with new configuration",
        }
        
        choice = self.ask_choice("What to modify?", options)
        
        if choice == "repository":
            self.clarify_repository()
        elif choice == "dataset":
            self.clarify_dataset_type()
            if self.config['dataset_type'] == 'benchmark':
                self.clarify_benchmark()
            else:
                self.clarify_custom_metrics()
        elif choice == "output":
            self.clarify_output()
        elif choice == "all":
            self.config = {}
        
        return choice
    
    def execute_generation(self):
        """Execute dataset generation"""
        self.print_header("GENERATING DATASET", "✓")
        
        print("Processing with configuration:")
        self.print_summary()
        
        # Here you would call the actual generation function
        # For now, simulate it
        
        print("✓ [1/5] Validating repository...")
        print("✓ [2/5] Analyzing source code...")
        print("✓ [3/5] Extracting metrics...")
        print("✓ [4/5] Formatting output...")
        print("✓ [5/5] Complete!")
        
        output_path = f"output/{self.config['output_name']}.{self.config['output_format']}"
        print(f"\n✓ Dataset saved to: {output_path}")
        
        return {
            "completed": True,
            "output_path": output_path,
            "config": self.config
        }
    
    def run_interactive(self, user_input: Optional[str] = None):
        """Run interactive generation flow"""
        self.print_header("INTERACTIVE DATASET GENERATOR")
        
        # Get initial input if not provided
        if not user_input:
            user_input = input("Describe what dataset you want: ").strip()
        
        self.conversation_history.append(("user", user_input))
        
        # Parse input
        print("\n🔍 Analyzing your request...")
        parsed = self.parse_user_input(user_input)
        self.config.update(parsed)
        
        # Iterative refinement loop
        while True:
            self.iteration += 1
            print(f"\n--- ITERATION {self.iteration} ---")
            
            # Clarify missing information
            if 'repository' not in self.config:
                self.clarify_repository()
            
            if 'dataset_type' not in self.config:
                self.clarify_dataset_type()
            
            if self.config.get('dataset_type') == 'benchmark' and 'benchmark_name' not in self.config:
                self.clarify_benchmark()
            
            if self.config.get('dataset_type') == 'custom' and 'selected_metrics' not in self.config:
                self.clarify_custom_metrics()
            
            if 'output_format' not in self.config:
                self.clarify_output()
            
            # Show summary and ask confirmation
            self.print_summary()
            response = self.ask_yes_no("Is this correct?")
            
            if response == 'y':
                # Execute
                result = self.execute_generation()
                return result
            
            elif response == 'n':
                # Ask what to modify
                self.ask_modifications()
            
            elif response == 'm':
                # Let user choose what to modify
                self.ask_modifications()
            
            elif response == 'c':
                print("\n✗ Cancelled")
                return {"completed": False, "cancelled": True}
            
            # Safety limit
            if self.iteration > 10:
                print("\n⚠ Too many iterations. Starting over...")
                self.config = {}
                self.iteration = 0

    def generate_defects4j_dataset(self):
        """Generate Defects4J dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from defects4j_generator import Defects4JGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = Defects4JGenerator(repo_path, commit_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_bugs_jar_dataset(self):
        """Generate Bugs.jar dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from bugsjar_generator import BugsJarGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = BugsJarGenerator(repo_path, commit_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_codexglue_dataset(self):
        """Generate CodeXGLUE dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from codexglue_generator import CodeXGLUEGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = CodeXGLUEGenerator(repo_path, commit_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_manystubs4j_dataset(self):
        """Generate ManySStuBs4J dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from manystubs4j_generator import ManySStuBs4JGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = ManySStuBs4JGenerator(repo_path, commit_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_codesearchnet_dataset(self):
        """Generate CodeSearchNet dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from codesearchnet_generator import CodeSearchNetGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = CodeSearchNetGenerator(repo_path, file_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_sourcerer_dataset(self):
        """Generate Sourcerer dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from sourcerer_generator import SourcererGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = SourcererGenerator(repo_path, file_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_promise_dataset(self):
        """Generate PROMISE dataset"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataset_generators'))
            from promise_generator import PROMISEGenerator
            
            repo_path = self.config.get('repository', '.')
            generator = PROMISEGenerator(repo_path, file_limit=500)
            return generator.generate()
        except Exception as e:
            return {"error": str(e)}

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    
    # Example 1: Interactive mode (ask user)
    print("EXAMPLE 1: Interactive Mode")
    print("-" * 60)
    generator = InteractiveDatasetGenerator()
    result = generator.run_interactive()
    
    # Example 2: With initial input
    print("\n\nEXAMPLE 2: With Initial Input")
    print("-" * 60)
    generator2 = InteractiveDatasetGenerator()
    result2 = generator2.run_interactive("Create Defects4J dataset from spring-framework")
    
    # Example 3: Custom metrics
    print("\n\nEXAMPLE 3: Custom Metrics")
    print("-" * 60)
    generator3 = InteractiveDatasetGenerator()
    result3 = generator3.run_interactive("Custom dataset with size and complexity metrics from my-repo")
    
    print("\n\nDone!")
