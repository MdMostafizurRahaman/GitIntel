#!/usr/bin/env python3
"""
RepoChat Metrics - Repository Analysis and Testing Metrics
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pydriller import Repository
import logging

class RepositoryMetrics:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_cache = {}
    
    def generate_baseline_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Generate baseline repository metrics"""
        try:
            print("📊 Generating repository metrics...")
            
            metrics = {
                'basic_stats': self._calculate_basic_stats(repo_path),
                'code_metrics': self._calculate_code_metrics(repo_path),
                'contributor_metrics': self._calculate_contributor_metrics(repo_path),
                'time_metrics': self._calculate_time_metrics(repo_path),
                'quality_metrics': self._calculate_quality_metrics(repo_path),
                'testing_metrics': self._calculate_testing_metrics(repo_path),
                'complexity_metrics': self._calculate_complexity_metrics(repo_path)
            }
            
            # Cache metrics
            self.metrics_cache[repo_path] = metrics
            
            # Save to file
            self._save_metrics(repo_path, metrics)
            
            print("✅ Repository metrics generated successfully!")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to generate metrics: {e}")
            return {}
    
    def _calculate_basic_stats(self, repo_path: str) -> Dict[str, Any]:
        """Calculate basic repository statistics"""
        try:
            stats = {
                'total_commits': 0,
                'total_files': 0,
                'total_contributors': set(),
                'total_lines_added': 0,
                'total_lines_deleted': 0,
                'total_files_modified': set(),
                'repository_age_days': 0,
                'languages': {}
            }
            
            first_commit_date = None
            last_commit_date = None
            
            for commit in Repository(repo_path).traverse_commits():
                stats['total_commits'] += 1
                stats['total_contributors'].add(commit.author.email)
                stats['total_lines_added'] += commit.insertions
                stats['total_lines_deleted'] += commit.deletions
                
                # Track commit dates
                if not first_commit_date or commit.committer_date < first_commit_date:
                    first_commit_date = commit.committer_date
                if not last_commit_date or commit.committer_date > last_commit_date:
                    last_commit_date = commit.committer_date
                
                # Track files and languages
                for file in commit.modified_files:
                    if file.filename:
                        stats['total_files_modified'].add(file.filename)
                        
                        # Detect language
                        ext = os.path.splitext(file.filename)[1].lower()
                        lang = self._get_language_from_extension(ext)
                        stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            # Calculate repository age
            if first_commit_date and last_commit_date:
                stats['repository_age_days'] = (last_commit_date - first_commit_date).days
                stats['first_commit'] = first_commit_date.isoformat()
                stats['last_commit'] = last_commit_date.isoformat()
            
            # Convert sets to counts
            stats['total_contributors'] = len(stats['total_contributors'])
            stats['total_files'] = len(stats['total_files_modified'])
            stats.pop('total_files_modified')  # Remove the set
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate basic stats: {e}")
            return {}
    
    def _calculate_code_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate code-related metrics"""
        try:
            metrics = {
                'lines_of_code_by_language': {},
                'files_by_language': {},
                'average_file_size': {},
                'largest_files': [],
                'code_churn': {
                    'total_churn': 0,
                    'churn_by_month': {},
                    'high_churn_files': []
                }
            }
            
            file_sizes = {}
            churn_by_file = {}
            
            # Analyze current files
            for root, dirs, files in os.walk(repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    if self._is_source_file(file):
                        filepath = os.path.join(root, file)
                        relative_path = os.path.relpath(filepath, repo_path)
                        
                        # Count lines
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                
                            ext = os.path.splitext(file)[1].lower()
                            lang = self._get_language_from_extension(ext)
                            
                            metrics['lines_of_code_by_language'][lang] = \
                                metrics['lines_of_code_by_language'].get(lang, 0) + lines
                            metrics['files_by_language'][lang] = \
                                metrics['files_by_language'].get(lang, 0) + 1
                            
                            file_sizes[relative_path] = lines
                            
                        except Exception:
                            continue
            
            # Calculate average file sizes
            for lang in metrics['files_by_language']:
                if metrics['files_by_language'][lang] > 0:
                    metrics['average_file_size'][lang] = \
                        metrics['lines_of_code_by_language'][lang] / metrics['files_by_language'][lang]
            
            # Find largest files
            sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)
            metrics['largest_files'] = sorted_files[:10]
            
            # Calculate code churn from commits
            for commit in Repository(repo_path).traverse_commits():
                month = commit.committer_date.strftime('%Y-%m')
                commit_churn = commit.insertions + commit.deletions
                
                metrics['code_churn']['total_churn'] += commit_churn
                metrics['code_churn']['churn_by_month'][month] = \
                    metrics['code_churn']['churn_by_month'].get(month, 0) + commit_churn
                
                # Track churn by file
                for file in commit.modified_files:
                    if file.filename:
                        file_churn = (file.added_lines or 0) + (file.deleted_lines or 0)
                        churn_by_file[file.filename] = churn_by_file.get(file.filename, 0) + file_churn
            
            # Find high churn files
            sorted_churn = sorted(churn_by_file.items(), key=lambda x: x[1], reverse=True)
            metrics['code_churn']['high_churn_files'] = sorted_churn[:10]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate code metrics: {e}")
            return {}
    
    def _calculate_contributor_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate contributor-related metrics"""
        try:
            metrics = {
                'contributor_activity': {},
                'top_contributors': [],
                'contributor_diversity': {
                    'unique_contributors': 0,
                    'contributors_per_month': {},
                    'new_contributors_per_month': {}
                },
                'collaboration_metrics': {
                    'files_touched_by_multiple_contributors': 0,
                    'average_contributors_per_file': 0
                }
            }
            
            contributor_stats = {}
            monthly_contributors = {}
            file_contributors = {}
            seen_contributors = set()
            
            for commit in Repository(repo_path).traverse_commits():
                author = commit.author.email
                month = commit.committer_date.strftime('%Y-%m')
                
                # Track overall contributor stats
                if author not in contributor_stats:
                    contributor_stats[author] = {
                        'name': commit.author.name,
                        'email': author,
                        'commits': 0,
                        'insertions': 0,
                        'deletions': 0,
                        'files_modified': set(),
                        'first_commit': commit.committer_date,
                        'last_commit': commit.committer_date
                    }
                
                stats = contributor_stats[author]
                stats['commits'] += 1
                stats['insertions'] += commit.insertions
                stats['deletions'] += commit.deletions
                
                # Update commit dates
                if commit.committer_date < stats['first_commit']:
                    stats['first_commit'] = commit.committer_date
                if commit.committer_date > stats['last_commit']:
                    stats['last_commit'] = commit.committer_date
                
                # Track monthly activity
                if month not in monthly_contributors:
                    monthly_contributors[month] = set()
                monthly_contributors[month].add(author)
                
                # Track new contributors
                if author not in seen_contributors:
                    seen_contributors.add(author)
                    if month not in metrics['contributor_diversity']['new_contributors_per_month']:
                        metrics['contributor_diversity']['new_contributors_per_month'][month] = 0
                    metrics['contributor_diversity']['new_contributors_per_month'][month] += 1
                
                # Track file contributors
                for file in commit.modified_files:
                    if file.filename:
                        stats['files_modified'].add(file.filename)
                        
                        if file.filename not in file_contributors:
                            file_contributors[file.filename] = set()
                        file_contributors[file.filename].add(author)
            
            # Process contributor stats
            for stats in contributor_stats.values():
                stats['files_modified'] = len(stats['files_modified'])
                stats['first_commit'] = stats['first_commit'].isoformat()
                stats['last_commit'] = stats['last_commit'].isoformat()
            
            # Sort contributors by activity
            sorted_contributors = sorted(
                contributor_stats.values(),
                key=lambda x: x['commits'],
                reverse=True
            )
            
            metrics['contributor_activity'] = contributor_stats
            metrics['top_contributors'] = sorted_contributors[:10]
            metrics['contributor_diversity']['unique_contributors'] = len(contributor_stats)
            
            # Calculate monthly contributor counts
            for month, contributors in monthly_contributors.items():
                metrics['contributor_diversity']['contributors_per_month'][month] = len(contributors)
            
            # Calculate collaboration metrics
            multi_contributor_files = sum(1 for contributors in file_contributors.values() if len(contributors) > 1)
            metrics['collaboration_metrics']['files_touched_by_multiple_contributors'] = multi_contributor_files
            
            if file_contributors:
                avg_contributors = sum(len(contributors) for contributors in file_contributors.values()) / len(file_contributors)
                metrics['collaboration_metrics']['average_contributors_per_file'] = round(avg_contributors, 2)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate contributor metrics: {e}")
            return {}
    
    def _calculate_time_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate time-based metrics"""
        try:
            metrics = {
                'commit_frequency': {
                    'commits_per_day': {},
                    'commits_per_week': {},
                    'commits_per_month': {},
                    'average_commits_per_day': 0
                },
                'development_velocity': {
                    'lines_per_day': {},
                    'files_per_day': {},
                    'average_velocity': 0
                },
                'release_metrics': {
                    'time_between_releases': [],
                    'commits_between_releases': []
                }
            }
            
            daily_commits = {}
            daily_lines = {}
            daily_files = {}
            
            commits_list = []
            for commit in Repository(repo_path).traverse_commits():
                commits_list.append(commit)
                
                day = commit.committer_date.strftime('%Y-%m-%d')
                week = commit.committer_date.strftime('%Y-W%U')
                month = commit.committer_date.strftime('%Y-%m')
                
                # Count commits
                daily_commits[day] = daily_commits.get(day, 0) + 1
                metrics['commit_frequency']['commits_per_week'][week] = \
                    metrics['commit_frequency']['commits_per_week'].get(week, 0) + 1
                metrics['commit_frequency']['commits_per_month'][month] = \
                    metrics['commit_frequency']['commits_per_month'].get(month, 0) + 1
                
                # Count lines and files
                daily_lines[day] = daily_lines.get(day, 0) + commit.insertions + commit.deletions
                daily_files[day] = daily_files.get(day, 0) + commit.files
            
            # Calculate averages
            if daily_commits:
                total_days = len(daily_commits)
                total_commits = sum(daily_commits.values())
                metrics['commit_frequency']['average_commits_per_day'] = total_commits / total_days
                
                total_lines = sum(daily_lines.values())
                metrics['development_velocity']['average_velocity'] = total_lines / total_days
            
            metrics['commit_frequency']['commits_per_day'] = daily_commits
            metrics['development_velocity']['lines_per_day'] = daily_lines
            metrics['development_velocity']['files_per_day'] = daily_files
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate time metrics: {e}")
            return {}
    
    def _calculate_quality_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate code quality metrics"""
        try:
            metrics = {
                'bug_metrics': {
                    'total_bug_fixes': 0,
                    'bug_fix_commits': [],
                    'bugs_per_month': {},
                    'bug_prone_files': {}
                },
                'maintenance_metrics': {
                    'refactoring_commits': 0,
                    'documentation_commits': 0,
                    'test_commits': 0
                }
            }
            
            bug_keywords = ['fix', 'fixes', 'fixed', 'bug', 'issue', 'error', 'problem']
            refactor_keywords = ['refactor', 'refactoring', 'cleanup', 'clean up']
            doc_keywords = ['doc', 'documentation', 'readme', 'comment']
            test_keywords = ['test', 'testing', 'spec', 'unit test']
            
            for commit in Repository(repo_path).traverse_commits():
                message_lower = commit.msg.lower()
                month = commit.committer_date.strftime('%Y-%m')
                
                # Check for bug fixes
                if any(keyword in message_lower for keyword in bug_keywords):
                    metrics['bug_metrics']['total_bug_fixes'] += 1
                    metrics['bug_metrics']['bug_fix_commits'].append({
                        'hash': commit.hash,
                        'message': commit.msg,
                        'date': commit.committer_date.isoformat(),
                        'author': commit.author.name
                    })
                    
                    metrics['bug_metrics']['bugs_per_month'][month] = \
                        metrics['bug_metrics']['bugs_per_month'].get(month, 0) + 1
                    
                    # Track bug-prone files
                    for file in commit.modified_files:
                        if file.filename:
                            metrics['bug_metrics']['bug_prone_files'][file.filename] = \
                                metrics['bug_metrics']['bug_prone_files'].get(file.filename, 0) + 1
                
                # Check for other types of commits
                if any(keyword in message_lower for keyword in refactor_keywords):
                    metrics['maintenance_metrics']['refactoring_commits'] += 1
                
                if any(keyword in message_lower for keyword in doc_keywords):
                    metrics['maintenance_metrics']['documentation_commits'] += 1
                
                if any(keyword in message_lower for keyword in test_keywords):
                    metrics['maintenance_metrics']['test_commits'] += 1
            
            # Sort bug-prone files
            sorted_bug_files = sorted(
                metrics['bug_metrics']['bug_prone_files'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            metrics['bug_metrics']['bug_prone_files'] = dict(sorted_bug_files[:10])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate quality metrics: {e}")
            return {}
    
    def _calculate_testing_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate testing-related metrics"""
        try:
            metrics = {
                'test_coverage': {
                    'test_files': 0,
                    'source_files': 0,
                    'test_to_source_ratio': 0
                },
                'test_patterns': {
                    'unit_tests': 0,
                    'integration_tests': 0,
                    'test_frameworks': set()
                },
                'test_evolution': {
                    'test_commits': 0,
                    'test_lines_added': 0,
                    'test_files_modified': set()
                }
            }
            
            test_file_patterns = [
                'test', 'spec', 'tests', '__test__', '__tests__',
                '.test.', '.spec.', 'Test.java', 'Tests.java'
            ]
            
            test_frameworks = {
                'junit': ['junit', '@Test', 'org.junit'],
                'testng': ['testng', '@Test', 'org.testng'],
                'mockito': ['mockito', 'mock', 'Mockito'],
                'pytest': ['pytest', 'test_', 'def test'],
                'jest': ['jest', 'describe(', 'it(', 'expect('],
                'mocha': ['mocha', 'describe(', 'it('],
                'rspec': ['rspec', 'describe ', 'it '],
                'gtest': ['gtest', 'TEST(', 'TEST_F(']
            }
            
            # Analyze current files
            for root, dirs, files in os.walk(repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    if self._is_source_file(file):
                        filepath = os.path.join(root, file)
                        
                        # Check if it's a test file
                        is_test_file = any(pattern in file.lower() for pattern in test_file_patterns)
                        
                        if is_test_file:
                            metrics['test_coverage']['test_files'] += 1
                            
                            # Check for test frameworks
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    
                                for framework, patterns in test_frameworks.items():
                                    if any(pattern in content for pattern in patterns):
                                        metrics['test_patterns']['test_frameworks'].add(framework)
                                        
                                # Count test types
                                if any(pattern in content.lower() for pattern in ['unit', 'unittest']):
                                    metrics['test_patterns']['unit_tests'] += 1
                                if any(pattern in content.lower() for pattern in ['integration', 'e2e', 'end to end']):
                                    metrics['test_patterns']['integration_tests'] += 1
                                    
                            except Exception:
                                continue
                        else:
                            metrics['test_coverage']['source_files'] += 1
            
            # Calculate test-to-source ratio
            if metrics['test_coverage']['source_files'] > 0:
                metrics['test_coverage']['test_to_source_ratio'] = \
                    metrics['test_coverage']['test_files'] / metrics['test_coverage']['source_files']
            
            # Analyze test evolution from commits
            for commit in Repository(repo_path).traverse_commits():
                # Check if commit modifies test files
                test_related = False
                for file in commit.modified_files:
                    if file.filename and any(pattern in file.filename.lower() for pattern in test_file_patterns):
                        test_related = True
                        metrics['test_evolution']['test_files_modified'].add(file.filename)
                        metrics['test_evolution']['test_lines_added'] += file.added_lines or 0
                
                if test_related or any(keyword in commit.msg.lower() for keyword in ['test', 'testing', 'spec']):
                    metrics['test_evolution']['test_commits'] += 1
            
            # Convert set to count
            metrics['test_evolution']['test_files_modified'] = len(metrics['test_evolution']['test_files_modified'])
            metrics['test_patterns']['test_frameworks'] = list(metrics['test_patterns']['test_frameworks'])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate testing metrics: {e}")
            return {}
    
    def _calculate_complexity_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Calculate complexity metrics"""
        try:
            metrics = {
                'file_complexity': {},
                'complexity_trends': {},
                'high_complexity_files': [],
                'complexity_by_language': {}
            }
            
            # This is a simplified complexity calculation
            # In a full implementation, you would use tools like:
            # - radon for Python
            # - eslint for JavaScript
            # - checkstyle for Java
            
            for root, dirs, files in os.walk(repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    if self._is_source_file(file):
                        filepath = os.path.join(root, file)
                        relative_path = os.path.relpath(filepath, repo_path)
                        
                        try:
                            complexity = self._calculate_file_complexity(filepath)
                            if complexity > 0:
                                metrics['file_complexity'][relative_path] = complexity
                                
                                ext = os.path.splitext(file)[1].lower()
                                lang = self._get_language_from_extension(ext)
                                
                                if lang not in metrics['complexity_by_language']:
                                    metrics['complexity_by_language'][lang] = []
                                metrics['complexity_by_language'][lang].append(complexity)
                                
                        except Exception:
                            continue
            
            # Find high complexity files
            sorted_complexity = sorted(
                metrics['file_complexity'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            metrics['high_complexity_files'] = sorted_complexity[:10]
            
            # Calculate average complexity by language
            for lang, complexities in metrics['complexity_by_language'].items():
                if complexities:
                    metrics['complexity_by_language'][lang] = {
                        'average': sum(complexities) / len(complexities),
                        'max': max(complexities),
                        'min': min(complexities),
                        'count': len(complexities)
                    }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate complexity metrics: {e}")
            return {}
    
    def _calculate_file_complexity(self, filepath: str) -> int:
        """Calculate simple complexity metric for a file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple complexity heuristics
            complexity = 0
            
            # Count control flow statements
            control_keywords = ['if', 'else', 'elif', 'while', 'for', 'switch', 'case', 'try', 'catch', 'finally']
            for keyword in control_keywords:
                complexity += content.count(keyword)
            
            # Count nested braces (approximate nesting)
            brace_depth = 0
            max_depth = 0
            for char in content:
                if char == '{':
                    brace_depth += 1
                    max_depth = max(max_depth, brace_depth)
                elif char == '}':
                    brace_depth -= 1
            
            complexity += max_depth * 2
            
            # Count lines of code (exclude comments and empty lines)
            lines = content.split('\n')
            loc = 0
            for line in lines:
                line = line.strip()
                if line and not line.startswith('//') and not line.startswith('#') and not line.startswith('*'):
                    loc += 1
            
            # Complexity increases with file size
            complexity += loc // 50
            
            return complexity
            
        except Exception:
            return 0
    
    def _save_metrics(self, repo_path: str, metrics: Dict[str, Any]):
        """Save metrics to file"""
        try:
            metrics_file = f'.repochat_metrics_{os.path.basename(repo_path)}.json'
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Could not save metrics: {e}")
    
    def get_metrics_summary(self, repo_path: str) -> str:
        """Get formatted metrics summary"""
        if repo_path not in self.metrics_cache:
            return "❌ No metrics available. Run ingestion first."
        
        metrics = self.metrics_cache[repo_path]
        
        summary = "📊 **Repository Metrics Summary**\n\n"
        
        # Basic stats
        basic = metrics.get('basic_stats', {})
        summary += f"📝 **Total Commits:** {basic.get('total_commits', 0)}\n"
        summary += f"👥 **Contributors:** {basic.get('total_contributors', 0)}\n"
        summary += f"📂 **Files Modified:** {basic.get('total_files', 0)}\n"
        summary += f"➕ **Lines Added:** {basic.get('total_lines_added', 0):,}\n"
        summary += f"➖ **Lines Deleted:** {basic.get('total_lines_deleted', 0):,}\n"
        summary += f"📅 **Repository Age:** {basic.get('repository_age_days', 0)} days\n\n"
        
        # Code metrics
        code = metrics.get('code_metrics', {})
        if 'lines_of_code_by_language' in code:
            summary += "💻 **Lines of Code by Language:**\n"
            for lang, loc in sorted(code['lines_of_code_by_language'].items(), key=lambda x: x[1], reverse=True):
                summary += f"   - {lang}: {loc:,} lines\n"
            summary += "\n"
        
        # Testing metrics
        testing = metrics.get('testing_metrics', {})
        if testing:
            test_coverage = testing.get('test_coverage', {})
            summary += f"🧪 **Test Coverage:**\n"
            summary += f"   - Test Files: {test_coverage.get('test_files', 0)}\n"
            summary += f"   - Source Files: {test_coverage.get('source_files', 0)}\n"
            summary += f"   - Test-to-Source Ratio: {test_coverage.get('test_to_source_ratio', 0):.2f}\n\n"
        
        # Quality metrics
        quality = metrics.get('quality_metrics', {})
        if quality:
            bug_metrics = quality.get('bug_metrics', {})
            summary += f"🐛 **Quality Metrics:**\n"
            summary += f"   - Total Bug Fixes: {bug_metrics.get('total_bug_fixes', 0)}\n"
            
            maintenance = quality.get('maintenance_metrics', {})
            summary += f"   - Refactoring Commits: {maintenance.get('refactoring_commits', 0)}\n"
            summary += f"   - Documentation Commits: {maintenance.get('documentation_commits', 0)}\n"
            summary += f"   - Test Commits: {maintenance.get('test_commits', 0)}\n"
        
        return summary
    
    # Helper methods
    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            '.java', '.py', '.js', '.ts', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.scala',
            '.sql', '.xml', '.json', '.yaml', '.yml', '.md', '.txt'
        }
        
        _, ext = os.path.splitext(filename)
        return ext.lower() in source_extensions
    
    def _get_language_from_extension(self, ext: str) -> str:
        """Get programming language from file extension"""
        language_map = {
            '.java': 'Java',
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sql': 'SQL',
            '.xml': 'XML',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown'
        }
        
        return language_map.get(ext.lower(), 'Other')