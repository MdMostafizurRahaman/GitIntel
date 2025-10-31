from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_neo4j_graph(uri, password):
    """Check what nodes and relationships were created in Neo4j"""
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))

    with driver.session() as session:
        # Count nodes by type
        print("📊 Neo4j Graph Statistics:")
        print("=" * 50)

        # Count total nodes
        result = session.run("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = result.single()["total_nodes"]
        print(f"Total Nodes: {total_nodes:,}")

        # Count nodes by label - use a different approach
        print("\nNodes by Type:")
        for label in ['Repository', 'Author', 'Package', 'Commit', 'File', 'GitIntelTest']:
            try:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"  {label}: {count:,}")
            except:
                print(f"  {label}: Error counting")

        # Count relationships by type
        print("\nRelationships by Type:")
        for rel_type in ['BELONGS_TO', 'CONTRIBUTES_TO', 'COMMITTED']:
            try:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()["count"]
                print(f"  {rel_type}: {count:,}")
            except:
                print(f"  {rel_type}: Error counting")

        # Sample some data with correct property names
        print("\n📋 Sample Data:")
        print("-" * 30)

        # Sample authors
        result = session.run("MATCH (a:Author) RETURN a.name as name LIMIT 5")
        authors = list(result)
        if authors:
            print("Sample Authors:")
            for author in authors:
                print(f"  {author['name']}")

        # Sample packages with their properties
        result = session.run("MATCH (p:Package) RETURN p.name as name, p.total_churn as churn LIMIT 5")
        packages = list(result)
        if packages:
            print("\nSample Packages:")
            for package in packages:
                churn = package.get('churn', 'N/A')
                print(f"  {package['name']} (churn: {churn:,})")

        # Sample files
        result = session.run("MATCH (f:File) RETURN f.name as name, f.package as package LIMIT 5")
        files = list(result)
        if files:
            print("\nSample Files:")
            for file in files:
                print(f"  {file['name']} (package: {file.get('package', 'N/A')})")

        # Sample commits
        result = session.run("MATCH (c:Commit) RETURN c.hash as hash, c.message as message LIMIT 3")
        commits = list(result)
        if commits:
            print("\nSample Commits:")
            for commit in commits:
                msg = commit['message'][:60] + "..." if len(commit['message']) > 60 else commit['message']
                print(f"  {commit['hash'][:8]}: {msg}")

        # Some interesting queries
        print("\n🔍 Interesting Insights:")
        print("-" * 25)

        # Top churn packages
        result = session.run("MATCH (p:Package) RETURN p.name as name, p.total_churn as churn ORDER BY churn DESC LIMIT 3")
        top_packages = list(result)
        if top_packages:
            print("Top Churn Packages:")
            for pkg in top_packages:
                print(f"  {pkg['name']}: {pkg['churn']:,} lines")

        # Most active authors (by commits)
        result = session.run("MATCH (a:Author)-[:COMMITTED]->(c:Commit) RETURN a.name as name, count(c) as commits ORDER BY commits DESC LIMIT 3")
        active_authors = list(result)
        if active_authors:
            print("\nMost Active Authors:")
            for author in active_authors:
                print(f"  {author['name']}: {author['commits']} commits")

        # Repository info
        result = session.run("MATCH (r:Repository) RETURN r.name as name, r.path as path")
        repo_info = result.single()
        if repo_info:
            print(f"\nRepository: {repo_info['name']}")
            print(f"Path: {repo_info['path']}")

    driver.close()

if __name__ == "__main__":
    uri = os.getenv("NEO4J_URI")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        print("❌ Error: NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        exit(1)

    check_neo4j_graph(uri, password)
    print("\n🎉 Graph analysis complete!")