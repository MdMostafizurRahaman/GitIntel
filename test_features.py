#!/usr/bin/env python3
"""
Test new features manually
"""

from llm_git_analyzer import LLMGitAnalyzer

def test_features():
    analyzer = LLMGitAnalyzer()
    
    # Set repository to Kafka
    analyzer.set_repository('d:/GitIntel/kafka')
    print("Repository set!")
    
    # Test LOC time ratio with commit limit
    print("\n" + "="*50)
    print("Testing LOC Time Ratio with Commit Limit (100)")
    print("="*50)
    
    result = analyzer.analyze_loc_time_ratio('excel', commit_limit=100)
    print(result)
    
    # Test package churn with commit limit
    print("\n" + "="*50) 
    print("Testing Package Churn with Commit Limit (50)")
    print("="*50)
    
    result = analyzer.analyze_package_churn(threshold=500, output_format='excel', commit_limit=50)
    print(result)

if __name__ == "__main__":
    test_features()