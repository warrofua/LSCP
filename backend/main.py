"""
LSCP Main CLI
Command-line interface for running scans and populating the database
"""
import argparse
import sys
from pathlib import Path

from config import settings
from db.relational import LSCPDatabase
from db.vector_store import VectorStore
from models.control import ControlModel
from models.explorer import ExplorerModel
from crawler.scanner import LSCPScanner


# Oxford 3000 Core Word List (subset for initial testing)
CORE_VOCABULARY = [
    # Abstract Concepts
    "time", "space", "reality", "truth", "knowledge", "memory", "thought", "idea",
    "concept", "meaning", "purpose", "value", "existence", "consciousness",

    # Emotions
    "love", "hate", "fear", "joy", "anger", "sadness", "hope", "trust",
    "anxiety", "peace", "desire", "curiosity",

    # Actions
    "think", "learn", "create", "destroy", "build", "grow", "change", "move",
    "predict", "understand", "believe", "know", "remember", "forget",

    # Properties
    "good", "bad", "right", "wrong", "true", "false", "real", "fake",
    "strong", "weak", "fast", "slow", "big", "small",

    # Science/Math
    "energy", "force", "matter", "wave", "particle", "entropy", "chaos",
    "order", "pattern", "system", "function", "variable", "constant",

    # Human Experience
    "birth", "death", "life", "dream", "sleep", "awake", "pain", "pleasure",
    "hunger", "thirst", "safety", "danger", "survival", "attention",

    # Social
    "family", "friend", "enemy", "stranger", "leader", "follower", "group",
    "society", "culture", "language", "communication", "relationship",

    # Computational (High Delta Expected)
    "compression", "loss", "gradient", "optimization", "prediction", "model",
    "data", "information", "signal", "noise", "probability", "distribution"
]


def initialize_system():
    """Initialize all components"""
    print("="*60)
    print("LATENT SPACE CARTOGRAPHY PROTOCOL")
    print("Initializing System...")
    print("="*60)

    # Check if DeepSeek API key is set
    if not settings.DEEPSEEK_API_KEY:
        print("\nERROR: DEEPSEEK_API_KEY not set!")
        print("Please set the environment variable DEEPSEEK_API_KEY.")
        print("Example: export DEEPSEEK_API_KEY=your_api_key_here")
        sys.exit(1)

    # Initialize databases
    print("\n1. Initializing databases...")
    db = LSCPDatabase(settings.SQLITE_DB_PATH)
    vector_store = VectorStore(settings.VECTOR_DB_PATH, settings.CHROMA_COLLECTION_NAME)

    # Initialize models
    print("\n2. Loading models...")
    print(f"Loading Control Model (Human): {settings.MINILM_MODEL_NAME}")
    control_model = ControlModel(settings.MINILM_MODEL_NAME)
    print("Control Model loaded successfully")

    print(f"Loading Explorer Model (Latent): DeepSeek {settings.DEEPSEEK_MODEL}")
    explorer_model = ExplorerModel(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        model_name=settings.DEEPSEEK_MODEL
    )
    print("Explorer Model loaded successfully")

    # Create scanner
    print("\n3. Initializing scanner...")
    scanner = LSCPScanner(
        control_model=control_model,
        explorer_model=explorer_model,
        vector_store=vector_store,
        database=db,
        neighbor_count=settings.NEIGHBOR_COUNT,
        delta_threshold=settings.DELTA_THRESHOLD
    )

    print("\n✓ System initialization complete!")
    return scanner, db, vector_store


def scan_single_concept(scanner: LSCPScanner, concept: str, vocabulary: list):
    """Scan a single concept"""
    result = scanner.scan_concept(concept, vocabulary)

    print("\n" + "="*60)
    print("SCAN RESULTS")
    print("="*60)
    print(f"Concept: {result['concept']}")
    print(f"Average Delta: {result['avg_delta']:.4f}")
    print(f"High Delta Pairs: {result['high_delta_count']}")
    print("\nHuman Neighbors:")
    for neighbor, dist in result['human_neighbors']:
        print(f"  • {neighbor}: {dist:.3f}")
    print("\nLatent Neighbors:")
    for neighbor, dist in result['latent_neighbors']:
        print(f"  • {neighbor}: {dist:.3f}")


def scan_batch(scanner: LSCPScanner, concepts: list, vocabulary: list):
    """Scan multiple concepts"""
    print(f"\n{'='*60}")
    print(f"BATCH SCAN: {len(concepts)} concepts")
    print(f"{'='*60}")

    results = scanner.batch_scan(concepts, vocabulary)

    print(f"\n{'='*60}")
    print("BATCH SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"Total scanned: {len(results)}")

    # Show top high-delta concepts
    sorted_results = sorted(results, key=lambda x: x['avg_delta'], reverse=True)
    print("\nTop 10 concepts by average delta:")
    for i, result in enumerate(sorted_results[:10], 1):
        print(f"{i}. {result['concept']}: Δ={result['avg_delta']:.4f} ({result['high_delta_count']} high-delta pairs)")


def show_stats(db: LSCPDatabase):
    """Show database statistics"""
    cursor = db.conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM concepts")
    concept_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships")
    relationship_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans")
    scan_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(delta) FROM relationships")
    avg_delta = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE delta >= ?", (settings.DELTA_THRESHOLD,))
    high_delta_count = cursor.fetchone()[0]

    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Concepts: {concept_count}")
    print(f"Relationships: {relationship_count}")
    print(f"Scans: {scan_count}")
    print(f"Average Delta: {avg_delta:.4f}")
    print(f"High Delta Pairs (≥{settings.DELTA_THRESHOLD}): {high_delta_count}")


def main():
    parser = argparse.ArgumentParser(description="LSCP Scanner CLI")
    parser.add_argument("--scan", type=str, help="Scan a single concept")
    parser.add_argument("--batch", action="store_true", help="Scan all core vocabulary")
    parser.add_argument("--batch-size", type=int, default=None, help="Limit batch scan to N words")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--edges", action="store_true", help="Show high-delta edges")
    parser.add_argument("--server", action="store_true", help="Start API server")

    args = parser.parse_args()

    if args.server:
        from api.server import run_server
        run_server()
        return

    # Initialize system for other operations
    scanner, db, vector_store = initialize_system()

    if args.stats:
        show_stats(db)

    elif args.edges:
        edges = db.get_high_delta_relationships(threshold=settings.DELTA_THRESHOLD, limit=20)
        print("\n" + "="*60)
        print(f"TOP HIGH-DELTA EDGES (threshold={settings.DELTA_THRESHOLD})")
        print("="*60)
        for edge in edges:
            print(f"\n{edge['concept_a']} ↔ {edge['concept_b']}")
            print(f"  Human Distance: {edge['human_distance']:.3f}")
            print(f"  Latent Distance: {edge['latent_distance']:.3f}")
            print(f"  Delta: {edge['delta']:.3f}")
            if edge['bridge_mechanism']:
                print(f"  Bridge: {edge['bridge_mechanism']}")

    elif args.scan:
        scan_single_concept(scanner, args.scan, CORE_VOCABULARY)

    elif args.batch:
        vocab = CORE_VOCABULARY[:args.batch_size] if args.batch_size else CORE_VOCABULARY
        scan_batch(scanner, vocab, vocab)

    else:
        parser.print_help()

    db.close()


if __name__ == "__main__":
    main()
