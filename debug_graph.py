from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_graph_data(uri, password):
    """Debug what data is being created in the graph"""
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))

    with driver.session() as session:
        print("🔍 Debugging Graph Creation Data:")
        print("=" * 50)

        # Check what we have in the database
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
        print("Current database contents:")
        for record in result:
            print(f"  {record['labels']}: {record['count']}")

        # Let's also check relationships
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
        print("\nRelationships:")
        for record in result:
            print(f"  {record['type']}: {record['count']}")

        # Sample some actual nodes
        print("\nSample nodes:")
        result = session.run("MATCH (n) RETURN labels(n) as labels, properties(n) as props LIMIT 10")
        for record in result:
            labels = record['labels']
            props = record['props']
            print(f"  {labels}: {props}")

    driver.close()

def check_excel_data():
    """Check what data is in the Excel files"""
    print("\n📊 Checking Excel Data:")
    print("=" * 30)

    # Find the latest Excel file
    excel_files = [f for f in os.listdir('D:/GitIntel/kafka/analysis_output') if f.endswith('.xlsx')]
    excel_files.sort(reverse=True)
    latest_file = os.path.join('D:/GitIntel/kafka/analysis_output', excel_files[0])

    print(f"Reading: {latest_file}")
    xl = pd.ExcelFile(latest_file)

    for sheet in xl.sheet_names:
        df = pd.read_excel(latest_file, sheet_name=sheet)
        print(f"\n{sheet}: {len(df)} rows")
        if len(df) > 0:
            print("Columns:", list(df.columns))
            print("First row sample:")
            print(df.iloc[0].to_dict())

if __name__ == "__main__":
    uri = os.getenv("NEO4J_URI")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        print("❌ Error: NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        exit(1)

    debug_graph_data(uri, password)
    check_excel_data()

    print("\n🎯 Analysis complete!")