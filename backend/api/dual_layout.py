"""
Dual-Layout Generation with Procrustes Alignment
Creates aligned 3D coordinates for MiniLM (human) and Qwen (AI) embeddings
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import networkx as nx
from scipy.spatial import procrustes
from typing import Dict, Tuple, List
import sqlite3


def compute_knn_relationships(embeddings: Dict[str, np.ndarray],
                              k: int = 5) -> List[Tuple[str, str, float]]:
    """
    Compute k-nearest neighbors from embeddings using cosine distance

    Args:
        embeddings: Dict mapping concept names to embedding vectors
        k: Number of nearest neighbors to keep per concept

    Returns:
        List of (concept, neighbor, distance) tuples
    """
    concepts = list(embeddings.keys())
    relationships = []

    print(f"   Computing k-NN (k={k}) from {len(concepts)} embeddings...")

    for concept in concepts:
        emb = embeddings[concept]
        emb_norm = np.linalg.norm(emb)

        if emb_norm == 0:
            continue

        distances = []

        for other in concepts:
            if other != concept:
                other_emb = embeddings[other]
                other_norm = np.linalg.norm(other_emb)

                if other_norm == 0:
                    continue

                # Cosine distance (1 - cosine similarity)
                cosine_sim = np.dot(emb, other_emb) / (emb_norm * other_norm)
                dist = 1.0 - cosine_sim
                distances.append((other, dist))

        # Keep top k neighbors
        distances.sort(key=lambda x: x[1])
        for neighbor, dist in distances[:k]:
            relationships.append((concept, neighbor, float(dist)))

    print(f"   ✓ Generated {len(relationships)} k-NN relationships")
    return relationships


def get_graph_layout_3d(embeddings: Dict[str, np.ndarray],
                        relationships: List[Tuple[str, str, float]],
                        spring_k: float = 2.0,
                        iterations: int = 150,
                        seed: int = 42) -> Dict[str, np.ndarray]:
    """
    Generate 3D force-directed layout from embeddings and relationships

    Args:
        embeddings: Dict mapping concept names to embedding vectors
        relationships: List of (source, target, distance) tuples
        spring_k: Optimal distance between nodes (higher = more spread)
        iterations: Number of iterations for spring layout
        seed: Random seed for reproducibility

    Returns:
        Dict mapping concept names to [x, y, z] coordinates
    """
    # Build weighted graph
    G = nx.Graph()

    for source, target, distance in relationships:
        if source in embeddings and target in embeddings:
            # AGGRESSIVE weight function (quadratic falloff)
            # Close neighbors hold tight, distant neighbors barely pull
            weight = 1.0 / ((distance + 0.1) ** 2)
            G.add_edge(source, target, weight=weight)

    # Generate 3D spring layout with custom parameters
    pos = nx.spring_layout(G, dim=3, k=spring_k, iterations=iterations, seed=seed)

    # Scale coordinates
    coords = {node: (np.array(coord) * 10).astype(np.float32)
              for node, coord in pos.items()}

    return coords


def align_layouts_procrustes(
    human_coords: Dict[str, np.ndarray],
    ai_coords: Dict[str, np.ndarray],
    preserve_scale: bool = False
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray], float]:
    """
    Align AI coordinate system to Human coordinate system using Procrustes analysis

    This ensures the two galaxies are in the same reference frame,
    so tension lines show true semantic drift, not arbitrary rotation.

    Args:
        human_coords: MiniLM-based 3D coordinates (base reality)
        ai_coords: Qwen-based 3D coordinates (alien thought)
        preserve_scale: If True, preserve natural variance differences (for authentic mode)

    Returns:
        (aligned_human_coords, aligned_ai_coords, disparity_score)
    """
    # Get shared concepts
    shared_concepts = sorted(set(human_coords.keys()) & set(ai_coords.keys()))

    if len(shared_concepts) < 3:
        raise ValueError(f"Need at least 3 shared concepts, got {len(shared_concepts)}")

    # Build matrices (N x 3)
    human_matrix = np.array([human_coords[c] for c in shared_concepts])
    ai_matrix = np.array([ai_coords[c] for c in shared_concepts])

    if preserve_scale:
        # AUTHENTIC MODE: Rotation + translation only (preserve natural scale)
        # Center both
        human_centered = human_matrix - np.mean(human_matrix, axis=0)
        ai_centered = ai_matrix - np.mean(ai_matrix, axis=0)

        # Print natural variance BEFORE rotation/scaling
        human_std_raw = np.std(human_centered)
        ai_std_raw = np.std(ai_centered)
        print(f"   Natural std deviation (before rotation):")
        print(f"      Human: {human_std_raw:.4f}")
        print(f"      AI:    {ai_std_raw:.4f}")
        print(f"      Ratio: AI is {ai_std_raw / human_std_raw:.2f}x the spread of Human")

        # Find rotation via SVD (but DON'T normalize scale)
        U, S, Vt = np.linalg.svd(ai_centered.T @ human_centered)
        R = U @ Vt
        ai_rotated = ai_centered @ R

        # Print variance AFTER rotation
        ai_std_rotated = np.std(ai_rotated)
        print(f"   After rotation (before scaling):")
        print(f"      Human: {human_std_raw:.4f}")
        print(f"      AI:    {ai_std_rotated:.4f}")
        print(f"      Ratio: AI is {ai_std_rotated / human_std_raw:.2f}x the spread of Human")

        # Compute disparity
        disparity = np.sqrt(np.sum((human_centered - ai_rotated) ** 2) / len(shared_concepts))

        # Scale for visualization based on human spread only (10x smaller for better viewing)
        scale_factor = 5.0 / np.std(human_centered)

        mtx1 = human_centered * scale_factor
        mtx2 = ai_rotated * scale_factor

        # Calculate actual coordinate ranges after scaling
        human_max_dist = np.max(np.linalg.norm(mtx1, axis=1))
        ai_max_dist = np.max(np.linalg.norm(mtx2, axis=1))
        human_final_std = np.std(mtx1)
        ai_final_std = np.std(mtx2)

        print(f"   Visualization scale factor: {scale_factor:.4f} (applied equally to both)")
        print(f"   Final coordinate statistics:")
        print(f"      Human - std: {human_final_std:.2f}, max distance from center: {human_max_dist:.2f}")
        print(f"      AI    - std: {ai_final_std:.2f}, max distance from center: {ai_max_dist:.2f}")
        print(f"      Visual size ratio: AI is {ai_max_dist / human_max_dist:.2f}x the radius of Human")
    else:
        # CONSTRAINED MODE: Standard Procrustes (rotation + scale)
        mtx1, mtx2, disparity = procrustes(human_matrix, ai_matrix)

        # Normalize variance to ensure both galaxies have same overall radius
        human_variance = np.var(mtx1)
        ai_variance = np.var(mtx2)

        if ai_variance > 0:  # Avoid division by zero
            variance_scale = np.sqrt(human_variance / ai_variance)
            mtx2 = mtx2 * variance_scale

        # Scale up for visualization (Procrustes normalizes to unit scale)
        scale_factor = 50.0
        mtx1 = mtx1 * scale_factor
        mtx2 = mtx2 * scale_factor

    # Reconstruct aligned dictionaries
    aligned_human = {c: mtx1[i] for i, c in enumerate(shared_concepts)}
    aligned_ai = {c: mtx2[i] for i, c in enumerate(shared_concepts)}

    return aligned_human, aligned_ai, disparity


def apply_drift_amplification(
    aligned_human: Dict[str, np.ndarray],
    aligned_ai: Dict[str, np.ndarray],
    amplification_factor: float = 3.0
) -> Dict[str, np.ndarray]:
    """
    Amplify drift by pushing AI positions further from human positions
    This creates the organic "bulging" topology

    Args:
        aligned_human: Human coordinates (base)
        aligned_ai: AI coordinates (to be pushed away)
        amplification_factor: How much to amplify drift

    Returns:
        Amplified AI coordinates
    """
    amplified_ai = {}

    for concept in aligned_human.keys():
        h_pos = aligned_human[concept]
        a_pos = aligned_ai[concept]

        # Calculate drift vector
        drift_vector = a_pos - h_pos

        # Amplify the drift
        amplified_pos = h_pos + (drift_vector * amplification_factor)
        amplified_ai[concept] = amplified_pos

    return amplified_ai


def generate_dual_layout():
    """
    Generate dual-view layout with both constrained and organic topologies

    Creates TWO layouts:
    - SPHERE mode: Both use same graph (constrained, for comparison)
    - ORGANIC mode: Separate k-NN graphs (authentic topology)

    Returns:
        Dict with structure:
        {
            "nodes": [
                {
                    "name": "love",
                    "pos_human": [x, y, z],
                    "pos_ai": [x, y, z],  # Sphere mode (shared graph)
                    "pos_ai_organic": [x, y, z],  # Organic mode (dual graph)
                    "drift": distance,
                    ...
                }
            ],
            "metadata": {
                "disparity": float,
                "num_concepts": int
            }
        }
    """
    print("\n" + "=" * 80)
    print("DUAL LAYOUT GENERATION: SPHERE + ORGANIC MODES")
    print("=" * 80)

    # Database paths
    db_path = "/Users/joshuafarrow/Projects/LSCP/data/lscp.db"
    minilm_npz_path = "/Users/joshuafarrow/Projects/LSCP/data/minilm_embeddings.npz"
    qwen_npz_path = "/Users/joshuafarrow/Projects/LSCP/data/qwen_embeddings.npz"

    # Get concepts
    print("\n1. Loading concepts from database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM concepts ORDER BY name")
    concepts = [row[0] for row in cursor.fetchall()]
    print(f"   Found {len(concepts)} concepts")

    # Get embeddings
    print("\n2. Loading embeddings...")

    # Load MiniLM (human) embeddings from .npz file
    print(f"   Loading MiniLM embeddings from {minilm_npz_path}...")
    minilm_data = np.load(minilm_npz_path)

    human_embeddings = {}
    for concept in concepts:
        if concept in minilm_data:
            emb = minilm_data[concept]
            # Flatten if needed
            if len(emb.shape) > 1:
                emb = emb.flatten()
            human_embeddings[concept] = emb

    # Load Qwen (AI) embeddings from .npz file
    print(f"   Loading Qwen embeddings from {qwen_npz_path}...")
    qwen_data = np.load(qwen_npz_path)

    ai_embeddings = {}
    for concept in concepts:
        if concept in qwen_data:
            emb = qwen_data[concept]
            # Flatten if needed (some are (1, 5120), should be (5120,))
            if len(emb.shape) > 1:
                emb = emb.flatten()
            # Handle duplicated embeddings (take first 5120 if > 5120)
            if emb.shape[0] > 5120:
                emb = emb[:5120]  # Take first 5120 dimensions only
            ai_embeddings[concept] = emb

    print(f"   ✓ Human (MiniLM): {len(human_embeddings)} embeddings (384D)")
    print(f"   ✓ AI (Qwen): {len(ai_embeddings)} embeddings (5120D)")

    # ====================
    # SPHERE MODE: Shared relationship graph from DB
    # ====================
    print("\n3. SPHERE MODE: Generating constrained layouts (shared graph)...")
    cursor.execute("""
        SELECT c1.name AS concept_a, c2.name AS concept_b, r.human_distance
        FROM relationships r
        JOIN concepts c1 ON r.concept_a_id = c1.id
        JOIN concepts c2 ON r.concept_b_id = c2.id
        WHERE r.human_distance IS NOT NULL
    """)
    shared_relationships = cursor.fetchall()
    print(f"   Using {len(shared_relationships)} shared relationships from DB")

    print("   Human sphere layout:")
    human_sphere = get_graph_layout_3d(
        human_embeddings,
        shared_relationships,
        spring_k=2.0,
        iterations=150,
        seed=42
    )

    print("   AI sphere layout:")
    ai_sphere = get_graph_layout_3d(
        ai_embeddings,
        shared_relationships,
        spring_k=2.0,
        iterations=150,
        seed=43
    )

    print("   Aligning sphere layouts (Procrustes)...")
    aligned_human_sphere, aligned_ai_sphere, disparity_sphere = align_layouts_procrustes(
        human_sphere, ai_sphere
    )
    print(f"   ✓ Sphere mode disparity: {disparity_sphere:.4f}")

    # ====================
    # AUTHENTIC MODE: Separate k-NN graphs, identical physics, preserve scale
    # ====================
    print("\n4. AUTHENTIC MODE: Generating scientifically rigorous layouts...")
    print("   IDENTICAL PHYSICS: k=8, spring_k=2.0, iterations=200")
    print("   SCALE PRESERVED: No variance normalization")

    print("   Computing human k-NN graph (k=8):")
    human_relationships = compute_knn_relationships(human_embeddings, k=8)

    print("   Computing AI k-NN graph (k=8):")
    ai_relationships = compute_knn_relationships(ai_embeddings, k=8)

    print("   Human authentic layout:")
    human_organic = get_graph_layout_3d(
        human_embeddings,
        human_relationships,
        spring_k=2.0,      # IDENTICAL
        iterations=200,    # IDENTICAL
        seed=42
    )

    print("   AI authentic layout:")
    ai_organic = get_graph_layout_3d(
        ai_embeddings,
        ai_relationships,
        spring_k=2.0,      # IDENTICAL
        iterations=200,    # IDENTICAL
        seed=43
    )

    print("   Aligning authentic layouts (rotation only, scale preserved)...")
    aligned_human_organic, aligned_ai_organic, disparity_organic = align_layouts_procrustes(
        human_organic, ai_organic, preserve_scale=True  # KEY: preserve natural variance
    )
    print(f"   ✓ Authentic mode disparity: {disparity_organic:.4f}")
    print(f"   ✓ Natural scale differences preserved")

    # ====================
    # Build node data with both modes
    # ====================
    print("\n5. Building dual-mode node data...")
    nodes = []

    for concept in sorted(aligned_human_sphere.keys()):
        # Sphere mode positions
        h_pos_sphere = aligned_human_sphere[concept]
        a_pos_sphere = aligned_ai_sphere[concept]
        drift_sphere = np.linalg.norm(h_pos_sphere - a_pos_sphere)

        # Organic mode positions (if available)
        h_pos_organic = aligned_human_organic.get(concept, h_pos_sphere)
        a_pos_organic = aligned_ai_organic.get(concept, a_pos_sphere)
        drift_organic = np.linalg.norm(h_pos_organic - a_pos_organic)

        # Get concept metadata
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
            "pos_human": h_pos_sphere.tolist(),  # Sphere mode human
            "pos_ai": a_pos_sphere.tolist(),  # Sphere mode AI
            "pos_human_organic": h_pos_organic.tolist(),  # Organic mode human
            "pos_ai_organic": a_pos_organic.tolist(),  # Organic mode AI
            "drift": float(drift_organic),  # Use organic drift for sorting
            "drift_sphere": float(drift_sphere),
            "drift_organic": float(drift_organic),
            "avgDistance": float(avg_dist or 0.5),
            "connections": int(conn_count or 0)
        })

    # Sort by organic drift (most divergent first)
    nodes.sort(key=lambda n: n["drift_organic"], reverse=True)

    print(f"   ✓ Generated {len(nodes)} dual nodes")
    print(f"\n   Top 5 most divergent (organic mode):")
    for node in nodes[:5]:
        print(f"     - {node['name']}: drift = {node['drift_organic']:.3f}")

    result = {
        "nodes": nodes,
        "metadata": {
            "disparity_sphere": float(disparity_sphere),
            "disparity_organic": float(disparity_organic),
            "num_concepts": len(nodes),
            "human_model": "MiniLM-L6-v2",
            "ai_model": "Qwen2.5-14B",
            "sphere_method": "Shared graph (constrained comparison)",
            "organic_method": "Dual k-NN graphs (authentic topology)"
        }
    }

    print("\n" + "=" * 80)
    print("✓ DUAL LAYOUT COMPLETE")
    print(f"Sphere mode: Constrained (disparity={disparity_sphere:.4f})")
    print(f"Organic mode: Authentic (disparity={disparity_organic:.4f})")
    print("=" * 80)

    return result


if __name__ == "__main__":
    # Test generation
    result = generate_dual_layout()
    print(f"\nGenerated {len(result['nodes'])} nodes with dual coordinates")
    print(f"Disparity: {result['metadata']['disparity']:.4f}")
