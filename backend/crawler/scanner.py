"""
The Scanner: Core LSCP Crawling Logic
Compares human and latent semantic spaces
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.spatial.distance import cosine
from tqdm import tqdm

from models.control import ControlModel
from models.explorer import ExplorerModel
from db.vector_store import VectorStore
from db.relational import LSCPDatabase


class LSCPScanner:
    """Performs LSCP scans on concepts"""

    def __init__(
        self,
        control_model: ControlModel,
        explorer_model: ExplorerModel,
        vector_store: VectorStore,
        database: LSCPDatabase,
        neighbor_count: int = 5,
        delta_threshold: float = 0.3
    ):
        self.control = control_model
        self.explorer = explorer_model
        self.vector_store = vector_store
        self.db = database
        self.neighbor_count = neighbor_count
        self.delta_threshold = delta_threshold

    def scan_concept(self, concept: str, vocabulary: List[str]) -> Dict:
        """
        Perform a complete LSCP scan on a single concept

        Args:
            concept: The anchor concept to scan
            vocabulary: List of all possible neighbor concepts

        Returns:
            Dictionary containing scan results
        """
        print(f"\n{'='*60}")
        print(f"SCANNING: {concept.upper()}")
        print(f"{'='*60}")

        # Step 1: Generate embeddings (using MiniLM for both - DeepSeek is for reasoning only)
        print("1. Generating embeddings...")
        embedding = self.control.encode(concept)

        # Store in both collections (we use same embedding space for comparison)
        self.vector_store.add_human_embedding(concept, embedding)
        self.vector_store.add_latent_embedding(concept, embedding)

        # Step 2: Find nearest neighbors in both spaces
        print("2. Finding nearest neighbors...")

        # Ensure vocabulary is embedded
        for word in tqdm(vocabulary, desc="Embedding vocabulary"):
            try:
                if not self.vector_store.concept_exists(word):
                    emb = self.control.encode(word)
                    self.vector_store.add_human_embedding(word, emb)
                    self.vector_store.add_latent_embedding(word, emb)
            except Exception as e:
                print(f"\n  Warning: Failed to embed '{word}': {e}")
                continue

        # Find neighbors (using MiniLM - DeepSeek will provide reasoning, not embeddings)
        neighbors = self.control.find_nearest(concept, vocabulary, self.neighbor_count)

        print("\nNearest Neighbors (MiniLM):")
        for neighbor, dist in neighbors:
            print(f"  - {neighbor}: {dist:.3f}")

        # Step 3: Generate DeepSeek reasoning for interesting pairs
        print("\n3. Generating DeepSeek reasoning for connections...")
        deltas = []

        # Process all neighbors and generate bridges for significant connections
        for neighbor_concept, dist in neighbors:
            # For now, treat distance as the delta (higher distance = more interesting)
            # We'll generate bridges for pairs above threshold
            deltas.append(dist)

            # Generate bridge mechanism if distance is high enough (interesting connection)
            bridge = None
            reasoning = None
            if dist >= self.delta_threshold:
                print(f"  Analyzing: {concept} <-> {neighbor_concept} (distance={dist:.3f})")
                bridge, reasoning = self.explorer.generate_bridge(concept, neighbor_concept)
                print(f"  Bridge: {bridge}")
                if reasoning:
                    print(f"\n  🧠 Thinking Trace:")
                    print(f"  {reasoning[:300]}..." if len(reasoning) > 300 else f"  {reasoning}")
                    print()

            # Store relationship (using same distance for both since we only have one embedding space)
            self.db.add_relationship(
                concept_a=concept,
                concept_b=neighbor_concept,
                human_distance=float(dist),
                latent_distance=float(dist),  # Same as human since we use one embedding space
                delta=0.0,  # No delta in this architecture
                bridge_mechanism=bridge,
                internal_monologue=reasoning,
                relationship_type="neighbor"
            )

        # Step 4: Log the scan
        avg_dist = np.mean(deltas)
        self.db.add_scan(
            anchor_concept=concept,
            human_vector=[n[0] for n in neighbors],
            latent_vector=[n[0] for n in neighbors],  # Same as human
            avg_delta=avg_dist
        )

        result = {
            "concept": concept,
            "human_neighbors": neighbors,
            "latent_neighbors": neighbors,  # Same as human in this architecture
            "avg_delta": avg_dist,
            "high_delta_count": sum(1 for d in deltas if d >= self.delta_threshold)
        }

        print(f"\nScan complete: Avg Distance = {avg_dist:.3f}")
        print(f"Bridges generated: {result['high_delta_count']}")

        return result

    def batch_scan(self, concepts: List[str], vocabulary: List[str]) -> List[Dict]:
        """
        Scan multiple concepts
        Vocabulary should include all concepts being scanned
        """
        results = []
        failed = []

        for i, concept in enumerate(concepts, 1):
            print(f"\n[{i}/{len(concepts)}] Processing: {concept}")
            try:
                result = self.scan_concept(concept, vocabulary)
                results.append(result)
                print(f"✓ Successfully scanned {concept}")
            except Exception as e:
                error_msg = str(e)
                print(f"✗ Error scanning {concept}: {error_msg}")

                # Log but don't stop
                failed.append({
                    'concept': concept,
                    'error': error_msg
                })

                # Continue to next concept
                continue

        # Print summary
        print(f"\n{'='*60}")
        print("BATCH SCAN SUMMARY")
        print(f"{'='*60}")
        print(f"Successful: {len(results)}/{len(concepts)}")
        print(f"Failed: {len(failed)}/{len(concepts)}")

        if failed:
            print("\nFailed scans:")
            for item in failed:
                print(f"  - {item['concept']}: {item['error'][:80]}")

        return results

    def calculate_semantic_delta(self, concept_a: str, concept_b: str) -> Tuple[float, float, float]:
        """
        Calculate the semantic delta between two concepts

        Returns:
            (human_distance, latent_distance, delta)
        """
        human_dist = self.control.distance(concept_a, concept_b)
        latent_dist = self.explorer.distance(concept_a, concept_b)
        delta = abs(human_dist - latent_dist)

        return human_dist, latent_dist, delta

    def find_edge_concepts(self, threshold: float = 0.3) -> List[Dict]:
        """
        Find all concept pairs with high semantic delta (the "Edge")

        Returns:
            List of high-delta relationships from database
        """
        return self.db.get_high_delta_relationships(threshold=threshold)
