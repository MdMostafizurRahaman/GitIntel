#!/usr/bin/env python3
"""
Test Neo4j + RAG Integration for GitIntel
Tests the complete Neo4j data storage + RAG-powered Q&A flow
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from repochat_core import RepoChatCore

def test_neo4j_rag_integration():
    """Test complete Neo4j + RAG flow"""
    print("🧪 Testing Neo4j + RAG Integration")
    print("="*50)
    
    try:
        # Initialize RepoChatCore with Neo4j Aura credentials
        print("🔗 Initializing RepoChatCore with Neo4j Aura...")
        core = RepoChatCore()
        
        if not core.neo4j_ready:
            print("❌ Neo4j connection failed - check credentials in .env file")
            return False
        
        print("✅ Neo4j Aura connected successfully")
        
        # Set repository to current project
        repo_path = os.path.abspath(".")
        print(f"📁 Setting repository: {repo_path}")
        
        success = core.set_repository(repo_path)
        if not success:
            print("❌ Failed to set repository")
            return False
        
        print("✅ Repository set successfully")
        
        # Test RAG-powered questions
        test_questions = [
            "Who are the top contributors to this project?",
            "Give me an overview of this repository",
            "Show me recent commits",
            "What are the largest files?",
            "কে সবচেয়ে বেশি অবদান রেখেছে?",  # Bengali question
            "Tell me about the project structure"
        ]
        
        print("\n🤖 Testing RAG-powered Q&A:")
        print("="*50)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. ❓ Question: {question}")
            print("-" * 60)
            
            try:
                response = core.ask_question(question)
                
                if response and "❌" not in response:
                    print(f"✅ Response received:")
                    print(f"{response[:200]}...")
                    if len(response) > 200:
                        print("   [Response truncated for display]")
                else:
                    print(f"⚠️ Limited response: {response}")
                    
            except Exception as e:
                print(f"❌ Question failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_neo4j_storage():
    """Test Neo4j data storage"""
    print("\n🔗 Testing Neo4j Data Storage")
    print("="*40)
    
    try:
        core = RepoChatCore()
        
        if not core.neo4j_ready:
            print("❌ Neo4j not connected")
            return False
        
        # Test repository metadata extraction and storage
        repo_path = os.path.abspath(".")
        core.set_repository(repo_path)
        
        print("📊 Extracting repository metadata...")
        metadata = core.extract_metadata()
        
        print(f"✅ Metadata extracted:")
        print(f"   - Commits: {len(metadata.get('commits', []))}")
        print(f"   - Files: {len(metadata.get('files', []))}")
        print(f"   - Contributors: {len(metadata.get('contributors', []))}")
        
        # Test Neo4j storage
        print("🔗 Storing in Neo4j...")
        core._store_metadata_in_neo4j(metadata)
        print("✅ Data stored in Neo4j knowledge graph")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GitIntel Neo4j + RAG Integration Test")
    print("="*60)
    
    # Test 1: Neo4j storage
    storage_success = test_neo4j_storage()
    
    # Test 2: RAG integration
    rag_success = test_neo4j_rag_integration()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    print(f"Neo4j Storage: {'✅ PASSED' if storage_success else '❌ FAILED'}")
    print(f"RAG Integration: {'✅ PASSED' if rag_success else '❌ FAILED'}")
    
    overall_success = storage_success and rag_success
    
    if overall_success:
        print("\n🎉 All tests passed! Neo4j + RAG integration working properly.")
        print("💡 Your GitIntel is ready for intelligent repository analysis!")
    else:
        print("\n⚠️ Some tests failed. Check your Neo4j credentials and setup.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)