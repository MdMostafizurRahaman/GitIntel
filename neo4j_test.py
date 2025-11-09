#!/usr/bin/env python3
"""
Neo4j Connection Test for GitIntel
"""
import os

print('🔍 Checking Neo4j Environment Variables:')
print(f'NEO4J_URI: {os.getenv("NEO4J_URI", "Not set")}')
print(f'NEO4J_USER: {os.getenv("NEO4J_USER", "Not set")}')
print(f'NEO4J_PASSWORD: {"***" if os.getenv("NEO4J_PASSWORD") else "Not set"}')
print()

print('📊 Testing Neo4j Connection...')
try:
    from neo4j import GraphDatabase
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print('✅ Neo4j Connected Successfully!')

    # Test basic query
    with driver.session() as session:
        result = session.run("RETURN 'GitIntel Ready!' as message")
        record = result.single()
        print(f'📝 Test Query Result: {record["message"]}')

    driver.close()
except Exception as e:
    print(f'❌ Neo4j Connection Failed: {e}')
    print('💡 Follow NEO4J_SETUP_BANGLA.md for setup instructions')
    print('💡 GitIntel will work in offline mode without Neo4j')