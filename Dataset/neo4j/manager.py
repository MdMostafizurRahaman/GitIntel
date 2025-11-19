"""
Neo4j Graph Database Manager
Handles all Neo4j operations: connection, data insertion, querying
"""

from typing import Dict, List, Optional, Any, Tuple
from neo4j import GraphDatabase, Session
import logging
from config.config import NEO4J_CONFIG, NEO4J_NODES, NEO4J_RELATIONSHIPS

logger = logging.getLogger(__name__)

class Neo4jManager:
    """Manages Neo4j database operations"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver = None
        self.session = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_CONFIG["uri"],
                auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
            )
            # Test connection
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict:
        """Create a single node"""
        query = f"""
        CREATE (n:{label} {self._build_properties(properties)})
        RETURN n
        """
        try:
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                result = session.run(query)
                node = result.single()
                logger.info(f"Created {label} node with properties: {properties}")
                return dict(node[0].items()) if node else {}
        except Exception as e:
            logger.error(f"Error creating {label} node: {e}")
            raise
    
    def create_nodes_batch(self, label: str, nodes_list: List[Dict[str, Any]]) -> List[Dict]:
        """Create multiple nodes in batch"""
        created_nodes = []
        for node_props in nodes_list:
            try:
                node = self.create_node(label, node_props)
                created_nodes.append(node)
            except Exception as e:
                logger.warning(f"Failed to create {label} node: {e}")
                continue
        
        logger.info(f"Created {len(created_nodes)}/{len(nodes_list)} {label} nodes")
        return created_nodes
    
    def create_relationship(self, 
                          from_node: Tuple[str, Dict],
                          relationship_type: str,
                          to_node: Tuple[str, Dict],
                          rel_properties: Optional[Dict] = None) -> bool:
        """Create relationship between two nodes"""
        
        from_label, from_props = from_node
        to_label, to_props = to_node
        rel_props = rel_properties or {}
        
        # Build match clause
        from_match = f"(a:{from_label} {self._build_properties(from_props)})"
        to_match = f"(b:{to_label} {self._build_properties(to_props)})"
        
        # Build relationship properties
        rel_prop_str = self._build_properties(rel_props)
        rel_clause = f"[r:{relationship_type} {rel_prop_str}]" if rel_props else f"[r:{relationship_type}]"
        
        query = f"""
        MATCH {from_match}, {to_match}
        CREATE (a)-{rel_clause}->(b)
        RETURN r
        """
        
        try:
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                result = session.run(query)
                rel = result.single()
                logger.info(f"Created {relationship_type} relationship")
                return True
        except Exception as e:
            logger.error(f"Error creating {relationship_type} relationship: {e}")
            return False
    
    def query(self, cypher_query: str, parameters: Optional[Dict] = None) -> List[Any]:
        """Execute Cypher query"""
        parameters = parameters or {}
        try:
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                result = session.run(cypher_query, parameters)
                records = list(result)
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def find_nodes(self, label: str, properties: Optional[Dict] = None) -> List[Dict]:
        """Find nodes by label and properties"""
        properties = properties or {}
        
        if properties:
            prop_str = self._build_properties(properties)
            query = f"MATCH (n:{label} {prop_str}) RETURN n"
        else:
            query = f"MATCH (n:{label}) RETURN n"
        
        try:
            records = self.query(query)
            nodes = [dict(record[0].items()) for record in records if record[0]]
            logger.info(f"Found {len(nodes)} {label} nodes")
            return nodes
        except Exception as e:
            logger.error(f"Error finding {label} nodes: {e}")
            return []
    
    def find_relationships(self, relationship_type: str, 
                          from_label: Optional[str] = None,
                          to_label: Optional[str] = None) -> List[Dict]:
        """Find relationships by type"""
        
        if from_label and to_label:
            query = f"""
            MATCH (a:{from_label})-[r:{relationship_type}]->(b:{to_label})
            RETURN a, r, b
            """
        elif from_label:
            query = f"""
            MATCH (a:{from_label})-[r:{relationship_type}]->()
            RETURN a, r
            """
        elif to_label:
            query = f"""
            MATCH ()-[r:{relationship_type}]->(b:{to_label})
            RETURN r, b
            """
        else:
            query = f"MATCH ()-[r:{relationship_type}]->() RETURN r"
        
        try:
            records = self.query(query)
            rels = [record for record in records]
            logger.info(f"Found {len(rels)} {relationship_type} relationships")
            return rels
        except Exception as e:
            logger.error(f"Error finding {relationship_type} relationships: {e}")
            return []
    
    def delete_node(self, label: str, properties: Dict) -> bool:
        """Delete a node and its relationships"""
        prop_str = self._build_properties(properties)
        query = f"""
        MATCH (n:{label} {prop_str})
        DETACH DELETE n
        """
        try:
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                session.run(query)
                logger.info(f"Deleted {label} node")
                return True
        except Exception as e:
            logger.error(f"Error deleting {label} node: {e}")
            return False
    
    def clear_database(self) -> bool:
        """Clear entire database (use with caution)"""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.driver.session(database=NEO4J_CONFIG["database"]) as session:
                session.run(query)
                logger.warning("Cleared entire database")
                return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        UNION ALL
        MATCH ()-[r]->()
        RETURN type(r) as label, count(*) as count
        ORDER BY label
        """
        try:
            records = self.query(query)
            stats = {record["label"]: record["count"] for record in records}
            logger.info(f"Database stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    @staticmethod
    def _build_properties(props: Dict) -> str:
        """Build property filter string for Cypher"""
        if not props:
            return ""
        
        prop_strings = []
        for key, value in props.items():
            if isinstance(value, str):
                prop_strings.append(f"{key}: '{value}'")
            else:
                prop_strings.append(f"{key}: {value}")
        
        return "{" + ", ".join(prop_strings) + "}"
    
    @staticmethod
    def build_cypher_create_statement(label: str, properties: Dict) -> str:
        """Build a CREATE statement for a node"""
        prop_str = Neo4jManager._build_properties(properties)
        return f"CREATE (:{label} {prop_str})"
    
    @staticmethod
    def build_cypher_match_statement(label: str, properties: Dict) -> str:
        """Build a MATCH statement for a node"""
        prop_str = Neo4jManager._build_properties(properties)
        return f"MATCH (n:{label} {prop_str})"

# Global instance
_neo4j_manager = None

def get_neo4j_manager() -> Neo4jManager:
    """Get or create Neo4j manager instance"""
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager
