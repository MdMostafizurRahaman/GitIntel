"""
LLM-Driven Dataset Generator
Fully flexible, user-driven dataset generation with Gemini AI intelligence
No hardcoded formulas - Complete customization based on user needs
"""

import os
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMDrivenDatasetGenerator:
    """
    Intelligent dataset generator that uses LLM to understand user requirements
    and generate custom datasets with flexible formulas
    """

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        # Use the latest Gemini model
        try:
            self.model = genai.GenerativeModel('gemini-flash-latest')
        except:
            # Fallback to other available models
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except:
                self.model = genai.GenerativeModel('models/gemini-pro')
        
        self.output_dir = Path("generated_datasets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.available_metrics = []
        self.target_formula = None
        self.formula_components = {}
        self.dataset_config = {}
        
    def start_interactive_session(self):
        """Start interactive session with user"""
        print("\n" + "="*80)
        print("🤖 LLM-Driven Dataset Generator")
        print("="*80)
        print("\nWelcome! I'll help you create a custom dataset based on YOUR metrics.")
        print("This is a fully flexible system - no hardcoded formulas!")
        print("\n" + "="*80 + "\n")
        
        # Phase 1: User Input
        self._collect_user_input()
        
        # Phase 2: LLM Intelligence
        self._llm_analysis_phase()
        
        # Phase 3: Dataset Generation
        self._generate_dataset()
        
    def _collect_user_input(self):
        """Phase 1: Collect information about available metrics and desired formula"""
        print("\n📊 PHASE 1: User Input")
        print("-" * 80)
        
        # Collect available metrics
        print("\n1️⃣ What metrics do you have available in your data?")
        print("   Examples: KLOC, bugs_count, test_coverage, cyclomatic_complexity, etc.")
        print("   (Enter metrics separated by commas, or 'help' for examples)\n")
        
        metrics_input = input("Your available metrics: ").strip()
        
        if metrics_input.lower() == 'help':
            self._show_metric_examples()
            metrics_input = input("Your available metrics: ").strip()
        
        self.available_metrics = [m.strip() for m in metrics_input.split(',') if m.strip()]
        
        print(f"\n✅ Recorded {len(self.available_metrics)} metrics: {', '.join(self.available_metrics)}")
        
        # Collect target formula
        print("\n2️⃣ What metric/formula do you want to calculate?")
        print("   Examples:")
        print("   - 'Defect Density = Bugs / KLOC'")
        print("   - 'Code Quality Score = (test_coverage * 0.4) + (1 - (bugs_count / KLOC)) * 0.6'")
        print("   - 'Maintainability Index = 171 - 5.2 * ln(volume) - 0.23 * complexity'")
        print("   (Be as detailed or simple as you want!)\n")
        
        self.target_formula = input("Your desired formula: ").strip()
        
        print(f"\n✅ Target formula: {self.target_formula}")
        
    def _show_metric_examples(self):
        """Show examples of common metrics"""
        print("\n📚 Common Software Metrics Examples:")
        print("-" * 80)
        examples = {
            "Size Metrics": ["KLOC", "LOC", "NCLOC", "file_count", "class_count"],
            "Quality Metrics": ["bugs_count", "vulnerabilities", "code_smells", "technical_debt"],
            "Testing Metrics": ["test_coverage", "test_count", "assertion_count", "test_success_rate"],
            "Complexity Metrics": ["cyclomatic_complexity", "cognitive_complexity", "npath_complexity"],
            "OOP Metrics": ["CBO", "WMC", "DIT", "NOC", "RFC", "LCOM"],
            "Change Metrics": ["commit_count", "author_count", "churn", "change_frequency"]
        }
        
        for category, metrics in examples.items():
            print(f"\n{category}:")
            print(f"  {', '.join(metrics)}")
        print("\n" + "-" * 80 + "\n")
        
    def _llm_analysis_phase(self):
        """Phase 2: Use LLM to analyze requirements and provide guidance"""
        print("\n🧠 PHASE 2: LLM Intelligence Analysis")
        print("-" * 80)
        print("\nAnalyzing your requirements with AI...\n")
        
        # Create analysis prompt
        analysis_prompt = self._create_analysis_prompt()
        
        try:
            response = self.model.generate_content(analysis_prompt)
            analysis_result = response.text
            
            print("🤖 AI Analysis:\n")
            print(analysis_result)
            print("\n" + "-" * 80)
            
            # Parse LLM response
            self._parse_llm_analysis(analysis_result)
            
            # Feedback loop
            self._feedback_loop()
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            print(f"\n❌ Error: {e}")
            print("Falling back to manual configuration...")
            self._manual_configuration()
    
    def _create_analysis_prompt(self) -> str:
        """Create comprehensive prompt for LLM analysis"""
        prompt = f"""
You are an expert data scientist and software metrics analyst. A user wants to create a custom dataset.

**Available Metrics:**
{', '.join(self.available_metrics)}

**Desired Formula/Metric:**
{self.target_formula}

**Your Task:**
Analyze the user's requirements and provide a detailed response in the following format:

1. FEASIBILITY ASSESSMENT:
   - Can this formula be calculated with the available metrics? (YES/NO)
   - List which metrics from the formula ARE available
   - List which metrics from the formula are MISSING (if any)

2. MISSING METRICS GUIDANCE:
   - For each missing metric, explain HOW it can be calculated from other available metrics
   - Provide specific formulas or calculation methods
   - If a metric CANNOT be derived, suggest alternatives

3. CALCULATION PLAN:
   - Step-by-step plan to calculate the target formula
   - Include any intermediate calculations needed
   - Specify the exact formula to use with available metrics

4. CLARIFYING QUESTIONS:
   - List any ambiguities or assumptions you're making
   - Ask specific questions to better understand the user's intent
   - Suggest improvements or alternative formulas if applicable

5. FINAL FORMULA:
   - Provide the complete, executable formula using only available metrics
   - Use Python syntax (e.g., metric_name, /, *, +, -, **, etc.)
   - Example: "defect_density = bugs_count / (KLOC if KLOC > 0 else 1)"

Be thorough, specific, and helpful. If something is unclear, ask questions.
"""
        return prompt
    
    def _parse_llm_analysis(self, analysis_text: str):
        """Parse LLM response and extract key information"""
        # Extract feasibility
        if "YES" in analysis_text.upper() and "CAN THIS FORMULA BE CALCULATED" in analysis_text.upper():
            self.dataset_config['feasible'] = True
        else:
            self.dataset_config['feasible'] = False
        
        # Try to extract final formula from response
        final_formula_match = re.search(
            r'(?:FINAL FORMULA|Final Formula).*?[:\n]\s*(?:```python\s*)?(.*?)(?:```)?(?=\n\n|\n[A-Z]|$)',
            analysis_text,
            re.DOTALL | re.IGNORECASE
        )
        
        if final_formula_match:
            formula = final_formula_match.group(1).strip()
            # Clean up formula
            formula = formula.replace('```', '').replace('python', '').strip()
            if formula:
                self.dataset_config['computed_formula'] = formula
                logger.info(f"Extracted formula: {formula}")
    
    def _feedback_loop(self):
        """Interactive feedback loop for clarification"""
        print("\n💬 FEEDBACK LOOP")
        print("-" * 80)
        
        while True:
            print("\nOptions:")
            print("  1. I'm satisfied - proceed to dataset generation")
            print("  2. I have a question or need clarification")
            print("  3. I want to modify the formula")
            print("  4. Show me the analysis again")
            print("  5. Exit")
            
            choice = input("\nYour choice (1-5): ").strip()
            
            if choice == '1':
                print("\n✅ Great! Proceeding to dataset generation...")
                break
            elif choice == '2':
                self._handle_clarification()
            elif choice == '3':
                self._modify_formula()
            elif choice == '4':
                print("\n" + "="*80)
                print("Previous Analysis:")
                print("="*80)
                # Re-run analysis if needed
                self._llm_analysis_phase()
            elif choice == '5':
                print("\n👋 Exiting...")
                exit(0)
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    def _handle_clarification(self):
        """Handle user questions and provide clarification"""
        print("\n❓ What would you like to know?")
        user_question = input("Your question: ").strip()
        
        if not user_question:
            return
        
        # Create clarification prompt
        clarification_prompt = f"""
Previous context:
- Available metrics: {', '.join(self.available_metrics)}
- Target formula: {self.target_formula}

User's question: {user_question}

Provide a clear, concise answer to help the user understand how to proceed.
"""
        
        try:
            response = self.model.generate_content(clarification_prompt)
            print("\n🤖 AI Response:\n")
            print(response.text)
            print("\n" + "-" * 80)
        except Exception as e:
            logger.error(f"Error during clarification: {e}")
            print(f"❌ Error: {e}")
    
    def _modify_formula(self):
        """Allow user to modify the formula"""
        print("\n✏️  Current formula:", self.target_formula)
        new_formula = input("Enter new formula (or press Enter to keep current): ").strip()
        
        if new_formula:
            self.target_formula = new_formula
            print("✅ Formula updated!")
            print("Re-analyzing with new formula...\n")
            self._llm_analysis_phase()
    
    def _manual_configuration(self):
        """Fallback manual configuration if LLM fails"""
        print("\n⚙️  Manual Configuration Mode")
        print("-" * 80)
        
        print("\nPlease provide the formula using Python syntax.")
        print("Example: bugs_count / KLOC")
        
        formula = input("\nFormula: ").strip()
        self.dataset_config['computed_formula'] = formula
        self.dataset_config['feasible'] = True
    
    def _generate_dataset(self):
        """Phase 3: Generate the actual dataset"""
        print("\n📂 PHASE 3: Dataset Generation")
        print("-" * 80)
        
        if not self.dataset_config.get('feasible', False):
            print("\n⚠️  Warning: Formula feasibility not confirmed.")
            proceed = input("Do you want to proceed anyway? (yes/no): ").strip().lower()
            if proceed != 'yes':
                print("❌ Dataset generation cancelled.")
                return
        
        # Get data source
        print("\n1️⃣ Where is your data?")
        print("   1. CSV file")
        print("   2. JSON file")
        print("   3. Manual entry (for testing)")
        print("   4. Sample data (I'll generate example data)")
        
        source_choice = input("\nYour choice (1-4): ").strip()
        
        if source_choice == '1':
            self._generate_from_csv()
        elif source_choice == '2':
            self._generate_from_json()
        elif source_choice == '3':
            self._generate_from_manual_entry()
        elif source_choice == '4':
            self._generate_sample_dataset()
        else:
            print("❌ Invalid choice.")
            return
    
    def _generate_from_csv(self):
        """Generate dataset from CSV file"""
        file_path = input("\nEnter CSV file path: ").strip()
        
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            print(f"\n✅ Loaded {len(df)} records")
            print(f"Columns: {', '.join(df.columns)}")
            
            # Apply formula
            self._apply_formula_to_dataframe(df)
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            print(f"❌ Error: {e}")
    
    def _generate_from_json(self):
        """Generate dataset from JSON file"""
        file_path = input("\nEnter JSON file path: ").strip()
        
        try:
            import pandas as pd
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("Unsupported JSON structure")
            
            print(f"\n✅ Loaded {len(df)} records")
            print(f"Columns: {', '.join(df.columns)}")
            
            # Apply formula
            self._apply_formula_to_dataframe(df)
            
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            print(f"❌ Error: {e}")
    
    def _generate_from_manual_entry(self):
        """Generate dataset from manual entry"""
        print("\n✏️  Manual Data Entry")
        print("-" * 80)
        
        num_records = int(input("How many records do you want to enter? "))
        
        records = []
        for i in range(num_records):
            print(f"\n📝 Record {i+1}:")
            record = {}
            for metric in self.available_metrics:
                value = input(f"  {metric}: ").strip()
                try:
                    record[metric] = float(value) if '.' in value else int(value)
                except:
                    record[metric] = value
            records.append(record)
        
        import pandas as pd
        df = pd.DataFrame(records)
        
        # Apply formula
        self._apply_formula_to_dataframe(df)
    
    def _generate_sample_dataset(self):
        """Generate sample dataset for testing"""
        print("\n🎲 Generating sample data...")
        
        import pandas as pd
        import random
        
        num_samples = int(input("How many sample records? (default: 10): ").strip() or "10")
        
        # Generate random sample data
        data = {}
        for metric in self.available_metrics:
            # Generate appropriate random data based on metric name
            if 'kloc' in metric.lower() or 'loc' in metric.lower():
                data[metric] = [random.uniform(1, 100) for _ in range(num_samples)]
            elif 'bug' in metric.lower() or 'defect' in metric.lower():
                data[metric] = [random.randint(0, 50) for _ in range(num_samples)]
            elif 'coverage' in metric.lower() or 'percent' in metric.lower():
                data[metric] = [random.uniform(0, 100) for _ in range(num_samples)]
            elif 'complexity' in metric.lower():
                data[metric] = [random.randint(1, 100) for _ in range(num_samples)]
            else:
                data[metric] = [random.uniform(1, 100) for _ in range(num_samples)]
        
        df = pd.DataFrame(data)
        
        print(f"\n✅ Generated {len(df)} sample records")
        print("\nSample preview:")
        print(df.head())
        
        # Apply formula
        self._apply_formula_to_dataframe(df)
    
    def _apply_formula_to_dataframe(self, df):
        """Apply the computed formula to dataframe"""
        print("\n🔢 Applying formula...")
        
        formula = self.dataset_config.get('computed_formula', '')
        
        if not formula:
            print("❌ No formula available. Using manual formula entry...")
            formula = input("Enter formula to apply: ").strip()
        
        print(f"Formula: {formula}")
        
        try:
            # Create a safe namespace for eval
            namespace = df.to_dict('list')
            
            # Convert lists to allow element-wise operations
            import pandas as pd
            for key in namespace:
                namespace[key] = pd.Series(namespace[key])
            
            # Add common functions
            import numpy as np
            namespace['np'] = np
            namespace['log'] = np.log
            namespace['ln'] = np.log
            namespace['sqrt'] = np.sqrt
            namespace['abs'] = np.abs
            namespace['max'] = np.maximum
            namespace['min'] = np.minimum
            
            # Extract the metric name from formula (left side of =)
            if '=' in formula:
                parts = formula.split('=')
                result_name = parts[0].strip()
                formula_expr = parts[1].strip()
            else:
                result_name = "calculated_metric"
                formula_expr = formula
            
            # Evaluate formula
            result = eval(formula_expr, {"__builtins__": {}}, namespace)
            
            # Add result to dataframe
            df[result_name] = result
            
            print(f"\n✅ Successfully calculated '{result_name}'")
            print("\nResult preview:")
            print(df.head(10))
            
            # Save dataset
            self._save_dataset(df, result_name)
            
        except Exception as e:
            logger.error(f"Error applying formula: {e}")
            print(f"\n❌ Error applying formula: {e}")
            print("\nThis could be due to:")
            print("  - Missing metrics in the data")
            print("  - Syntax errors in the formula")
            print("  - Division by zero")
            print("\nPlease check your formula and data.")
    
    def _save_dataset(self, df, metric_name: str):
        """Save the generated dataset"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV output
        csv_path = self.output_dir / f"custom_dataset_{metric_name}_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n💾 Saved CSV: {csv_path}")
        
        # JSON output
        json_path = self.output_dir / f"custom_dataset_{metric_name}_{timestamp}.json"
        df.to_json(json_path, orient='records', indent=2)
        print(f"💾 Saved JSON: {json_path}")
        
        # Summary statistics
        print("\n📊 Dataset Statistics:")
        print(df.describe())
        
        # Generate metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "metric_name": metric_name,
            "formula": self.target_formula,
            "computed_formula": self.dataset_config.get('computed_formula', ''),
            "available_metrics": self.available_metrics,
            "num_records": len(df),
            "columns": list(df.columns),
            "output_files": {
                "csv": str(csv_path),
                "json": str(json_path)
            }
        }
        
        metadata_path = self.output_dir / f"custom_dataset_{metric_name}_{timestamp}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📄 Saved metadata: {metadata_path}")
        
        print("\n" + "="*80)
        print("✅ DATASET GENERATION COMPLETE!")
        print("="*80)


def main():
    """Main entry point"""
    try:
        generator = LLMDrivenDatasetGenerator()
        generator.start_interactive_session()
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted by user. Goodbye!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
