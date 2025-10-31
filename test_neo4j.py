#!/usr/bin/env python3
"""
Neo4j Connection Test Script
Test your Neo4j Desktop connection before running the main analyzer
"""

from neo4j import GraphDatabase
import sys

def test_neo4j_connection(uri, user, password):
    """Test Neo4j connection and basic operations"""
    try:
        print(f"🔗 Connecting to Neo4j at: {uri}")
        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            # Test basic query
            result = session.run("RETURN 'GitIntel Neo4j Test' as message")
            record = result.single()
            print(f"✅ Connection successful: {record['message']}")

            # Clear any existing data
            session.run("MATCH (n) DETACH DELETE n")
            print("🧹 Cleared existing data")

            # Create test nodes
            session.run("CREATE (:TestNode {name: 'GitIntel', type: 'RepositoryAnalyzer'})")
            print("📍 Created test node")

            # Query test node
            result = session.run("MATCH (n:TestNode) RETURN n.name as name, n.type as type")
            for record in result:
                print(f"📊 Test node found: {record['name']} ({record['type']})")

        driver.close()
        print("🎉 Neo4j connection test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Neo4j connection test FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Neo4j Desktop is running")
        print("2. Check that your database is started")
        print("3. Verify the connection details (URI, username, password)")
        print("4. Check firewall settings for port 7687")
        return False

if __name__ == "__main__":
    # Neo4j Aura Cloud Settings
    NEO4J_URI = input("Enter your Neo4j Aura connection URI (neo4j+s://xxxxx.databases.neo4j.io): ")
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = input("Enter your Neo4j Aura password: ")

    success = test_neo4j_connection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    if success:
        print("\n🚀 Ready to run GitIntel with Neo4j Aura!")
        print(f"URI: {NEO4J_URI}")
        print("Command: python git_analyzer_tool.py D:\\GitIntel\\kafka --create-graph --neo4j-uri YOUR_URI --neo4j-password YOUR_PASSWORD")
    else:
        print("\n❌ Fix connection issues before proceeding")
        sys.exit(1)