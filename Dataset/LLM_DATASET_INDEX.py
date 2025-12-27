"""
LLM-Driven Dataset Generator - Complete Index
Navigate all features and functionality
"""

# ============================================================================
# 🎯 MAIN FEATURES
# ============================================================================

MAIN_SCRIPTS = {
    "llm_driven_dataset_generator.py": {
        "description": "Main interactive dataset generator with AI guidance",
        "usage": "python llm_driven_dataset_generator.py",
        "features": [
            "User-driven metric input",
            "AI-powered formula analysis",
            "Interactive feedback loop",
            "Multiple data source support",
            "Custom formula generation"
        ]
    },
    
    "examples_llm_dataset.py": {
        "description": "Complete examples and demonstrations",
        "usage": "python examples_llm_dataset.py",
        "includes": [
            "Defect Density calculation",
            "Quality Score (complex weighted)",
            "Maintainability Index",
            "Risk Assessment",
            "Technical Debt estimation"
        ]
    },
    
    "test_llm_setup.py": {
        "description": "Setup verification and testing",
        "usage": "python test_llm_setup.py",
        "checks": [
            "Python version",
            "Required packages",
            "Environment variables",
            "Gemini API connection",
            "Formula evaluation"
        ]
    }
}


# ============================================================================
# 📚 DOCUMENTATION
# ============================================================================

DOCUMENTATION = {
    "README_LLM_DATASET.md": "Quick start guide and overview",
    "LLM_DATASET_GUIDE.md": "Complete detailed documentation",
    "requirements.txt": "Python package dependencies"
}


# ============================================================================
# 🚀 QUICK START WORKFLOW
# ============================================================================

def quick_start_guide():
    """Display quick start workflow"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║        LLM-DRIVEN DATASET GENERATOR - QUICK START              ║
    ╚════════════════════════════════════════════════════════════════╝
    
    STEP 1: Install Dependencies
    ─────────────────────────────────────────────────────────────────
    cd d:\\GitIntel\\GitIntelProject\\Dataset
    pip install -r requirements.txt
    
    STEP 2: Configure API Key
    ─────────────────────────────────────────────────────────────────
    Create .env file with:
        GEMINI_API_KEY=your_api_key_here
    
    STEP 3: Verify Setup
    ─────────────────────────────────────────────────────────────────
    python test_llm_setup.py
    
    STEP 4: Run Examples (Optional)
    ─────────────────────────────────────────────────────────────────
    python examples_llm_dataset.py
    
    STEP 5: Generate Your Dataset
    ─────────────────────────────────────────────────────────────────
    python llm_driven_dataset_generator.py
    
    OR use the batch file:
    ─────────────────────────────────────────────────────────────────
    run_llm_dataset.bat
    """)


# ============================================================================
# 💡 USAGE PATTERNS
# ============================================================================

USAGE_PATTERNS = {
    "Simple Metric": {
        "scenario": "Calculate defect density",
        "metrics": ["KLOC", "bugs_count"],
        "formula": "defect_density = bugs_count / KLOC",
        "complexity": "Low"
    },
    
    "Weighted Score": {
        "scenario": "Calculate quality score from multiple factors",
        "metrics": ["test_coverage", "bugs_count", "KLOC", "complexity"],
        "formula": "quality = (test_coverage/100 * 0.4) + ((1 - bugs_count/KLOC) * 0.3) + ((100 - complexity)/100 * 0.3)",
        "complexity": "Medium"
    },
    
    "Mathematical Formula": {
        "scenario": "Calculate Maintainability Index",
        "metrics": ["volume", "complexity", "LOC"],
        "formula": "MI = 171 - 5.2*ln(volume) - 0.23*complexity - 16.2*ln(LOC)",
        "complexity": "High"
    },
    
    "Risk Assessment": {
        "scenario": "Combine multiple risk factors",
        "metrics": ["bugs_count", "change_frequency", "complexity", "test_coverage"],
        "formula": "risk = (bugs/max_bugs * 0.3) + (changes/max_changes * 0.2) + (complexity/max_complexity * 0.3) + ((100-coverage)/100 * 0.2)",
        "complexity": "High"
    }
}


