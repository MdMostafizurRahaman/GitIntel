"""
Intelligent Agentic Dataset Maker
==================================
Collects maximum possible metrics from GitHub repos and generates datasets
with both known and unknown/custom metrics using intelligent formula parsing.
"""

import os
import ast
import operator
import subprocess
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import re
from datetime import datetime
import math
import statistics


@dataclass
class MetricsCollector:
    """Collects all possible metrics from a git repository"""
    repo_path: Path
    collected_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Main method to collect all possible metrics"""
        print(f"Collecting metrics from: {self.repo_path}")
        
        # Git-based metrics
        self.collect_commit_metrics()
        self.collect_author_metrics()
        self.collect_file_change_metrics()
        self.collect_code_churn_metrics()
        
        # Code quality metrics
        self.collect_code_complexity_metrics()
        self.collect_loc_metrics()
        
        # Project structure metrics
        self.collect_project_structure_metrics()
        
        # Time-based metrics
        self.collect_temporal_metrics()
        
        # Bug/Defect related metrics (if possible)
        self.collect_bug_metrics()
        
        return self.collected_metrics
    
    def _run_git_command(self, cmd: List[str]) -> str:
        """Execute git command safely"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Git command failed: {e}")
            return ""
    
    def collect_commit_metrics(self):
        """Collect commit-related metrics"""
        # Total commits
        total_commits = self._run_git_command(['git', 'rev-list', '--all', '--count'])
        self.collected_metrics['total_commits'] = int(total_commits) if total_commits else 0
        
        # Commits in last 30 days, 90 days, 1 year
        for days in [30, 90, 365]:
            commits = self._run_git_command([
                'git', 'rev-list', '--all', '--count',
                f'--since={days}.days.ago'
            ])
            self.collected_metrics[f'commits_last_{days}_days'] = int(commits) if commits else 0
        
        # Average commit message length
        messages = self._run_git_command([
            'git', 'log', '--all', '--pretty=format:%s'
        ])
        if messages:
            msg_lengths = [len(m) for m in messages.split('\n') if m]
            self.collected_metrics['avg_commit_msg_length'] = statistics.mean(msg_lengths) if msg_lengths else 0
            self.collected_metrics['max_commit_msg_length'] = max(msg_lengths) if msg_lengths else 0
    
    def collect_author_metrics(self):
        """Collect author/contributor metrics"""
        # Unique authors
        authors = self._run_git_command([
            'git', 'log', '--all', '--format=%aN'
        ])
        unique_authors = set(authors.split('\n')) if authors else set()
        self.collected_metrics['total_authors'] = len(unique_authors) - 1  # Remove empty string
        
        # Authors in last 90 days
        recent_authors = self._run_git_command([
            'git', 'log', '--all', '--format=%aN', '--since=90.days.ago'
        ])
        recent_unique = set(recent_authors.split('\n')) if recent_authors else set()
        self.collected_metrics['active_authors_90_days'] = len(recent_unique) - 1
    
    def collect_file_change_metrics(self):
        """Collect file change metrics"""
        # Files changed per commit (average)
        files_changed = self._run_git_command([
            'git', 'log', '--all', '--pretty=format:', '--numstat'
        ])
        
        if files_changed:
            lines = [l for l in files_changed.split('\n') if l.strip()]
            commits_count = self.collected_metrics.get('total_commits', 1)
            self.collected_metrics['avg_files_per_commit'] = len(lines) / commits_count if commits_count > 0 else 0
        
        # Total files in repo
        files = self._run_git_command(['git', 'ls-files'])
        file_list = [f for f in files.split('\n') if f.strip()]
        self.collected_metrics['total_files'] = len(file_list)
        
        # File types distribution
        extensions = {}
        for f in file_list:
            ext = Path(f).suffix or 'no_extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        self.collected_metrics['file_extensions'] = extensions
    
    def collect_code_churn_metrics(self):
        """Collect code churn metrics (lines added/deleted)"""
        stats = self._run_git_command([
            'git', 'log', '--all', '--numstat', '--pretty=format:'
        ])
        
        total_additions = 0
        total_deletions = 0
        
        if stats:
            for line in stats.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        total_additions += int(parts[0])
                        total_deletions += int(parts[1])
        
        self.collected_metrics['total_lines_added'] = total_additions
        self.collected_metrics['total_lines_deleted'] = total_deletions
        self.collected_metrics['net_lines'] = total_additions - total_deletions
        self.collected_metrics['code_churn'] = total_additions + total_deletions
    
    def collect_loc_metrics(self):
        """Collect Lines of Code metrics"""
        total_loc = 0
        code_files = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
            
            for file in files:
                # Focus on source code files
                if file.endswith(('.py', '.java', '.js', '.cpp', '.c', '.h', '.cs', '.rb', '.go')):
                    try:
                        file_path = Path(root) / file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            total_loc += len(lines)
                            code_files += 1
                    except:
                        pass
        
        self.collected_metrics['total_loc'] = total_loc
        self.collected_metrics['code_files_count'] = code_files
        self.collected_metrics['avg_loc_per_file'] = total_loc / code_files if code_files > 0 else 0
    
    def collect_code_complexity_metrics(self):
        """Collect complexity metrics (basic cyclomatic complexity estimation)"""
        # This is a simplified version - real complexity needs AST parsing
        complexity_keywords = ['if', 'else', 'elif', 'for', 'while', 'case', 'switch', '&&', '||', 'catch']
        total_complexity = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in root:
                continue
            
            for file in files:
                if file.endswith(('.py', '.java', '.js', '.cpp')):
                    try:
                        file_path = Path(root) / file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for keyword in complexity_keywords:
                                total_complexity += content.count(keyword)
                    except:
                        pass
        
        self.collected_metrics['estimated_complexity'] = total_complexity
        files = self.collected_metrics.get('code_files_count', 1)
        self.collected_metrics['avg_complexity_per_file'] = total_complexity / files if files > 0 else 0
    
    def collect_project_structure_metrics(self):
        """Collect project structure metrics"""
        directories = set()
        max_depth = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in root:
                continue
            
            rel_path = os.path.relpath(root, self.repo_path)
            directories.add(rel_path)
            depth = len(Path(rel_path).parts)
            max_depth = max(max_depth, depth)
        
        self.collected_metrics['total_directories'] = len(directories)
        self.collected_metrics['max_directory_depth'] = max_depth
    
    def collect_temporal_metrics(self):
        """Collect time-based metrics"""
        # First and last commit dates
        first_commit = self._run_git_command([
            'git', 'log', '--all', '--reverse', '--format=%ct', '-1'
        ])
        last_commit = self._run_git_command([
            'git', 'log', '--all', '--format=%ct', '-1'
        ])
        
        if first_commit and last_commit:
            first_date = datetime.fromtimestamp(int(first_commit))
            last_date = datetime.fromtimestamp(int(last_commit))
            
            project_age_days = (last_date - first_date).days
            self.collected_metrics['project_age_days'] = project_age_days
            self.collected_metrics['first_commit_date'] = first_date.isoformat()
            self.collected_metrics['last_commit_date'] = last_date.isoformat()
            
            # Commit frequency (commits per day)
            total_commits = self.collected_metrics.get('total_commits', 0)
            self.collected_metrics['commits_per_day'] = total_commits / project_age_days if project_age_days > 0 else 0
    
    def collect_bug_metrics(self):
        """Collect bug-related metrics from commit messages"""
        bug_keywords = ['fix', 'bug', 'issue', 'error', 'defect', 'patch']
        
        messages = self._run_git_command([
            'git', 'log', '--all', '--pretty=format:%s'
        ])
        
        bug_fix_commits = 0
        if messages:
            for msg in messages.split('\n'):
                if any(keyword in msg.lower() for keyword in bug_keywords):
                    bug_fix_commits += 1
        
        self.collected_metrics['bug_fix_commits'] = bug_fix_commits
        total_commits = self.collected_metrics.get('total_commits', 1)
        self.collected_metrics['bug_fix_ratio'] = bug_fix_commits / total_commits if total_commits > 0 else 0


