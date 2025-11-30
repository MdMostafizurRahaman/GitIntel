#!/usr/bin/env python3
"""
Dataset Type Explanation Guide
GitHub Autonomous Agent generates various types of datasets
"""

DATASET_TYPES = {
    "Bug Density Dataset": {
        "description": "Calculates bug density using formula: defects / (lines_of_code / 1000)",
        "contains": ["Module names", "Lines of code", "Number of defects", "Bug density per KLOC", "Quality ratings"],
        "format": "CSV/Excel",
        "use_cases": ["Software quality assessment", "Code review prioritization", "Technical debt analysis"],
        "example_query": "make dataset of bug density = defects / (lines_of_code / 1000) in csv"
    },
    
    "Author-Commit Activity Dataset": {
        "description": "Analysis of developer contributions and commit patterns",
        "contains": ["Commit hashes", "Author names", "Commit dates", "Commit messages", "Author activity frequency"],
        "format": "Excel/JSON/CSV", 
        "use_cases": ["Developer productivity analysis", "Team performance assessment", "Contribution tracking"],
        "example_query": "generate dataset using Authors, Commits, Age, Frequency"
    },
    
    "Temporal Activity Dataset": {
        "description": "Time-based analysis of repository activity and development patterns",
        "contains": ["Commit timestamps", "Activity frequency", "Temporal patterns", "Development cycles"],
        "format": "Excel/JSON",
        "use_cases": ["Development timeline analysis", "Sprint planning", "Resource allocation"],
        "example_query": "generate dataset with commit frequency and time patterns"
    },
    
    "Repository Evolution Dataset": {
        "description": "Track repository changes and evolution over time",
        "contains": ["Repository age", "Growth metrics", "Change patterns", "Evolution indicators"],
        "format": "Excel/JSON",
        "use_cases": ["Project lifecycle analysis", "Growth tracking", "Maintenance planning"],
        "example_query": "create dataset showing repository age and evolution metrics"
    },
    
    "Code Quality Metrics Dataset": {
        "description": "Comprehensive code quality and complexity analysis",
        "contains": ["Cyclomatic complexity", "Code quality scores", "Maintainability index", "Technical debt indicators"],
        "format": "Excel/CSV",
        "use_cases": ["Code quality assessment", "Refactoring prioritization", "Quality gates"],
        "example_query": "generate dataset with complexity and quality metrics"
    },
    
    "Code Size & Structure Dataset": {
        "description": "Analysis of codebase size, structure, and organization",
        "contains": ["Lines of code (LOC)", "File sizes", "Module structure", "Size distribution"],
        "format": "Excel/CSV",
        "use_cases": ["Codebase analysis", "Architecture assessment", "Size estimation"],
        "example_query": "create dataset of LOC, file sizes, and code structure"
    },
    
    "Benchmark Datasets": {
        "description": "Industry-standard benchmark datasets for research and testing",
        "contains": {
            "Defects4J": "Real bugs from Java projects with buggy/fixed code pairs",
            "Bugs.jar": "Curated bug dataset with severity and complexity metrics",
            "Promise": "Software engineering metrics and defect data",
            "CodeXGLUE": "Code understanding and generation tasks",
            "CodeSearchNet": "Code search and documentation datasets"
        },
        "format": "JSON/Folder structure",
        "use_cases": ["Research validation", "Algorithm testing", "Comparative studies"],
        "example_query": "generate Defects4J, Bugs.jar, Promise datasets"
    }
}

def print_dataset_guide():
    """Print a comprehensive guide to dataset types"""
    print("🤖 GitHub Autonomous Agent - Dataset Types Guide")
    print("=" * 60)
    print()
    
    for dataset_type, info in DATASET_TYPES.items():
        print(f"📊 {dataset_type}")
        print("-" * len(dataset_type))
        print(f"Description: {info['description']}")
        print()
        
        if isinstance(info['contains'], dict):
            print("Contains:")
            for key, value in info['contains'].items():
                print(f"  • {key}: {value}")
        else:
            print(f"Contains: {', '.join(info['contains'])}")
        
        print(f"Format: {info['format']}")
        print(f"Use Cases: {', '.join(info['use_cases'])}")
        print(f"Example: '{info['example_query']}'")
        print()
        print("-" * 60)
        print()

if __name__ == "__main__":
    print_dataset_guide()