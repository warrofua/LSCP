"""
Run batch scan for remaining concepts (excluding already-scanned ones)
"""
import sys
from config import settings
from db.relational import LSCPDatabase
from db.vector_store import VectorStore
from models.control import ControlModel
from models.explorer import ExplorerModel
from crawler.scanner import LSCPScanner
from main import CORE_VOCABULARY, initialize_system

if __name__ == "__main__":
    # Initialize system
    scanner, db, vector_store = initialize_system()

    # Get already-scanned concepts
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT c.name FROM scans s JOIN concepts c ON s.anchor_concept_id = c.id")
    scanned = set(row[0].lower() for row in cursor.fetchall())

    print(f"\nAlready scanned: {len(scanned)} concepts")
    print(f"  {', '.join(sorted(scanned))}")

    # Get remaining concepts (ensure case-insensitive comparison)
    remaining = [c for c in CORE_VOCABULARY if c.lower() not in scanned]

    print(f"\nRemaining: {len(remaining)} concepts")
    print(f"First 10: {', '.join(remaining[:10])}")
    print(f"\nStarting batch scan of {len(remaining)} concepts...")
    print("="*60)

    # Run batch on remaining concepts
    results = scanner.batch_scan(remaining, CORE_VOCABULARY)

    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Previously completed: {len(scanned)}")
    print(f"Newly completed: {len(results)}")
    print(f"Total concepts: {len(scanned) + len(results)}/{len(CORE_VOCABULARY)}")

    db.close()
