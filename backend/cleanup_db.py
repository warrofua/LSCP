"""
Database Cleanup Script
Fixes corrupted blob data and removes duplicates
"""
import sqlite3
import struct
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "lscp.db"

def fix_corrupted_floats():
    """Fix blob data that should be floats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all relationships
    cursor.execute("SELECT id, human_distance FROM relationships")
    rows = cursor.fetchall()

    fixed_count = 0
    for row_id, human_dist in rows:
        if isinstance(human_dist, bytes):
            try:
                # Decode 4-byte IEEE 754 float from blob
                float_value = struct.unpack('f', human_dist)[0]
                # Update with proper float
                cursor.execute("UPDATE relationships SET human_distance = ? WHERE id = ?",
                             (float_value, row_id))
                fixed_count += 1
            except Exception as e:
                print(f"Error fixing row {row_id}: {e}")

    conn.commit()
    print(f"Fixed {fixed_count} corrupted human_distance values")

    # Verify fix
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE typeof(human_distance) = 'blob'")
    remaining_blobs = cursor.fetchone()[0]
    print(f"Remaining blob entries: {remaining_blobs}")

    conn.close()

def remove_duplicate_scans():
    """Remove duplicate scan entries, keeping only the first"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find duplicates
    cursor.execute("""
        SELECT anchor_concept_id, MIN(id) as keep_id, COUNT(*) as count
        FROM scans
        GROUP BY anchor_concept_id
        HAVING count > 1
    """)

    duplicates = cursor.fetchall()

    total_removed = 0
    for concept_id, keep_id, count in duplicates:
        # Delete all except the one we're keeping
        cursor.execute("""
            DELETE FROM scans
            WHERE anchor_concept_id = ? AND id != ?
        """, (concept_id, keep_id))
        removed = count - 1
        total_removed += removed
        print(f"Removed {removed} duplicate scan(s) for concept_id {concept_id}")

    conn.commit()
    print(f"Total duplicate scans removed: {total_removed}")

    conn.close()

def verify_database():
    """Verify database integrity"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE INTEGRITY CHECK")
    print("="*60)

    # Check data types
    cursor.execute("""
        SELECT
            SUM(CASE WHEN typeof(human_distance) = 'blob' THEN 1 ELSE 0 END) as blob_count,
            SUM(CASE WHEN typeof(human_distance) = 'real' THEN 1 ELSE 0 END) as real_count,
            COUNT(*) as total
        FROM relationships
    """)
    blob_count, real_count, total = cursor.fetchone()
    print(f"\nRelationships table:")
    print(f"  Total entries: {total}")
    print(f"  Correct (real): {real_count}")
    print(f"  Corrupted (blob): {blob_count}")

    # Check for duplicate scans
    cursor.execute("""
        SELECT anchor_concept_id, COUNT(*) as count
        FROM scans
        GROUP BY anchor_concept_id
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    print(f"\nScans table:")
    cursor.execute("SELECT COUNT(*) FROM scans")
    print(f"  Total scans: {cursor.fetchone()[0]}")
    print(f"  Duplicate scans: {len(duplicates)}")

    conn.close()

if __name__ == "__main__":
    print("Starting database cleanup...")
    print("="*60)

    verify_database()

    print("\n" + "="*60)
    print("FIXING ISSUES")
    print("="*60)

    fix_corrupted_floats()
    remove_duplicate_scans()

    verify_database()

    print("\n✓ Database cleanup complete!")
