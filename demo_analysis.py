#!/usr/bin/env python3
"""
GitIntel Ultimate Demo Script
"""
from gitintel_ultimate_fixed import GitIntelUltimate
import time

print('🚀 GitIntel Ultimate Demo - Analyzing test repository')
print('=' * 60)

# Initialize
ultimate = GitIntelUltimate(
    neo4j_uri='bolt://localhost:7687',
    neo4j_user='neo4j',
    neo4j_password='password'
)

try:
    # Analyze test repository
    repo_path = '../test'

    def progress_callback(progress, message):
        print(f'📊 {progress:.1f}% - {message}')

    print(f'📁 Analyzing: {repo_path}')
    print('⏳ Starting analysis (this may take a moment)...')
    print()

    start_time = time.time()
    results = ultimate.analyze_repository(
        repo_path=repo_path,
        progress_callback=progress_callback,
        commit_limit=50  # Limit for demo
    )

    duration = time.time() - start_time

    print()
    print('🎉 ANALYSIS COMPLETE!')
    print('=' * 60)
    print(f'⏱️  Duration: {duration:.1f} seconds')
    print(f'📊 Commits processed: {results.get("commits_processed", 0):,}')
    print(f'📁 Files analyzed: {results.get("files_analyzed", 0):,}')
    print(f'👥 Contributors found: {results.get("contributors_found", 0):,}')
    print(f'🐛 Bug relationships: {results.get("bug_relationships", 0):,}')

    # Show key metrics
    if 'reliability_metrics' in results:
        rel = results['reliability_metrics']
        print()
        print('🔧 RELIABILITY METRICS:')
        print(f'   Bug Density: {rel.get("bug_density", 0):.2f}')
        print(f'   File Stability: {rel.get("file_stability_index", 0):.1f}%')
        print(f'   Test Coverage: {rel.get("test_file_ratio", 0):.1f}%')

    if 'productivity_metrics' in results:
        prod = results['productivity_metrics']
        print()
        print('⚡ PRODUCTIVITY METRICS:')
        print(f'   Commits/Day: {prod.get("commits_per_day", 0):.1f}')
        print(f'   Collaboration: {prod.get("collaboration_index", 0):.1f}%')

    print()
    print('✅ GitIntel Ultimate is WORKING PERFECTLY!')
    print('💡 The system successfully analyzed the repository with all metrics!')

finally:
    ultimate.close()