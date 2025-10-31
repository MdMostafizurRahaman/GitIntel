#!/usr/bin/env python3
"""
RepoChatCore - Core Conversational Q&A System for Repository Analysis
This module provides the foundational conversational intelligence for GitIntel
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import pickle

from pydriller import Repository
from git import Repo

class RepoChatCore:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_repo_path = None
        self.repo_metadata = {}
        self.state_file = ".repochat_state.json"
        
        # Load previous state if exists
        self.load_repository_state()
        
    def load_repository_state(self):
        """Load previously saved repository state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.current_repo_path = state.get('current_repo_path')
                    self.repo_metadata = state.get('repo_metadata', {})
                    
                if self.current_repo_path:
                    self.logger.info(f"Loaded repository state: {self.current_repo_path}")
        except Exception as e:
            self.logger.error(f"Failed to load repository state: {e}")
    
    def save_repository_state(self):
        """Save current repository state"""
        try:
            state = {
                'current_repo_path': self.current_repo_path,
                'repo_metadata': self.repo_metadata,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save repository state: {e}")
    
    def set_repository(self, repo_path: str) -> bool:
        """Set the current repository for analysis"""
        try:
            repo_path = os.path.abspath(repo_path)
            
            if not os.path.exists(repo_path):
                self.logger.error(f"Repository path does not exist: {repo_path}")
                return False
                
            if not os.path.exists(os.path.join(repo_path, '.git')):
                self.logger.error(f"Not a Git repository: {repo_path}")
                return False
            
            self.current_repo_path = repo_path
            self.logger.info(f"Repository set to: {repo_path}")
            
            # Extract basic metadata
            self.repo_metadata = self._extract_basic_metadata()
            
            # Save state
            self.save_repository_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set repository: {e}")
            return False
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract comprehensive repository metadata for knowledge graph"""
        if not self.current_repo_path:
            raise ValueError("No repository set")
        
        try:
            self.logger.info("Extracting repository metadata...")
            
            metadata = {
                'repository': self._extract_repository_info(),
                'commits': self._extract_commit_info(),
                'files': self._extract_file_info(),
                'contributors': self._extract_contributor_info(),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            self.repo_metadata.update(metadata)
            self.save_repository_state()
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            raise
    
    def _extract_basic_metadata(self) -> Dict[str, Any]:
        """Extract basic repository metadata"""
        try:
            repo = Repo(self.current_repo_path)
            
            metadata = {
                'path': self.current_repo_path,
                'name': os.path.basename(self.current_repo_path),
                'active_branch': repo.active_branch.name if repo.active_branch else 'main',
                'total_commits': len(list(repo.iter_commits())),
                'remotes': [remote.url for remote in repo.remotes],
                'last_updated': datetime.now().isoformat()
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract basic metadata: {e}")
            return {}
    
    def _extract_repository_info(self) -> Dict[str, Any]:
        """Extract repository-level information"""
        try:
            repo = Repo(self.current_repo_path)
            
            # Get repository statistics
            branches = [branch.name for branch in repo.branches]
            tags = [tag.name for tag in repo.tags]
            
            # Get remote information
            remotes = []
            for remote in repo.remotes:
                remotes.append({
                    'name': remote.name,
                    'url': remote.url
                })
            
            repo_info = {
                'name': os.path.basename(self.current_repo_path),
                'path': self.current_repo_path,
                'active_branch': repo.active_branch.name if repo.active_branch else 'main',
                'branches': branches,
                'tags': tags,
                'remotes': remotes,
                'total_commits': len(list(repo.iter_commits())),
                'size_mb': self._get_directory_size(self.current_repo_path) / (1024 * 1024)
            }
            
            return repo_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract repository info: {e}")
            return {}
    
    def _extract_commit_info(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Extract commit information using PyDriller"""
        try:
            commits = []
            commit_count = 0
            
            self.logger.info(f"Extracting commit information (limit: {limit})...")
            
            for commit in Repository(self.current_repo_path).traverse_commits():
                if commit_count >= limit:
                    break
                
                # Determine if it's a bug fix
                is_bug_fix = any(keyword in commit.msg.lower() 
                               for keyword in ['fix', 'bug', 'error', 'issue', 'patch'])
                
                # Calculate changes
                total_additions = sum(m.added_lines for m in commit.modified_files if m.added_lines)
                total_deletions = sum(m.deleted_lines for m in commit.modified_files if m.deleted_lines)
                
                commit_info = {
                    'hash': commit.hash,
                    'message': commit.msg,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'date': commit.author_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_bug_fix': is_bug_fix,
                    'modified_files_count': len(commit.modified_files),
                    'additions': total_additions,
                    'deletions': total_deletions,
                    'net_changes': total_additions - total_deletions
                }
                
                commits.append(commit_info)
                commit_count += 1
                
                if commit_count % 100 == 0:
                    self.logger.info(f"Processed {commit_count} commits...")
            
            self.logger.info(f"Extracted {len(commits)} commits")
            return commits
            
        except Exception as e:
            self.logger.error(f"Failed to extract commit info: {e}")
            return []
    
    def _extract_file_info(self) -> List[Dict[str, Any]]:
        """Extract file information from repository"""
        try:
            files = []
            
            self.logger.info("Extracting file information...")
            
            for root, dirs, filenames in os.walk(self.current_repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, self.current_repo_path)
                    
                    try:
                        # Get file statistics
                        stat = os.stat(file_path)
                        
                        # Determine file type and language
                        extension = os.path.splitext(filename)[1].lower()
                        language = self._get_language_from_extension(extension)
                        
                        # Count lines for text files
                        lines_of_code = 0
                        if language and self._is_text_file(file_path):
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines_of_code = len(f.readlines())
                            except:
                                pass
                        
                        file_info = {
                            'name': filename,
                            'path': relative_path,
                            'extension': extension,
                            'language': language,
                            'size_bytes': stat.st_size,
                            'lines_of_code': lines_of_code,
                            'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        files.append(file_info)
                        
                    except Exception as e:
                        self.logger.debug(f"Skipped file {file_path}: {e}")
                        continue
            
            self.logger.info(f"Extracted {len(files)} files")
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to extract file info: {e}")
            return []
    
    def _extract_contributor_info(self) -> List[Dict[str, Any]]:
        """Extract contributor information"""
        try:
            contributors = {}
            
            self.logger.info("Extracting contributor information...")
            
            for commit in Repository(self.current_repo_path).traverse_commits():
                author_name = commit.author.name
                author_email = commit.author.email
                
                # Use email as unique identifier
                if author_email not in contributors:
                    contributors[author_email] = {
                        'name': author_name,
                        'email': author_email,
                        'commits': 0,
                        'first_commit': commit.author_date,
                        'last_commit': commit.author_date,
                        'total_additions': 0,
                        'total_deletions': 0
                    }
                
                # Update contributor stats
                contributors[author_email]['commits'] += 1
                contributors[author_email]['last_commit'] = max(
                    contributors[author_email]['last_commit'], 
                    commit.author_date
                )
                contributors[author_email]['first_commit'] = min(
                    contributors[author_email]['first_commit'], 
                    commit.author_date
                )
                
                # Add file changes
                total_additions = sum(m.added_lines for m in commit.modified_files if m.added_lines)
                total_deletions = sum(m.deleted_lines for m in commit.modified_files if m.deleted_lines)
                
                contributors[author_email]['total_additions'] += total_additions
                contributors[author_email]['total_deletions'] += total_deletions
            
            # Convert to list and format dates
            contributor_list = []
            for contributor in contributors.values():
                contributor['first_commit'] = contributor['first_commit'].strftime('%Y-%m-%d %H:%M:%S')
                contributor['last_commit'] = contributor['last_commit'].strftime('%Y-%m-%d %H:%M:%S')
                contributor_list.append(contributor)
            
            # Sort by commit count
            contributor_list.sort(key=lambda x: x['commits'], reverse=True)
            
            self.logger.info(f"Extracted {len(contributor_list)} contributors")
            return contributor_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract contributor info: {e}")
            return []
    
    def _get_directory_size(self, directory: str) -> int:
        """Calculate directory size in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                # Skip .git directory
                if '.git' in dirpath:
                    continue
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
            return total_size
        except:
            return 0
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Determine programming language from file extension"""
        language_map = {
            '.py': 'Python',
            '.java': 'Java',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.swift': 'Swift',
            '.dart': 'Dart',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
            '.sql': 'SQL',
            '.xml': 'XML',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.txt': 'Text'
        }
        
        return language_map.get(extension, 'Unknown')
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file is a text file"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:
                    return False
            return True
        except:
            return False

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize RepoChatCore
    core = RepoChatCore()
    
    # Set repository (example)
    if len(os.sys.argv) > 1:
        repo_path = os.sys.argv[1]
        if core.set_repository(repo_path):
            print(f"✅ Repository set: {repo_path}")
            
            # Extract metadata
            metadata = core.extract_metadata()
            print(f"📊 Extracted metadata for {metadata['repository']['name']}")
            print(f"   - {len(metadata['commits'])} commits")
            print(f"   - {len(metadata['files'])} files")
            print(f"   - {len(metadata['contributors'])} contributors")
        else:
            print(f"❌ Failed to set repository: {repo_path}")
    else:
        print("Usage: python repochat_core.py <repo_path>")