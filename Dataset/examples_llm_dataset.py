"""
Example Usage of LLM-Driven Dataset Generator
Demonstrates various scenarios and use cases
"""

from llm_driven_dataset_generator import LLMDrivenDatasetGenerator
import pandas as pd
import os
from pathlib import Path


def example_1_simple_defect_density():
    """Example 1: Simple Defect Density Calculation"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Defect Density")
    print("="*80)
    
    # Sample data
    data = {
        'project': ['ProjectA', 'ProjectB', 'ProjectC', 'ProjectD', 'ProjectE'],
        'KLOC': [10.5, 25.3, 15.7, 8.2, 42.1],
        'bugs_count': [5, 12, 8, 3, 20]
    }
    
    df = pd.DataFrame(data)
    
    # Calculate defect density
    df['defect_density'] = df['bugs_count'] / df['KLOC']
    
    print("\nInput Data:")
    print(df[['project', 'KLOC', 'bugs_count']])
    print("\nResult:")
    print(df[['project', 'defect_density']])
    
    return df


def example_2_complex_quality_score():
    """Example 2: Complex Quality Score with Multiple Factors"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Complex Quality Score")
    print("="*80)
    
    # Sample data
    data = {
        'project': ['App1', 'App2', 'App3', 'App4', 'App5'],
        'test_coverage': [85.5, 92.3, 78.1, 88.7, 95.2],
        'bugs_count': [12, 5, 18, 8, 3],
        'KLOC': [25.5, 18.2, 35.7, 22.1, 15.8],
        'cyclomatic_complexity': [45, 32, 68, 38, 28]
    }
    
    df = pd.DataFrame(data)
    
    # Complex quality score calculation
    # Weighted formula: 40% test coverage, 30% defect density (inverted), 30% complexity (inverted)
    df['quality_score'] = (
        (df['test_coverage'] / 100 * 0.4) + 
        ((1 - df['bugs_count'] / df['KLOC'] / 10) * 0.3).clip(0, 1) +  # Normalize defect density
        ((100 - df['cyclomatic_complexity']) / 100 * 0.3).clip(0, 1)   # Normalize complexity
    ) * 100
    
    print("\nInput Data:")
    print(df[['project', 'test_coverage', 'bugs_count', 'KLOC', 'cyclomatic_complexity']])
    print("\nResult:")
    print(df[['project', 'quality_score']])
    
    return df


def example_3_maintainability_index():
    """Example 3: Maintainability Index (Microsoft Formula)"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Maintainability Index")
    print("="*80)
    
    import numpy as np
    
    # Sample data
    data = {
        'module': ['ModuleA', 'ModuleB', 'ModuleC', 'ModuleD'],
        'volume': [1500, 2800, 1200, 3500],  # Halstead volume
        'cyclomatic_complexity': [25, 45, 18, 52],
        'LOC': [450, 820, 380, 950]
    }
    
    df = pd.DataFrame(data)
    
    # Maintainability Index formula
    # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)
    # where V = Halstead Volume, G = Cyclomatic Complexity
    df['maintainability_index'] = (
        171 - 
        5.2 * np.log(df['volume']) - 
        0.23 * df['cyclomatic_complexity'] - 
        16.2 * np.log(df['LOC'])
    )
    
    # Normalize to 0-100 scale
    df['maintainability_index'] = df['maintainability_index'].clip(0, 100)
    
    print("\nInput Data:")
    print(df[['module', 'volume', 'cyclomatic_complexity', 'LOC']])
    print("\nResult:")
    print(df[['module', 'maintainability_index']])
    print("\nInterpretation:")
    print("  > 85: High maintainability")
    print("  65-85: Moderate maintainability")
    print("  < 65: Low maintainability")
    
    return df


def example_4_risk_assessment():
    """Example 4: Risk Assessment Score"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Risk Assessment Score")
    print("="*80)
    
    # Sample data
    data = {
        'component': ['Auth', 'Payment', 'API', 'UI', 'Database'],
        'bugs_count': [8, 15, 5, 3, 12],
        'change_frequency': [45, 82, 38, 22, 55],  # commits in last 3 months
        'complexity': [35, 68, 28, 15, 52],
        'test_coverage': [78, 65, 88, 92, 71]
    }
    
    df = pd.DataFrame(data)
    
    # Risk score calculation
    # Higher risk = more bugs, more changes, higher complexity, lower coverage
    df['risk_score'] = (
        (df['bugs_count'] / df['bugs_count'].max() * 0.3) +
        (df['change_frequency'] / df['change_frequency'].max() * 0.2) +
        (df['complexity'] / df['complexity'].max() * 0.3) +
        ((100 - df['test_coverage']) / 100 * 0.2)
    ) * 100
    
    print("\nInput Data:")
    print(df)
    print("\nResult:")
    print(df[['component', 'risk_score']].sort_values('risk_score', ascending=False))
    
    return df


