#!/usr/bin/env python3
"""
Git Repository Analysis Tool with LLM Integration
=================================================

A comprehensive CLI tool for analyzing Git repositories with LLM-powered insights.
Supports package churn analysis, release analysis, and automated report generation.

Author: AI Assistant
Date: October 2025
"""

import argparse
import json
import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional
import logging
from neo4j import GraphDatabase

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitRepoAnalyzer:
    """Main class for Git repository analysis with LLM integration"""
    
    def __init__(self, repo_path: str, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_dir = self.repo_path / "analysis_output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Neo4j connection
        self.neo4j_driver = None
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 'Hello Neo4j!' as message")
                logger.info("✅ Connected to Neo4j database successfully!")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Neo4j: {e}")
                logger.info("💡 Make sure Neo4j Desktop is running and database is started")
        
        if not self._is_git_repo():
            raise ValueError(f"Not a valid Git repository: {repo_path}")
    
    def _is_git_repo(self) -> bool:
        """Check if the path is a valid Git repository"""
        return (self.repo_path / ".git").exists()
    
    def run_git_command(self, command: List[str]) -> str:
        """Execute a git command and return the output"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',  # Specify UTF-8 encoding
                errors='replace'   # Replace undecodable bytes
            )
            return result.stdout.strip() if result.stdout else ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            return ""
    
    def get_all_commits(self) -> List[Dict]:
        """Get all commits with metadata"""
        logger.info("Fetching all commits...")
        
        # Get commit hashes, dates, authors, and messages
        log_format = "--pretty=format:%H|%ad|%an|%s"
        output = self.run_git_command([
            "log", log_format, "--date=iso"
        ])
        
        commits = []
        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'date': parts[1],
                        'author': parts[2],
                        'message': parts[3]
                    })
        
        logger.info(f"Found {len(commits)} commits")
        return commits
    
    def get_releases_and_tags(self) -> List[Dict]:
        """Get all release tags and their information"""
        logger.info("Fetching release tags...")
        
        tags_output = self.run_git_command(["tag", "-l", "--sort=-version:refname"])
        tags = [tag.strip() for tag in tags_output.split('\n') if tag.strip()]
        
        releases = []
        for tag in tags:
            # Get tag information
            tag_info = self.run_git_command(["show", "--quiet", "--format=%H|%ad|%an|%s", tag])
            if '|' in tag_info:
                parts = tag_info.split('|', 3)
                if len(parts) == 4:
                    releases.append({
                        'tag': tag,
                        'hash': parts[0],
                        'date': parts[1],
                        'author': parts[2],
                        'message': parts[3]
                    })
        
        logger.info(f"Found {len(releases)} release tags")
        return releases
    
    def analyze_package_churn(self, threshold: int = 500) -> pd.DataFrame:
        """Analyze package-level code churn"""
        logger.info(f"Analyzing package churn with threshold: {threshold} lines")
        
        try:
            from pydriller import Repository
        except ImportError:
            logger.error("PyDriller not installed. Please install: pip install pydriller")
            return pd.DataFrame()
        
        package_data = []
        cumulative_churn = {}
        
        for commit in Repository(str(self.repo_path)).traverse_commits():
            commit_data = {
                'commit': commit.hash,
                'date': commit.author_date.isoformat(),
                'author': commit.author.name,
                'message': commit.msg.replace('\n', ' ')[:200]
            }
            
            for file_mod in commit.modified_files:
                if not file_mod.filename or not file_mod.filename.endswith('.java'):
                    continue
                
                # Extract package name
                package = self._extract_package_name(file_mod)
                
                added = file_mod.added_lines or 0
                removed = file_mod.deleted_lines or 0  # Fixed: was removed_lines
                churn = added + removed
                
                if churn == 0:
                    continue
                
                # Update cumulative churn
                if package not in cumulative_churn:
                    cumulative_churn[package] = {
                        'total_added': 0,
                        'total_removed': 0,
                        'total_churn': 0,
                        'commits': 0,
                        'files': set()
                    }
                
                cumulative_churn[package]['total_added'] += added
                cumulative_churn[package]['total_removed'] += removed
                cumulative_churn[package]['total_churn'] += churn
                cumulative_churn[package]['commits'] += 1
                cumulative_churn[package]['files'].add(file_mod.filename)
                
                # Store individual commit data
                package_data.append({
                    **commit_data,
                    'package': package,
                    'file': file_mod.filename,
                    'lines_added': added,
                    'lines_removed': removed,
                    'churn': churn
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(package_data)
        
        # Create summary for packages exceeding threshold
        high_churn_packages = []
        for package, data in cumulative_churn.items():
            if data['total_churn'] >= threshold:
                high_churn_packages.append({
                    'package': package,
                    'total_churn': data['total_churn'],
                    'total_added': data['total_added'],
                    'total_removed': data['total_removed'],
                    'commits_count': data['commits'],
                    'files_count': len(data['files']),
                    'avg_churn_per_commit': data['total_churn'] / data['commits'] if data['commits'] > 0 else 0
                })
        
        summary_df = pd.DataFrame(high_churn_packages)
        summary_df = summary_df.sort_values('total_churn', ascending=False)
        
        return df, summary_df
    
    def _extract_package_name(self, file_mod) -> str:
        """Extract package name from Java file modification"""
        # Try to get package from source code
        if file_mod.source_code:
            package_match = re.search(r'^\s*package\s+([a-zA-Z0-9_.]+)\s*;', 
                                    file_mod.source_code, re.MULTILINE)
            if package_match:
                return package_match.group(1)
        
        # Fallback to file path
        if file_mod.new_path or file_mod.old_path:
            path = file_mod.new_path or file_mod.old_path
            # Extract package from path structure
            parts = path.replace('\\', '/').split('/')
            if 'java' in parts:
                java_idx = parts.index('java')
                if java_idx + 1 < len(parts):
                    package_parts = parts[java_idx + 1:-1]  # exclude filename
                    if package_parts:
                        return '.'.join(package_parts)
        
        return 'unknown.package'
    
    def analyze_release_changes(self, from_tag: str = None, to_tag: str = None) -> Dict:
        """Analyze changes between releases"""
        logger.info(f"Analyzing changes between {from_tag} and {to_tag}")
        
        if from_tag and to_tag:
            diff_command = ["diff", "--stat", f"{from_tag}..{to_tag}"]
        elif to_tag:
            diff_command = ["diff", "--stat", f"HEAD~10..{to_tag}"]
        else:
            # Get changes from last 10 commits
            diff_command = ["diff", "--stat", "HEAD~10..HEAD"]
        
        diff_output = self.run_git_command(diff_command)
        
        # Parse diff output
        changes = {
            'files_changed': [],
            'total_insertions': 0,
            'total_deletions': 0,
            'summary': diff_output
        }
        
        for line in diff_output.split('\n'):
            if '|' in line and ('+' in line or '-' in line):
                parts = line.split('|')
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    changes_info = parts[1].strip()
                    
                    # Extract insertions and deletions
                    insertions = changes_info.count('+')
                    deletions = changes_info.count('-')
                    
                    changes['files_changed'].append({
                        'file': filename,
                        'insertions': insertions,
                        'deletions': deletions
                    })
                    
                    changes['total_insertions'] += insertions
                    changes['total_deletions'] += deletions
        
        return changes
    
    def generate_excel_report(self, churn_df: pd.DataFrame, summary_df: pd.DataFrame, 
                            releases_data: List[Dict] = None) -> str:
        """Generate comprehensive Excel report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = self.output_dir / f"{self.repo_name}_analysis_{timestamp}.xlsx"
        
        logger.info(f"Generating Excel report: {excel_file}")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Package churn summary
            if not summary_df.empty:
                summary_df.to_excel(writer, sheet_name='High_Churn_Packages', index=False)
            
            # Detailed churn data
            if not churn_df.empty:
                churn_df.to_excel(writer, sheet_name='Detailed_Churn', index=False)
            
            # Release information
            if releases_data:
                releases_df = pd.DataFrame(releases_data)
                releases_df.to_excel(writer, sheet_name='Releases', index=False)
            
            # Repository metadata
            metadata = {
                'Repository': [self.repo_name],
                'Analysis_Date': [datetime.now().isoformat()],
                'Total_Commits': [len(self.get_all_commits())],
                'Analysis_Threshold': [500]
            }
            pd.DataFrame(metadata).to_excel(writer, sheet_name='Metadata', index=False)
        
        return str(excel_file)
    
    def generate_llm_prompts(self, summary_df: pd.DataFrame, releases_data: List[Dict] = None) -> str:
        """Generate LLM prompts for further analysis"""
        prompts_file = self.output_dir / f"{self.repo_name}_llm_prompts.md"
        
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(f"# LLM Analysis Prompts for {self.repo_name}\n\n")
            f.write(f"Generated on: {datetime.now().isoformat()}\n\n")
            
            # High churn packages prompt
            if not summary_df.empty:
                f.write("## Prompt 1: Package Churn Analysis\n\n")
                f.write("```\n")
                f.write("Analyze these high-churn Java packages and provide insights:\n\n")
                
                for _, row in summary_df.head(10).iterrows():
                    f.write(f"Package: {row['package']}\n")
                    f.write(f"  - Total churn: {row['total_churn']} lines\n")
                    f.write(f"  - Files affected: {row['files_count']}\n")
                    f.write(f"  - Commits: {row['commits_count']}\n")
                    f.write(f"  - Avg churn/commit: {row['avg_churn_per_commit']:.1f}\n\n")
                
                f.write("Tasks:\n")
                f.write("1. Identify potential architectural issues\n")
                f.write("2. Suggest refactoring opportunities\n")
                f.write("3. Assess maintenance risks\n")
                f.write("4. Recommend monitoring strategies\n")
                f.write("```\n\n")
            
            # Release analysis prompt
            if releases_data:
                f.write("## Prompt 2: Release Analysis\n\n")
                f.write("```\n")
                f.write("Analyze the release history and suggest improvements:\n\n")
                
                for release in releases_data[:5]:
                    f.write(f"Release: {release['tag']}\n")
                    f.write(f"  - Date: {release['date']}\n")
                    f.write(f"  - Author: {release['author']}\n")
                    f.write(f"  - Message: {release['message']}\n\n")
                
                f.write("Tasks:\n")
                f.write("1. Analyze release frequency and patterns\n")
                f.write("2. Identify release management improvements\n")
                f.write("3. Suggest semantic versioning strategies\n")
                f.write("```\n\n")
        
        return str(prompts_file)
    
    def create_knowledge_graph(self, churn_df: pd.DataFrame, summary_df: pd.DataFrame, 
                              commits_data: List[Dict] = None) -> bool:
        """Create knowledge graph in Neo4j for repository analysis"""
        if not self.neo4j_driver:
            logger.warning("Neo4j not connected. Skipping knowledge graph creation.")
            return False
        
        logger.info("Creating knowledge graph in Neo4j...")
        
        try:
            with self.neo4j_driver.session() as session:
                # Clear existing data
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create repository node
                session.run(
                    "CREATE (r:Repository {name: $name, path: $path})",
                    name=self.repo_name, path=str(self.repo_path)
                )
                
                # Create author nodes and relationships
                authors = {}
                if not churn_df.empty:
                    for _, row in churn_df.iterrows():
                        author_name = row['author']
                        if author_name not in authors:
                            authors[author_name] = True
                            session.run(
                                "MERGE (a:Author {name: $name})",
                                name=author_name
                            )
                            # Connect author to repository
                            session.run(
                                "MATCH (a:Author {name: $name}), (r:Repository {name: $repo}) "
                                "CREATE (a)-[:CONTRIBUTES_TO]->(r)",
                                name=author_name, repo=self.repo_name
                            )
                
                # Create package nodes
                packages = {}
                if not summary_df.empty:
                    for _, row in summary_df.iterrows():
                        package_name = row['package']
                        if package_name not in packages:
                            packages[package_name] = True
                            session.run(
                                "MERGE (p:Package {name: $name, total_churn: $churn, files_count: $files, commits_count: $commits})",
                                name=package_name, churn=int(row['total_churn']), 
                                files=int(row['files_count']), commits=int(row['commits_count'])
                            )
                            # Connect package to repository
                            session.run(
                                "MATCH (p:Package {name: $name}), (r:Repository {name: $repo}) "
                                "CREATE (p)-[:BELONGS_TO]->(r)",
                                name=package_name, repo=self.repo_name
                            )
                
                # Create commit nodes and relationships
                if commits_data:
                    for commit in commits_data[:100]:  # Limit to avoid too many nodes
                        session.run(
                            "CREATE (c:Commit {hash: $hash, date: $date, message: $message})",
                            hash=commit['hash'], date=commit['date'], message=commit['message']
                        )
                        
                        # Connect commit to author
                        session.run(
                            "MATCH (c:Commit {hash: $hash}), (a:Author {name: $author}) "
                            "CREATE (a)-[:COMMITTED]->(c)",
                            hash=commit['hash'], author=commit['author']
                        )
                        
                        # Connect commit to repository
                        session.run(
                            "MATCH (c:Commit {hash: $hash}), (r:Repository {name: $repo}) "
                            "CREATE (c)-[:BELONGS_TO]->(r)",
                            hash=commit['hash'], repo=self.repo_name
                        )
                
                # Create file nodes and relationships from churn data
                files = {}
                if not churn_df.empty:
                    for _, row in churn_df.iterrows():
                        file_name = row['file']
                        if file_name not in files:
                            files[file_name] = True
                            session.run(
                                "MERGE (f:File {name: $name, package: $package})",
                                name=file_name, package=row['package']
                            )
                            
                            # Connect file to package
                            session.run(
                                "MATCH (f:File {name: $name}), (p:Package {name: $package}) "
                                "CREATE (f)-[:BELONGS_TO]->(p)",
                                name=file_name, package=row['package']
                            )
                
                logger.info("Knowledge graph created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create knowledge graph: {e}")
            return False
    
    def analyze_releases(self, repo_path, threshold=500):
        """Analyze changes between releases/tags"""
        
        try:
            from git import Repo
            import pandas as pd
            
            repo = Repo(repo_path)
            tags = list(repo.tags)
            
            if len(tags) < 2:
                # If no tags, analyze last 10 commits as "releases"
                commits = list(repo.iter_commits(max_count=10))
                releases_data = []
                
                for i, commit in enumerate(commits[:-1]):
                    next_commit = commits[i+1]
                    
                    release_info = {
                        'release_name': f"Commit-{commit.hexsha[:8]}",
                        'release_date': commit.committed_datetime.isoformat(),
                        'author': commit.author.name,
                        'message': commit.message.strip()[:100],
                        'total_files_changed': 0,
                        'total_lines_added': 0,
                        'total_lines_removed': 0,
                        'packages_affected': [],
                        'major_changes': []
                    }
                    
                    # Analyze diff between commits
                    try:
                        diff = next_commit.diff(commit)
                        for diff_item in diff:
                            if diff_item.a_path and diff_item.a_path.endswith('.java'):
                                lines_added = len([l for l in str(diff_item.diff, 'utf-8', errors='ignore').split('\n') if l.startswith('+')])
                                lines_removed = len([l for l in str(diff_item.diff, 'utf-8', errors='ignore').split('\n') if l.startswith('-')])
                                
                                release_info['total_files_changed'] += 1
                                release_info['total_lines_added'] += lines_added
                                release_info['total_lines_removed'] += lines_removed
                                
                                # Extract package info
                                package = self._extract_package_from_path(diff_item.a_path)
                                if package and package not in release_info['packages_affected']:
                                    release_info['packages_affected'].append(package)
                                    
                    except Exception as e:
                        print(f"Warning: Could not analyze diff for {commit.hexsha[:8]}: {e}")
                    
                    releases_data.append(release_info)
            else:
                # Analyze actual tags/releases
                releases_data = []
                sorted_tags = sorted(tags, key=lambda t: t.commit.committed_datetime)
                
                for i, tag in enumerate(sorted_tags[1:], 1):
                    prev_tag = sorted_tags[i-1]
                    
                    release_info = {
                        'release_name': tag.name,
                        'release_date': tag.commit.committed_datetime.isoformat(),
                        'author': tag.commit.author.name,
                        'message': tag.commit.message.strip()[:100],
                        'total_files_changed': 0,
                        'total_lines_added': 0,
                        'total_lines_removed': 0,
                        'packages_affected': [],
                        'major_changes': []
                    }
                    
                    # Analyze changes between tags
                    commits_between = list(repo.iter_commits(f"{prev_tag.name}..{tag.name}"))
                    
                    for commit in commits_between:
                        try:
                            for modified_file in commit.stats.files:
                                if modified_file.endswith('.java'):
                                    file_stats = commit.stats.files[modified_file]
                                    release_info['total_files_changed'] += 1
                                    release_info['total_lines_added'] += file_stats['insertions']
                                    release_info['total_lines_removed'] += file_stats['deletions']
                                    
                                    package = self._extract_package_from_path(modified_file)
                                    if package and package not in release_info['packages_affected']:
                                        release_info['packages_affected'].append(package)
                        except Exception as e:
                            continue
                    
                    releases_data.append(release_info)
            
            # Filter releases that meet threshold
            significant_releases = []
            for release in releases_data:
                total_churn = release['total_lines_added'] + release['total_lines_removed']
                if total_churn >= threshold:
                    release['total_churn'] = total_churn
                    significant_releases.append(release)
            
            # Create Excel report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"release_analysis_{timestamp}.xlsx"
            
            # Prepare data for Excel
            excel_data = []
            for release in significant_releases:
                excel_data.append({
                    'Release Name': release['release_name'],
                    'Release Date': release['release_date'][:10],
                    'Author': release['author'],
                    'Message': release['message'],
                    'Files Changed': release['total_files_changed'],
                    'Lines Added': release['total_lines_added'],
                    'Lines Removed': release['total_lines_removed'],
                    'Total Churn': release['total_churn'],
                    'Packages Affected': ', '.join(release['packages_affected'][:5]),  # Top 5 packages
                    'Package Count': len(release['packages_affected'])
                })
            
            if excel_data:
                df = pd.DataFrame(excel_data)
                df.to_excel(excel_filename, index=False, engine='openpyxl')
                print(f"✅ Release analysis Excel created: {excel_filename}")
            
            return {
                'success': True,
                'excel_file': excel_filename,
                'total_releases': len(significant_releases),
                'data': significant_releases
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_ml_dataset(self, analysis_data):
        """Generate ML-ready dataset from analysis results"""
        
        try:
            import pandas as pd
            
            ml_features = []
            
            for item in analysis_data:
                features = {
                    'package_name': item.get('package', 'unknown'),
                    'package_depth': len(item.get('package', '').split('.')) if item.get('package') else 1,
                    'is_test_package': 'test' in item.get('package', '').lower(),
                    'lines_added': item.get('lines_added', 0),
                    'lines_removed': item.get('lines_removed', 0),
                    'total_churn': item.get('churn', 0),
                    'file_count': item.get('num_files', 0),
                    'churn_per_file': item.get('churn', 0) / max(item.get('num_files', 1), 1),
                    'has_high_churn': item.get('churn', 0) > 1000,
                    'change_type': self._classify_change_type(item),
                    'commit_count': item.get('commits', 1),
                    'avg_churn_per_commit': item.get('churn', 0) / max(item.get('commits', 1), 1)
                }
                ml_features.append(features)
            
            ml_df = pd.DataFrame(ml_features)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dataset_filename = f"ml_dataset_{timestamp}.csv"
            ml_df.to_csv(dataset_filename, index=False)
            
            print(f"🤖 ML Dataset created: {dataset_filename}")
            print(f"📊 Features: {len(ml_df.columns)}, Records: {len(ml_df)}")
            
            return dataset_filename
            
        except Exception as e:
            print(f"❌ Error creating ML dataset: {str(e)}")
            return None

    def _classify_change_type(self, item):
        """Classify change type based on heuristics"""
        
        package = item.get('package', '').lower()
        lines_added = item.get('lines_added', 0)
        lines_removed = item.get('lines_removed', 0)
        
        if 'test' in package:
            return 'TEST'
        elif lines_removed > lines_added * 1.5:
            return 'REFACTOR'
        elif lines_added > 2000:
            return 'MAJOR_FEATURE'
        elif lines_added > lines_removed * 2:
            return 'FEATURE'
        else:
            return 'MAINTENANCE'

    def _extract_package_from_path(self, file_path):
        """Extract package name from file path"""
        if not file_path:
            return None
            
        # Standard Java path patterns
        parts = file_path.replace('\\', '/').split('/')
        
        # Look for src/main/java or src/test/java patterns
        if 'java' in parts:
            try:
                java_idx = parts.index('java')
                package_parts = parts[java_idx + 1:-1]  # exclude filename
                if package_parts:
                    return '.'.join(package_parts)
            except (ValueError, IndexError):
                pass
        
        # Fallback to directory structure
        return '.'.join(parts[:-1]) if len(parts) > 1 else 'default'

def main():
    parser = argparse.ArgumentParser(description="Git Repository Analysis Tool with LLM Integration")
    parser.add_argument("repo_path", help="Path to the Git repository")
    parser.add_argument("--threshold", type=int, default=500, 
                       help="Line change threshold for package analysis (default: 500)")
    parser.add_argument("--output-excel", action="store_true", 
                       help="Generate Excel report")
    parser.add_argument("--analyze-releases", action="store_true",
                       help="Analyze release changes")
    parser.add_argument("--from-tag", help="Start tag for release analysis")
    parser.add_argument("--to-tag", help="End tag for release analysis")
    parser.add_argument("--clone-repo", help="Clone repository from URL before analysis")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687",
                       help="Neo4j database URI (default: bolt://localhost:7687)")
    parser.add_argument("--neo4j-user", default="neo4j",
                       help="Neo4j username (default: neo4j)")
    parser.add_argument("--neo4j-password", help="Neo4j password")
    parser.add_argument("--create-graph", action="store_true",
                       help="Create knowledge graph in Neo4j")
    
    args = parser.parse_args()
    
    try:
        # Clone repository if URL provided
        if args.clone_repo:
            logger.info(f"Cloning repository: {args.clone_repo}")
            repo_name = args.clone_repo.split('/')[-1].replace('.git', '')
            clone_path = Path.cwd() / repo_name
            
            subprocess.run([
                "git", "clone", args.clone_repo, str(clone_path)
            ], check=True)
            
            args.repo_path = str(clone_path)
        
        # Initialize analyzer with Neo4j if provided
        neo4j_params = {}
        if args.neo4j_password:
            neo4j_params = {
                'neo4j_uri': args.neo4j_uri,
                'neo4j_user': args.neo4j_user,
                'neo4j_password': args.neo4j_password
            }
        
        analyzer = GitRepoAnalyzer(args.repo_path, **neo4j_params)
        
        # Get commits data for graph
        commits_data = None
        if args.create_graph:
            commits_data = analyzer.get_all_commits()
        
        # Perform package churn analysis
        logger.info("Starting package churn analysis...")
        churn_df, summary_df = analyzer.analyze_package_churn(args.threshold)
        
        if summary_df.empty:
            logger.warning(f"No packages found exceeding {args.threshold} line threshold")
        else:
            logger.info(f"Found {len(summary_df)} packages exceeding threshold")
            print("\n🔥 HIGH CHURN PACKAGES:")
            print(summary_df.to_string(index=False))
        
        # Analyze releases if requested
        releases_data = None
        if args.analyze_releases:
            releases_data = analyzer.get_releases_and_tags()
            if releases_data:
                logger.info(f"Found {len(releases_data)} releases")
                print("\n📦 RELEASES:")
                for release in releases_data[:5]:
                    print(f"  {release['tag']} - {release['date']} - {release['message'][:50]}...")
            
            # Analyze changes between releases
            if args.from_tag or args.to_tag:
                changes = analyzer.analyze_release_changes(args.from_tag, args.to_tag)
                print(f"\n📊 CHANGES: {changes['total_insertions']} insertions, {changes['total_deletions']} deletions")
        
        # Generate Excel report if requested
        if args.output_excel:
            excel_file = analyzer.generate_excel_report(churn_df, summary_df, releases_data)
            logger.info(f"Excel report generated: {excel_file}")
        
        # Generate LLM prompts
        prompts_file = analyzer.generate_llm_prompts(summary_df, releases_data)
        logger.info(f"LLM prompts generated: {prompts_file}")
        
        # Create knowledge graph if requested
        if args.create_graph and analyzer.neo4j_driver:
            success = analyzer.create_knowledge_graph(churn_df, summary_df, commits_data)
            if success:
                print("\n🕸️ Knowledge graph created in Neo4j!")
            else:
                print("\n❌ Failed to create knowledge graph")
        
        print(f"\n✅ Analysis complete! Check {analyzer.output_dir} for outputs.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()