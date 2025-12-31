"""
ChromaDB Vector Store for LSCP
Stores embeddings and performs nearest neighbor searches
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Tuple, Dict
import numpy as np

class VectorStore:
    """Manages vector embeddings and similarity searches"""

    def __init__(self, persist_directory: str, collection_name: str = "lscp_embeddings"):
        self.client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection_name = collection_name
        self._initialize_collections()

    def _initialize_collections(self):
        """Create or load collections for human and latent embeddings"""
        # Human embeddings (MiniLM)
        self.human_collection = self.client.get_or_create_collection(
            name=f"{self.collection_name}_human",
            metadata={"description": "Human semantic embeddings (MiniLM)"}
        )

        # Latent embeddings (llama.cpp)
        self.latent_collection = self.client.get_or_create_collection(
            name=f"{self.collection_name}_latent",
            metadata={"description": "Latent space embeddings (llama.cpp)"}
        )

    def add_human_embedding(self, concept: str, embedding: np.ndarray):
        """Store a human (MiniLM) embedding"""
        try:
            self.human_collection.add(
                embeddings=[embedding.tolist()],
                documents=[concept],
                ids=[concept]
            )
        except Exception as e:
            # If ID already exists, update instead
            if "already exist" in str(e):
                self.human_collection.update(
                    embeddings=[embedding.tolist()],
                    documents=[concept],
                    ids=[concept]
                )
            else:
                raise

    def add_latent_embedding(self, concept: str, embedding: np.ndarray):
        """Store a latent (llama.cpp) embedding"""
        try:
            self.latent_collection.add(
                embeddings=[embedding.tolist()],
                documents=[concept],
                ids=[concept]
            )
        except Exception as e:
            # If ID already exists, update instead
            if "already exist" in str(e):
                self.latent_collection.update(
                    embeddings=[embedding.tolist()],
                    documents=[concept],
                    ids=[concept]
                )
            else:
                raise

    def find_human_neighbors(self, concept: str, n: int = 5) -> List[Tuple[str, float]]:
        """Find N nearest neighbors in human space"""
        results = self.human_collection.query(
            query_texts=[concept],
            n_results=n + 1  # +1 because the concept itself will be included
        )

        neighbors = []
        if results['documents'] and results['distances']:
            for doc, dist in zip(results['documents'][0], results['distances'][0]):
                if doc != concept:  # Exclude the query concept itself
                    neighbors.append((doc, dist))

        return neighbors[:n]

    def find_latent_neighbors(self, concept: str, n: int = 5) -> List[Tuple[str, float]]:
        """Find N nearest neighbors in latent space"""
        results = self.latent_collection.query(
            query_texts=[concept],
            n_results=n + 1
        )

        neighbors = []
        if results['documents'] and results['distances']:
            for doc, dist in zip(results['documents'][0], results['distances'][0]):
                if doc != concept:
                    neighbors.append((doc, dist))

        return neighbors[:n]

    def get_human_embedding(self, concept: str) -> np.ndarray:
        """Retrieve stored human embedding for a concept"""
        result = self.human_collection.get(
            ids=[concept],
            include=["embeddings"]
        )
        if result['embeddings']:
            return np.array(result['embeddings'][0])
        return None

    def get_latent_embedding(self, concept: str) -> np.ndarray:
        """Retrieve stored latent embedding for a concept"""
        result = self.latent_collection.get(
            ids=[concept],
            include=["embeddings"]
        )
        if result['embeddings']:
            return np.array(result['embeddings'][0])
        return None

    def get_all_concepts(self) -> List[str]:
        """Get all concepts stored in the database"""
        human_results = self.human_collection.get()
        return human_results['ids'] if human_results['ids'] else []

    def concept_exists(self, concept: str) -> bool:
        """Check if a concept has been embedded"""
        result = self.human_collection.get(ids=[concept])
        return len(result['ids']) > 0

    def get_all_embeddings(self, space: str = "human") -> Tuple[List[str], np.ndarray]:
        """
        Get all embeddings from a space
        Returns: (concept_names, embeddings_matrix)
        """
        collection = self.human_collection if space == "human" else self.latent_collection
        results = collection.get(include=["embeddings"])

        if results['ids'] and results['embeddings']:
            concepts = results['ids']
            embeddings = np.array(results['embeddings'])
            return concepts, embeddings

        return [], np.array([])

    def persist(self):
        """Persist the vector store to disk"""
        # ChromaDB with persist_directory automatically persists
        pass