def example_5_technical_debt():
    """Example 5: Technical Debt Estimation"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Technical Debt Estimation")
    print("="*80)
    
    # Sample data
    data = {
        'file': ['Service.java', 'Controller.java', 'Utils.java', 'Model.java'],
        'code_smells': [12, 8, 5, 3],
        'duplications': [15, 8, 3, 2],  # percentage
        'complexity': [45, 32, 28, 18],
        'LOC': [850, 620, 450, 280]
    }
    
    df = pd.DataFrame(data)
    
    # Technical debt calculation (in hours to fix)
    # Assumption: each code smell = 30min, each % duplication = 1hr per 100 LOC, complexity adds time
    df['debt_hours'] = (
        (df['code_smells'] * 0.5) +  # 30 minutes per code smell
        (df['duplications'] / 100 * df['LOC'] / 100) +  # duplication penalty
        (df['complexity'] / 10)  # complexity penalty
    )
    
    print("\nInput Data:")
    print(df)
    print("\nResult:")
    print(df[['file', 'debt_hours']].sort_values('debt_hours', ascending=False))
    print(f"\nTotal Technical Debt: {df['debt_hours'].sum():.2f} hours")
    print(f"Average per file: {df['debt_hours'].mean():.2f} hours")
    
    return df


def save_example_results():
    """Save all example results to files"""
    output_dir = Path("generated_datasets/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    examples = {
        'defect_density': example_1_simple_defect_density(),
        'quality_score': example_2_complex_quality_score(),
        'maintainability_index': example_3_maintainability_index(),
        'risk_assessment': example_4_risk_assessment(),
        'technical_debt': example_5_technical_debt()
    }
    
    for name, df in examples.items():
        csv_path = output_dir / f"{name}_example.csv"
        json_path = output_dir / f"{name}_example.json"
        
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=2)
        
        print(f"\n💾 Saved: {csv_path}")


def demonstrate_interactive_workflow():
    """Show how the interactive workflow would look"""
    print("\n" + "="*80)
    print("INTERACTIVE WORKFLOW DEMONSTRATION")
    print("="*80)
    
    print("""
SCENARIO: User wants to calculate a custom metric

User Input:
-----------
Available metrics: KLOC, bugs_count, test_coverage, complexity
Target formula: "Code Health = (test_coverage/100 * 0.5) + (1 - bugs_count/KLOC/10) * 0.3 + (1 - complexity/100) * 0.2"

LLM Analysis:
-------------
✅ All metrics are available
✅ Formula is feasible
📝 Breakdown:
   - test_coverage: 50% weight, normalized to 0-1
   - defect density: 30% weight, inverted and normalized
   - complexity: 20% weight, inverted and normalized

💡 Recommendations:
   - Add boundary checks for division by zero
   - Ensure complexity is on 0-100 scale
   - Consider capping defect density at reasonable max

Final Formula:
--------------
code_health = (
    (test_coverage / 100 * 0.5) + 
    ((1 - (bugs_count / (KLOC if KLOC > 0 else 1)) / 10).clip(0, 1) * 0.3) +
    ((1 - complexity / 100).clip(0, 1) * 0.2)
) * 100

Result:
-------
[Dataset generated with code_health values 0-100]
    """)


def main():
    """Run all examples"""
    print("\n" + "🎯 " * 30)
    print("LLM-DRIVEN DATASET GENERATOR - EXAMPLES")
    print("🎯 " * 30)
    
    # Run individual examples
    example_1_simple_defect_density()
    input("\nPress Enter to continue to next example...")
    
    example_2_complex_quality_score()
    input("\nPress Enter to continue to next example...")
    
    example_3_maintainability_index()
    input("\nPress Enter to continue to next example...")
    
    example_4_risk_assessment()
    input("\nPress Enter to continue to next example...")
    
    example_5_technical_debt()
    input("\nPress Enter to continue...")
    
    demonstrate_interactive_workflow()
    
    # Ask if user wants to save
    print("\n" + "="*80)
    save = input("\nWould you like to save these example results? (yes/no): ").strip().lower()
    if save == 'yes':
        save_example_results()
        print("\n✅ All examples saved!")
    
    print("\n" + "="*80)
    print("✨ Examples complete!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Run: python llm_driven_dataset_generator.py")
    print("  2. Try your own metrics and formulas")
    print("  3. Let the AI guide you through the process")
    print("\nHappy dataset generation! 🚀")


if __name__ == "__main__":
    main()
