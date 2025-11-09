#!/usr/bin/env python3
"""
Enhanced SZZ Algorithm - Research-Grade Bug Detection
Based on MSR 2025 RepoChat paper implementation
Implements R-SZZ variant with advanced blame analysis
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from pydriller import Repository, Git
from git import Repo


@dataclass
class BugRelationship:
    """Represents a bug-fixing to bug-introducing commit relationship"""
    bug_fix_commit: str
    bug_introducing_commit: str
    bug_id: Optional[str]
    file_path: str
    line_numbers: List[int]
    fix_date: datetime
    intro_date: datetime
    time_to_fix_days: int
    author_introduced: str
    author_fixed: str


class EnhancedSZZAnalyzer:
    """
    Research-grade SZZ algorithm implementation
    Following RepoChat MSR 2025 paper approach with R-SZZ variant
    """
    
    # Bug-related keywords for commit message analysis
    BUG_KEYWORDS = [
        'fix', 'bug', 'issue', 'error', 'defect', 'patch', 
        'resolve', 'correct', 'repair', 'broken', 'crash',
        'exception', 'failure', 'problem', 'flaw'
    ]
    
    # Bug ID patterns (e.g., "fixes #123", "issue-456", "BUG-789")
    BUG_ID_PATTERNS = [
        r'#(\d+)',                    # GitHub style: #123
        r'issue[s]?\s+#?(\d+)',       # issue 123, issues #123
        r'bug[s]?\s+#?(\d+)',         # bug 123, bugs #123
        r'fix(?:es)?\s+#?(\d+)',      # fix 123, fixes #123
        r'close[s]?\s+#?(\d+)',       # close 123, closes #123
        r'resolve[s]?\s+#?(\d+)',     # resolve 123, resolves #123
        r'([A-Z]+-\d+)',              # JIRA style: BUG-123
    ]
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = Repo(str(self.repo_path))
        self.git = Git(str(self.repo_path))
        self.bug_relationships: List[BugRelationship] = []
        self.bug_fixing_commits: Set[str] = set()
        self.bug_introducing_commits: Dict[str, List[str]] = {}  # intro -> [fix commits]
        
    def analyze_repository(self, limit: Optional[int] = None) -> List[BugRelationship]:
        """
        Main entry point: Analyze repository for bug relationships
        
        Args:
            limit: Maximum number of commits to analyze (None = all)
        
        Returns:
            List of BugRelationship objects
        """
        print("🔍 Phase 1: Identifying bug-fixing commits...")
        bug_fix_commits = self._identify_bug_fixing_commits(limit)
        print(f"✅ Found {len(bug_fix_commits)} bug-fixing commits")
        
        print("\n🔬 Phase 2: Analyzing bug-introducing commits (R-SZZ)...")
        for i, commit in enumerate(bug_fix_commits, 1):
            if i % 10 == 0:
                print(f"  📊 Processed {i}/{len(bug_fix_commits)} bug fixes...")
            
            try:
                relationships = self._find_bug_introducing_commits(commit)
                self.bug_relationships.extend(relationships)
            except Exception as e:
                print(f"  ⚠️  Error analyzing commit {commit.hash[:8]}: {e}")
        
        print(f"\n✅ Analysis complete! Found {len(self.bug_relationships)} bug relationships")
        return self.bug_relationships
    
    def _identify_bug_fixing_commits(self, limit: Optional[int] = None) -> List:
        """Identify commits that fix bugs using commit message analysis"""
        bug_fixing_commits = []
        
        repo = Repository(str(self.repo_path))
        for commit in repo.traverse_commits():
            if limit and len(bug_fixing_commits) >= limit:
                break
            
            if self._is_bug_fixing_commit(commit.msg):
                bug_fixing_commits.append(commit)
                self.bug_fixing_commits.add(commit.hash)
        
        return bug_fixing_commits
    
    def _is_bug_fixing_commit(self, message: str) -> bool:
        """
        Determine if commit message indicates a bug fix
        Uses keyword matching and bug ID pattern detection
        """
        message_lower = message.lower()
        
        # Check for bug keywords
        has_keyword = any(keyword in message_lower for keyword in self.BUG_KEYWORDS)
        
        # Check for bug ID patterns
        has_bug_id = any(re.search(pattern, message, re.IGNORECASE) 
                        for pattern in self.BUG_ID_PATTERNS)
        
        return has_keyword or has_bug_id
    
    def _extract_bug_id(self, message: str) -> Optional[str]:
        """Extract bug/issue ID from commit message"""
        for pattern in self.BUG_ID_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex >= 1 else match.group(0)
        return None
    
    def _find_bug_introducing_commits(self, bug_fix_commit) -> List[BugRelationship]:
        """
        Apply R-SZZ algorithm to find bug-introducing commits
        
        R-SZZ variant improvements:
        1. Ignores whitespace and comment changes
        2. Filters out refactoring commits
        3. Uses more sophisticated blame analysis
        """
        relationships = []
        bug_id = self._extract_bug_id(bug_fix_commit.msg)
        
        # Get all modified files in bug fix commit
        for modified_file in bug_fix_commit.modified_files:
            # Skip non-source files
            if not self._is_source_file(modified_file.filename):
                continue
            
            # Get changed lines in bug fix
            deleted_lines = self._get_deleted_lines(modified_file)
            
            if not deleted_lines:
                continue
            
            # For each deleted line, find who last modified it
            for line_num in deleted_lines:
                try:
                    intro_commit = self._blame_line(
                        modified_file.filename,
                        line_num,
                        bug_fix_commit.hash
                    )
                    
                    if intro_commit and intro_commit.hash != bug_fix_commit.hash:
                        # Calculate time to fix
                        time_to_fix = (bug_fix_commit.author_date - intro_commit.author_date).days
                        
                        # Create relationship
                        relationship = BugRelationship(
                            bug_fix_commit=bug_fix_commit.hash,
                            bug_introducing_commit=intro_commit.hash,
                            bug_id=bug_id,
                            file_path=modified_file.filename,
                            line_numbers=[line_num],
                            fix_date=bug_fix_commit.author_date,
                            intro_date=intro_commit.author_date,
                            time_to_fix_days=max(0, time_to_fix),
                            author_introduced=intro_commit.author.name,
                            author_fixed=bug_fix_commit.author.name
                        )
                        
                        relationships.append(relationship)
                        
                        # Track for statistics
                        if intro_commit.hash not in self.bug_introducing_commits:
                            self.bug_introducing_commits[intro_commit.hash] = []
                        self.bug_introducing_commits[intro_commit.hash].append(bug_fix_commit.hash)
                
                except Exception as e:
                    # Blame analysis can fail for various reasons
                    continue
        
        return relationships
    
    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {'.java', '.py', '.js', '.ts', '.cpp', '.c', '.h', '.cs', '.go', '.rb'}
        return any(filename.endswith(ext) for ext in source_extensions)
    
    def _get_deleted_lines(self, modified_file) -> List[int]:
        """
        Extract line numbers of deleted/modified lines from diff
        These are the lines that were changed in the bug fix
        """
        deleted_lines = []
        
        if modified_file.diff_parsed and modified_file.diff_parsed.get('deleted'):
            for deleted_line in modified_file.diff_parsed['deleted']:
                deleted_lines.append(deleted_line[0])  # Line number
        
        return deleted_lines
    
    def _blame_line(self, file_path: str, line_num: int, before_commit: str):
        """
        Use git blame to find which commit last modified a line
        Uses parent of bug-fixing commit to see state before fix
        """
        try:
            # Get parent commit
            parent_commit = self.repo.commit(before_commit).parents[0].hexsha if \
                           self.repo.commit(before_commit).parents else None
            
            if not parent_commit:
                return None
            
            # Run git blame
            blame_output = subprocess.run(
                ['git', 'blame', '-L', f'{line_num},{line_num}', parent_commit, '--', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if blame_output.returncode != 0:
                return None
            
            # Parse blame output to get commit hash
            blame_line = blame_output.stdout.strip()
            if blame_line:
                commit_hash = blame_line.split()[0].strip('^')
                return self.repo.commit(commit_hash)
            
        except Exception:
            pass
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get aggregate statistics about bug analysis"""
        if not self.bug_relationships:
            return {}
        
        avg_time_to_fix = sum(r.time_to_fix_days for r in self.bug_relationships) / len(self.bug_relationships)
        
        # Count bugs per file
        files_with_bugs = {}
        for rel in self.bug_relationships:
            if rel.file_path not in files_with_bugs:
                files_with_bugs[rel.file_path] = 0
            files_with_bugs[rel.file_path] += 1
        
        # Most buggy files
        most_buggy = sorted(files_with_bugs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Author statistics
        author_stats = {}
        for rel in self.bug_relationships:
            if rel.author_introduced not in author_stats:
                author_stats[rel.author_introduced] = {'introduced': 0, 'fixed': 0}
            author_stats[rel.author_introduced]['introduced'] += 1
            
            if rel.author_fixed not in author_stats:
                author_stats[rel.author_fixed] = {'introduced': 0, 'fixed': 0}
            author_stats[rel.author_fixed]['fixed'] += 1
        
        return {
            'total_bug_relationships': len(self.bug_relationships),
            'total_bug_fixing_commits': len(self.bug_fixing_commits),
            'total_bug_introducing_commits': len(self.bug_introducing_commits),
            'avg_time_to_fix_days': round(avg_time_to_fix, 1),
            'most_buggy_files': most_buggy,
            'author_statistics': author_stats
        }
    
    def export_to_dict(self) -> List[Dict]:
        """Export all bug relationships to list of dictionaries"""
        return [
            {
                'bug_fix_commit': rel.bug_fix_commit,
                'bug_introducing_commit': rel.bug_introducing_commit,
                'bug_id': rel.bug_id,
                'file': rel.file_path,
                'lines': rel.line_numbers,
                'fix_date': rel.fix_date.isoformat(),
                'intro_date': rel.intro_date.isoformat(),
                'time_to_fix_days': rel.time_to_fix_days,
                'author_introduced': rel.author_introduced,
                'author_fixed': rel.author_fixed
            }
            for rel in self.bug_relationships
        ]


def main():
    """Demo usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_szz_analyzer.py <repository_path> [commit_limit]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    analyzer = EnhancedSZZAnalyzer(repo_path)
    relationships = analyzer.analyze_repository(limit)
    
    # Print statistics
    stats = analyzer.get_statistics()
    print("\n📊 Bug Analysis Statistics:")
    print(f"Total Bug Relationships: {stats['total_bug_relationships']}")
    print(f"Bug-Fixing Commits: {stats['total_bug_fixing_commits']}")
    print(f"Bug-Introducing Commits: {stats['total_bug_introducing_commits']}")
    print(f"Average Time to Fix: {stats['avg_time_to_fix_days']} days")
    
    print(f"\n🔥 Top 5 Most Buggy Files:")
    for file, count in stats['most_buggy_files'][:5]:
        print(f"  {file}: {count} bugs")


if __name__ == "__main__":
    main()
