import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class MemoryManager:
    def __init__(self):
        self.db_path = "memory.db"
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self._init_db()
        self._init_faiss()

    def _init_db(self):
        """Initialize SQLite database for long-term memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                prompt TEXT,
                expanded_prompt TEXT,
                image_path TEXT,
                model_path TEXT,
                created_at TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def _init_faiss(self):
        """Initialize FAISS index for similarity search."""
        self.index = faiss.IndexFlatL2(384)  # Dimension for MiniLM embeddings
        self.prompts = []

    def store(self, session_id: str, prompt: str, expanded_prompt: str, 
             image_path: str, model_path: str, metadata: Optional[Dict] = None):
        """Store a generation in both short-term and long-term memory."""
        # Store in SQLite (long-term)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generations 
            (session_id, prompt, expanded_prompt, image_path, model_path, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            prompt,
            expanded_prompt,
            image_path,
            model_path,
            datetime.now(),
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()

        # Store in FAISS (short-term)
        embedding = self.encoder.encode([prompt])[0]
        self.index.add(np.array([embedding], dtype=np.float32))
        self.prompts.append(prompt)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar generations using FAISS."""
        query_embedding = self.encoder.encode([query])[0]
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.prompts):
                results.append({
                    "prompt": self.prompts[idx],
                    "similarity": float(1 / (1 + distance))
                })
        
        return results

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Retrieve all generations for a specific session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT prompt, expanded_prompt, image_path, model_path, created_at, metadata
            FROM generations
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "prompt": row[0],
                "expanded_prompt": row[1],
                "image_path": row[2],
                "model_path": row[3],
                "created_at": row[4],
                "metadata": json.loads(row[5]) if row[5] else None
            })
        
        conn.close()
        return results 