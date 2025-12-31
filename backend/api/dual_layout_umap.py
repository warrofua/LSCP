"""
UMAP-Based Dual-Layout Generation with Procrustes Alignment
Creates aligned 3D coordinates using UMAP manifold reduction
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from typing import Dict, Tuple
import sqlite3

try:
    import umap
except ImportError:
    print("ERROR: umap-learn not installed. Install with: pip install umap-learn")
    sys.exit(1)


def align_umap_coords(
    human_coords: np.ndarray,
    ai_coords: np.ndarray,
    concept_names: list
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray], float]:
    """
    Align AI UMAP coordinates to Human UMAP coordinates using Procrustes

    Args:
        human_coords: Human UMAP coordinates (N x 3)
        ai_coords: AI UMAP coordinates (N x 3)
        concept_names: List of concept names

    Returns:
        (aligned_human_dict, aligned_ai_dict, disparity)
    """
    # Center both
    human_centered = human_coords - np.mean(human_coords, axis=0)
    ai_centered = ai_coords - np.mean(ai_coords, axis=0)

    # Rotation-only Procrustes (preserve scale to show manifold differences)
    U, S, Vt = np.linalg.svd(ai_centered.T @ human_centered)
    R = U @ Vt
    ai_rotated = ai_centered @ R

    # Compute disparity
    disparity = np.sqrt(np.sum((human_centered - ai_rotated) ** 2) / len(concept_names))

    # Scale for visualization (apply equally to preserve relative differences)
    scale_factor = 3.75 / np.std(human_centered)
    human_scaled = human_centered * scale_factor
    ai_scaled = ai_rotated * scale_factor

    # Convert to dictionaries
    aligned_human = {name: human_scaled[i] for i, name in enumerate(concept_names)}
    aligned_ai = {name: ai_scaled[i] for i, name in enumerate(concept_names)}

    print(f"   UMAP Procrustes alignment complete")
    print(f"   Disparity: {disparity:.4f}")
    print(f"   Scale factor: {scale_factor:.4f}")

    return aligned_human, aligned_ai, disparity


def generate_umap_layout():
    """
    Generate UMAP-based dual-view layout

    Returns:
        Dict with structure:
        {
            "nodes": [
                {
                    "name": "love",
                    "pos_human_umap": [x, y, z],
                    "pos_ai_umap": [x, y, z],
                    "drift_umap": distance,
                    ...
                }
            ],
            "metadata": {
                "disparity_umap": float,
                "num_concepts": int,
                "method": "UMAP manifold reduction"
            }
        }
    """
    print("\n" + "=" * 80)
    print("UMAP MANIFOLD-BASED DUAL LAYOUT GENERATION")
    print("=" * 80)

    # Database and embedding paths
    db_path = "/Users/joshuafarrow/Projects/LSCP/data/lscp.db"
    minilm_npz_path = "/Users/joshuafarrow/Projects/LSCP/data/minilm_embeddings.npz"
    qwen_npz_path = "/Users/joshuafarrow/Projects/LSCP/data/qwen_embeddings.npz"

    # Get concepts from database
    print("\n1. Loading concepts from database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM concepts ORDER BY name")
    concepts = [row[0] for row in cursor.fetchall()]
    print(f"   Found {len(concepts)} concepts")

    # Load embeddings
    print("\n2. Loading embeddings...")
    print(f"   Loading MiniLM embeddings from {minilm_npz_path}...")
    minilm_data = np.load(minilm_npz_path)

    print(f"   Loading Qwen embeddings from {qwen_npz_path}...")
    qwen_data = np.load(qwen_npz_path)

    # Build embedding matrices
    human_embeddings = []
    ai_embeddings = []
    valid_concepts = []

    for concept in concepts:
        if concept in minilm_data and concept in qwen_data:
            # MiniLM embedding
            h_emb = minilm_data[concept]
            if len(h_emb.shape) > 1:
                h_emb = h_emb.flatten()

            # Qwen embedding
            a_emb = qwen_data[concept]
            if len(a_emb.shape) > 1:
                a_emb = a_emb.flatten()
            if a_emb.shape[0] > 5120:
                a_emb = a_emb[:5120]

            human_embeddings.append(h_emb)
            ai_embeddings.append(a_emb)
            valid_concepts.append(concept)

    human_matrix = np.array(human_embeddings)
    ai_matrix = np.array(ai_embeddings)

    print(f"   ✓ Human (MiniLM): {human_matrix.shape}")
    print(f"   ✓ AI (Qwen): {ai_matrix.shape}")

    # Apply UMAP reduction
    print("\n3. Applying UMAP manifold reduction...")
    print("   Reducing Human embeddings to 3D...")
    umap_human = umap.UMAP(
        n_components=3,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )
    human_coords = umap_human.fit_transform(human_matrix)
    print(f"   ✓ Human UMAP complete: {human_coords.shape}")

    print("   Reducing AI embeddings to 3D...")
    umap_ai = umap.UMAP(
        n_components=3,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=43
    )
    ai_coords = umap_ai.fit_transform(ai_matrix)
    print(f"   ✓ AI UMAP complete: {ai_coords.shape}")

    # Align the UMAP coordinates
    print("\n4. Aligning UMAP manifolds (Procrustes)...")
    aligned_human, aligned_ai, disparity = align_umap_coords(
        human_coords, ai_coords, valid_concepts
    )

    # Build node data
    print("\n5. Building node data...")
    nodes = []

    for concept in valid_concepts:
        h_pos = aligned_human[concept]
        a_pos = aligned_ai[concept]
        drift = np.linalg.norm(h_pos - a_pos)

        # Get concept metadata from database
        cursor.execute("""
            SELECT AVG(r.human_distance), COUNT(*)
            FROM relationships r
            JOIN concepts c1 ON r.concept_a_id = c1.id
            JOIN concepts c2 ON r.concept_b_id = c2.id
            WHERE c1.name = ? OR c2.name = ?
        """, (concept, concept))
        avg_dist, conn_count = cursor.fetchone()

        nodes.append({
            "id": concept,
            "name": concept,
            "pos_human_umap": h_pos.tolist(),
            "pos_ai_umap": a_pos.tolist(),
            "drift_umap": float(drift),
            "avgDistance": float(avg_dist or 0.5),
            "connections": int(conn_count or 0)
        })

    # Sort by drift
    nodes.sort(key=lambda n: n["drift_umap"], reverse=True)

    print(f"   ✓ Generated {len(nodes)} UMAP nodes")
    print(f"\n   Top 5 most divergent (UMAP manifold drift):")
    for node in nodes[:5]:
        print(f"     - {node['name']}: drift = {node['drift_umap']:.3f}")

    conn.close()

    result = {
        "nodes": nodes,
        "metadata": {
            "disparity_umap": float(disparity),
            "num_concepts": len(nodes),
            "human_model": "MiniLM-L6-v2",
            "ai_model": "Qwen2.5-14B",
            "method": "UMAP manifold reduction (n_neighbors=15, min_dist=0.1)",
            "layout_type": "manifold"
        }
    }

    print("\n" + "=" * 80)
    print("✓ UMAP MANIFOLD LAYOUT COMPLETE")
    print(f"Disparity: {disparity:.4f}")
    print("=" * 80)

    return result


if __name__ == "__main__":
    # Test generation
    result = generate_umap_layout()
    print(f"\nGenerated {len(result['nodes'])} nodes with UMAP coordinates")
    print(f"Disparity: {result['metadata']['disparity_umap']:.4f}")
