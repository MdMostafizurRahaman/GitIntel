#!/usr/bin/env python3
"""
Change Metrics Calculator - Using real git history
Calculates code churn, additions, deletions from git commits
"""

import subprocess
from pathlib import Path
from typing import Dict
import re


class ChangeAnalyzer:
    """Analyze code changes from git history"""
    
    @staticmethod
    def analyze_file(file_path: str, repo_path: str = None) -> Dict[str, int]:
        """
        Analyze changes to a file using git history
        
        Args:
            file_path: Path to file to analyze
            repo_path: Path to git repository (auto-detected if None)
            
        Returns:
            Dictionary with change metrics
        """
        if repo_path is None:
            repo_path = Path(file_path).parent
        
        try:
            # Get number of commits affecting this file
            result = subprocess.run(
                ['git', 'log', '--oneline', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            
            commits = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Get total additions and deletions (--numstat is fast: no diff content)
            result = subprocess.run(
                ['git', 'log', '--numstat', '--format=', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )

            additions, deletions = 0, 0
            for line in result.stdout.splitlines():
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        additions += int(parts[0])
                        deletions += int(parts[1])
                    except ValueError:
                        pass  # binary files show '-' instead of numbers
            
            return {
                'num_commits': commits,
                'additions': additions,
                'deletions': deletions,
                'churn': additions + deletions,
                'changes': commits
            }
            
        except Exception as e:
            return ChangeAnalyzer._empty_changes()
    
    @staticmethod
    def analyze_directory(dir_path: str) -> Dict[str, int]:
        """
        Analyze total changes in a directory
        
        Args:
            dir_path: Path to directory
            
        Returns:
            Dictionary with aggregate change metrics
        """
        try:
            result = subprocess.run(
                ['git', 'log', '--all', '--oneline'],
                cwd=dir_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )
            
            total_commits = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Get total additions/deletions (--numstat: no diff content)
            result = subprocess.run(
                ['git', 'log', '--all', '--numstat', '--format='],
                cwd=dir_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            additions, deletions = 0, 0
            for line in result.stdout.splitlines():
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        additions += int(parts[0])
                        deletions += int(parts[1])
                    except ValueError:
                        pass
            
            return {
                'total_commits': total_commits,
                'total_additions': additions,
                'total_deletions': deletions,
                'total_churn': additions + deletions
            }
            
        except Exception:
            return ChangeAnalyzer._empty_changes()
    
    @staticmethod
    def _empty_changes() -> Dict:
        """Return empty change metrics"""
        return {
            'num_commits': 0,
            'additions': 0,
            'deletions': 0,
            'churn': 0,
            'changes': 0
        }
