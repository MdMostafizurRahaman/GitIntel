#!/usr/bin/env python3
"""
Demo: Interactive Dataset Generator in Action
Shows the workflow without requiring user input
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interactive_dataset_generator import InteractiveDatasetGenerator

def demo_workflow():
    """Show demo of the interactive workflow"""
    
    print("\n" + "="*70)
    print(" DEMO: INTERACTIVE DATASET GENERATOR - FEEDBACK-DRIVEN WORKFLOW")
    print("="*70)
    
    print("\n[SCENARIO] User wants to create a Defects4J dataset")
    print("\nUser enters command:")
    print('  > "Create Defects4J dataset from spring-framework in JSON format"')
    
    # Simulate the workflow
    generator = InteractiveDatasetGenerator()
    
    # Manually set config to show the workflow
    print("\n" + "-"*70)
    print(" STEP 1: AI PARSES INPUT")
    print("-"*70)
    
    parsed = generator.parse_user_input("Create Defects4J dataset from spring-framework in JSON format")
    generator.config.update(parsed)
    
    print("\n✓ Detected components:")
    for key, value in parsed.items():
        print(f"   - {key}: {value}")
    
    print("\n" + "-"*70)
    print(" STEP 2: AI SHOWS UNDERSTANDING")
    print("-"*70)
    
    # Simulate clarification
    generator.config['repository'] = 'github.com/spring-projects/spring-framework'
    generator.config['repo_type'] = 'github'
    generator.config['dataset_type'] = 'benchmark'
    generator.config['benchmark_name'] = 'defects4j'
    generator.config['output_format'] = 'json'
    generator.config['output_name'] = 'defects4j_spring'
    
    generator.print_summary()
    
    print("\n" + "-"*70)
    print(" STEP 3: AI ASKS FOR CONFIRMATION")
    print("-"*70)
    
    print('\n? Is this correct?')
    print('  (yes/no/modify/cancel)')
    print('\n[User Input] > yes')
    
    print("\n" + "-"*70)
    print(" STEP 4: AI EXECUTES")
    print("-"*70)
    
    result = generator.execute_generation()
    
    print("\n" + "="*70)
    print(" RESULT: SUCCESS")
    print("="*70)
    print(f"\n✓ Dataset generation complete!")
    print(f"✓ Output: {result['output_path']}")
    
    # =========================================================================
    
    print("\n\n" + "="*70)
    print(" DEMO 2: WITH MODIFICATION REQUEST")
    print("="*70)
    
    print("\n[SCENARIO] User wants to modify the previous request")
    print("\nUser enters command:")
    print('  > "I want to add more metrics, use CSV instead, and name it my_bugs"')
    
    generator2 = InteractiveDatasetGenerator()
    generator2.config = {
        'repository': 'github.com/google/gson',
        'repo_type': 'github',
        'dataset_type': 'custom',
        'selected_metrics': ['size', 'complexity'],
        'output_format': 'csv',
        'output_name': 'my_bugs'
    }
    
    print("\n" + "-"*70)
    print(" SUMMARY BEFORE MODIFICATION")
    print("-"*70)
    generator2.print_summary()
    
    print("\n" + "-"*70)
    print(" USER FEEDBACK: MODIFICATION REQUEST")
    print("-"*70)
    print("\n[User] > modify")
    print("[AI] > What would you like to change?")
    print("  1. Change repository source")
    print("  2. Change dataset type/selection")
    print("  3. Change output format/name")
    print("  4. Start over with new configuration")
    print("\n[User] > 2")
    print("[AI] > Which metric categories? (select multiple)")
    print("  1. size: LOC, comments, blank lines")
    print("  2. complexity: Cyclomatic, nesting depth")
    print("  3. ck: OOP metrics (WMC, DIT, NOC, CBO, RFC, LCOM)")
    print("  4. coupling: Afferent, efferent coupling")
    print("  5. quality: Maintainability, comment ratio")
    print("  6. defect: Bug presence, severity")
    print("  7. structure: Classes, methods, fields")
    print("\n[User] > 1 2 3 5")
    
    # Update config to reflect modifications
    generator2.config['selected_metrics'] = ['size', 'complexity', 'ck', 'quality']
    
    print("\n✓ Added: CK, Quality metrics")
    print(f"✓ Total selected: {len(generator2.config['selected_metrics'])} categories")
    
    print("\n" + "-"*70)
    print(" SUMMARY AFTER MODIFICATION")
    print("-"*70)
    generator2.print_summary()
    
    print("\n[AI] > Is this correct now?")
    print("  (yes/no/modify/cancel)")
    print("\n[User] > yes")
    
    print("\n" + "-"*70)
    print(" EXECUTING WITH MODIFIED CONFIG")
    print("-"*70)
    
    result2 = generator2.execute_generation()
    
    # =========================================================================
    
    print("\n\n" + "="*70)
    print(" KEY FEATURES DEMONSTRATED")
    print("="*70)
    
    features = [
        ("Parse Input", "AI understands natural language commands"),
        ("Show Understanding", "AI displays what it understood"),
        ("Ask Confirmation", "AI asks 'Is this correct?'"),
        ("Handle Feedback", "AI responds to 'modify' requests"),
        ("Show Options", "AI presents choices for each aspect"),
        ("Iterate", "AI loops until user confirms"),
        ("Execute", "Once confirmed, AI executes the task"),
        ("Deliver", "AI shows results and completion")
    ]
    
    print()
    for i, (feature, description) in enumerate(features, 1):
        print(f"  {i}. {feature:<20} - {description}")
    
    print("\n" + "="*70)
    print(" WORKFLOW FLOW")
    print("="*70)
    
    workflow = """
    User Input
        ↓
    Parse → Extract components (repo, dataset, metrics, format, name)
        ↓
    Show Summary → Display what AI understood in readable format
        ↓
    Ask Confirmation → "Is this correct? (yes/no/modify)"
        ↓
        ├─ YES → EXECUTE → Show Progress → Deliver Results
        ├─ NO → Ask What to Change → Modify → Show New Summary → Loop
        └─ MODIFY → Show Options → User Selects → Update Config → Loop
    """
    
    print(workflow)
    
    print("\n" + "="*70)
    print(" WHEN TO USE THIS APPROACH")
    print("="*70)
    
    scenarios = [
        "✓ Complex configurations with many options",
        "✓ When users might not know exact requirements upfront",
        "✓ When you need to validate understanding before execution",
        "✓ For interactive tools where feedback improves results",
        "✓ When building AI agents that need to clarify intent",
        "✓ For any multi-step process requiring confirmation"
    ]
    
    print()
    for scenario in scenarios:
        print(f"  {scenario}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    demo_workflow()
    
    print("\n\n💡 TIP: This is the feedback-driven workflow you requested!")
    print("   Use it by calling: generator.run_interactive(user_input)")
    print("\n✅ Ready to use with your autonomous agent and GUI!\n")
