#!/usr/bin/env python3
"""
Debug RepoChat Knowledge Graph
Check what data is actually loaded in the knowledge graph
"""

import json
import os
from repochat_knowledge_graph import KnowledgeGraphBuilder
from repochat_core import RepoChatCore

def debug_knowledge_graph(repo_path):
    """Debug the knowledge graph content"""
    print(f"🔍 Debugging Knowledge Graph for: {repo_path}")
    print("="*60)
    
    # Initialize components
    kg_builder = KnowledgeGraphBuilder()
    core = RepoChatCore()
    
    # Set repository
    if core.set_repository(repo_path):
        print(f"✅ Repository set: {repo_path}")
    else:
        print(f"❌ Failed to set repository: {repo_path}")
        return
    
    # Check if knowledge graph file exists
    graph_file = '.repochat_graph.json'
    if os.path.exists(graph_file):
        print(f"✅ Knowledge graph file exists: {graph_file}")
        
        # Load and analyze the graph
        with open(graph_file, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        print(f"📊 Graph Statistics:")
        print(f"   Total nodes: {len(graph_data.get('nodes', {}))}")
        print(f"   Total relationships: {len(graph_data.get('relationships', []))}")
        
        # Analyze node types
        node_types = {}
        sample_nodes = {}
        
        for node_id, node in graph_data.get('nodes', {}).items():
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # Keep sample of each type
            if node_type not in sample_nodes:
                sample_nodes[node_type] = node.get('properties', {})
        
        print(f"\n📋 Node Types:")
        for node_type, count in sorted(node_types.items()):
            print(f"   {node_type}: {count} nodes")
        
        # Show sample contributor data
        if 'Contributor' in sample_nodes:
            print(f"\n👤 Sample Contributor:")
            contributor = sample_nodes['Contributor']
            for key, value in contributor.items():
                print(f"   {key}: {value}")
        
        # Analyze relationships
        relationship_types = {}
        for rel in graph_data.get('relationships', []):
            rel_type = rel.get('type', 'Unknown')
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        print(f"\n🔗 Relationship Types:")
        for rel_type, count in sorted(relationship_types.items()):
            print(f"   {rel_type}: {count} relationships")
        
        # Test specific contributor search
        print(f"\n🔍 Testing Contributor Search:")
        contributors = []
        for node in graph_data.get('nodes', {}).values():
            if node.get('type') == 'Contributor':
                contributors.append(node.get('properties', {}))
        
        # Sort by commits
        contributors.sort(key=lambda x: x.get('commits', 0), reverse=True)
        
        print(f"📊 Top 5 Contributors:")
        for i, contributor in enumerate(contributors[:5], 1):
            name = contributor.get('name', 'Unknown')
            commits = contributor.get('commits', 0)
            email = contributor.get('email', 'Unknown')
            print(f"   {i}. {name} ({email}) - {commits} commits")
        
        # Test specific commit count
        print(f"\n🔍 Contributors with exactly 2 commits:")
        exactly_2 = [c for c in contributors if c.get('commits', 0) == 2]
        for contributor in exactly_2[:5]:
            name = contributor.get('name', 'Unknown')
            email = contributor.get('email', 'Unknown')
            print(f"   - {name} ({email})")
        
        if not exactly_2:
            print("   No contributors found with exactly 2 commits")
        
        # Test name search
        print(f"\n🔍 Contributors containing 'rakib' (case insensitive):")
        rakib_contributors = []
        for c in contributors:
            name = c.get('name', '').lower()
            email = c.get('email', '').lower()
            if 'rakib' in name or 'rakib' in email:
                rakib_contributors.append(c)
        
        if rakib_contributors:
            for contributor in rakib_contributors:
                name = contributor.get('name', 'Unknown')
                email = contributor.get('email', 'Unknown')
                commits = contributor.get('commits', 0)
                print(f"   - {name} ({email}) - {commits} commits")
        else:
            print("   No contributors found containing 'rakib'")
        
        # Debug commits and their dates
        print("\n🔍 Sample Commits with Dates:")
        commit_count = 0
        for node_id, node_data in kg_builder.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Commit' and commit_count < 5:
                props = node_data['properties']
                print(f"   Commit {commit_count + 1}:")
                print(f"     Hash: {props.get('hash', 'N/A')[:10]}...")
                print(f"     Date: {props.get('date', 'N/A')}")
                print(f"     Author: {props.get('author_name', 'N/A')}")
                print(f"     Message: {props.get('message', 'N/A')[:50]}...")
                print()
                commit_count += 1
        
        # Test today's date query
        print("\n🔍 Testing Today's Date Query:")
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"   Today's date: {today}")
        
        # Count commits for today
        today_commits = 0
        for node_id, node_data in kg_builder.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Commit':
                commit_date = node_data['properties'].get('date', '')
                if commit_date.startswith(today):
                    today_commits += 1
        
        print(f"   Commits found for today ({today}): {today_commits}")
        
        # Show some recent commits
        print("\n🔍 Most Recent Commits (by date):")
        recent_commits = []
        for node_id, node_data in kg_builder.in_memory_graph['nodes'].items():
            if node_data['type'] == 'Commit':
                props = node_data['properties']
                if 'date' in props:
                    recent_commits.append(props)
        
        # Sort by date (most recent first)
        recent_commits.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        for i, commit in enumerate(recent_commits[:5]):
            print(f"   {i+1}. {commit.get('date', 'N/A')} - {commit.get('author_name', 'N/A')}")
            print(f"      {commit.get('message', 'N/A')[:60]}...")
            print()
        
    else:
        print(f"❌ Knowledge graph file not found: {graph_file}")
        print("💡 Try rebuilding the knowledge graph:")
        print(f"   python repochat_cli.py --repo \"{repo_path}\" --ingest")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = input("Enter repository path: ").strip()
    
    debug_knowledge_graph(repo_path)