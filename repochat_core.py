#!/usr/bin/env python3
"""
RepoChat Core - Repository Analysis and Management
"""

import os
import git
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydriller import Repository
import logging

class RepoChatCore:
    def __init__(self):
        self.current_repo_path = None
        self.repo_metadata = {}
        self.logger = logging.getLogger(__name__)
        
        # Load saved repository state
        self.load_repository_state()
    
    def load_repository_state(self):
        """Load previously saved repository state"""
        try:
            if os.path.exists('.repochat_state.json'):
                with open('.repochat_state.json', 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    repo_path = state.get('current_repo_path')
                    if repo_path and os.path.exists(repo_path):
                        self.current_repo_path = repo_path
                        print(f"📂 Loaded repository: {repo_path}")
        except Exception as e:
            self.logger.warning(f"Could not load repository state: {e}")
    
    def save_repository_state(self):
        """Save current repository state"""
        try:
            state = {
                'current_repo_path': self.current_repo_path,
                'last_updated': datetime.now().isoformat()
            }
            with open('.repochat_state.json', 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save repository state: {e}")
    
    def set_repository(self, repo_path: str) -> bool:
        """Set the current repository for analysis"""
        try:
            repo_path = os.path.abspath(repo_path)
            
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            if not os.path.exists(os.path.join(repo_path, '.git')):
                raise ValueError(f"Not a git repository: {repo_path}")
            
            self.current_repo_path = repo_path
            self.save_repository_state()
            
            # Extract basic metadata
            self.repo_metadata = self._extract_basic_metadata()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set repository: {e}")
            return False
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract comprehensive repository metadata for knowledge graph"""
        if not self.current_repo_path:
            raise ValueError("No repository set")
        
        metadata = {
            'repository': self._extract_repository_info(),
            'commits': self._extract_commit_info(),
            'files': self._extract_file_info(),
            'contributors': self._extract_contributor_info(),
            'issues': self._extract_issue_info(),
            'branches': self._extract_branch_info(),
            'tags': self._extract_tag_info()
        }
        
        return metadata
    
    def _extract_basic_metadata(self) -> Dict[str, Any]:
        """Extract basic repository metadata"""
        try:
            repo = git.Repo(self.current_repo_path)
            
            return {
                'name': os.path.basename(self.current_repo_path),
                'path': self.current_repo_path,
                'remote_url': self._get_remote_url(repo),
                'current_branch': repo.active_branch.name if repo.active_branch else 'main',
                'last_commit': repo.head.commit.hexsha[:8] if repo.head.commit else None,
                'last_commit_date': repo.head.commit.committed_datetime.isoformat() if repo.head.commit else None
            }
        except Exception as e:
            self.logger.warning(f"Could not extract basic metadata: {e}")
            return {'name': os.path.basename(self.current_repo_path or ''), 'path': self.current_repo_path}
    
    def _extract_repository_info(self) -> Dict[str, Any]:
        """Extract repository-level information"""
        try:
            repo = git.Repo(self.current_repo_path)
            
            return {
                'name': os.path.basename(self.current_repo_path),
                'path': self.current_repo_path,
                'remote_url': self._get_remote_url(repo),
                'description': self._get_repository_description(),
                'language': self._detect_primary_language(),
                'created_date': self._get_first_commit_date(repo),
                'last_activity': repo.head.commit.committed_datetime.isoformat() if repo.head.commit else None,
                'total_commits': len(list(repo.iter_commits())),
                'total_branches': len(list(repo.branches)),
                'total_tags': len(list(repo.tags))
            }
        except Exception as e:
            self.logger.error(f"Failed to extract repository info: {e}")
            return {'name': os.path.basename(self.current_repo_path or ''), 'error': str(e)}
    
    def _extract_commit_info(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Extract commit information using PyDriller"""
        commits = []
        
        try:
            print(f"📊 Extracting commit information (limit: {limit})...")
            
            count = 0
            for commit in Repository(self.current_repo_path).traverse_commits():
                if count >= limit:
                    break
                
                # Extract modified files with metrics
                modified_files = []
                for file in commit.modified_files:
                    modified_files.append({
                        'filename': file.filename,
                        'old_path': file.old_path,
                        'new_path': file.new_path,
                        'change_type': file.change_type.name if file.change_type else 'UNKNOWN',
                        'added_lines': file.added_lines,
                        'deleted_lines': file.deleted_lines,
                        'nloc': file.nloc,
                        'complexity': file.complexity if hasattr(file, 'complexity') else None
                    })
                
                commit_info = {
                    'hash': commit.hash,
                    'message': commit.msg,
                    'author': {
                        'name': commit.author.name,
                        'email': commit.author.email
                    },
                    'committer': {
                        'name': commit.committer.name,
                        'email': commit.committer.email
                    },
                    'date': commit.committer_date.isoformat(),
                    'modified_files': modified_files,
                    'insertions': commit.insertions,
                    'deletions': commit.deletions,
                    'lines': commit.lines,
                    'files': commit.files,
                    'dmm_unit_size': commit.dmm_unit_size,
                    'dmm_unit_complexity': commit.dmm_unit_complexity,
                    'dmm_unit_interfacing': commit.dmm_unit_interfacing,
                    'is_merge': commit.merge,
                    'branches': list(commit.branches) if commit.branches else [],
                    'in_main_branch': commit.in_main_branch
                }
                
                # Check if this is a bug-fixing commit
                commit_info['is_bug_fix'] = self._is_bug_fixing_commit(commit.msg)
                
                commits.append(commit_info)
                count += 1
                
                if count % 100 == 0:
                    print(f"   📈 Processed {count} commits...")
            
            print(f"✅ Extracted {len(commits)} commits")
            return commits
            
        except Exception as e:
            self.logger.error(f"Failed to extract commit info: {e}")
            return []
    
    def _extract_file_info(self) -> List[Dict[str, Any]]:
        """Extract file information from repository"""
        files = []
        
        try:
            print("📂 Extracting file information...")
            
            for root, dirs, filenames in os.walk(self.current_repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, self.current_repo_path)
                    
                    # Skip binary files and common non-source files
                    if self._is_source_file(filename):
                        file_info = {
                            'path': relative_path,
                            'absolute_path': filepath,
                            'name': filename,
                            'extension': os.path.splitext(filename)[1],
                            'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                            'language': self._detect_file_language(filename),
                            'lines_of_code': self._count_lines_of_code(filepath),
                            'last_modified': os.path.getmtime(filepath) if os.path.exists(filepath) else None
                        }
                        
                        files.append(file_info)
            
            print(f"✅ Extracted {len(files)} files")
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to extract file info: {e}")
            return []
    
    def _extract_contributor_info(self) -> List[Dict[str, Any]]:
        """Extract contributor information"""
        contributors = {}
        
        try:
            print("👥 Extracting contributor information...")
            
            for commit in Repository(self.current_repo_path).traverse_commits():
                author_email = commit.author.email
                
                if author_email not in contributors:
                    contributors[author_email] = {
                        'name': commit.author.name,
                        'email': author_email,
                        'commits': 0,
                        'insertions': 0,
                        'deletions': 0,
                        'files_modified': set(),
                        'first_commit': commit.committer_date.isoformat(),
                        'last_commit': commit.committer_date.isoformat()
                    }
                
                contributor = contributors[author_email]
                contributor['commits'] += 1
                contributor['insertions'] += commit.insertions
                contributor['deletions'] += commit.deletions
                contributor['files_modified'].update([f.filename for f in commit.modified_files if f.filename])
                
                # Update first and last commit dates
                commit_date = commit.committer_date.isoformat()
                if commit_date < contributor['first_commit']:
                    contributor['first_commit'] = commit_date
                if commit_date > contributor['last_commit']:
                    contributor['last_commit'] = commit_date
            
            # Convert sets to lists for JSON serialization
            for contributor in contributors.values():
                contributor['files_modified'] = list(contributor['files_modified'])
                contributor['total_files_modified'] = len(contributor['files_modified'])
            
            contributor_list = list(contributors.values())
            print(f"✅ Extracted {len(contributor_list)} contributors")
            return contributor_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract contributor info: {e}")
            return []
    
    def _extract_issue_info(self) -> List[Dict[str, Any]]:
        """Extract issue information (placeholder for future GitHub API integration)"""
        # This would integrate with GitHub API in a full implementation
        return []
    
    def _extract_branch_info(self) -> List[Dict[str, Any]]:
        """Extract branch information"""
        branches = []
        
        try:
            repo = git.Repo(self.current_repo_path)
            
            for branch in repo.branches:
                branch_info = {
                    'name': branch.name,
                    'last_commit': branch.commit.hexsha,
                    'last_commit_date': branch.commit.committed_datetime.isoformat(),
                    'author': branch.commit.author.name
                }
                branches.append(branch_info)
            
            return branches
            
        except Exception as e:
            self.logger.error(f"Failed to extract branch info: {e}")
            return []
    
    def _extract_tag_info(self) -> List[Dict[str, Any]]:
        """Extract tag information"""
        tags = []
        
        try:
            repo = git.Repo(self.current_repo_path)
            
            for tag in repo.tags:
                tag_info = {
                    'name': tag.name,
                    'commit': tag.commit.hexsha,
                    'date': tag.commit.committed_datetime.isoformat(),
                    'message': tag.tag.message if hasattr(tag, 'tag') and tag.tag else None
                }
                tags.append(tag_info)
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Failed to extract tag info: {e}")
            return []
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic repository statistics"""
        if not self.current_repo_path:
            return {}
        
        try:
            repo = git.Repo(self.current_repo_path)
            
            # Count commits
            commits = list(repo.iter_commits())
            
            # Count files
            total_files = 0
            for root, dirs, files in os.walk(self.current_repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                total_files += len([f for f in files if self._is_source_file(f)])
            
            # Count contributors
            contributors = set()
            for commit in Repository(self.current_repo_path).traverse_commits():
                contributors.add(commit.author.email)
            
            return {
                'commits': len(commits),
                'files': total_files,
                'contributors': len(contributors),
                'branches': len(list(repo.branches)),
                'tags': len(list(repo.tags))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get basic stats: {e}")
            return {}
    
    # Helper methods
    def _get_remote_url(self, repo) -> Optional[str]:
        """Get remote URL of the repository"""
        try:
            return repo.remotes.origin.url if repo.remotes else None
        except:
            return None
    
    def _get_repository_description(self) -> Optional[str]:
        """Get repository description from README or other files"""
        try:
            readme_files = ['README.md', 'README.txt', 'README', 'readme.md']
            for readme in readme_files:
                readme_path = os.path.join(self.current_repo_path, readme)
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(500)  # First 500 characters
                        return content.split('\n')[0]  # First line
            return None
        except:
            return None
    
    def _detect_primary_language(self) -> str:
        """Detect primary programming language"""
        language_counts = {}
        
        try:
            for root, dirs, files in os.walk(self.current_repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    lang = self._detect_file_language(file)
                    if lang != 'Unknown':
                        language_counts[lang] = language_counts.get(lang, 0) + 1
            
            if language_counts:
                return max(language_counts, key=language_counts.get)
            else:
                return 'Unknown'
                
        except:
            return 'Unknown'
    
    def _get_first_commit_date(self, repo) -> Optional[str]:
        """Get the date of the first commit"""
        try:
            commits = list(repo.iter_commits())
            if commits:
                return commits[-1].committed_datetime.isoformat()
            return None
        except:
            return None
    
    def _is_bug_fixing_commit(self, commit_message: str) -> bool:
        """Check if commit message indicates a bug fix"""
        bug_keywords = [
            'fix', 'fixes', 'fixed', 'bug', 'issue', 'error', 'problem',
            'resolve', 'resolves', 'resolved', 'correction', 'patch'
        ]
        
        message_lower = commit_message.lower()
        return any(keyword in message_lower for keyword in bug_keywords)
    
    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            '.java', '.py', '.js', '.ts', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.scala',
            '.sql', '.xml', '.json', '.yaml', '.yml', '.md', '.txt',
            '.properties', '.gradle', '.maven', '.pom'
        }
        
        _, ext = os.path.splitext(filename)
        return ext.lower() in source_extensions
    
    def _detect_file_language(self, filename: str) -> str:
        """Detect programming language from file extension"""
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
            '.md': 'Markdown',
            '.gradle': 'Gradle',
            '.properties': 'Properties'
        }
        
        _, ext = os.path.splitext(filename)
        return language_map.get(ext.lower(), 'Unknown')
    
    def _count_lines_of_code(self, filepath: str) -> int:
        """Count lines of code in a file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return len(f.readlines())
        except:
            return 0