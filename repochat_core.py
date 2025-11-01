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
from dotenv import load_dotenv

from pydriller import Repository
from git import Repo

# Load environment variables
load_dotenv()

# Import Neo4j for knowledge graph
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
    print("✅ Neo4j available for knowledge graph")
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ Neo4j not available, using in-memory storage")

# ChromaDB not available - using Neo4j only
CHROMADB_AVAILABLE = False
print("ℹ️ Using Neo4j-only approach (no ChromaDB)")

# Import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
    print("✅ Google Generative AI available")
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ Google Generative AI not available")

class RepoChatCore:
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        self.logger = logging.getLogger(__name__)
        self.current_repo_path = None
        self.repo_metadata = {}
        self.state_file = ".repochat_state.json"
        
        # Get Neo4j credentials from environment
        self.neo4j_uri = neo4j_uri or os.getenv('NEO4J_URI')
        self.neo4j_user = neo4j_user if neo4j_user != "neo4j" else os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = neo4j_password if neo4j_password != "password" else os.getenv('NEO4J_PASSWORD')
        
        # Setup Gemini AI
        self.gemini_model = None
        if GENAI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')  # Use Pro model
                print("✅ Gemini AI configured (pro model)")
            else:
                print("⚠️ GEMINI_API_KEY not found in environment")
        
        # Initialize Neo4j connection
        self.neo4j_driver = None
        self.neo4j_ready = False
        
        if NEO4J_AVAILABLE and self.neo4j_uri:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    self.neo4j_uri, 
                    auth=(self.neo4j_user, self.neo4j_password)
                )
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 'Neo4j Connected!' as message")
                self.neo4j_ready = True
                self.logger.info("✅ Neo4j Aura connected successfully")
                print("✅ Neo4j Aura connected successfully")
                # Initialize schema
                self._initialize_neo4j_schema()
            except Exception as e:
                self.logger.warning(f"Neo4j connection failed: {e}")
                self.neo4j_ready = False
                print(f"⚠️ Neo4j connection failed: {e}")
        
        # Initialize ChromaDB - DISABLED (using Neo4j only)
        self.chroma_client = None
        self.chroma_collection = None
        self.embedding_function = None
        print("ℹ️ ChromaDB disabled - using Neo4j for all storage")
        
        # Load previous state if exists
        self.load_repository_state()
    
    def _initialize_neo4j_schema(self):
        """Initialize Neo4j schema for repository data"""
        if not self.neo4j_driver:
            return
        
        try:
            with self.neo4j_driver.session() as session:
                # Create constraints and indexes
                schema_queries = [
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE", 
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:Contributor) REQUIRE u.email IS UNIQUE",
                    "CREATE INDEX IF NOT EXISTS FOR (c:Commit) ON (c.date)",
                    "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.language)"
                ]
                
                for query in schema_queries:
                    try:
                        session.run(query)
                    except Exception as e:
                        self.logger.debug(f"Schema query might already exist: {e}")
                        
                self.logger.info("Neo4j schema initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Neo4j schema: {e}")
        
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
            
            # Initialize Neo4j knowledge graph for this repository
            if self.neo4j_ready:
                try:
                    self._initialize_neo4j_schema()
                    self.logger.info("Neo4j schema initialized")
                except Exception as e:
                    self.logger.warning(f"Neo4j schema initialization failed: {e}")
            
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
                'commits': self._extract_commit_info_fast(),
                'files': self._extract_file_info_fast(),
                'contributors': self._extract_contributor_info_fast(),
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
    
    def _extract_commit_info(self, limit: int = 1000, progress_callback=None) -> List[Dict[str, Any]]:
        """Extract commit information using PyDriller"""
        try:
            commits = []
            commit_count = 0
            
            self.logger.info(f"Extracting commit information (limit: {limit})...")
            
            # Handle None limit (process all commits)
            if limit is None:
                actual_limit = float('inf')  # No limit
                limit_desc = "all commits"
            else:
                actual_limit = limit
                limit_desc = f"{limit} commits"
            
            # Count total commits for progress reporting if we have a callback
            total_commits = 0
            if progress_callback:
                try:
                    self.logger.info("Counting total commits for progress tracking...")
                    for _ in Repository(self.current_repo_path).traverse_commits():
                        total_commits += 1
                        # For very large repos, limit counting to avoid long delays
                        if total_commits >= 50000:  # Reasonable upper limit for counting
                            break
                    self.logger.info(f"Found {total_commits} total commits")
                except Exception as e:
                    self.logger.warning(f"Could not count total commits: {e}")
                    total_commits = 0
            
            # Now extract commits with proper progress tracking
            commit_start_time = datetime.now()
            print(f"⏱️ Starting commit extraction at {commit_start_time.strftime('%H:%M:%S')}")
            
            for commit in Repository(self.current_repo_path).traverse_commits():
                if commit_count >= actual_limit:
                    break
                
                commit_start = datetime.now()
                
                # Determine if it's a bug fix
                is_bug_fix = any(keyword in commit.msg.lower() 
                               for keyword in ['fix', 'bug', 'error', 'issue', 'patch'])
                
                # Calculate changes (limit to first 100 files per commit for speed)
                modified_files = list(commit.modified_files)[:100]  # Limit files per commit
                total_additions = sum(m.added_lines for m in modified_files if m.added_lines)
                total_deletions = sum(m.deleted_lines for m in modified_files if m.deleted_lines)
                
                commit_info = {
                    'hash': commit.hash,
                    'message': commit.msg,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'date': commit.author_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_bug_fix': is_bug_fix,
                    'modified_files_count': len(modified_files),
                    'additions': total_additions,
                    'deletions': total_deletions,
                    'net_changes': total_additions - total_deletions
                }
                
                commits.append(commit_info)
                commit_count += 1
                
                commit_end = datetime.now()
                commit_duration = (commit_end - commit_start).total_seconds()
                
                # Provide progress updates
                if progress_callback and commit_count % 10 == 0:  # More frequent updates
                    if total_commits > 0 and total_commits < 50000:
                        # We have accurate count
                        progress_percent = min(100, int((commit_count / min(actual_limit, total_commits)) * 100))
                        progress_callback(40 + int(progress_percent * 0.2), 
                                        f"Analyzing commits... ({commit_count}/{min(actual_limit, total_commits)} processed, {commit_duration:.2f}s per commit)")
                    else:
                        # No accurate count, show incremental progress
                        progress_callback(40 + min(20, int((commit_count / max(actual_limit, 1000)) * 20)), 
                                        f"Analyzing commits... ({commit_count} processed, {commit_duration:.2f}s per commit)")
                
                if commit_count % 50 == 0:
                    batch_time = (datetime.now() - commit_start_time).total_seconds()
                    avg_time_per_commit = batch_time / commit_count
                    estimated_total = avg_time_per_commit * actual_limit
                    remaining = estimated_total - batch_time
                    print(f"📊 Processed {commit_count}/{actual_limit} commits in {batch_time:.1f}s (avg: {avg_time_per_commit:.2f}s/commit, est. remaining: {remaining:.1f}s)")
            
            total_commit_time = (datetime.now() - commit_start_time).total_seconds()
            print(f"✅ Commit extraction completed in {total_commit_time:.1f}s ({commit_count} commits, avg: {total_commit_time/commit_count:.2f}s per commit)")
            
            self.logger.info(f"Extracted {len(commits)} commits (limit: {limit_desc})")
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
                            'size': stat.st_size,
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
    
    def ask_question(self, question: str) -> str:
        """Answer questions about the repository using Neo4j knowledge graph"""
        try:
            if not self.current_repo_path:
                return "❌ No repository set. Please set a repository first."
            
            # Try Neo4j query first if available
            if self.neo4j_ready and self.neo4j_driver:
                try:
                    print("� Querying Neo4j knowledge graph...")
                    start_time = datetime.now()
                    
                    # Try Neo4j-based answer first
                    neo4j_response = self._answer_with_neo4j(question)
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"⚡ Neo4j response time: {elapsed:.2f}s")
                    
                    if neo4j_response and "❌" not in neo4j_response:
                        return neo4j_response
                except Exception as e:
                    self.logger.warning(f"Neo4j query failed: {e}")
            
            # Fallback to metadata-based response
            print("📊 Using metadata for response...")
            
            if not self.repo_metadata:
                # Extract metadata quickly (limited data for speed)
                self.repo_metadata = self._extract_metadata_fast()
                
                # Store in Neo4j if available
                if self.neo4j_ready:
                    self._store_metadata_in_neo4j(self.repo_metadata)
            
            question_lower = question.lower()
            
            # Simple pattern matching for common questions
            if any(word in question_lower for word in ['contributor', 'author', 'developer', 'কে', 'অবদানকারী']):
                return self._answer_contributor_question()
            elif any(word in question_lower for word in ['commit', 'change', 'recent', 'latest', 'কমিট']):
                return self._answer_commit_question()
            elif any(word in question_lower for word in ['file', 'complex', 'big', 'large', 'ফাইল', 'জটিল']):
                return self._answer_file_question()
            elif any(word in question_lower for word in ['overview', 'summary', 'about', 'সম্পর্কে', 'সারাংশ']):
                return self._answer_overview_question()
            else:
                return self._generate_fallback_response(question)
                
        except Exception as e:
            self.logger.error(f"Question processing failed: {e}")
            return f"❌ Error processing question: {e}"
    
    def _answer_with_neo4j(self, question: str) -> str:
        """Answer question using Neo4j knowledge graph"""
        try:
            if not self.neo4j_driver:
                return None
            
            question_lower = question.lower()
            
            with self.neo4j_driver.session() as session:
                # Contributors query
                if any(word in question_lower for word in ['contributor', 'author', 'developer', 'কে', 'অবদানকারী']):
                    query = """
                    MATCH (u:Contributor)-[r:AUTHORED]->(c:Commit)
                    RETURN u.name as name, u.email as email, count(c) as commits,
                           sum(r.additions) as total_additions, sum(r.deletions) as total_deletions
                    ORDER BY commits DESC LIMIT 10
                    """
                    result = session.run(query)
                    
                    response = "👥 **Top Contributors (from Neo4j):**\n\n"
                    for record in result:
                        response += f"• **{record['name']}** ({record['email']})\n"
                        response += f"  Commits: {record['commits']:,}, "
                        response += f"Added: {record['total_additions'] or 0:,}, "
                        response += f"Removed: {record['total_deletions'] or 0:,}\n\n"
                    
                    return response if "•" in response else None
                
                # Recent commits query
                elif any(word in question_lower for word in ['commit', 'change', 'recent', 'latest', 'কমিট']):
                    query = """
                    MATCH (c:Commit)-[:AUTHORED_BY]->(u:Contributor)
                    RETURN c.hash as hash, c.message as message, c.date as date, u.name as author
                    ORDER BY c.date DESC LIMIT 10
                    """
                    result = session.run(query)
                    
                    response = "📝 **Recent Commits (from Neo4j):**\n\n"
                    for record in result:
                        response += f"• **{record['hash'][:8]}** by {record['author']}\n"
                        response += f"  {record['date']}: {record['message'][:80]}...\n\n"
                    
                    return response if "•" in response else None
                
                # Files query
                elif any(word in question_lower for word in ['file', 'large', 'big', 'ফাইল']):
                    query = """
                    MATCH (f:File)
                    RETURN f.path as path, f.language as language, f.size as size
                    ORDER BY f.size DESC LIMIT 10
                    """
                    result = session.run(query)
                    
                    response = "� **Files (from Neo4j):**\n\n"
                    for record in result:
                        size_kb = (record['size'] or 0) / 1024
                        response += f"• **{record['path']}** ({record['language']})\n"
                        response += f"  Size: {size_kb:.1f} KB\n\n"
                    
                    return response if "•" in response else None
                
                # Overview query
                elif any(word in question_lower for word in ['overview', 'summary', 'about', 'সম্পর্কে']):
                    query = """
                    MATCH (r:Repository) 
                    OPTIONAL MATCH (c:Commit)
                    OPTIONAL MATCH (f:File)
                    OPTIONAL MATCH (u:Contributor)
                    RETURN r.name as repo_name, count(DISTINCT c) as total_commits,
                           count(DISTINCT f) as total_files, count(DISTINCT u) as total_contributors
                    """
                    result = session.run(query)
                    record = result.single()
                    
                    if record:
                        response = f"📊 **Repository Overview (from Neo4j):**\n\n"
                        response += f"• **Repository:** {record['repo_name']}\n"
                        response += f"• **Total Commits:** {record['total_commits']:,}\n"
                        response += f"• **Total Files:** {record['total_files']:,}\n"
                        response += f"• **Contributors:** {record['total_contributors']}\n"
                        return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Neo4j query failed: {e}")
            return None
    
    def _store_metadata_in_neo4j(self, metadata: Dict[str, Any]):
        """Store metadata in Neo4j knowledge graph"""
        try:
            if not self.neo4j_driver:
                return
            
            with self.neo4j_driver.session() as session:
                # Clear existing data for this repository
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create repository node
                repo_info = metadata.get('repository', {})
                session.run("""
                    CREATE (r:Repository {name: $name, path: $path, description: $desc})
                """, name=repo_info.get('name'), path=self.current_repo_path, 
                desc=repo_info.get('description', 'No description'))
                
                # Create contributor nodes and relationships
                contributors = metadata.get('contributors', [])
                for contrib in contributors:
                    session.run("""
                        MERGE (u:Contributor {email: $email})
                        SET u.name = $name
                    """, email=contrib['email'], name=contrib['name'])
                
                # Create commits and relationships
                commits = metadata.get('commits', [])
                for commit in commits:
                    session.run("""
                        MATCH (u:Contributor {email: $email})
                        CREATE (c:Commit {hash: $hash, message: $message, date: $date})
                        CREATE (u)-[:AUTHORED {additions: $additions, deletions: $deletions}]->(c)
                    """, email=commit['author_email'], hash=commit['hash'],
                    message=commit['message'], date=commit['date'],
                    additions=0, deletions=0)  # Simplified for speed
                
                # Create file nodes
                files = metadata.get('files', [])
                for file_info in files:
                    session.run("""
                        CREATE (f:File {path: $path, language: $language, size: $size})
                    """, path=file_info['path'], language=file_info['language'],
                    size=file_info.get('size', 0))
                
                self.logger.info("Metadata stored in Neo4j successfully")
                
        except Exception as e:
                self.logger.error(f"Failed to store metadata in Neo4j: {e}")
    
    def _extract_metadata_fast(self) -> Dict[str, Any]:
        """Extract metadata quickly for fast responses"""
        try:
            metadata = {
                'repository': self._extract_repository_info(),
                'commits': self._extract_commit_info_fast(),
                'files': self._extract_file_info_fast(),
                'contributors': self._extract_contributor_info_fast(),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Fast metadata extraction failed: {e}")
            return {}

    def _answer_contributor_question(self) -> str:
        """Answer questions about contributors"""
        contributors = self.repo_metadata.get('contributors', [])
        if not contributors:
            return "❌ No contributor data available."
        
        top_contributors = contributors[:5]  # Top 5 contributors
        response = "👥 **Top Contributors:**\n\n"
        
        for i, contrib in enumerate(top_contributors, 1):
            response += f"{i}. **{contrib['name']}** ({contrib['email']})\n"
            response += f"   • Commits: {contrib['commits']:,}\n"
            response += f"   • Lines Added: {contrib.get('total_additions', 0):,}\n"
            response += f"   • Lines Removed: {contrib.get('total_deletions', 0):,}\n"
            response += f"   • Active: {contrib['first_commit']} to {contrib['last_commit']}\n\n"
        
        return response
    
    def _answer_commit_question(self) -> str:
        """Answer questions about commits"""
        commits = self.repo_metadata.get('commits', [])
        if not commits:
            return "❌ No commit data available."
        
        recent_commits = commits[:10]  # Most recent 10 commits
        response = "📝 **Recent Commits:**\n\n"
        
        for commit in recent_commits:
            response += f"• **{commit['hash'][:8]}** by {commit['author']}\n"
            response += f"  {commit['date']}: {commit['message'][:80]}...\n\n"
        
        return response
    
    def _answer_file_question(self) -> str:
        """Answer questions about files"""
        files = self.repo_metadata.get('files', [])
        if not files:
            return "❌ No file data available."
        
        # Sort by size to find largest files
        large_files = sorted(files, key=lambda x: x.get('size', 0), reverse=True)[:10]
        
        response = "📁 **Largest Files:**\n\n"
        for file_info in large_files:
            size_kb = file_info.get('size', 0) / 1024
            response += f"• **{file_info['path']}** ({file_info['language']})\n"
            response += f"  Size: {size_kb:.1f} KB\n\n"
        
        return response
    
    def _answer_overview_question(self) -> str:
        """Answer overview questions about the repository"""
        repo_info = self.repo_metadata.get('repository', {})
        commits = self.repo_metadata.get('commits', [])
        files = self.repo_metadata.get('files', [])
        contributors = self.repo_metadata.get('contributors', [])
        
        response = f"📊 **Repository Overview: {repo_info.get('name', 'Unknown')}**\n\n"
        response += f"• **Total Commits:** {len(commits):,}\n"
        response += f"• **Total Files:** {len(files):,}\n"
        response += f"• **Contributors:** {len(contributors)}\n"
        response += f"• **Repository Size:** {repo_info.get('size_mb', 0):.1f} MB\n\n"
        
        # Language breakdown
        languages = {}
        for file_info in files:
            lang = file_info.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        if languages:
            response += "**Programming Languages:**\n"
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                response += f"• {lang}: {count} files\n"
        
        return response
    
    def _generate_fallback_response(self, question: str) -> str:
        """Generate a fallback response for unrecognized questions"""
        return f"🤔 I don't understand the question: '{question}'\n\n" + \
               "Try asking about:\n" + \
               "• Who are the top contributors?\n" + \
               "• Show me recent commits\n" + \
               "• What files are largest?\n" + \
               "• Give me an overview\n" + \
               "• কে সবচেয়ে বেশি অবদান রেখেছে? (Bengali)"

    def _extract_commit_info_fast(self, limit: int = 100) -> List[Dict]:
        """Extract commit information quickly (minimal data for speed)"""
        try:
            self.logger.info(f"Extracting commit info (fast mode, limit: {limit})...")
            
            commits = []
            repo = Repository(self.current_repo_path)
            
            commit_count = 0
            start_time = datetime.now()
            
            for commit in repo.traverse_commits():
                if commit_count >= limit:
                    break
                
                # Minimal data extraction for speed
                commit_info = {
                    'hash': commit.hash,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'date': commit.author_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': commit.msg.strip()[:200],  # Truncate long messages
                    'modified_files_count': len(list(commit.modified_files)[:10]),  # Quick count, limit to 10
                    'additions': 0,  # Skip expensive calculation
                    'deletions': 0,
                    'net_changes': 0,
                    'is_bug_fix': 'fix' in commit.msg.lower() or 'bug' in commit.msg.lower()
                }
                
                commits.append(commit_info)
                commit_count += 1
                
                if commit_count % 25 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"🚀 Fast mode: {commit_count}/{limit} commits in {elapsed:.1f}s (avg: {elapsed/commit_count:.2f}s/commit)")
            
            total_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Fast commit extraction: {len(commits)} commits in {total_time:.1f}s")
            return commits
            
        except Exception as e:
            self.logger.error(f"Failed to extract commit info (fast): {e}")
            return []

    def _extract_contributor_info_fast(self) -> List[Dict]:
        """Extract contributor information (optimized - last 50 commits)"""
        try:
            self.logger.info("Extracting contributor info (fast)...")
            
            contributors = {}
            repo = Repository(self.current_repo_path)
            
            # Only analyze last 50 commits for speed
            commit_count = 0
            for commit in repo.traverse_commits():
                commit_count += 1
                if commit_count > 50:
                    break
                
                author_email = commit.author.email
                author_name = commit.author.name
                
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
                
                contributors[author_email]['commits'] += 1
                
                # Update date range
                if commit.author_date < contributors[author_email]['first_commit']:
                    contributors[author_email]['first_commit'] = commit.author_date
                if commit.author_date > contributors[author_email]['last_commit']:
                    contributors[author_email]['last_commit'] = commit.author_date
                
                # Add line count changes
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
            
            self.logger.info(f"Extracted {len(contributor_list)} contributors (fast mode)")
            return contributor_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract contributor info: {e}")
            return []

    def _extract_file_info_fast(self) -> List[Dict]:
        """Extract file information (optimized - sample files)"""
        try:
            self.logger.info("Extracting file info (fast)...")
            
            files = []
            file_count = 0
            
            for root, dirs, filenames in os.walk(self.current_repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                
                for filename in filenames:
                    file_count += 1
                    if file_count > 500:  # Limit to 500 files for speed
                        break
                    
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.current_repo_path)
                    
                    try:
                        file_stat = os.stat(filepath)
                        extension = os.path.splitext(filename)[1].lower()
                        
                        files.append({
                            'path': rel_path,
                            'name': filename,
                            'size': file_stat.st_size,
                            'extension': extension,
                            'language': self._get_language_from_extension(extension),
                            'modified_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
                        
                    except OSError:
                        continue
                
                if file_count > 500:
                    break
            
            self.logger.info(f"Extracted {len(files)} files (fast mode)")
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to extract file info: {e}")
            return []

    def _extract_contributor_info_from_commits(self, commits: List[Dict]) -> List[Dict]:
        """Extract contributor information from a list of commits (efficient)"""
        try:
            self.logger.info("Extracting contributor info from commits...")
            
            contributors = {}
            
            for commit in commits:
                author_email = commit.get('author_email', '')
                author_name = commit.get('author_name', 'Unknown')
                
                if not author_email:
                    continue
                
                # Use email as unique identifier
                if author_email not in contributors:
                    contributors[author_email] = {
                        'name': author_name,
                        'email': author_email,
                        'commits': 0,
                        'first_commit': commit.get('date', datetime.now().isoformat()),
                        'last_commit': commit.get('date', datetime.now().isoformat()),
                        'total_additions': 0,
                        'total_deletions': 0
                    }
                
                # Update contributor stats
                contributors[author_email]['commits'] += 1
                
                # Update date range
                commit_date = commit.get('date', datetime.now().isoformat())
                if commit_date < contributors[author_email]['first_commit']:
                    contributors[author_email]['first_commit'] = commit_date
                if commit_date > contributors[author_email]['last_commit']:
                    contributors[author_email]['last_commit'] = commit_date
                
                # Add line count changes (use commit data if available, otherwise estimate)
                additions = commit.get('additions', 0)
                deletions = commit.get('deletions', 0)
                
                # If no detailed data, make a rough estimate based on modified files
                if additions == 0 and deletions == 0 and commit.get('modified_files_count', 0) > 0:
                    # Rough estimate: assume 10 lines per modified file
                    additions = commit['modified_files_count'] * 10
                    deletions = commit['modified_files_count'] * 5
                
                contributors[author_email]['total_additions'] += additions
                contributors[author_email]['total_deletions'] += deletions
            
            # Convert to list
            contributor_list = list(contributors.values())
            
            # Sort by commit count
            contributor_list.sort(key=lambda x: x['commits'], reverse=True)
            
            self.logger.info(f"Extracted {len(contributor_list)} contributors from {len(commits)} commits")
            return contributor_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract contributor info from commits: {e}")
            return []

    def ask_question_neo4j_only(self, question: str) -> str:
        """RAG-powered Q&A using Neo4j knowledge graph"""
        try:
            if not self.current_repo_path:
                return "❌ No repository set. Please set a repository first."
            
            print(f"🤖 Processing question: {question}")
            start_time = datetime.now()
            
            # Step 1: Extract repository data and store in Neo4j if needed
            if not self.repo_metadata:
                print("📊 Extracting repository metadata...")
                self.repo_metadata = self.extract_metadata()
                
                # Store in Neo4j knowledge graph
                if self.neo4j_ready:
                    print("🔗 Storing data in Neo4j knowledge graph...")
                    self._store_metadata_in_neo4j(self.repo_metadata)
            
            # Step 2: Query Neo4j for relevant data
            neo4j_context = ""
            if self.neo4j_ready and self.neo4j_driver:
                try:
                    print("🔍 Querying Neo4j for relevant data...")
                    neo4j_context = self._query_neo4j_for_rag(question)
                    
                except Exception as e:
                    print(f"⚠️ Neo4j query failed: {e}")
            
            # Step 3: Use RAG (Retrieval-Augmented Generation) with Gemini
            if self.gemini_model and neo4j_context:
                try:
                    print("🧠 Generating RAG response with Gemini...")
                    
                    rag_prompt = f"""
You are an expert repository analyst with access to a knowledge graph. Use the retrieved data to answer questions accurately.

QUESTION: {question}

RETRIEVED DATA FROM KNOWLEDGE GRAPH:
{neo4j_context}

REPOSITORY: {self.current_repo_path}

Instructions for RAG Response:
1. Use the retrieved data to provide specific, accurate answers
2. Mention specific numbers, names, and facts from the data
3. If the question asks about contributors, use the contributor data
4. If the question asks about commits, use commit history data  
5. If the question asks about files, use file analysis data
6. Answer in the same language as the question (English/Bengali)
7. Be concise but informative
8. Use emojis for better readability

Generate a helpful response based on the retrieved knowledge graph data.
"""
                    
                    response = self.gemini_model.generate_content(rag_prompt)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"⚡ RAG response time: {elapsed:.2f}s")
                    
                    return f"🤖 **RAG Analysis:**\n\n{response.text}"
                    
                except Exception as e:
                    print(f"⚠️ RAG generation failed: {e}")
            
            # Step 4: Fallback to direct Neo4j query response
            if self.neo4j_ready:
                try:
                    direct_response = self._answer_with_neo4j(question)
                    if direct_response and "❌" not in direct_response:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        print(f"⚡ Neo4j response time: {elapsed:.2f}s")
                        return direct_response
                except Exception as e:
                    print(f"⚠️ Direct Neo4j query failed: {e}")
            
            # Step 5: Basic metadata fallback
            print("📊 Using basic metadata for response...")
            question_lower = question.lower()
            
            if any(word in question_lower for word in ['contributor', 'author', 'developer', 'কে', 'অবদান']):
                return self._answer_contributor_question()
            elif any(word in question_lower for word in ['commit', 'recent', 'latest', 'সাম্প্রতিক']):
                return self._answer_commit_question()
            elif any(word in question_lower for word in ['file', 'largest', 'biggest', 'ফাইল']):
                return self._answer_file_question()
            elif any(word in question_lower for word in ['overview', 'summary', 'সংক্ষেপ', 'ওভারভিউ']):
                return self._answer_overview_question()
            else:
                return self._generate_fallback_response(question)
                
        except Exception as e:
            self.logger.error(f"Error in RAG Q&A: {e}")
            return f"❌ Error processing question: {str(e)}"

    def _query_neo4j_for_rag(self, question: str) -> str:
        """Query Neo4j to retrieve relevant context for RAG using actual database schema"""
        try:
            if not self.neo4j_driver:
                return ""
            
            question_lower = question.lower()
            context_parts = []
            
            with self.neo4j_driver.session() as session:
                
                # Query contributors if question is about people
                if any(word in question_lower for word in ['who', 'contributor', 'author', 'developer', 'কে', 'অবদান']):
                    query = """
                    MATCH (u:Contributor)-[r:AUTHORED]->(c:Commit)
                    WITH u, count(c) as commit_count, sum(r.additions) as total_adds, sum(r.deletions) as total_dels
                    ORDER BY commit_count DESC LIMIT 10
                    RETURN u.name as name, u.email as email, commit_count, total_adds, total_dels
                    """
                    result = session.run(query)
                    contributors_data = "TOP CONTRIBUTORS:\n"
                    for record in result:
                        contributors_data += f"- {record['name']} ({record['email']}): {record['commit_count']} commits, +{record['total_adds'] or 0}/-{record['total_dels'] or 0} lines\n"
                    context_parts.append(contributors_data)
                
                # Query recent commits - use actual schema
                if any(word in question_lower for word in ['commit', 'recent', 'latest', 'change', 'সাম্প্রতিক']):
                    query = """
                    MATCH (c:Commit)
                    RETURN c.hash as hash, c.message as message, c.date as date
                    ORDER BY c.date DESC LIMIT 10
                    """
                    result = session.run(query)
                    commits_data = "RECENT COMMITS:\n"
                    for record in result:
                        date_str = str(record['date']) if record['date'] else 'N/A'
                        commits_data += f"- {record['hash'][:8]}: {record['message'][:60]}... ({date_str})\n"
                    context_parts.append(commits_data)
                
                # Query files - use actual schema
                if any(word in question_lower for word in ['file', 'big', 'large', 'complex', 'ফাইল']):
                    query = """
                    MATCH (f:File)
                    WHERE f.name IS NOT NULL AND f.size IS NOT NULL
                    RETURN f.name as name, f.size as size, f.language as language, f.path as path
                    ORDER BY f.size DESC LIMIT 10
                    """
                    result = session.run(query)
                    files_data = "LARGEST FILES:\n"
                    for record in result:
                        files_data += f"- {record['name'] or 'Unknown'}: {record['size']} bytes ({record['language'] or 'Unknown'})\n"
                    context_parts.append(files_data)
                
                # Get repository overview - use actual relationships
                if any(word in question_lower for word in ['overview', 'summary', 'about', 'total', 'সংক্ষেপ']):
                    query = """
                    MATCH (r:Repository)
                    OPTIONAL MATCH (c:Commit)
                    OPTIONAL MATCH (u:Contributor)
                    OPTIONAL MATCH (f:File)
                    RETURN r.name as repo_name, r.path as repo_path,
                           count(DISTINCT c) as total_commits,
                           count(DISTINCT u) as total_contributors, 
                           count(DISTINCT f) as total_files
                    """
                    result = session.run(query).single()
                    if result:
                        overview_data = f"""REPOSITORY OVERVIEW:
Repository: {result['repo_name'] or 'Unknown'}
Path: {result['repo_path'] or 'Unknown'}
Total Commits: {result['total_commits'] or 0}
Total Contributors: {result['total_contributors'] or 0}
Total Files: {result['total_files'] or 0}
"""
                        context_parts.append(overview_data)
                
                # Get file language distribution
                if any(word in question_lower for word in ['language', 'programming', 'code', 'ভাষা']):
                    query = """
                    MATCH (f:File)
                    WHERE f.language IS NOT NULL
                    WITH f.language as lang, count(f) as file_count, sum(f.size) as total_size
                    ORDER BY file_count DESC LIMIT 10
                    RETURN lang, file_count, total_size
                    """
                    result = session.run(query)
                    lang_data = "PROGRAMMING LANGUAGES:\n"
                    for record in result:
                        lang_data += f"- {record['lang']}: {record['file_count']} files, {record['total_size']} bytes\n"
                    context_parts.append(lang_data)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"⚠️ Neo4j RAG query failed: {e}")
            return ""

    def _check_existing_data(self, repo_name: str) -> bool:
        """Check if repository data already exists in Neo4j"""
        try:
            if not self.neo4j_driver:
                return False
            
            with self.neo4j_driver.session() as session:
                # Check if repository node exists with data
                query = """
                MATCH (r:Repository {name: $repo_name})
                OPTIONAL MATCH (r)-->(c:Commit)
                OPTIONAL MATCH (r)-->(f:File) 
                OPTIONAL MATCH (r)-->(u:Contributor)
                RETURN count(DISTINCT c) as commit_count,
                       count(DISTINCT f) as file_count,
                       count(DISTINCT u) as contributor_count
                """
                
                result = session.run(query, repo_name=repo_name).single()
                if result and (result['commit_count'] > 0 or result['file_count'] > 0 or result['contributor_count'] > 0):
                    print(f"📊 Found existing data for {repo_name}: {result['commit_count']} commits, {result['file_count']} files, {result['contributor_count']} contributors")
                    return True
                    
        except Exception as e:
            print(f"⚠️ Error checking existing data: {e}")
            
        return False

    def ingest_repository_to_neo4j(self, commit_limit: int = 100, progress_callback=None, force_reprocess: bool = False) -> bool:
        """
        Ingest repository data to Neo4j with commit limit and progress tracking
        Returns True if successful, False otherwise
        """
        try:
            if not self.neo4j_ready:
                print("⚠️ Neo4j not ready")
                return False
            
            if not self.current_repo_path:
                print("⚠️ No repository set")
                return False
            
            print(f"🔍 Ingesting repository data (limit: {commit_limit} commits)...")
            if progress_callback:
                progress_callback(5, "Starting ingestion...")
            
            # Check if data already exists for this repository (unless force reprocess)
            repo_name = os.path.basename(self.current_repo_path)
            if not force_reprocess and self._check_existing_data(repo_name):
                if progress_callback:
                    progress_callback(100, f"Data already exists for {repo_name} - skipping ingestion")
                print(f"ℹ️ Repository {repo_name} data already exists in Neo4j - skipping ingestion")
                return True
            
            # Extract metadata with limited commits
            if progress_callback:
                progress_callback(10, "Extracting basic metadata...")
            metadata = self._extract_basic_metadata()
            
            # Initialize data lists
            metadata['commits'] = []
            metadata['files'] = []
            metadata['contributors'] = []
            
            # Get limited commits with dynamic progress (15% - 45%)
            if progress_callback:
                progress_callback(15, "Analyzing commits...")
            
            def commit_progress_callback(progress, message):
                # Map commit progress (0-100) to 15-45 range
                mapped_progress = 15 + (progress * 0.3)
                if progress_callback:
                    progress_callback(mapped_progress, message)
            
            # Choose extraction method based on commit limit
            if commit_limit and commit_limit <= 100:
                # Use detailed extraction for small limits
                commits = self._extract_commit_info(limit=commit_limit, progress_callback=commit_progress_callback)
            else:
                # Use fast extraction for large limits to avoid slow processing
                print(f"🚀 Using fast commit extraction for limit {commit_limit}")
                commits = self._extract_commit_info_fast(limit=commit_limit or 500)
            
            metadata['commits'] = commits
            
            # Get other data with dynamic progress
            if progress_callback:
                progress_callback(50, "Processing files...")
            try:
                metadata['files'] = self._extract_file_info()
            except Exception as e:
                print(f"⚠️ File extraction failed: {e}")
                metadata['files'] = []
            
            if progress_callback:
                progress_callback(70, "Processing contributors...")
            try:
                # Extract contributors from the already processed commits to avoid re-traversing
                metadata['contributors'] = self._extract_contributor_info_from_commits(commits)
            except Exception as e:
                print(f"⚠️ Contributor extraction failed: {e}")
                metadata['contributors'] = []
            
            # Store in Neo4j with progress updates
            if progress_callback:
                progress_callback(85, "Storing data in Neo4j...")
            self._store_metadata_in_neo4j(metadata)
            
            if progress_callback:
                progress_callback(100, f"Ingestion completed! Processed {len(commits)} commits, {len(metadata['files'])} files, {len(metadata['contributors'])} contributors")
            
            print(f"✅ Repository ingested: {len(commits)} commits, {len(metadata['files'])} files, {len(metadata['contributors'])} contributors")
            return True
            
        except Exception as e:
            print(f"❌ Failed to ingest repository: {e}")
            return False

    def ask_question(self, question: str) -> str:
        """Main question answering method - redirects to Neo4j-only approach"""
        return self.ask_question_neo4j_only(question)

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