class FormulaParser:
    """
    Intelligent formula parser that can evaluate custom metrics
    This is the KEY component for handling unknown metrics!
    """
    
    # Safe operators allowed in formulas
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # Safe functions
    SAFE_FUNCTIONS = {
        'abs': abs,
        'max': max,
        'min': min,
        'sum': sum,
        'len': len,
        'round': round,
        'sqrt': math.sqrt,
        'log': math.log,
        'exp': math.exp,
        'mean': statistics.mean,
        'median': statistics.median,
        'stdev': statistics.stdev,
    }
    
    def __init__(self, available_metrics: Dict[str, Any]):
        self.available_metrics = available_metrics
    
    def parse_and_evaluate(self, formula: str) -> Optional[float]:
        """
        Parse and safely evaluate a custom formula
        
        Examples:
        - "total_commits / project_age_days"
        - "code_churn / total_loc"
        - "(total_lines_added - total_lines_deleted) / total_commits"
        - "sqrt(estimated_complexity * avg_loc_per_file)"
        """
        try:
            # Replace metric names with their values
            formula_with_values = self._replace_metrics_in_formula(formula)
            
            # Parse the formula
            tree = ast.parse(formula_with_values, mode='eval')
            
            # Safely evaluate
            result = self._safe_eval(tree.body)
            
            return float(result) if result is not None else None
            
        except Exception as e:
            print(f"Formula evaluation error: {e}")
            return None
    
    def _replace_metrics_in_formula(self, formula: str) -> str:
        """Replace metric names with their actual values"""
        result = formula
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_metrics = sorted(self.available_metrics.keys(), key=len, reverse=True)
        
        for metric_name in sorted_metrics:
            if metric_name in result:
                value = self.available_metrics[metric_name]
                if isinstance(value, (int, float)):
                    result = result.replace(metric_name, str(value))
        
        return result
    
    def _safe_eval(self, node):
        """Safely evaluate AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in self.SAFE_FUNCTIONS:
                args = [self._safe_eval(arg) for arg in node.args]
                return self.SAFE_FUNCTIONS[func_name](*args)
        
        raise ValueError(f"Unsafe operation: {ast.dump(node)}")
    
    def suggest_available_metrics(self, partial_name: str) -> List[str]:
        """Suggest metrics based on partial name"""
        suggestions = [
            name for name in self.available_metrics.keys()
            if partial_name.lower() in name.lower()
        ]
        return suggestions
    
    def validate_formula(self, formula: str) -> tuple[bool, str]:
        """Validate if a formula can be evaluated"""
        try:
            # Extract metric names from formula
            tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula)
            
            missing_metrics = []
            for token in tokens:
                if token not in self.SAFE_FUNCTIONS and token not in self.available_metrics:
                    missing_metrics.append(token)
            
            if missing_metrics:
                return False, f"Missing metrics: {', '.join(missing_metrics)}"
            
            # Try to parse
            ast.parse(self._replace_metrics_in_formula(formula), mode='eval')
            return True, "Valid formula"
            
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Error: {e}"


class AgenticDatasetMaker:
    """
    Main agentic system that orchestrates everything
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("datasets")
        self.output_dir.mkdir(exist_ok=True)
        self.collected_data: List[Dict] = []
    
    def process_repository(self, repo_path: str) -> Dict[str, Any]:
        """Process a single repository and collect all metrics"""
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists():
            print(f"Repository not found: {repo_path}")
            return {}
        
        print(f"\nProcessing repository: {repo_path.name}")
        
        # Collect all metrics
        collector = MetricsCollector(repo_path)
        metrics = collector.collect_all_metrics()
        
        # Add repo metadata
        metrics['repo_name'] = repo_path.name
        metrics['repo_path'] = str(repo_path)
        
        print(f"Collected {len(metrics)} metrics")
        
        return metrics
    
    def add_custom_metrics(self, metrics: Dict[str, Any], custom_formulas: Dict[str, str]) -> Dict[str, Any]:
        """
        Add custom metrics using formulas
        This is where the magic happens for unknown metrics!
        """
        parser = FormulaParser(metrics)
        
        for metric_name, formula in custom_formulas.items():
            print(f"\nEvaluating custom metric: {metric_name}")
            print(f"   Formula: {formula}")
            
            # Validate first
            is_valid, message = parser.validate_formula(formula)
            if not is_valid:
                print(f"{message}")
                continue
            
            # Evaluate
            result = parser.parse_and_evaluate(formula)
            if result is not None:
                metrics[metric_name] = result
                print(f"Result: {result}")
            else:
                print(f"Could not evaluate")
        
        return metrics
    
    def generate_dataset(
        self,
        repo_paths: List[str],
        custom_formulas: Dict[str, str] = None,
        output_filename: str = "dataset.csv"
    ) -> pd.DataFrame:
        """
        Generate complete dataset from multiple repositories
        
        Args:
            repo_paths: List of git repository paths
            custom_formulas: Dictionary of custom metric formulas
            output_filename: Output CSV filename
        """
        print("\n" + "="*60)
        print("AGENTIC DATASET MAKER STARTING")
        print("="*60)
        
        all_metrics = []
        
        # Process each repository
        for repo_path in repo_paths:
            metrics = self.process_repository(repo_path)
            
            if metrics:
                # Add custom metrics if provided
                if custom_formulas:
                    metrics = self.add_custom_metrics(metrics, custom_formulas)
                
                all_metrics.append(metrics)
        
        # Create DataFrame
        df = pd.DataFrame(all_metrics)
        
        # Save to CSV
        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False)
        
        print(f"\nDataset generated: {output_path}")
        print(f"Total repositories: {len(all_metrics)}")
        print(f"Total metrics: {len(df.columns)}")
        
        return df
    
    def show_available_metrics(self, sample_repo: str):
        """Show all available metrics from a sample repository"""
        metrics = self.process_repository(sample_repo)
        
        print("\n" + "="*60)
        print("AVAILABLE METRICS")
        print("="*60)
        
        # Group metrics by category
        categories = {
            'Commit Metrics': [],
            'Author Metrics': [],
            'Code Metrics': [],
            'Structure Metrics': [],
            'Temporal Metrics': [],
            'Bug Metrics': [],
            'Other': []
        }
        
        for metric_name in sorted(metrics.keys()):
            if 'commit' in metric_name:
                categories['Commit Metrics'].append(metric_name)
            elif 'author' in metric_name:
                categories['Author Metrics'].append(metric_name)
            elif any(x in metric_name for x in ['loc', 'lines', 'churn', 'complexity']):
                categories['Code Metrics'].append(metric_name)
            elif any(x in metric_name for x in ['file', 'directory', 'depth']):
                categories['Structure Metrics'].append(metric_name)
            elif any(x in metric_name for x in ['date', 'age', 'days', 'per_day']):
                categories['Temporal Metrics'].append(metric_name)
            elif 'bug' in metric_name:
                categories['Bug Metrics'].append(metric_name)
            else:
                categories['Other'].append(metric_name)
        
        for category, metric_list in categories.items():
            if metric_list:
                print(f"\n{category}:")
                for m in metric_list:
                    print(f"  - {m}")
        
        return list(metrics.keys())


