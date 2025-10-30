# Enhanced Java Package Churn Analysis Script
from pydriller import Repository
import re
import csv
import os
import pandas as pd
from datetime import datetime

# Configuration
REPO_PATHS = [
    r'D:\GitIntel\Spring-Boot-in-Detailed-Way',
    r'D:\GitIntel\MOOC-Java-course'
]
OUTPUT_CSV = 'package_churn_analysis.csv'
DETAILED_OUTPUT_CSV = 'detailed_package_analysis.csv'
LINE_THRESHOLD = 500   # configurable threshold
MODE = 'per_commit'    # 'per_commit' or 'cumulative'

def detect_package_from_source(src_text):
    """Extract package name from Java source code"""
    if not src_text:
        return None
    
    # Try regex first for speed
    m = re.search(r'^\s*package\s+([a-zA-Z0-9_.]+)\s*;', src_text, re.MULTILINE)
    if m:
        return m.group(1)
    
    # Fallback to javalang for robustness
    try:
        import javalang
        tree = javalang.parse.parse(src_text)
        if getattr(tree, 'package', None):
            return tree.package.name
    except Exception:
        pass
    
    return None

def package_from_filepath(filepath):
    """Infer package name from file path"""
    if not filepath:
        return '<<unknown>>'
    
    # Normalize path separators
    parts = filepath.replace('\\', '/').split('/')
    
    # Look for standard Java patterns
    if 'src' in parts:
        try:
            src_idx = parts.index('src')
            # Common patterns: src/main/java/com/example/...
            if len(parts) > src_idx + 2 and parts[src_idx + 1] == 'main' and parts[src_idx + 2] == 'java':
                pkg_parts = parts[src_idx + 3:-1]  # exclude filename
            else:
                pkg_parts = parts[src_idx + 1:-1]
            
            if pkg_parts:
                return '.'.join(pkg_parts)
        except ValueError:
            pass
    
    # Fallback: use directory structure
    dir_path = os.path.dirname(filepath)
    if dir_path:
        return dir_path.replace('/', '.').replace('\\', '.')
    
    return '<<unknown>>'

def analyze_repository(repo_path):
    """Analyze a single repository and return results"""
    print(f"\nAnalyzing repository: {repo_path}")
    
    # Storage for results
    rows = []
    cumulative = {}
    commit_count = 0
    
    try:
        for commit in Repository(repo_path).traverse_commits():
            commit_count += 1
            if commit_count % 10 == 0:
                print(f"Processed {commit_count} commits...")
            
            commit_hash = commit.hash
            commit_date = commit.author_date.isoformat()
            author = commit.author.name
            message = commit.msg.replace('\n', ' ').replace('\r', ' ')[:200]  # truncate long messages
            
            per_pkg = {}
            
            for mod in commit.modified_files:
                # Focus only on Java files
                if not (mod.filename and mod.filename.endswith('.java')):
                    continue
                
                # Get metrics from PyDriller
                added = mod.added_lines or 0
                removed = mod.deleted_lines or 0
                churn = added + removed
                
                # Skip if no meaningful changes
                if churn == 0:
                    continue
                
                # Determine package name
                pkg = None
                if mod.source_code:
                    pkg = detect_package_from_source(mod.source_code)
                
                if not pkg:
                    file_path = mod.new_path or mod.old_path or mod.filename
                    pkg = package_from_filepath(file_path)
                
                if not pkg:
                    pkg = '<<unknown>>'
                
                # Aggregate by package
                if pkg not in per_pkg:
                    per_pkg[pkg] = {
                        'added': 0, 
                        'removed': 0, 
                        'churn': 0, 
                        'files': set(),
                        'file_details': []
                    }
                
                per_pkg[pkg]['added'] += added
                per_pkg[pkg]['removed'] += removed
                per_pkg[pkg]['churn'] += churn
                per_pkg[pkg]['files'].add(mod.new_path or mod.old_path or mod.filename)
                per_pkg[pkg]['file_details'].append({
                    'file': mod.filename,
                    'added': added,
                    'removed': removed,
                    'churn': churn
                })
            
            # Process results based on mode
            if MODE == 'per_commit':
                for pkg, metrics in per_pkg.items():
                    if metrics['churn'] >= LINE_THRESHOLD:
                        rows.append({
                            'repository': os.path.basename(repo_path),
                            'commit': commit_hash,
                            'date': commit_date,
                            'author': author,
                            'message': message,
                            'package': pkg,
                            'lines_added': metrics['added'],
                            'lines_removed': metrics['removed'],
                            'churn': metrics['churn'],
                            'num_files': len(metrics['files']),
                            'files_changed': '|'.join(metrics['files']),
                            'threshold_exceeded': True
                        })
            else:  # cumulative mode
                for pkg, metrics in per_pkg.items():
                    if pkg not in cumulative:
                        cumulative[pkg] = {
                            'added': 0, 
                            'removed': 0, 
                            'churn': 0, 
                            'commits': 0,
                            'files': set(),
                            'repository': os.path.basename(repo_path)
                        }
                    
                    cumulative[pkg]['added'] += metrics['added']
                    cumulative[pkg]['removed'] += metrics['removed']
                    cumulative[pkg]['churn'] += metrics['churn']
                    cumulative[pkg]['commits'] += 1
                    cumulative[pkg]['files'].update(metrics['files'])
    
    except Exception as e:
        print(f"Error processing repository {repo_path}: {e}")
        return rows, cumulative
    
    print(f"Completed analysis. Total commits processed: {commit_count}")
    
    # If cumulative mode, add qualifying packages to rows
    if MODE == 'cumulative':
        for pkg, metrics in cumulative.items():
            if metrics['churn'] >= LINE_THRESHOLD:
                rows.append({
                    'repository': metrics['repository'],
                    'commit': 'CUMULATIVE',
                    'date': '',
                    'author': '',
                    'message': f'Cumulative across {metrics["commits"]} commits',
                    'package': pkg,
                    'lines_added': metrics['added'],
                    'lines_removed': metrics['removed'],
                    'churn': metrics['churn'],
                    'num_files': len(metrics['files']),
                    'files_changed': '|'.join(metrics['files']),
                    'threshold_exceeded': True
                })
    
    return rows, cumulative