# ============================================================================
# 🎓 EXAMPLE FORMULAS
# ============================================================================

EXAMPLE_FORMULAS = {
    "Basic Arithmetic": [
        "defect_density = bugs_count / KLOC",
        "code_churn = lines_added + lines_deleted",
        "test_ratio = test_count / class_count"
    ],
    
    "Normalization": [
        "normalized_coverage = test_coverage / 100",
        "scaled_complexity = (complexity - min) / (max - min)",
        "percentage = (value / total) * 100"
    ],
    
    "Weighted Combinations": [
        "quality = (metric1 * 0.4) + (metric2 * 0.3) + (metric3 * 0.3)",
        "score = (coverage * w1) + (complexity * w2) + (bugs * w3)",
        "health = sum(metrics[i] * weights[i])"
    ],
    
    "Conditional Logic": [
        "risk = high_risk if bugs > 10 else low_risk",
        "category = 'good' if score > 80 else 'poor'",
        "adjusted = value * (1.5 if priority == 'high' else 1.0)"
    ],
    
    "Mathematical Functions": [
        "entropy = -sum(p * log(p))",
        "distance = sqrt((x2-x1)**2 + (y2-y1)**2)",
        "mi = 171 - 5.2*ln(volume) - 0.23*G - 16.2*ln(LOC)"
    ]
}


# ============================================================================
# 🔧 SUPPORTED OPERATIONS
# ============================================================================

SUPPORTED_OPERATIONS = {
    "Arithmetic": {
        "operators": ["+", "-", "*", "/", "**", "//", "%"],
        "description": "Basic mathematical operations"
    },
    
    "Comparison": {
        "operators": [">", "<", ">=", "<=", "==", "!="],
        "description": "Comparison and equality checks"
    },
    
    "Logical": {
        "operators": ["and", "or", "not"],
        "description": "Boolean logic operations"
    },
    
    "Mathematical Functions": {
        "functions": ["log", "ln", "sqrt", "abs", "max", "min", "round"],
        "description": "Common mathematical functions"
    },
    
    "Pandas Operations": {
        "methods": ["clip", "fillna", "replace", "apply"],
        "description": "DataFrame operations for data manipulation"
    }
}


# ============================================================================
# 📊 OUTPUT FORMATS
# ============================================================================

OUTPUT_FORMATS = {
    "CSV": {
        "extension": ".csv",
        "description": "Comma-separated values, universal compatibility",
        "use_case": "Excel, data analysis tools, database import"
    },
    
    "JSON": {
        "extension": ".json",
        "description": "JavaScript Object Notation, structured data",
        "use_case": "APIs, web applications, NoSQL databases"
    },
    
    "Metadata": {
        "extension": "_metadata.json",
        "description": "Configuration and statistics about the dataset",
        "use_case": "Tracking provenance, reproducibility"
    }
}


# ============================================================================
# 🎯 WORKFLOW PHASES
# ============================================================================

WORKFLOW_PHASES = {
    "Phase 1: User Input": {
        "purpose": "Collect user requirements",
        "inputs": [
            "Available metrics list",
            "Target formula/metric definition"
        ],
        "outputs": [
            "Validated metric list",
            "Formula string"
        ]
    },
    
    "Phase 2: LLM Intelligence": {
        "purpose": "Analyze and provide guidance",
        "steps": [
            "Feasibility assessment",
            "Missing metrics identification",
            "Calculation plan generation",
            "Clarifying questions",
            "Final formula generation"
        ],
        "ai_features": [
            "Natural language understanding",
            "Formula validation",
            "Alternative suggestions",
            "Interactive feedback"
        ]
    },
    
    "Phase 3: Dataset Generation": {
        "purpose": "Generate the actual dataset",
        "data_sources": [
            "CSV file import",
            "JSON file import",
            "Manual entry",
            "Sample data generation"
        ],
        "processing": [
            "Formula application",
            "Error handling",
            "Result validation",
            "Output generation"
        ]
    }
}