# Example usage and test function
def example_usage():
    """Example of how to use the system"""
    
    # Initialize the agentic dataset maker
    maker = AgenticDatasetMaker(output_dir=Path("d:/GitIntel/datasets"))
    
    # Show available metrics from a sample repo
    print("First, let's see what metrics we can collect:")
    available = maker.show_available_metrics("d:/GitIntel/repo")
    
    # Example 1: Generate dataset with known metrics only
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Dataset")
    print("="*60)
    
    df1 = maker.generate_dataset(
        repo_paths=[
            "d:/GitIntel/repo",
            # Add more repos here
        ],
        output_filename="basic_dataset.csv"
    )
    
    # Example 2: Generate dataset with custom formulas
    print("\n" + "="*60)
    print("EXAMPLE 2: Dataset with Custom Metrics")
    print("="*60)
    
    custom_formulas = {
        # Unknown/Custom metrics defined as formulas
        'churn_per_commit': 'code_churn / total_commits',
        'complexity_density': 'estimated_complexity / total_loc',
        'author_productivity': 'total_commits / total_authors',
        'bug_proneness': 'bug_fix_ratio * estimated_complexity',
        'activity_score': 'commits_last_30_days / project_age_days * 365',
        'code_growth_rate': 'net_lines / project_age_days',
    }
    
    df2 = maker.generate_dataset(
        repo_paths=[
            "d:/GitIntel/repo",
        ],
        custom_formulas=custom_formulas,
        output_filename="custom_metrics_dataset.csv"
    )
    
    print("\nAll done! Check the datasets folder.")


if __name__ == "__main__":
    example_usage()
