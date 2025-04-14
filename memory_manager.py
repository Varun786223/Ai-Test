import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import json
from datetime import datetime
from typing import List, Dict, Any

class MemoryManager:
    def __init__(self, persist_directory: str = "memory"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=os.path.join(persist_directory, "chroma"),
            settings=Settings(allow_reset=True)
        )
        
        # Initialize collection
        self.collection = self.client.get_or_create_collection(
            name="generation_history",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load existing history
        self.history_file = os.path.join(persist_directory, "history.json")
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_generation(self, prompt: str, expanded_prompt: str, image_path: str, model_path: str):
        # Generate embedding
        embedding = self.encoder.encode(prompt).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=[embedding],
            documents=[prompt],
            metadatas=[{
                "expanded_prompt": expanded_prompt,
                "image_path": image_path,
                "model_path": model_path,
                "timestamp": datetime.now().isoformat()
            }],
            ids=[str(len(self.history))]
        )
        
        # Add to history
        self.history.append({
            "prompt": prompt,
            "expanded_prompt": expanded_prompt,
            "image_path": image_path,
            "model_path": model_path,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_history()
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        # Generate query embedding
        query_embedding = self.encoder.encode(query).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "prompt": results['documents'][0][i],
                "metadata": results['metadatas'][0][i]
            })
        
        return formatted_results
    
    def get_history(self) -> List[Dict[str, Any]]:
        return self.history
    
    def get_generation_by_id(self, generation_id: str) -> Dict[str, Any]:
        try:
            return self.history[int(generation_id)]
        except (IndexError, ValueError):
            return None 