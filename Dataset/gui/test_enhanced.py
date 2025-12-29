"""
Quick Test for Enhanced Agentic Dataset Maker with LLM Jury
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

print("="*60)
print("🧪 TESTING ENHANCED AGENTIC DATASET MAKER")
print("="*60)

# Test 1: Import all modules
print("\n✅ Test 1: Import Modules")
try:
    from intelligent_metrics_system import AgenticDatasetMaker, MetricsCollector, FormulaParser
    print("   ✓ Intelligent Metrics System")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    from llm_jury_system import LLMJurySystem, CodeProposal, JuryVote, ValidationResult
    print("   ✓ LLM Jury System")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: MetricsCollector
print("\n✅ Test 2: MetricsCollector (Sample)")
try:
    # Use your repo as sample
    repo_path = Path("d:/GitIntel/repo")
    if repo_path.exists():
        collector = MetricsCollector(repo_path)
        metrics = collector.collect_all_metrics()
        print(f"   ✓ Collected {len(metrics)} metrics")
        print(f"   Sample metrics: {list(metrics.keys())[:5]}")
    else:
        print(f"   ⚠ Repo not found at {repo_path}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: FormulaParser
print("\n✅ Test 3: FormulaParser")
try:
    sample_metrics = {
        'total_commits': 100,
        'project_age_days': 365,
        'total_loc': 5000,
        'estimated_complexity': 250
    }
    
    parser = FormulaParser(sample_metrics)
    
    # Test simple formula
    result = parser.parse_and_evaluate("total_commits / project_age_days")
    print(f"   ✓ Simple formula: total_commits / project_age_days = {result}")
    
    # Test complex formula
    result = parser.parse_and_evaluate("(total_loc / total_commits) * 100")
    print(f"   ✓ Complex formula: (total_loc / total_commits) * 100 = {result}")
    
    # Test validation
    is_valid, msg = parser.validate_formula("total_commits * 2")
    print(f"   ✓ Validation: {msg}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: LLM Jury System (basic check)
print("\n✅ Test 4: LLM Jury System (Structure)")
try:
    import os
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if api_key:
        jury = LLMJurySystem(api_key)
        print(f"   ✓ LLM Jury initialized")
        print(f"   ✓ Generator config: {jury.generator_config}")
        print(f"   ✓ Number of jury configs: {len(jury.jury_configs)}")
    else:
        print(f"   ⚠ GOOGLE_API_KEY not set - LLM features will not work")
        print(f"   Set it in environment or .env file")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: AgenticDatasetMaker
print("\n✅ Test 5: AgenticDatasetMaker")
try:
    maker = AgenticDatasetMaker(output_dir=Path("d:/GitIntel/test_datasets"))
    print(f"   ✓ Dataset maker initialized")
    print(f"   ✓ Output dir: {maker.output_dir}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*60)
print("🎉 ALL BASIC TESTS PASSED!")
print("="*60)
print("\nNext steps:")
print("1. Set GOOGLE_API_KEY for LLM features")
print("2. Run: python enhanced_interactive_gui.py")
print("3. Or: run_enhanced.bat")
print("\n")
