#!/usr/bin/env python3
"""
RepoChat Knowledge Graph Builder
Constructs and manages repository knowledge graphs
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Try to import Neo4j, fallback to in-memory graph if not available
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ Neo4j not available, using in-memory graph storage")

class KnowledgeGraphBuilder:
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
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
            
        self.graph_file = '.repochat_graph.json'
        self.load_graph()
    
    def __del__(self):
        """Close Neo4j driver if available"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
    
    def build_knowledge_graph(self, repo_path: str, metadata: Dict[str, Any]) -> bool:
        """Build knowledge graph from repository metadata"""
        try:
            print("🏗️ Building knowledge graph...")
            
            # Clear existing graph
            self.clear_graph()
            
            # Create repository node
            self._create_repository_node(metadata['repository'])
            
            # Create file nodes
            print("📂 Creating file nodes...")
            for file_info in metadata['files']:
                self._create_file_node(file_info)
            
            # Create contributor nodes
            print("👥 Creating contributor nodes...")
            for contributor in metadata['contributors']:
                self._create_contributor_node(contributor)
            
            # Create commit nodes and relationships
            print("📝 Creating commit nodes...")
            commit_count = 0
            for commit in metadata['commits']:
                self._create_commit_node(commit)
                commit_count += 1
                
                if commit_count % 100 == 0:
                    print(f"   📈 Created {commit_count} commit nodes...")
            
            # Create branch nodes
            print("🌿 Creating branch nodes...")
            for branch in metadata['branches']:
                self._create_branch_node(branch)
            
            # Create tag nodes
            print("🏷️ Creating tag nodes...")
            for tag in metadata['tags']:
                self._create_tag_node(tag)
            
            # Save graph
            self.save_graph()
            
            print("✅ Knowledge graph construction complete!")
            print(f"📊 Total nodes: {self.get_node_count()}")
            print(f"🔗 Total relationships: {self.get_relationship_count()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to build knowledge graph: {e}")
            return False
    
    def _create_repository_node(self, repo_info: Dict[str, Any]):
        """Create repository node"""
        if self.use_neo4j:
            query = """
            CREATE (r:Repository {
                name: $name,
                path: $path,
                remote_url: $remote_url,
                description: $description,
                language: $language,
                created_date: $created_date,
                last_activity: $last_activity,
                total_commits: $total_commits,
                total_branches: $total_branches,
                total_tags: $total_tags
            })
            """
            self._execute_neo4j_query(query, repo_info)
        else:
            self.in_memory_graph['nodes']['repository'] = {
                'type': 'Repository',
                'properties': repo_info
            }
    
    def _create_file_node(self, file_info: Dict[str, Any]):
        """Create file node"""
        if self.use_neo4j:
            query = """
            CREATE (f:File {
                path: $path,
                name: $name,
                extension: $extension,
                size: $size,
                language: $language,
                lines_of_code: $lines_of_code,
                last_modified: $last_modified
            })
            """
            self._execute_neo4j_query(query, file_info)
        else:
            file_id = f"file_{hash(file_info['path'])}"
            self.in_memory_graph['nodes'][file_id] = {
                'type': 'File',
                'properties': file_info
            }
    
    def _create_contributor_node(self, contributor_info: Dict[str, Any]):
        """Create contributor node"""
        if self.use_neo4j:
            query = """
            CREATE (c:Contributor {
                name: $name,
                email: $email,
                commits: $commits,
                insertions: $insertions,
                deletions: $deletions,
                total_files_modified: $total_files_modified,
                first_commit: $first_commit,
                last_commit: $last_commit
            })
            """
            self._execute_neo4j_query(query, contributor_info)
        else:
            contributor_id = f"contributor_{hash(contributor_info['email'])}"
            self.in_memory_graph['nodes'][contributor_id] = {
                'type': 'Contributor',
                'properties': contributor_info
            }
    
    def _create_commit_node(self, commit_info: Dict[str, Any]):
        """Create commit node and relationships"""
        if self.use_neo4j:
            # Create commit node
            query = """
            CREATE (c:Commit {
                hash: $hash,
                message: $message,
                author_name: $author_name,
                author_email: $author_email,
                committer_name: $committer_name,
                committer_email: $committer_email,
                date: $date,
                insertions: $insertions,
                deletions: $deletions,
                lines: $lines,
                files: $files,
                is_bug_fix: $is_bug_fix,
                is_merge: $is_merge,
                in_main_branch: $in_main_branch
            })
            """
            
            commit_params = {
                'hash': commit_info['hash'],
                'message': commit_info['message'],
                'author_name': commit_info['author']['name'],
                'author_email': commit_info['author']['email'],
                'committer_name': commit_info['committer']['name'],
                'committer_email': commit_info['committer']['email'],
                'date': commit_info['date'],
                'insertions': commit_info.get('insertions', 0),
                'deletions': commit_info.get('deletions', 0),
                'lines': commit_info.get('lines', 0),
                'files': commit_info.get('files', 0),
                'is_bug_fix': commit_info.get('is_bug_fix', False),
                'is_merge': commit_info.get('is_merge', False),
                'in_main_branch': commit_info.get('in_main_branch', True)
            }
            
            self._execute_neo4j_query(query, commit_params)
            
            # Create relationships
            self._create_commit_relationships(commit_info)
            
        else:
            commit_id = f"commit_{commit_info['hash']}"
            self.in_memory_graph['nodes'][commit_id] = {
                'type': 'Commit',
                'properties': commit_info
            }
            
            # Create relationships
            self._create_commit_relationships_memory(commit_info)
    
    def _create_commit_relationships(self, commit_info: Dict[str, Any]):
        """Create commit relationships in Neo4j"""
        commit_hash = commit_info['hash']
        author_email = commit_info['author']['email']
        
        # AUTHORED relationship
        query = """
        MATCH (c:Commit {hash: $commit_hash})
        MATCH (a:Contributor {email: $author_email})
        CREATE (a)-[:AUTHORED]->(c)
        """
        self._execute_neo4j_query(query, {
            'commit_hash': commit_hash,
            'author_email': author_email
        })
        
        # MODIFIED relationships with files
        for file_info in commit_info.get('modified_files', []):
            if file_info.get('filename'):
                query = """
                MATCH (c:Commit {hash: $commit_hash})
                MATCH (f:File {path: $file_path})
                CREATE (c)-[:MODIFIED {
                    change_type: $change_type,
                    added_lines: $added_lines,
                    deleted_lines: $deleted_lines,
                    nloc: $nloc
                }]->(f)
                """
                self._execute_neo4j_query(query, {
                    'commit_hash': commit_hash,
                    'file_path': file_info['filename'],
                    'change_type': file_info.get('change_type', 'UNKNOWN'),
                    'added_lines': file_info.get('added_lines', 0),
                    'deleted_lines': file_info.get('deleted_lines', 0),
                    'nloc': file_info.get('nloc', 0)
                })
    
    def _create_commit_relationships_memory(self, commit_info: Dict[str, Any]):
        """Create commit relationships in memory"""
        commit_id = f"commit_{commit_info['hash']}"
        author_email = commit_info['author']['email']
        contributor_id = f"contributor_{hash(author_email)}"
        
        # AUTHORED relationship
        self.in_memory_graph['relationships'].append({
            'from': contributor_id,
            'to': commit_id,
            'type': 'AUTHORED',
            'properties': {}
        })
        
        # MODIFIED relationships
        for file_info in commit_info.get('modified_files', []):
            if file_info.get('filename'):
                file_id = f"file_{hash(file_info['filename'])}"
                self.in_memory_graph['relationships'].append({
                    'from': commit_id,
                    'to': file_id,
                    'type': 'MODIFIED',
                    'properties': {
                        'change_type': file_info.get('change_type', 'UNKNOWN'),
                        'added_lines': file_info.get('added_lines', 0),
                        'deleted_lines': file_info.get('deleted_lines', 0),
                        'nloc': file_info.get('nloc', 0)
                    }
                })
    
    def _create_branch_node(self, branch_info: Dict[str, Any]):
        """Create branch node"""
        if self.use_neo4j:
            query = """
            CREATE (b:Branch {
                name: $name,
                last_commit: $last_commit,
                last_commit_date: $last_commit_date,
                author: $author
            })
            """
            self._execute_neo4j_query(query, branch_info)
        else:
            branch_id = f"branch_{hash(branch_info['name'])}"
            self.in_memory_graph['nodes'][branch_id] = {
                'type': 'Branch',
                'properties': branch_info
            }
    
    def _create_tag_node(self, tag_info: Dict[str, Any]):
        """Create tag node"""
        if self.use_neo4j:
            query = """
            CREATE (t:Tag {
                name: $name,
                commit: $commit,
                date: $date,
                message: $message
            })
            """
            self._execute_neo4j_query(query, tag_info)
        else:
            tag_id = f"tag_{hash(tag_info['name'])}"
            self.in_memory_graph['nodes'][tag_id] = {
                'type': 'Tag',
                'properties': tag_info
            }
    
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
    
    def _execute_memory_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute query against in-memory graph (simplified)"""
        # This is a simplified query processor for in-memory graphs
        # In a full implementation, this would be a proper Cypher parser
        
        results = []
        
        try:
            query_lower = cypher_query.lower()
            
            # Handle simple node queries
            if 'match' in query_lower and 'return' in query_lower:
                if 'contributor' in query_lower:
                    for node_id, node in self.in_memory_graph['nodes'].items():
                        if node['type'] == 'Contributor':
                            results.append(node['properties'])
                
                elif 'commit' in query_lower:
                    for node_id, node in self.in_memory_graph['nodes'].items():
                        if node['type'] == 'Commit':
                            results.append(node['properties'])
                
                elif 'file' in query_lower:
                    for node_id, node in self.in_memory_graph['nodes'].items():
                        if node['type'] == 'File':
                            results.append(node['properties'])
                
                # Add more query patterns as needed
                
        except Exception as e:
            self.logger.error(f"Memory query processing failed: {e}")
        
        return results
    
    def clear_graph(self):
        """Clear the knowledge graph"""
        if self.use_neo4j:
            query = "MATCH (n) DETACH DELETE n"
            self._execute_neo4j_query(query)
        else:
            self.in_memory_graph = {
                'nodes': {},
                'relationships': []
            }
    
    def has_knowledge_graph(self) -> bool:
        """Check if knowledge graph exists"""
        if self.use_neo4j:
            try:
                result = self._execute_neo4j_query("MATCH (n) RETURN count(n) as count")
                return result[0]['count'] > 0 if result else False
            except:
                return False
        else:
            return len(self.in_memory_graph['nodes']) > 0
    
    def get_node_count(self) -> int:
        """Get total number of nodes"""
        if self.use_neo4j:
            try:
                result = self._execute_neo4j_query("MATCH (n) RETURN count(n) as count")
                return result[0]['count'] if result else 0
            except:
                return 0
        else:
            return len(self.in_memory_graph['nodes'])
    
    def get_relationship_count(self) -> int:
        """Get total number of relationships"""
        if self.use_neo4j:
            try:
                result = self._execute_neo4j_query("MATCH ()-[r]->() RETURN count(r) as count")
                return result[0]['count'] if result else 0
            except:
                return 0
        else:
            return len(self.in_memory_graph['relationships'])
    
    def save_graph(self):
        """Save in-memory graph to file"""
        if not self.use_neo4j:
            try:
                with open(self.graph_file, 'w', encoding='utf-8') as f:
                    json.dump(self.in_memory_graph, f, indent=2, default=str)
            except Exception as e:
                self.logger.warning(f"Could not save graph: {e}")
    
    def load_graph(self):
        """Load in-memory graph from file"""
        if not self.use_neo4j and os.path.exists(self.graph_file):
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.in_memory_graph = json.load(f)
                print(f"📊 Loaded knowledge graph: {self.get_node_count()} nodes, {self.get_relationship_count()} relationships")
            except Exception as e:
                self.logger.warning(f"Could not load graph: {e}")
                self.in_memory_graph = {'nodes': {}, 'relationships': []}
    
    def get_graph_schema(self) -> Dict[str, List[str]]:
        """Get knowledge graph schema"""
        schema = {
            'node_types': [],
            'relationship_types': []
        }
        
        if self.use_neo4j:
            # Get node labels
            result = self._execute_neo4j_query("CALL db.labels()")
            schema['node_types'] = [record['label'] for record in result]
            
            # Get relationship types
            result = self._execute_neo4j_query("CALL db.relationshipTypes()")
            schema['relationship_types'] = [record['relationshipType'] for record in result]
        else:
            # Extract from in-memory graph
            node_types = set()
            relationship_types = set()
            
            for node in self.in_memory_graph['nodes'].values():
                node_types.add(node['type'])
            
            for rel in self.in_memory_graph['relationships']:
                relationship_types.add(rel['type'])
            
            schema['node_types'] = list(node_types)
            schema['relationship_types'] = list(relationship_types)
        
        return schema