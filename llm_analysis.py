# LLM-based Package Analysis Orchestrator
import pandas as pd
import json
import os
from datetime import datetime

def analyze_churn_data(csv_file):
    """Analyze the package churn data and provide insights"""
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    # Load data
    df = pd.read_csv(csv_file)
    
    print("=" * 60)
    print("📊 COMPREHENSIVE JAVA PACKAGE CHURN ANALYSIS")
    print("=" * 60)
    
    # Basic statistics
    print(f"\n🔍 BASIC STATISTICS:")
    print(f"   • Total records: {len(df)}")
    print(f"   • Unique packages: {df['package'].nunique()}")
    print(f"   • Repositories analyzed: {df['repository'].nunique()}")
    print(f"   • Date range: {df['date'].min()[:10]} to {df['date'].max()[:10]}")
    
    # Churn analysis
    print(f"\n📈 CHURN METRICS:")
    print(f"   • Average churn per package: {df['churn'].mean():.1f} lines")
    print(f"   • Median churn: {df['churn'].median():.1f} lines")
    print(f"   • Maximum churn: {df['churn'].max()} lines")
    print(f"   • Standard deviation: {df['churn'].std():.1f}")
    
    # Top churning packages
    print(f"\n🔥 TOP 5 HIGHEST CHURN PACKAGES:")
    top_packages = df.nlargest(5, 'churn')[['package', 'churn', 'lines_added', 'lines_removed', 'commit']]
    for i, row in top_packages.iterrows():
        print(f"   {top_packages.index.get_loc(i)+1}. {row['package']}")
        print(f"      └─ Churn: {row['churn']} lines (+{row['lines_added']}, -{row['lines_removed']})")
        print(f"      └─ Commit: {row['commit'][:8]}")
    
    # Repository breakdown
    print(f"\n📁 REPOSITORY BREAKDOWN:")
    repo_stats = df.groupby('repository').agg({
        'churn': ['count', 'sum', 'mean'],
        'num_files': 'sum'
    }).round(1)
    
    for repo in df['repository'].unique():
        repo_data = df[df['repository'] == repo]
        total_churn = repo_data['churn'].sum()
        avg_churn = repo_data['churn'].mean()
        total_commits = len(repo_data)
        
        print(f"   📂 {repo}:")
        print(f"      └─ Qualifying commits: {total_commits}")
        print(f"      └─ Total churn: {total_churn:,} lines")
        print(f"      └─ Average churn/commit: {avg_churn:.1f} lines")
    
    # File impact analysis
    print(f"\n📄 FILE IMPACT ANALYSIS:")
    print(f"   • Average files changed per commit: {df['num_files'].mean():.1f}")
    print(f"   • Maximum files in single commit: {df['num_files'].max()}")
    
    # Package patterns
    print(f"\n🎯 PACKAGE PATTERNS:")
    package_patterns = {}
    for pkg in df['package'].unique():
        if '.' in pkg:
            root = pkg.split('.')[0]
        else:
            root = pkg
        
        if root not in package_patterns:
            package_patterns[root] = 0
        package_patterns[root] += 1
    
    sorted_patterns = sorted(package_patterns.items(), key=lambda x: x[1], reverse=True)
    for pattern, count in sorted_patterns[:5]:
        print(f"   • {pattern}: {count} packages")
    
    # Generate LLM prompt for further analysis
    generate_llm_prompts(df)
    
    return df