def main():
    print("Java Package Churn Analysis")
    print("=" * 50)
    print(f"Mode: {MODE}")
    print(f"Threshold: {LINE_THRESHOLD} lines")
    print(f"Repositories to analyze: {len(REPO_PATHS)}")
    
    all_rows = []
    all_cumulative = {}
    
    # Analyze each repository
    for repo_path in REPO_PATHS:
        if os.path.exists(repo_path):
            rows, cumulative = analyze_repository(repo_path)
            all_rows.extend(rows)
            
            # Merge cumulative data
            for pkg, metrics in cumulative.items():
                repo_pkg_key = f"{os.path.basename(repo_path)}::{pkg}"
                all_cumulative[repo_pkg_key] = metrics
        else:
            print(f"Repository not found: {repo_path}")
    
    # Write main results
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\nResults written to: {OUTPUT_CSV}")
        print(f"Total packages exceeding threshold: {len(all_rows)}")
        
        # Summary statistics
        print("\n" + "=" * 50)
        print("SUMMARY STATISTICS")
        print("=" * 50)
        
        if not df.empty:
            print(f"Total repositories analyzed: {df['repository'].nunique()}")
            print(f"Total packages exceeding {LINE_THRESHOLD} line threshold: {len(df)}")
            print(f"Average churn per qualifying package: {df['churn'].mean():.1f}")
            print(f"Maximum churn in a single package: {df['churn'].max()}")
            
            print("\nTop 10 packages by churn:")
            top_packages = df.nlargest(10, 'churn')[['repository', 'package', 'churn', 'num_files']]
            print(top_packages.to_string(index=False))
            
            print("\nPackages by repository:")
            repo_summary = df.groupby('repository').agg({
                'package': 'count',
                'churn': ['sum', 'mean'],
                'num_files': 'sum'
            }).round(1)
            print(repo_summary)
    else:
        print(f"\nNo packages found exceeding the {LINE_THRESHOLD} line threshold.")
    
    # Write detailed cumulative analysis
    if all_cumulative:
        detailed_rows = []
        for repo_pkg, metrics in all_cumulative.items():
            repo, pkg = repo_pkg.split('::', 1)
            detailed_rows.append({
                'repository': repo,
                'package': pkg,
                'total_commits': metrics['commits'],
                'total_added': metrics['added'],
                'total_removed': metrics['removed'],
                'total_churn': metrics['churn'],
                'total_files': len(metrics['files']),
                'avg_churn_per_commit': metrics['churn'] / metrics['commits'] if metrics['commits'] > 0 else 0
            })
        
        detailed_df = pd.DataFrame(detailed_rows)
        detailed_df = detailed_df.sort_values('total_churn', ascending=False)
        detailed_df.to_csv(DETAILED_OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"\nDetailed cumulative analysis written to: {DETAILED_OUTPUT_CSV}")

if __name__ == "__main__":
    main()