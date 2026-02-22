#!/usr/bin/env python3
"""
Process Metrics Calculator - Real implementation
Measures software process metrics like bug lifecycle, revisions
"""

import subprocess
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta


class ProcessAnalyzer:
    """Analyze software process metrics"""
    
    @staticmethod
    def analyze_file(file_path: str, repo_path: str = None) -> Dict[str, int]:
        """
        Analyze process metrics for a file (REAL git data)
        
        Returns: num_authors, num_commits, code_age, change_frequency, 
                pre_release_bugs, post_release_bugs, bug_fix_time, revision_count
        """
        try:
            if repo_path is None:
                repo_path = Path(file_path).parent
            
            # Get commits
            result = subprocess.run(
                ['git', 'log', '--oneline', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            num_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get authors
            result = subprocess.run(
                ['git', 'log', '--format=%aN', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            authors = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
            num_authors = len(authors)
            
            # Get first and last commit dates for age
            result = subprocess.run(
                ['git', 'log', '--format=%at', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            timestamps = [int(t) for t in result.stdout.strip().split('\n') if t]
            code_age = (max(timestamps) - min(timestamps)) if len(timestamps) > 1 else 0
            code_age_days = code_age // 86400  # Convert seconds to days
            
            # Change frequency = commits per day
            change_frequency = round(num_commits / max(1, code_age_days), 3)
            
            return {
                'num_authors': num_authors,
                'num_commits': num_commits,
                'code_age': code_age_days,
                'change_frequency': change_frequency,
                'pre_release_bugs': 0,  # Requires release tagging
                'post_release_bugs': 0,
                'bug_fix_time': 0,  # Requires bug tracking integration
                'revision_count': num_commits
            }
        except:
            return {
                'num_authors': 0,
                'num_commits': 0,
                'code_age': 0,
                'change_frequency': 0,
                'pre_release_bugs': 0,
                'post_release_bugs': 0,
                'bug_fix_time': 0,
                'revision_count': 0
            }
    
    @staticmethod
    def analyze_file_history(file_path: str, repo_path: str = None) -> Dict[str, int]:
        """
        Analyze process metrics from file's git history
        
        Args:
            file_path: Path to file to analyze
            repo_path: Path to git repository
            
        Returns:
            Dictionary with process metrics
        """
        if repo_path is None:
            repo_path = Path(file_path).parent
        
        try:
            # Get revision count (number of commits)
            result = subprocess.run(
                ['git', 'log', '--oneline', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            revision_count = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Get total additions and deletions per revision
            result = subprocess.run(
                ['git', 'log', '-p', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            loc_added_total = result.stdout.count('\n+')
            loc_deleted_total = result.stdout.count('\n-')
            
            loc_added_per_revision = (loc_added_total / revision_count) if revision_count > 0 else 0
            loc_deleted_per_revision = (loc_deleted_total / revision_count) if revision_count > 0 else 0
            
            # Get authors (pre-release contributors)
            result = subprocess.run(
                ['git', 'log', '--format=%aN', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            authors = len(set(result.stdout.strip().split('\n'))) if result.stdout else 0
            
            return {
                'revision_count': revision_count,
                'loc_added_per_revision': round(loc_added_per_revision, 2),
                'loc_deleted_per_revision': round(loc_deleted_per_revision, 2),
                'pre_release_bugs': 0,  # Placeholder - would need bug tracking data
                'post_release_bugs': 0,
                'authors_count': authors
            }
            
        except Exception:
            return ProcessAnalyzer._empty_process()
    
    @staticmethod
    def analyze_repository(repo_path: str) -> Dict[str, int]:
        """
        Analyze process metrics for entire repository
        
        Args:
            repo_path: Path to git repository
            
        Returns:
            Dictionary with repository-level process metrics
        """
        try:
            # Total revisions
            result = subprocess.run(
                ['git', 'log', '--oneline', '--all'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            total_revisions = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Total authors
            result = subprocess.run(
                ['git', 'log', '--format=%aN', '--all'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            total_authors = len(set(result.stdout.strip().split('\n'))) if result.stdout else 0
            
            # Repository age
            result = subprocess.run(
                ['git', 'log', '--format=%ai', '--all', '--reverse'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            repo_age_days = 0
            if result.stdout:
                first_commit = result.stdout.strip().split('\n')[0]
                try:
                    first_date = datetime.fromisoformat(first_commit.replace(' ', 'T'))
                    repo_age_days = (datetime.now() - first_date).days
                except:
                    repo_age_days = 0
            
            return {
                'total_revisions': total_revisions,
                'total_authors': total_authors,
                'repository_age_days': repo_age_days
            }
            
        except Exception:
            return ProcessAnalyzer._empty_process()
    
    @staticmethod
    def _empty_process() -> Dict:
        """Return empty process metrics"""
        return {
            'revision_count': 0,
            'loc_added_per_revision': 0.0,
            'loc_deleted_per_revision': 0.0,
            'pre_release_bugs': 0,
            'post_release_bugs': 0,
            'authors_count': 0
        }
