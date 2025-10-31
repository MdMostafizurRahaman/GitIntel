#!/usr/bin/env python3
"""
Knowledge Graph Builder - Creates and manages repository knowledge graphs
Supports both Neo4j and in-memory graph storage for GitIntel
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try to import Neo4j, fallback to in-memory graph
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ Neo4j not available, using in-memory graph storage")

class KnowledgeGraphBuilder:
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None, repo_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Try Neo4j first, fallback to in-memory
        if NEO4J_AVAILABLE and neo4j_uri:
            self.use_neo4j = True
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        else:
            self.use_neo4j = False
            self.in_memory_graph = {
                'nodes': {},
                'relationships': []
            }
            
        # Dynamic graph file naming based on repository
        self.graph_file = self._get_graph_file_name(repo_path)
        self.load_graph()
    
    def _get_graph_file_name(self, repo_path: str = None) -> str:
        """Generate dynamic graph file name based on repository"""
        if repo_path:
            repo_name = os.path.basename(repo_path)
            return f".knowledge_graph_{repo_name}.json"
        return ".knowledge_graph.json"
    
    def has_knowledge_graph(self) -> bool:
        """Check if knowledge graph exists and has data"""
        if self.use_neo4j:
            return self._neo4j_has_data()
        else:
            return len(self.in_memory_graph['nodes']) > 0
    
    def _neo4j_has_data(self) -> bool:
        """Check if Neo4j database has any nodes"""
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                record = result.single()
                return record and record["count"] > 0
        except Exception as e:
            self.logger.error(f"Failed to check Neo4j data: {e}")
            return False
    
    def build_knowledge_graph(self, repo_path: str, metadata: Dict[str, Any]) -> bool:
        """Build knowledge graph from repository metadata"""
        try:
            self.logger.info("Building knowledge graph...")
            
            # Clear existing graph
            self.clear_graph()
            
            # Create repository node
            self._create_repository_node(metadata['repository'])
            
            # Create commit nodes and relationships
            self._create_commit_nodes(metadata['commits'])
            
            # Create file nodes and relationships
            self._create_file_nodes(metadata['files'])
            
            # Create contributor nodes and relationships
            self._create_contributor_nodes(metadata['contributors'])
            
            # Save graph state
            self.save_graph()
            
            self.logger.info("Knowledge graph built successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to build knowledge graph: {e}")
            return False
    
    def clear_graph(self):
        """Clear the entire knowledge graph"""
        if self.use_neo4j:
            self._clear_neo4j_graph()
        else:
            self.in_memory_graph = {
                'nodes': {},
                'relationships': []
            }
    
    def _clear_neo4j_graph(self):
        """Clear Neo4j database"""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        except Exception as e:
            self.logger.error(f"Failed to clear Neo4j graph: {e}")
    
    def _create_repository_node(self, repo_info: Dict[str, Any]):
        """Create repository node"""
        if self.use_neo4j:
            self._create_neo4j_repository_node(repo_info)
        else:
            self._create_memory_repository_node(repo_info)
    
    def _create_neo4j_repository_node(self, repo_info: Dict[str, Any]):
        """Create repository node in Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (r:Repository {
                        name: $name,
                        path: $path,
                        active_branch: $active_branch,
                        total_commits: $total_commits,
                        size_mb: $size_mb,
                        branches: $branches,
                        tags: $tags
                    })
                """, **repo_info)
        except Exception as e:
            self.logger.error(f"Failed to create Neo4j repository node: {e}")
    
    def _create_memory_repository_node(self, repo_info: Dict[str, Any]):
        """Create repository node in memory"""
        node_id = f"repo_{repo_info['name']}"
        self.in_memory_graph['nodes'][node_id] = {
            'type': 'Repository',
            'data': repo_info
        }
    
    def _create_commit_nodes(self, commits: List[Dict[str, Any]]):
        """Create commit nodes and relationships"""
        for commit in commits:
            if self.use_neo4j:
                self._create_neo4j_commit_node(commit)
            else:
                self._create_memory_commit_node(commit)
    
    def _create_neo4j_commit_node(self, commit: Dict[str, Any]):
        """Create commit node in Neo4j"""
        try:
            with self.driver.session() as session:
                # Create commit node
                session.run("""
                    CREATE (c:Commit {
                        hash: $hash,
                        message: $message,
                        author_name: $author_name,
                        author_email: $author_email,
                        date: $date,
                        is_bug_fix: $is_bug_fix,
                        modified_files_count: $modified_files_count,
                        additions: $additions,
                        deletions: $deletions,
                        net_changes: $net_changes
                    })
                """, **commit)
                
                # Create contributor if not exists and link to commit
                session.run("""
                    MERGE (contributor:Contributor {
                        email: $author_email
                    })
                    ON CREATE SET 
                        contributor.name = $author_name,
                        contributor.commits = 1
                    ON MATCH SET 
                        contributor.commits = contributor.commits + 1
                    
                    WITH contributor
                    MATCH (c:Commit {hash: $hash})
                    CREATE (contributor)-[:AUTHORED]->(c)
                """, **commit)
                
        except Exception as e:
            self.logger.error(f"Failed to create Neo4j commit node: {e}")
    
    def _create_memory_commit_node(self, commit: Dict[str, Any]):
        """Create commit node in memory"""
        commit_id = f"commit_{commit['hash']}"
        self.in_memory_graph['nodes'][commit_id] = {
            'type': 'Commit',
            'data': commit
        }
        
        # Create contributor node if not exists
        contributor_id = f"contributor_{commit['author_email']}"
        if contributor_id not in self.in_memory_graph['nodes']:
            self.in_memory_graph['nodes'][contributor_id] = {
                'type': 'Contributor',
                'data': {
                    'name': commit['author_name'],
                    'email': commit['author_email'],
                    'commits': 1
                }
            }
        else:
            # Update commit count
            self.in_memory_graph['nodes'][contributor_id]['data']['commits'] += 1
        
        # Create relationship
        self.in_memory_graph['relationships'].append({
            'from': contributor_id,
            'to': commit_id,
            'type': 'AUTHORED'
        })
    
    def _create_file_nodes(self, files: List[Dict[str, Any]]):
        """Create file nodes and relationships"""
        for file_info in files:
            if self.use_neo4j:
                self._create_neo4j_file_node(file_info)
            else:
                self._create_memory_file_node(file_info)
    
    def _create_neo4j_file_node(self, file_info: Dict[str, Any]):
        """Create file node in Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (f:File {
                        name: $name,
                        path: $path,
                        extension: $extension,
                        language: $language,
                        size_bytes: $size_bytes,
                        lines_of_code: $lines_of_code,
                        last_modified: $last_modified
                    })
                """, **file_info)
        except Exception as e:
            self.logger.error(f"Failed to create Neo4j file node: {e}")
    
    def _create_memory_file_node(self, file_info: Dict[str, Any]):
        """Create file node in memory"""
        file_id = f"file_{file_info['path'].replace('/', '_').replace('\\', '_')}"
        self.in_memory_graph['nodes'][file_id] = {
            'type': 'File',
            'data': file_info
        }
    
    def _create_contributor_nodes(self, contributors: List[Dict[str, Any]]):
        """Create/update contributor nodes with full information"""
        for contributor in contributors:
            if self.use_neo4j:
                self._update_neo4j_contributor_node(contributor)
            else:
                self._update_memory_contributor_node(contributor)
    
    def _update_neo4j_contributor_node(self, contributor: Dict[str, Any]):
        """Update contributor node in Neo4j with full information"""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (c:Contributor {email: $email})
                    SET c.name = $name,
                        c.commits = $commits,
                        c.first_commit = $first_commit,
                        c.last_commit = $last_commit,
                        c.total_additions = $total_additions,
                        c.total_deletions = $total_deletions
                """, **contributor)
        except Exception as e:
            self.logger.error(f"Failed to update Neo4j contributor node: {e}")
    
    def _update_memory_contributor_node(self, contributor: Dict[str, Any]):
        """Update contributor node in memory with full information"""
        contributor_id = f"contributor_{contributor['email']}"
        if contributor_id in self.in_memory_graph['nodes']:
            # Update existing node with full information
            self.in_memory_graph['nodes'][contributor_id]['data'].update(contributor)
        else:
            # Create new node
            self.in_memory_graph['nodes'][contributor_id] = {
                'type': 'Contributor',
                'data': contributor
            }
    
    def save_graph(self):
        """Save in-memory graph to file"""
        if not self.use_neo4j:
            try:
                with open(self.graph_file, 'w', encoding='utf-8') as f:
                    json.dump(self.in_memory_graph, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Graph saved to {self.graph_file}")
            except Exception as e:
                self.logger.error(f"Failed to save graph: {e}")
    
    def load_graph(self):
        """Load in-memory graph from file"""
        if not self.use_neo4j and os.path.exists(self.graph_file):
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.in_memory_graph = json.load(f)
                self.logger.info(f"Graph loaded from {self.graph_file}")
            except Exception as e:
                self.logger.error(f"Failed to load graph: {e}")
                self.in_memory_graph = {'nodes': {}, 'relationships': []}
    
    def execute_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query against the knowledge graph"""
        try:
            if self.use_neo4j:
                return self._execute_neo4j_query(cypher_query)
            else:
                return self._execute_memory_query(cypher_query)
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return []
    
    def _execute_neo4j_query(self, query: str, parameters: Dict = None) -> List[Dict[str, Any]]:
        """Execute query against Neo4j database"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            self.logger.error(f"Neo4j query failed: {e}")
            return []
    
    def _execute_memory_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute simplified query against in-memory graph"""
        try:
            # Simple query parsing for common patterns
            query_lower = query.lower()
            
            if 'match (c:contributor)' in query_lower:
                return self._query_contributors(query)
            elif 'match (commit:commit)' in query_lower or 'match (c:commit)' in query_lower:
                return self._query_commits(query)
            elif 'match (f:file)' in query_lower:
                return self._query_files(query)
            elif 'match (r:repository)' in query_lower:
                return self._query_repository(query)
            else:
                # Generic fallback - return all nodes
                return self._query_all_nodes()
                
        except Exception as e:
            self.logger.error(f"Memory query failed: {e}")
            return []
    
    def _query_contributors(self, query: str) -> List[Dict[str, Any]]:
        """Query contributors from in-memory graph"""
        contributors = []
        
        for node_id, node_data in self.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Contributor':
                # Map to Neo4j-like structure
                data = node_data['data']
                contributor = {
                    'c.name': data.get('name'),
                    'c.email': data.get('email'),
                    'c.commits': data.get('commits', 0),
                    'c.first_commit': data.get('first_commit'),
                    'c.last_commit': data.get('last_commit'),
                    'c.total_additions': data.get('total_additions', 0),
                    'c.total_deletions': data.get('total_deletions', 0)
                }
                contributors.append(contributor)
        
        # Sort by commits if ORDER BY is in query
        if 'order by' in query.lower() and 'commits' in query.lower():
            if 'desc' in query.lower():
                contributors.sort(key=lambda x: x.get('c.commits', 0), reverse=True)
            else:
                contributors.sort(key=lambda x: x.get('c.commits', 0))
        
        # Apply LIMIT if present
        limit = self._extract_limit(query)
        if limit:
            contributors = contributors[:limit]
        
        return contributors
    
    def _query_commits(self, query: str) -> List[Dict[str, Any]]:
        """Query commits from in-memory graph"""
        commits = []
        
        for node_id, node_data in self.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Commit':
                data = node_data['data']
                commit = {
                    'c.hash': data.get('hash'),
                    'c.message': data.get('message'),
                    'c.author_name': data.get('author_name'),
                    'c.author_email': data.get('author_email'),
                    'c.date': data.get('date'),
                    'c.is_bug_fix': data.get('is_bug_fix', False),
                    'c.additions': data.get('additions', 0),
                    'c.deletions': data.get('deletions', 0)
                }
                commits.append(commit)
        
        # Sort by date if ORDER BY is in query
        if 'order by' in query.lower() and 'date' in query.lower():
            if 'desc' in query.lower():
                commits.sort(key=lambda x: x.get('c.date', ''), reverse=True)
            else:
                commits.sort(key=lambda x: x.get('c.date', ''))
        
        # Apply LIMIT if present
        limit = self._extract_limit(query)
        if limit:
            commits = commits[:limit]
        
        return commits
    
    def _query_files(self, query: str) -> List[Dict[str, Any]]:
        """Query files from in-memory graph"""
        files = []
        
        for node_id, node_data in self.in_memory_graph['nodes'].items():
            if node_data['type'] == 'File':
                data = node_data['data']
                file_info = {
                    'f.name': data.get('name'),
                    'f.path': data.get('path'),
                    'f.language': data.get('language'),
                    'f.lines_of_code': data.get('lines_of_code', 0),
                    'f.size_bytes': data.get('size_bytes', 0)
                }
                files.append(file_info)
        
        # Apply filters and sorting
        if 'lines_of_code' in query.lower() and 'order by' in query.lower():
            files.sort(key=lambda x: x.get('f.lines_of_code', 0), reverse='desc' in query.lower())
        
        # Apply LIMIT if present
        limit = self._extract_limit(query)
        if limit:
            files = files[:limit]
        
        return files
    
    def _query_repository(self, query: str) -> List[Dict[str, Any]]:
        """Query repository from in-memory graph"""
        for node_id, node_data in self.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Repository':
                data = node_data['data']
                return [{
                    'r.name': data.get('name'),
                    'r.path': data.get('path'),
                    'r.active_branch': data.get('active_branch'),
                    'r.total_commits': data.get('total_commits', 0),
                    'r.size_mb': data.get('size_mb', 0),
                    'r.branches': data.get('branches', []),
                    'r.tags': data.get('tags', [])
                }]
        return []
    
    def _query_all_nodes(self) -> List[Dict[str, Any]]:
        """Return all nodes for debugging"""
        result = []
        for node_id, node_data in self.in_memory_graph['nodes'].items():
            result.append({
                'node_id': node_id,
                'type': node_data['type'],
                'data': node_data['data']
            })
        return result[:20]  # Limit to prevent overwhelming output
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract LIMIT value from query"""
        import re
        match = re.search(r'limit\s+(\d+)', query.lower())
        if match:
            return int(match.group(1))
        return None
    
    def close(self):
        """Close database connections"""
        if self.use_neo4j and hasattr(self, 'driver'):
            self.driver.close()

# Example usage
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize knowledge graph builder
    kg_builder = KnowledgeGraphBuilder()
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
        
        # Example: build knowledge graph
        from repochat_core import RepoChatCore
        
        core = RepoChatCore()
        if core.set_repository(repo_path):
            metadata = core.extract_metadata()
            
            if kg_builder.build_knowledge_graph(repo_path, metadata):
                print("✅ Knowledge graph built successfully")
                
                # Test some queries
                print("\n🔍 Testing queries:")
                
                # Query contributors
                contributors = kg_builder.execute_query(
                    "MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 5"
                )
                print(f"Top contributors: {len(contributors)} found")
                
                # Query commits
                commits = kg_builder.execute_query(
                    "MATCH (c:Commit) RETURN c.hash, c.message, c.author_name ORDER BY c.date DESC LIMIT 3"
                )
                print(f"Recent commits: {len(commits)} found")
            else:
                print("❌ Failed to build knowledge graph")
        else:
            print(f"❌ Failed to set repository: {repo_path}")
    else:
        print("Usage: python repochat_knowledge_graph.py <repo_path>")