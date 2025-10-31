#!/usr/bin/env python3
"""
RAG Vector Database - Document Embedding and Retrieval System for GitIntel
Provides intelligent document retrieval using embeddings and similarity search
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pickle
from datetime import datetime
import hashlib

# Try to import vector database libraries
VECTOR_DB_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
    VECTOR_DB_AVAILABLE = True
    print("✅ ChromaDB available for vector storage")
except ImportError:
    CHROMA_AVAILABLE = False
    try:
        import faiss
        import numpy as np
        FAISS_AVAILABLE = True
        VECTOR_DB_AVAILABLE = True
        print("✅ FAISS available for vector storage")
    except ImportError:
        FAISS_AVAILABLE = False
        print("⚠️ No vector database available, using simple text search")

# Try to import embedding models
EMBEDDING_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    EMBEDDING_AVAILABLE = True
    print("✅ SentenceTransformers available for embeddings")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    try:
        import google.generativeai as genai
        GEMINI_EMBEDDINGS_AVAILABLE = True
        EMBEDDING_AVAILABLE = True
        print("✅ Gemini embeddings available")
    except ImportError:
        GEMINI_EMBEDDINGS_AVAILABLE = False
        print("⚠️ No embedding model available, using keyword search")

class RAGVectorDatabase:
    def __init__(self, repo_path: str = None, embedding_model: str = "all-MiniLM-L6-v2"):
        self.logger = logging.getLogger(__name__)
        self.repo_path = repo_path
        self.repo_name = os.path.basename(repo_path) if repo_path else "default"
        
        # Database files
        self.db_dir = f".rag_db_{self.repo_name}"
        self.metadata_file = os.path.join(self.db_dir, "metadata.json")
        self.documents_file = os.path.join(self.db_dir, "documents.pkl")
        
        # Initialize embedding model
        self.embedding_model = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        self._init_embedding_model(embedding_model)
        
        # Initialize vector database
        self.vector_db = None
        self.chroma_client = None
        self.chroma_collection = None
        self.faiss_index = None
        self._init_vector_db()
        
        # Document storage
        self.documents = []
        self.document_metadata = {}
        
        # Create database directory
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Load existing data
        self.load_database()
    
    def _init_embedding_model(self, model_name: str):
        """Initialize embedding model"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer(model_name)
                self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                self.logger.info(f"Loaded SentenceTransformer model: {model_name}")
            elif GEMINI_EMBEDDINGS_AVAILABLE:
                # Setup Gemini for embeddings
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.embedding_model = "gemini"
                    self.embedding_dim = 768  # Gemini embedding dimension
                    self.logger.info("Using Gemini embeddings")
                else:
                    self.logger.warning("GEMINI_API_KEY not found")
            else:
                self.logger.warning("No embedding model available, using keyword search")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
    
    def _init_vector_db(self):
        """Initialize vector database"""
        try:
            if CHROMA_AVAILABLE:
                self.chroma_client = chromadb.PersistentClient(
                    path=os.path.join(self.db_dir, "chroma_db")
                )
                collection_name = f"repo_{self.repo_name}"
                try:
                    self.chroma_collection = self.chroma_client.get_collection(collection_name)
                except:
                    self.chroma_collection = self.chroma_client.create_collection(collection_name)
                self.vector_db = "chroma"
                self.logger.info("ChromaDB initialized")
                
            elif FAISS_AVAILABLE:
                # FAISS will be initialized when first document is added
                self.vector_db = "faiss"
                self.logger.info("FAISS will be initialized on first use")
            else:
                self.vector_db = "simple"
                self.logger.info("Using simple keyword search")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize vector database: {e}")
            self.vector_db = "simple"
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE and self.embedding_model:
                embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
                return embeddings.tolist()
                
            elif GEMINI_EMBEDDINGS_AVAILABLE and self.embedding_model == "gemini":
                embeddings = []
                for text in texts:
                    try:
                        result = genai.embed_content(
                            model="models/embedding-001",
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings.append(result['embedding'])
                    except Exception as e:
                        self.logger.error(f"Gemini embedding failed: {e}")
                        # Fallback to zero vector
                        embeddings.append([0.0] * self.embedding_dim)
                return embeddings
            else:
                # Fallback: simple keyword-based "embeddings"
                return [[float(hash(text) % 1000) / 1000] * self.embedding_dim for text in texts]
                
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return [[0.0] * self.embedding_dim] * len(texts)
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database"""
        try:
            if not documents:
                return True
            
            self.logger.info(f"Adding {len(documents)} documents to vector database...")
            
            # Prepare documents for embedding
            texts = []
            doc_ids = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                # Create document text for embedding
                text_parts = []
                
                if doc.get('type') == 'commit':
                    text_parts.append(f"Commit: {doc.get('message', '')}")
                    text_parts.append(f"Author: {doc.get('author_name', '')}")
                    text_parts.append(f"Date: {doc.get('date', '')}")
                    if doc.get('is_bug_fix'):
                        text_parts.append("Bug fix")
                        
                elif doc.get('type') == 'file':
                    text_parts.append(f"File: {doc.get('name', '')}")
                    text_parts.append(f"Language: {doc.get('language', '')}")
                    text_parts.append(f"Path: {doc.get('path', '')}")
                    
                elif doc.get('type') == 'contributor':
                    text_parts.append(f"Contributor: {doc.get('name', '')}")
                    text_parts.append(f"Email: {doc.get('email', '')}")
                    text_parts.append(f"Commits: {doc.get('commits', 0)}")
                
                text = " | ".join(text_parts)
                texts.append(text)
                
                # Generate unique document ID
                doc_id = f"{doc.get('type', 'doc')}_{i}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
                doc_ids.append(doc_id)
                
                # Prepare metadata
                metadata = doc.copy()
                metadata['text'] = text
                metadata['timestamp'] = datetime.now().isoformat()
                metadatas.append(metadata)
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Store in vector database
            if self.vector_db == "chroma" and self.chroma_collection:
                self._add_to_chroma(doc_ids, texts, embeddings, metadatas)
            elif self.vector_db == "faiss":
                self._add_to_faiss(doc_ids, texts, embeddings, metadatas)
            else:
                self._add_to_simple_store(doc_ids, texts, metadatas)
            
            # Update local storage
            self.documents.extend(documents)
            for doc_id, metadata in zip(doc_ids, metadatas):
                self.document_metadata[doc_id] = metadata
            
            # Save database
            self.save_database()
            
            self.logger.info(f"Successfully added {len(documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False
    
    def _add_to_chroma(self, doc_ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        """Add documents to ChromaDB"""
        try:
            # Convert metadata to strings for ChromaDB
            chroma_metadata = []
            for metadata in metadatas:
                chroma_meta = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_meta[key] = str(value)
                    else:
                        chroma_meta[key] = json.dumps(value)
                chroma_metadata.append(chroma_meta)
            
            self.chroma_collection.add(
                ids=doc_ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=chroma_metadata
            )
        except Exception as e:
            self.logger.error(f"ChromaDB addition failed: {e}")
    
    def _add_to_faiss(self, doc_ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict]):
        """Add documents to FAISS"""
        try:
            if not FAISS_AVAILABLE:
                return
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Initialize FAISS index if not exists
            if self.faiss_index is None:
                self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
            
            # Add to FAISS
            self.faiss_index.add(embeddings_array)
            
            # Save FAISS index
            faiss_index_file = os.path.join(self.db_dir, "faiss.index")
            faiss.write_index(self.faiss_index, faiss_index_file)
            
        except Exception as e:
            self.logger.error(f"FAISS addition failed: {e}")
    
    def _add_to_simple_store(self, doc_ids: List[str], texts: List[str], metadatas: List[Dict]):
        """Add documents to simple keyword store"""
        # Documents are stored in self.document_metadata
        pass
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        try:
            if self.vector_db == "chroma" and self.chroma_collection:
                return self._search_chroma(query, limit)
            elif self.vector_db == "faiss" and self.faiss_index:
                return self._search_faiss(query, limit)
            else:
                return self._search_simple(query, limit)
                
        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            return []
    
    def _search_chroma(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using ChromaDB"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search ChromaDB
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # Parse JSON metadata back
                parsed_metadata = {}
                for key, value in metadata.items():
                    try:
                        parsed_metadata[key] = json.loads(value)
                    except:
                        parsed_metadata[key] = value
                
                search_results.append({
                    'document': doc,
                    'metadata': parsed_metadata,
                    'similarity_score': 1 - distance,  # Convert distance to similarity
                    'rank': i + 1
                })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"ChromaDB search failed: {e}")
            return []
    
    def _search_faiss(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using FAISS"""
        try:
            if not FAISS_AVAILABLE or not self.faiss_index:
                return []
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search FAISS
            scores, indices = self.faiss_index.search(query_vector, limit)
            
            # Format results
            search_results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    search_results.append({
                        'document': self.documents[idx],
                        'metadata': self.documents[idx],
                        'similarity_score': float(score),
                        'rank': i + 1
                    })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"FAISS search failed: {e}")
            return []
    
    def _search_simple(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Simple keyword-based search"""
        try:
            query_lower = query.lower()
            query_keywords = query_lower.split()
            
            search_results = []
            
            for doc_id, metadata in self.document_metadata.items():
                text = metadata.get('text', '').lower()
                
                # Calculate simple keyword match score
                score = 0
                for keyword in query_keywords:
                    if keyword in text:
                        score += 1
                
                if score > 0:
                    search_results.append({
                        'document': metadata.get('text', ''),
                        'metadata': metadata,
                        'similarity_score': score / len(query_keywords),
                        'rank': 0
                    })
            
            # Sort by score and limit
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Update ranks
            for i, result in enumerate(search_results[:limit]):
                result['rank'] = i + 1
            
            return search_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Simple search failed: {e}")
            return []
    
    def get_relevant_context(self, question: str, limit: int = 5) -> str:
        """Get relevant context for RAG-based question answering"""
        try:
            # Search for relevant documents
            search_results = self.search_documents(question, limit)
            
            if not search_results:
                return "No relevant context found."
            
            # Build context string
            context_parts = []
            context_parts.append(f"🔍 Relevant context for: {question}\n")
            
            for result in search_results:
                metadata = result['metadata']
                doc_type = metadata.get('type', 'unknown')
                score = result['similarity_score']
                
                context_parts.append(f"📄 {doc_type.title()} (relevance: {score:.2f}):")
                
                if doc_type == 'commit':
                    context_parts.append(f"   • Commit: {metadata.get('hash', '')[:8]}")
                    context_parts.append(f"   • Message: {metadata.get('message', '')}")
                    context_parts.append(f"   • Author: {metadata.get('author_name', '')}")
                    context_parts.append(f"   • Date: {metadata.get('date', '')}")
                    
                elif doc_type == 'file':
                    context_parts.append(f"   • File: {metadata.get('name', '')}")
                    context_parts.append(f"   • Language: {metadata.get('language', '')}")
                    context_parts.append(f"   • Lines: {metadata.get('lines_of_code', 0)}")
                    
                elif doc_type == 'contributor':
                    context_parts.append(f"   • Name: {metadata.get('name', '')}")
                    context_parts.append(f"   • Commits: {metadata.get('commits', 0)}")
                
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Context retrieval failed: {e}")
            return f"Error retrieving context: {e}"
    
    def save_database(self):
        """Save database state to disk"""
        try:
            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'repo_name': self.repo_name,
                    'repo_path': self.repo_path,
                    'document_count': len(self.documents),
                    'vector_db': self.vector_db,
                    'embedding_dim': self.embedding_dim,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            
            # Save documents
            with open(self.documents_file, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'document_metadata': self.document_metadata
                }, f)
            
            self.logger.info("Database state saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save database: {e}")
    
    def load_database(self):
        """Load database state from disk"""
        try:
            # Load documents
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.document_metadata = data.get('document_metadata', {})
                
                self.logger.info(f"Loaded {len(self.documents)} documents from database")
            
            # Load FAISS index if available
            if self.vector_db == "faiss":
                faiss_index_file = os.path.join(self.db_dir, "faiss.index")
                if os.path.exists(faiss_index_file) and FAISS_AVAILABLE:
                    self.faiss_index = faiss.read_index(faiss_index_file)
                    self.logger.info("FAISS index loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load database: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'repo_name': self.repo_name,
            'vector_db': self.vector_db,
            'embedding_model': type(self.embedding_model).__name__ if self.embedding_model else None,
            'document_count': len(self.documents),
            'embedding_dimension': self.embedding_dim,
            'database_size_mb': self._get_database_size()
        }
        
        # Count documents by type
        type_counts = {}
        for doc in self.documents:
            doc_type = doc.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        stats['document_types'] = type_counts
        return stats
    
    def _get_database_size(self) -> float:
        """Calculate database size in MB"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.db_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            return total_size / (1024 * 1024)
        except:
            return 0.0

# Example usage
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
        
        # Initialize RAG database
        rag_db = RAGVectorDatabase(repo_path=repo_path)
        
        # Example: add some test documents
        test_documents = [
            {
                'type': 'commit',
                'hash': 'abc123',
                'message': 'Fix memory leak in data processor',
                'author_name': 'John Doe',
                'date': '2024-01-15',
                'is_bug_fix': True
            },
            {
                'type': 'file',
                'name': 'processor.py',
                'language': 'Python',
                'path': 'src/processor.py',
                'lines_of_code': 450
            },
            {
                'type': 'contributor',
                'name': 'John Doe',
                'email': 'john@example.com',
                'commits': 125
            }
        ]
        
        # Add documents
        success = rag_db.add_documents(test_documents)
        if success:
            print("✅ Documents added successfully")
            
            # Test search
            print("\n🔍 Testing search:")
            results = rag_db.search_documents("memory leak fix", limit=3)
            for result in results:
                print(f"  • {result['metadata'].get('type', 'unknown')}: {result['similarity_score']:.3f}")
            
            # Test context retrieval
            print("\n📄 Testing context retrieval:")
            context = rag_db.get_relevant_context("Who fixed the memory leak?")
            print(context[:200] + "...")
            
            # Show database stats
            print("\n📊 Database statistics:")
            stats = rag_db.get_database_stats()
            for key, value in stats.items():
                print(f"  • {key}: {value}")
        else:
            print("❌ Failed to add documents")
    else:
        print("Usage: python rag_vector_database.py <repo_path>")