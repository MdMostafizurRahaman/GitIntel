#!/usr/bin/env python3
"""
Quick Neo4j Aura Test
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Aura connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    print("❌ Error: NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in .env file")
    exit(1)

try:
    print(f"🔗 Connecting to Neo4j Aura at: {NEO4J_URI}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        result = session.run("RETURN 'GitIntel Connected!' as message")
        record = result.single()
        print(f"✅ SUCCESS: {record['message']}")

        # Create a test node
        session.run("CREATE (:GitIntelTest {name: 'Success', timestamp: datetime()})")
        print("📍 Created test node in Aura")

    driver.close()
    print("🎉 Neo4j Aura connection test PASSED!")

except Exception as e:
    print(f"❌ FAILED: {e}")
    print("Check your connection details and try again")