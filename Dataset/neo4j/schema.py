"""
Neo4j Graph Schema and Data Model Definitions
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# ==================== DATA MODELS ====================

@dataclass
class Project:
    """Project node"""
    id: str
    name: str
    url: str
    language: str
    stars: int = 0
    forks: int = 0
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "language": self.language,
            "stars": self.stars,
            "forks": self.forks,
            "description": self.description[:500],
        }

@dataclass
class Bug:
    """Bug node"""
    id: str
    title: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, closed, fixed
    reported_date: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description[:1000],
            "severity": self.severity,
            "status": self.status,
            "reported_date": self.reported_date,
        }

@dataclass
class Commit:
    """Commit node"""
    hash: str
    message: str
    author: str
    timestamp: str
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "hash": self.hash,
            "message": self.message[:500],
            "author": self.author,
            "timestamp": self.timestamp,
            "files_changed": self.files_changed,
            "additions": self.additions,
            "deletions": self.deletions,
        }

@dataclass
class File:
    """File node"""
    path: str
    language: str
    size: int = 0
    complexity: int = 0
    lines_of_code: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "language": self.language,
            "size": self.size,
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
        }

@dataclass
class Function:
    """Function/Method node"""
    name: str
    signature: str
    lines: int = 0
    cyclomatic_complexity: int = 0
    parameters: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "signature": self.signature[:1000],
            "lines": self.lines,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "parameters": self.parameters,
        }

@dataclass
class Issue:
    """Issue/Ticket node"""
    id: str
    title: str
    body: str
    state: str = "open"  # open, closed
    created_at: str = ""
    priority: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body[:1000],
            "state": self.state,
            "created_at": self.created_at,
            "priority": self.priority,
        }

@dataclass
class CodeSnippet:
    """Code snippet node"""
    hash: str
    content: str
    language: str
    tokens: int = 0
    complexity: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "hash": self.hash,
            "content": self.content[:2000],
            "language": self.language,
            "tokens": self.tokens,
            "complexity": self.complexity,
        }

@dataclass
class Metric:
    """Metric node"""
    name: str
    value: float
    category: str = "general"
    timestamp: str = ""
    unit: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "timestamp": self.timestamp,
            "unit": self.unit,
        }

# ==================== RELATIONSHIP MODELS ====================

class Relationships:
    """Relationship constants and utilities"""
    
    # Relationship types
    HAS_BUG = "HAS_BUG"
    FIXED_BY = "FIXED_BY"
    CONTAINS_FILE = "CONTAINS_FILE"
    CONTAINS_FUNCTION = "CONTAINS_FUNCTION"
    CALLS = "CALLS"
    RELATED_TO = "RELATED_TO"
    REPORTED_IN = "REPORTED_IN"
    CHANGED_IN = "CHANGED_IN"
    LOCATED_IN = "LOCATED_IN"
    HAS_METRIC = "HAS_METRIC"
    CREATED_FROM = "CREATED_FROM"
    
    @staticmethod
    def get_all_types() -> List[str]:
        """Get all relationship types"""
        return [
            "HAS_BUG", "FIXED_BY", "CONTAINS_FILE", "CONTAINS_FUNCTION",
            "CALLS", "RELATED_TO", "REPORTED_IN", "CHANGED_IN", "LOCATED_IN",
            "HAS_METRIC", "CREATED_FROM"
        ]

# ==================== CYPHER TEMPLATES ====================

CYPHER_TEMPLATES = {
    "get_project_bugs": """
        MATCH (p:Project)-[HAS_BUG]->(b:Bug)
        WHERE p.id = $project_id
        RETURN b
    """,
    
    "get_bug_fixes": """
        MATCH (b:Bug)-[FIXED_BY]->(c:Commit)
        WHERE b.id = $bug_id
        RETURN c
    """,
    
    "get_project_commits": """
        MATCH (p:Project)-[CHANGED_IN]->(c:Commit)
        WHERE p.id = $project_id
        RETURN c ORDER BY c.timestamp DESC
    """,
    
    "find_related_bugs": """
        MATCH (b1:Bug)-[RELATED_TO]-(b2:Bug)
        WHERE b1.id = $bug_id
        RETURN b2
    """,
    
    "get_file_functions": """
        MATCH (f:File)-[CONTAINS_FUNCTION]->(fn:Function)
        WHERE f.path = $file_path
        RETURN fn
    """,
    
    "find_buggy_files": """
        MATCH (b:Bug)<-[LOCATED_IN]-(f:File)
        WHERE b.severity = $severity
        RETURN DISTINCT f
    """,
    
    "get_code_metrics": """
        MATCH (c:CodeSnippet)-[HAS_METRIC]->(m:Metric)
        WHERE c.hash = $snippet_hash
        RETURN m
    """,
    
    "project_statistics": """
        MATCH (p:Project)
        WHERE p.id = $project_id
        WITH p
        OPTIONAL MATCH (p)-[HAS_BUG]->(b:Bug)
        WITH p, COUNT(DISTINCT b) as bug_count
        OPTIONAL MATCH (p)-[CHANGED_IN]->(c:Commit)
        WITH p, bug_count, COUNT(DISTINCT c) as commit_count
        RETURN {
            project: p.name,
            bugs: bug_count,
            commits: commit_count
        }
    """,
}