def generate_llm_prompts(df):
    """Generate prompts for LLM analysis"""
    
    print(f"\n🤖 LLM ANALYSIS PROMPTS:")
    print("=" * 60)
    
    # Prompt 1: Change Classification
    sample_commits = df.head(3)
    print(f"\n💡 PROMPT 1 - CHANGE CLASSIFICATION:")
    print(f"```")
    print(f"You are a software engineering analyst. Analyze these Java package changes and classify them as:")
    print(f"- REFACTOR: Code restructuring without functional changes")
    print(f"- FEATURE: New functionality addition")
    print(f"- BUGFIX: Error corrections")
    print(f"- TEST: Test code changes")
    print(f"- MAINTENANCE: Documentation, formatting, etc.")
    print(f"")
    print(f"Data to analyze:")
    for _, row in sample_commits.iterrows():
        print(f"Package: {row['package']}")
        print(f"Churn: {row['churn']} lines (+{row['lines_added']}, -{row['lines_removed']})")
        print(f"Files: {row['num_files']} files changed")
        print(f"Commit: {row['message'][:100]}...")
        print(f"---")
    print(f"```")
    
    # Prompt 2: Risk Assessment
    high_churn = df[df['churn'] > df['churn'].quantile(0.75)]
    print(f"\n💡 PROMPT 2 - RISK ASSESSMENT:")
    print(f"```")
    print(f"Analyze these high-churn packages for potential risks:")
    print(f"- Maintainability concerns")
    print(f"- Code quality issues")
    print(f"- Testing requirements")
    print(f"- Refactoring opportunities")
    print(f"")
    print(f"High churn packages (top 75th percentile):")
    for _, row in high_churn.head(3).iterrows():
        print(f"• {row['package']}: {row['churn']} lines changed")
        print(f"  └─ {row['num_files']} files affected")
    print(f"```")
    
    # Prompt 3: Pattern Recognition
    print(f"\n💡 PROMPT 3 - PATTERN RECOGNITION:")
    print(f"```")
    print(f"Identify patterns in this Java project evolution:")
    print(f"1. Which packages show consistent high activity?")
    print(f"2. Are there coupling issues between packages?")
    print(f"3. What's the test vs production code ratio?")
    print(f"4. Are there any architectural smells?")
    print(f"")
    print(f"Summary statistics:")
    print(f"- Total packages analyzed: {df['package'].nunique()}")
    print(f"- Average churn: {df['churn'].mean():.1f} lines")
    print(f"- Most active package: {df.loc[df['churn'].idxmax(), 'package']}")
    print(f"```")

def create_dataset_for_ml():
    """Create structured dataset for machine learning"""
    
    df = pd.read_csv('package_churn_analysis.csv')
    
    # Feature engineering
    ml_features = []
    
    for _, row in df.iterrows():
        features = {
            'repository': row['repository'],
            'package_name': row['package'],
            'package_depth': len(row['package'].split('.')) if '.' in row['package'] else 1,
            'is_test_package': 'test' in row['package'].lower(),
            'lines_added': row['lines_added'],
            'lines_removed': row['lines_removed'],
            'churn_ratio': row['lines_removed'] / (row['lines_added'] + 1),  # avoid division by zero
            'file_count': row['num_files'],
            'churn_per_file': row['churn'] / row['num_files'] if row['num_files'] > 0 else 0,
            'commit_message_length': len(row['message']),
            'is_major_change': row['churn'] > 1000,
            'change_type': classify_change_heuristic(row)
        }
        ml_features.append(features)
    
    ml_df = pd.DataFrame(ml_features)
    ml_df.to_csv('ml_dataset.csv', index=False)
    
    print(f"\n🎯 MACHINE LEARNING DATASET CREATED:")
    print(f"   • File: ml_dataset.csv")
    print(f"   • Features: {len(ml_df.columns)}")
    print(f"   • Records: {len(ml_df)}")
    print(f"   • Features: {list(ml_df.columns)}")
    
    return ml_df

def classify_change_heuristic(row):
    """Simple heuristic to classify changes"""
    if 'test' in row['package'].lower():
        return 'TEST'
    elif row['lines_removed'] > row['lines_added']:
        return 'REFACTOR'
    elif row['churn'] > 2000:
        return 'MAJOR_FEATURE'
    else:
        return 'FEATURE'

def main():
    """Main analysis function"""
    csv_file = 'package_churn_analysis.csv'
    
    # Perform comprehensive analysis
    df = analyze_churn_data(csv_file)
    
    if df is not None:
        # Create ML dataset
        ml_df = create_dataset_for_ml()
        
        # Additional insights
        print(f"\n📋 NEXT STEPS FOR LLM INTEGRATION:")
        print(f"1. Copy the generated prompts above and paste them into your LLM")
        print(f"2. Use ml_dataset.csv for automated classification training")
        print(f"3. Consider running cumulative analysis for long-term trends")
        print(f"4. Integrate with code quality metrics (complexity, coverage)")
        
        print(f"\n✅ Analysis complete! Check the generated CSV files for detailed data.")

if __name__ == "__main__":
    main()