# ============================================================================
# 🛠️ TROUBLESHOOTING
# ============================================================================

TROUBLESHOOTING = {
    "API Key Issues": {
        "symptom": "GEMINI_API_KEY not found",
        "solutions": [
            "Create .env file in Dataset folder",
            "Add line: GEMINI_API_KEY=your_key",
            "Restart terminal/IDE"
        ]
    },
    
    "Formula Errors": {
        "symptom": "Error applying formula",
        "solutions": [
            "Check metric names match data exactly",
            "Add division by zero protection",
            "Verify parentheses balance",
            "Test with sample data first"
        ]
    },
    
    "Missing Dependencies": {
        "symptom": "ModuleNotFoundError",
        "solutions": [
            "Run: pip install -r requirements.txt",
            "Check Python version (3.7+)",
            "Use virtual environment"
        ]
    },
    
    "Data Import Issues": {
        "symptom": "Error loading CSV/JSON",
        "solutions": [
            "Verify file path is correct",
            "Check file format is valid",
            "Ensure column names match metrics",
            "Try sample data first"
        ]
    }
}


# ============================================================================
# 📈 BEST PRACTICES
# ============================================================================

BEST_PRACTICES = {
    "Metric Naming": [
        "Use descriptive names: 'bugs_count' not 'bc'",
        "Be consistent with casing",
        "Avoid special characters except underscore",
        "Match data column names exactly"
    ],
    
    "Formula Design": [
        "Start simple, add complexity gradually",
        "Add division by zero protection",
        "Normalize different scale metrics",
        "Document weights and rationale",
        "Test with sample data first"
    ],
    
    "Data Quality": [
        "Validate input data ranges",
        "Handle missing values appropriately",
        "Check for outliers",
        "Document data sources",
        "Keep metadata with datasets"
    ],
    
    "Workflow": [
        "Use test_llm_setup.py before starting",
        "Try examples first to understand system",
        "Start with sample data for new formulas",
        "Save intermediate results",
        "Keep formula documentation"
    ]
}


# ============================================================================
# 🎪 MAIN FUNCTION
# ============================================================================

def main():
    """Display complete index and navigation"""
    import json
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "LLM-DRIVEN DATASET GENERATOR INDEX" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    # Show quick start
    quick_start_guide()
    
    # Show main features
    print("\n" + "="*80)
    print("📂 MAIN SCRIPTS")
    print("="*80)
    for script, info in MAIN_SCRIPTS.items():
        print(f"\n📄 {script}")
        print(f"   {info['description']}")
        print(f"   Usage: {info['usage']}")
    
    # Show usage patterns
    print("\n" + "="*80)
    print("💡 USAGE PATTERNS")
    print("="*80)
    for pattern, info in USAGE_PATTERNS.items():
        print(f"\n🎯 {pattern} ({info['complexity']} complexity)")
        print(f"   Scenario: {info['scenario']}")
        print(f"   Metrics: {', '.join(info['metrics'])}")
        print(f"   Formula: {info['formula'][:80]}...")
    
    # Show example formulas
    print("\n" + "="*80)
    print("📝 EXAMPLE FORMULAS")
    print("="*80)
    for category, formulas in EXAMPLE_FORMULAS.items():
        print(f"\n{category}:")
        for formula in formulas[:2]:  # Show first 2
            print(f"   • {formula}")
    
    # Show best practices
    print("\n" + "="*80)
    print("✨ BEST PRACTICES")
    print("="*80)
    print("\nMetric Naming:")
    for practice in BEST_PRACTICES["Metric Naming"][:3]:
        print(f"   • {practice}")
    
    print("\nFormula Design:")
    for practice in BEST_PRACTICES["Formula Design"][:3]:
        print(f"   • {practice}")
    
    # Final instructions
    print("\n" + "="*80)
    print("🚀 READY TO START")
    print("="*80)
    print("\n1. Run test: python test_llm_setup.py")
    print("2. Try examples: python examples_llm_dataset.py")
    print("3. Generate dataset: python llm_driven_dataset_generator.py")
    print("\nOr use: run_llm_dataset.bat (Windows)")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
