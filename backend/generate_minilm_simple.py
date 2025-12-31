"""
Simple MiniLM embedding generator - bypasses ChromaDB to avoid version issues
"""
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Configuration
DB_PATH = "/Users/joshuafarrow/Projects/LSCP/data/lscp.db"
OUTPUT_FILE = "/Users/joshuafarrow/Projects/LSCP/data/minilm_embeddings.npz"

def main():
    print("=" * 80)
    print("MINILM EMBEDDING GENERATION (Standalone)")
    print("=" * 80)

    # 1. Load MiniLM model
    print("\n1. Loading MiniLM model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"✓ MiniLM model loaded")

    # 2. Get concepts from database
    print("\n2. Loading concepts from database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM concepts ORDER BY name")
    concepts = [row[0] for row in cursor.fetchall()]
    conn.close()
    print(f"✓ Found {len(concepts)} concepts")

    # 3. Generate embeddings
    print(f"\n3. Generating embeddings...")
    print("-" * 80)

    embeddings_dict = {}

    for i, concept in enumerate(concepts, 1):
        try:
            # Generate embedding
            embedding = model.encode(concept)
            embeddings_dict[concept] = np.array(embedding)

            if i % 10 == 0:
                print(f"[{i}/{len(concepts)}] {concept}: shape={embeddings_dict[concept].shape}")
            else:
                print(f"[{i}/{len(concepts)}] {concept}")

        except Exception as e:
            print(f"ERROR on '{concept}': {e}")
            continue

    # 4. Save embeddings
    print(f"\n4. Saving embeddings to {OUTPUT_FILE}...")
    np.savez_compressed(OUTPUT_FILE, **embeddings_dict)
    print(f"✓ Saved {len(embeddings_dict)} embeddings")

    # Print sample
    sample_concept = concepts[0]
    sample_emb = embeddings_dict[sample_concept]
    print(f"\nSample: '{sample_concept}' → {sample_emb.shape} dims")
    print(f"First 5 values: {sample_emb[:5]}")

    print("\n" + "=" * 80)
    print("✓ COMPLETE")
    print("=" * 80)
    print(f"\nEmbeddings saved to: {OUTPUT_FILE}")
    print("These can now be loaded by the dual-layout visualization system.")


if __name__ == "__main__":
    main()
