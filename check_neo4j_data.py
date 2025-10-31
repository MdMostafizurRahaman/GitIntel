#!/usr/bin/env python3
"""
Check what data is actually stored in Neo4j database
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("❌ Neo4j not available")
    sys.exit(1)

def check_neo4j_data():
    """Check what data is stored in Neo4j"""
    print("🔍 Checking Neo4j Database Content")
    print("="*50)
    
    # Get credentials
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([neo4j_uri, neo4j_password]):
        print("❌ Neo4j credentials missing")
        return
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            
            # Check all node types
            print("📊 Node Types and Counts:")
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record["label"] for record in result]
            
            for label in labels:
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = count_result.single()["count"]
                print(f"   • {label}: {count} nodes")
            
            print("\n🔗 Relationship Types:")
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            rel_types = [record["relationshipType"] for record in result]
            
            for rel_type in rel_types:
                count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = count_result.single()["count"]
                print(f"   • {rel_type}: {count} relationships")
            
            # Sample data from each node type
            print("\n📋 Sample Data:")
            
            # Check Repositories
            if "Repository" in labels:
                result = session.run("MATCH (r:Repository) RETURN r LIMIT 3")
                print("   🗂️ Repository samples:")
                for record in result:
                    repo = record["r"]
                    print(f"     - {repo.get('name', 'N/A')} ({repo.get('path', 'N/A')})")
            
            # Check Contributors
            if "Contributor" in labels:
                result = session.run("MATCH (c:Contributor) RETURN c LIMIT 5")
                print("   👥 Contributor samples:")
                for record in result:
                    contributor = record["c"]
                    print(f"     - {contributor.get('name', 'N/A')} ({contributor.get('email', 'N/A')})")
            
            # Check Commits
            if "Commit" in labels:
                result = session.run("MATCH (c:Commit) RETURN c LIMIT 5")
                print("   📝 Commit samples:")
                for record in result:
                    commit = record["c"]
                    print(f"     - {commit.get('hash', 'N/A')[:8]}: {commit.get('message', 'N/A')[:50]}...")
            
            # Check Files
            if "File" in labels:
                result = session.run("MATCH (f:File) RETURN f LIMIT 5")
                print("   📄 File samples:")
                for record in result:
                    file_node = record["f"]
                    print(f"     - {file_node.get('name', 'N/A')} ({file_node.get('size', 0)} bytes)")
            
            # Check relationships between nodes
            print("\n🔗 Relationship Samples:")
            if "AUTHORED" in rel_types:
                result = session.run("""
                    MATCH (u:Contributor)-[r:AUTHORED]->(c:Commit) 
                    RETURN u.name as author, c.hash as commit, r.additions as adds, r.deletions as dels
                    LIMIT 5
                """)
                print("   👤➡️📝 AUTHORED relationships:")
                for record in result:
                    print(f"     - {record['author']} authored {record['commit'][:8]} (+{record['adds'] or 0}/-{record['dels'] or 0})")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error checking Neo4j: {e}")

def test_cypher_queries():
    """Test the actual Cypher queries we use for RAG"""
    print("\n🔍 Testing RAG Cypher Queries")
    print("="*50)
    
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            
            # Test contributor query
            print("👥 Testing contributor query:")
            query = """
            MATCH (u:Contributor)-[r:AUTHORED]->(c:Commit)
            WITH u, count(c) as commit_count, sum(r.additions) as total_adds, sum(r.deletions) as total_dels
            ORDER BY commit_count DESC LIMIT 5
            RETURN u.name as name, u.email as email, commit_count, total_adds, total_dels
            """
            
            result = session.run(query)
            for record in result:
                print(f"   • {record['name']} ({record['email']}): {record['commit_count']} commits, +{record['total_adds'] or 0}/-{record['total_dels'] or 0}")
            
            # Test file query  
            print("\n📄 Testing file query:")
            query = """
            MATCH (f:File)
            RETURN f.name as name, f.size as size, f.language as language
            ORDER BY f.size DESC LIMIT 5
            """
            
            result = session.run(query)
            for record in result:
                print(f"   • {record['name']}: {record['size']} bytes ({record['language']})")
            
            # Test commit query
            print("\n📝 Testing commit query:")
            query = """
            MATCH (c:Commit)
            RETURN c.hash as hash, c.message as message, c.author_name as author, c.date as date
            ORDER BY c.date DESC LIMIT 5
            """
            
            result = session.run(query)
            for record in result:
                date_str = record['date'].strftime('%Y-%m-%d') if record['date'] else 'N/A'
                print(f"   • {record['hash'][:8]}: {record['message'][:50]}... by {record['author']} ({date_str})")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error testing queries: {e}")

if __name__ == "__main__":
    check_neo4j_data()
    test_cypher_queries()