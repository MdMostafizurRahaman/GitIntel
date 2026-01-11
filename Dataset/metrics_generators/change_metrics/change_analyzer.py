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
                timeout=5
            )
            
            commits = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Get total additions and deletions
            result = subprocess.run(
                ['git', 'log', '-p', '--', file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            additions = len(re.findall(r'^\+[^+]', result.stdout, re.MULTILINE))
            deletions = len(re.findall(r'^-[^-]', result.stdout, re.MULTILINE))
            
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
                timeout=10
            )
            
            total_commits = len(result.stdout.strip().split('\n')) if result.stdout else 0
            
            # Get total additions/deletions
            result = subprocess.run(
                ['git', 'log', '--all', '-p'],
                cwd=dir_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            additions = len(re.findall(r'^\+[^+]', result.stdout, re.MULTILINE))
            deletions = len(re.findall(r'^-[^-]', result.stdout, re.MULTILINE))
            
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
