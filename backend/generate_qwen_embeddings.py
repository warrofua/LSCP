"""
Generate Qwen embeddings for all concepts to enable dual-view visualization
This creates the "AI" embedding set to compare against MiniLM (human baseline)
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from llama_cpp import Llama
from db.vector_store import VectorStore
from db.relational import LSCPDatabase

# Load configuration
from config import settings

def generate_qwen_embeddings():
    """Generate Qwen embeddings for all concepts in the database"""

    print("=" * 80)
    print("QWEN EMBEDDING GENERATION")
    print("Generating 'Alien' embeddings for dual-view visualization")
    print("=" * 80)

    # Initialize Qwen model
    print("\n1. Loading Qwen model...")
    qwen_model_path = "/Users/joshuafarrow/Downloads/Qwen2.5-14B-Instruct-Q4_K_M.gguf"

    if not Path(qwen_model_path).exists():
        print(f"ERROR: Qwen model not found at {qwen_model_path}")
        print("Please download the model first.")
        sys.exit(1)

    llm = Llama(
        model_path=qwen_model_path,
        n_ctx=512,
        n_batch=32,
        embedding=True,
        verbose=False
    )
    print(f"✓ Qwen model loaded from {qwen_model_path}")

    # Get all concepts from database
    print("\n2. Loading concepts from database...")
    db = LSCPDatabase()
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT concept_a FROM concepts")
    concepts = [row[0] for row in cursor.fetchall()]
    print(f"✓ Found {len(concepts)} concepts")

    # Initialize vector store for Qwen embeddings
    print("\n3. Initializing Qwen vector store...")
    # Use a separate collection for Qwen embeddings
    vector_store = VectorStore(collection_suffix="_qwen")
    print("✓ Qwen vector store initialized")

    # Generate embeddings
    print(f"\n4. Generating Qwen embeddings for {len(concepts)} concepts...")
    print("-" * 80)

    for i, concept in enumerate(concepts, 1):
        try:
            # Generate embedding
            embedding = llm.embed(concept)
            embedding_array = np.array(embedding)

            # Store in both latent and human collections (for compatibility)
            vector_store.add_human_embedding(concept, embedding_array)
            vector_store.add_latent_embedding(concept, embedding_array)

            print(f"[{i}/{len(concepts)}] {concept}: {embedding_array.shape}")

        except Exception as e:
            print(f"ERROR generating embedding for '{concept}': {e}")
            continue

    print("\n" + "=" * 80)
    print("✓ QWEN EMBEDDINGS GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nGenerated embeddings for {len(concepts)} concepts")
    print(f"Dimension: {embedding_array.shape[0]}")
    print("\nThese embeddings are stored in the '_qwen' collection")
    print("and can now be used for dual-view visualization.")


if __name__ == "__main__":
    generate_qwen_embeddings()
